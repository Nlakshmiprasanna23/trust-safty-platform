import os
from functools import lru_cache

class Settings:
    APP_NAME = "AI-Powered Multi-Agent Trust & Safety Platform"
    VERSION = "1.0.0"
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trust_safety.db")
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-me")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "240"))
    DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "180"))
    RISK_MODEL_VERSION = "risk-model-v1"
    AUTH_MODEL_VERSION = "authenticity-model-v1"
    REVIEW_MODEL_VERSION = "review-model-v1"
    POLICY_VERSION = "policy-v1"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
