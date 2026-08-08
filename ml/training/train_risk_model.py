"""Trains the Risk Scoring model (XGBoost, falls back to GradientBoosting).

Usage:
    python ml/training/train_risk_model.py                 # synthetic demo data
    python ml/training/train_risk_model.py --data data/raw/ieee_cis_train.csv
Saves: models/risk_model.joblib
"""
import argparse, os, json
import numpy as np, pandas as pd, joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

FEATURES = ["amount", "is_cod", "previous_orders", "cod_refusals", "returns_count",
            "return_frequency", "account_age_days", "ip_velocity", "new_device",
            "payment_risk_flag", "location_mismatch"]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def synthetic(n=8000, seed=42):
    rng = np.random.default_rng(seed)
    prev = rng.integers(0, 90, n)
    returns = rng.integers(0, 8, n)
    df = pd.DataFrame({
        "amount": rng.choice([499, 1299, 2499, 4999, 8999, 19999], n),
        "is_cod": rng.integers(0, 2, n),
        "previous_orders": prev,
        "cod_refusals": rng.choice([0, 0, 0, 1, 2, 5], n),
        "returns_count": returns,
        "return_frequency": np.round(returns / np.maximum(prev, 1), 3),
        "account_age_days": rng.integers(1, 1500, n),
        "ip_velocity": rng.integers(1, 12, n),
        "new_device": rng.integers(0, 2, n),
        "payment_risk_flag": (rng.random(n) < 0.1).astype(int),
        "location_mismatch": (rng.random(n) < 0.2).astype(int),
    })
    logit = (-3.2 + 0.42 * df.cod_refusals + 1.6 * df.return_frequency + 0.55 * df.new_device
             + 0.16 * df.ip_velocity + 0.00004 * df.amount * df.is_cod
             + 0.7 * df.payment_risk_flag + 0.45 * df.location_mismatch
             - 0.012 * np.minimum(df.previous_orders, 60))
    p = 1 / (1 + np.exp(-logit))
    df["is_fraud"] = (rng.random(n) < p).astype(int)
    return df

def build_model():
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=250, max_depth=5, learning_rate=0.08,
                             subsample=0.9, eval_metric="logloss", n_jobs=4)
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier
        print("xgboost unavailable - using scikit-learn GradientBoostingClassifier")
        return GradientBoostingClassifier()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="CSV with FEATURES + is_fraud column")
    args = ap.parse_args()
    df = pd.read_csv(args.data) if args.data else synthetic()
    X, y = df[FEATURES], df["is_fraud"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model = build_model()
    model.fit(Xtr, ytr)
    pred = model.predict(Xte); proba = model.predict_proba(Xte)[:, 1]
    metrics = {"precision": round(precision_score(yte, pred, zero_division=0), 4),
               "recall": round(recall_score(yte, pred, zero_division=0), 4),
               "f1": round(f1_score(yte, pred, zero_division=0), 4),
               "roc_auc": round(roc_auc_score(yte, proba), 4),
               "n_train": len(Xtr), "source": args.data or "synthetic"}
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
    joblib.dump(model, os.path.join(ROOT, "models", "risk_model.joblib"))
    with open(os.path.join(ROOT, "models", "risk_model_metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)
    print("Saved models/risk_model.joblib"); print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
