"""LangGraph State Machine for Simulated AI Buyer Agent."""
import re
import uuid
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from app.ai_buyer.state import BuyerState
from app.ai_buyer.tools import AICommerceClient


def parse_buyer_intent(text: str) -> Dict[str, Any]:
    """Deterministically parse natural-language buyer request into structured constraints."""
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
    if any(w in text_lower for w in ["buy", "order", "purchase", "checkout", "get me", "place order"]):
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

    # Specific category filters if explicit
    if "footwear" in text_lower:
        constraints["category"] = "Footwear"
    elif "apparel" in text_lower:
        constraints["category"] = "Apparel"
    elif "accessories" in text_lower or "accessory" in text_lower:
        constraints["category"] = "Accessories"

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


def create_buyer_agent_graph(client: AICommerceClient):
    """Build and compile the LangGraph workflow for the simulated AI buyer."""

    def understand_intent_node(state: BuyerState) -> Dict[str, Any]:
        req = state.get("buyer_request", "")
        parsed = parse_buyer_intent(req)
        steps = list(state.get("execution_steps", []))
        steps.append(f"Parsed buyer intent: query='{parsed['search_query']}', max_price={parsed.get('max_price')}")

        return {
            "search_query": parsed["search_query"],
            "category": parsed["category"],
            "max_price": parsed["max_price"],
            "min_price": parsed["min_price"],
            "selected_quantity": parsed["quantity"],
            "execution_steps": steps,
            "errors": [],
        }

    def discover_capabilities_node(state: BuyerState) -> Dict[str, Any]:
        merchant_id = state.get("merchant_id", 1)
        steps = list(state.get("execution_steps", []))

        try:
            manifest = client.discover_merchant(merchant_id)
            steps.append(f"Discovered merchant '{manifest.get('name')}' capabilities: ordering=True, payments=False")
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
        req_lower = state.get("buyer_request", "").lower()
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
            f"✓ Listed price ₹{selected['price']} is compatible\n"
            f"✓ Availability: {selected['availability']} ({selected['stock_quantity']} units in stock)\n"
            f"✓ Factual relevance score: {selected['relevance_score']}"
        )

        steps.append(f"Selected candidate: '{selected['name']}' (₹{selected['price']})")

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
        # Only create order if user requested purchase/ordering and there are no errors
        req_lower = state.get("buyer_request", "").lower()
        is_purchase = any(w in req_lower for w in ["buy", "order", "purchase", "checkout", "get me", "place order"])

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
            steps.append(f"Order created successfully: #{order_data['order_id']} for ₹{order_data['total_amount']} (Payment: {order_data['payment_status']})")
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

    def format_buyer_response_node(state: BuyerState) -> Dict[str, Any]:
        errors = state.get("errors", [])
        order_resp = state.get("order_response")
        candidates = state.get("candidate_products", [])
        selected = state.get("selected_product")

        if errors:
            response_text = (
                f"⚠️ **Could not complete order:**\n"
                f"{errors[0]}\n\n"
                f"*No payment was attempted. Your account and merchant data remain unaffected.*"
            )
        elif order_resp:
            response_text = (
                f"✅ **Order Created via AI Commerce Interface!**\n\n"
                f"• **Order ID:** #{order_resp['order_id']}\n"
                f"• **Total Amount:** ₹{order_resp['total_amount']:,.2f} {order_resp['currency']}\n"
                f"• **Status:** {order_resp['status']}\n"
                f"• **Payment Status:** `{order_resp['payment_status']}` (Payment integration reserved for Phase 5)\n\n"
                f"**Explainability & Selection Rationale:**\n"
                f"{state.get('selection_reasoning', '')}"
            )
        elif candidates:
            lines = [f"I found **{len(candidates)}** matching product(s) in the merchant catalog:\n"]
            for idx, c in enumerate(candidates[:3], 1):
                stock_label = f"✓ In Stock ({c['stock_quantity']} units)" if c['stock_quantity'] > 0 else "✗ Out of Stock"
                lines.append(f"{idx}. **{c['name']}** — ₹{c['price']:,.2f} ({stock_label})")
            lines.append(
                f"\nWould you like me to prepare an order for **{selected['name']}** (₹{selected['price']:,.2f})?"
            )
            response_text = "\n".join(lines)
        else:
            response_text = "I searched the merchant's catalog but could not find any products matching your criteria. Try expanding your price range or search terms."

        return {"final_response": response_text}

    # Build LangGraph
    builder = StateGraph(BuyerState)
    builder.add_node("understand_intent", understand_intent_node)
    builder.add_node("discover_capabilities", discover_capabilities_node)
    builder.add_node("search_catalog", search_catalog_node)
    builder.add_node("evaluate_and_select", evaluate_and_select_node)
    builder.add_node("verify_availability", verify_availability_node)
    builder.add_node("create_order", create_order_node)
    builder.add_node("format_buyer_response", format_buyer_response_node)

    builder.set_entry_point("understand_intent")
    builder.add_edge("understand_intent", "discover_capabilities")
    builder.add_edge("discover_capabilities", "search_catalog")
    builder.add_edge("search_catalog", "evaluate_and_select")
    builder.add_edge("evaluate_and_select", "verify_availability")
    builder.add_edge("verify_availability", "create_order")
    builder.add_edge("create_order", "format_buyer_response")
    builder.add_edge("format_buyer_response", END)

    return builder.compile()
