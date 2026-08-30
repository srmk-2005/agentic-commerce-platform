"""Typed state definition for the LangGraph Merchant Agent."""
from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    merchant_id: int
    user_request: str
    merchant_context: Optional[Dict[str, Any]]
    sales_summary: Optional[Dict[str, Any]]
    products: List[Dict[str, Any]]
    co_purchases: List[Dict[str, Any]]
    slow_moving: List[Dict[str, Any]]
    raw_opportunities: List[Dict[str, Any]]
    validated_opportunities: List[Dict[str, Any]]
    current_node: str
    error: Optional[str]
    final_response: Optional[str]
    used_llm_provider: str
    is_fallback_mode: bool
