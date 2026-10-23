from pathlib import Path
from threading import Lock
import subprocess
import sys
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DEMO_DIR = ROOT_DIR / "demoData"

app = FastAPI(title="SmartAlloc API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Production frontend on Vercel
        "https://smart-allocation-pmi.vercel.app",
        # Allow any Vercel preview deployments for this project
        "https://smart-allocation-pmi-*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline_lock = Lock()


def read_csv(name: str):
    path = DEMO_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{name} not found. Run the allocation pipeline first.")
    return pd.read_csv(path).fillna("").to_dict(orient="records")


def run_python(script: str, args: list = None):
    cmd = [sys.executable, script] + (args or [])
    result = subprocess.run(
        cmd,
        cwd=SRC_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{script} failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SmartAlloc API"}


@app.get("/api/candidates")
def candidates():
    return read_csv("candidates.csv")


@app.get("/api/opportunities")
def opportunities():
    return read_csv("internships.csv")


@app.get("/api/results")
def results():
    return read_csv("final_allocation.csv")


@app.post("/api/allocation/run")
def run_allocation():
    # Keep the existing Python engine unchanged. The API simply orchestrates
    # its existing scripts and exposes their CSV outputs to React.
    with pipeline_lock:
        try:
            logs = []
            for script in [
                "generate_data.py",
                "eligibility.py",
                "fuzzy_scoring.py",
                "train_acceptance_model.py",
                "optimizer.py",
            ]:
                logs.append(run_python(script))

            allocation = read_csv("final_allocation.csv")
            candidates_data = read_csv("candidates.csv")
            internships_data = read_csv("internships.csv")

            return {
                "success": True,
                "message": "Allocation completed successfully using the Python engine.",
                "candidates_processed": len(candidates_data),
                "internships": len(internships_data),
                "allocated": len(allocation),
                "pending": len(candidates_data) - len(allocation),
                "results": allocation,
                "logs": logs,
            }
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Python allocation pipeline timed out.")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/reallocation/decline/{candidate_id}")
def decline_offer(candidate_id: str):
    with pipeline_lock:
        try:
            output = run_python("reallocation.py", [candidate_id])
            allocation = read_csv("final_allocation.csv")
            return {
                "success": True,
                "message": output.strip(),
                "results": allocation,
            }
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/explainability/candidate/{candidate_id}")
def explain_candidate_route(candidate_id: str):
    try:
        output = run_python("explainability.py", [candidate_id])
        return {"success": True, "candidate_id": candidate_id, "explanation": output}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/explainability/pair/{candidate_id}/{internship_id}")
def explain_pair_route(candidate_id: str, internship_id: str):
    try:
        output = run_python("explainability.py", [candidate_id, internship_id])
        return {"success": True, "candidate_id": candidate_id, "internship_id": internship_id, "explanation": output}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))