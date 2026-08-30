"""Order API router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import OrderStatus
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order_service import (
    EntityNotFoundError,
    InsufficientStockError,
    InvalidProductError,
    OrderService,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order with server-verified products, inventory safety check,
    and server-side computed totals.
    """
    try:
        return OrderService.create_order(db, order_in)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except (InvalidProductError, InsufficientStockError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List orders with filters",
)
def list_orders(
    merchant_id: Optional[int] = Query(None, description="Filter orders by merchant ID"),
    customer_id: Optional[int] = Query(None, description="Filter orders by customer ID"),
    order_status: Optional[OrderStatus] = Query(None, alias="status", description="Filter by status (PENDING, CONFIRMED, CANCELLED, FAILED)"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit records per page"),
    db: Session = Depends(get_db),
):
    """Retrieve orders list with optional merchant/customer/status filtering."""
    return OrderService.get_orders(
        db,
        merchant_id=merchant_id,
        customer_id=customer_id,
        status=order_status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed order information including line items and products."""
    order = OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found.",
        )
    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
)
def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update lifecycle status of an order."""
    updated = OrderService.update_order_status(db, order_id, status_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found.",
        )
    return updated
