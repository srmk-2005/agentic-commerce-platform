"""Unit tests for Phase 6 Protocol Message Validation & Error Codes."""
import pytest
from app.agent_commerce.protocol import (
    ErrorCodes,
    SUPPORTED_ACTIONS,
    SUPPORTED_PROTOCOL_VERSION,
    create_error_response,
    create_success_response,
    validate_protocol_message,
)
from app.agent_commerce.schemas import (
    AgentMessage,
    AgentSenderRecipient,
    ProtocolAction,
)


def test_supported_protocol_version():
    """Verify supported protocol version is '1.0'."""
    assert SUPPORTED_PROTOCOL_VERSION == "1.0"
    assert "SEARCH" in SUPPORTED_ACTIONS
    assert "CREATE_ORDER" in SUPPORTED_ACTIONS
    assert "PROPOSE_PAYMENT" in SUPPORTED_ACTIONS


def test_validate_valid_message():
    """Test valid message passes validation."""
    msg = AgentMessage(
        protocol_version="1.0",
        message_id="msg_test_001",
        session_id="acs_test_123",
        sender=AgentSenderRecipient(type="AI_BUYER", id="buyer_1"),
        recipient=AgentSenderRecipient(type="MERCHANT", id="1"),
        action=ProtocolAction.SEARCH,
        payload={"query": "shoes"},
    )
    err = validate_protocol_message(msg)
    assert err is None


def test_validate_invalid_version():
    """Test unsupported protocol version returns UNSUPPORTED_PROTOCOL_VERSION error."""
    msg = AgentMessage(
        protocol_version="2.0",
        message_id="msg_test_002",
        session_id="acs_test_123",
        sender=AgentSenderRecipient(type="AI_BUYER", id="buyer_1"),
        recipient=AgentSenderRecipient(type="MERCHANT", id="1"),
        action=ProtocolAction.SEARCH,
    )
    err = validate_protocol_message(msg)
    assert err is not None
    assert err.success is False
    assert err.error.code == ErrorCodes.UNSUPPORTED_PROTOCOL_VERSION


def test_create_success_envelope():
    """Test success response envelope structure."""
    resp = create_success_response(
        message_id="msg_101",
        session_id="acs_101",
        trace_id="trace_101",
        action="SEARCH",
        data={"items_count": 5},
    )
    assert resp.success is True
    assert resp.protocol_version == "1.0"
    assert resp.data["items_count"] == 5
    assert resp.error is None


def test_create_error_envelope():
    """Test error response envelope structure."""
    resp = create_error_response(
        message_id="msg_102",
        session_id="acs_102",
        trace_id="trace_102",
        action="PROPOSE_PAYMENT",
        code=ErrorCodes.PAYMENT_LIMIT_EXCEEDED,
        message="Amount exceeds ₹5,000 limit.",
    )
    assert resp.success is False
    assert resp.error.code == ErrorCodes.PAYMENT_LIMIT_EXCEEDED
    assert "₹5,000" in resp.error.message
