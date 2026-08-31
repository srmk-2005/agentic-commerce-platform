"""Router for Simulated AI Buyer Agent interactions (Phase 5)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.ai_buyer.agent import create_buyer_agent_graph
from app.ai_buyer.schemas import (
    BuyerChatRequest,
    BuyerChatResponse,
    BuyerProductOption,
    BuyerSimulationRequest,
    BuyerSimulationResponse,
)
from app.ai_buyer.tools import AICommerceClient
from app.db.database import get_db
from app.payments.payment_service import PaymentService
from app.payments.schemas import PaymentIntentResponse

router = APIRouter(prefix="/buyer", tags=["AI Buyer Simulator"])


@router.post(
    "/chat",
    response_model=BuyerChatResponse,
    summary="Chat with Simulated AI Buyer",
    description="Simulate external AI Buyer discovering the merchant, querying catalog, evaluating candidates, creating orders, and proposing payment intents.",
)
def buyer_chat_endpoint(
    req: BuyerChatRequest,
    db: Session = Depends(get_db),
):
    """Interact with simulated AI buyer agent."""
    client = AICommerceClient(db_session=db)
    graph = create_buyer_agent_graph(client)

    initial_state = {
        "buyer_request": req.message,
        "merchant_id": req.merchant_id,
        "execution_steps": [],
        "errors": [],
    }

    final_state = graph.invoke(initial_state)

    candidate_objs = [
        BuyerProductOption(
            id=c["id"],
            name=c["name"],
            category=c["category"],
            price=c["price"],
            availability=c["availability"],
            stock_quantity=c["stock_quantity"],
            relevance_score=c.get("relevance_score", 0.0),
            reason=c.get("reason"),
        )
        for c in final_state.get("candidate_products", [])
    ]

    selected_obj = None
    if final_state.get("selected_product"):
        sp = final_state["selected_product"]
        selected_obj = BuyerProductOption(
            id=sp["id"],
            name=sp["name"],
            category=sp["category"],
            price=sp["price"],
            availability=sp["availability"],
            stock_quantity=sp["stock_quantity"],
            relevance_score=sp.get("relevance_score", 0.0),
            reason=sp.get("reason"),
        )

    payment_intent_obj = None
    if final_state.get("payment_intent_response"):
        pir = final_state["payment_intent_response"]
        payment_intent_obj = PaymentIntentResponse.model_validate(pir)

    return BuyerChatResponse(
        response=final_state.get("final_response", ""),
        candidates=candidate_objs,
        selected_product=selected_obj,
        order_created=final_state.get("order_response"),
        payment_intent=payment_intent_obj,
        execution_steps=final_state.get("execution_steps", []),
        provider_used=final_state.get("used_llm_provider", "Gemini / Groq"),
        is_fallback_mode=final_state.get("is_fallback_mode", False),
    )


@router.post(
    "/simulate-order",
    response_model=BuyerSimulationResponse,
    summary="Simulate Direct AI Buyer Checkout with Payment Intent",
    description="Execute an end-to-end automated product order and propose a Razorpay Test Mode payment intent.",
)
def simulate_buyer_order_endpoint(
    req: BuyerSimulationRequest,
    db: Session = Depends(get_db),
):
    """Direct simulated order placement and payment proposal."""
    client = AICommerceClient(db_session=db)

    try:
        # 1. Fetch live product info
        prod = client.get_product(req.product_id)

        # 2. Check stock
        if prod["stock_quantity"] < req.quantity:
            return BuyerSimulationResponse(
                success=False,
                error_message=f"Insufficient stock for '{prod['name']}'. Requested {req.quantity}, available: {prod['stock_quantity']}.",
                explainability=f"Order rejected because available inventory ({prod['stock_quantity']}) is lower than requested quantity ({req.quantity}). Zero payments attempted.",
            )

        # 3. Create Order
        order_data = client.create_order(
            merchant_id=req.merchant_id,
            items=[{"product_id": req.product_id, "quantity": req.quantity}],
            idempotency_key=req.idempotency_key,
        )

        # 4. Propose Payment Intent
        intent_resp = PaymentService.propose_payment(
            db=db,
            order_id=order_data["order_id"],
            merchant_id=req.merchant_id,
            idempotency_key=f"sim-pay-{order_data['order_id']}",
        )

        explainability = (
            f"AI Buyer successfully placed order #{order_data['order_id']} for {req.quantity}x '{prod['name']}' "
            f"at ₹{order_data['total_amount']:,.2f}. Payment Intent #{intent_resp.id} proposed "
            f"(Risk: {intent_resp.risk_level}, Status: {intent_resp.status}). {intent_resp.explainability}"
        )

        return BuyerSimulationResponse(
            success=True,
            order=order_data,
            payment_intent=intent_resp,
            explainability=explainability,
            payment_note="Razorpay Test Mode Payment Intent created. Awaiting human/merchant approval.",
        )
    except HTTPException as he:
        return BuyerSimulationResponse(
            success=False,
            error_message=he.detail,
            explainability=f"API error: {he.detail}. No payment attempted.",
        )
    except Exception as e:
        return BuyerSimulationResponse(
            success=False,
            error_message=str(e),
            explainability=f"Order failed with exception: {str(e)}. No payment attempted.",
        )
