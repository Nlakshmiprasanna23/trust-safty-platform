import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(tempfile.gettempdir(), 'test_ts.db')}"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import init_db, SessionLocal
from app.models import User, AuditLog
from app.security import hash_password

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup():
    init_db()
    db = SessionLocal()
    if not db.query(User).filter(User.email == "admin@trustsafe.local").first():
        db.add(User(email="admin@trustsafe.local", full_name="Admin", role="admin",
                    password_hash=hash_password("Admin@123")))
        db.commit()
    db.close()

def token():
    r = client.post("/api/auth/login", json={"email": "admin@trustsafe.local", "password": "Admin@123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_health():
    assert client.get("/api/health").json()["status"] == "ok"

def test_login_rejects_bad_password():
    assert client.post("/api/auth/login", json={"email": "admin@trustsafe.local", "password": "wrong"}).status_code == 401

def test_protected_route_requires_auth():
    assert client.get("/api/dashboard/stats").status_code == 401

def test_risk_endpoint_and_audit_log():
    before = SessionLocal().query(AuditLog).count()
    r = client.post("/api/risk/analyze", headers=token(), json={
        "customer_id": "CUS-1", "order_id": "ORD-TEST-1", "order_amount": 19999, "is_cod": True,
        "previous_orders": 9, "previous_returns": 4, "cod_refusals": 5, "account_age_days": 42,
        "ip_velocity": 7, "new_device": True})
    assert r.status_code == 200
    body = r.json()
    assert body["recommended_action"] == "BLOCK_COD"
    assert body["audit_id"].startswith("AUD-")
    assert SessionLocal().query(AuditLog).count() == before + 1

def test_review_endpoint():
    r = client.post("/api/reviews/analyze", headers=token(), json={
        "text": "Best product must buy", "rating": 5, "user_code": "USR-1",
        "seller_code": "SEL-1", "product_id": "PRD-1", "account_age_days": 2,
        "verified_purchase": False})
    assert r.status_code == 200 and r.json()["decision"] in ("HIDE", "FLAG")

def test_authenticity_endpoint():
    r = client.post("/api/authenticity/analyze", headers=token(), data={
        "product_name": "Luxe Milano Tote 7a quality", "brand": "Luxe Milano",
        "description": "master copy replica first copy no bill", "price": 1299, "msrp": 10000,
        "authorized": "false", "certification_status": "self certified"})
    assert r.status_code == 200 and r.json()["decision"] == "REJECT"

def test_validation_error():
    assert client.post("/api/risk/analyze", headers=token(), json={"order_id": "x"}).status_code == 422

def test_audit_logs_listing():
    assert client.get("/api/audit-logs?limit=5", headers=token()).status_code == 200
