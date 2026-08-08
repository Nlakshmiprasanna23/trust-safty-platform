"""Agent 1 - Risk Scoring Agent.

Uses a trained XGBoost/GradientBoosting model when available in models/,
otherwise falls back to a deterministic, fully explainable rule engine
(DEMO MODE). Both paths return identical response shapes.
"""
import os, time, joblib
import numpy as np
from app.config import settings

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models", "risk_model.joblib")
FEATURES = ["amount", "is_cod", "previous_orders", "cod_refusals", "returns_count",
            "return_frequency", "account_age_days", "ip_velocity", "new_device",
            "payment_risk_flag", "location_mismatch"]

_model = None
def _load():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception:
            _model = None
    return _model

def build_features(p: dict) -> dict:
    prev = max(int(p.get("previous_orders", 0)), 0)
    returns = int(p.get("previous_returns", 0))
    return {
        "amount": float(p.get("order_amount", 0)),
        "is_cod": 1 if p.get("is_cod") else 0,
        "previous_orders": prev,
        "cod_refusals": int(p.get("cod_refusals", 0)),
        "returns_count": returns,
        "return_frequency": round(returns / prev, 3) if prev else 0.0,
        "account_age_days": int(p.get("account_age_days", 0)),
        "ip_velocity": int(p.get("ip_velocity", 1)),
        "new_device": 1 if p.get("new_device") else 0,
        "payment_risk_flag": 1 if p.get("payment_risk_flag") else 0,
        "location_mismatch": 1 if p.get("location_mismatch") else 0,
    }

def _rule_score(f: dict):
    score, reasons = 5.0, []
    if f["cod_refusals"] >= 5:
        score += 32; reasons.append(f"{f['cod_refusals']} COD refusals in the previous 30 days")
    elif f["cod_refusals"] >= 2:
        score += 16; reasons.append(f"{f['cod_refusals']} recent COD refusals")
    if f["return_frequency"] >= 0.5 and f["returns_count"] >= 3:
        score += 20; reasons.append(f"{f['returns_count']} suspicious returns ({int(f['return_frequency']*100)}% return rate)")
    elif f["returns_count"] >= 2:
        score += 9; reasons.append(f"{f['returns_count']} recent returns")
    if f["new_device"]:
        score += 10; reasons.append("Order placed from a new/unrecognised device")
    if f["ip_velocity"] >= 5:
        score += 14; reasons.append(f"High IP velocity: {f['ip_velocity']} orders from same IP")
    if f["is_cod"] and f["amount"] >= 15000:
        score += 15; reasons.append("High-value COD order")
    elif f["is_cod"] and f["amount"] >= 5000:
        score += 7; reasons.append("Elevated-value COD order")
    if f["account_age_days"] < 30 and (f["cod_refusals"] or f["returns_count"]):
        score += 8; reasons.append("New account combined with prior refusal/return signals")
    if f["payment_risk_flag"]:
        score += 10; reasons.append("Payment instrument flagged by risk provider")
    if f["location_mismatch"]:
        score += 8; reasons.append("Delivery/IP location inconsistency")
    if f["previous_orders"] >= 20 and f["cod_refusals"] == 0 and f["returns_count"] <= 1:
        score -= 12; reasons.append("Long positive order history (risk reduced)")
    if not reasons:
        reasons.append("No material risk signals detected")
    return max(0.0, min(100.0, score)), reasons

def level_and_action(score: float, is_cod: bool):
    if score >= 80:
        return "CRITICAL", ("BLOCK_COD" if is_cod else "MANUAL_REVIEW")
    if score >= 60:
        return "HIGH", ("BLOCK_COD" if is_cod else "MANUAL_REVIEW")
    if score >= 35:
        return "MEDIUM", "VERIFY"
    return "LOW", "ALLOW"

def analyze(payload: dict) -> dict:
    start = time.perf_counter()
    f = build_features(payload)
    score, reasons = _rule_score(f)
    mode = "DEMO_RULES"
    model = _load()
    if model is not None:
        try:
            x = np.array([[f[k] for k in FEATURES]])
            proba = float(model.predict_proba(x)[0][1]) * 100
            score = round(0.5 * score + 0.5 * proba, 2)
            mode = "ML_MODEL"
        except Exception:
            pass
    fraud_probability = round(min(99.0, score * 0.95 + 3), 2)
    risk_level, action = level_and_action(score, bool(f["is_cod"]))
    return {
        "risk_score": round(score, 2),
        "fraud_probability": fraud_probability,
        "risk_level": risk_level,
        "recommended_action": action,
        "reasons": reasons,
        "features": f,
        "model_version": settings.RISK_MODEL_VERSION,
        "policy_version": settings.POLICY_VERSION,
        "mode": mode,
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
    }
