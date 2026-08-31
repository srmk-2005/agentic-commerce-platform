"""Deterministic Payment Policy & Safety Verification Engine."""
from datetime import datetime, timezone
from typing import Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import MerchantAiPolicy, Payment, PaymentStatus, RiskLevel
from app.payments.schemas import PaymentPolicyCheck


def classify_payment_risk(amount: float, max_limit: float) -> RiskLevel:
    """
    Deterministic risk classification in Python:
    - amount <= 25% of limit -> LOW
    - amount > 25% and <= 75% -> MEDIUM
    - amount > 75% and <= 100% -> HIGH
    - amount > 100% -> BLOCKED
    """
    if max_limit <= 0:
        return RiskLevel.BLOCKED
    if amount <= 0:
        return RiskLevel.BLOCKED
    if amount > max_limit:
        return RiskLevel.BLOCKED

    ratio = amount / max_limit
    if ratio <= 0.25:
        return RiskLevel.LOW
    elif ratio <= 0.75:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


def calculate_today_ai_spent(db: Session, merchant_id: int) -> float:
    """Calculate total successful AI transactions for the merchant today (UTC)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_spent = db.query(func.coalesce(func.sum(Payment.amount), 0.0)).filter(
        Payment.merchant_id == merchant_id,
        Payment.status == PaymentStatus.CAPTURED,
        Payment.created_at >= today_start,
    ).scalar()

    return float(total_spent or 0.0)


def evaluate_payment_policy(
    db: Session,
    merchant_id: int,
    amount: float,
    currency: str = "INR",
    order_id: int = 0,
) -> PaymentPolicyCheck:
    """
    Evaluate deterministic payment policy against merchant bounds.
    """
    policy = db.query(MerchantAiPolicy).filter(MerchantAiPolicy.merchant_id == merchant_id).first()

    max_tx_limit = policy.max_ai_transaction_amount if policy else 5000.0
    daily_limit = policy.daily_ai_transaction_limit if policy else 25000.0
    allow_ai_payment = policy.allow_ai_payment if policy else True
    require_approval = policy.require_payment_approval if policy else True

    today_spent = calculate_today_ai_spent(db, merchant_id)
    remaining_daily_limit = max(0.0, daily_limit - today_spent)

    reasons = []
    is_allowed = True

    # 1. Amount validity
    if amount <= 0:
        is_allowed = False
        reasons.append(f"Payment amount must be greater than zero (received {amount}).")

    # 2. AI Payment enabled check
    if not allow_ai_payment:
        is_allowed = False
        reasons.append("Merchant policy has disabled automated AI payments.")

    # 3. Maximum single transaction limit
    if amount > max_tx_limit:
        is_allowed = False
        reasons.append(
            f"Requested amount (₹{amount:,.2f}) exceeds maximum allowed AI transaction limit (₹{max_tx_limit:,.2f})."
        )

    # 4. Daily transaction limit
    if (today_spent + amount) > daily_limit:
        is_allowed = False
        reasons.append(
            f"Requested amount (₹{amount:,.2f}) exceeds remaining daily AI limit (₹{remaining_daily_limit:,.2f} of ₹{daily_limit:,.2f})."
        )

    # Classify risk
    risk = classify_payment_risk(amount, max_tx_limit)
    if not is_allowed:
        risk = RiskLevel.BLOCKED

    # Formulate factual explainability statement
    if is_allowed:
        explainability = (
            f"Payment of ₹{amount:,.2f} {currency} for order #{order_id} is within the configured single-transaction "
            f"limit of ₹{max_tx_limit:,.2f} (Risk: {risk.value}). Today's AI spend is ₹{today_spent:,.2f} with "
            f"₹{remaining_daily_limit:,.2f} remaining on the daily limit of ₹{daily_limit:,.2f}. "
            f"{'Human approval is required before execution.' if require_approval else 'Pre-authorized for automated execution.'}"
        )
    else:
        explainability = (
            f"Payment of ₹{amount:,.2f} {currency} for order #{order_id} is BLOCKED by merchant safety policy: "
            f"{'; '.join(reasons)}"
        )

    return PaymentPolicyCheck(
        is_allowed=is_allowed,
        amount=amount,
        currency=currency,
        max_transaction_limit=max_tx_limit,
        daily_limit=daily_limit,
        today_spent=today_spent,
        remaining_daily_limit=remaining_daily_limit,
        risk_level=risk.value,
        requires_approval=require_approval,
        reasons=reasons,
        explainability=explainability,
    )
