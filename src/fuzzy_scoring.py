import pandas as pd
import numpy as np
import skfuzzy as fuzz

def compute_skill_match_pct(candidate, internship):
    """% of internship's required skills that the candidate has."""
    candidate_skills = set(s.strip() for s in candidate["skills"].split(","))
    required_skills = set(s.strip() for s in internship["required_skills"].split(","))
    return len(candidate_skills & required_skills) / len(required_skills) * 100

def fuzzy_fit_score(skill_match_pct, qualification_score):
    """
    Combines skill match % and qualification score into one fuzzy fit score (0-100)
    using fuzzy membership functions instead of a flat weighted average.
    """
    # Define universes (input ranges)
    x_skill = np.arange(0, 101, 1)
    x_qual = np.arange(0, 101, 1)
    x_fit = np.arange(0, 101, 1)

    # Membership functions for skill match
    skill_low = fuzz.trimf(x_skill, [0, 0, 50])
    skill_med = fuzz.trimf(x_skill, [20, 50, 80])
    skill_high = fuzz.trimf(x_skill, [50, 100, 100])

    # Membership functions for qualification score
    qual_low = fuzz.trimf(x_qual, [0, 0, 60])
    qual_med = fuzz.trimf(x_qual, [40, 65, 90])
    qual_high = fuzz.trimf(x_qual, [70, 100, 100])

    # Membership functions for output fit score
    # NOTE (BUG #6 fix): fit_low/fit_high are boundary ("shoulder") sets whose
    # triangular membership peaks only at a single edge point (x=0 or x=100).
    # Under centroid defuzzification, a plain linear triangular shoulder always
    # centroids at exactly 1/3 of the way in from its edge (a fixed geometric
    # property, independent of base width), which is why full activation of
    # fit_high alone centroids at 83.33 and fit_low alone at 16.67 rather than
    # near the true 100/0 endpoints. The standard fuzzy-logic fix for
    # sharpening a boundary set without changing its crossover points, rules,
    # or aggregation is the "very" linguistic concentration hedge (squaring
    # the membership degree pointwise, i.e. "very high" = high^2), which
    # concentrates more of the set's weight near its true edge. Applied only
    # to the two boundary sets; fit_med (an interior set, not a boundary
    # shoulder) is unchanged.
    fit_low = fuzz.trimf(x_fit, [0, 0, 50]) ** 2
    fit_med = fuzz.trimf(x_fit, [20, 50, 80])
    fit_high = fuzz.trimf(x_fit, [50, 100, 100]) ** 2

    # Fuzzify the inputs (find degree of membership at the given crisp value)
    skill_level_low = fuzz.interp_membership(x_skill, skill_low, skill_match_pct)
    skill_level_med = fuzz.interp_membership(x_skill, skill_med, skill_match_pct)
    skill_level_high = fuzz.interp_membership(x_skill, skill_high, skill_match_pct)

    qual_level_low = fuzz.interp_membership(x_qual, qual_low, qualification_score)
    qual_level_med = fuzz.interp_membership(x_qual, qual_med, qualification_score)
    qual_level_high = fuzz.interp_membership(x_qual, qual_high, qualification_score)

    # Simple rule base:
    # If skill is high AND qual is high -> fit is high
    # If skill is low OR qual is low -> fit is low
    # Otherwise -> fit is medium
    rule_high = np.fmin(skill_level_high, qual_level_high)
    rule_low = np.fmax(skill_level_low, qual_level_low)
    rule_med = np.fmin(np.fmax(skill_level_med, qual_level_med), 1 - max(rule_high, rule_low))

    # Aggregate output membership
    fit_activation_low = np.fmin(rule_low, fit_low)
    fit_activation_med = np.fmin(rule_med, fit_med)
    fit_activation_high = np.fmin(rule_high, fit_high)

    aggregated = np.fmax(fit_activation_low, np.fmax(fit_activation_med, fit_activation_high))

    # Defuzzify (convert fuzzy set back into one crisp number) using centroid method
    if aggregated.sum() == 0:
        return 0.0
    fit_score = fuzz.defuzz(x_fit, aggregated, 'centroid')
    return round(fit_score, 2)

def score_eligible_pairs(candidates_df, internships_df, eligible_pairs_df):
    cand_lookup = candidates_df.set_index("candidate_id")
    intern_lookup = internships_df.set_index("internship_id")

    scores = []
    for _, row in eligible_pairs_df.iterrows():
        cand = cand_lookup.loc[row["candidate_id"]]
        intern = intern_lookup.loc[row["internship_id"]]

        skill_match_pct = compute_skill_match_pct(cand, intern)
        fit_score = fuzzy_fit_score(skill_match_pct, cand["qualification_score"])

        scores.append({
            "candidate_id": row["candidate_id"],
            "internship_id": row["internship_id"],
            "skill_match_pct": round(skill_match_pct, 1),
            "fit_score": fit_score,
        })
    return pd.DataFrame(scores)

if __name__ == "__main__":
    candidates_df = pd.read_csv("../demoData/candidates.csv")
    internships_df = pd.read_csv("../demoData/internships.csv")
    eligible_pairs_df = pd.read_csv("../demoData/eligible_pairs.csv")

    scored_pairs = score_eligible_pairs(candidates_df, internships_df, eligible_pairs_df)
    scored_pairs.to_csv("../demoData/scored_pairs.csv", index=False)

    print(scored_pairs.head(10))
    print(f"\nTotal scored pairs: {len(scored_pairs)}")
    print(f"Average fit score: {scored_pairs['fit_score'].mean():.2f}")