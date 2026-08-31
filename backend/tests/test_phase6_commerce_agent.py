"""Integration tests for Merchant Commerce Agent Protocol Message Dispatcher."""
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
from app.db.models import Merchant, Order, Product, SessionStatus


def test_e2e_agent_commerce_flow(db: Session, sample_merchant: Merchant, sample_product: Product):
    """Test full message lifecycle: DISCOVER -> SEARCH -> CHECK_INVENTORY -> CREATE_ORDER -> PROPOSE_PAYMENT."""
    # 1. Create session
    session = session_manager.create_session(
        db=db,
        merchant_id=sample_merchant.id,
        buyer_id="flow_buyer_01",
    )
    session_id = session.session_id

    # 2. DISCOVER
    disc_msg = AgentMessage(
        message_id="msg_01",
        session_id=session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="flow_buyer_01"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.DISCOVER,
    )
    disc_res = merchant_commerce_agent.dispatch_message(db, disc_msg)
    assert disc_res.success is True
    assert disc_res.data["merchant_name"] == sample_merchant.name

    # 3. SEARCH
    search_msg = AgentMessage(
        message_id="msg_02",
        session_id=session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="flow_buyer_01"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.SEARCH,
        payload={"query": sample_product.name[:4]},
    )
    search_res = merchant_commerce_agent.dispatch_message(db, search_msg)
    assert search_res.success is True
    assert len(search_res.data["products"]) >= 1

    # 4. CHECK_INVENTORY
    inv_msg = AgentMessage(
        message_id="msg_03",
        session_id=session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="flow_buyer_01"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.CHECK_INVENTORY,
        payload={"product_id": sample_product.id, "quantity": 1},
    )
    inv_res = merchant_commerce_agent.dispatch_message(db, inv_msg)
    assert inv_res.success is True
    assert inv_res.data["in_stock"] is True

    # 5. CREATE_ORDER
    ord_msg = AgentMessage(
        message_id="msg_04",
        session_id=session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="flow_buyer_01"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.CREATE_ORDER,
        payload={"product_id": sample_product.id, "quantity": 1},
    )
    ord_res = merchant_commerce_agent.dispatch_message(db, ord_msg)
    assert ord_res.success is True
    order_id = ord_res.data["order_id"]
    assert order_id is not None

    # 6. PROPOSE_PAYMENT
    pay_msg = AgentMessage(
        message_id="msg_05",
        session_id=session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="flow_buyer_01"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.PROPOSE_PAYMENT,
        payload={"order_id": order_id},
    )
    pay_res = merchant_commerce_agent.dispatch_message(db, pay_msg)
    assert pay_res.success is True
    assert pay_res.data["amount"] == sample_product.price
    assert pay_res.data["requires_approval"] is True


def test_out_of_stock_inventory_check(db: Session, sample_merchant: Merchant, sample_product: Product):
    """Test checking inventory beyond available stock returns OUT_OF_STOCK error."""
    session = session_manager.create_session(
        db=db,
        merchant_id=sample_merchant.id,
        buyer_id="oos_buyer",
    )
    inv_msg = AgentMessage(
        message_id="msg_oos",
        session_id=session.session_id,
        sender=AgentSenderRecipient(type="AI_BUYER", id="oos_buyer"),
        recipient=AgentSenderRecipient(type="MERCHANT", id=str(sample_merchant.id)),
        action=ProtocolAction.CHECK_INVENTORY,
        payload={"product_id": sample_product.id, "quantity": sample_product.stock_quantity + 1000},
    )
    res = merchant_commerce_agent.dispatch_message(db, inv_msg)
    assert res.success is False
    assert res.error.code == ErrorCodes.OUT_OF_STOCK
