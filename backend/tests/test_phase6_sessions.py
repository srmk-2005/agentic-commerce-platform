"""Unit tests for Phase 6 Agent Commerce Sessions & Trace Timeline."""
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.orm import Session
from app.agent_commerce.session import session_manager
from app.db.models import AgentCommerceSession, Merchant, SessionStatus


def test_create_session(db: Session, sample_merchant: Merchant):
    """Test session creation generates valid session_id, trace_id, and timeline."""
    session = session_manager.create_session(
        db=db,
        merchant_id=sample_merchant.id,
        buyer_id="pytest_ai_buyer",
    )
    assert session.session_id.startswith("acs_")
    assert session.trace_id.startswith("trace_")
    assert session.buyer_id == "pytest_ai_buyer"
    assert session.status == SessionStatus.DISCOVERY
    assert session.merchant_id == sample_merchant.id

    # Verify timeline
    timeline = session_manager.get_timeline(session)
    assert len(timeline.timeline) == 1
    assert timeline.timeline[0].action == "SESSION_CREATED"


def test_session_state_transitions(db: Session, sample_merchant: Merchant):
    """Test state transitions throughout session lifecycle."""
    from app.db.models import Customer, Order, OrderStatus

    customer = Customer(
        name="Test AI Buyer",
        email="ai_buyer_test@example.com",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    order = Order(
        merchant_id=sample_merchant.id,
        customer_id=customer.id,
        total_amount=2499.0,
        currency="INR",
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    session = session_manager.create_session(
        db=db,
        merchant_id=sample_merchant.id,
        buyer_id="state_tester",
    )

    # Transition to BROWSING
    session_manager.update_session_state(db, session, SessionStatus.BROWSING)
    assert session.status == SessionStatus.BROWSING

    # Transition to ORDER_CREATED
    session_manager.update_session_state(db, session, SessionStatus.ORDER_CREATED, order_id=order.id)
    assert session.status == SessionStatus.ORDER_CREATED
    assert session.order_id == order.id

    # Transition to COMPLETED
    session_manager.update_session_state(db, session, SessionStatus.COMPLETED)
    assert session.status == SessionStatus.COMPLETED


def test_session_expiration(db: Session, sample_merchant: Merchant):
    """Test expired session transitions to EXPIRED status on fetch."""
    session = session_manager.create_session(
        db=db,
        merchant_id=sample_merchant.id,
        buyer_id="expiry_tester",
    )
    # Force expired timestamp
    session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()

    fetched = session_manager.get_session(db, session.session_id)
    assert fetched.status == SessionStatus.EXPIRED


def test_session_not_found(db: Session):
    """Test querying nonexistent session returns None."""
    session = session_manager.get_session(db, "acs_nonexistent_12345")
    assert session is None
