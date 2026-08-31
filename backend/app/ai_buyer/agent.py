"""LangGraph State Machine for Simulated AI Buyer Agent (Connected to Multi-Provider LLM Engine)."""
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from app.agent.llm import llm_manager
from app.ai_buyer.state import BuyerState
from app.ai_buyer.tools import AICommerceClient
from app.payments.payment_service import PaymentService

logger = logging.getLogger(__name__)

BUYER_AGENT_SYSTEM_PROMPT = """You are an autonomous, intelligent AI Buyer Agent acting on behalf of a consumer in an AI-to-Merchant commerce platform.
Your job is to discover merchant products, evaluate catalog suitability, select items based on real-time inventory and pricing ground truth, and prepare orders safely under human-in-the-loop governance.
Always be helpful, transparent about pricing and inventory, and explain why specific products were selected."""


def parse_buyer_intent_deterministic(text: str) -> Dict[str, Any]:
    """Deterministic fallback parsing for natural-language buyer request."""
    text_lower = text.lower()
    constraints: Dict[str, Any] = {
        "search_query": text.strip(),
        "category": None,
        "max_price": None,
        "min_price": None,
        "is_purchase_intent": False,
        "target_product_name": None,
        "quantity": 1,
    }

    # Detect purchase/order intent
    if any(w in text_lower for w in ["buy", "order", "purchase", "checkout", "get me", "place order", "pay", "i want"]):
        constraints["is_purchase_intent"] = True

    # Extract price constraints (e.g. "under ₹3000", "< 3000", "below 2500", "under 1000")
    price_match = re.search(r"(?:under|below|less than|within|<=|<|₹|rs\.?)\s*₹?\s*(\d+)", text_lower)
    if price_match:
        try:
            constraints["max_price"] = float(price_match.group(1))
        except ValueError:
            pass

    # Extract search query focus
    if "shoe" in text_lower or "footwear" in text_lower or "running shoes" in text_lower:
        constraints["search_query"] = "running shoes"
    elif "sock" in text_lower:
        constraints["search_query"] = "running socks"
    elif "shirt" in text_lower or "apparel" in text_lower or "t-shirt" in text_lower:
        constraints["search_query"] = "sports t-shirt"
    elif "bag" in text_lower:
        constraints["search_query"] = "sports bag"
    elif "bottle" in text_lower or "shaker" in text_lower or "water" in text_lower:
        constraints["search_query"] = "water bottle"

    # Specific category filters if explicit
    if "footwear" in text_lower:
        constraints["category"] = "Footwear"
    elif "apparel" in text_lower:
        constraints["category"] = "Apparel"
    elif "accessories" in text_lower or "accessory" in text_lower:
        constraints["category"] = "Accessories"
    elif "equipment" in text_lower:
        constraints["category"] = "Equipment"

    # Specific product targets
    if "premium running shoes" in text_lower:
        constraints["target_product_name"] = "Premium Running Shoes"
    elif "running shoes" in text_lower:
        constraints["target_product_name"] = "Running Shoes"
    elif "running socks" in text_lower:
        constraints["target_product_name"] = "Running Socks"
    elif "sports bag" in text_lower:
        constraints["target_product_name"] = "Sports Bag"
    elif "sports t-shirt" in text_lower:
        constraints["target_product_name"] = "Sports T-Shirt"

    return constraints


def extract_intent_with_llm(text: str) -> Dict[str, Any]:
    """Extract structured buyer constraints using LLM with deterministic fallback."""
    fallback_result = parse_buyer_intent_deterministic(text)

    prompt = f"""Extract the search criteria from this consumer request into a JSON object:
Consumer Request: "{text}"

Respond ONLY with valid JSON (no markdown formatting, no code blocks):
{{
  "search_query": "short product keywords (e.g. running shoes, t-shirt, water bottle)",
  "category": "Footwear" or "Apparel" or "Accessories" or "Equipment" or null,
  "max_price": number or null,
  "min_price": number or null,
  "is_purchase_intent": boolean,
  "target_product_name": string or null,
  "quantity": integer
}}"""

    def fallback_fn():
        return json.dumps(fallback_result)

    try:
        raw_resp, provider, is_fallback = llm_manager.invoke_with_fallback(
            prompt=prompt,
            system_prompt="You are a precise JSON intent extraction assistant. Always output valid JSON only.",
            fallback_generator=fallback_fn,
        )

        # Clean JSON markdown fences if present
        clean_json = raw_resp.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\n|\n```$", "", clean_json, flags=re.MULTILINE).strip()

        parsed = json.loads(clean_json)
        # Validate extracted fields
        return {
            "search_query": parsed.get("search_query") or fallback_result["search_query"],
            "category": parsed.get("category") or fallback_result["category"],
            "max_price": float(parsed["max_price"]) if parsed.get("max_price") is not None else fallback_result["max_price"],
            "min_price": float(parsed["min_price"]) if parsed.get("min_price") is not None else fallback_result["min_price"],
            "is_purchase_intent": bool(parsed.get("is_purchase_intent", fallback_result["is_purchase_intent"])),
            "target_product_name": parsed.get("target_product_name") or fallback_result["target_product_name"],
            "quantity": int(parsed.get("quantity", 1)),
            "provider_used": provider,
            "is_fallback": is_fallback,
        }
    except Exception as e:
        logger.warning(f"LLM intent extraction failed, using deterministic fallback: {e}")
        return fallback_result


def create_buyer_agent_graph(client: AICommerceClient):
    """Build and compile the LangGraph workflow for the simulated AI buyer."""

    def understand_intent_node(state: BuyerState) -> Dict[str, Any]:
        req = state.get("buyer_request", "")
        parsed = extract_intent_with_llm(req)
        steps = list(state.get("execution_steps", []))
        provider_tag = parsed.get("provider_used", "Deterministic Engine")
        steps.append(
            f"Parsed buyer intent via {provider_tag}: query='{parsed['search_query']}', "
            f"max_price={parsed.get('max_price')}, is_purchase={parsed.get('is_purchase_intent', False)}"
        )

        return {
            "search_query": parsed["search_query"],
            "category": parsed.get("category"),
            "max_price": parsed.get("max_price"),
            "min_price": parsed.get("min_price"),
            "selected_quantity": parsed.get("quantity", 1),
            "is_purchase_intent": parsed.get("is_purchase_intent", False),
            "execution_steps": steps,
            "used_llm_provider": parsed.get("provider_used"),
            "is_fallback_mode": parsed.get("is_fallback", False),
            "errors": [],
        }

    def discover_capabilities_node(state: BuyerState) -> Dict[str, Any]:
        merchant_id = state.get("merchant_id", 1)
        steps = list(state.get("execution_steps", []))

        try:
            manifest = client.discover_merchant(merchant_id)
            steps.append(f"Discovered merchant '{manifest.get('name')}' capabilities: ordering=True, payments=True (Razorpay Test Mode)")
            return {
                "merchant_capabilities": manifest.get("capabilities", {}),
                "execution_steps": steps,
            }
        except Exception as e:
            steps.append(f"Capability discovery failed: {str(e)}")
            return {
                "errors": [f"Could not discover merchant #{merchant_id}: {str(e)}"],
                "execution_steps": steps,
            }

    def search_catalog_node(state: BuyerState) -> Dict[str, Any]:
        if state.get("errors"):
            return {}

        merchant_id = state.get("merchant_id", 1)
        query = state.get("search_query", "")
        category = state.get("category")
        max_price = state.get("max_price")
        min_price = state.get("min_price")
        steps = list(state.get("execution_steps", []))

        try:
            raw_results = client.search_products(
                query=query,
                merchant_id=merchant_id,
                category=category,
                max_price=max_price,
                min_price=min_price,
            )

            # If strict category filter produced 0 matches, retry without category
            if not raw_results and category:
                raw_results = client.search_products(
                    query=query,
                    merchant_id=merchant_id,
                    category=None,
                    max_price=max_price,
                    min_price=min_price,
                )

            candidates = []
            for r in raw_results:
                prod = r.get("product", {})
                candidates.append({
                    "id": prod.get("id"),
                    "name": prod.get("name"),
                    "category": prod.get("category"),
                    "price": prod.get("price"),
                    "availability": prod.get("availability"),
                    "stock_quantity": prod.get("stock_quantity"),
                    "relevance_score": r.get("relevance_score", 0.0),
                    "reason": " • ".join(r.get("match_reasons", [])),
                })

            steps.append(f"Queried AI Catalog: Found {len(candidates)} candidate products")
            return {
                "candidate_products": candidates,
                "execution_steps": steps,
            }
        except Exception as e:
            return {
                "errors": [f"Catalog search error: {str(e)}"],
                "execution_steps": steps,
            }

    def evaluate_and_select_node(state: BuyerState) -> Dict[str, Any]:
        if state.get("errors"):
            return {}

        candidates = state.get("candidate_products", [])
        steps = list(state.get("execution_steps", []))

        if not candidates:
            steps.append("No candidate products matched criteria.")
            return {
                "selection_reasoning": "No products matched the given price and search constraints.",
                "execution_steps": steps,
            }

        # Select highest-scoring in-stock candidate
        in_stock_candidates = [c for c in candidates if c["stock_quantity"] > 0]
        selected = in_stock_candidates[0] if in_stock_candidates else candidates[0]

        reasoning = (
            f"Selected '{selected['name']}' because:\n"
            f"✓ Matches query '{state.get('search_query')}'\n"
            f"✓ Listed price ₹{selected['price']:,.2f} is compatible\n"
            f"✓ Availability: {selected['availability']} ({selected['stock_quantity']} units in stock)\n"
            f"✓ Factual relevance score: {selected['relevance_score']}"
        )

        steps.append(f"Selected candidate: '{selected['name']}' (₹{selected['price']:,.2f})")

        return {
            "selected_product": selected,
            "availability": selected["availability"],
            "selection_reasoning": reasoning,
            "execution_steps": steps,
        }

    def verify_availability_node(state: BuyerState) -> Dict[str, Any]:
        selected = state.get("selected_product")
        if not selected or state.get("errors"):
            return {}

        steps = list(state.get("execution_steps", []))
        try:
            live_prod = client.get_product(selected["id"])
            steps.append(f"Verified live ground-truth stock for '{live_prod['name']}': {live_prod['stock_quantity']} units ({live_prod['availability']})")

            if live_prod["stock_quantity"] <= 0 or live_prod["availability"] == "OUT_OF_STOCK":
                steps.append(f"CRITICAL: Product '{live_prod['name']}' is OUT OF STOCK. Order aborted safely.")
                return {
                    "errors": [f"Product '{live_prod['name']}' is no longer available in stock."],
                    "availability": "OUT_OF_STOCK",
                    "execution_steps": steps,
                }

            return {
                "availability": live_prod["availability"],
                "execution_steps": steps,
            }
        except Exception as e:
            return {
                "errors": [f"Failed to verify live inventory: {str(e)}"],
                "execution_steps": steps,
            }

    def create_order_node(state: BuyerState) -> Dict[str, Any]:
        req_lower = state.get("buyer_request", "").lower()
        is_purchase = state.get("is_purchase_intent") or any(
            w in req_lower for w in ["buy", "order", "purchase", "checkout", "get me", "place order", "pay", "i want"]
        )

        if not is_purchase or state.get("errors") or not state.get("selected_product"):
            return {}

        merchant_id = state.get("merchant_id", 1)
        selected = state.get("selected_product")
        qty = state.get("selected_quantity", 1)
        idempotency_key = f"buyer-order-{uuid.uuid4().hex[:12]}"
        steps = list(state.get("execution_steps", []))

        try:
            order_data = client.create_order(
                merchant_id=merchant_id,
                items=[{"product_id": selected["id"], "quantity": qty}],
                idempotency_key=idempotency_key,
            )
            steps.append(f"Order created successfully: #{order_data['order_id']} for ₹{order_data['total_amount']:,.2f}")
            return {
                "order_id": order_data["order_id"],
                "order_response": order_data,
                "execution_steps": steps,
            }
        except Exception as e:
            steps.append(f"Order creation rejected by backend: {str(e)}")
            return {
                "errors": [f"Order creation failed: {str(e)}"],
                "execution_steps": steps,
            }

    def propose_payment_node(state: BuyerState) -> Dict[str, Any]:
        """Phase 5: Propose Payment Intent with Deterministic Policy Bounds & Gated Approval."""
        order_resp = state.get("order_response")
        if not order_resp or state.get("errors") or not client.db:
            return {}

        merchant_id = state.get("merchant_id", 1)
        order_id = order_resp["order_id"]
        steps = list(state.get("execution_steps", []))
        idempotency_key = f"buyer-pay-intent-{order_id}"

        try:
            intent_resp = PaymentService.propose_payment(
                db=client.db,
                order_id=order_id,
                merchant_id=merchant_id,
                idempotency_key=idempotency_key,
            )
            steps.append(
                f"Proposed Payment Intent #{intent_resp.id} for ₹{intent_resp.amount:,.2f} "
                f"(Risk: {intent_resp.risk_level}, Gated for User Approval)"
            )
            return {
                "payment_intent_id": intent_resp.id,
                "payment_amount": intent_resp.amount,
                "payment_currency": intent_resp.currency,
                "payment_risk": intent_resp.risk_level,
                "payment_intent_response": intent_resp.model_dump(),
                "payment_explainability": intent_resp.explainability,
                "execution_steps": steps,
            }
        except Exception as e:
            steps.append(f"Payment proposal failed policy check: {str(e)}")
            return {
                "errors": [f"Payment policy violation: {str(e)}"],
                "execution_steps": steps,
            }

    def format_buyer_response_node(state: BuyerState) -> Dict[str, Any]:
        req = state.get("buyer_request", "")
        errors = state.get("errors", [])
        order_resp = state.get("order_response")
        payment_intent = state.get("payment_intent_response")
        candidates = state.get("candidate_products", [])
        selected = state.get("selected_product")

        # Fallback generator for resilience
        def fallback_generator() -> str:
            if errors:
                return (
                    f"⚠️ **Could not complete order:**\n"
                    f"{errors[0]}\n\n"
                    f"*No payment was executed. Your account and merchant limits remain unaffected.*"
                )
            if order_resp and payment_intent:
                return (
                    f"✅ **Order Created & Payment Intent Proposed!**\n\n"
                    f"• **Order ID:** #{order_resp['order_id']}\n"
                    f"• **Product:** {selected.get('name') if selected else 'Selected item'}\n"
                    f"• **Total Amount:** ₹{order_resp['total_amount']:,.2f} {order_resp['currency']}\n"
                    f"• **Payment Intent:** #{payment_intent['id']} ({payment_intent['status']})\n"
                    f"• **Risk Level:** `{payment_intent['risk_level']}`\n\n"
                    f"**Permitted by Policy:**\n"
                    f"{state.get('payment_explainability', 'Transaction within single-purchase safety limit.')}\n\n"
                    f"👉 *Merchant approval is required before Razorpay Test Mode checkout executes.*"
                )
            if order_resp:
                return (
                    f"✅ **Order Created via AI Commerce Interface!**\n\n"
                    f"• **Order ID:** #{order_resp['order_id']}\n"
                    f"• **Total Amount:** ₹{order_resp['total_amount']:,.2f} {order_resp['currency']}\n"
                    f"• **Status:** {order_resp['status']}\n\n"
                    f"**Selection Rationale:**\n"
                    f"{state.get('selection_reasoning', '')}"
                )
            if candidates:
                lines = [f"I found **{len(candidates)}** matching product(s) in the merchant catalog:\n"]
                for idx, c in enumerate(candidates[:3], 1):
                    stock_label = f"✓ In Stock ({c['stock_quantity']} units)" if c['stock_quantity'] > 0 else "✗ Out of Stock"
                    lines.append(f"{idx}. **{c['name']}** — ₹{c['price']:,.2f} ({stock_label})")
                if selected:
                    lines.append(
                        f"\nWould you like me to prepare an order for **{selected['name']}** (₹{selected['price']:,.2f})?"
                    )
                return "\n".join(lines)
            return "I searched the merchant's catalog but could not find any products matching your criteria. Try expanding your price range or search terms."

        # Construct LLM prompt for dynamic, personalized response
        llm_prompt = f"""You are the External AI Buyer Agent communicating directly with the consumer who requested:
"{req}"

Here is the factual backend state:
- Products Found in Catalog: {json.dumps(candidates, default=str)}
- Selected Item: {json.dumps(selected, default=str) if selected else "None"}
- Order Status: {json.dumps(order_resp, default=str) if order_resp else "No order created"}
- Payment Proposal: {json.dumps(payment_intent, default=str) if payment_intent else "No payment intent"}
- Policy Explainability: {state.get('payment_explainability', '')}
- Errors Encountered: {json.dumps(errors)}

Instructions:
1. Write a natural, smart, and professional response in clean Markdown.
2. If an order was created & payment intent proposed: Confirm the Order ID, total price in INR, explain why this item was chosen for the buyer, and state clearly that the transaction is held in the merchant approval gate for safety before Razorpay checkout.
3. If only searching/browsing: Present the top matching options, compare their prices and stock availability, explain why they fit the user's intent, and offer to place the order.
4. If out of stock or error: Explain the issue politely and suggest alternative options from the catalog.
5. Avoid repetitive boilerplate."""

        try:
            response_text, provider_used, is_fallback = llm_manager.invoke_with_fallback(
                prompt=llm_prompt,
                system_prompt=BUYER_AGENT_SYSTEM_PROMPT,
                fallback_generator=fallback_generator,
            )
        except Exception as e:
            logger.warning(f"Buyer response generation failed with LLM, using fallback: {e}")
            response_text = fallback_generator()
            provider_used = "Deterministic Engine"
            is_fallback = True

        return {
            "final_response": response_text,
            "used_llm_provider": provider_used,
            "is_fallback_mode": is_fallback,
        }

    # Build LangGraph
    builder = StateGraph(BuyerState)
    builder.add_node("understand_intent", understand_intent_node)
    builder.add_node("discover_capabilities", discover_capabilities_node)
    builder.add_node("search_catalog", search_catalog_node)
    builder.add_node("evaluate_and_select", evaluate_and_select_node)
    builder.add_node("verify_availability", verify_availability_node)
    builder.add_node("create_order", create_order_node)
    builder.add_node("propose_payment", propose_payment_node)
    builder.add_node("format_buyer_response", format_buyer_response_node)

    builder.set_entry_point("understand_intent")
    builder.add_edge("understand_intent", "discover_capabilities")
    builder.add_edge("discover_capabilities", "search_catalog")
    builder.add_edge("search_catalog", "evaluate_and_select")
    builder.add_edge("evaluate_and_select", "verify_availability")
    builder.add_edge("verify_availability", "create_order")
    builder.add_edge("create_order", "propose_payment")
    builder.add_edge("propose_payment", "format_buyer_response")
    builder.add_edge("format_buyer_response", END)

    return builder.compile()
