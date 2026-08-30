"""Tests for deterministic database analytics tools."""
from datetime import datetime, timezone
from app.agent.tools import (
    find_slow_moving_products,
    get_merchant_context,
    get_product_co_purchases,
    get_product_sales,
    get_products,
    get_sales_summary,
)
from app.db.models import Customer, Merchant, Order, OrderItem, OrderStatus, Product


def _seed_test_data(db_session):
    # Merchant
    m = Merchant(name="Test Sports Store", email="tools@sports.com", currency="INR")
    db_session.add(m)
    db_session.flush()

    # Customer
    c = Customer(name="Ajay", email="ajay@test.com")
    db_session.add(c)
    db_session.flush()

    # Products
    p1 = Product(merchant_id=m.id, name="Shoes", category="Footwear", price=2000.0, stock_quantity=20, sku="SKU-1")
    p2 = Product(merchant_id=m.id, name="Socks", category="Accessories", price=200.0, stock_quantity=50, sku="SKU-2")
    p3 = Product(merchant_id=m.id, name="Heavy Weight Bag", category="Gear", price=1500.0, stock_quantity=30, sku="SKU-3")
    db_session.add_all([p1, p2, p3])
    db_session.flush()

    # Multi-item order (p1 + p2)
    o1 = Order(merchant_id=m.id, customer_id=c.id, status=OrderStatus.CONFIRMED, total_amount=2200.0, currency="INR")
    db_session.add(o1)
    db_session.flush()
    db_session.add_all([
        OrderItem(order_id=o1.id, product_id=p1.id, quantity=1, unit_price=2000.0, subtotal=2000.0),
        OrderItem(order_id=o1.id, product_id=p2.id, quantity=1, unit_price=200.0, subtotal=200.0),
    ])

    # Second multi-item order (p1 + p2)
    o2 = Order(merchant_id=m.id, customer_id=c.id, status=OrderStatus.CONFIRMED, total_amount=2400.0, currency="INR")
    db_session.add(o2)
    db_session.flush()
    db_session.add_all([
        OrderItem(order_id=o2.id, product_id=p1.id, quantity=1, unit_price=2000.0, subtotal=2000.0),
        OrderItem(order_id=o2.id, product_id=p2.id, quantity=2, unit_price=200.0, subtotal=400.0),
    ])

    db_session.commit()
    return m.id, [p1.id, p2.id, p3.id]


def test_get_merchant_context(db_session):
    m_id, _ = _seed_test_data(db_session)
    ctx = get_merchant_context(db_session, m_id)
    assert ctx is not None
    assert ctx["name"] == "Test Sports Store"
    assert ctx["total_catalog_products"] == 3
    assert ctx["total_store_orders"] == 2


def test_get_products(db_session):
    m_id, _ = _seed_test_data(db_session)
    prods = get_products(db_session, m_id)
    assert len(prods) == 3
    assert any(p["sku"] == "SKU-1" for p in prods)


def test_get_sales_summary(db_session):
    m_id, _ = _seed_test_data(db_session)
    summary = get_sales_summary(db_session, m_id)
    assert summary["total_orders"] == 2
    assert summary["total_revenue"] == 4600.0
    assert summary["average_order_value"] == 2300.0


def test_get_product_sales(db_session):
    m_id, _ = _seed_test_data(db_session)
    sales = get_product_sales(db_session, m_id)
    assert len(sales) == 3
    # p1 revenue: 2000 + 2000 = 4000
    shoes_sales = next(s for s in sales if s["product_name"] == "Shoes")
    assert shoes_sales["revenue_generated"] == 4000.0
    assert shoes_sales["units_sold"] == 2


def test_get_product_co_purchases(db_session):
    m_id, _ = _seed_test_data(db_session)
    co_purchases = get_product_co_purchases(db_session, m_id)
    assert len(co_purchases) >= 1
    pair = co_purchases[0]
    assert pair["co_purchase_orders"] == 2
    names = {pair["product_a_name"], pair["product_b_name"]}
    assert names == {"Shoes", "Socks"}


def test_find_slow_moving_products(db_session):
    m_id, _ = _seed_test_data(db_session)
    # p3 (Heavy Weight Bag) has 30 in stock and 0 orders
    slow = find_slow_moving_products(db_session, m_id)
    assert len(slow) >= 1
    assert any(s["product_name"] == "Heavy Weight Bag" for s in slow)
