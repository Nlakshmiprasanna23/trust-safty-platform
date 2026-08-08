from pathlib import Path

import joblib
import pandas as pd


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "risk_model.joblib"

_model = None


# ============================================================
# LOAD TRAINED IEEE-CIS MODEL
# ============================================================

def get_model():
    global _model

    if _model is None:

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Risk model not found: {MODEL_PATH}"
            )

        _model = joblib.load(MODEL_PATH)

    return _model


# ============================================================
# IEEE-CIS MODEL INPUT
# ============================================================

def build_model_input(payload: dict) -> pd.DataFrame:

    amount = float(
        payload.get(
            "order_amount",
            payload.get("amount", 0)
        )
    )

    payment_method = str(
        payload.get(
            "payment_method",
            "COD"
        )
    ).upper()

    previous_orders = int(
        payload.get("previous_orders", 0)
    )

    previous_returns = int(
        payload.get("previous_returns", 0)
    )

    cod_refusals = int(
        payload.get("cod_refusals", 0)
    )

    account_age_days = int(
        payload.get("account_age_days", 0)
    )

    ip_velocity = int(
        payload.get("ip_velocity", 1)
    )

    new_device = bool(
        payload.get("new_device", False)
    )

    location_mismatch = bool(
        payload.get("location_mismatch", False)
    )

    payment_risk_flag = bool(
        payload.get("payment_risk_flag", False)
    )

    device_id = str(
        payload.get("device_id", "")
    )

    # --------------------------------------------------------
    # Payment mapping
    # --------------------------------------------------------

    if payment_method == "COD":
        card4 = "COD"
        card6 = "debit"

    elif payment_method == "UPI":
        card4 = "UPI"
        card6 = "debit"

    elif payment_method in {"CARD", "CREDIT_CARD"}:
        card4 = "card"
        card6 = "credit"

    elif payment_method == "NETBANKING":
        card4 = "NETBANKING"
        card6 = "debit"

    else:
        card4 = payment_method
        card6 = "unknown"

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    if device_id:
        device_info = device_id
    elif new_device:
        device_info = "NEW_DEVICE"
    else:
        device_info = "UNKNOWN"

    device_type = (
        "mobile"
        if "mobile" in device_info.lower()
        else "desktop"
    )

    # --------------------------------------------------------
    # Application behavioral signals
    #
    # These are mapped only so the trained model receives
    # correctly shaped input. They are NOT claimed to be
    # original IEEE-CIS meanings.
    # --------------------------------------------------------

    row = {
        "TransactionDT": account_age_days * 86400,
        "TransactionAmt": amount,
        "ProductCD": "W",

        "card1": 0,
        "card2": 0,
        "card3": 0,
        "card4": card4,
        "card5": 0,
        "card6": card6,

        "addr1": 0,
        "addr2": 0,
        "dist1": 0,
        "dist2": 0,

        "P_emaildomain": "UNKNOWN",
        "R_emaildomain": "UNKNOWN",

        "C1": previous_orders,
        "C2": previous_returns,
        "C3": cod_refusals,
        "C4": ip_velocity,

        "C5": int(new_device),
        "C6": int(location_mismatch),
        "C7": int(payment_risk_flag),

        "C8": 0,
        "C9": 0,
        "C10": 0,
        "C11": 0,
        "C12": 0,
        "C13": 0,
        "C14": 0,

        "DeviceType": device_type,
        "DeviceInfo": device_info,
    }

    return pd.DataFrame([row])


# ============================================================
# BEHAVIORAL RISK SCORE
# ============================================================

def calculate_behavior_score(payload: dict):

    score = 0
    reasons = []

    amount = float(
        payload.get(
            "order_amount",
            payload.get("amount", 0)
        )
    )

    previous_orders = int(
        payload.get("previous_orders", 0)
    )

    previous_returns = int(
        payload.get("previous_returns", 0)
    )

    cod_refusals = int(
        payload.get("cod_refusals", 0)
    )

    account_age_days = int(
        payload.get("account_age_days", 0)
    )

    ip_velocity = int(
        payload.get("ip_velocity", 1)
    )

    new_device = bool(
        payload.get("new_device", False)
    )

    location_mismatch = bool(
        payload.get("location_mismatch", False)
    )

    payment_risk_flag = bool(
        payload.get("payment_risk_flag", False)
    )

    payment_method = str(
        payload.get(
            "payment_method",
            "COD"
        )
    ).upper()

    # --------------------------------------------------------
    # HIGH-VALUE COD
    # --------------------------------------------------------

    if payment_method == "COD" and amount >= 10000:

        score += 20

        reasons.append(
            "High-value COD order"
        )

    elif payment_method == "COD" and amount >= 5000:

        score += 10

        reasons.append(
            "Elevated-value COD order"
        )

    # --------------------------------------------------------
    # COD REFUSALS
    # --------------------------------------------------------

    if cod_refusals >= 5:

        score += 25

        reasons.append(
            "High history of COD refusals"
        )

    elif cod_refusals >= 3:

        score += 15

        reasons.append(
            "Multiple previous COD refusals"
        )

    elif cod_refusals >= 1:

        score += 5

        reasons.append(
            "Previous COD refusal history"
        )

    # --------------------------------------------------------
    # RETURN HISTORY
    # --------------------------------------------------------

    if previous_returns >= 8:

        score += 20

        reasons.append(
            "High previous return activity"
        )

    elif previous_returns >= 4:

        score += 12

        reasons.append(
            "Elevated previous return activity"
        )

    elif previous_returns >= 2:

        score += 5

        reasons.append(
            "Previous return activity detected"
        )

    # --------------------------------------------------------
    # RETURN RATE
    # --------------------------------------------------------

    if previous_orders > 0:

        return_rate = (
            previous_returns / previous_orders
        )

        if return_rate >= 0.50:

            score += 15

            reasons.append(
                "High historical return rate"
            )

        elif return_rate >= 0.30:

            score += 8

            reasons.append(
                "Elevated historical return rate"
            )

    # --------------------------------------------------------
    # NEW DEVICE
    # --------------------------------------------------------

    if new_device:

        score += 15

        reasons.append(
            "Transaction originated from a new device"
        )

    # --------------------------------------------------------
    # LOCATION MISMATCH
    # --------------------------------------------------------

    if location_mismatch:

        score += 15

        reasons.append(
            "Location mismatch detected"
        )

    # --------------------------------------------------------
    # IP VELOCITY
    # --------------------------------------------------------

    if ip_velocity >= 10:

        score += 20

        reasons.append(
            "Very high IP transaction velocity"
        )

    elif ip_velocity >= 5:

        score += 10

        reasons.append(
            "Elevated IP transaction velocity"
        )

    # --------------------------------------------------------
    # ACCOUNT AGE
    # --------------------------------------------------------

    if account_age_days <= 7:

        score += 15

        reasons.append(
            "Very new customer account"
        )

    elif account_age_days <= 30:

        score += 8

        reasons.append(
            "Recently created customer account"
        )

    # --------------------------------------------------------
    # PAYMENT RISK
    # --------------------------------------------------------

    if payment_risk_flag:

        score += 20

        reasons.append(
            "Payment risk flag detected"
        )

    return min(score, 100), reasons


# ============================================================
# FINAL RISK PREDICTION
# ============================================================

def predict_risk(payload: dict) -> dict:

    # --------------------------------------------------------
    # ML prediction
    # --------------------------------------------------------

    model = get_model()

    model_input = build_model_input(
        payload
    )

    ml_probability = float(
        model.predict_proba(
            model_input
        )[0][1]
    )

    # --------------------------------------------------------
    # Behavioral prediction
    # --------------------------------------------------------

    behavior_score, reasons = calculate_behavior_score(
        payload
    )

    # --------------------------------------------------------
    # Combine signals
    #
    # 30% ML
    # 70% deterministic behavioral signals
    #
    # This keeps the IEEE-CIS model involved while ensuring
    # the application's real-time fraud signals matter.
    # --------------------------------------------------------

    ml_score = ml_probability * 100

    final_score = (
        (ml_score * 0.30)
        +
        (behavior_score * 0.70)
    )

    final_score = min(
        max(final_score, 0),
        100
    )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    if final_score >= 80:

        risk_level = "CRITICAL"

    elif final_score >= 60:

        risk_level = "HIGH"

    elif final_score >= 30:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"

    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    if final_score >= 80:

        decision = "REJECT"

    elif final_score >= 60:

        decision = "REVIEW"

    else:

        decision = "APPROVE"

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = (
        0.50
        +
        abs(final_score - 50) / 100
    )

    confidence = min(
        confidence,
        0.99
    )

    # --------------------------------------------------------
    # Default reason
    # --------------------------------------------------------

    if not reasons:

        reasons.append(
            "No significant behavioral risk indicators detected"
        )

    # --------------------------------------------------------
    # Feature contributions
    # --------------------------------------------------------

    feature_contributions = []

    if payload.get("cod_refusals", 0) > 0:
        feature_contributions.append({
            "feature": "COD refusals",
            "impact": min(
                int(payload["cod_refusals"]) * 5,
                25
            )
        })

    if payload.get("previous_returns", 0) > 0:
        feature_contributions.append({
            "feature": "Previous returns",
            "impact": min(
                int(payload["previous_returns"]) * 3,
                20
            )
        })

    if payload.get("new_device", False):
        feature_contributions.append({
            "feature": "New device",
            "impact": 15
        })

    if payload.get("location_mismatch", False):
        feature_contributions.append({
            "feature": "Location mismatch",
            "impact": 15
        })

    if payload.get("ip_velocity", 1) >= 5:
        feature_contributions.append({
            "feature": "IP velocity",
            "impact": 10
        })

    if payload.get("payment_risk_flag", False):
        feature_contributions.append({
            "feature": "Payment risk flag",
            "impact": 20
        })

    if not feature_contributions:
        feature_contributions.append({
            "feature": "Behavioral risk",
            "impact": 0
        })

    return {
        "risk_score": round(
            final_score,
            2
        ),

        "risk_probability": round(
            final_score / 100,
            6
        ),

        "risk_level": risk_level,

        "decision": decision,

        "confidence": round(
            confidence,
            4
        ),

        "model_version": "risk-model-v2",

        "reasons": reasons,

        "feature_contributions":
            feature_contributions,

        "ml_probability": round(
            ml_probability,
            6
        ),

        "behavior_score": round(
            behavior_score,
            2
        ),
    }