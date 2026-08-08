"""Trains the fake-review classifier (TF-IDF + Logistic Regression).

Usage:
    python ml/training/train_review_model.py
    python ml/training/train_review_model.py --data data/raw/fake_reviews.csv   # columns: text,label
Saves: models/review_model.joblib
"""
import argparse, os, json, joblib, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAKE = ["Best product must buy highly recommend", "Amazing quality fast delivery must buy",
        "Overall, in conclusion this is a top-notch quality product", "Value for money best product ever",
        "Loved it, nice product, highly recommend this product", "Superb must buy amazing quality"]
REAL = ["The stitching near the sleeve came loose after two washes but the fabric is soft",
        "Battery lasts about six hours on my commute which is acceptable at this price",
        "Delivery took four days to Pune, packaging was sealed and invoice included",
        "Sizing runs small, order one size up, otherwise the material is decent",
        "Sound is clear for calls but bass is weak compared to my previous pair",
        "Works fine, though the charging cable that shipped with it is quite short"]

def synthetic():
    rows = [{"text": t + f" #{i}", "label": 1} for i in range(300) for t in FAKE]
    rows += [{"text": t + f" #{i}", "label": 0} for i in range(300) for t in REAL]
    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default=None)
    args = ap.parse_args()
    df = pd.read_csv(args.data) if args.data else synthetic()
    Xtr, Xte, ytr, yte = train_test_split(df.text, df.label, test_size=0.2, stratify=df.label, random_state=42)
    pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
                     ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    pipe.fit(Xtr, ytr)
    proba = pipe.predict_proba(Xte)[:, 1]
    print(classification_report(yte, pipe.predict(Xte)))
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
    joblib.dump(pipe, os.path.join(ROOT, "models", "review_model.joblib"))
    json.dump({"roc_auc": round(roc_auc_score(yte, proba), 4), "source": args.data or "synthetic"},
              open(os.path.join(ROOT, "models", "review_model_metrics.json"), "w"), indent=2)
    print("Saved models/review_model.joblib")

if __name__ == "__main__":
    main()
