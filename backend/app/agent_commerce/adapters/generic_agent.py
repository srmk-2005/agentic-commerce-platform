"""Generic Agent Adapter: Reference protocol bridge for external autonomous buyers."""
from typing import Any, Dict, Optional
from app.agent_commerce.schemas import (
    AgentMessage,
    AgentResponse,
    AgentSenderRecipient,
    ProtocolAction,
)


class GenericAgentAdapter:
    """Protocol adapter for transforming external agent payloads into standardized Mercora AgentMessages."""

    @staticmethod
    def build_message(
        session_id: str,
        buyer_id: str,
        merchant_id: int,
        action: ProtocolAction,
        payload: Dict[str, Any],
        trace_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> AgentMessage:
        import uuid

        return AgentMessage(
            protocol_version="1.0",
            message_id=message_id or f"msg_{uuid.uuid4().hex[:10]}",
            session_id=session_id,
            trace_id=trace_id,
            sender=AgentSenderRecipient(type="AI_BUYER", id=buyer_id),
            recipient=AgentSenderRecipient(type="MERCHANT", id=str(merchant_id)),
            action=action,
            payload=payload,
        )

    @staticmethod
    def parse_response(response_dict: Dict[str, Any]) -> AgentResponse:
        """Parse raw JSON dict into standardized AgentResponse."""
        return AgentResponse.model_validate(response_dict)
