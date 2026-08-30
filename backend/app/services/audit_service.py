"""Audit logging service for tracking agent actions, approvals, campaigns, and state transitions."""
import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models import ActorType, AuditLog

logger = logging.getLogger("agent_audit")
logger.setLevel(logging.INFO)


class AuditService:
    """Structured audit store for Phase 2 and Phase 3 actions."""

    def __init__(self):
        self._audit_logs: List[Dict[str, Any]] = []

    def log_agent_action(
        self,
        merchant_id: int,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        db: Optional[Session] = None,
        actor_type: ActorType = ActorType.AI_AGENT,
        actor_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        status: str = "SUCCESS",
    ) -> Dict[str, Any]:
        """
        Record an agent lifecycle event, approval, or campaign execution.
        Sanitizes sensitive keys and persists to database if DB session is available.
        """
        sanitized_details = {}
        if details:
            for k, v in details.items():
                if any(sec in k.lower() for sec in ["key", "secret", "password", "token", "auth"]):
                    sanitized_details[k] = "[REDACTED]"
                else:
                    sanitized_details[k] = v

        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "merchant_id": merchant_id,
            "actor_type": actor_type.value if hasattr(actor_type, "value") else str(actor_type),
            "actor_id": actor_id or "AI_AGENT",
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": "FAILED" if error else status,
            "reason": error or sanitized_details.get("reason"),
            "details": sanitized_details,
            "error": error,
        }

        self._audit_logs.append(entry)

        if error:
            logger.error(f"[AUDIT] Merchant {merchant_id} | {action} | ERROR: {error}")
        else:
            logger.info(f"[AUDIT] Merchant {merchant_id} | {action} | Details: {sanitized_details}")

        # Persist to database if db session provided
        if db:
            try:
                db_log = AuditLog(
                    merchant_id=merchant_id,
                    actor_type=actor_type,
                    actor_id=actor_id or "AI_AGENT",
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    status="FAILED" if error else status,
                    reason=error or sanitized_details.get("reason"),
                    metadata_json=json.dumps(sanitized_details, default=str),
                )
                db.add(db_log)
                db.commit()
            except Exception as ex:
                logger.warning(f"Failed to persist audit log to DB: {ex}")

        return entry

    def get_merchant_logs(
        self,
        db: Session,
        merchant_id: int,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Retrieve historical audit records from database for a merchant."""
        return (
            db.query(AuditLog)
            .filter(AuditLog.merchant_id == merchant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )


# Global audit service instance
audit_service = AuditService()
