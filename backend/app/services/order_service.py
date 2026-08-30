"""Business logic service for Order and OrderItem entities."""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.db.models import Customer, Merchant, Order, OrderItem, OrderStatus, Product
from app.schemas.order import OrderCreate, OrderStatusUpdate


class InsufficientStockError(Exception):
    """Raised when ordered quantity exceeds available inventory stock."""
    pass


class InvalidProductError(Exception):
    """Raised when product does not exist or does not belong to merchant."""
    pass


class EntityNotFoundError(Exception):
    """Raised when merchant or customer cannot be found."""
    pass


class OrderService:
    @staticmethod
    def create_order(db: Session, order_in: OrderCreate) -> Order:
        """
        Create a validated order with server-computed line-item pricing and totals.
        
        Validations:
        1. Verify merchant exists.
        2. Verify customer exists.
        3. Verify all products exist.
        4. Verify all products belong to merchant_id.
        5. Verify requested_quantity <= stock_quantity for all items.
        6. Compute unit_price, subtotal, and total_amount securely on server.
        """
        # 1. Verify merchant exists
        merchant = db.query(Merchant).filter(Merchant.id == order_in.merchant_id).first()
        if not merchant:
            raise EntityNotFoundError(f"Merchant with id {order_in.merchant_id} not found.")

        # 2. Verify customer exists
        customer = db.query(Customer).filter(Customer.id == order_in.customer_id).first()
        if not customer:
            raise EntityNotFoundError(f"Customer with id {order_in.customer_id} not found.")

        # 3, 4, 5. Validate products, merchant ownership, and inventory stock
        calculated_items = []
        total_amount = 0.0

        for item_in in order_in.items:
            product = db.query(Product).filter(Product.id == item_in.product_id).first()
            if not product:
                raise InvalidProductError(f"Product with id {item_in.product_id} not found.")

            if product.merchant_id != order_in.merchant_id:
                raise InvalidProductError(
                    f"Product '{product.name}' (id: {product.id}) does not belong to merchant id {order_in.merchant_id}."
                )

            if not product.is_active:
                raise InvalidProductError(f"Product '{product.name}' is currently inactive.")

            if item_in.quantity > product.stock_quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for product '{product.name}' (SKU: {product.sku}). "
                    f"Requested: {item_in.quantity}, Available: {product.stock_quantity}."
                )

            # Server-side pricing computation
            unit_price = float(product.price)
            subtotal = round(unit_price * item_in.quantity, 2)
            total_amount += subtotal

            calculated_items.append({
                "product_id": product.id,
                "quantity": item_in.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            })

        total_amount = round(total_amount, 2)

        # Create Order record
        order = Order(
            merchant_id=order_in.merchant_id,
            customer_id=order_in.customer_id,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
            currency=merchant.currency,
        )
        db.add(order)
        db.flush()  # Assigns order.id

        # Create OrderItem records
        for item_data in calculated_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                subtotal=item_data["subtotal"],
            )
            db.add(order_item)

        db.commit()
        db.refresh(order)

        # Load relationships for response schema
        return (
            db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.customer),
                joinedload(Order.merchant),
            )
            .filter(Order.id == order.id)
            .first()
        )

    @staticmethod
    def get_order(db: Session, order_id: int) -> Optional[Order]:
        """Fetch single order by ID with loaded relationships."""
        return (
            db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.customer),
                joinedload(Order.merchant),
            )
            .filter(Order.id == order_id)
            .first()
        )

    @staticmethod
    def get_orders(
        db: Session,
        merchant_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Fetch orders with filtering and pagination."""
        query = db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.product),
            joinedload(Order.customer),
            joinedload(Order.merchant),
        )

        if merchant_id is not None:
            query = query.filter(Order.merchant_id == merchant_id)

        if customer_id is not None:
            query = query.filter(Order.customer_id == customer_id)

        if status is not None:
            query = query.filter(Order.status == status)

        return query.order_by(Order.id.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_order_status(
        db: Session, order_id: int, status_in: OrderStatusUpdate
    ) -> Optional[Order]:
        """Update status of existing order."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None

        order.status = status_in.status
        db.commit()
        db.refresh(order)
        return OrderService.get_order(db, order_id)
