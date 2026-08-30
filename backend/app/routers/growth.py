"""API Router for AI Revenue Growth Action Proposals and Safety Policies."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import AgentAction, Merchant
from app.schemas.growth import (
    ActionProposal,
    ActionProposalCreate,
    MerchantAiPolicyResponse,
    MerchantAiPolicyUpdate,
)
from app.services.growth_service import GrowthService
from app.services.safety_service import SafetyService

router = APIRouter(prefix="/growth", tags=["Revenue Growth Actions"])


@router.post(
    "/actions/propose",
    response_model=ActionProposal,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a validated AI Action Proposal requiring merchant approval",
)
def propose_growth_action(
    payload: ActionProposalCreate,
    db: Session = Depends(get_db),
):
    """
    Submits a structured action proposal. Runs strict safety policy validation,
    creates a pending AgentAction and Approval record, and logs audit events.
    """
    return GrowthService.propose_action(db, payload)


@router.get(
    "/actions",
    response_model=List[Dict[str, Any]],
    summary="List historical agent action tracking records",
)
def list_agent_actions(
    merchant_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(AgentAction)
    if merchant_id:
        query = query.filter(AgentAction.merchant_id == merchant_id)
    actions = query.order_by(AgentAction.created_at.desc()).limit(100).all()

    return [
        {
            "id": a.id,
            "merchant_id": a.merchant_id,
            "agent_session_id": a.agent_session_id,
            "action_type": a.action_type,
            "target_type": a.target_type,
            "target_id": a.target_id,
            "status": a.status.value,
            "reason": a.reason,
            "created_at": a.created_at,
            "completed_at": a.completed_at,
        }
        for a in actions
    ]


@router.get(
    "/policies/{merchant_id}",
    response_model=MerchantAiPolicyResponse,
    summary="Get merchant AI safety policy limits",
)
def get_merchant_policy(
    merchant_id: int,
    db: Session = Depends(get_db),
):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Merchant #{merchant_id} not found.")
    return SafetyService.get_or_create_policy(db, merchant_id)


@router.put(
    "/policies/{merchant_id}",
    response_model=MerchantAiPolicyResponse,
    summary="Update merchant AI safety policy limits",
)
def update_merchant_policy(
    merchant_id: int,
    payload: MerchantAiPolicyUpdate,
    db: Session = Depends(get_db),
):
    policy = SafetyService.get_or_create_policy(db, merchant_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(policy, field, val)

    db.commit()
    db.refresh(policy)
    return policy
