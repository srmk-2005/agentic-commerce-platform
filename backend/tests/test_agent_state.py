"""Tests for LangGraph AgentState structure and transitions."""
from app.agent.state import AgentState


def test_agent_state_initialization():
    state: AgentState = {
        "merchant_id": 1,
        "user_request": "Increase my store revenue",
    }
    assert state["merchant_id"] == 1
    assert state["user_request"] == "Increase my store revenue"
    assert "error" not in state


def test_agent_state_with_opportunities():
    state: AgentState = {
        "merchant_id": 1,
        "validated_opportunities": [
            {
                "id": "opp-cross-1",
                "type": "CROSS_SELL",
                "title": "Cross-Sell Socks",
                "primary_product_id": 1,
                "confidence": 0.85,
            }
        ],
        "used_llm_provider": "Google Gemini (gemini-1.5-flash)",
        "is_fallback_mode": False,
    }
    assert len(state["validated_opportunities"]) == 1
    assert state["is_fallback_mode"] is False
    assert "Gemini" in state["used_llm_provider"]
