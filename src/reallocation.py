"""
reallocation.py

Dynamic reallocation for the AI-based Smart Allocation Engine.

Handles the case where a candidate DECLINES an internship offer AFTER the
initial optimizer.py allocation has been produced. Rather than re-running
the full ILP over every candidate/internship, this module identifies the
single internship affected by the decline and re-optimizes only that
affected subset (the vacated internship + its still-unallocated eligible
candidates), reusing:

  - the same candidate/internship/eligibility data the rest of the
    pipeline already produced (demoData/candidates.csv,
    demoData/internships.csv, demoData/scored_pairs_with_probability.csv)
  - the same objective used by optimizer.py: fit_score * accept_probability
  - the same hard constraints enforced by optimizer.py: one internship per
    candidate, internship capacity, reserved-category restriction

"""

import os
import csv
from datetime import datetime, timezone
import pandas as pd
from ortools.sat.python import cp_model


DEMO_DATA_DIR = "../demoData"
ALLOCATION_PATH = os.path.join(DEMO_DATA_DIR, "final_allocation.csv")
CANDIDATES_PATH = os.path.join(DEMO_DATA_DIR, "candidates.csv")
INTERNSHIPS_PATH = os.path.join(DEMO_DATA_DIR, "internships.csv")
SCORED_PATH = os.path.join(DEMO_DATA_DIR, "scored_pairs_with_probability.csv")
OUTPUT_PATH = os.path.join(DEMO_DATA_DIR, "final_allocation.csv")
AUDIT_PATH = os.path.join(DEMO_DATA_DIR, "allocation_audit.csv")

AUDIT_COLUMNS = [
    "timestamp",
    "event_type",
    "candidate_id",
    "internship_id",
    "previous_status",
    "new_status",
    "declined_candidate_id",
    "replacement_candidate_id",
]


def _append_audit_records(records):
    """Append-only write to AUDIT_PATH. Creates the file with header if it
    does not exist yet; otherwise appends without touching prior rows.
    Only called after validation has already succeeded, so a failed
    reallocation never reaches this function."""
    file_exists = os.path.exists(AUDIT_PATH)
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    with open(AUDIT_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_COLUMNS)
        if not file_exists:
            writer.writeheader()
        for record in records:
            writer.writerow(record)


class ReallocationError(Exception):
    """Raised for clearly-identified error conditions (not used for
    generic/broad exception swallowing -- callers see exactly what failed)."""
    pass


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_required_data():
    missing = [p for p in (ALLOCATION_PATH, CANDIDATES_PATH, INTERNSHIPS_PATH, SCORED_PATH)
               if not os.path.exists(p)]
    if missing:
        raise ReallocationError(
            f"Required CSV file(s) missing: {missing}. "
            f"Run the existing pipeline (generate_data.py -> eligibility.py -> "
            f"fuzzy_scoring.py -> train_acceptance_model.py -> optimizer.py) first."
        )

    allocation_df = pd.read_csv(ALLOCATION_PATH)
    candidates_df = pd.read_csv(CANDIDATES_PATH)
    internships_df = pd.read_csv(INTERNSHIPS_PATH)
    scored_df = pd.read_csv(SCORED_PATH)

    required_alloc_cols = {"candidate_id", "internship_id", "fit_score", "accept_probability"}
    if not required_alloc_cols.issubset(allocation_df.columns):
        raise ReallocationError(
            f"{ALLOCATION_PATH} is malformed: expected columns {required_alloc_cols}, "
            f"found {list(allocation_df.columns)}"
        )

    return allocation_df, candidates_df, internships_df, scored_df


# ---------------------------------------------------------------------------
# Validation (run before ever writing final_allocation.csv)
# ---------------------------------------------------------------------------

def _validate_allocation(allocation_df, candidates_df, internships_df, declined_candidate_id):
    """Raises ReallocationError on any violation. Never silently writes an
    invalid result."""

    valid_candidate_ids = set(candidates_df["candidate_id"])
    valid_internship_ids = set(internships_df["internship_id"])

    # no invalid candidate/internship IDs
    bad_cands = set(allocation_df["candidate_id"]) - valid_candidate_ids
    if bad_cands:
        raise ReallocationError(f"Invalid candidate_id(s) in allocation: {bad_cands}")
    bad_interns = set(allocation_df["internship_id"]) - valid_internship_ids
    if bad_interns:
        raise ReallocationError(f"Invalid internship_id(s) in allocation: {bad_interns}")

    # no duplicate candidate assignments (each candidate <= 1 internship)
    dup = allocation_df["candidate_id"].value_counts()
    dup = dup[dup > 1]
    if len(dup) > 0:
        raise ReallocationError(f"Candidate(s) assigned to more than one internship: {list(dup.index)}")

    # declined candidate must not remain assigned
    if declined_candidate_id in set(allocation_df["candidate_id"]):
        raise ReallocationError(
            f"Validation failed: declined candidate {declined_candidate_id} still appears in allocation"
        )

    # capacity respected
    capacity_lookup = internships_df.set_index("internship_id")["capacity"]
    counts = allocation_df["internship_id"].value_counts()
    for intern_id, count in counts.items():
        if count > int(capacity_lookup[intern_id]):
            raise ReallocationError(
                f"Capacity violation: {intern_id} has {count} allocated, capacity is {capacity_lookup[intern_id]}"
            )

    # reserved-category restriction respected
    reserved_lookup = internships_df.set_index("internship_id")["reserved_category"]
    category_lookup = candidates_df.set_index("candidate_id")["category"]
    for _, row in allocation_df.iterrows():
        reserved_cat = reserved_lookup[row["internship_id"]]
        if pd.notna(reserved_cat):
            cand_cat = category_lookup[row["candidate_id"]]
            if cand_cat != reserved_cat:
                raise ReallocationError(
                    f"Reserved-category violation: candidate {row['candidate_id']} "
                    f"(category {cand_cat}) allocated to {row['internship_id']} "
                    f"(reserved for {reserved_cat})"
                )


# ---------------------------------------------------------------------------
# Core feature: handle_decline
# ---------------------------------------------------------------------------

def handle_decline(candidate_id):
    """
    Handle a candidate declining their allocated internship offer.

    Steps (see module docstring for design rationale):
      1. Load current allocation + supporting data.
      2. Verify candidate_id exists and currently has an allocation.
      3. Identify the vacated internship and remove the candidate's row.
      4. Identify the affected subset: candidates who are eligible/scored
         for that specific internship, are not already allocated elsewhere,
         are not the declining candidate, and (if the internship is
         reserved) belong to the reserved category.
      5. Re-optimize ONLY that affected subset with a small CP-SAT model
         using the identical objective/constraints optimizer.py uses
         (fit_score * accept_probability, capacity, reserved category) --
         not a full pipeline re-run.
      6. Merge the (possibly unchanged, if no replacement exists) result
         with every other allocation, which is left untouched.
      7. Validate the result and write demoData/final_allocation.csv.

    Returns a dict describing what happened:
        {
            "declined_candidate": ...,
            "vacated_internship": ...,
            "replacement_candidate": <candidate_id or None>,
            "original_allocation_count": int,
            "updated_allocation_count": int,
        }

    Raises ReallocationError on any clearly-identified failure condition
    (candidate not found, candidate has no allocation, missing/malformed
    CSVs). Never uses broad/silent exception handling.
    """
    allocation_df, candidates_df, internships_df, scored_df = _load_required_data()

    valid_candidate_ids = set(candidates_df["candidate_id"])
    if candidate_id not in valid_candidate_ids:
        raise ReallocationError(f"candidate_id '{candidate_id}' not found in {CANDIDATES_PATH}")

    current_row = allocation_df[allocation_df["candidate_id"] == candidate_id]
    if current_row.empty:
        raise ReallocationError(
            f"candidate_id '{candidate_id}' exists but has no current allocation "
            f"(nothing to decline)"
        )

    vacated_internship_id = current_row.iloc[0]["internship_id"]

    # --- remove the declining candidate; this restores one unit of capacity ---
    remaining_allocation_df = allocation_df[allocation_df["candidate_id"] != candidate_id].copy()

    # --- identify the affected subset ---
    already_allocated = set(remaining_allocation_df["candidate_id"])

    candidate_pool = scored_df[
        (scored_df["internship_id"] == vacated_internship_id)
        & (scored_df["candidate_id"] != candidate_id)
        & (~scored_df["candidate_id"].isin(already_allocated))
    ].copy()

    reserved_lookup = internships_df.set_index("internship_id")["reserved_category"]
    category_lookup = candidates_df.set_index("candidate_id")["category"]
    reserved_cat = reserved_lookup[vacated_internship_id]
    if pd.notna(reserved_cat):
        candidate_pool = candidate_pool[
            candidate_pool["candidate_id"].map(category_lookup) == reserved_cat
        ]

    capacity_lookup = internships_df.set_index("internship_id")["capacity"]
    total_capacity = int(capacity_lookup[vacated_internship_id])
    currently_filled = int((remaining_allocation_df["internship_id"] == vacated_internship_id).sum())
    remaining_capacity = total_capacity - currently_filled  # how many seats are open right now

    replacement_candidate_id = None

    if remaining_capacity > 0 and len(candidate_pool) > 0:
        replacement_candidate_id = _reoptimize_affected_subset(
            candidate_pool, remaining_capacity
        )

    if replacement_candidate_id is not None:
        chosen_row = candidate_pool[candidate_pool["candidate_id"] == replacement_candidate_id].iloc[0]
        new_row = pd.DataFrame([{
            "candidate_id": chosen_row["candidate_id"],
            "internship_id": vacated_internship_id,
            "fit_score": chosen_row["fit_score"],
            "accept_probability": chosen_row["accept_probability"],
        }])
        updated_allocation_df = pd.concat([remaining_allocation_df, new_row], ignore_index=True)
    else:
        # no feasible replacement -- leave the vacancy open
        updated_allocation_df = remaining_allocation_df

    # --- validate before writing anything ---
    _validate_allocation(updated_allocation_df, candidates_df, internships_df, candidate_id)

    # --- build audit records describing ONLY the changes from this event ---
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_records = [{
        "timestamp": timestamp,
        "event_type": "DECLINE",
        "candidate_id": candidate_id,
        "internship_id": vacated_internship_id,
        "previous_status": "allocated",
        "new_status": "declined/unallocated",
        "declined_candidate_id": candidate_id,
        "replacement_candidate_id": "",
    }]
    if replacement_candidate_id is not None:
        audit_records.append({
            "timestamp": timestamp,
            "event_type": "REALLOCATION",
            "candidate_id": replacement_candidate_id,
            "internship_id": vacated_internship_id,
            "previous_status": "unallocated",
            "new_status": "allocated",
            "declined_candidate_id": candidate_id,
            "replacement_candidate_id": replacement_candidate_id,
        })

    # --- only after successful validation: persist current state, then audit ---
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    updated_allocation_df.to_csv(OUTPUT_PATH, index=False)
    _append_audit_records(audit_records)

    return {
        "declined_candidate": candidate_id,
        "vacated_internship": vacated_internship_id,
        "replacement_candidate": replacement_candidate_id,
        "original_allocation_count": len(allocation_df),
        "updated_allocation_count": len(updated_allocation_df),
    }


def _reoptimize_affected_subset(candidate_pool, remaining_capacity):
    """
    Re-optimize ONLY the affected subset (one vacated internship + its
    still-eligible, still-unallocated candidates) using the same decision
    variables / objective structure optimizer.py uses:
        maximize sum(fit_score * accept_probability * 100 * x_i)
        subject to: sum(x_i) <= remaining_capacity
    This is a direct, deliberately-scoped-down reuse of optimizer.py's own
    modeling approach -- not a new scoring system, and not a full pipeline
    re-run. Returns the winning candidate_id, or None if the pool is empty
    or the solver finds no assignment.
    """
    model = cp_model.CpModel()

    x = {}
    for idx, row in candidate_pool.iterrows():
        x[idx] = model.NewBoolVar(f"x_{row['candidate_id']}")

    model.Add(sum(x.values()) <= remaining_capacity)

    objective_terms = []
    for idx, row in candidate_pool.iterrows():
        value = int(row["fit_score"] * row["accept_probability"] * 100)
        objective_terms.append(value * x[idx])
    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    winners = [idx for idx in x if solver.Value(x[idx]) == 1]
    if not winners:
        return None

    # remaining_capacity is 1 in the common single-decline case; if capacity
    # allows more than one seat, just report the single best pick as "the"
    # replacement (the feature spec's decline event concerns one vacancy).
    best_idx = max(winners, key=lambda i: candidate_pool.loc[i, "fit_score"] * candidate_pool.loc[i, "accept_probability"])
    return candidate_pool.loc[best_idx, "candidate_id"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python reallocation.py <candidate_id>")
        sys.exit(1)

    result = handle_decline(sys.argv[1])
    print(result)