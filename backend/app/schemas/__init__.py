import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=4, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Enter a valid email address")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    email: str


class RiskRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=40)
    order_id: str = Field(default="ORD-1001", min_length=1, max_length=40)
    order_amount: float = Field(default=0, ge=0, le=10_000_000)

    payment_method: str = "COD"
    is_cod: bool = True

    previous_orders: int = Field(0, ge=0, le=100000)
    previous_returns: int = Field(0, ge=0, le=100000)
    cod_refusals: int = Field(0, ge=0, le=100000)

    account_age_days: int = Field(0, ge=0, le=20000)

    device_id: str = ""
    ip_address: str = ""
    ip_velocity: int = Field(1, ge=0, le=1000)

    new_device: bool = False
    payment_risk_flag: bool = False
    location_mismatch: bool = False


class AuthenticityRequest(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    brand: str = Field("", max_length=80)
    description: str = Field("", max_length=5000)

    price: float = Field(0, ge=0)
    msrp: float = Field(0, ge=0)

    seller_code: str = "SEL-000"
    authorized: bool = False
    certification_status: str = Field("", max_length=200)

    listing_id: Optional[str] = None


class ReviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    rating: int = Field(5, ge=1, le=5)

    user_code: str = "USR-000"
    seller_code: str = "SEL-000"
    product_id: str = "PRD-000"

    account_age_days: int = Field(100, ge=0, le=20000)
    verified_purchase: bool = True

    review_id: Optional[str] = None


class CaseAction(BaseModel):
    reviewer: Optional[str] = Field(None, max_length=120)
    note: Optional[str] = Field(None, max_length=1000)
    decision: Optional[str] = Field(None, max_length=40)


class BusinessImpactRequest(BaseModel):
    monthly_gmv: float = Field(ge=0)
    fraud_loss_pct: float = Field(ge=0, le=100)
    expected_reduction_pct: float = Field(ge=0, le=100)


class GenericResponse(BaseModel):
    status: str
    data: Any | None = None