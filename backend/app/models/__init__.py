from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON)
from app.database.session import Base

def now():
    return datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(120))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), default="reviewer")  # admin|reviewer|seller|customer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)

class Seller(Base):
    __tablename__ = "sellers"
    id = Column(Integer, primary_key=True)
    seller_code = Column(String(32), unique=True, index=True)
    name = Column(String(160))
    tier = Column(String(32), default="new")  # new|small|established
    brand_authorized = Column(Boolean, default=False)
    account_age_days = Column(Integer, default=30)
    rating = Column(Float, default=4.0)
    created_at = Column(DateTime, default=now)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    customer_code = Column(String(32), unique=True, index=True)
    masked_email = Column(String(160))
    masked_phone = Column(String(60))
    hashed_id = Column(String(64))
    account_age_days = Column(Integer, default=100)
    previous_orders = Column(Integer, default=0)
    cod_refusals = Column(Integer, default=0)
    returns_count = Column(Integer, default=0)
    city = Column(String(80))
    created_at = Column(DateTime, default=now)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    order_id = Column(String(40), unique=True, index=True)
    customer_code = Column(String(32), index=True)
    seller_code = Column(String(32), index=True)
    amount = Column(Float)
    payment_method = Column(String(32))
    is_cod = Column(Boolean, default=False)
    status = Column(String(32), default="PLACED")
    risk_score = Column(Float, default=0)
    decision = Column(String(32), default="ALLOW")
    created_at = Column(DateTime, default=now)

class Return(Base):
    __tablename__ = "returns"
    id = Column(Integer, primary_key=True)
    return_id = Column(String(40), unique=True)
    order_id = Column(String(40), index=True)
    customer_code = Column(String(32), index=True)
    reason = Column(String(160))
    suspicious = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)

class FraudCase(Base):
    __tablename__ = "fraud_cases"
    id = Column(Integer, primary_key=True)
    case_id = Column(String(40), unique=True, index=True)
    case_type = Column(String(48))
    severity = Column(String(24))
    agent = Column(String(48))
    risk_score = Column(Float)
    reference = Column(String(64))
    status = Column(String(32), default="OPEN")
    assigned_reviewer = Column(String(120), nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

class ProductListing(Base):
    __tablename__ = "product_listings"
    id = Column(Integer, primary_key=True)
    listing_id = Column(String(40), unique=True, index=True)
    product_name = Column(String(200))
    brand = Column(String(80))
    description = Column(Text)
    seller_code = Column(String(32), index=True)
    price = Column(Float)
    msrp = Column(Float)
    authorized = Column(Boolean, default=False)
    certification_status = Column(String(120))
    authenticity_score = Column(Float, default=0)
    counterfeit_probability = Column(Float, default=0)
    status = Column(String(24), default="REVIEW")
    created_at = Column(DateTime, default=now)

class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True)
    listing_id = Column(String(40), index=True)
    filename = Column(String(255))
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    analysis = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now)

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    review_id = Column(String(40), unique=True, index=True)
    text = Column(Text)
    rating = Column(Integer)
    user_code = Column(String(32), index=True)
    seller_code = Column(String(32), index=True)
    product_id = Column(String(40), index=True)
    account_age_days = Column(Integer, default=100)
    verified_purchase = Column(Boolean, default=True)
    risk_score = Column(Float, default=0)
    fake_probability = Column(Float, default=0)
    ai_probability = Column(Float, default=0)
    sentiment = Column(String(24), default="NEUTRAL")
    decision = Column(String(24), default="PUBLISH")
    created_at = Column(DateTime, default=now)

class ReviewCluster(Base):
    __tablename__ = "review_clusters"
    id = Column(Integer, primary_key=True)
    cluster_id = Column(String(40), unique=True)
    seller_code = Column(String(32), index=True)
    members = Column(JSON, default=list)
    coordination_score = Column(Float, default=0)
    detected_at = Column(DateTime, default=now)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True)
    order_id = Column(String(40), index=True)
    customer_code = Column(String(32), index=True)
    score = Column(Float)
    fraud_probability = Column(Float)
    risk_level = Column(String(24))
    decision = Column(String(32))
    reasons = Column(JSON, default=list)
    latency_ms = Column(Float, default=0)
    model_version = Column(String(48))
    created_at = Column(DateTime, default=now)

class AuthenticityScore(Base):
    __tablename__ = "authenticity_scores"
    id = Column(Integer, primary_key=True)
    listing_id = Column(String(40), index=True)
    authenticity_score = Column(Float)
    counterfeit_probability = Column(Float)
    risk_level = Column(String(24))
    decision = Column(String(24))
    reasons = Column(JSON, default=list)
    breakdown = Column(JSON, default=dict)
    model_version = Column(String(48))
    created_at = Column(DateTime, default=now)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    audit_id = Column(String(40), unique=True, index=True)
    agent = Column(String(64), index=True)
    input_reference = Column(String(64), index=True)
    risk_score = Column(Float, default=0)
    risk_level = Column(String(24), index=True)
    decision = Column(String(32), index=True)
    reasons = Column(JSON, default=list)
    model_version = Column(String(48))
    policy_version = Column(String(48))
    actor = Column(String(120))
    reviewer_override = Column(Boolean, default=False)
    override_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now, index=True)

class ModelMetric(Base):
    __tablename__ = "model_metrics"
    id = Column(Integer, primary_key=True)
    model_name = Column(String(64))
    model_version = Column(String(48))
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    roc_auc = Column(Float)
    latency_ms = Column(Float)
    dataset = Column(String(120))
    training_date = Column(String(40))
    health = Column(String(24), default="HEALTHY")
    drift_status = Column(String(24), default="STABLE")
    metric_type = Column(String(24), default="DEMO")

class FairnessMetric(Base):
    __tablename__ = "fairness_metrics"
    id = Column(Integer, primary_key=True)
    cohort = Column(String(48))
    false_positive_rate = Column(Float)
    true_positive_rate = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    sample_size = Column(Integer)
    status = Column(String(24), default="PASS")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    title = Column(String(160))
    body = Column(Text)
    level = Column(String(24), default="info")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)
