"""Agent 2 - Authenticity & Integrity Agent (image + text + price + authorization)."""
import io, time, re, hashlib
from app.config import settings

SUSPICIOUS_KEYWORDS = ["100% original guaranteed", "first copy", "master copy", "7a quality",
                       "replica", "mirror quality", "duplicate", "unbranded original",
                       "no bill", "without invoice", "imported copy", "aaa grade"]
FAKE_CERT_PATTERNS = ["iso certified by self", "self certified", "government approved original",
                      "fda approved", "certified by brand owner (pending)", "cert pending"]

def analyze_image(image_bytes: bytes | None) -> dict:
    """Deterministic DEMO-MODE computer-vision pipeline (OpenCV/Pillow when available)."""
    if not image_bytes:
        return {"available": False, "score": 50.0, "signals": ["No product image supplied - image analysis skipped"]}
    signals, score = [], 80.0
    width = height = 0
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = img.size
        arr = np.asarray(img.resize((256, 256)))
        gray = arr.mean(axis=2)
        # edge energy proxy for logo distortion / print quality
        gx = abs(gray[:, 1:] - gray[:, :-1]).mean()
        gy = abs(gray[1:, :] - gray[:-1, :]).mean()
        sharpness = float((gx + gy) / 2)
        colour_std = float(arr.std())
        if sharpness < 4:
            score -= 25; signals.append("Low edge sharpness - possible logo distortion or rescanned packaging")
        if colour_std < 30:
            score -= 12; signals.append("Flat colour distribution - packaging anomaly indicator")
        if width and (width < 400 or height < 400):
            score -= 15; signals.append(f"Low-resolution image ({width}x{height}) typical of scraped listings")
        aspect = width / height if height else 1
        if aspect > 2.2 or aspect < 0.45:
            score -= 8; signals.append("Unusual aspect ratio - cropped/composited image")
        if not signals:
            signals.append("No visual counterfeit indicators detected")
    except Exception as exc:  # pillow missing / corrupt image
        signals.append(f"Image could not be decoded ({type(exc).__name__}) - defaulting to neutral image score")
        score = 50.0
    phash = hashlib.sha256(image_bytes).hexdigest()[:16]
    return {"available": True, "score": max(0.0, min(100.0, score)), "signals": signals,
            "width": width, "height": height, "image_fingerprint": phash, "mode": "DEMO_MODE"}

def analyze_text(name: str, brand: str, description: str, certification: str) -> dict:
    blob = f"{name} {description} {certification}".lower()
    signals, score = [], 85.0
    for kw in SUSPICIOUS_KEYWORDS:
        if kw in blob:
            score -= 18; signals.append(f"Suspicious listing keyword detected: '{kw}'")
    for pat in FAKE_CERT_PATTERNS:
        if pat in blob:
            score -= 20; signals.append(f"Unverifiable certification claim: '{pat}'")
    if brand and brand.lower() not in f"{name} {description}".lower():
        score -= 6; signals.append("Brand name absent from product title/description")
    if len(re.findall(r"[!]{2,}|[A-Z]{6,}", description or "")) > 2:
        score -= 8; signals.append("Aggressive promotional formatting typical of grey-market listings")
    if len((description or "").split()) < 12:
        score -= 8; signals.append("Unusually thin product description")
    if not signals:
        signals.append("No misleading claims or brand misuse detected")
    return {"score": max(0.0, min(100.0, score)), "signals": signals}

def analyze_price(price: float, msrp: float) -> dict:
    if not msrp or msrp <= 0:
        return {"score": 60.0, "deviation_pct": 0.0, "signals": ["MSRP unavailable - price analysis inconclusive"]}
    deviation = round((msrp - price) / msrp * 100, 2)
    signals, score = [], 90.0
    if deviation >= 80:
        score = 8.0; signals.append(f"Price {deviation}% below MSRP - strong counterfeit indicator")
    elif deviation >= 60:
        score = 25.0; signals.append(f"Price {deviation}% below MSRP - highly improbable discount")
    elif deviation >= 40:
        score = 55.0; signals.append(f"Price {deviation}% below MSRP - requires verification")
    elif deviation < 0:
        score = 75.0; signals.append("Listed above MSRP - price gouging check")
    else:
        signals.append(f"Price deviation {deviation}% within plausible discount range")
    return {"score": score, "deviation_pct": deviation, "signals": signals}

def analyze_authorization(authorized: bool, certification: str) -> dict:
    signals, score = [], 90.0
    if not authorized:
        score = 35.0; signals.append("Seller is not an authorised distributor for this brand")
    else:
        signals.append("Seller holds valid brand authorisation")
    if not certification:
        score -= 10; signals.append("No certification information provided")
    return {"score": max(0.0, min(100.0, score)), "signals": signals}

def analyze(payload: dict, image_bytes: bytes | None = None) -> dict:
    start = time.perf_counter()
    img = analyze_image(image_bytes)
    txt = analyze_text(payload.get("product_name", ""), payload.get("brand", ""),
                       payload.get("description", ""), payload.get("certification_status", ""))
    price = analyze_price(float(payload.get("price", 0) or 0), float(payload.get("msrp", 0) or 0))
    auth = analyze_authorization(bool(payload.get("authorized")), payload.get("certification_status", ""))
    weights = {"image": 0.25 if img["available"] else 0.10, "text": 0.25, "price": 0.30, "auth": 0.20}
    total_w = sum(weights.values())
    authenticity = (img["score"] * weights["image"] + txt["score"] * weights["text"] +
                    price["score"] * weights["price"] + auth["score"] * weights["auth"]) / total_w
    authenticity = round(max(0.0, min(100.0, authenticity)), 2)
    counterfeit_probability = round(min(99.0, 100 - authenticity + 2), 2)
    if authenticity < 40:
        decision, risk_level = "REJECT", "CRITICAL"
    elif authenticity < 70:
        decision, risk_level = "REVIEW", "HIGH" if authenticity < 55 else "MEDIUM"
    else:
        decision, risk_level = "APPROVE", "LOW"
    reasons = img["signals"] + txt["signals"] + price["signals"] + auth["signals"]
    return {
        "authenticity_score": authenticity,
        "counterfeit_probability": counterfeit_probability,
        "risk_level": risk_level,
        "decision": decision,
        "reasons": reasons,
        "breakdown": {"image": img, "text": txt, "price": price, "authorization": auth},
        "model_version": settings.AUTH_MODEL_VERSION,
        "policy_version": settings.POLICY_VERSION,
        "mode": "DEMO_MODE",
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
    }
