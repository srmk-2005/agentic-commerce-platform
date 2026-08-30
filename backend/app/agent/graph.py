"""LangGraph StateGraph definition for Merchant AI Growth Agent."""
from typing import Any, Dict
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session
from app.agent.nodes import (
    analyze_products_node,
    analyze_sales_node,
    explain_recommendations_node,
    generate_opportunities_node,
    load_merchant_context_node,
    validate_recommendations_node,
)
from app.agent.state import AgentState


def check_merchant_validity(state: AgentState) -> str:
    """Conditional routing edge: check if merchant was successfully loaded."""
    if state.get("error") or not state.get("merchant_context"):
        return "end"
    return "continue"


def create_merchant_agent_graph(db: Session):
    """
    Build and compile the LangGraph workflow for merchant revenue analysis.
    
    Graph Topology:
    [START]
       │
       ▼
    [load_context]
       │
       ├── (Invalid / Not Found) ────────► [END]
       │
       ▼ (Valid)
    [analyze_sales]
       │
       ▼
    [analyze_products]
       │
       ▼
    [generate_opportunities]
       │
       ▼
    [validate_recommendations]
       │
       ▼
    [explain_recommendations]
       │
       ▼
    [END]
    """
    workflow = StateGraph(AgentState)

    # Wrap nodes to pass the active database session
    workflow.add_node(
        "load_context",
        lambda state: load_merchant_context_node(state, db),
    )
    workflow.add_node(
        "analyze_sales",
        lambda state: analyze_sales_node(state, db),
    )
    workflow.add_node(
        "analyze_products",
        lambda state: analyze_products_node(state, db),
    )
    workflow.add_node(
        "generate_opportunities",
        generate_opportunities_node,
    )
    workflow.add_node(
        "validate_recommendations",
        lambda state: validate_recommendations_node(state, db),
    )
    workflow.add_node(
        "explain_recommendations",
        explain_recommendations_node,
    )

    # Set entry point
    workflow.set_entry_point("load_context")

    # Add conditional branching after loading merchant context
    workflow.add_conditional_edges(
        "load_context",
        check_merchant_validity,
        {
            "continue": "analyze_sales",
            "end": END,
        },
    )

    # Linear analysis and synthesis pipeline
    workflow.add_edge("analyze_sales", "analyze_products")
    workflow.add_edge("analyze_products", "generate_opportunities")
    workflow.add_edge("generate_opportunities", "validate_recommendations")
    workflow.add_edge("validate_recommendations", "explain_recommendations")
    workflow.add_edge("explain_recommendations", END)

    return workflow.compile()
