"""Tests to strictly verify Agent Safety Boundaries."""
import inspect
from app.agent import tools
from app.agent.graph import create_merchant_agent_graph
from app.db.models import Customer, Merchant, Order, OrderItem, OrderStatus, Product


def test_agent_tools_have_no_financial_or_mutation_methods():
    """Verify that tools module exposes only read-only analytical functions."""
    forbidden_terms = [
        "payment",
        "charge",
        "refund",
        "capture",
        "modify_price",
        "change_price",
        "delete",
        "update_price",
        "execute_campaign",
        "transfer_money",
    ]

    all_functions = inspect.getmembers(tools, inspect.isfunction)
    for name, func in all_functions:
        for term in forbidden_terms:
            assert term not in name.lower(), f"Forbidden mutation tool found: {name}"


def test_opportunities_always_require_merchant_approval(db_session):
    """Verify that all opportunities produced have requires_merchant_approval = True."""
    m = Merchant(name="Safety Store", email="safe@store.com", currency="INR")
    db_session.add(m)
    db_session.flush()

    p = Product(merchant_id=m.id, name="Test Item", category="Cat", price=100.0, stock_quantity=10, sku="SAFE-01")
    db_session.add(p)
    db_session.commit()

    graph = create_merchant_agent_graph(db_session)
    result = graph.invoke({"merchant_id": m.id, "user_request": "Opportunities"})

    opps = result.get("validated_opportunities", [])
    for opp in opps:
        assert opp["requires_merchant_approval"] is True, "Opportunity must require merchant approval"
