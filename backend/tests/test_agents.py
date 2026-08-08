import pytest
from app.services.risk_agent import agent as risk_agent
from app.services.authenticity_agent import agent as auth_agent
from app.services.review_agent import agent as review_agent

def test_risk_agent_flags_high_risk_cod():
    r = risk_agent.analyze({"order_amount": 19999, "is_cod": True, "previous_orders": 9,
                            "previous_returns": 4, "cod_refusals": 5, "account_age_days": 42,
                            "ip_velocity": 7, "new_device": True, "location_mismatch": True})
    assert r["risk_level"] in ("HIGH", "CRITICAL")
    assert r["recommended_action"] in ("BLOCK_COD", "MANUAL_REVIEW")
    assert r["latency_ms"] < 250
    assert len(r["reasons"]) >= 3

def test_risk_agent_allows_genuine_customer():
    r = risk_agent.analyze({"order_amount": 4999, "is_cod": False, "previous_orders": 68,
                            "previous_returns": 1, "cod_refusals": 0, "account_age_days": 1120,
                            "ip_velocity": 1})
    assert r["risk_level"] == "LOW"
    assert r["recommended_action"] == "ALLOW"

def test_authenticity_agent_rejects_counterfeit():
    r = auth_agent.analyze({"product_name": "Luxe Milano Tote 7a quality", "brand": "Luxe Milano",
                            "description": "master copy replica first copy no bill",
                            "price": 1299, "msrp": 10000, "authorized": False,
                            "certification_status": "self certified"})
    assert r["decision"] == "REJECT"
    assert r["counterfeit_probability"] > 60
    assert r["breakdown"]["price"]["deviation_pct"] == 87.01

def test_authenticity_agent_approves_genuine():
    r = auth_agent.analyze({"product_name": "Nordwear Running Shoes", "brand": "Nordwear",
                            "description": "Nordwear breathable mesh running shoes with cushioned midsole and BIS marked packaging for daily training.",
                            "price": 4200, "msrp": 4999, "authorized": True,
                            "certification_status": "BIS certified"})
    assert r["decision"] == "APPROVE"

def test_review_agent_detects_fake():
    r = review_agent.analyze({"text": "Best product must buy. Overall, in conclusion highly recommend this product.",
                              "rating": 5, "account_age_days": 3, "verified_purchase": False})
    assert r["decision"] in ("HIDE", "FLAG")
    assert r["ai_generated_probability"] > 20

def test_review_ring_detection():
    text = "Best product must buy amazing quality fast delivery highly recommend"
    reviews = [{"user_code": f"USR-{i}", "seller_code": "SEL-207", "text": text,
                "account_age_days": 3, "created_at": ""} for i in range(4)]
    out = review_agent.detect_rings(reviews)
    assert out["clusters"] and out["clusters"][0]["size"] >= 3
