"""Multi-agent orchestration layer.

REQUEST -> ORCHESTRATOR -> AGENT -> AI SCORE -> DETERMINISTIC GUARDRAILS
        -> FINAL DECISION -> AUDIT LOG -> RESPONSE
"""
from sqlalchemy.orm import Session
from app.services.risk_agent import agent as risk_agent
from app.services.authenticity_agent import agent as authenticity_agent
from app.services.review_agent import agent as review_agent
from app.utils.audit import write_audit
from app.config import settings

AGENT_NAMES = {
    "risk": "Risk Scoring Agent",
    "authenticity": "Authenticity & Integrity Agent",
    "review": "Review Moderation Agent",
}

class Orchestrator:
    """Routes to the correct specialised agent and applies policy guardrails."""

    def route(self, task: str, payload: dict, db: Session, actor: str = "system", **kwargs) -> dict:
        if task == "risk":
            result = risk_agent.analyze(payload)
            result = self._risk_guardrails(payload, result)
            score, level, decision = result["risk_score"], result["risk_level"], result["recommended_action"]
            reference = payload.get("order_id", "UNKNOWN")
        elif task == "authenticity":
            result = authenticity_agent.analyze(payload, kwargs.get("image_bytes"))
            result = self._authenticity_guardrails(payload, result)
            score, level, decision = result["authenticity_score"], result["risk_level"], result["decision"]
            reference = payload.get("listing_id", payload.get("product_name", "UNKNOWN"))
        elif task == "review":
            result = review_agent.analyze(payload, kwargs.get("peer_reviews"), kwargs.get("seller_recent_count", 0))
            result = self._review_guardrails(payload, result)
            score, level, decision = result["risk_score"], result["risk_level"], result["decision"]
            reference = payload.get("review_id", payload.get("product_id", "UNKNOWN"))
        else:
            raise ValueError(f"Unknown orchestration task: {task}")

        audit = write_audit(db, agent=AGENT_NAMES[task], reference=str(reference), risk_score=score,
                            risk_level=level, decision=decision, reasons=result["reasons"],
                            model_version=result["model_version"], actor=actor)
        result["audit_id"] = audit.audit_id
        result["policy_version"] = settings.POLICY_VERSION
        result["orchestrator"] = {"task": task, "agent": AGENT_NAMES[task], "guardrails_applied": True}
        return result

    # ---- deterministic guardrails (policy layer, always wins over the model) ----
    def _risk_guardrails(self, payload, result):
        f = result["features"]
        if f["is_cod"] and f["cod_refusals"] >= 5:
            result["recommended_action"] = "BLOCK_COD"
            result["risk_level"] = "CRITICAL"
            result["risk_score"] = max(result["risk_score"], 85.0)
            result["reasons"].append("GUARDRAIL: hard policy block - 5+ COD refusals")
        # Fairness guardrail: never escalate on account age alone
        if len(result["reasons"]) == 1 and "new" in result["reasons"][0].lower():
            result["recommended_action"] = "ALLOW"
            result["reasons"].append("FAIRNESS GUARDRAIL: account age alone is not a fraud signal")
        return result

    def _authenticity_guardrails(self, payload, result):
        dev = result["breakdown"]["price"].get("deviation_pct", 0)
        if dev >= 80 and not payload.get("authorized"):
            result["decision"] = "REJECT"
            result["risk_level"] = "CRITICAL"
            result["counterfeit_probability"] = max(result["counterfeit_probability"], 90.0)
            result["reasons"].append("GUARDRAIL: unauthorised seller with >80% price deviation")
        return result

    def _review_guardrails(self, payload, result):
        if result["coordination_probability"] >= 80:
            result["decision"] = "HIDE"
            result["risk_level"] = "CRITICAL"
            result["reasons"].append("GUARDRAIL: coordinated review ring participation")
        if payload.get("verified_purchase") and result["risk_score"] < 35:
            result["decision"] = "PUBLISH"
        return result

orchestrator = Orchestrator()
