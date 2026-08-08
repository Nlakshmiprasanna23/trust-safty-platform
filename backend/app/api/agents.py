from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.session import get_db
from app.models import Review, RiskScore, AuthenticityScore, ProductListing, FraudCase, Transaction, ProductImage
from app.schemas import RiskRequest, AuthenticityRequest, ReviewRequest
from app.security import get_current_user
from app.services.orchestrator import orchestrator
from app.services.review_agent.agent import detect_rings
import uuid

router = APIRouter(prefix="/api", tags=["agents"])
MAX_IMAGE_BYTES = 5 * 1024 * 1024

def _open_case(db, case_type, severity, agent, score, reference):
    case = FraudCase(case_id=f"CASE-{uuid.uuid4().hex[:8].upper()}", case_type=case_type,
                     severity=severity, agent=agent, risk_score=score, reference=reference, status="OPEN")
    db.add(case); db.commit()
    return case.case_id

@router.post("/risk/analyze")
def analyze_risk(payload: RiskRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    data = payload.model_dump()
    result = orchestrator.route("risk", data, db, actor=user.email)
    db.add(RiskScore(order_id=payload.order_id, customer_code=payload.customer_id,
                     score=result["risk_score"], fraud_probability=result["fraud_probability"],
                     risk_level=result["risk_level"], decision=result["recommended_action"],
                     reasons=result["reasons"], latency_ms=result["latency_ms"],
                     model_version=result["model_version"]))
    txn = db.query(Transaction).filter(Transaction.order_id == payload.order_id).first()
    if not txn:
        txn = Transaction(order_id=payload.order_id, customer_code=payload.customer_id,
                          seller_code="SEL-001", amount=payload.order_amount,
                          payment_method=payload.payment_method, is_cod=payload.is_cod)
        db.add(txn)
    txn.risk_score = result["risk_score"]
    txn.decision = result["recommended_action"]
    txn.status = "BLOCKED" if result["recommended_action"] == "BLOCK_COD" else "PLACED"
    db.commit()
    if result["risk_level"] in ("HIGH", "CRITICAL"):
        result["case_id"] = _open_case(db, "COD/Return Fraud", result["risk_level"],
                                       "Risk Scoring Agent", result["risk_score"], payload.order_id)
    return result

@router.post("/authenticity/analyze")
async def analyze_authenticity(
    product_name: str = Form(...), brand: str = Form(""), description: str = Form(""),
    price: float = Form(0), msrp: float = Form(0), seller_code: str = Form("SEL-000"),
    authorized: bool = Form(False), certification_status: str = Form(""),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db), user=Depends(get_current_user)):
    image_bytes = None
    if image is not None:
        image_bytes = await image.read()
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(413, "Image exceeds the 5MB upload limit")
        if image.content_type and not image.content_type.startswith("image/"):
            raise HTTPException(415, "Only image uploads are supported")
    payload = AuthenticityRequest(product_name=product_name, brand=brand, description=description,
                                  price=price, msrp=msrp, seller_code=seller_code,
                                  authorized=authorized, certification_status=certification_status).model_dump()
    listing_id = f"LST-{uuid.uuid4().hex[:8].upper()}"
    payload["listing_id"] = listing_id
    result = orchestrator.route("authenticity", payload, db, actor=user.email, image_bytes=image_bytes)
    db.add(ProductListing(listing_id=listing_id, product_name=product_name, brand=brand,
                          description=description, seller_code=seller_code, price=price, msrp=msrp,
                          authorized=authorized, certification_status=certification_status,
                          authenticity_score=result["authenticity_score"],
                          counterfeit_probability=result["counterfeit_probability"],
                          status=result["decision"]))
    if image_bytes:
        b = result["breakdown"]["image"]
        db.add(ProductImage(listing_id=listing_id, filename=image.filename or "upload",
                            width=b.get("width", 0), height=b.get("height", 0), analysis=b))
    db.add(AuthenticityScore(listing_id=listing_id, authenticity_score=result["authenticity_score"],
                             counterfeit_probability=result["counterfeit_probability"],
                             risk_level=result["risk_level"], decision=result["decision"],
                             reasons=result["reasons"], breakdown=result["breakdown"],
                             model_version=result["model_version"]))
    db.commit()
    result["listing_id"] = listing_id
    if result["decision"] == "REJECT":
        result["case_id"] = _open_case(db, "Counterfeit Listing", result["risk_level"],
                                       "Authenticity & Integrity Agent", result["counterfeit_probability"], listing_id)
    return result

@router.post("/reviews/analyze")
def analyze_review(payload: ReviewRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    since = datetime.utcnow() - timedelta(days=7)
    peers = db.query(Review).filter(Review.seller_code == payload.seller_code).limit(200).all()
    peer_texts = [r.text for r in peers]
    recent = db.query(Review).filter(Review.seller_code == payload.seller_code,
                                     Review.created_at >= since).count()
    data = payload.model_dump()
    review_id = payload.review_id or f"REV-{uuid.uuid4().hex[:8].upper()}"
    data["review_id"] = review_id
    result = orchestrator.route("review", data, db, actor=user.email,
                                peer_reviews=peer_texts, seller_recent_count=recent)
    db.add(Review(review_id=review_id, text=payload.text, rating=payload.rating,
                  user_code=payload.user_code, seller_code=payload.seller_code,
                  product_id=payload.product_id, account_age_days=payload.account_age_days,
                  verified_purchase=payload.verified_purchase, risk_score=result["risk_score"],
                  fake_probability=result["fake_probability"], ai_probability=result["ai_generated_probability"],
                  sentiment=result["sentiment"], decision=result["decision"]))
    db.commit()
    result["review_id"] = review_id
    if result["decision"] == "HIDE":
        result["case_id"] = _open_case(db, "Fake Review", result["risk_level"],
                                       "Review Moderation Agent", result["risk_score"], review_id)
    return result

@router.get("/review-rings")
def review_rings(db: Session = Depends(get_db), user=Depends(get_current_user)):
    reviews = db.query(Review).all()
    data = [{"user_code": r.user_code, "seller_code": r.seller_code, "text": r.text,
             "account_age_days": r.account_age_days, "created_at": r.created_at} for r in reviews]
    return detect_rings(data)
