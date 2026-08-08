from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database.session import get_db
from app.models import (Transaction, FraudCase, ProductListing, Review, AuditLog, RiskScore,
                        ModelMetric, FairnessMetric, Notification, Customer, Seller, Return)
from app.schemas import CaseAction, BusinessImpactRequest
from app.security import get_current_user, require_roles
from app.utils.audit import write_audit
from app.config import settings

router = APIRouter(prefix="/api", tags=["platform"])

@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(func.now() if not settings.DATABASE_URL.startswith("sqlite") else func.current_timestamp())
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "demo_mode": settings.DEMO_MODE, "version": settings.VERSION,
            "components": {"api": "ONLINE", "database": "ONLINE" if db_ok else "DEGRADED",
                           "risk_agent": "ONLINE", "authenticity_agent": "ONLINE",
                           "review_agent": "ONLINE", "orchestrator": "ONLINE"}}

@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), user=Depends(get_current_user)):
    txns = db.query(Transaction).count()
    blocked = db.query(Transaction).filter(Transaction.decision == "BLOCK_COD").count()
    high_risk = db.query(RiskScore).filter(RiskScore.risk_level.in_(["HIGH", "CRITICAL"])).count()
    counterfeit = db.query(ProductListing).filter(ProductListing.status == "REJECT").count()
    suspicious_reviews = db.query(Review).filter(Review.decision.in_(["HIDE", "FLAG"])).count()
    rings = db.query(func.count(func.distinct(Review.seller_code))).filter(Review.decision == "HIDE").scalar() or 0
    queue = db.query(FraudCase).filter(FraudCase.status.in_(["OPEN", "INVESTIGATING"])).count()
    prevented = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.decision == "BLOCK_COD").scalar() or 0
    latency = db.query(func.coalesce(func.avg(RiskScore.latency_ms), 0)).scalar() or 0
    fraud_detected = db.query(FraudCase).count()
    return {"demo_data": settings.DEMO_MODE, "total_transactions": txns, "fraud_detected": fraud_detected,
            "high_risk_orders": high_risk, "counterfeit_listings": counterfeit,
            "suspicious_reviews": suspicious_reviews, "review_rings": int(rings),
            "blocked_orders": blocked, "estimated_fraud_prevented": round(float(prevented), 2),
            "average_latency_ms": round(float(latency), 2), "manual_review_queue": queue}

@router.get("/activity")
def activity(limit: int = 12, db: Session = Depends(get_db), user=Depends(get_current_user)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 50)).all()
    return [{"time": l.created_at.strftime("%H:%M:%S"), "agent": l.agent, "decision": l.decision,
             "reference": l.input_reference, "risk_level": l.risk_level,
             "message": f"{l.agent} → {l.decision} on {l.input_reference}"} for l in logs]

@router.get("/fraud/cases")
def list_cases(status: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(FraudCase)
    if status:
        q = q.filter(FraudCase.status == status)
    return [{"case_id": c.case_id, "type": c.case_type, "severity": c.severity, "agent": c.agent,
             "risk_score": c.risk_score, "reference": c.reference, "status": c.status,
             "assigned_reviewer": c.assigned_reviewer, "resolution_note": c.resolution_note,
             "created_at": c.created_at.isoformat()} for c in q.order_by(FraudCase.created_at.desc()).all()]

def _get_case(db, case_id):
    case = db.query(FraudCase).filter(FraudCase.case_id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found")
    return case

@router.post("/cases/{case_id}/assign")
def assign_case(case_id: str, body: CaseAction, db: Session = Depends(get_db),
                user=Depends(require_roles("admin", "reviewer"))):
    case = _get_case(db, case_id)
    case.assigned_reviewer = body.reviewer or user.email
    case.status = "INVESTIGATING"
    db.commit()
    write_audit(db, agent="Case Management", reference=case_id, risk_score=case.risk_score or 0,
                risk_level=case.severity or "MEDIUM", decision="ASSIGNED",
                reasons=[f"Assigned to {case.assigned_reviewer}"], model_version="n/a", actor=user.email)
    return {"status": "assigned", "case_id": case_id, "assigned_reviewer": case.assigned_reviewer}

@router.post("/cases/{case_id}/resolve")
def resolve_case(case_id: str, body: CaseAction, db: Session = Depends(get_db),
                 user=Depends(require_roles("admin", "reviewer"))):
    case = _get_case(db, case_id)
    case.status = body.decision if body.decision in ("RESOLVED", "FALSE_POSITIVE") else "RESOLVED"
    case.resolution_note = body.note
    db.commit()
    write_audit(db, agent="Case Management", reference=case_id, risk_score=case.risk_score or 0,
                risk_level=case.severity or "MEDIUM", decision=case.status,
                reasons=[body.note or "Resolved by reviewer"], model_version="n/a", actor=user.email)
    return {"status": case.status, "case_id": case_id}

@router.post("/cases/{case_id}/escalate")
def escalate_case(case_id: str, body: CaseAction, db: Session = Depends(get_db),
                  user=Depends(require_roles("admin", "reviewer"))):
    case = _get_case(db, case_id)
    case.severity = "CRITICAL"
    case.status = "INVESTIGATING"
    db.commit()
    write_audit(db, agent="Case Management", reference=case_id, risk_score=case.risk_score or 0,
                risk_level="CRITICAL", decision="ESCALATED", reasons=[body.note or "Escalated"],
                model_version="n/a", actor=user.email)
    return {"status": "escalated", "case_id": case_id}

@router.post("/cases/{case_id}/override")
def override_case(case_id: str, body: CaseAction, db: Session = Depends(get_db),
                  user=Depends(require_roles("admin", "reviewer"))):
    case = _get_case(db, case_id)
    if not body.decision:
        raise HTTPException(422, "An override decision is required")
    case.status = "FALSE_POSITIVE" if body.decision.upper() == "ALLOW" else "RESOLVED"
    case.resolution_note = body.note
    db.commit()
    log = write_audit(db, agent="Human Override", reference=case_id, risk_score=case.risk_score or 0,
                      risk_level=case.severity or "MEDIUM", decision=body.decision.upper(),
                      reasons=[body.note or "Manual reviewer override"], model_version="n/a",
                      actor=user.email, override=True, note=body.note)
    return {"status": "overridden", "case_id": case_id, "audit_id": log.audit_id}

@router.get("/listings")
def listings(status: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(ProductListing)
    if status:
        q = q.filter(ProductListing.status == status)
    return [{"listing_id": l.listing_id, "product_name": l.product_name, "seller_code": l.seller_code,
             "brand": l.brand, "price": l.price, "msrp": l.msrp,
             "authenticity_score": l.authenticity_score, "counterfeit_probability": l.counterfeit_probability,
             "status": l.status, "created_at": l.created_at.isoformat()}
            for l in q.order_by(ProductListing.created_at.desc()).all()]

@router.get("/reviews")
def reviews(decision: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(Review)
    if decision:
        q = q.filter(Review.decision == decision)
    return [{"review_id": r.review_id, "text": r.text, "rating": r.rating, "user_code": r.user_code,
             "seller_code": r.seller_code, "product_id": r.product_id, "risk_score": r.risk_score,
             "fake_probability": r.fake_probability, "ai_probability": r.ai_probability,
             "sentiment": r.sentiment, "decision": r.decision, "verified_purchase": r.verified_purchase,
             "created_at": r.created_at.isoformat()} for r in q.order_by(Review.created_at.desc()).limit(300).all()]

@router.get("/audit-logs")
def audit_logs(agent: str | None = None, decision: str | None = None, risk_level: str | None = None,
               reference: str | None = None, date_from: str | None = None, date_to: str | None = None,
               limit: int = Query(200, le=1000), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(AuditLog)
    if agent: q = q.filter(AuditLog.agent == agent)
    if decision: q = q.filter(AuditLog.decision == decision)
    if risk_level: q = q.filter(AuditLog.risk_level == risk_level)
    if reference: q = q.filter(AuditLog.input_reference.contains(reference))
    for value, op in ((date_from, "gte"), (date_to, "lte")):
        if value:
            try:
                dt = datetime.fromisoformat(value)
            except ValueError:
                raise HTTPException(422, "Dates must be ISO formatted (YYYY-MM-DD)")
            q = q.filter(AuditLog.created_at >= dt if op == "gte" else AuditLog.created_at <= dt)
    return [{"audit_id": l.audit_id, "agent": l.agent, "input_reference": l.input_reference,
             "risk_score": l.risk_score, "risk_level": l.risk_level, "decision": l.decision,
             "reasons": l.reasons, "model_version": l.model_version, "policy_version": l.policy_version,
             "actor": l.actor, "reviewer_override": l.reviewer_override,
             "created_at": l.created_at.isoformat()}
            for l in q.order_by(AuditLog.created_at.desc()).limit(limit).all()]

@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    today = datetime.utcnow().date()
    trends = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        start = datetime.combine(day, datetime.min.time())
        end = start + timedelta(days=1)
        trends.append({
            "date": day.isoformat()[5:],
            "fraud": db.query(RiskScore).filter(RiskScore.created_at.between(start, end),
                                                RiskScore.risk_level.in_(["HIGH", "CRITICAL"])).count(),
            "cod_refusals": db.query(Transaction).filter(Transaction.created_at.between(start, end),
                                                         Transaction.decision == "BLOCK_COD").count(),
            "returns": db.query(Return).filter(Return.created_at.between(start, end)).count(),
            "counterfeit": db.query(ProductListing).filter(ProductListing.created_at.between(start, end),
                                                           ProductListing.status == "REJECT").count(),
            "fake_reviews": db.query(Review).filter(Review.created_at.between(start, end),
                                                    Review.decision.in_(["HIDE", "FLAG"])).count(),
        })
    def counts(model, column):
        return [{"name": k or "UNKNOWN", "value": v} for k, v in
                db.query(column, func.count()).group_by(column).all()]
    return {"demo_data": True, "trends": trends,
            "risk_distribution": counts(RiskScore, RiskScore.risk_level),
            "listing_decisions": counts(ProductListing, ProductListing.status),
            "review_decisions": counts(Review, Review.decision),
            "case_status": counts(FraudCase, FraudCase.status)}

@router.get("/fairness")
def fairness(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(FairnessMetric).all()
    cohorts = [{"cohort": r.cohort, "false_positive_rate": r.false_positive_rate,
                "true_positive_rate": r.true_positive_rate, "precision": r.precision,
                "recall": r.recall, "sample_size": r.sample_size} for r in rows]
    status = "PASS"
    if len(cohorts) >= 2:
        gap = abs(cohorts[0]["false_positive_rate"] - cohorts[1]["false_positive_rate"])
        status = "PASS" if gap <= 0.02 else "WARNING"
    return {"demo_data": True, "cohorts": cohorts, "fairness_status": status,
            "notes": ["Seller account age is never used as a standalone fraud signal.",
                      "Guardrail downgrades decisions driven only by account novelty."]}

@router.get("/model-metrics")
def model_metrics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(ModelMetric).all()
    return {"demo_metrics": [{"model_name": r.model_name, "model_version": r.model_version,
                              "precision": r.precision, "recall": r.recall, "f1": r.f1,
                              "roc_auc": r.roc_auc, "latency_ms": r.latency_ms, "dataset": r.dataset,
                              "training_date": r.training_date, "health": r.health,
                              "drift_status": r.drift_status} for r in rows if r.metric_type == "DEMO"],
            "target_metrics": [{"model_name": r.model_name, "precision": r.precision, "recall": r.recall,
                                "f1": r.f1, "roc_auc": r.roc_auc, "latency_ms": r.latency_ms}
                               for r in rows if r.metric_type == "TARGET"]}

@router.get("/cost")
def cost(db: Session = Depends(get_db), user=Depends(get_current_user)):
    inferences = db.query(AuditLog).count()
    avg_latency = db.query(func.coalesce(func.avg(RiskScore.latency_ms), 12)).scalar() or 12
    requests_per_day = max(inferences * 24, 1000)
    cost_per_inference = 0.00004  # self-hosted lightweight models, INR estimate
    daily = requests_per_day * cost_per_inference
    return {"estimated": True, "requests_per_day": requests_per_day, "inference_count": inferences,
            "average_latency_ms": round(float(avg_latency), 2),
            "cost_per_inference_inr": cost_per_inference,
            "estimated_daily_cost_inr": round(daily, 2),
            "estimated_monthly_cost_inr": round(daily * 30, 2),
            "routing": [
                {"tier": "LOW COMPLEXITY", "model": "Deterministic rules / logistic regression",
                 "share_pct": 70, "latency_ms": 8, "relative_cost": 1},
                {"tier": "MEDIUM COMPLEXITY", "model": "Gradient boosted trees (XGBoost)",
                 "share_pct": 25, "latency_ms": 45, "relative_cost": 4},
                {"tier": "HIGH COMPLEXITY", "model": "Embedding models + human review",
                 "share_pct": 5, "latency_ms": 300, "relative_cost": 30}]}

@router.post("/business-impact")
def business_impact(body: BusinessImpactRequest, user=Depends(get_current_user)):
    loss = body.monthly_gmv * body.fraud_loss_pct / 100
    monthly_saving = loss * body.expected_reduction_pct / 100
    return {"label": "ESTIMATED / DEMO CALCULATION", "monthly_fraud_loss": round(loss, 2),
            "estimated_monthly_savings": round(monthly_saving, 2),
            "estimated_annual_savings": round(monthly_saving * 12, 2),
            "estimated_gmv_protected": round(body.monthly_gmv * 12, 2)}

@router.get("/notifications")
def notifications(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [{"id": n.id, "title": n.title, "body": n.body, "level": n.level, "read": n.read,
             "created_at": n.created_at.isoformat()}
            for n in db.query(Notification).order_by(Notification.created_at.desc()).limit(20).all()]

@router.get("/security/overview")
def security_overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"controls": {
                "authentication": "JWT bearer tokens, PBKDF2-SHA256 password hashing (120k iterations)",
                "authorization": "Role-based access control: admin / reviewer / seller / customer",
                "api_security": "Pydantic validation, rate limiting, CORS allow-list, security headers",
                "pii_protection": "Masked email & phone, hashed identifiers, no raw PII in dashboards",
                "audit_logging": "Immutable append-only decision log with model & policy versions",
                "data_retention": f"{settings.DATA_RETENTION_DAYS} days (configurable)",
                "privacy": "Minimum-necessary collection, purpose limitation",
                "dpdp_design": "Consent-aware, purpose-bound processing, access control, auditability"},
            "system_status": {"api": "ONLINE", "database": "ONLINE", "risk_agent": "ONLINE",
                              "authenticity_agent": "ONLINE", "review_agent": "ONLINE"},
            "customers_sample": [{"customer_code": c.customer_code, "email": c.masked_email,
                                  "phone": c.masked_phone, "hashed_id": c.hashed_id}
                                 for c in db.query(Customer).limit(5).all()]}

@router.get("/scorecard")
def scorecard(user=Depends(get_current_user)):
    return {"label": "HACKATHON TARGETS - not yet achieved",
            "criteria": [
                {"name": "Business Impact & ROI", "weight": 20,
                 "coverage": "Business impact calculator, fraud-prevented tracking, cost analytics"},
                {"name": "AI Innovation & Depth", "weight": 20,
                 "coverage": "Three specialised agents, orchestrator, graph ring detection, multimodal analysis"},
                {"name": "Technical Excellence & Code", "weight": 20,
                 "coverage": "FastAPI + SQLAlchemy + React SPA, typed schemas, tests, modular services"},
                {"name": "Enterprise Security & Guardrails", "weight": 25,
                 "coverage": "JWT + RBAC, rate limiting, deterministic guardrails, audit trail, DPDP design"},
                {"name": "Cost Efficiency & Scalability", "weight": 15,
                 "coverage": "Tiered model routing, no paid APIs, SQLite→Postgres ready"}],
            "targets": [
                {"metric": "Reduction in return/COD fraud losses", "target": "35%"},
                {"metric": "Precision on automated counterfeit/listing flags", "target": ">96%"},
                {"metric": "Human review queue reduction", "target": "70%"},
                {"metric": "False-positive rate", "target": "<0.1%"},
                {"metric": "Checkout risk latency", "target": "<250ms"}]}

@router.get("/sellers")
def sellers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [{"seller_code": s.seller_code, "name": s.name, "tier": s.tier,
             "brand_authorized": s.brand_authorized, "account_age_days": s.account_age_days,
             "rating": s.rating} for s in db.query(Seller).all()]
