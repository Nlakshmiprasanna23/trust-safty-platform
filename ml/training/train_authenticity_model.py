"""Trains the counterfeit-listing classifier on tabular + text listing features.

Usage:
    python ml/training/train_authenticity_model.py
    python ml/training/train_authenticity_model.py --data data/raw/luxury_listings.csv
Saves: models/authenticity_model.joblib

Image analysis stays in the deterministic OpenCV/Pillow DEMO pipeline in
backend/app/services/authenticity_agent/agent.py until a licensed vision
dataset is placed in data/raw (see docs/dataset-guide.md).
"""
import argparse, os, json, joblib
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEATURES = ["price_deviation_pct", "authorized", "suspicious_keyword_count",
            "description_length", "cert_claim_unverified", "seller_rating"]

def synthetic(n=6000, seed=7):
    rng = np.random.default_rng(seed)
    counterfeit = rng.integers(0, 2, n)
    df = pd.DataFrame({
        "price_deviation_pct": np.where(counterfeit, rng.uniform(55, 95, n), rng.uniform(0, 40, n)),
        "authorized": np.where(counterfeit, rng.integers(0, 2, n) * 0, rng.integers(0, 2, n)),
        "suspicious_keyword_count": np.where(counterfeit, rng.integers(1, 6, n), rng.integers(0, 2, n)),
        "description_length": np.where(counterfeit, rng.integers(5, 40, n), rng.integers(25, 200, n)),
        "cert_claim_unverified": np.where(counterfeit, rng.integers(0, 2, n), rng.integers(0, 2, n) * 0),
        "seller_rating": np.where(counterfeit, rng.uniform(2.5, 4.0, n), rng.uniform(3.8, 5.0, n)),
    })
    df["is_counterfeit"] = counterfeit
    return df

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default=None)
    args = ap.parse_args()
    df = pd.read_csv(args.data) if args.data else synthetic()
    X, y = df[FEATURES], df["is_counterfeit"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model = RandomForestClassifier(n_estimators=300, max_depth=10, n_jobs=4, random_state=42)
    model.fit(Xtr, ytr)
    print(classification_report(yte, model.predict(Xte)))
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
    joblib.dump(model, os.path.join(ROOT, "models", "authenticity_model.joblib"))
    json.dump({"roc_auc": round(roc_auc_score(yte, model.predict_proba(Xte)[:, 1]), 4),
               "source": args.data or "synthetic"},
              open(os.path.join(ROOT, "models", "authenticity_model_metrics.json"), "w"), indent=2)
    print("Saved models/authenticity_model.joblib")

if __name__ == "__main__":
    main()
