"""Standardized Protocol Validator and Message Envelope Factory."""
from typing import Any, Dict, List, Optional
from app.agent_commerce.schemas import (
    AgentError,
    AgentMessage,
    AgentResponse,
    ProtocolAction,
)

SUPPORTED_PROTOCOL_VERSION = "1.0"

SUPPORTED_ACTIONS: List[str] = [
    ProtocolAction.DISCOVER.value,
    ProtocolAction.SEARCH.value,
    ProtocolAction.GET_PRODUCT.value,
    ProtocolAction.CHECK_INVENTORY.value,
    ProtocolAction.CREATE_ORDER.value,
    ProtocolAction.PROPOSE_PAYMENT.value,
    ProtocolAction.GET_PAYMENT_STATUS.value,
]

# Stable Standard Error Codes
class ErrorCodes:
    MERCHANT_NOT_FOUND = "MERCHANT_NOT_FOUND"
    CAPABILITY_NOT_SUPPORTED = "CAPABILITY_NOT_SUPPORTED"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    PAYMENT_NOT_ALLOWED = "PAYMENT_NOT_ALLOWED"
    PAYMENT_LIMIT_EXCEEDED = "PAYMENT_LIMIT_EXCEEDED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    INVALID_SESSION = "INVALID_SESSION"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    UNSUPPORTED_PROTOCOL_VERSION = "UNSUPPORTED_PROTOCOL_VERSION"
    UNAUTHORIZED_SESSION = "UNAUTHORIZED_SESSION"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def validate_protocol_message(msg: AgentMessage) -> Optional[AgentResponse]:
    """Validate protocol version and format."""
    if msg.protocol_version != SUPPORTED_PROTOCOL_VERSION:
        return create_error_response(
            message_id=msg.message_id,
            session_id=msg.session_id,
            trace_id=msg.trace_id or "unknown",
            action=msg.action.value if hasattr(msg.action, "value") else str(msg.action),
            code=ErrorCodes.UNSUPPORTED_PROTOCOL_VERSION,
            message=f"Protocol version '{msg.protocol_version}' is not supported. Required: '{SUPPORTED_PROTOCOL_VERSION}'.",
        )

    if msg.action.value not in SUPPORTED_ACTIONS:
        return create_error_response(
            message_id=msg.message_id,
            session_id=msg.session_id,
            trace_id=msg.trace_id or "unknown",
            action=str(msg.action),
            code=ErrorCodes.CAPABILITY_NOT_SUPPORTED,
            message=f"Action '{msg.action}' is not supported by protocol {SUPPORTED_PROTOCOL_VERSION}.",
        )

    return None


def create_success_response(
    message_id: str,
    session_id: str,
    trace_id: str,
    action: str,
    data: Optional[Dict[str, Any]] = None,
) -> AgentResponse:
    """Create standardized success envelope."""
    return AgentResponse(
        success=True,
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id=message_id,
        session_id=session_id,
        trace_id=trace_id,
        action=action,
        data=data or {},
        error=None,
    )


def create_error_response(
    message_id: str,
    session_id: str,
    trace_id: str,
    action: str,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> AgentResponse:
    """Create standardized error envelope."""
    return AgentResponse(
        success=False,
        protocol_version=SUPPORTED_PROTOCOL_VERSION,
        message_id=message_id,
        session_id=session_id,
        trace_id=trace_id,
        action=action,
        data=None,
        error=AgentError(code=code, message=message, details=details),
    )
