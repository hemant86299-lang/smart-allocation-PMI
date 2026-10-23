import pandas as pd

def is_eligible(candidate, internship):
    """Returns True if candidate is allowed to be considered for this internship."""

    # Rule 1: Minimum qualification score
    if candidate["qualification_score"] < 55:
        return False

    # Rule 2: Location — candidate must prefer this internship's location
    if candidate["location_pref"] != internship["location"]:
        return False

    # Rule 3: Skill overlap — candidate must have at least 1 required skill
    candidate_skills = set(s.strip() for s in candidate["skills"].split(","))
    required_skills = set(s.strip() for s in internship["required_skills"].split(","))
    if len(candidate_skills & required_skills) == 0:
        return False

    return True

def build_eligibility_pairs(candidates_df, internships_df):
    """Returns a DataFrame of every eligible (candidate, internship) pair."""
    pairs = []
    for _, cand in candidates_df.iterrows():
        for _, intern in internships_df.iterrows():
            if is_eligible(cand, intern):
                pairs.append({
                    "candidate_id": cand["candidate_id"],
                    "internship_id": intern["internship_id"],
                })
    return pd.DataFrame(pairs)

if __name__ == "__main__":
    candidates_df = pd.read_csv("../demoData/candidates.csv")
    internships_df = pd.read_csv("../demoData/internships.csv")

    eligible_pairs = build_eligibility_pairs(candidates_df, internships_df)
    eligible_pairs.to_csv("../demoData/eligible_pairs.csv", index=False)

    print(f"Total candidates: {len(candidates_df)}")
    print(f"Total internships: {len(internships_df)}")
    print(f"Total eligible pairs: {len(eligible_pairs)}")
    print("\nSample eligible pairs:")
    print(eligible_pairs.head(10))