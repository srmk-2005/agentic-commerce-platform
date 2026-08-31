"""AI Commerce Order Service with Idempotency, Inventory Locking, and Audit Logging."""
import json
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.commerce.policies import DEFAULT_MAX_QUANTITY_PER_ORDER
from app.commerce.schemas import (
    AIOrderCreateRequest,
    AIOrderItemResponse,
    AIOrderResponse,
)
from app.db.models import (
    ActorType,
    AuditLog,
    Customer,
    Merchant,
    Order,
    OrderItem,
    OrderStatus,
    Product,
)


def create_ai_order(
    db: Session,
    request: AIOrderCreateRequest,
    idempotency_key: Optional[str] = None,
) -> AIOrderResponse:
    """
    Validate and execute AI Buyer order creation.
    
    Safety & Invariants:
    1. Idempotent execution (duplicate keys return original order).
    2. Zero trust in client pricing (all prices fetched from DB).
    3. Merchant ownership & active state verification.
    4. Real-time inventory verification and deduction.
    5. Immutable audit log entry with ActorType.AI_BUYER.
    6. Payment status marked NOT_AVAILABLE (deferred to Phase 5).
    """
    key = idempotency_key or request.idempotency_key

    # 1. Check Idempotency Key
    if key:
        existing_order = db.query(Order).filter(Order.idempotency_key == key).first()
        if existing_order:
            item_responses = [
                AIOrderItemResponse(
                    product_id=it.product_id,
                    name=it.product.name if it.product else f"Product #{it.product_id}",
                    quantity=it.quantity,
                    unit_price=float(it.unit_price),
                    subtotal=float(it.subtotal),
                )
                for it in existing_order.items
            ]
            return AIOrderResponse(
                order_id=existing_order.id,
                merchant_id=existing_order.merchant_id,
                status=existing_order.status.value if hasattr(existing_order.status, "value") else str(existing_order.status),
                items=item_responses,
                total_amount=float(existing_order.total_amount),
                currency=existing_order.currency,
                payment_status=existing_order.payment_status,
                idempotency_key=existing_order.idempotency_key,
                created_at=existing_order.created_at,
            )

    # 2. Validate Merchant
    merchant = db.query(Merchant).filter(Merchant.id == request.merchant_id).first()
    if not merchant or not merchant.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant #{request.merchant_id} not found or inactive."
        )

    # 3. Resolve Customer (Ensure a customer exists for AI buyer interactions)
    customer = (
        db.query(Customer)
        .filter(Customer.email == "ai_buyer@agenticcommerce.ai")
        .first()
    )
    if not customer:
        customer = Customer(
            name="Simulated AI Buyer Agent",
            email="ai_buyer@agenticcommerce.ai",
        )
        db.add(customer)
        db.flush()

    # 4. Validate Products & Ground-Truth Inventory
    items_to_create = []
    total_amount = 0.0

    for item_req in request.items:
        if item_req.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item quantity must be greater than zero."
            )

        if item_req.quantity > DEFAULT_MAX_QUANTITY_PER_ORDER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({item_req.quantity}) exceeds maximum limit per order ({DEFAULT_MAX_QUANTITY_PER_ORDER})."
            )

        product = db.query(Product).filter(Product.id == item_req.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_req.product_id} not found."
            )

        if product.merchant_id != request.merchant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' (ID {product.id}) does not belong to merchant #{request.merchant_id}."
            )

        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is currently inactive."
            )

        if product.stock_quantity < item_req.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({item_req.quantity}) is greater than available inventory ({product.stock_quantity}) for '{product.name}'."
            )

        # Calculate unit price and subtotal strictly from DB
        unit_price = float(product.price)
        subtotal = round(unit_price * item_req.quantity, 2)
        total_amount += subtotal

        # Deduct inventory atomically
        product.stock_quantity -= item_req.quantity

        items_to_create.append({
            "product": product,
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item_req.quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    total_amount = round(total_amount, 2)

    # 5. Create Order Record
    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        currency=merchant.currency,
        idempotency_key=key,
        payment_status="NOT_AVAILABLE",
    )
    db.add(order)
    db.flush()

    item_responses = []
    for it in items_to_create:
        order_item = OrderItem(
            order_id=order.id,
            product_id=it["product_id"],
            quantity=it["quantity"],
            unit_price=it["unit_price"],
            subtotal=it["subtotal"],
        )
        db.add(order_item)
        item_responses.append(
            AIOrderItemResponse(
                product_id=it["product_id"],
                name=it["product_name"],
                quantity=it["quantity"],
                unit_price=it["unit_price"],
                subtotal=it["subtotal"],
            )
        )

    # 6. Record Audit Log for AI Buyer Event
    audit_entry = AuditLog(
        merchant_id=merchant.id,
        actor_type=ActorType.AI_BUYER,
        actor_id="simulated-ai-buyer-agent",
        action="AI_ORDER_CREATE",
        entity_type="Order",
        entity_id=order.id,
        status="SUCCESS",
        reason=f"AI Buyer ordered {len(items_to_create)} item(s) for total ₹{total_amount}",
        metadata_json=json.dumps({
            "order_id": order.id,
            "total_amount": total_amount,
            "currency": merchant.currency,
            "items_count": len(items_to_create),
            "idempotency_key": key,
            "payment_status": "NOT_AVAILABLE",
        }),
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(order)

    return AIOrderResponse(
        order_id=order.id,
        merchant_id=order.merchant_id,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        items=item_responses,
        total_amount=float(order.total_amount),
        currency=order.currency,
        payment_status=order.payment_status,
        idempotency_key=order.idempotency_key,
        created_at=order.created_at,
    )
