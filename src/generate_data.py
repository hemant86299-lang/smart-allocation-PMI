from faker import Faker
import pandas as pd
import random

fake = Faker()
Faker.seed(42)
random.seed(42)

CATEGORIES = ["General", "OBC", "SC", "ST", "EWS"]
SKILLS = ["Python", "Excel", "Communication", "Data Analysis", "Marketing",
          "Design", "Sales", "Content Writing", "Finance", "Customer Support"]
LOCATIONS = ["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Pune", "Chennai"]

def generate_candidates(n=200):
    candidates = []
    for i in range(n):
        candidates.append({
            "candidate_id": f"C{i+1:04d}",
            "name": fake.name(),
            "category": random.choice(CATEGORIES),
            "location_pref": random.choice(LOCATIONS),
            "skills": ", ".join(random.sample(SKILLS, k=random.randint(2, 4))),
            "qualification_score": round(random.uniform(50, 100), 1),
        })
    return pd.DataFrame(candidates)

def generate_internships(n=30):
    internships = []
    for i in range(n):
        internships.append({
            "internship_id": f"I{i+1:03d}",
            "title": fake.job(),
            "location": random.choice(LOCATIONS),
            "capacity": random.randint(2, 10),
            "required_skills": ", ".join(random.sample(SKILLS, k=random.randint(2, 3))),
            "reserved_category": random.choice(CATEGORIES + [None, None]),
        })
    return pd.DataFrame(internships)

if __name__ == "__main__":
    candidates_df = generate_candidates(200)
    internships_df = generate_internships(30)

    candidates_df.to_csv("../demoData/candidates.csv", index=False)
    internships_df.to_csv("../demoData/internships.csv", index=False)

    print("Candidates sample:")
    print(candidates_df.head())
    print("\nInternships sample:")
    print(internships_df.head())
    print(f"\nGenerated {len(candidates_df)} candidates and {len(internships_df)} internships.")