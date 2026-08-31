"""Agent Commerce Session and End-to-End Trace Management."""
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.agent_commerce.schemas import (
    SessionResponse,
    SessionTimelineEvent,
    SessionTimelineResponse,
)
from app.db.models import (
    ActorType,
    AgentCommerceSession,
    Merchant,
    SessionStatus,
)
from app.services.audit_service import audit_service


class SessionManager:
    """Manages stateful agent commerce sessions and trace event timelines."""

    @staticmethod
    def create_session(
        db: Session,
        merchant_id: int,
        buyer_id: str = "demo_ai_buyer",
    ) -> AgentCommerceSession:
        """Create and persist a new Agent Commerce Session."""
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            raise ValueError(f"Merchant with ID {merchant_id} not found.")

        now = datetime.now(timezone.utc)
        session_id = f"acs_{uuid.uuid4().hex[:12]}"
        trace_id = f"trace_{uuid.uuid4().hex[:16]}"

        initial_event = {
            "timestamp": now.isoformat(),
            "action": "SESSION_CREATED",
            "actor": buyer_id,
            "status": "SUCCESS",
            "details": {"merchant_id": merchant_id, "buyer_id": buyer_id},
        }

        session = AgentCommerceSession(
            session_id=session_id,
            trace_id=trace_id,
            buyer_id=buyer_id,
            merchant_id=merchant_id,
            status=SessionStatus.DISCOVERY,
            events_json=json.dumps([initial_event]),
            created_at=now,
            expires_at=now + timedelta(hours=2),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Audit
        audit_service.log_agent_action(
            db=db,
            merchant_id=merchant_id,
            action="AGENT_SESSION_CREATED",
            entity_type="AgentCommerceSession",
            entity_id=session.id,
            status="SUCCESS",
            reason=f"Agent commerce session '{session_id}' started by '{buyer_id}'.",
            metadata={"session_id": session_id, "trace_id": trace_id, "buyer_id": buyer_id},
            actor_type=ActorType.AI_BUYER,
        )

        return session

    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[AgentCommerceSession]:
        """Fetch session and check for expiration."""
        session = db.query(AgentCommerceSession).filter(
            AgentCommerceSession.session_id == session_id
        ).first()

        if not session:
            return None

        # Expiry check
        now = datetime.now(timezone.utc)
        if session.expires_at:
            exp = (
                session.expires_at.replace(tzinfo=timezone.utc)
                if session.expires_at.tzinfo is None
                else session.expires_at
            )
            if exp < now and session.status not in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.EXPIRED]:
                session.status = SessionStatus.EXPIRED
                db.commit()

        return session

    @staticmethod
    def record_timeline_event(
        db: Session,
        session: AgentCommerceSession,
        action: str,
        actor: str,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Append a timestamped trace event to the session's chronological timeline."""
        now = datetime.now(timezone.utc)
        try:
            events = json.loads(session.events_json or "[]")
        except Exception:
            events = []

        event = {
            "timestamp": now.isoformat(),
            "action": action,
            "actor": actor,
            "status": status,
            "details": details or {},
        }
        events.append(event)
        session.events_json = json.dumps(events)
        session.updated_at = now
        db.commit()

    @staticmethod
    def update_session_state(
        db: Session,
        session: AgentCommerceSession,
        status: SessionStatus,
        product_id: Optional[int] = None,
        order_id: Optional[int] = None,
        payment_intent_id: Optional[int] = None,
    ):
        """Transition session state."""
        session.status = status
        if product_id is not None:
            session.selected_product_id = product_id
        if order_id is not None:
            session.order_id = order_id
        if payment_intent_id is not None:
            session.payment_intent_id = payment_intent_id

        session.updated_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def get_timeline(session: AgentCommerceSession) -> SessionTimelineResponse:
        """Format session timeline response."""
        try:
            raw_events = json.loads(session.events_json or "[]")
        except Exception:
            raw_events = []

        timeline_objs = [
            SessionTimelineEvent(
                timestamp=e.get("timestamp", ""),
                action=e.get("action", ""),
                actor=e.get("actor", ""),
                status=e.get("status", ""),
                details=e.get("details", {}),
            )
            for e in raw_events
        ]

        return SessionTimelineResponse(
            session_id=session.session_id,
            trace_id=session.trace_id,
            status=session.status.value,
            merchant_id=session.merchant_id,
            buyer_id=session.buyer_id,
            timeline=timeline_objs,
        )


session_manager = SessionManager()
