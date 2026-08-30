"""Pydantic schemas for Audit Logs."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from app.db.models import ActorType


class AuditLogResponse(BaseModel):
    id: int
    merchant_id: int
    actor_type: ActorType
    actor_id: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    status: str
    reason: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
