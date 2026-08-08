from sqlalchemy.orm import Session
from app.models import AuditLog
from app.config import settings
from datetime import datetime

def next_audit_id(db: Session) -> str:
    count = db.query(AuditLog).count() + 1
    return f"AUD-{datetime.utcnow().year}-{count:06d}"

def write_audit(db: Session, *, agent: str, reference: str, risk_score: float, risk_level: str,
                decision: str, reasons: list, model_version: str, actor: str = "system",
                override: bool = False, note: str | None = None) -> AuditLog:
    log = AuditLog(
        audit_id=next_audit_id(db), agent=agent, input_reference=reference,
        risk_score=risk_score, risk_level=risk_level, decision=decision, reasons=reasons,
        model_version=model_version, policy_version=settings.POLICY_VERSION,
        actor=actor, reviewer_override=override, override_note=note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
