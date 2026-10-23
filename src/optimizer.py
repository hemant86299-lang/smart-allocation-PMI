import pandas as pd
from ortools.sat.python import cp_model

def run_allocation(scored_pairs_df, candidates_df, internships_df):
    model = cp_model.CpModel()

    # Create a decision variable for every (candidate, internship) pair:
    # x[i] = 1 means that candidate gets that internship, 0 means they don't
    x = {}
    for idx, row in scored_pairs_df.iterrows():
        x[idx] = model.NewBoolVar(f"x_{row['candidate_id']}_{row['internship_id']}")

    # CONSTRAINT 1: each candidate gets AT MOST one internship
    for cand_id in candidates_df["candidate_id"]:
        pair_indices = scored_pairs_df.index[scored_pairs_df["candidate_id"] == cand_id]
        if len(pair_indices) > 0:
            model.Add(sum(x[idx] for idx in pair_indices) <= 1)

    # CONSTRAINT 2: each internship fills AT MOST its capacity
    capacity_lookup = internships_df.set_index("internship_id")["capacity"]
    for intern_id in internships_df["internship_id"]:
        pair_indices = scored_pairs_df.index[scored_pairs_df["internship_id"] == intern_id]
        if len(pair_indices) > 0:
            model.Add(sum(x[idx] for idx in pair_indices) <= int(capacity_lookup[intern_id]))

    # CONSTRAINT 3 (fairness): if an internship has a reserved_category,
    # only candidates from that category can be allocated to it
    reserved_lookup = internships_df.set_index("internship_id")["reserved_category"]
    category_lookup = candidates_df.set_index("candidate_id")["category"]

    for idx, row in scored_pairs_df.iterrows():
        reserved_cat = reserved_lookup[row["internship_id"]]
        if pd.notna(reserved_cat):
            cand_cat = category_lookup[row["candidate_id"]]
            if cand_cat != reserved_cat:
                model.Add(x[idx] == 0)  # this pair is not allowed

    # OBJECTIVE: maximize total value = fit_score * accept_probability, summed over all matches
    # We scale to integers (CP-SAT requires integer coefficients) by multiplying by 100
    objective_terms = []
    for idx, row in scored_pairs_df.iterrows():
        value = int(row["fit_score"] * row["accept_probability"] * 100)
        objective_terms.append(value * x[idx])
    model.Maximize(sum(objective_terms))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    results = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for idx, row in scored_pairs_df.iterrows():
            if solver.Value(x[idx]) == 1:
                results.append({
                    "candidate_id": row["candidate_id"],
                    "internship_id": row["internship_id"],
                    "fit_score": row["fit_score"],
                    "accept_probability": row["accept_probability"],
                })

    return pd.DataFrame(results), status

if __name__ == "__main__":
    candidates_df = pd.read_csv("../demoData/candidates.csv")
    internships_df = pd.read_csv("../demoData/internships.csv")
    scored_pairs_df = pd.read_csv("../demoData/scored_pairs_with_probability.csv")

    allocation_df, status = run_allocation(scored_pairs_df, candidates_df, internships_df)
    allocation_df.to_csv("../demoData/final_allocation.csv", index=False)

    print(f"Solver status: {status} (3=OPTIMAL, 4=FEASIBLE)")
    print(f"Total candidates allocated: {len(allocation_df)} out of {len(candidates_df)}")
    print("\nSample allocation:")
    print(allocation_df.head(10))