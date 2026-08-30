"""Agent API router exposing LangGraph revenue analysis and conversational assistant."""
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.agent.graph import create_merchant_agent_graph
from app.agent.llm import llm_manager
from app.agent.prompts import AGENT_SYSTEM_PROMPT, CHAT_ASSISTANT_PROMPT
from app.agent.schemas import (
    AgentAnalysisResponse,
    AgentChatRequest,
    AgentChatResponse,
    AgentSummaryMetrics,
    Opportunity,
)
from app.db.database import get_db
from app.db.models import Approval, ApprovalStatus, Campaign, CampaignStatus, Product
from app.schemas.growth import ActionProposal, ActionProposalCreate
from app.services.audit_service import audit_service
from app.services.growth_service import GrowthService
from app.services.merchant_service import MerchantService

router = APIRouter(prefix="/agent", tags=["Merchant AI Agent"])


class AgentAnalyzeRequest(BaseModel):
    merchant_id: int = Field(..., gt=0, description="Merchant store ID to analyze")
    request: Optional[str] = Field(
        "Analyze my product catalog and sales history to find revenue opportunities.",
        description="Optional custom analysis query or focus",
    )


@router.post(
    "/analyze",
    response_model=AgentAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze store for revenue opportunities using LangGraph",
)
def analyze_merchant_store(
    payload: AgentAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Executes the multi-node LangGraph pipeline to generate data-backed,
    explainable revenue growth recommendations.
    """
    # 1. Verify merchant exists
    merchant = MerchantService.get_merchant(db, payload.merchant_id)
    if not merchant:
        audit_service.log_agent_action(
            payload.merchant_id,
            "ANALYZE_STORE_FAILED",
            {"error": "Merchant not found"},
            error="Merchant not found",
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {payload.merchant_id} not found.",
        )

    audit_service.log_agent_action(
        payload.merchant_id,
        "ANALYZE_STORE_STARTED",
        {"user_request": payload.request},
        db=db,
    )

    try:
        # Build and invoke LangGraph workflow
        app_graph = create_merchant_agent_graph(db)
        initial_state = {
            "merchant_id": payload.merchant_id,
            "user_request": payload.request,
        }

        final_state = app_graph.invoke(initial_state)

        if final_state.get("error"):
            audit_service.log_agent_action(
                payload.merchant_id,
                "ANALYZE_STORE_ERROR",
                {"error": final_state["error"]},
                error=final_state["error"],
                db=db,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=final_state["error"],
            )

        opportunities = [
            Opportunity.model_validate(opp)
            for opp in final_state.get("validated_opportunities", [])
        ]

        audit_service.log_agent_action(
            payload.merchant_id,
            "ANALYZE_STORE_COMPLETED",
            {
                "opportunities_count": len(opportunities),
                "provider": final_state.get("used_llm_provider"),
                "is_fallback": final_state.get("is_fallback_mode"),
            },
            db=db,
        )

        return AgentAnalysisResponse(
            merchant_id=payload.merchant_id,
            summary=final_state.get("final_response", "Analysis complete."),
            opportunities=opportunities,
            proposals=[],
            provider_used=final_state.get("used_llm_provider", "Deterministic Engine"),
            is_fallback_mode=final_state.get("is_fallback_mode", False),
        )
    except HTTPException:
        raise
    except Exception as e:
        audit_service.log_agent_action(
            payload.merchant_id,
            "ANALYZE_STORE_EXCEPTION",
            {"exception": str(e)},
            error=str(e),
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during agent analysis: {str(e)}",
        )


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with the Merchant AI Assistant",
)
def chat_with_agent(
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
):
    """
    Merchant conversational assistant that interprets merchant requests,
    references real database metrics, offers targeted recommendations, and
    generates structured Action Proposals requiring merchant approval.
    """
    merchant = MerchantService.get_merchant(db, payload.merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {payload.merchant_id} not found.",
        )

    audit_service.log_agent_action(
        payload.merchant_id,
        "CHAT_REQUEST",
        {"message": payload.message},
        db=db,
    )

    try:
        # Run graph to get latest validated opportunities and context
        app_graph = create_merchant_agent_graph(db)
        state = app_graph.invoke({
            "merchant_id": payload.merchant_id,
            "user_request": payload.message,
        })

        opps = [
            Opportunity.model_validate(opp)
            for opp in state.get("validated_opportunities", [])
        ]

        # Context for conversational response
        sales_summary = state.get("sales_summary", {})
        products = state.get("products", [])
        co_purchases = state.get("co_purchases", [])
        slow_moving = state.get("slow_moving", [])

        # Check for Action Intent: e.g. "create", "promote", "bundle", "discount", "campaign"
        msg_lower = payload.message.lower()
        proposals_generated: list[ActionProposal] = []

        is_action_intent = any(keyword in msg_lower for keyword in ["create", "launch", "promote", "bundle", "discount", "set up"])
        
        if is_action_intent:
            # Extract discount percentage if specified, default to 10%
            discount_val = 10.0
            match_disc = re.search(r"(\d+(\.\d+)?)%", msg_lower)
            if match_disc:
                discount_val = float(match_disc.group(1))

            # Match target products from catalog
            matched_products = [p for p in products if p["name"].lower() in msg_lower]

            if "bundle" in msg_lower or "cross" in msg_lower or ("shoes" in msg_lower and "socks" in msg_lower):
                # Bundle or cross-sell proposal
                p_shoes = next((p for p in products if "shoes" in p["name"].lower()), products[0] if products else None)
                p_socks = next((p for p in products if "socks" in p["name"].lower()), products[2] if len(products) > 2 else None)
                
                if p_shoes and p_socks:
                    target_pids = [p_shoes["id"], p_socks["id"]]
                    proposal_create = ActionProposalCreate(
                        merchant_id=payload.merchant_id,
                        action_type="CREATE_BUNDLE",
                        title="Runner Essentials Combo Bundle",
                        description=f"Bundle {p_shoes['name']} with {p_socks['name']} at {discount_val}% discount.",
                        campaign_type="BUNDLE",
                        target_product_ids=target_pids,
                        primary_product_id=p_shoes["id"],
                        recommended_product_ids=[p_socks["id"]],
                        discount_type="PERCENTAGE",
                        discount_value=discount_val,
                        campaign_duration_days=7,
                        expected_benefit="Increase average order value by packaging complementary athletic gear.",
                        reasoning="Strong historical co-purchase association identified between these catalog items.",
                    )
                    try:
                        prop = GrowthService.propose_action(db, proposal_create)
                        proposals_generated.append(prop)
                    except Exception as err:
                        print(f"Action proposal creation error: {err}")

            elif "slow" in msg_lower or "inventory" in msg_lower:
                if slow_moving:
                    slow_item = slow_moving[0]
                    proposal_create = ActionProposalCreate(
                        merchant_id=payload.merchant_id,
                        action_type="SLOW_MOVING_PROMOTION",
                        title=f"Liquidation Promotion: {slow_item['product_name']}",
                        description=f"Run a {discount_val}% discount campaign for 7 days to accelerate stock turnover.",
                        campaign_type="SLOW_MOVING_PRODUCT",
                        target_product_ids=[slow_item["product_id"]],
                        primary_product_id=slow_item["product_id"],
                        discount_type="PERCENTAGE",
                        discount_value=discount_val,
                        campaign_duration_days=7,
                        expected_benefit=f"Liquidate ₹{slow_item.get('unliquidated_capital', 0)} in stagnant inventory capital.",
                        reasoning="Item has high stock quantity with low sales velocity over recent order history.",
                    )
                    try:
                        prop = GrowthService.propose_action(db, proposal_create)
                        proposals_generated.append(prop)
                    except Exception as err:
                        print(f"Action proposal creation error: {err}")

            elif matched_products:
                # Custom campaign proposal for matched product
                target_p = matched_products[0]
                proposal_create = ActionProposalCreate(
                    merchant_id=payload.merchant_id,
                    action_type="CREATE_CAMPAIGN",
                    title=f"Special Promotion: {target_p['name']}",
                    description=f"{discount_val}% promotional campaign for {target_p['name']} for 7 days.",
                    campaign_type="GENERAL_PROMOTION",
                    target_product_ids=[target_p["id"]],
                    primary_product_id=target_p["id"],
                    discount_type="PERCENTAGE",
                    discount_value=discount_val,
                    campaign_duration_days=7,
                    expected_benefit="Boost unit sales and customer conversion on active catalog items.",
                    reasoning=f"Merchant requested campaign creation for {target_p['name']}.",
                )
                try:
                    prop = GrowthService.propose_action(db, proposal_create)
                    proposals_generated.append(prop)
                except Exception as err:
                    print(f"Action proposal creation error: {err}")

        # Filter relevant opportunities matching user intent if query is specific
        matched_opps = opps
        if "cross" in msg_lower or "together" in msg_lower:
            matched_opps = [o for o in opps if o.type == "CROSS_SELL"] or opps
        elif "upsell" in msg_lower or "upgrade" in msg_lower or "premium" in msg_lower:
            matched_opps = [o for o in opps if o.type == "UPSELL"] or opps
        elif "slow" in msg_lower or "stock" in msg_lower or "dead" in msg_lower:
            matched_opps = [o for o in opps if o.type == "SLOW_MOVING_PRODUCT"] or opps

        catalog_summary = "\n".join(
            f"- {p['name']} (₹{p['price']}, Stock: {p['stock_quantity']}, Category: {p['category']})"
            for p in products
        )
        opps_summary = "\n".join(
            f"- {o.title}: {o.description} (Fact: {o.fact_statement})"
            for o in matched_opps
        )

        chat_prompt = CHAT_ASSISTANT_PROMPT.format(
            user_message=payload.message,
            merchant_name=merchant.name,
            currency=merchant.currency,
            total_revenue=sales_summary.get("total_revenue", 0.0),
            aov=sales_summary.get("average_order_value", 0.0),
            relevant_data=catalog_summary,
            opportunities_list=opps_summary or "No active opportunities",
        )

        def fallback_chat():
            if proposals_generated:
                p = proposals_generated[0]
                return (
                    f"I have prepared an **Action Proposal** for **{p.title}** ({p.discount_value}% discount for {p.campaign_duration_days} days).\n\n"
                    f"**Safety Status**: Validated against merchant policies (within {p.discount_value}% limit).\n"
                    f"**Next Step**: Please review and approve this proposal in the Approvals queue to activate the campaign."
                )

            if "cross" in msg_lower or "together" in msg_lower:
                top_cp = state.get("co_purchases", [])
                if top_cp:
                    cp = top_cp[0]
                    return (
                        f"Based on historical sales for {merchant.name}, **{cp['product_a_name']}** and **{cp['product_b_name']}** "
                        f"are frequently purchased together ({cp['co_purchase_orders']} shared orders).\n\n"
                        f"I recommend setting up a checkout cross-sell promotion to attach {cp['product_b_name']} whenever customers buy {cp['product_a_name']}."
                    )
            elif "upsell" in msg_lower or "upgrade" in msg_lower:
                upsell_opps = [o for o in opps if o.type == "UPSELL"]
                if upsell_opps:
                    return f"I found a strong upsell opportunity: **{upsell_opps[0].title}**.\n\n{upsell_opps[0].reasoning}"

            return (
                f"Hello {merchant.name}! I analyzed your catalog ({len(products)} items) and sales history.\n\n"
                f"I have identified **{len(matched_opps)} active revenue opportunities** for your store, focusing on cross-selling high affinity accessories and promoting performance upgrades."
            )

        response_text, provider_used, is_fallback = llm_manager.invoke_with_fallback(
            prompt=chat_prompt,
            system_prompt=AGENT_SYSTEM_PROMPT,
            fallback_generator=fallback_chat,
        )

        audit_service.log_agent_action(
            payload.merchant_id,
            "CHAT_RESPONSE_GENERATED",
            {
                "provider": provider_used,
                "is_fallback": is_fallback,
                "proposals_count": len(proposals_generated),
            },
            db=db,
        )

        return AgentChatResponse(
            response=response_text,
            opportunities=matched_opps,
            proposals=proposals_generated,
            provider_used=provider_used,
            is_fallback_mode=is_fallback,
        )
    except Exception as e:
        audit_service.log_agent_action(
            payload.merchant_id,
            "CHAT_EXCEPTION",
            {"exception": str(e)},
            error=str(e),
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat execution failed: {str(e)}",
        )


@router.get(
    "/metrics/{merchant_id}",
    response_model=AgentSummaryMetrics,
    summary="Get summarized AI opportunity and approval metrics for dashboard",
)
def get_agent_metrics(merchant_id: int, db: Session = Depends(get_db)):
    """Lightweight summary of revenue opportunities and pending approvals for dashboard KPI integration."""
    merchant = MerchantService.get_merchant(db, merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {merchant_id} not found.",
        )

    app_graph = create_merchant_agent_graph(db)
    state = app_graph.invoke({
        "merchant_id": merchant_id,
        "user_request": "Summary metrics",
    })

    opps = state.get("validated_opportunities", [])
    total_opportunities = len(opps)
    high_confidence_count = sum(1 for o in opps if o.get("confidence", 0) >= 0.80)
    potential_revenue_impact = sum(o.get("estimated_revenue_impact", 0.0) for o in opps)

    pending_approvals = (
        db.query(Approval)
        .filter(Approval.merchant_id == merchant_id, Approval.status == ApprovalStatus.PENDING)
        .count()
    )
    active_campaigns = (
        db.query(Campaign)
        .filter(Campaign.merchant_id == merchant_id, Campaign.status == CampaignStatus.ACTIVE)
        .count()
    )

    return AgentSummaryMetrics(
        total_opportunities=total_opportunities,
        high_confidence_count=high_confidence_count,
        potential_revenue_impact=round(potential_revenue_impact, 2),
        pending_approvals_count=pending_approvals,
        active_campaigns_count=active_campaigns,
        provider_used=state.get("used_llm_provider", "Deterministic Engine"),
        is_fallback_mode=state.get("is_fallback_mode", False),
    )
