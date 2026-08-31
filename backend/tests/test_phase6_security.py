"""Security & Safety Invariant tests for Phase 6 Agent Commerce."""
import pytest
from sqlalchemy.orm import Session
from app.agent_commerce.protocol import ErrorCodes
from app.agent_commerce.schemas import (
    AgentMessage,
    AgentSenderRecipient,
    ProtocolAction,
)
from app.agent_commerce.service import merchant_commerce_agent
from app.agent_commerce.session import session_manager
from app.db.models import Merchant, MerchantAiPolicy, Order, OrderStatus, Product


def test_payment_limit_exceeded_block(db: Session, sample_merchant: Merchant, sample_product: Product):
    """Test AI Buyer payment exceeding merchant single transaction limit is blocked."""
    # Policy with 500 cap
    policy = db.query(MerchantAiPolicy).filter(MerchantAiPolicy.merchant_id == sample_merchant.id).first()
    if policy:
        policy.max_ai_transaction_amount = 500.0
        db.commit()

    session = session_manager.create_session(
        db=db,
        merchant_id=sample_merchant.id,
        buyer_id="limit_tester",
    )

    # Order product costing more than 500
    ord_msg = AgentMessage(
        message_id="msg_limit_01",
        session_id=session.session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="limit_tester"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.CREATE_ORDER,
        payload={"product_id": sample_product.id, "quantity": 1},
    )
    ord_res = merchant_commerce_agent.dispatch_message(db, ord_msg)
    order_id = ord_res.data["order_id"]

    # Propose payment
    pay_msg = AgentMessage(
        message_id="msg_limit_02",
        session_id=session.session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="limit_tester"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.PROPOSE_PAYMENT,
        payload={"order_id": order_id},
    )
    pay_res = merchant_commerce_agent.dispatch_message(db, pay_msg)
    assert pay_res.success is False
    assert pay_res.error.code == ErrorCodes.PAYMENT_LIMIT_EXCEEDED


def test_cross_merchant_isolation(db: Session, sample_merchant: Merchant):
    """Test AI Buyer cannot query products of another merchant."""
    other_merchant = Merchant(
        name="Other Merchant",
        email="other@example.com",
    )
    db.add(other_merchant)
    db.commit()
    db.refresh(other_merchant)

    other_product = Product(
        merchant_id=other_merchant.id,
        name="Secret Item",
        category="Secret",
        price=100.0,
        sku="SECRET-SKU",
        stock_quantity=10,
    )
    db.add(other_product)
    db.commit()
    db.refresh(other_product)

    session = session_manager.create_session(
        db=db,
        merchant_id=sample_merchant.id,
        buyer_id="snooper_buyer",
    )

    # Attempt to fetch other merchant's product
    get_msg = AgentMessage(
        message_id="msg_snoop",
        session_id=session.session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="snooper_buyer"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.GET_PRODUCT,
        payload={"product_id": other_product.id},
    )
    res = merchant_commerce_agent.dispatch_message(db, get_msg)
    assert res.success is False
    assert res.error.code == ErrorCodes.PRODUCT_NOT_FOUND
