"""
explainability.py

Deterministic decision-explainability layer over the AI-Based Smart
Allocation Engine.

This module NEVER makes, changes, or overrides an allocation decision. It
is a READ-ONLY evidence-interpretation layer over the outputs the rest of
the pipeline already produced:

    generate_data.py -> eligibility.py -> fuzzy_scoring.py ->
    train_acceptance_model.py -> optimizer.py -> reallocation.py

It answers two questions:

    explain_candidate(candidate_id)
        "What is this candidate's overall allocation status, and why?"

    explain_pair(candidate_id, internship_id)
        "Why did this candidate get (or not get) this specific internship?"

ARCHITECTURE
------------
    Existing Pipeline
          |
          +--> eligible_pairs.csv
          +--> scored_pairs.csv
          +--> scored_pairs_with_probability.csv
          +--> final_allocation.csv          (current state -- source of truth)
          +--> allocation_audit.csv          (append-only history)
                        |
                        v
                explainability.py
                        |
                        v
                 HUMAN EXPLANATION

`final_allocation.csv` is the single source of truth for current
allocation; `final_allocation_updated.csv` (or any file like it) is never
read. This module never writes to `final_allocation.csv` or
`allocation_audit.csv` -- the only file it may write is
`demoData/explanations.csv`, a report output.

FACT vs INTERPRETATION vs LIMITATION
-------------------------------------
Every explanation this module produces distinguishes:

  FACT           -- a value read directly from a pipeline output file.
  INTERPRETATION -- a plain-English gloss of what those facts mean,
                    never a claim about the optimizer's internal reasoning
                    beyond what the global-optimizer constraints allow us
                    to say.
  LIMITATION     -- an explicit statement of what cannot be established
                    from the stored outputs (e.g. the exact counterfactual
                    tradeoff behind a non-selection).

The optimizer solves allocation GLOBALLY (maximize total fit_score *
accept_probability subject to capacity, one-internship-per-candidate, and
reservation constraints). This module therefore never claims a candidate
was "rejected because of score" -- it reports the comparative evidence and
explicitly notes that the true joint tradeoff cannot be reconstructed from
stored output alone.
"""

import os
import pandas as pd


DEMO_DATA_DIR = "../demoData"

CANDIDATES_PATH = os.path.join(DEMO_DATA_DIR, "candidates.csv")
INTERNSHIPS_PATH = os.path.join(DEMO_DATA_DIR, "internships.csv")
ELIGIBLE_PAIRS_PATH = os.path.join(DEMO_DATA_DIR, "eligible_pairs.csv")
SCORED_PAIRS_PATH = os.path.join(DEMO_DATA_DIR, "scored_pairs.csv")
SCORED_WITH_PROB_PATH = os.path.join(DEMO_DATA_DIR, "scored_pairs_with_probability.csv")
FINAL_ALLOCATION_PATH = os.path.join(DEMO_DATA_DIR, "final_allocation.csv")
ALLOCATION_AUDIT_PATH = os.path.join(DEMO_DATA_DIR, "allocation_audit.csv")

EXPLANATIONS_OUTPUT_PATH = os.path.join(DEMO_DATA_DIR, "explanations.csv")

# Mirrors the hard-coded thresholds actually enforced in eligibility.py's
# is_eligible(). Named constants here (not re-derived from data) so this
# reasoning is provably the same rule the pipeline used. eligibility.py
# itself is not imported, run, or modified.
MIN_QUALIFICATION_SCORE = 55
MIN_SKILL_OVERLAP = 1

UNAVAILABLE = "UNAVAILABLE"


class ExplainabilityError(Exception):
    """Raised for clearly-identified error conditions (candidate/internship
    id not found). Not used for broad/silent exception swallowing."""
    pass


# ---------------------------------------------------------------------------
# Data loading -- read-only, no fallback to final_allocation_updated.csv
# ---------------------------------------------------------------------------

def _try_read_csv(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def _load_data():
    """Loads every pipeline output this module is allowed to read. Each
    entry may be None if that file doesn't exist -- callers must handle
    that explicitly rather than crashing or fabricating a value."""
    return {
        "candidates": _try_read_csv(CANDIDATES_PATH),
        "internships": _try_read_csv(INTERNSHIPS_PATH),
        "eligible_pairs": _try_read_csv(ELIGIBLE_PAIRS_PATH),
        "scored_pairs": _try_read_csv(SCORED_PAIRS_PATH),
        "scored_with_prob": _try_read_csv(SCORED_WITH_PROB_PATH),
        "final_allocation": _try_read_csv(FINAL_ALLOCATION_PATH),
        "allocation_audit": _try_read_csv(ALLOCATION_AUDIT_PATH),
    }


def _safe(value):
    """NaN/missing -> UNAVAILABLE instead of raw NaN/crash."""
    if value is None:
        return UNAVAILABLE
    if isinstance(value, str) and value.strip() == "":
        return UNAVAILABLE
    try:
        if pd.isna(value):
            return UNAVAILABLE
    except (TypeError, ValueError):
        pass
    return value


def _safe_float(value):
    """Best-effort float conversion. Returns None (not a crash) if the
    value is missing, NaN, empty, or not numeric."""
    v = _safe(value)
    if v == UNAVAILABLE:
        return None
    try:
        f = float(v)
        if f != f:  # NaN check without importing math
            return None
        return f
    except (TypeError, ValueError):
        return None


def _get_col(row, col_name):
    """Safe column access on a pandas Series/row. Returns UNAVAILABLE
    (never raises KeyError/AttributeError) if the column is absent or the
    row itself is missing."""
    if row is None:
        return UNAVAILABLE
    try:
        if col_name not in row.index:
            return UNAVAILABLE
        return _safe(row[col_name])
    except (AttributeError, KeyError, TypeError):
        return UNAVAILABLE


def _get_row(df, key_col, key_val):
    """Safe single-row lookup by key_col == key_val. Returns None if the
    dataframe, key column, or matching row is missing -- never raises
    KeyError. If more than one row matches, returns the first row AND a
    duplicate flag so callers can report the inconsistency rather than
    silently picking one."""
    if df is None or key_col not in df.columns:
        return None, False
    matches = df[df[key_col] == key_val]
    if matches.empty:
        return None, False
    return matches.iloc[0], len(matches) > 1


def _candidate_exists(data, candidate_id):
    if data["candidates"] is None or "candidate_id" not in data["candidates"].columns:
        return None
    return candidate_id in set(data["candidates"]["candidate_id"])


def _internship_exists(data, internship_id):
    if data["internships"] is None or "internship_id" not in data["internships"].columns:
        return None
    return internship_id in set(data["internships"]["internship_id"])


# ---------------------------------------------------------------------------
# Audit history -- deterministic, chronological
# ---------------------------------------------------------------------------

def get_candidate_history(candidate_id, audit_df):
    """
    Returns all audit records associated with candidate_id (as
    candidate_id, declined_candidate_id, or replacement_candidate_id),
    ordered chronologically by timestamp when every matched timestamp
    parses cleanly. Falls back to original row order (never a fabricated
    order) if timestamps are missing or malformed.
    """
    empty_cols = ["timestamp", "event_type", "candidate_id", "internship_id",
                  "previous_status", "new_status", "declined_candidate_id",
                  "replacement_candidate_id"]
    if audit_df is None or audit_df.empty:
        return pd.DataFrame(columns=empty_cols)

    mask = pd.Series(False, index=audit_df.index)
    for col in ("candidate_id", "declined_candidate_id", "replacement_candidate_id"):
        if col in audit_df.columns:
            mask = mask | (audit_df[col] == candidate_id)

    history = audit_df[mask].copy()
    if "timestamp" in history.columns and not history.empty:
        try:
            parsed = pd.to_datetime(history["timestamp"], errors="coerce", utc=True)
            if parsed.notna().all():
                history = history.assign(_ts=parsed).sort_values("_ts").drop(columns=["_ts"])
        except (TypeError, ValueError):
            pass

    return history.reset_index(drop=True)


def _render_history_narrative(candidate_id, history):
    """Turns audit rows into FACT-grounded plain-English sentences using
    only fields present in the audit schema. Never invents a reason."""
    lines = []
    for _, rec in history.iterrows():
        event_type = _safe(rec.get("event_type"))
        rec_candidate = _safe(rec.get("candidate_id"))
        internship_id = _safe(rec.get("internship_id"))
        prev_status = _safe(rec.get("previous_status"))
        new_status = _safe(rec.get("new_status"))
        declined_id = _safe(rec.get("declined_candidate_id"))
        replacement_id = _safe(rec.get("replacement_candidate_id"))

        if event_type == "DECLINE" and rec_candidate == candidate_id:
            lines.append(
                f"Candidate previously allocated to {internship_id}; "
                f"declined the allocation ({prev_status} -> {new_status})."
            )
        elif event_type == "REALLOCATION" and rec_candidate == candidate_id:
            if declined_id != UNAVAILABLE and declined_id:
                lines.append(
                    f"Candidate was previously unallocated and was subsequently "
                    f"selected as the replacement for the vacancy at {internship_id} "
                    f"created by {declined_id}'s decline ({prev_status} -> {new_status})."
                )
            else:
                lines.append(
                    f"Candidate was subsequently allocated to {internship_id} "
                    f"({prev_status} -> {new_status})."
                )
        elif event_type == "REALLOCATION" and replacement_id == candidate_id and rec_candidate != candidate_id:
            lines.append(
                f"Candidate is referenced as the replacement selected for "
                f"{internship_id} in this audit record."
            )
        elif event_type == "REALLOCATION" and declined_id == candidate_id and rec_candidate != candidate_id:
            lines.append(
                f"The vacancy at {internship_id} created by this candidate's decline "
                f"was subsequently filled by {rec_candidate}."
            )
        else:
            lines.append(
                f"Audit record: event_type={event_type}, internship_id={internship_id}, "
                f"previous_status={prev_status}, new_status={new_status}."
            )
    return lines


# ---------------------------------------------------------------------------
# Eligibility evidence (FACTs only, mirrors eligibility.py's actual rules)
# ---------------------------------------------------------------------------

def _eligibility_evidence(candidate_id, internship_id, data):
    """Returns the per-criterion PASS/FAIL/UNAVAILABLE evidence for the
    THREE BASE eligibility rules actually enforced by eligibility.py:
    qualification score, location match, skill overlap. Reservation is
    deliberately NOT part of base eligibility here -- it is enforced by
    optimizer.py as a separate hard constraint (see _reservation_evidence)
    and must never be folded into this function's "eligible" flag, or the
    module would misreport which layer produced a given infeasibility.

    Never raises KeyError: if a required column or row is missing, that
    criterion's status becomes UNAVAILABLE rather than crashing or being
    silently treated as PASS/FAIL.
    """
    cand_row, _ = _get_row(data["candidates"], "candidate_id", candidate_id)
    intern_row, _ = _get_row(data["internships"], "internship_id", internship_id)

    def _criterion_unavailable(note):
        return {"status": UNAVAILABLE, "note": note}

    if cand_row is None:
        qualification = _criterion_unavailable("Candidate row not found in candidates.csv.")
        location = _criterion_unavailable("Candidate row not found in candidates.csv.")
        skill_overlap = _criterion_unavailable("Candidate row not found in candidates.csv.")
        return {"qualification": qualification, "location": location,
                "skill_overlap": skill_overlap, "eligible": None}
    if intern_row is None:
        note = "Internship row not found in internships.csv."
        return {"qualification": _criterion_unavailable(note), "location": _criterion_unavailable(note),
                "skill_overlap": _criterion_unavailable(note), "eligible": None}

    # --- qualification ---
    qual_score = _safe_float(_get_col(cand_row, "qualification_score"))
    if qual_score is None:
        qualification = {"status": UNAVAILABLE, "candidate_value": _get_col(cand_row, "qualification_score"),
                          "required_minimum": MIN_QUALIFICATION_SCORE,
                          "note": "qualification_score missing or non-numeric."}
        qual_pass = None
    else:
        qual_pass = bool(qual_score >= MIN_QUALIFICATION_SCORE)
        qualification = {"status": "PASS" if qual_pass else "FAIL",
                          "candidate_value": qual_score, "required_minimum": MIN_QUALIFICATION_SCORE}

    # --- location ---
    cand_location = _get_col(cand_row, "location_pref")
    intern_location = _get_col(intern_row, "location")
    if cand_location == UNAVAILABLE or intern_location == UNAVAILABLE:
        location = {"status": UNAVAILABLE, "candidate_location_pref": cand_location,
                    "internship_location": intern_location, "note": "location_pref/location missing."}
        location_pass = None
    else:
        location_pass = bool(cand_location == intern_location)
        location = {"status": "PASS" if location_pass else "FAIL",
                    "candidate_location_pref": cand_location, "internship_location": intern_location}

    # --- skill overlap ---
    cand_skills_raw = _get_col(cand_row, "skills")
    required_skills_raw = _get_col(intern_row, "required_skills")
    if cand_skills_raw == UNAVAILABLE or required_skills_raw == UNAVAILABLE:
        skill_overlap = {"status": UNAVAILABLE, "note": "skills/required_skills missing."}
        skill_pass = None
    else:
        cand_skills = set(s.strip() for s in str(cand_skills_raw).split(",") if s.strip())
        required_skills = set(s.strip() for s in str(required_skills_raw).split(",") if s.strip())
        overlap = cand_skills & required_skills
        skill_pass = bool(len(overlap) >= MIN_SKILL_OVERLAP)
        skill_overlap = {"status": "PASS" if skill_pass else "FAIL",
                          "candidate_skills": sorted(cand_skills), "required_skills": sorted(required_skills),
                          "overlapping_skills": sorted(overlap), "required_minimum_overlap": MIN_SKILL_OVERLAP}

    # eligible is None (unknown) if any criterion could not be evaluated,
    # rather than silently defaulting to True or False.
    if qual_pass is None or location_pass is None or skill_pass is None:
        eligible = None
    else:
        eligible = qual_pass and location_pass and skill_pass

    return {"qualification": qualification, "location": location,
            "skill_overlap": skill_overlap, "eligible": eligible}


def _reservation_evidence(candidate_id, internship_id, data):
    """Evaluates the RESERVATION constraint -- a SEPARATE hard constraint
    enforced by optimizer.py, independent of base eligibility. Never
    raises KeyError on missing columns/rows."""
    intern_row, _ = _get_row(data["internships"], "internship_id", internship_id)
    if intern_row is None:
        return {"requirement": None, "status": UNAVAILABLE,
                "note": "Internship row not found in internships.csv."}

    reserved_cat = _get_col(intern_row, "reserved_category")
    if reserved_cat == UNAVAILABLE:
        return {"requirement": None, "status": "NO RESERVATION"}

    cand_row, _ = _get_row(data["candidates"], "candidate_id", candidate_id)
    if cand_row is None:
        return {"requirement": reserved_cat, "status": UNAVAILABLE,
                "note": "Candidate row not found in candidates.csv; reservation compliance cannot be confirmed."}

    cand_cat = _get_col(cand_row, "category")
    if cand_cat == UNAVAILABLE:
        return {"requirement": reserved_cat, "status": UNAVAILABLE,
                "note": "Candidate category is missing; reservation compliance cannot be confirmed."}

    satisfied = bool(cand_cat == reserved_cat)
    return {
        "requirement": reserved_cat,
        "candidate_category": cand_cat,
        "status": "SATISFIED" if satisfied else "NOT ELIGIBLE FOR THIS RESERVED INTERNSHIP",
    }


def _match_quality(candidate_id, internship_id, data):
    """Reads skill_match_pct/fit_score from scored_pairs.csv and
    accept_probability from scored_pairs_with_probability.csv. Never
    raises on missing columns/rows/malformed numbers; reports UNAVAILABLE
    instead. Flags duplicate (candidate, internship) rows in either
    source rather than silently using the first one, since silently
    picking one hides a real data-integrity problem."""
    result = {"skill_match_pct": UNAVAILABLE, "fit_score": UNAVAILABLE,
              "accept_probability": UNAVAILABLE, "utility": UNAVAILABLE,
              "duplicate_scored_pairs": False, "duplicate_scored_with_prob": False}

    if data["scored_pairs"] is not None and {"candidate_id", "internship_id"}.issubset(data["scored_pairs"].columns):
        matches = data["scored_pairs"][
            (data["scored_pairs"]["candidate_id"] == candidate_id)
            & (data["scored_pairs"]["internship_id"] == internship_id)
        ]
        if not matches.empty:
            row = matches.iloc[0]
            result["skill_match_pct"] = _get_col(row, "skill_match_pct")
            result["fit_score"] = _get_col(row, "fit_score")
            result["duplicate_scored_pairs"] = len(matches) > 1

    if data["scored_with_prob"] is not None and {"candidate_id", "internship_id"}.issubset(data["scored_with_prob"].columns):
        matches = data["scored_with_prob"][
            (data["scored_with_prob"]["candidate_id"] == candidate_id)
            & (data["scored_with_prob"]["internship_id"] == internship_id)
        ]
        if not matches.empty:
            row = matches.iloc[0]
            result["accept_probability"] = _get_col(row, "accept_probability")
            result["duplicate_scored_with_prob"] = len(matches) > 1

    fit_f = _safe_float(result["fit_score"])
    prob_f = _safe_float(result["accept_probability"])
    if fit_f is not None and prob_f is not None:
        result["utility"] = round(fit_f * prob_f, 2)

    return result


def _capacity_context(internship_id, data):
    """Never raises on missing/malformed capacity. capacity_known is False
    if capacity could not be parsed as a non-negative number, so callers
    can avoid claiming "capacity is full" without proof."""
    intern_row, _ = _get_row(data["internships"], "internship_id", internship_id)
    if intern_row is None:
        return {"capacity": UNAVAILABLE, "capacity_known": False, "filled": 0,
                "selected_candidates": [], "capacity_full": False}

    capacity_raw = _get_col(intern_row, "capacity")
    capacity_val = _safe_float(capacity_raw)
    capacity_known = capacity_val is not None and capacity_val >= 0

    filled_candidates = []
    if data["final_allocation"] is not None and {"candidate_id", "internship_id"}.issubset(data["final_allocation"].columns):
        alloc_df = data["final_allocation"]
        filled_candidates = alloc_df[alloc_df["internship_id"] == internship_id]["candidate_id"].tolist()

    capacity_full = bool(capacity_known and len(filled_candidates) >= capacity_val)

    return {
        "capacity": capacity_raw if capacity_known else UNAVAILABLE,
        "capacity_known": capacity_known,
        "filled": len(filled_candidates),
        "selected_candidates": filled_candidates,
        "capacity_full": capacity_full,
    }


# ---------------------------------------------------------------------------
# explain_pair -- the main pairwise explainability function
# ---------------------------------------------------------------------------

def explain_pair(candidate_id, internship_id, data=None):
    """
    Explains WHY candidate_id was or was not allocated to internship_id.
    Read-only; runs no optimization; makes no decision. Raises
    ExplainabilityError if either id cannot be verified.

    Decision values:
        DATA INCONSISTENCY                      -- stored evidence disagrees with itself
        NOT ELIGIBLE                             -- fails base eligibility (qual/location/skills)
        ELIGIBLE BUT INFEASIBLE DUE TO RESERVATION -- passes base eligibility, fails reservation
        SELECTED                                 -- currently allocated, evidence consistent
        ELIGIBLE BUT NOT SELECTED                -- feasible, but not in final_allocation.csv
    """
    if data is None:
        data = _load_data()

    cand_exists = _candidate_exists(data, candidate_id)
    if cand_exists is False:
        raise ExplainabilityError(f"Candidate '{candidate_id}' does not exist in {CANDIDATES_PATH}")
    if cand_exists is None:
        raise ExplainabilityError(f"Cannot verify candidate: {CANDIDATES_PATH} is missing")

    intern_exists = _internship_exists(data, internship_id)
    if intern_exists is False:
        raise ExplainabilityError(f"Internship '{internship_id}' does not exist in {INTERNSHIPS_PATH}")
    if intern_exists is None:
        raise ExplainabilityError(f"Cannot verify internship: {INTERNSHIPS_PATH} is missing")

    eligibility = _eligibility_evidence(candidate_id, internship_id, data)
    reservation = _reservation_evidence(candidate_id, internship_id, data)
    capacity_ctx = _capacity_context(internship_id, data)
    match_quality = _match_quality(candidate_id, internship_id, data)

    inconsistencies = []

    # FACT: is this pair recorded as eligible by eligibility.py's own output?
    eligible_pair_recorded = None
    eligible_pairs_dup = False
    if data["eligible_pairs"] is not None and {"candidate_id", "internship_id"}.issubset(data["eligible_pairs"].columns):
        matches = data["eligible_pairs"][
            (data["eligible_pairs"]["candidate_id"] == candidate_id)
            & (data["eligible_pairs"]["internship_id"] == internship_id)
        ]
        eligible_pair_recorded = not matches.empty
        eligible_pairs_dup = len(matches) > 1
    if eligible_pairs_dup:
        inconsistencies.append(
            f"eligible_pairs.csv contains duplicate rows for ({candidate_id}, {internship_id})."
        )

    # FACT: is this the candidate's current allocation?
    currently_selected = False
    final_alloc_dup = False
    if data["final_allocation"] is not None and {"candidate_id", "internship_id"}.issubset(data["final_allocation"].columns):
        alloc_df = data["final_allocation"]
        row = alloc_df[(alloc_df["candidate_id"] == candidate_id) & (alloc_df["internship_id"] == internship_id)]
        currently_selected = not row.empty
        # candidate appearing more than once anywhere in final_allocation.csv
        # is a structural integrity problem regardless of this specific pair
        final_alloc_dup = int((alloc_df["candidate_id"] == candidate_id).sum()) > 1
    if final_alloc_dup:
        inconsistencies.append(
            f"final_allocation.csv contains more than one row for candidate {candidate_id}."
        )

    if match_quality.get("duplicate_scored_pairs"):
        inconsistencies.append(
            f"scored_pairs.csv contains duplicate rows for ({candidate_id}, {internship_id})."
        )
    if match_quality.get("duplicate_scored_with_prob"):
        inconsistencies.append(
            f"scored_pairs_with_probability.csv contains duplicate rows for ({candidate_id}, {internship_id})."
        )

    base_eligible = eligibility["eligible"]  # True / False / None (unknown)

    # Cross-check independently-derived base eligibility against
    # eligibility.py's own recorded output, when both are knowable.
    if base_eligible is not None and eligible_pair_recorded is not None and base_eligible != eligible_pair_recorded:
        inconsistencies.append(
            f"Independently derived eligibility evidence says "
            f"{'PASS' if base_eligible else 'FAIL'}, but eligible_pairs.csv "
            f"{'contains' if eligible_pair_recorded else 'does not contain'} this pair."
        )

    reservation_incompatible = reservation.get("status") == "NOT ELIGIBLE FOR THIS RESERVED INTERNSHIP"

    # A pair that is currently SELECTED must be consistent with base
    # eligibility and reservation feasibility -- if not, that is a data
    # inconsistency, not a normal explainable allocation.
    if currently_selected and base_eligible is False:
        inconsistencies.append(
            f"Candidate is currently allocated to {internship_id} in final_allocation.csv, "
            f"but independently derived evidence shows the pair fails base eligibility."
        )
    if currently_selected and reservation_incompatible:
        inconsistencies.append(
            f"Candidate is currently allocated to {internship_id} in final_allocation.csv, "
            f"but the internship's reservation requirement is not satisfied by this candidate."
        )

    result = {
        "candidate_id": candidate_id,
        "internship_id": internship_id,
        "eligibility": eligibility,
        "eligible_pair_on_record": eligible_pair_recorded,
        "reservation": reservation,
        "capacity": capacity_ctx,
        "match_quality": match_quality if base_eligible else None,
        "data_warnings": inconsistencies,
    }

    if inconsistencies:
        result["decision"] = "DATA INCONSISTENCY"
        result["interpretation"] = (
            "The stored evidence for this candidate/internship pair is internally "
            "inconsistent: " + " ".join(inconsistencies) + " This is reported rather "
            "than silently resolved, so the underlying data can be investigated."
        )
        return result

    if base_eligible is None:
        result["decision"] = "INFORMATION UNAVAILABLE"
        result["interpretation"] = (
            "Base eligibility (qualification, location, skill overlap) could not be "
            "fully evaluated because required candidate or internship data is missing."
        )
        return result

    if not base_eligible:
        result["decision"] = "NOT ELIGIBLE"
        result["match_quality"] = None
        result["interpretation"] = (
            "Candidate-internship pair failed at least one base eligibility "
            "constraint (qualification, location, or skill overlap) and therefore "
            "could not be selected by the optimizer."
        )
        return result

    if reservation_incompatible:
        result["decision"] = "ELIGIBLE BUT INFEASIBLE DUE TO RESERVATION"
        result["interpretation"] = (
            f"Candidate {candidate_id} passes base eligibility (qualification, location, "
            f"skill overlap) for {internship_id}, but this internship is reserved for "
            f"category '{reservation.get('requirement')}' and the candidate's category "
            f"does not match. Reservation is a separate hard constraint enforced by "
            f"optimizer.py, distinct from base eligibility -- this pair was infeasible "
            f"for the optimizer regardless of fit score or acceptance probability."
        )
        return result

    if currently_selected:
        result["decision"] = "SELECTED"
        result["interpretation"] = (
            f"Candidate {candidate_id} is currently allocated to {internship_id}. "
            f"This is consistent with the pair being eligible and reservation-compliant; "
            f"the underlying fit score and acceptance probability are relevant to the "
            f"global objective but the exact joint tradeoff against every other feasible "
            f"allocation is not individually reconstructable from stored output."
        )
        return result

    # ELIGIBLE BUT NOT SELECTED
    result["decision"] = "ELIGIBLE BUT NOT SELECTED"
    competitor_rows = []
    for sel_cid in capacity_ctx["selected_candidates"]:
        mq = _match_quality(sel_cid, internship_id, data)
        competitor_rows.append({"candidate_id": sel_cid, **mq})
    result["selected_competitors"] = competitor_rows

    if capacity_ctx["capacity_known"] and capacity_ctx["capacity_full"]:
        capacity_clause = (
            f"Current capacity is {capacity_ctx['filled']}/{capacity_ctx['capacity']} "
            f"and is full."
        )
    elif capacity_ctx["capacity_known"]:
        capacity_clause = (
            f"Current capacity is {capacity_ctx['filled']}/{capacity_ctx['capacity']} "
            f"and is not full."
        )
    else:
        capacity_clause = "Current capacity could not be determined from stored data."

    result["interpretation"] = (
        f"Candidate {candidate_id} was eligible for {internship_id} but is not present "
        f"in the final allocation. {capacity_clause} Other selected candidates and their "
        f"objective values are shown as comparative evidence. Because the optimizer "
        f"solves globally, the exact counterfactual reason for this non-selection "
        f"cannot be proven from stored output alone."
    )
    result["limitation"] = (
        "The optimizer solves the allocation globally (maximizing total "
        "fit_score * accept_probability subject to capacity, one-internship-"
        "per-candidate, and reservation constraints), so any comparison shown "
        "here is descriptive evidence, not a proof of the exact counterfactual "
        "tradeoff that determined this specific non-selection."
    )
    return result


# ---------------------------------------------------------------------------
# explain_candidate -- overall candidate-level explanation
# ---------------------------------------------------------------------------

def explain_candidate(candidate_id, data=None):
    """
    Master entry point for `python explainability.py <candidate_id>`.
    Determines current allocation status and, if unallocated, reports
    eligible-options evidence. Raises ExplainabilityError if the candidate
    id cannot be verified.
    """
    if data is None:
        data = _load_data()

    cand_exists = _candidate_exists(data, candidate_id)
    if cand_exists is False:
        raise ExplainabilityError(f"Candidate '{candidate_id}' does not exist in {CANDIDATES_PATH}")
    if cand_exists is None:
        raise ExplainabilityError(f"Cannot verify candidate: {CANDIDATES_PATH} is missing")

    history = get_candidate_history(candidate_id, data["allocation_audit"])
    history_narrative = _render_history_narrative(candidate_id, history)

    if data["final_allocation"] is None:
        return {
            "candidate_id": candidate_id, "status": "UNKNOWN",
            "history_narrative": history_narrative,
            "note": f"{FINAL_ALLOCATION_PATH} is missing; current status cannot be determined.",
        }

    alloc_df = data["final_allocation"]
    if "candidate_id" not in alloc_df.columns or "internship_id" not in alloc_df.columns:
        return {
            "candidate_id": candidate_id, "status": "UNKNOWN",
            "history_narrative": history_narrative,
            "note": f"{FINAL_ALLOCATION_PATH} is missing expected columns; current status cannot be determined.",
        }

    dup_count = int((alloc_df["candidate_id"] == candidate_id).sum())
    if dup_count > 1:
        return {
            "candidate_id": candidate_id, "status": "DATA INCONSISTENCY",
            "history_narrative": history_narrative,
            "note": f"Candidate appears {dup_count} times in {FINAL_ALLOCATION_PATH}; "
                    f"violates one-internship-per-candidate. Not resolved automatically.",
        }

    row = alloc_df[alloc_df["candidate_id"] == candidate_id]
    if not row.empty:
        internship_id = row.iloc[0]["internship_id"]
        pair_explanation = explain_pair(candidate_id, internship_id, data=data)
        return {
            "candidate_id": candidate_id,
            "status": "ALLOCATED" if pair_explanation["decision"] != "DATA INCONSISTENCY" else "DATA INCONSISTENCY",
            "internship_id": internship_id,
            "pair_explanation": pair_explanation,
            "history_narrative": history_narrative,
        }

    # NOT ALLOCATED -- report eligible-options evidence, never invent a reason
    result = {"candidate_id": candidate_id, "status": "NOT ALLOCATED", "history_narrative": history_narrative}

    if data["eligible_pairs"] is None:
        result["reason"] = f"{ELIGIBLE_PAIRS_PATH} is missing; cannot determine eligible options."
        return result
    if not {"candidate_id", "internship_id"}.issubset(data["eligible_pairs"].columns):
        result["reason"] = f"{ELIGIBLE_PAIRS_PATH} is missing expected columns; cannot determine eligible options."
        return result

    eligible_rows = data["eligible_pairs"][data["eligible_pairs"]["candidate_id"] == candidate_id]
    eligible_internships = eligible_rows["internship_id"].tolist()
    dup_pairs = eligible_rows["internship_id"].duplicated().any()
    result["eligible_option_count"] = len(set(eligible_internships))
    if dup_pairs:
        result["data_warning"] = (
            f"{ELIGIBLE_PAIRS_PATH} contains duplicate rows for one or more of this "
            f"candidate's eligible internships."
        )

    if len(eligible_internships) == 0:
        result["reason"] = "Candidate had no eligible internship pairs under the project's eligibility rules."
        return result

    result["reason"] = "Candidate had eligible internship options but was not included in the final global allocation."
    options = []
    for iid in sorted(set(eligible_internships)):
        mq = _match_quality(candidate_id, iid, data)
        options.append({"internship_id": iid, **mq})
    result["eligible_options"] = options
    result["limitation"] = (
        "The exact counterfactual reason this candidate was not selected for any "
        "of these eligible internships cannot be proven from stored output alone; "
        "the optimizer decides globally across all candidates and internships."
    )
    return result


# ---------------------------------------------------------------------------
# Human-readable CLI rendering
# ---------------------------------------------------------------------------

def _fmt_history(history_narrative):
    if not history_narrative:
        return ["No allocation audit event was found for this candidate."]
    return history_narrative


def render_candidate_explanation(explanation):
    lines = ["=" * 50, "CANDIDATE ALLOCATION EXPLANATION", "=" * 50, "",
             f"Candidate: {explanation['candidate_id']}", ""]

    status = explanation["status"]
    lines.append("CURRENT STATUS:")
    lines.append(status)
    lines.append("")

    if status in ("ALLOCATED", "DATA INCONSISTENCY") and "pair_explanation" in explanation:
        lines.append("CURRENT INTERNSHIP:")
        lines.append(str(explanation["internship_id"]))
        lines.append("")
        pe = explanation["pair_explanation"]
        lines.append("-" * 50)
        lines.append("EVIDENCE FOR THIS ALLOCATION")
        lines.append("-" * 50)
        lines.extend(_render_pair_body(pe))
    elif status == "NOT ALLOCATED":
        lines.append("REASON:")
        lines.append(explanation.get("reason", UNAVAILABLE))
        lines.append("")
        if "eligible_option_count" in explanation:
            lines.append(f"ELIGIBLE OPTIONS: {explanation['eligible_option_count']}")
            for opt in explanation.get("eligible_options", []):
                lines.append(
                    f"  {opt['internship_id']}: fit_score={opt['fit_score']}, "
                    f"accept_probability={opt['accept_probability']}, utility={opt['utility']}"
                )
            lines.append("")
        if explanation.get("limitation"):
            lines.append("LIMITATION:")
            lines.append(explanation["limitation"])
            lines.append("")
    else:
        lines.append("NOTE:")
        lines.append(explanation.get("note", UNAVAILABLE))
        lines.append("")

    lines.append("-" * 50)
    lines.append("AUDIT HISTORY")
    lines.append("-" * 50)
    for item in _fmt_history(explanation.get("history_narrative")):
        lines.append(f"- {item}")
    lines.append("=" * 50)
    return "\n".join(lines)


def _render_pair_body(pe):
    lines = []
    if pe.get("data_warnings"):
        lines.append("")
        lines.append("DATA WARNINGS:")
        for w in pe["data_warnings"]:
            lines.append(f"- {w}")

    e = pe["eligibility"]
    lines.append("")
    lines.append("1. ELIGIBILITY (base rules: qualification, location, skills)")
    lines.append(f"Qualification: {e['qualification']['status']} "
                 f"(candidate={e['qualification'].get('candidate_value')}, "
                 f"required>={e['qualification'].get('required_minimum')})")
    lines.append(f"Location: {e['location']['status']} "
                 f"(candidate pref={e['location'].get('candidate_location_pref')}, "
                 f"internship location={e['location'].get('internship_location')})")
    lines.append(f"Skills: {e['skill_overlap']['status']} "
                 f"(shared={e['skill_overlap'].get('overlapping_skills')})")
    lines.append("")

    if pe.get("match_quality"):
        mq = pe["match_quality"]
        lines.append("2. MATCH QUALITY")
        lines.append(f"Skill Match: {mq['skill_match_pct']}")
        lines.append(f"Fuzzy Fit Score: {mq['fit_score']}")
        lines.append(f"Acceptance Probability: {mq['accept_probability']}")
        lines.append(f"Objective Utility (fit_score * accept_probability): {mq['utility']}")
        lines.append("")

    r = pe["reservation"]
    lines.append("3. RESERVATION (separate hard constraint enforced by optimizer.py)")
    if r["status"] == "NO RESERVATION":
        lines.append("No reserved category.")
    else:
        lines.append(f"Requirement: {r.get('requirement')}")
        lines.append(f"Status: {r['status']}")
    lines.append("")

    cap = pe["capacity"]
    lines.append("4. INTERNSHIP CAPACITY")
    lines.append(f"Capacity: {cap['capacity']}")
    lines.append(f"Filled: {cap['filled']}")
    lines.append(f"Selected candidates: {cap['selected_candidates']}")
    lines.append("")

    lines.append("5. DECISION")
    lines.append(pe["decision"])
    lines.append("")
    if pe.get("selected_competitors"):
        lines.append("SELECTED COMPETITORS (comparative evidence, not proof of causality):")
        for comp in pe["selected_competitors"]:
            lines.append(
                f"  {comp['candidate_id']}: fit_score={comp['fit_score']}, "
                f"accept_probability={comp['accept_probability']}, utility={comp['utility']}"
            )
        lines.append("")
    lines.append("INTERPRETATION:")
    lines.append(pe.get("interpretation", UNAVAILABLE))
    if pe.get("limitation"):
        lines.append("")
        lines.append("LIMITATION:")
        lines.append(pe["limitation"])
    return lines


def render_pair_explanation(pe, history_narrative=None):
    lines = ["=" * 50, "ALLOCATION DECISION EXPLANATION", "=" * 50, "",
             f"Candidate: {pe['candidate_id']}", f"Internship: {pe['internship_id']}", "",
             "DECISION:", pe["decision"]]
    lines.append("-" * 50)
    lines.extend(_render_pair_body(pe))
    lines.append("")
    lines.append("-" * 50)
    lines.append("6. AUDIT HISTORY")
    lines.append("-" * 50)
    for item in _fmt_history(history_narrative or []):
        lines.append(f"- {item}")
    lines.append("=" * 50)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Machine-readable bulk output: demoData/explanations.csv
# ---------------------------------------------------------------------------

def generate_explanations_csv(data=None):
    """
    Writes demoData/explanations.csv with one row per (candidate, current
    or best-known internship) combination this module can explain.
    Read-only over the pipeline outputs; never writes to
    final_allocation.csv or allocation_audit.csv.
    """
    if data is None:
        data = _load_data()

    if data["candidates"] is None:
        raise ExplainabilityError(f"Cannot generate explanations.csv: {CANDIDATES_PATH} is missing")

    rows = []
    for candidate_id in data["candidates"]["candidate_id"]:
        explanation = explain_candidate(candidate_id, data=data)
        history_narrative = explanation.get("history_narrative", [])
        audit_history_str = " | ".join(history_narrative) if history_narrative else UNAVAILABLE

        if "pair_explanation" in explanation:
            pe = explanation["pair_explanation"]
            mq = pe.get("match_quality") or {}
            rows.append({
                "candidate_id": candidate_id,
                "internship_id": explanation["internship_id"],
                "highest_utility_eligible_internship_id": UNAVAILABLE,
                "internship_id_basis": "current allocation (final_allocation.csv)",
                "decision": pe["decision"],
                "eligibility_status": (
                    "PASS" if pe["eligibility"]["eligible"] is True
                    else "FAIL" if pe["eligibility"]["eligible"] is False
                    else UNAVAILABLE
                ),
                "qualification_status": pe["eligibility"]["qualification"]["status"],
                "location_status": pe["eligibility"]["location"]["status"],
                "skill_status": pe["eligibility"]["skill_overlap"]["status"],
                "skill_match_pct": mq.get("skill_match_pct", UNAVAILABLE),
                "fit_score": mq.get("fit_score", UNAVAILABLE),
                "accept_probability": mq.get("accept_probability", UNAVAILABLE),
                "allocation_utility": mq.get("utility", UNAVAILABLE),
                "reservation_status": pe["reservation"]["status"],
                "internship_capacity": pe["capacity"]["capacity"],
                "internship_filled": pe["capacity"]["filled"],
                "selected_competitors": (
                    ", ".join(c["candidate_id"] for c in pe.get("selected_competitors", []))
                    if pe.get("selected_competitors") else UNAVAILABLE
                ),
                "decision_reason": pe.get("interpretation", UNAVAILABLE),
                "audit_history": audit_history_str,
                "limitation": pe.get("limitation") or ("; ".join(pe.get("data_warnings", [])) or ""),
            })
        elif explanation["status"] == "NOT ALLOCATED":
            # "highest_utility_eligible_internship_id" is purely descriptive:
            # the eligible internship with the highest independently-computed
            # fit_score * accept_probability among this candidate's OBSERVED
            # eligible options. It is NOT a recommendation, NOT what the
            # optimizer would have chosen, and NOT the internship the
            # candidate "should" have received -- the optimizer solves
            # globally and this module never recomputes its decision.
            best_option = None
            if explanation.get("eligible_options"):
                numeric_options = [o for o in explanation["eligible_options"] if o["utility"] != UNAVAILABLE]
                if numeric_options:
                    best_option = max(numeric_options, key=lambda o: o["utility"])
            rows.append({
                "candidate_id": candidate_id,
                "internship_id": UNAVAILABLE,
                "highest_utility_eligible_internship_id": best_option["internship_id"] if best_option else UNAVAILABLE,
                "internship_id_basis": (
                    "highest individual utility (fit_score * accept_probability) among "
                    "observed eligible options -- descriptive only, not a recommendation "
                    "and not the optimizer's decision"
                ) if best_option else UNAVAILABLE,
                "decision": "NOT ALLOCATED",
                "eligibility_status": UNAVAILABLE,
                "qualification_status": UNAVAILABLE,
                "location_status": UNAVAILABLE,
                "skill_status": UNAVAILABLE,
                "skill_match_pct": UNAVAILABLE,
                "fit_score": best_option["fit_score"] if best_option else UNAVAILABLE,
                "accept_probability": best_option["accept_probability"] if best_option else UNAVAILABLE,
                "allocation_utility": best_option["utility"] if best_option else UNAVAILABLE,
                "reservation_status": UNAVAILABLE,
                "internship_capacity": UNAVAILABLE,
                "internship_filled": UNAVAILABLE,
                "selected_competitors": UNAVAILABLE,
                "decision_reason": explanation.get("reason", UNAVAILABLE),
                "audit_history": audit_history_str,
                "limitation": explanation.get("limitation", "") or explanation.get("data_warning", ""),
            })
        else:
            rows.append({
                "candidate_id": candidate_id, "internship_id": UNAVAILABLE,
                "highest_utility_eligible_internship_id": UNAVAILABLE,
                "internship_id_basis": UNAVAILABLE,
                "decision": explanation["status"], "eligibility_status": UNAVAILABLE,
                "qualification_status": UNAVAILABLE, "location_status": UNAVAILABLE,
                "skill_status": UNAVAILABLE, "skill_match_pct": UNAVAILABLE,
                "fit_score": UNAVAILABLE, "accept_probability": UNAVAILABLE,
                "allocation_utility": UNAVAILABLE, "reservation_status": UNAVAILABLE,
                "internship_capacity": UNAVAILABLE, "internship_filled": UNAVAILABLE,
                "selected_competitors": UNAVAILABLE,
                "decision_reason": explanation.get("note", UNAVAILABLE),
                "audit_history": audit_history_str, "limitation": "",
            })

    out_df = pd.DataFrame(rows, columns=[
        "candidate_id", "internship_id", "highest_utility_eligible_internship_id",
        "internship_id_basis", "decision", "eligibility_status",
        "qualification_status", "location_status", "skill_status",
        "skill_match_pct", "fit_score", "accept_probability",
        "allocation_utility", "reservation_status", "internship_capacity",
        "internship_filled", "selected_competitors", "decision_reason",
        "audit_history", "limitation",
    ])
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    out_df.to_csv(EXPLANATIONS_OUTPUT_PATH, index=False)
    return out_df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) not in (2, 3):
        print("Usage: python explainability.py <candidate_id> [internship_id]")
        sys.exit(1)

    try:
        data = _load_data()
        if len(sys.argv) == 2:
            cid = sys.argv[1]
            explanation = explain_candidate(cid, data=data)
            print(render_candidate_explanation(explanation))
        else:
            cid, iid = sys.argv[1], sys.argv[2]
            pe = explain_pair(cid, iid, data=data)
            history = get_candidate_history(cid, data["allocation_audit"])
            narrative = _render_history_narrative(cid, history)
            print(render_pair_explanation(pe, history_narrative=narrative))
    except ExplainabilityError as e:
        print("=" * 50)
        print("ERROR")
        print("=" * 50)
        print(str(e))
        sys.exit(1)