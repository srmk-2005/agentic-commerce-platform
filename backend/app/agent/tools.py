"""Deterministic Database Analytics and Action Proposal Tools for LangGraph Agent."""
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import Customer, Merchant, Order, OrderItem, OrderStatus, Product
from app.schemas.growth import ActionProposal, ActionProposalCreate
from app.services.growth_service import GrowthService
from app.services.safety_service import SafetyService


def get_merchant_context(db: Session, merchant_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve ground-truth merchant profile and active store metrics."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        return None

    total_products = db.query(Product).filter(Product.merchant_id == merchant_id).count()
    total_orders = db.query(Order).filter(Order.merchant_id == merchant_id).count()

    return {
        "id": merchant.id,
        "name": merchant.name,
        "email": merchant.email,
        "currency": merchant.currency,
        "is_active": merchant.is_active,
        "total_catalog_products": total_products,
        "total_store_orders": total_orders,
    }


def get_products(db: Session, merchant_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
    """Retrieve full merchant catalog products."""
    query = db.query(Product).filter(Product.merchant_id == merchant_id)
    if active_only:
        query = query.filter(Product.is_active.is_(True))

    products = query.all()
    return [
        {
            "id": p.id,
            "merchant_id": p.merchant_id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            "currency": p.currency,
            "stock_quantity": p.stock_quantity,
            "sku": p.sku,
            "is_active": p.is_active,
            "description": p.description or "",
        }
        for p in products
    ]


def get_sales_summary(db: Session, merchant_id: int) -> Dict[str, Any]:
    """Calculate deterministic revenue summary."""
    orders = (
        db.query(Order)
        .filter(Order.merchant_id == merchant_id)
        .filter(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PENDING]))
        .all()
    )

    total_orders = len(orders)
    total_revenue = sum(o.total_amount for o in orders)
    aov = (total_revenue / total_orders) if total_orders > 0 else 0.0

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(aov, 2),
    }


def get_product_sales(db: Session, merchant_id: int) -> List[Dict[str, Any]]:
    """Calculate sales quantity and gross revenue per product."""
    results = (
        db.query(
            Product.id,
            Product.name,
            Product.category,
            Product.price,
            Product.stock_quantity,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
            func.coalesce(func.sum(OrderItem.subtotal), 0.0).label("revenue_generated"),
            func.count(func.distinct(Order.id)).label("orders_count"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id, isouter=True)
        .join(Order, OrderItem.order_id == Order.id, isouter=True)
        .filter(Product.merchant_id == merchant_id)
        .filter((Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PENDING])) | (Order.id.is_(None)))
        .group_by(Product.id)
        .all()
    )

    return [
        {
            "product_id": r[0],
            "product_name": r[1],
            "category": r[2],
            "price": float(r[3]),
            "stock_quantity": r[4],
            "units_sold": int(r[5]),
            "revenue_generated": round(float(r[6]), 2),
            "orders_count": int(r[7]),
        }
        for r in results
    ]


def get_product_co_purchases(db: Session, merchant_id: int) -> List[Dict[str, Any]]:
    """Analyze co-purchases from multi-item order history."""
    orders = (
        db.query(Order)
        .filter(Order.merchant_id == merchant_id)
        .filter(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PENDING]))
        .all()
    )

    co_counts: Dict[tuple, int] = {}
    item_order_counts: Dict[int, int] = {}

    for order in orders:
        product_ids = sorted(list(set(item.product_id for item in order.items)))
        for pid in product_ids:
            item_order_counts[pid] = item_order_counts.get(pid, 0) + 1

        for i in range(len(product_ids)):
            for j in range(i + 1, len(product_ids)):
                pair = (product_ids[i], product_ids[j])
                co_counts[pair] = co_counts.get(pair, 0) + 1

    prods = {p.id: p for p in db.query(Product).filter(Product.merchant_id == merchant_id).all()}

    co_purchases = []
    for (p1_id, p2_id), count in co_counts.items():
        if p1_id in prods and p2_id in prods:
            p1 = prods[p1_id]
            p2 = prods[p2_id]
            a_orders = item_order_counts.get(p1_id, 1)
            b_orders = item_order_counts.get(p2_id, 1)
            base_orders = max(a_orders, b_orders)
            affinity_score = round(count / base_orders, 2)
            affinity_rate = round(affinity_score * 100, 1)

            co_purchases.append({
                "product_a_id": p1.id,
                "product_a_name": p1.name,
                "product_a_price": float(p1.price),
                "product_a_orders": a_orders,
                "product_b_id": p2.id,
                "product_b_name": p2.name,
                "product_b_price": float(p2.price),
                "product_b_orders": b_orders,
                "co_purchase_orders": count,
                "affinity_score": affinity_score,
                "affinity_rate": affinity_rate,
            })

    co_purchases.sort(key=lambda x: (x["co_purchase_orders"], x["affinity_score"]), reverse=True)
    return co_purchases


def find_slow_moving_products(db: Session, merchant_id: int) -> List[Dict[str, Any]]:
    """Identify products with high stock but low sales velocity."""
    sales_data = get_product_sales(db, merchant_id)
    slow_moving = []

    for item in sales_data:
        if item["stock_quantity"] >= 20 and item["orders_count"] <= 2:
            unliquidated_capital = round(item["stock_quantity"] * item["price"], 2)
            slow_moving.append({
                **item,
                "unliquidated_capital": unliquidated_capital,
                "capital_tied_up": unliquidated_capital,
                "turnover_status": "SLOW_MOVING",
            })

    slow_moving.sort(key=lambda x: x["unliquidated_capital"], reverse=True)
    return slow_moving


# --- Phase 3 Agent Growth Action Tools ---

def create_action_proposal_tool(
    db: Session,
    merchant_id: int,
    proposal_in: ActionProposalCreate,
) -> ActionProposal:
    """Tool for the agent to submit a structured growth proposal."""
    return GrowthService.propose_action(db, proposal_in)


def validate_action_tool(
    db: Session,
    proposal_in: ActionProposalCreate,
):
    """Tool for pre-validating a proposal without saving."""
    return SafetyService.validate_action_proposal(db, proposal_in)
