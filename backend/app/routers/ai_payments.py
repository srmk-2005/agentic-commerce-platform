"""Router for AI-initiated Payment Proposals and Gated Approval Endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.payments.payment_service import PaymentService
from app.payments.schemas import (
    PaymentApprovalRequest,
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentRejectionRequest,
    RazorpayOrderResponse,
)

router = APIRouter(prefix="/ai/payments", tags=["AI Payments & Approval Gate"])


@router.post(
    "/propose",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Propose AI Payment Intent",
    description="Evaluates deterministic policy bounds and creates a gated payment intent requiring merchant/user approval.",
)
def propose_payment_endpoint(
    req: PaymentIntentCreate,
    db: Session = Depends(get_db),
):
    """Propose a payment intent for an order."""
    return PaymentService.propose_payment(
        db=db,
        order_id=req.order_id,
        merchant_id=req.merchant_id,
        idempotency_key=req.idempotency_key,
    )


@router.get(
    "/{payment_intent_id}",
    response_model=PaymentIntentResponse,
    summary="Get Payment Intent Details",
    description="Retrieve payment proposal details, risk classification, and explainability breakdown.",
)
def get_payment_intent_endpoint(
    payment_intent_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve payment intent by ID."""
    intent = PaymentService.get_transaction_detail(db, payment_intent_id) if False else None
    # Direct fetch
    from app.db.models import PaymentIntent
    from app.payments.exceptions import PaymentApprovalRequiredException
    from app.payments.policies import evaluate_payment_policy

    intent_db = db.query(PaymentIntent).filter(PaymentIntent.id == payment_intent_id).first()
    if not intent_db:
        raise PaymentApprovalRequiredException(f"Payment intent #{payment_intent_id} not found.")

    policy_check = evaluate_payment_policy(
        db=db,
        merchant_id=intent_db.merchant_id,
        amount=intent_db.amount,
        currency=intent_db.currency,
        order_id=intent_db.order_id,
    )

    return PaymentIntentResponse(
        id=intent_db.id,
        order_id=intent_db.order_id,
        merchant_id=intent_db.merchant_id,
        amount=intent_db.amount,
        currency=intent_db.currency,
        status=intent_db.status.value,
        risk_level=intent_db.risk_level.value,
        reason=intent_db.reason,
        requires_approval=intent_db.requires_approval,
        approved_by=intent_db.approved_by,
        approved_at=intent_db.approved_at,
        expires_at=intent_db.expires_at,
        idempotency_key=intent_db.idempotency_key,
        created_at=intent_db.created_at,
        explainability=policy_check.explainability,
        policy_check=policy_check,
    )


@router.post(
    "/{payment_intent_id}/approve",
    response_model=RazorpayOrderResponse,
    summary="Approve Payment Intent & Create Razorpay Order",
    description="Re-validates order & daily limits, approves intent, and creates a Razorpay Test Order.",
)
def approve_payment_intent_endpoint(
    payment_intent_id: int,
    req: PaymentApprovalRequest = PaymentApprovalRequest(),
    db: Session = Depends(get_db),
):
    """Explicit human approval of payment intent."""
    return PaymentService.approve_payment_intent(
        db=db,
        intent_id=payment_intent_id,
        reviewed_by=req.reviewed_by,
        reason=req.reason,
    )


@router.post(
    "/{payment_intent_id}/reject",
    response_model=PaymentIntentResponse,
    summary="Reject Payment Intent",
    description="Explicitly rejects a proposed payment intent.",
)
def reject_payment_intent_endpoint(
    payment_intent_id: int,
    req: PaymentRejectionRequest,
    db: Session = Depends(get_db),
):
    """Explicit human rejection of payment intent."""
    return PaymentService.reject_payment_intent(
        db=db,
        intent_id=payment_intent_id,
        reviewed_by=req.reviewed_by,
        reason=req.reason,
    )
