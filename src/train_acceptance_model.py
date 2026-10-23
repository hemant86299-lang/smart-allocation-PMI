import pandas as pd
import numpy as np
import random
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

random.seed(42)
np.random.seed(42)

def simulate_training_data(scored_pairs_df):
    """
    Simulates whether a candidate 'accepted' or 'declined' each offer,
    based on a realistic rule: higher fit_score and skill_match -> more likely to accept.
    This stands in for real historical data you'd have in production.
    """
    df = scored_pairs_df.copy()

    # Simulate acceptance probability based on fit_score (with some randomness)
    true_prob = (df["fit_score"] / 100) * 0.7 + (df["skill_match_pct"] / 100) * 0.3
    noise = np.random.normal(0, 0.15, size=len(df))
    accept_prob = np.clip(true_prob + noise, 0, 1)

    df["accepted"] = (accept_prob > 0.5).astype(int)
    return df

def train_model(df):
    X = df[["fit_score", "skill_match_pct"]]
    y = df["accepted"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))

    return model

if __name__ == "__main__":
    scored_pairs_df = pd.read_csv("../demoData/scored_pairs.csv")

    labeled_df = simulate_training_data(scored_pairs_df)
    labeled_df.to_csv("../demoData/labeled_pairs.csv", index=False)

    model = train_model(labeled_df)

    # Save the trained model so we can reuse it later without retraining
    joblib.dump(model, "acceptance_model.pkl")

    # Predict acceptance probability for ALL scored pairs (not just test set)
    scored_pairs_df["accept_probability"] = model.predict_proba(
        scored_pairs_df[["fit_score", "skill_match_pct"]]
    )[:, 1]
    scored_pairs_df.to_csv("../demoData/scored_pairs_with_probability.csv", index=False)

    print("\nSample predictions:")
    print(scored_pairs_df.head(10))
    print("\nModel saved as acceptance_model.pkl")