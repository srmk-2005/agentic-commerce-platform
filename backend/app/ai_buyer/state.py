"""TypedDict state definition for LangGraph Simulated AI Buyer agent."""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class BuyerState(TypedDict, total=False):
    buyer_request: str
    merchant_id: int
    merchant_capabilities: Dict[str, Any]
    search_query: str
    category: Optional[str]
    max_price: Optional[float]
    min_price: Optional[float]
    candidate_products: List[Dict[str, Any]]
    selected_product: Optional[Dict[str, Any]]
    selected_quantity: int
    availability: Optional[str]
    order_id: Optional[int]
    order_response: Optional[Dict[str, Any]]
    errors: List[str]
    selection_reasoning: str
    execution_steps: List[str]
    final_response: str
