"""Revenue Growth Action & Campaign Execution Service."""
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.db.models import (
    ActorType,
    AgentAction,
    AgentActionStatus,
    Approval,
    ApprovalActionType,
    ApprovalStatus,
    Campaign,
    CampaignProduct,
    CampaignStatus,
    CampaignType,
    DiscountType,
    Merchant,
    Offer,
    OfferType,
    Product,
    ProductCampaignRole,
)
from app.schemas.growth import ActionProposal, ActionProposalCreate
from app.services.audit_service import audit_service
from app.services.safety_service import SafetyService


class GrowthService:
    """Core deterministic orchestrator for Action Proposals, Merchant Approvals, and Campaign Execution."""

    @classmethod
    def propose_action(
        cls,
        db: Session,
        proposal_in: ActionProposalCreate,
        session_id: str = "agent-growth-session",
    ) -> ActionProposal:
        """
        Create a structured, validated action proposal.
        The action is never executed directly; it is placed in PENDING_APPROVAL status.
        """
        # 1. Run strict deterministic safety policy checks
        safety_result = SafetyService.validate_action_proposal(db, proposal_in)
        if not safety_result.is_safe:
            audit_service.log_agent_action(
                merchant_id=proposal_in.merchant_id,
                action="PROPOSE_ACTION_REJECTED_BY_POLICY",
                details={
                    "title": proposal_in.title,
                    "rejections": safety_result.rejection_reasons,
                },
                error="; ".join(safety_result.rejection_reasons),
                db=db,
                actor_type=ActorType.AI_AGENT,
                status="FAILED",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action proposal violates merchant safety policy: {'; '.join(safety_result.rejection_reasons)}",
            )

        # 2. Ingest catalog products for deterministic pricing calculations
        all_pids = list(set(proposal_in.target_product_ids + [
            pid for pid in ([proposal_in.primary_product_id] if proposal_in.primary_product_id else []) + proposal_in.recommended_product_ids
        ]))
        products = db.query(Product).filter(Product.id.in_(all_pids)).all()
        prod_map = {p.id: p for p in products}

        target_names = [prod_map[pid].name for pid in proposal_in.target_product_ids if pid in prod_map]
        primary_name = prod_map[proposal_in.primary_product_id].name if proposal_in.primary_product_id in prod_map else None
        rec_names = [prod_map[pid].name for pid in proposal_in.recommended_product_ids if pid in prod_map]

        # Calculate original bundle price and discounted total deterministically
        original_price = sum(prod_map[pid].price for pid in proposal_in.target_product_ids if pid in prod_map)
        discounted_price = original_price
        if proposal_in.discount_type == "PERCENTAGE":
            discounted_price = round(original_price * (1.0 - (proposal_in.discount_value / 100.0)), 2)
        elif proposal_in.discount_type == "FIXED_AMOUNT":
            discounted_price = max(0.0, round(original_price - proposal_in.discount_value, 2))

        # 3. Create AgentAction record (PROPOSED / PENDING_APPROVAL)
        agent_action = AgentAction(
            merchant_id=proposal_in.merchant_id,
            agent_session_id=session_id,
            action_type=proposal_in.action_type,
            target_type="CAMPAIGN",
            status=AgentActionStatus.PENDING_APPROVAL,
            reason=proposal_in.reasoning or proposal_in.description,
            input_data=json.dumps(proposal_in.model_dump(), default=str),
        )
        db.add(agent_action)
        db.flush()

        # 4. Create Approval Request
        meta_dict = {
            "title": proposal_in.title,
            "description": proposal_in.description,
            "campaign_type": proposal_in.campaign_type,
            "target_product_ids": proposal_in.target_product_ids,
            "target_product_names": target_names,
            "primary_product_id": proposal_in.primary_product_id,
            "primary_product_name": primary_name,
            "recommended_product_ids": proposal_in.recommended_product_ids,
            "recommended_product_names": rec_names,
            "discount_type": proposal_in.discount_type,
            "discount_value": proposal_in.discount_value,
            "original_bundle_price": original_price,
            "discounted_bundle_price": discounted_price,
            "campaign_duration_days": proposal_in.campaign_duration_days,
            "expected_benefit": proposal_in.expected_benefit or "Increase gross sales through strategic cross-selling",
            "risk_level": proposal_in.risk_level,
            "safety_checks": [c.model_dump() for c in safety_result.checks],
        }

        approval = Approval(
            merchant_id=proposal_in.merchant_id,
            action_type=ApprovalActionType.CREATE_CAMPAIGN,
            action_id=agent_action.id,
            status=ApprovalStatus.PENDING,
            reason=proposal_in.reasoning or f"AI proposal for {proposal_in.title}",
            metadata_json=json.dumps(meta_dict, default=str),
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        db.refresh(agent_action)

        # 5. Record Audit Log
        audit_service.log_agent_action(
            merchant_id=proposal_in.merchant_id,
            action="ACTION_PROPOSAL_CREATED",
            details={
                "proposal_title": proposal_in.title,
                "approval_id": approval.id,
                "action_id": agent_action.id,
                "discount": f"{proposal_in.discount_value}%",
            },
            db=db,
            actor_type=ActorType.AI_AGENT,
            entity_type="APPROVAL",
            entity_id=approval.id,
        )

        return ActionProposal(
            id=f"prop-{approval.id}",
            merchant_id=proposal_in.merchant_id,
            action_type=proposal_in.action_type,
            opportunity_id=proposal_in.opportunity_id,
            title=proposal_in.title,
            description=proposal_in.description or "",
            campaign_type=proposal_in.campaign_type,
            target_product_ids=proposal_in.target_product_ids,
            target_product_names=target_names,
            primary_product_id=proposal_in.primary_product_id,
            primary_product_name=primary_name,
            recommended_product_ids=proposal_in.recommended_product_ids,
            recommended_product_names=rec_names,
            discount_type=proposal_in.discount_type,
            discount_value=proposal_in.discount_value,
            original_bundle_price=original_price,
            discounted_bundle_price=discounted_price,
            campaign_duration_days=proposal_in.campaign_duration_days,
            expected_benefit=proposal_in.expected_benefit or "Increase store sales",
            reasoning=proposal_in.reasoning or "",
            risk_level=proposal_in.risk_level,
            requires_approval=True,
            safety_check=safety_result,
            approval_id=approval.id,
            agent_action_id=agent_action.id,
        )

    @classmethod
    def approve_action(
        cls,
        db: Session,
        approval_id: int,
        reviewed_by: str = "Merchant Owner",
    ) -> Dict[str, Any]:
        """
        Execute an approved action.
        - Guarantees idempotency (repeated approval returns existing result).
        - Re-validates safety policy immediately prior to execution.
        """
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval #{approval_id} not found.")

        # 1. Idempotency & Stale Status Handling
        if approval.status == ApprovalStatus.APPROVED:
            # Already executed; find and return the existing campaign
            agent_action = db.query(AgentAction).filter(AgentAction.id == approval.action_id).first()
            if agent_action and agent_action.target_id:
                existing_campaign = db.query(Campaign).filter(Campaign.id == agent_action.target_id).first()
                if existing_campaign:
                    return {
                        "message": "Action has already been approved and executed (idempotent response).",
                        "campaign_id": existing_campaign.id,
                        "status": existing_campaign.status.value,
                        "approval_id": approval.id,
                        "is_duplicate": True,
                    }

        if approval.status == ApprovalStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot approve an action that has already been REJECTED by the merchant.",
            )

        # 2. Parse proposal metadata
        try:
            meta = json.loads(approval.metadata_json or "{}")
        except Exception:
            meta = {}

        # 3. MANDATORY PRE-EXECUTION SAFETY RE-VALIDATION
        proposal_reval = ActionProposalCreate(
            merchant_id=approval.merchant_id,
            action_type=meta.get("action_type", "CREATE_CAMPAIGN"),
            title=meta.get("title", "Growth Campaign"),
            description=meta.get("description"),
            campaign_type=meta.get("campaign_type", "CROSS_SELL"),
            target_product_ids=meta.get("target_product_ids", []),
            primary_product_id=meta.get("primary_product_id"),
            recommended_product_ids=meta.get("recommended_product_ids", []),
            discount_type=meta.get("discount_type", "PERCENTAGE"),
            discount_value=float(meta.get("discount_value", 10.0)),
            campaign_duration_days=int(meta.get("campaign_duration_days", 7)),
        )

        reval_result = SafetyService.validate_action_proposal(db, proposal_reval)
        if not reval_result.is_safe:
            approval.status = ApprovalStatus.REJECTED
            approval.reason = f"Pre-execution re-validation failed: {'; '.join(reval_result.rejection_reasons)}"
            approval.reviewed_by = reviewed_by
            approval.reviewed_at = datetime.now(timezone.utc)
            db.commit()

            audit_service.log_agent_action(
                merchant_id=approval.merchant_id,
                action="APPROVAL_REVALIDATION_FAILED",
                details={"rejection_reasons": reval_result.rejection_reasons},
                error="; ".join(reval_result.rejection_reasons),
                db=db,
                actor_type=ActorType.SYSTEM,
                entity_type="APPROVAL",
                entity_id=approval.id,
                status="FAILED",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Safety re-validation failed before execution: {'; '.join(reval_result.rejection_reasons)}",
            )

        # 4. EXECUTE GROWTH ACTION (Create Campaign, CampaignProduct, Offer)
        now = datetime.now(timezone.utc)
        duration_days = int(meta.get("campaign_duration_days", 7))
        end_date = now + timedelta(days=duration_days)

        camp_type_str = meta.get("campaign_type", "CROSS_SELL")
        try:
            camp_type_enum = CampaignType(camp_type_str)
        except Exception:
            camp_type_enum = CampaignType.CROSS_SELL

        campaign = Campaign(
            merchant_id=approval.merchant_id,
            name=meta.get("title", "Growth Promotion"),
            description=meta.get("description"),
            campaign_type=camp_type_enum,
            status=CampaignStatus.ACTIVE,
            start_date=now,
            end_date=end_date,
            created_by=ActorType.AI_AGENT,
        )
        db.add(campaign)
        db.flush()

        # Add products to campaign
        for pid in meta.get("target_product_ids", []):
            role = ProductCampaignRole.PRIMARY if pid == meta.get("primary_product_id") else ProductCampaignRole.RECOMMENDED
            db.add(CampaignProduct(campaign_id=campaign.id, product_id=pid, role=role))

        # Add Offer
        disc_type_str = meta.get("discount_type", "PERCENTAGE")
        disc_type_enum = DiscountType.PERCENTAGE if disc_type_str == "PERCENTAGE" else DiscountType.FIXED_AMOUNT

        offer_type_enum = OfferType.CROSS_SELL
        if camp_type_enum == CampaignType.UPSELL:
            offer_type_enum = OfferType.UPSELL
        elif camp_type_enum == CampaignType.BUNDLE:
            offer_type_enum = OfferType.BUNDLE
        elif camp_type_enum == CampaignType.SLOW_MOVING_PRODUCT:
            offer_type_enum = OfferType.PRODUCT_DISCOUNT

        offer = Offer(
            merchant_id=approval.merchant_id,
            campaign_id=campaign.id,
            product_id=meta.get("recommended_product_ids", [None])[0] if meta.get("recommended_product_ids") else None,
            offer_type=offer_type_enum,
            discount_type=disc_type_enum,
            discount_value=float(meta.get("discount_value", 10.0)),
            maximum_discount_amount=float(meta.get("maximum_discount_amount", 500.0)),
            status="ACTIVE",
        )
        db.add(offer)

        # 5. Update Approval & AgentAction states
        approval.status = ApprovalStatus.APPROVED
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = now

        agent_action = db.query(AgentAction).filter(AgentAction.id == approval.action_id).first()
        if agent_action:
            agent_action.status = AgentActionStatus.EXECUTED
            agent_action.target_id = campaign.id
            agent_action.completed_at = now
            agent_action.output_data = json.dumps({"campaign_id": campaign.id, "offer_id": offer.id}, default=str)

        db.commit()

        # 6. Audit Logging
        audit_service.log_agent_action(
            merchant_id=approval.merchant_id,
            action="ACTION_APPROVED_AND_EXECUTED",
            details={
                "approval_id": approval.id,
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "reviewed_by": reviewed_by,
            },
            db=db,
            actor_type=ActorType.MERCHANT,
            actor_id=reviewed_by,
            entity_type="CAMPAIGN",
            entity_id=campaign.id,
            status="SUCCESS",
        )

        return {
            "message": f"Action successfully approved and executed. Campaign #{campaign.id} is now ACTIVE.",
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "status": campaign.status.value,
            "approval_id": approval.id,
            "is_duplicate": False,
        }

    @classmethod
    def reject_action(
        cls,
        db: Session,
        approval_id: int,
        reason: Optional[str] = None,
        reviewed_by: str = "Merchant Owner",
    ) -> Dict[str, Any]:
        """
        Reject a proposed action.
        - Guarantees rejection idempotency.
        - Strictly prevents the AI agent from auto-retrying.
        """
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval #{approval_id} not found.")

        if approval.status == ApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reject an action that has already been approved and executed.",
            )

        if approval.status == ApprovalStatus.REJECTED:
            return {
                "message": "Action was already rejected.",
                "approval_id": approval.id,
                "status": "REJECTED",
                "is_duplicate": True,
            }

        now = datetime.now(timezone.utc)
        rejection_reason = reason or "Merchant declined proposal."
        approval.status = ApprovalStatus.REJECTED
        approval.reason = rejection_reason
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = now

        agent_action = db.query(AgentAction).filter(AgentAction.id == approval.action_id).first()
        if agent_action:
            agent_action.status = AgentActionStatus.REJECTED
            agent_action.reason = rejection_reason
            agent_action.completed_at = now

        db.commit()

        # Audit Rejection
        audit_service.log_agent_action(
            merchant_id=approval.merchant_id,
            action="ACTION_REJECTED",
            details={
                "approval_id": approval.id,
                "reason": rejection_reason,
                "reviewed_by": reviewed_by,
            },
            db=db,
            actor_type=ActorType.MERCHANT,
            actor_id=reviewed_by,
            entity_type="APPROVAL",
            entity_id=approval.id,
            status="REJECTED",
        )

        return {
            "message": "Action proposal rejected. The AI agent will not automatically retry this action.",
            "approval_id": approval.id,
            "status": "REJECTED",
            "reason": rejection_reason,
        }

    @classmethod
    def simulate_failure_approve(
        cls,
        db: Session,
        approval_id: int,
        reviewed_by: str = "Merchant Owner",
    ) -> Dict[str, Any]:
        """
        Simulates a transient downstream activation failure for live hackathon demonstration.
        Leaves financial transactions untouched and records the failure in audit logs.
        """
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Approval #{approval_id} not found.")

        agent_action = db.query(AgentAction).filter(AgentAction.id == approval.action_id).first()
        if agent_action:
            agent_action.status = AgentActionStatus.FAILED
            agent_action.reason = "Simulated downstream campaign activation timeout."

        audit_service.log_agent_action(
            merchant_id=approval.merchant_id,
            action="CAMPAIGN_ACTIVATION_FAILED",
            details={"approval_id": approval.id, "error": "Simulated downstream activation timeout"},
            error="Downstream campaign service temporarily unavailable. No financial transaction attempted.",
            db=db,
            actor_type=ActorType.SYSTEM,
            entity_type="APPROVAL",
            entity_id=approval.id,
            status="FAILED",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Campaign activation failed (simulated). Zero financial transactions attempted. Retry is safe.",
        )
