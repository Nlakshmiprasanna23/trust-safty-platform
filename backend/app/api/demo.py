from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.security import get_current_user


router = APIRouter(prefix="/api/demo", tags=["demo"])


# ============================================================
# DEMO SCENARIOS
# ============================================================

SCENARIOS = {

    # ========================================================
    # 1. HIGH-RISK COD ORDER
    # ========================================================
    "high_risk_cod": {
        "id": "high_risk_cod",
        "title": "HIGH-RISK COD ORDER",
        "agent": "risk",

        "description": (
            "Repeat COD refuser placing a high-value "
            "cash-on-delivery order from a new device."
        ),

        "steps": [
            "Customer is placing a high-value COD order.",
            "Customer has a history of multiple previous orders and returns.",
            "Customer has several previous COD refusals.",
            "The account is relatively new.",
            "The order is coming from a new device.",
            "IP velocity is unusually high.",
            "Location mismatch is detected.",
            "Risk agent combines these signals and evaluates the transaction as high risk."
        ],

        "narrative": (
            "The customer is attempting a high-value cash-on-delivery order "
            "while showing multiple behavioural and device-risk signals. "
            "The combination of COD refusals, new device activity, high IP "
            "velocity and location mismatch increases the likelihood of fraud."
        ),

        "payload": {
            "customer_id": "CUS-40218",
            "order_id": "ORD-10291",
            "order_amount": 19999,
            "payment_method": "COD",
            "is_cod": True,
            "previous_orders": 9,
            "previous_returns": 4,
            "cod_refusals": 5,
            "account_age_days": 42,
            "device_id": "DEV-NEW-7781",
            "ip_address": "103.21.44.19",
            "ip_velocity": 7,
            "new_device": True,
            "payment_risk_flag": False,
            "location_mismatch": True
        }
    },


    # ========================================================
    # 2. COUNTERFEIT LUXURY PRODUCT
    # ========================================================
    "counterfeit_luxury": {
        "id": "counterfeit_luxury",
        "title": "COUNTERFEIT LUXURY PRODUCT",
        "agent": "authenticity",

        "description": (
            "Unauthorised seller listing a luxury handbag "
            "at 87% below MSRP."
        ),

        "steps": [
            "A luxury product is listed at a significantly reduced price.",
            "The seller is not authorised by the brand.",
            "The product description contains replica and first-copy language.",
            "The listing claims the product is original despite counterfeit indicators.",
            "The listing has no genuine purchase bill.",
            "The authenticity agent evaluates the pricing, seller and description signals.",
            "The listing is flagged as a potential counterfeit."
        ],

        "narrative": (
            "This luxury product listing contains multiple counterfeit "
            "indicators. The seller is unauthorised, the price is far below "
            "MSRP, and the description explicitly uses replica and first-copy "
            "language while claiming authenticity."
        ),

        "payload": {
            "product_name": "Luxe Milano Leather Tote Bag - 7A Quality",
            "brand": "Luxe Milano",
            "description": (
                "Master copy first copy AAA grade replica tote. "
                "100% original guaranteed. No bill."
            ),
            "price": 1299,
            "msrp": 10000,
            "seller_code": "SEL-207",
            "authorized": False,
            "certification_status": "self certified"
        }
    },


    # ========================================================
    # 3. UNSAFE COSMETIC LISTING
    # ========================================================
    "unsafe_cosmetic": {
        "id": "unsafe_cosmetic",
        "title": "UNSAFE COSMETIC LISTING",
        "agent": "authenticity",

        "description": (
            "Skin cream with unverifiable regulatory certification claims."
        ),

        "steps": [
            "A cosmetic product is listed with strong regulatory approval claims.",
            "The seller is not authorised.",
            "The certification status claims FDA approval.",
            "The description promises extremely fast results.",
            "The regulatory claim cannot be verified from the listing.",
            "The authenticity agent evaluates the certification and seller signals.",
            "The listing is flagged for additional review."
        ],

        "narrative": (
            "The cosmetic listing makes unverifiable regulatory and product "
            "claims. The seller is unauthorised and the listing claims FDA "
            "approval while promising unusually fast results."
        ),

        "payload": {
            "product_name": "GlowMax Fairness Cream",
            "brand": "GlowMax",
            "description": (
                "FDA approved. Instant results in 3 days. "
                "Government approved original formula."
            ),
            "price": 499,
            "msrp": 899,
            "seller_code": "SEL-311",
            "authorized": False,
            "certification_status": "fda approved"
        }
    },


    # ========================================================
    # 4. FAKE REVIEW RING
    # ========================================================
    "fake_review_ring": {
        "id": "fake_review_ring",
        "title": "FAKE REVIEW RING",
        "agent": "review",

        "description": (
            "Newly created unverified account posting templated "
            "5-star praise."
        ),

        "steps": [
            "A new user account posts a 5-star review.",
            "The purchase is not verified.",
            "The review contains highly promotional language.",
            "The review follows a templated writing pattern.",
            "The reviewer account is only a few days old.",
            "The review integrity agent analyses linguistic and behavioural signals.",
            "The review is flagged as potentially coordinated or inauthentic."
        ],

        "narrative": (
            "A newly created account is posting an overly promotional "
            "5-star review without a verified purchase. The templated "
            "language and young account age create strong review-integrity "
            "risk signals."
        ),

        "payload": {
            "text": (
                "Best product must buy. Overall, in conclusion highly "
                "recommend this product, top-notch quality."
            ),
            "rating": 5,
            "user_code": "USR-9901",
            "seller_code": "SEL-207",
            "product_id": "PRD-5521",
            "account_age_days": 3,
            "verified_purchase": False
        }
    },


    # ========================================================
    # 5. GENUINE CUSTOMER / FALSE POSITIVE PREVENTION
    # ========================================================
    "genuine_customer": {
        "id": "genuine_customer",
        "title": "GENUINE CUSTOMER / FALSE POSITIVE PREVENTION",
        "agent": "risk",

        "description": (
            "Loyal customer with a long clean history placing "
            "a routine prepaid order."
        ),

        "steps": [
            "Customer has a long account history.",
            "Customer has completed many previous orders.",
            "The customer has very few previous returns.",
            "There are no previous COD refusals.",
            "The transaction uses prepaid UPI payment.",
            "The customer is using a known device.",
            "IP velocity is normal.",
            "There is no location mismatch.",
            "Risk agent evaluates the transaction as low risk.",
            "The system avoids creating a false positive for a genuine customer."
        ],

        "narrative": (
            "This scenario demonstrates false-positive prevention. "
            "Although the customer is making a significant purchase, "
            "their long account history, clean order behaviour, known device, "
            "normal IP activity and prepaid payment method indicate a "
            "legitimate transaction."
        ),

        "payload": {
            "customer_id": "CUS-11002",
            "order_id": "ORD-10444",
            "order_amount": 4999,
            "payment_method": "UPI",
            "is_cod": False,
            "previous_orders": 68,
            "previous_returns": 1,
            "cod_refusals": 0,
            "account_age_days": 1120,
            "device_id": "DEV-KNOWN-1010",
            "ip_address": "49.36.12.7",
            "ip_velocity": 1,
            "new_device": False,
            "payment_risk_flag": False,
            "location_mismatch": False
        }
    }
}


# ============================================================
# GET ALL DEMO SCENARIOS
# ============================================================

@router.get("/scenarios")
def scenarios(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return {
        "demo_mode": True,
        "scenarios": list(SCENARIOS.values())
    }