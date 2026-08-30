"""Pydantic schemas for Merchant Approvals."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import ApprovalActionType, ApprovalStatus


class ApprovalActionRequest(BaseModel):
    reviewed_by: Optional[str] = Field(default="Merchant Owner", description="User identity approving the action")


class ApprovalRejectRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Optional explanation for rejecting the proposal")
    reviewed_by: Optional[str] = Field(default="Merchant Owner", description="User identity rejecting the action")


class ApprovalResponse(BaseModel):
    id: int
    merchant_id: int
    action_type: ApprovalActionType
    action_id: Optional[int] = None
    status: ApprovalStatus
    requested_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reason: Optional[str] = None
    metadata_json: Optional[str] = None
    metadata_parsed: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
