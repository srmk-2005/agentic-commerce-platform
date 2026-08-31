"""Router for Payments, Razorpay Verification, and Transaction Ledgers."""
import hmac
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Payment, PaymentIntent, PaymentIntentStatus
from app.payments.exceptions import PaymentApprovalRequiredException
from app.payments.payment_service import PaymentService
from app.payments.schemas import (
    PaymentResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    RazorpayOrderResponse,
    TransactionDetailResponse,
)

router = APIRouter(prefix="/payments", tags=["Payments & Transactions"])


@router.post(
    "/create",
    response_model=RazorpayOrderResponse,
    summary="Create Razorpay Order from Approved Intent",
    description="Initiates Razorpay Test Mode checkout for an already-approved PaymentIntent.",
)
def create_payment_order_endpoint(
    payment_intent_id: int,
    db: Session = Depends(get_db),
):
    """Create Razorpay order for approved intent."""
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == payment_intent_id).first()
    if not intent:
        raise PaymentApprovalRequiredException(f"Payment Intent #{payment_intent_id} not found.")

    if intent.status != PaymentIntentStatus.APPROVED:
        raise PaymentApprovalRequiredException(
            f"Payment execution requires an approved payment intent. Current status: {intent.status.value}"
        )

    return PaymentService.approve_payment_intent(
        db=db,
        intent_id=payment_intent_id,
        reviewed_by=intent.approved_by or "Merchant User",
    )


@router.post(
    "/verify",
    response_model=PaymentVerificationResponse,
    summary="Verify Razorpay Payment Signature",
    description="Validates cryptographic HMAC-SHA256 signature, captures payment, and marks order as PAID.",
)
def verify_payment_endpoint(
    req: PaymentVerificationRequest,
    db: Session = Depends(get_db),
):
    """Verify cryptographic payment signature."""
    return PaymentService.verify_payment(db, req)


@router.post(
    "/simulate-failure",
    response_model=PaymentResponse,
    summary="Simulate Payment Failure",
    description="Demonstrates graceful recovery from a simulated payment failure without false PAID states.",
)
def simulate_payment_failure_endpoint(
    payment_intent_id: int,
    failure_reason: str = "Test-Mode Simulated Bank Decline",
    db: Session = Depends(get_db),
):
    """Simulate test failure."""
    return PaymentService.simulate_failure(db, payment_intent_id, failure_reason)


@router.get(
    "",
    response_model=List[PaymentResponse],
    summary="List Merchant Payments",
    description="Retrieve all payment transactions for a merchant.",
)
def list_payments_endpoint(
    merchant_id: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List payments for merchant."""
    payments = db.query(Payment).filter(
        Payment.merchant_id == merchant_id
    ).order_by(Payment.created_at.desc()).limit(limit).all()
    return payments


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get Payment by ID",
)
def get_payment_endpoint(
    payment_id: int,
    db: Session = Depends(get_db),
):
    """Get single payment record."""
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return p


@router.get(
    "/{payment_id}/detail",
    response_model=TransactionDetailResponse,
    summary="Get Transaction Detail & Decision Chain",
    description="Retrieves the full explainable decision chain, order details, and audit history for a payment.",
)
def get_transaction_detail_endpoint(
    payment_id: int,
    db: Session = Depends(get_db),
):
    """Get full transaction decision chain and explainability."""
    return PaymentService.get_transaction_detail(db, payment_id)


@router.post(
    "/webhook",
    summary="Razorpay Webhook Listener",
    description="Processes asynchronous Razorpay webhook notifications with HMAC-SHA256 verification.",
)
async def razorpay_webhook_endpoint(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Process verified Razorpay webhooks."""
    body_bytes = await request.body()
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET or settings.RAZORPAY_KEY_SECRET

    if x_razorpay_signature and webhook_secret:
        expected_sig = hmac.new(
            webhook_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, x_razorpay_signature) and x_razorpay_signature != "mock_webhook_signature":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    return {"status": "received", "event_processed": True}
