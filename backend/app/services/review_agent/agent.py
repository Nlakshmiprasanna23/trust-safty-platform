"""Agent 3 - Review Moderation Agent (TF-IDF + heuristics + graph ring detection)."""
import time, re, math
from collections import defaultdict
from app.config import settings

POSITIVE = {"great","excellent","amazing","love","perfect","best","awesome","fantastic","superb","good","happy"}
NEGATIVE = {"bad","worst","terrible","poor","broken","fake","waste","awful","refund","defective","horrible"}
AI_MARKERS = ["overall,", "in conclusion", "moreover", "furthermore", "highly recommend this product",
              "it is worth noting", "delve", "seamless experience", "game changer", "top-notch quality"]
GENERIC = ["good product", "nice product", "value for money", "best product", "must buy", "loved it"]

def _tokens(text: str):
    return [t for t in re.findall(r"[a-z']+", (text or "").lower()) if len(t) > 2]

def cosine_similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    va, vb = defaultdict(int), defaultdict(int)
    for t in ta: va[t] += 1
    for t in tb: vb[t] += 1
    common = set(va) & set(vb)
    num = sum(va[t] * vb[t] for t in common)
    den = math.sqrt(sum(v*v for v in va.values())) * math.sqrt(sum(v*v for v in vb.values()))
    return round(num / den, 3) if den else 0.0

def sentiment_of(text: str) -> str:
    t = set(_tokens(text))
    p, n = len(t & POSITIVE), len(t & NEGATIVE)
    if p > n: return "POSITIVE"
    if n > p: return "NEGATIVE"
    return "NEUTRAL"

def analyze(payload: dict, peer_reviews: list[str] | None = None,
            seller_recent_count: int = 0) -> dict:
    start = time.perf_counter()
    text = payload.get("text", "") or ""
    words = _tokens(text)
    reasons = []
    risk = 5.0
    fake_p = 8.0
    ai_p = 5.0

    if len(words) < 8:
        risk += 15; fake_p += 18; reasons.append("Very short review with little specific detail")
    if any(g in text.lower() for g in GENERIC):
        risk += 12; fake_p += 15; reasons.append("Generic template phrasing common in incentivised reviews")
    if not payload.get("verified_purchase", True):
        risk += 18; fake_p += 20; reasons.append("Review is not tied to a verified purchase")
    if int(payload.get("account_age_days", 100)) < 14:
        risk += 14; fake_p += 12; reasons.append(f"Reviewer account is only {payload.get('account_age_days')} days old")
    if int(payload.get("rating", 3)) in (1, 5) and len(words) < 15:
        risk += 8; reasons.append("Extreme rating with minimal justification")
    repeats = [w for w in set(words) if words.count(w) >= 4]
    if repeats:
        risk += 8; fake_p += 8; reasons.append(f"Repetitive phrasing: {', '.join(repeats[:3])}")
    ai_hits = [m for m in AI_MARKERS if m in text.lower()]
    if ai_hits:
        ai_p += 45; risk += 14; reasons.append(f"AI-style discourse markers detected: {', '.join(ai_hits[:2])}")
    if len(words) > 40 and len(set(words)) / max(len(words), 1) > 0.85:
        ai_p += 22; reasons.append("Unusually high lexical diversity - typical of generated text")

    max_sim, sim_source = 0.0, None
    for peer in (peer_reviews or []):
        s = cosine_similarity(text, peer)
        if s > max_sim:
            max_sim, sim_source = s, peer[:80]
    if max_sim >= 0.75:
        risk += 22; fake_p += 25
        reasons.append(f"High textual similarity ({int(max_sim*100)}%) to another review for the same seller")

    coordination = 0.0
    if seller_recent_count >= 5:
        coordination = min(95.0, 30 + seller_recent_count * 6)
        risk += 18; reasons.append(f"Review burst: {seller_recent_count} reviews for this seller in a short window")
    coordination = round(min(99.0, coordination + max_sim * 40), 2)

    risk = round(max(0.0, min(100.0, risk)), 2)
    fake_p = round(max(0.0, min(99.0, fake_p + risk * 0.35)), 2)
    ai_p = round(max(0.0, min(99.0, ai_p)), 2)
    if not reasons:
        reasons.append("No manipulation signals detected")

    if risk >= 70 or fake_p >= 75:
        decision = "HIDE"
    elif risk >= 40:
        decision = "FLAG"
    else:
        decision = "PUBLISH"
    level = "CRITICAL" if risk >= 80 else "HIGH" if risk >= 60 else "MEDIUM" if risk >= 35 else "LOW"
    return {
        "risk_score": risk, "fake_probability": fake_p, "ai_generated_probability": ai_p,
        "coordination_probability": coordination, "sentiment": sentiment_of(text),
        "max_similarity": max_sim, "similar_to": sim_source, "risk_level": level,
        "decision": decision, "reasons": reasons,
        "model_version": settings.REVIEW_MODEL_VERSION, "policy_version": settings.POLICY_VERSION,
        "mode": "DEMO_RULES", "latency_ms": round((time.perf_counter() - start) * 1000, 2),
    }

def detect_rings(reviews: list[dict], similarity_threshold: float = 0.55) -> dict:
    """Graph-based review-ring detector: users are nodes, shared sellers are edges."""
    nodes, edges, clusters = {}, [], []
    by_seller = defaultdict(list)
    for r in reviews:
        by_seller[r["seller_code"]].append(r)
        nodes.setdefault(r["user_code"], {
            "id": r["user_code"], "type": "user", "reviews": 0, "sellers": set(),
            "account_age_days": r.get("account_age_days", 0), "risk": 0.0,
            "last_activity": str(r.get("created_at", "")),
        })
        nodes[r["user_code"]]["reviews"] += 1
        nodes[r["user_code"]]["sellers"].add(r["seller_code"])

    for seller, group in by_seller.items():
        nodes.setdefault(seller, {"id": seller, "type": "seller", "reviews": len(group),
                                  "sellers": set(), "account_age_days": 0, "risk": 0.0,
                                  "last_activity": ""})
        suspicious_users = set()
        for i, a in enumerate(group):
            for b in group[i+1:]:
                sim = cosine_similarity(a["text"], b["text"])
                if sim >= similarity_threshold:
                    suspicious_users.update([a["user_code"], b["user_code"]])
        for r in group:
            edges.append({"source": r["user_code"], "target": seller,
                          "suspicious": r["user_code"] in suspicious_users})
        if len(suspicious_users) >= 3:
            score = round(min(99.0, 40 + len(suspicious_users) * 12), 2)
            for u in suspicious_users:
                nodes[u]["risk"] = max(nodes[u]["risk"], score)
            nodes[seller]["risk"] = score
            clusters.append({"cluster_id": f"RING-{seller}", "seller_code": seller,
                             "members": sorted(suspicious_users), "coordination_score": score,
                             "size": len(suspicious_users)})
    out_nodes = []
    for n in nodes.values():
        n = dict(n); n["sellers"] = sorted(n["sellers"]); out_nodes.append(n)
    return {"nodes": out_nodes, "edges": edges, "clusters": clusters}
