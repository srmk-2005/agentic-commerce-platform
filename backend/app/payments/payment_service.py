"""Business-Level Payment Orchestration Service.

CRITICAL INVARIANTS:
1. Every money action is explainable, bounded, and gated.
2. The AI agent cannot approve its own payments, alter prices, or bypass validation.
3. Server recalculates all prices from ground-truth database rows before charging.
4. Idempotency guarantees zero duplicate charges or double deductions.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import status
from sqlalchemy.orm import Session
from app.db.models import (
    ActorType,
    MoneyAction,
    MoneyActionType,
    Order,
    OrderStatus,
    Payment,
    PaymentIntent,
    PaymentIntentStatus,
    PaymentStatus,
    RiskLevel,
)
from app.payments.exceptions import (
    DuplicatePaymentException,
    OrderNotPayableException,
    PaymentApprovalRequiredException,
    PaymentPolicyViolationException,
    PaymentSignatureInvalidException,
    StaleApprovalException,
)
from app.payments.policies import evaluate_payment_policy
from app.payments.razorpay_service import razorpay_adapter
from app.payments.schemas import (
    PaymentIntentResponse,
    PaymentPolicyCheck,
    PaymentResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    RazorpayOrderResponse,
    TransactionDetailResponse,
)
from app.services.audit_service import audit_service


class PaymentService:
    """Orchestrates all payment lifecycles, bounds checking, and Razorpay interactions."""

    @staticmethod
    def propose_payment(
        db: Session,
        order_id: int,
        merchant_id: int,
        idempotency_key: Optional[str] = None,
    ) -> PaymentIntentResponse:
        """
        Step 1: Propose a payment intent for an order.
        Validates order, runs deterministic policy checks, and stores a PENDING_APPROVAL intent.
        """
        # 1. Fetch Order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise OrderNotPayableException(f"Order #{order_id} does not exist.")

        if order.merchant_id != merchant_id:
            raise OrderNotPayableException(f"Order #{order_id} does not belong to merchant #{merchant_id}.")

        # 2. Check if already paid
        if order.status == OrderStatus.PAID or order.payment_status == "PAID":
            raise DuplicatePaymentException(f"Order #{order_id} has already been paid in full.")

        # 3. Idempotency Check
        if idempotency_key:
            existing_intent = db.query(PaymentIntent).filter(
                PaymentIntent.idempotency_key == idempotency_key
            ).first()
            if existing_intent:
                policy_check = evaluate_payment_policy(
                    db=db,
                    merchant_id=merchant_id,
                    amount=existing_intent.amount,
                    currency=existing_intent.currency,
                    order_id=order_id,
                )
                return PaymentIntentResponse(
                    id=existing_intent.id,
                    order_id=existing_intent.order_id,
                    merchant_id=existing_intent.merchant_id,
                    amount=existing_intent.amount,
                    currency=existing_intent.currency,
                    status=existing_intent.status.value,
                    risk_level=existing_intent.risk_level.value,
                    reason=existing_intent.reason,
                    requires_approval=existing_intent.requires_approval,
                    approved_by=existing_intent.approved_by,
                    approved_at=existing_intent.approved_at,
                    expires_at=existing_intent.expires_at,
                    idempotency_key=existing_intent.idempotency_key,
                    created_at=existing_intent.created_at,
                    explainability=policy_check.explainability,
                    policy_check=policy_check,
                )

        # 4. Evaluate Deterministic Payment Policy & Bounds
        policy_check = evaluate_payment_policy(
            db=db,
            merchant_id=merchant_id,
            amount=order.total_amount,
            currency=order.currency,
            order_id=order_id,
        )

        if not policy_check.is_allowed:
            # Record blocked event in audit trail
            audit_service.log_agent_action(
                db=db,
                merchant_id=merchant_id,
                action="AI_PAYMENT_BLOCKED",
                entity_type="Order",
                entity_id=order_id,
                status="BLOCKED",
                reason=f"Payment blocked by policy: {'; '.join(policy_check.reasons)}",
                metadata={"amount": order.total_amount, "currency": order.currency, "reasons": policy_check.reasons},
                actor_type=ActorType.SYSTEM,
            )
            raise PaymentPolicyViolationException(
                f"Payment blocked by policy: {'; '.join(policy_check.reasons)}"
            )

        # 5. Create Payment Intent
        now = datetime.now(timezone.utc)
        intent = PaymentIntent(
            order_id=order.id,
            merchant_id=merchant_id,
            amount=order.total_amount,
            currency=order.currency,
            status=PaymentIntentStatus.PENDING_APPROVAL if policy_check.requires_approval else PaymentIntentStatus.APPROVED,
            risk_level=RiskLevel(policy_check.risk_level),
            reason=f"Payment requested for merchant order #{order.id}.",
            requires_approval=policy_check.requires_approval,
            expires_at=now + timedelta(minutes=15),
            idempotency_key=idempotency_key,
            metadata_json=json.dumps({
                "policy_check": policy_check.model_dump(),
                "order_items_count": len(order.items),
            }),
        )
        db.add(intent)
        db.flush()

        # Update order status to PENDING_PAYMENT
        order.status = OrderStatus.PENDING_PAYMENT
        order.payment_status = "AWAITING_APPROVAL"
        db.commit()

        # 6. Audit Logs
        audit_service.log_agent_action(
            db=db,
            merchant_id=merchant_id,
            action="AI_PAYMENT_PROPOSED",
            entity_type="PaymentIntent",
            entity_id=intent.id,
            status="SUCCESS",
            reason=f"AI proposed payment of ₹{intent.amount:,.2f} for Order #{order.id}.",
            metadata={"amount": intent.amount, "currency": intent.currency, "risk_level": intent.risk_level.value},
            actor_type=ActorType.AI_BUYER,
        )

        audit_service.log_agent_action(
            db=db,
            merchant_id=merchant_id,
            action="AI_PAYMENT_POLICY_CHECK",
            entity_type="PaymentIntent",
            entity_id=intent.id,
            status="PASSED",
            reason=policy_check.explainability,
            metadata=policy_check.model_dump(),
            actor_type=ActorType.SYSTEM,
        )

        return PaymentIntentResponse(
            id=intent.id,
            order_id=intent.order_id,
            merchant_id=intent.merchant_id,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status.value,
            risk_level=intent.risk_level.value,
            reason=intent.reason,
            requires_approval=intent.requires_approval,
            approved_by=intent.approved_by,
            approved_at=intent.approved_at,
            expires_at=intent.expires_at,
            idempotency_key=intent.idempotency_key,
            created_at=intent.created_at,
            explainability=policy_check.explainability,
            policy_check=policy_check,
        )

    @staticmethod
    def approve_payment_intent(
        db: Session,
        intent_id: int,
        reviewed_by: str = "Merchant Owner / User",
        reason: Optional[str] = None,
    ) -> RazorpayOrderResponse:
        """
        Step 2: Explicit Human/Merchant Approval Gate.
        Re-validates all parameters, creates Razorpay Test Order, and prepares checkout.
        """
        intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
        if not intent:
            raise PaymentApprovalRequiredException(f"Payment Intent #{intent_id} not found.")

        # Idempotent Return if already approved with an active payment
        if intent.status in [PaymentIntentStatus.APPROVED, PaymentIntentStatus.EXECUTING]:
            existing_payment = db.query(Payment).filter(Payment.payment_intent_id == intent.id).first()
            if existing_payment and existing_payment.razorpay_order_id:
                return RazorpayOrderResponse(
                    razorpay_order_id=existing_payment.razorpay_order_id,
                    razorpay_key_id=razorpay_adapter.key_id,
                    amount=int(existing_payment.amount * 100),
                    currency=existing_payment.currency,
                    payment_intent_id=intent.id,
                    order_id=intent.order_id,
                    status=existing_payment.status.value,
                    is_test_mode=True,
                )

        if intent.status == PaymentIntentStatus.REJECTED:
            raise PaymentApprovalRequiredException("Cannot approve a payment intent that has already been REJECTED.")

        if intent.status == PaymentIntentStatus.COMPLETED:
            raise DuplicatePaymentException("Payment intent has already been completed and verified.")

        now = datetime.now(timezone.utc)
        if intent.expires_at:
            exp = (
                intent.expires_at.replace(tzinfo=timezone.utc)
                if intent.expires_at.tzinfo is None
                else intent.expires_at
            )
            if exp < now:
                intent.status = PaymentIntentStatus.FAILED
                db.commit()
                raise StaleApprovalException("Payment proposal has expired. Please initiate a new payment request.")

        # MANDATORY PRE-EXECUTION REVALIDATION
        order = db.query(Order).filter(Order.id == intent.order_id).first()
        if not order:
            raise OrderNotPayableException(f"Order #{intent.order_id} no longer exists.")

        if order.total_amount != intent.amount:
            raise StaleApprovalException(
                f"Order amount changed from ₹{intent.amount} to ₹{order.total_amount}. Approval invalidated."
            )

        policy_check = evaluate_payment_policy(
            db=db,
            merchant_id=intent.merchant_id,
            amount=intent.amount,
            currency=intent.currency,
            order_id=order.id,
        )
        if not policy_check.is_allowed:
            intent.status = PaymentIntentStatus.REJECTED
            db.commit()
            raise PaymentPolicyViolationException(
                f"Pre-execution revalidation failed: {'; '.join(policy_check.reasons)}"
            )

        # 1. Update PaymentIntent status
        intent.status = PaymentIntentStatus.APPROVED
        intent.approved_by = reviewed_by
        intent.approved_at = now
        db.flush()

        # 2. Record MoneyAction entry
        money_action = MoneyAction(
            merchant_id=intent.merchant_id,
            order_id=intent.order_id,
            payment_intent_id=intent.id,
            action_type=MoneyActionType.CREATE_PAYMENT,
            amount=intent.amount,
            currency=intent.currency,
            status="APPROVED",
            risk_level=intent.risk_level,
            reason=reason or f"Approved by {reviewed_by}",
            requires_approval=True,
            approved_by=reviewed_by,
            approved_at=now,
        )
        db.add(money_action)

        # 3. Create Razorpay Test Order
        amount_paise = int(round(intent.amount * 100))
        rzp_order = razorpay_adapter.create_order(
            amount_paise=amount_paise,
            currency=intent.currency,
            receipt=f"rcpt_ord_{order.id}",
            notes={"intent_id": intent.id, "order_id": order.id, "merchant_id": intent.merchant_id},
        )

        # 4. Create Payment record in DB
        payment = Payment(
            order_id=order.id,
            merchant_id=intent.merchant_id,
            payment_intent_id=intent.id,
            razorpay_order_id=rzp_order["id"],
            amount=intent.amount,
            currency=intent.currency,
            status=PaymentStatus.PENDING,
            payment_method="RAZORPAY_TEST",
        )
        db.add(payment)

        # 5. Update Order status
        order.status = OrderStatus.PAYMENT_PROCESSING
        order.payment_status = "PENDING"
        db.commit()

        # 6. Audit Trail
        audit_service.log_agent_action(
            db=db,
            merchant_id=intent.merchant_id,
            action="AI_PAYMENT_APPROVED",
            entity_type="PaymentIntent",
            entity_id=intent.id,
            status="APPROVED",
            reason=f"Payment of ₹{intent.amount:,.2f} approved by {reviewed_by}.",
            metadata={"approved_by": reviewed_by, "amount": intent.amount},
            actor_type=ActorType.MERCHANT,
        )

        audit_service.log_agent_action(
            db=db,
            merchant_id=intent.merchant_id,
            action="RAZORPAY_ORDER_CREATED",
            entity_type="Payment",
            entity_id=payment.id,
            status="SUCCESS",
            reason=f"Created Razorpay Test Order '{rzp_order['id']}' for {amount_paise} paise.",
            metadata={"razorpay_order_id": rzp_order["id"], "amount_paise": amount_paise},
            actor_type=ActorType.SYSTEM,
        )

        return RazorpayOrderResponse(
            razorpay_order_id=rzp_order["id"],
            razorpay_key_id=rzp_order["key_id"],
            amount=amount_paise,
            currency=intent.currency,
            payment_intent_id=intent.id,
            order_id=order.id,
            status="CREATED",
            is_test_mode=True,
        )

    @staticmethod
    def reject_payment_intent(
        db: Session,
        intent_id: int,
        reviewed_by: str = "Merchant Owner / User",
        reason: str = "Payment rejected by user.",
    ) -> PaymentIntentResponse:
        """Explicit rejection of a proposed payment intent."""
        intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
        if not intent:
            raise PaymentApprovalRequiredException(f"Payment Intent #{intent_id} not found.")

        intent.status = PaymentIntentStatus.REJECTED
        intent.approved_by = reviewed_by
        intent.approved_at = datetime.now(timezone.utc)
        db.commit()

        # Audit
        audit_service.log_agent_action(
            db=db,
            merchant_id=intent.merchant_id,
            action="AI_PAYMENT_REJECTED",
            entity_type="PaymentIntent",
            entity_id=intent.id,
            status="REJECTED",
            reason=f"Payment rejected by {reviewed_by}: {reason}",
            metadata={"reviewed_by": reviewed_by, "reason": reason},
            actor_type=ActorType.MERCHANT,
        )

        return PaymentIntentResponse(
            id=intent.id,
            order_id=intent.order_id,
            merchant_id=intent.merchant_id,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status.value,
            risk_level=intent.risk_level.value,
            reason=intent.reason,
            requires_approval=intent.requires_approval,
            approved_by=intent.approved_by,
            approved_at=intent.approved_at,
            expires_at=intent.expires_at,
            idempotency_key=intent.idempotency_key,
            created_at=intent.created_at,
            explainability=f"Payment rejected by {reviewed_by}.",
        )

    @staticmethod
    def verify_payment(
        db: Session,
        req: PaymentVerificationRequest,
    ) -> PaymentVerificationResponse:
        """
        Step 3: Cryptographic HMAC Signature Verification & Order Settlement.
        """
        # 1. Fetch Payment Intent and Payment
        intent = db.query(PaymentIntent).filter(PaymentIntent.id == req.payment_intent_id).first()
        if not intent:
            raise PaymentApprovalRequiredException(f"Payment Intent #{req.payment_intent_id} not found.")

        payment = db.query(Payment).filter(
            Payment.payment_intent_id == intent.id,
            Payment.razorpay_order_id == req.razorpay_order_id,
        ).first()

        if not payment:
            # Fallback query by razorpay_order_id
            payment = db.query(Payment).filter(Payment.razorpay_order_id == req.razorpay_order_id).first()
            if not payment:
                raise PaymentApprovalRequiredException("Matching payment record not found for verification.")

        # Idempotency: if already captured, return success immediately
        if payment.status == PaymentStatus.CAPTURED:
            return PaymentVerificationResponse(
                success=True,
                payment_id=payment.id,
                order_id=payment.order_id,
                status=payment.status.value,
                amount=payment.amount,
                currency=payment.currency,
                message="Payment already verified and captured.",
                verified_at=payment.verified_at or datetime.now(timezone.utc),
            )

        # 2. Cryptographic HMAC Signature Verification
        is_valid = razorpay_adapter.verify_payment_signature(
            razorpay_order_id=req.razorpay_order_id,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_signature=req.razorpay_signature,
        )

        now = datetime.now(timezone.utc)

        if not is_valid:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Invalid HMAC-SHA256 signature."
            intent.status = PaymentIntentStatus.FAILED

            order = db.query(Order).filter(Order.id == payment.order_id).first()
            if order:
                order.status = OrderStatus.PAYMENT_FAILED
                order.payment_status = "FAILED"

            db.commit()

            audit_service.log_agent_action(
                db=db,
                merchant_id=payment.merchant_id,
                action="PAYMENT_FAILED",
                entity_type="Payment",
                entity_id=payment.id,
                status="FAILED",
                reason="Razorpay signature verification failed.",
                metadata={"razorpay_order_id": req.razorpay_order_id},
                actor_type=ActorType.SYSTEM,
            )
            raise PaymentSignatureInvalidException("HMAC-SHA256 signature verification failed.")

        # 3. Successful Verification
        payment.status = PaymentStatus.CAPTURED
        payment.razorpay_payment_id = req.razorpay_payment_id
        payment.razorpay_signature = req.razorpay_signature
        payment.verified_at = now
        intent.status = PaymentIntentStatus.COMPLETED

        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = OrderStatus.PAID
            order.payment_status = "PAID"

        db.commit()

        # 4. Audit Trail
        audit_service.log_agent_action(
            db=db,
            merchant_id=payment.merchant_id,
            action="PAYMENT_VERIFIED",
            entity_type="Payment",
            entity_id=payment.id,
            status="SUCCESS",
            reason=f"Verified Razorpay signature for payment '{req.razorpay_payment_id}'.",
            metadata={"razorpay_payment_id": req.razorpay_payment_id, "amount": payment.amount},
            actor_type=ActorType.SYSTEM,
        )

        audit_service.log_agent_action(
            db=db,
            merchant_id=payment.merchant_id,
            action="ORDER_MARKED_PAID",
            entity_type="Order",
            entity_id=payment.order_id,
            status="SUCCESS",
            reason=f"Order #{payment.order_id} marked as PAID.",
            metadata={"amount": payment.amount, "currency": payment.currency},
            actor_type=ActorType.SYSTEM,
        )

        return PaymentVerificationResponse(
            success=True,
            payment_id=payment.id,
            order_id=payment.order_id,
            status=payment.status.value,
            amount=payment.amount,
            currency=payment.currency,
            message="Payment successfully verified and order marked PAID.",
            verified_at=now,
        )

    @staticmethod
    def simulate_failure(
        db: Session,
        intent_id: int,
        failure_reason: str = "Test-Mode Simulated Bank Decline",
    ) -> PaymentResponse:
        """Simulate a failure in Razorpay test mode to verify graceful error recovery."""
        intent = db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first()
        if not intent:
            raise PaymentApprovalRequiredException(f"Payment Intent #{intent_id} not found.")

        payment = db.query(Payment).filter(Payment.payment_intent_id == intent.id).first()
        if not payment:
            payment = Payment(
                order_id=intent.order_id,
                merchant_id=intent.merchant_id,
                payment_intent_id=intent.id,
                amount=intent.amount,
                currency=intent.currency,
                status=PaymentStatus.FAILED,
                failure_reason=failure_reason,
            )
            db.add(payment)
        else:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = failure_reason

        intent.status = PaymentIntentStatus.FAILED

        order = db.query(Order).filter(Order.id == intent.order_id).first()
        if order:
            order.status = OrderStatus.PAYMENT_FAILED
            order.payment_status = "PAYMENT_FAILED"

        db.commit()

        audit_service.log_agent_action(
            db=db,
            merchant_id=intent.merchant_id,
            action="PAYMENT_FAILED",
            entity_type="Payment",
            entity_id=payment.id,
            status="FAILED",
            reason=f"Payment failed: {failure_reason}. No money transferred.",
            metadata={"reason": failure_reason, "amount": intent.amount},
            actor_type=ActorType.SYSTEM,
        )

        return PaymentResponse.model_validate(payment)

    @staticmethod
    def get_transaction_detail(db: Session, payment_id: int) -> TransactionDetailResponse:
        """Compile complete explainable decision chain for the transaction detail view."""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise PaymentApprovalRequiredException(f"Payment #{payment_id} not found.")

        order = db.query(Order).filter(Order.id == payment.order_id).first()
        order_dict = {
            "id": order.id if order else 0,
            "status": order.status.value if order else "UNKNOWN",
            "total_amount": order.total_amount if order else 0.0,
            "currency": order.currency if order else "INR",
            "items": [
                {"name": it.product.name if it.product else f"Product #{it.product_id}", "quantity": it.quantity, "unit_price": it.unit_price}
                for it in (order.items if order else [])
            ],
        }

        intent = db.query(PaymentIntent).filter(PaymentIntent.id == payment.payment_intent_id).first() if payment.payment_intent_id else None
        intent_resp = PaymentIntentResponse.model_validate(intent) if intent else None

        # Build decision chain narrative
        chain = [
            f"1. AI Buyer selected products and created Order #{payment.order_id} (Total: ₹{payment.amount:,.2f})",
            f"2. Deterministic safety policy evaluated: single-limit bound check & daily spend threshold",
            f"3. Risk classified as '{intent.risk_level.value if intent else 'LOW'}'",
            f"4. PaymentIntent proposed with explicit merchant approval gate",
            f"5. Merchant/User approved payment (Authorized by: {intent.approved_by if intent else 'User'})",
            f"6. Razorpay Test-Mode order created: '{payment.razorpay_order_id or 'N/A'}'",
        ]

        if payment.status == PaymentStatus.CAPTURED:
            chain.extend([
                f"7. Razorpay test checkout completed",
                f"8. Cryptographic HMAC-SHA256 signature verified by server",
                f"9. Payment marked CAPTURED and Order marked PAID",
            ])
        elif payment.status == PaymentStatus.FAILED:
            chain.extend([
                f"7. Razorpay test checkout reported failure: {payment.failure_reason}",
                f"8. Payment marked FAILED (Order marked PAYMENT_FAILED, 0 charges made)",
            ])

        # Fetch audit events
        audit_records = audit_service.get_merchant_audit_logs(
            db=db,
            merchant_id=payment.merchant_id,
            limit=10,
        )
        audit_dicts = [
            {"id": a.id, "action": a.action, "actor": a.actor_type.value, "status": a.status, "timestamp": a.created_at.isoformat(), "reason": a.reason}
            for a in audit_records if str(payment.order_id) in (a.reason or "") or a.entity_id == payment.id or a.entity_id == (intent.id if intent else 0)
        ]

        return TransactionDetailResponse(
            payment=PaymentResponse.model_validate(payment),
            order=order_dict,
            payment_intent=intent_resp,
            decision_chain=chain,
            audit_events=audit_dicts,
        )
