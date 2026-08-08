"""Seeds the SQLite database with realistic Indian-marketplace demo data.

Run:  python -m app.seed
"""
import random, uuid
from datetime import datetime, timedelta
from app.database.session import SessionLocal, init_db
from app.security import hash_password
from app.utils.privacy import mask_email, mask_phone, hash_identifier
from app.models import (User, Seller, Customer, Transaction, Return, FraudCase, ProductListing,
                        Review, ReviewCluster, RiskScore, AuthenticityScore, AuditLog,
                        ModelMetric, FairnessMetric, Notification)

random.seed(42)

DEMO_USERS = [
    ("admin@trustsafe.local", "Aarav Mehta", "Admin@123", "admin"),
    ("reviewer@trustsafe.local", "Priya Nair", "Review@123", "reviewer"),
    ("seller@trustsafe.local", "Rohit Sharma", "Seller@123", "seller"),
    ("customer@trustsafe.local", "Ananya Rao", "Customer@123", "customer"),
]

CITIES = ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune", "Jaipur", "Kolkata", "Chennai"]
BRANDS = ["Luxe Milano", "Nordwear", "AudioPeak", "GlowMax", "TrekPro", "Solstice"]
PRODUCTS = ["Leather Tote Bag", "Wireless Earbuds", "Running Shoes", "Fairness Cream",
            "Trekking Backpack", "Smart Watch", "Cotton Kurta", "Bluetooth Speaker"]
PRICES = [499, 1299, 2499, 4999, 8999, 19999]

def seed():
    init_db()
    db = SessionLocal()
    if db.query(User).count():
        print("Database already seeded. Delete trust_safety.db to reseed.")
        db.close(); return

    for email, name, pwd, role in DEMO_USERS:
        db.add(User(email=email, full_name=name, password_hash=hash_password(pwd), role=role))

    sellers = []
    for i in range(1, 13):
        tier = "established" if i <= 5 else ("small" if i <= 9 else "new")
        s = Seller(seller_code=f"SEL-{200+i}", name=f"{random.choice(['Kiran','Vertex','Bharat','Nova','Sunrise'])} Traders {i}",
                   tier=tier, brand_authorized=tier == "established",
                   account_age_days={"established": 1500, "small": 400, "new": 45}[tier],
                   rating=round(random.uniform(3.2, 4.9), 1))
        sellers.append(s); db.add(s)

    customers = []
    for i in range(1, 41):
        email = f"user{i}@example.com"
        phone = f"98{random.randint(10000000, 99999999)}"
        prev = random.randint(1, 80)
        c = Customer(customer_code=f"CUS-{40000+i}", masked_email=mask_email(email),
                     masked_phone=mask_phone(phone), hashed_id=hash_identifier(email),
                     account_age_days=random.randint(5, 1500), previous_orders=prev,
                     cod_refusals=random.choice([0, 0, 0, 1, 2, 5]),
                     returns_count=random.randint(0, 6), city=random.choice(CITIES))
        customers.append(c); db.add(c)
    db.commit()

    now = datetime.utcnow()
    audit_n = 0
    for i in range(260):
        c = random.choice(customers)
        s = random.choice(sellers)
        created = now - timedelta(days=random.randint(0, 13), hours=random.randint(0, 23))
        amount = float(random.choice(PRICES))
        is_cod = random.random() < 0.55
        risky = c.cod_refusals >= 2 and is_cod
        score = round(random.uniform(62, 94) if risky else random.uniform(4, 48), 2)
        level = "CRITICAL" if score >= 80 else "HIGH" if score >= 60 else "MEDIUM" if score >= 35 else "LOW"
        decision = "BLOCK_COD" if (level in ("HIGH", "CRITICAL") and is_cod) else \
                   "MANUAL_REVIEW" if level in ("HIGH", "CRITICAL") else \
                   "VERIFY" if level == "MEDIUM" else "ALLOW"
        order_id = f"ORD-{10000+i}"
        db.add(Transaction(order_id=order_id, customer_code=c.customer_code, seller_code=s.seller_code,
                           amount=amount, payment_method="COD" if is_cod else random.choice(["UPI", "CARD", "NETBANKING"]),
                           is_cod=is_cod, status="BLOCKED" if decision == "BLOCK_COD" else "PLACED",
                           risk_score=score, decision=decision, created_at=created))
        reasons = ["COD refusal frequency", "Device mismatch", "High IP velocity"] if risky else ["No material risk signals detected"]
        db.add(RiskScore(order_id=order_id, customer_code=c.customer_code, score=score,
                         fraud_probability=round(min(99, score * .95 + 3), 2), risk_level=level,
                         decision=decision, reasons=reasons, latency_ms=round(random.uniform(6, 60), 2),
                         model_version="risk-model-v1", created_at=created))
        audit_n += 1
        db.add(AuditLog(audit_id=f"AUD-{now.year}-{audit_n:06d}", agent="Risk Scoring Agent",
                        input_reference=order_id, risk_score=score, risk_level=level, decision=decision,
                        reasons=reasons, model_version="risk-model-v1", policy_version="policy-v1",
                        actor="system", created_at=created))
        if random.random() < 0.18:
            db.add(Return(return_id=f"RET-{20000+i}", order_id=order_id, customer_code=c.customer_code,
                          reason=random.choice(["Item not as described", "Empty box claim", "Damaged", "Changed mind"]),
                          suspicious=risky, created_at=created + timedelta(days=2)))
        if level in ("HIGH", "CRITICAL") and random.random() < 0.35:
            db.add(FraudCase(case_id=f"CASE-{uuid.uuid4().hex[:8].upper()}", case_type="COD/Return Fraud",
                             severity=level, agent="Risk Scoring Agent", risk_score=score,
                             reference=order_id, status=random.choice(["OPEN", "INVESTIGATING", "RESOLVED"]),
                             created_at=created))
    db.commit()

    for i in range(70):
        s = random.choice(sellers)
        brand = random.choice(BRANDS)
        msrp = float(random.choice([1999, 4999, 9999, 10000, 24999]))
        counterfeit = random.random() < 0.3
        price = round(msrp * (random.uniform(0.08, 0.25) if counterfeit else random.uniform(0.7, 0.98)))
        auth_score = round(random.uniform(8, 38) if counterfeit else random.uniform(62, 96), 2)
        status = "REJECT" if auth_score < 40 else "REVIEW" if auth_score < 70 else "APPROVE"
        created = now - timedelta(days=random.randint(0, 13))
        lid = f"LST-{30000+i}"
        db.add(ProductListing(listing_id=lid, product_name=f"{brand} {random.choice(PRODUCTS)}",
                              brand=brand, description="Premium quality product for the Indian market.",
                              seller_code=s.seller_code, price=price, msrp=msrp,
                              authorized=s.brand_authorized, certification_status="BIS" if s.brand_authorized else "",
                              authenticity_score=auth_score,
                              counterfeit_probability=round(100 - auth_score, 2), status=status,
                              created_at=created))
        db.add(AuthenticityScore(listing_id=lid, authenticity_score=auth_score,
                                 counterfeit_probability=round(100 - auth_score, 2),
                                 risk_level="CRITICAL" if status == "REJECT" else "MEDIUM" if status == "REVIEW" else "LOW",
                                 decision=status, reasons=["Price deviation", "Authorization status"],
                                 breakdown={}, model_version="authenticity-model-v1", created_at=created))
        audit_n += 1
        db.add(AuditLog(audit_id=f"AUD-{now.year}-{audit_n:06d}", agent="Authenticity & Integrity Agent",
                        input_reference=lid, risk_score=auth_score,
                        risk_level="CRITICAL" if status == "REJECT" else "LOW", decision=status,
                        reasons=["Price deviation vs MSRP", "Seller authorisation check"],
                        model_version="authenticity-model-v1", policy_version="policy-v1",
                        actor="system", created_at=created))
        if status == "REJECT":
            db.add(FraudCase(case_id=f"CASE-{uuid.uuid4().hex[:8].upper()}", case_type="Counterfeit Listing",
                             severity="CRITICAL", agent="Authenticity & Integrity Agent",
                             risk_score=round(100 - auth_score, 2), reference=lid, status="OPEN",
                             created_at=created))
    db.commit()

    ring_seller = sellers[10].seller_code
    ring_texts = ["Best product must buy, amazing quality and fast delivery, highly recommend this product",
                  "Best product must buy, amazing quality and quick delivery, highly recommend this product",
                  "Must buy best product, amazing quality and fast delivery, highly recommend it",
                  "Amazing quality best product must buy, fast delivery, highly recommend this product"]
    genuine = ["The fabric is soft but the stitching near the sleeve came loose after two washes.",
               "Battery lasts about six hours on my commute which is fine for the price.",
               "Delivery took four days to Pune. Packaging was sealed and the invoice was included.",
               "Sizing runs small, I would order one size up next time."]
    idx = 0
    for i, txt in enumerate(ring_texts * 2):
        idx += 1
        created = now - timedelta(hours=random.randint(1, 20))
        db.add(Review(review_id=f"REV-{50000+idx}", text=txt, rating=5, user_code=f"USR-99{i:02d}",
                      seller_code=ring_seller, product_id="PRD-5521", account_age_days=random.randint(2, 12),
                      verified_purchase=False, risk_score=88, fake_probability=91, ai_probability=54,
                      sentiment="POSITIVE", decision="HIDE", created_at=created))
        audit_n += 1
        db.add(AuditLog(audit_id=f"AUD-{now.year}-{audit_n:06d}", agent="Review Moderation Agent",
                        input_reference=f"REV-{50000+idx}", risk_score=88, risk_level="CRITICAL",
                        decision="HIDE", reasons=["High textual similarity", "Review burst", "Unverified purchase"],
                        model_version="review-model-v1", policy_version="policy-v1", actor="system",
                        created_at=created))
    for i in range(60):
        idx += 1
        s = random.choice(sellers)
        created = now - timedelta(days=random.randint(0, 13))
        db.add(Review(review_id=f"REV-{50000+idx}", text=random.choice(genuine),
                      rating=random.randint(3, 5), user_code=f"USR-{1000+i}", seller_code=s.seller_code,
                      product_id=f"PRD-{5000+i}", account_age_days=random.randint(60, 900),
                      verified_purchase=True, risk_score=round(random.uniform(3, 28), 2),
                      fake_probability=round(random.uniform(2, 20), 2),
                      ai_probability=round(random.uniform(1, 15), 2), sentiment="POSITIVE",
                      decision="PUBLISH", created_at=created))
    db.add(ReviewCluster(cluster_id=f"RING-{ring_seller}", seller_code=ring_seller,
                         members=[f"USR-99{i:02d}" for i in range(8)], coordination_score=92.0))
    db.add(FraudCase(case_id=f"CASE-{uuid.uuid4().hex[:8].upper()}", case_type="Review Ring",
                     severity="CRITICAL", agent="Review Moderation Agent", risk_score=92,
                     reference=ring_seller, status="INVESTIGATING", assigned_reviewer="reviewer@trustsafe.local"))

    demo_metrics = [("Risk Scoring Model", "risk-model-v1", .91, .88, .89, .94, 18, "Synthetic demo set (IEEE-CIS ready)"),
                    ("Authenticity Model", "authenticity-model-v1", .87, .83, .85, .90, 62, "Synthetic demo set (INNV ready)"),
                    ("Review Moderation Model", "review-model-v1", .89, .86, .87, .92, 24, "Synthetic demo set (OpSpam ready)")]
    for name, ver, p, r, f1, auc, lat, ds in demo_metrics:
        db.add(ModelMetric(model_name=name, model_version=ver, precision=p, recall=r, f1=f1, roc_auc=auc,
                           latency_ms=lat, dataset=ds, training_date="2026-01-15", health="HEALTHY",
                           drift_status="STABLE", metric_type="DEMO"))
        db.add(ModelMetric(model_name=name, model_version="target", precision=.96, recall=.92, f1=.94,
                           roc_auc=.97, latency_ms=250, dataset="Hackathon target", training_date="-",
                           health="TARGET", drift_status="-", metric_type="TARGET"))

    db.add(FairnessMetric(cohort="New / small sellers", false_positive_rate=0.021, true_positive_rate=0.87,
                          precision=0.89, recall=0.87, sample_size=420, status="PASS"))
    db.add(FairnessMetric(cohort="Established sellers", false_positive_rate=0.018, true_positive_rate=0.89,
                          precision=0.91, recall=0.89, sample_size=1180, status="PASS"))

    db.add(Notification(title="Review ring detected", body=f"Coordinated cluster on {ring_seller}", level="critical"))
    db.add(Notification(title="Counterfeit listings queued", body="12 listings await reviewer action", level="warning"))
    db.add(Notification(title="Model health nominal", body="No drift detected in the last 24h", level="info"))
    db.commit()
    print(f"Seeded: {db.query(Transaction).count()} transactions, {db.query(ProductListing).count()} listings, "
          f"{db.query(Review).count()} reviews, {db.query(AuditLog).count()} audit logs.")
    db.close()

if __name__ == "__main__":
    seed()
