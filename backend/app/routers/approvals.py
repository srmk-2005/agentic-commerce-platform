"""API Router for Merchant Approvals & Rejections."""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Approval, ApprovalStatus
from app.schemas.approval import (
    ApprovalActionRequest,
    ApprovalRejectRequest,
    ApprovalResponse,
)
from app.services.growth_service import GrowthService

router = APIRouter(prefix="/approvals", tags=["Merchant Approvals"])


def _format_approval(appr: Approval) -> ApprovalResponse:
    try:
        parsed_meta = json.loads(appr.metadata_json or "{}")
    except Exception:
        parsed_meta = None

    return ApprovalResponse(
        id=appr.id,
        merchant_id=appr.merchant_id,
        action_type=appr.action_type,
        action_id=appr.action_id,
        status=appr.status,
        requested_at=appr.requested_at,
        reviewed_at=appr.reviewed_at,
        reviewed_by=appr.reviewed_by,
        reason=appr.reason,
        metadata_json=appr.metadata_json,
        metadata_parsed=parsed_meta,
    )


@router.get(
    "",
    response_model=List[ApprovalResponse],
    summary="List approvals with optional merchant and status filters",
)
def list_approvals(
    merchant_id: Optional[int] = Query(None, gt=0),
    approval_status: Optional[ApprovalStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(Approval)
    if merchant_id:
        query = query.filter(Approval.merchant_id == merchant_id)
    if approval_status:
        query = query.filter(Approval.status == approval_status)

    approvals = query.order_by(Approval.requested_at.desc()).all()
    return [_format_approval(a) for a in approvals]


@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    summary="Get approval details by ID",
)
def get_approval(
    approval_id: int,
    db: Session = Depends(get_db),
):
    appr = db.query(Approval).filter(Approval.id == approval_id).first()
    if not appr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval #{approval_id} not found.")
    return _format_approval(appr)


@router.post(
    "/{approval_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve and execute a proposed growth action",
)
def approve_proposal(
    approval_id: int,
    payload: ApprovalActionRequest = ApprovalActionRequest(),
    db: Session = Depends(get_db),
):
    """
    Approves a proposal, re-validates safety constraints immediately,
    and executes the campaign creation idempotently.
    """
    return GrowthService.approve_action(
        db=db,
        approval_id=approval_id,
        reviewed_by=payload.reviewed_by or "Merchant Owner",
    )


@router.post(
    "/{approval_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject a proposed growth action",
)
def reject_proposal(
    approval_id: int,
    payload: ApprovalRejectRequest = ApprovalRejectRequest(),
    db: Session = Depends(get_db),
):
    """
    Rejects the proposal, prevents autonomous retry, and records the audit reason.
    """
    return GrowthService.reject_action(
        db=db,
        approval_id=approval_id,
        reason=payload.reason,
        reviewed_by=payload.reviewed_by or "Merchant Owner",
    )


@router.post(
    "/{approval_id}/simulate-failure",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    summary="Simulate a transient downstream failure during approval for demonstration",
)
def simulate_approval_failure(
    approval_id: int,
    payload: ApprovalActionRequest = ApprovalActionRequest(),
    db: Session = Depends(get_db),
):
    """
    Demonstrates resilient failure handling: marked as FAILED in audit logs
    with ZERO money movement or broken state.
    """
    return GrowthService.simulate_failure_approve(
        db=db,
        approval_id=approval_id,
        reviewed_by=payload.reviewed_by or "Merchant Owner",
    )
