# SmartAlloc — AI-Based Smart Allocation Engine for PM Internship Scheme

SmartAlloc matches candidates to internships automatically. Instead of someone manually
comparing hundreds of resumes against dozens of openings, this system does it with a
combination of rule-based filtering, fuzzy logic, a trained ML model, and a global
optimizer — then explains every decision it makes.

This README explains what every part of the project does, how they connect, and how to
run the whole thing from scratch.

---

## 1. What problem does this solve?

The PM Internship Scheme needs to assign thousands of candidates to a limited number of
internship seats, while respecting rules like:

- A candidate must be qualified enough for the role
- A candidate must be willing to work in that internship's location
- A candidate must have at least one of the required skills
- Some internships are reserved for specific categories (e.g. SC/ST/OBC/EWS)
- Each internship only has a fixed number of seats

On top of that, not every candidate who gets offered a seat will accept it — so the
system also predicts how likely someone is to accept before deciding who to allocate.

This prototype demonstrates the full decision pipeline using **synthetic (fake) data**
that mimics what a real dataset would look like.

---

## 2. How a candidate becomes "allocated" — the pipeline

Every candidate goes through five stages, run in this order:

```
generate_data.py  →  eligibility.py  →  fuzzy_scoring.py  →  train_acceptance_model.py  →  optimizer.py
```

### Stage 1 — `generate_data.py`
Creates fake candidates and internships using the `Faker` library, so the system has
something to work with. Produces:
- `candidates.csv` — 200 candidates (id, name, category, preferred location, skills, qualification score)
- `internships.csv` — 30 internships (id, title, location, seat capacity, required skills, reserved category if any)

### Stage 2 — `eligibility.py`
Goes through every possible (candidate, internship) pair and applies three hard rules.
A pair only passes if **all three** are true:
1. Candidate's `qualification_score` is at least 55
2. Candidate's preferred location matches the internship's location exactly
3. Candidate has at least 1 skill that overlaps with the internship's required skills

Anything that fails any rule is discarded. What's left is written to `eligible_pairs.csv`.

### Stage 3 — `fuzzy_scoring.py`
For every eligible pair, this calculates a **fit score from 0–100** — not with a simple
weighted average, but using fuzzy logic (`scikit-fuzzy`). It classifies skill match % and
qualification score into "low / medium / high" fuzzy categories, applies rule logic
(e.g. "if skill is high AND qualification is high → fit is high"), and converts that back
into one number via centroid defuzzification. Output: `scored_pairs.csv`.

### Stage 4 — `train_acceptance_model.py`
Trains a **Logistic Regression** model to predict the probability a candidate would
*accept* an offer, based on `fit_score` and `skill_match_pct`. Since there's no real
historical acceptance data available yet, this stage simulates realistic labels (higher
fit → more likely to accept, plus some randomness) purely to have something to train on.
Outputs:
- `acceptance_model.pkl` — the trained model, saved so it doesn't need retraining every run
- `scored_pairs_with_probability.csv` — every eligible pair, now with an `accept_probability` column

### Stage 5 — `optimizer.py`
This is where the actual allocation decision happens. Using Google **OR-Tools CP-SAT**,
it solves the assignment problem globally — not pair by pair — while enforcing:
- Each candidate gets **at most one** internship
- Each internship fills **at most its capacity**
- Reserved-category internships only go to candidates from that category

The objective it maximizes is `fit_score × accept_probability`, summed across everyone
allocated. Output: `final_allocation.csv` — the source of truth for who's currently
allocated where.

---

## 3. What happens after the initial allocation

Two more modules act on top of the finished allocation:

### `reallocation.py` — handling declines
If an allocated candidate declines their offer, this module doesn't rerun the entire
pipeline. It:
1. Removes that candidate from the allocation and frees up their seat
2. Finds every eligible, still-unallocated candidate for that specific internship
3. Re-solves *just that one seat* with the same objective/constraints the main optimizer
   uses (a small CP-SAT model, not a full 200-candidate re-run)
4. Validates the result (no duplicate allocations, capacity respected, reservation
   respected) **before** writing anything
5. Writes the updated `final_allocation.csv` and logs the event to `allocation_audit.csv`

If no eligible replacement exists, the seat is simply left open — it never fabricates an
invalid assignment.

### `explainability.py` — explaining decisions
This is a **read-only** reporting layer. It never changes an allocation. Given a
candidate id (and optionally an internship id), it explains:
- Whether they passed each eligibility rule, and why
- Their fit score, skill match, and acceptance probability
- Whether reservation rules applied
- The internship's capacity and who else is allocated there
- The final decision, in plain English, with an explicit note about what *can't* be
  proven (since the optimizer decides globally, this module never claims to know the
  exact reason a specific candidate lost out to another)

It also carefully distinguishes **facts** (numbers read directly from the CSVs),
**interpretation** (what those facts mean), and **limitations** (what genuinely can't be
determined from stored data).

---

## 4. How the frontend talks to all of this

The React frontend never runs Python directly. Everything goes through the FastAPI
backend:

```
React (localhost:5173)
     │  fetch()
     ▼
FastAPI backend (localhost:8000)
     │  subprocess — runs the actual .py scripts in src/
     ▼
Python engine  →  writes to demoData/*.csv
     │
     ▼
FastAPI reads the CSVs, returns JSON
     │
     ▼
React renders it
```

### API endpoints (`backend/app.py`)

| Method | Endpoint | What it does |
|---|---|---|
| GET | `/api/health` | Confirms the backend is running |
| GET | `/api/candidates` | Returns all candidates from `candidates.csv` |
| GET | `/api/opportunities` | Returns all internships from `internships.csv` |
| GET | `/api/results` | Returns the current allocation from `final_allocation.csv` |
| POST | `/api/allocation/run` | Runs the full 5-stage pipeline, returns the new allocation |
| POST | `/api/reallocation/decline/{candidate_id}` | Runs `reallocation.py` for that candidate, returns the updated allocation |
| GET | `/api/explainability/candidate/{candidate_id}` | Runs `explainability.py`, returns the text explanation report |
| GET | `/api/explainability/pair/{candidate_id}/{internship_id}` | Same, but for one specific candidate-internship pair |

### Frontend pages (`frontend/src/App.jsx`)

- **Dashboard** — overview stats, allocation %, engine status
- **Candidates** — full candidate list, searchable
- **Opportunities** — internship cards with location, capacity, required skills
- **Smart Allocation** — the "Run Smart Allocation" button that triggers the whole pipeline
- **Results** — the allocation table, with **Explain** and **Decline** buttons on every row
- **Analytics** — success rate, average fit score, summary metrics

---

## 5. Project structure

```
SIH_MINI/
├── backend/
│   ├── __init__.py
│   └── app.py                     # FastAPI server — the bridge between React and Python
│
├── demoData/                      # All pipeline inputs/outputs live here as CSVs
│   ├── candidates.csv
│   ├── internships.csv
│   ├── eligible_pairs.csv
│   ├── scored_pairs.csv
│   ├── labeled_pairs.csv
│   ├── scored_pairs_with_probability.csv
│   ├── final_allocation.csv       # current allocation — source of truth
│   ├── allocation_audit.csv       # append-only log of decline/reallocation events
│   └── explanations.csv           # bulk explanation report (optional, generated on demand)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # the entire UI
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── src/                           # the actual AI/allocation engine
│   ├── generate_data.py           # stage 1: creates fake candidates/internships
│   ├── eligibility.py             # stage 2: hard rule filtering
│   ├── fuzzy_scoring.py           # stage 3: fuzzy logic fit scoring
│   ├── train_acceptance_model.py  # stage 4: trains + applies the ML acceptance model
│   ├── optimizer.py               # stage 5: OR-Tools global allocation
│   ├── reallocation.py            # handles declines after the fact
│   ├── explainability.py          # read-only decision explanations
│   └── acceptance_model.pkl       # the trained model (generated, not hand-written)
│
├── requirements.txt
└── README.md
```

---

## 6. Setup and running it

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

Check what you have:
```bash
python --version
node --version
npm --version
```

### Step 1 — Create and activate a virtual environment (from the project root)

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> Note: a venv is tied to the exact machine/folder it was created in — never copy a
> `venv` folder between computers or Git it. Always create a fresh one.

### Step 2 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Start the backend
From the project root, with the venv active:
```bash
python -m uvicorn backend.app:app --reload --port 8000
```
Leave this running. Confirm it worked: open `http://127.0.0.1:8000/api/health` — you
should see `{"status": "ok", "service": "SmartAlloc API"}`.

### Step 4 — Start the frontend (in a second terminal)
```bash
cd frontend
npm install
npm run dev
```
Open the URL it gives you — normally `http://localhost:5173`.

### Step 5 — Use it
1. Open the app in your browser
2. Go to **Smart Allocation** → click **Run Smart Allocation** (runs the full 5-stage pipeline)
3. Go to **Results** to see who got allocated where
4. Click **Explain** on any row to see the full reasoning behind that allocation
5. Click **Decline** on any row to simulate that candidate turning down the offer, and
   watch the engine try to find a replacement in real time

---

## 7. Running the Python engine without the frontend

Useful for debugging or demoing just the AI side.

```bash
cd src
python generate_data.py
python eligibility.py
python fuzzy_scoring.py
python train_acceptance_model.py
python optimizer.py
```
Each stage reads the previous stage's CSV and writes the next one, ending in
`demoData/final_allocation.csv`.

**Handling a decline manually:**
```bash
python reallocation.py C0001
```

**Getting an explanation manually:**
```bash
python explainability.py C0001
python explainability.py C0001 I010    # explain one specific candidate-internship pair
```

---

## 8. Current limitations

This is a working prototype, not a production system. Specifically:

- Data is synthetic (`Faker`-generated), not real applicant data
- Acceptance labels used to train the ML model are simulated, not historical
- Data is stored in CSV files, not a database
- There's no authentication or access control
- Not deployed anywhere — runs locally only

## 9. Planned for a production version

- PostgreSQL (or similar) instead of CSVs
- Real historical acceptance data to train the ML model properly
- Authentication and role-based access control
- Proper deployment and security hardening
- Expanded analytics and reporting

---

## 10. Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite |
| Icons | Lucide React |
| Backend API | FastAPI + Uvicorn |
| Data handling | pandas, numpy |
| Eligibility filtering | plain Python rule logic |
| Fit scoring | scikit-fuzzy |
| Acceptance prediction | scikit-learn (Logistic Regression) |
| Global optimization | Google OR-Tools (CP-SAT solver) |
| Data storage (prototype) | CSV files |
