"""FastAPI Router for Standardized Agent Commerce Protocol (Phase 6)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.agent_commerce.discovery import get_merchant_contract
from app.agent_commerce.policies import readiness_scorer
from app.agent_commerce.schemas import (
    AgentCommerceContract,
    AgentCommerceStatsResponse,
    AgentMessage,
    AgentResponse,
    CommerceReadinessResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionTimelineResponse,
)
from app.agent_commerce.service import merchant_commerce_agent
from app.agent_commerce.session import session_manager
from app.db.database import get_db
from app.db.models import (
    AgentCommerceSession,
    Order,
    OrderStatus,
    Payment,
    PaymentIntent,
    PaymentStatus,
    RiskLevel,
    SessionStatus,
)

router = APIRouter(prefix="/agent-commerce", tags=["Agent Commerce Protocol"])


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start new Agent Commerce Session",
)
def create_session(
    req: SessionCreateRequest,
    db: Session = Depends(get_db),
):
    """Initialize a stateful agent commerce session with an end-to-end trace ID."""
    try:
        session = session_manager.create_session(
            db=db,
            merchant_id=req.merchant_id,
            buyer_id=req.buyer_id,
        )
        return SessionResponse(
            session_id=session.session_id,
            trace_id=session.trace_id,
            merchant_id=session.merchant_id,
            buyer_id=session.buyer_id,
            status=session.status.value,
            created_at=session.created_at,
            expires_at=session.expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get Agent Commerce Session State",
)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve current state and lifecycle status of an agent commerce session."""
    session = session_manager.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent commerce session '{session_id}' not found.",
        )
    return SessionResponse(
        session_id=session.session_id,
        trace_id=session.trace_id,
        merchant_id=session.merchant_id,
        buyer_id=session.buyer_id,
        status=session.status.value,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.get(
    "/sessions/{session_id}/timeline",
    response_model=SessionTimelineResponse,
    summary="Get Transaction Timeline and Trace Events",
)
def get_session_timeline(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve complete chronological trace events and actions for judge inspection."""
    session = session_manager.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent commerce session '{session_id}' not found.",
        )
    return session_manager.get_timeline(session)


@router.get(
    "/merchants/{merchant_id}",
    response_model=AgentCommerceContract,
    summary="Discover Merchant and Capability Contract",
)
def discover_merchant(
    merchant_id: int,
    db: Session = Depends(get_db),
):
    """Return machine-readable capability manifest and routing contract for AI buyers."""
    contract = get_merchant_contract(db, merchant_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant #{merchant_id} not found.",
        )
    return contract


@router.post(
    "/message",
    response_model=AgentResponse,
    summary="Unified Protocol Message Dispatcher",
)
def dispatch_protocol_message(
    msg: AgentMessage,
    db: Session = Depends(get_db),
):
    """Standardized API envelope for all agent-to-agent commerce operations."""
    return merchant_commerce_agent.dispatch_message(db, msg)


@router.get(
    "/readiness/{merchant_id}",
    response_model=CommerceReadinessResponse,
    summary="Calculate AI Commerce Readiness Score & Checklist",
)
def get_commerce_readiness(
    merchant_id: int,
    db: Session = Depends(get_db),
):
    """Deterministic, mathematically weighted capability checklist and readiness score (0-100%)."""
    res = readiness_scorer.calculate_readiness(db, merchant_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant #{merchant_id} not found.",
        )
    return res


@router.get(
    "/stats",
    response_model=AgentCommerceStatsResponse,
    summary="Get Agent Commerce Overview Metrics",
)
def get_agent_commerce_stats(
    merchant_id: Optional[int] = Query(None, description="Optional merchant filter"),
    db: Session = Depends(get_db),
):
    """Retrieve aggregate platform metrics for AI buyer activities."""
    # Active sessions
    sess_q = db.query(AgentCommerceSession).filter(
        AgentCommerceSession.status.in_([
            SessionStatus.DISCOVERY,
            SessionStatus.BROWSING,
            SessionStatus.PRODUCT_SELECTED,
            SessionStatus.ORDER_CREATED,
            SessionStatus.PAYMENT_PENDING,
        ])
    )
    if merchant_id:
        sess_q = sess_q.filter(AgentCommerceSession.merchant_id == merchant_id)
    active_sessions = sess_q.count()

    # AI Orders & Revenue
    # We consider orders with customer_id or linked to agent sessions/audit
    orders_q = db.query(Order).filter(Order.status == OrderStatus.PAID)
    if merchant_id:
        orders_q = orders_q.filter(Order.merchant_id == merchant_id)
    paid_orders = orders_q.all()
    ai_revenue = sum(o.total_amount for o in paid_orders)
    orders_via_ai = len(paid_orders)

    # Successful Payments
    pay_q = db.query(Payment).filter(Payment.status == PaymentStatus.CAPTURED)
    if merchant_id:
        pay_q = pay_q.filter(Payment.merchant_id == merchant_id)
    successful_payments = pay_q.count()

    # Blocked Transactions
    blocked_q = db.query(PaymentIntent).filter(PaymentIntent.risk_level == RiskLevel.BLOCKED)
    if merchant_id:
        blocked_q = blocked_q.filter(PaymentIntent.merchant_id == merchant_id)
    blocked_transactions = blocked_q.count()

    return AgentCommerceStatsResponse(
        active_sessions=active_sessions,
        orders_via_ai=orders_via_ai,
        ai_revenue=float(ai_revenue),
        successful_payments=successful_payments,
        blocked_transactions=blocked_transactions,
        currency="INR",
    )
