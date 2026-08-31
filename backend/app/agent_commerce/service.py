"""Merchant Commerce Agent: Orchestrates AI Buyer Interactions & Standard Protocol Actions."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.agent_commerce.discovery import get_merchant_contract
from app.agent_commerce.protocol import (
    ErrorCodes,
    create_error_response,
    create_success_response,
    validate_protocol_message,
)
from app.agent_commerce.schemas import (
    AgentMessage,
    AgentResponse,
    ProtocolAction,
)
from app.agent_commerce.session import session_manager
from app.commerce.catalog import get_canonical_product
from app.commerce.order_service import create_ai_order
from app.commerce.schemas import AIOrderCreateRequest, AIOrderItemCreate
from app.commerce.service import search_ai_products
from app.db.models import (
    ActorType,
    AgentCommerceSession,
    Merchant,
    Order,
    PaymentIntent,
    Product,
    SessionStatus,
)
from app.payments.payment_service import PaymentService as payment_service
from app.services.audit_service import audit_service


class MerchantCommerceAgent:
    """Standardized Merchant Commerce Agent for processing AI Buyer protocol messages."""

    def dispatch_message(self, db: Session, msg: AgentMessage) -> AgentResponse:
        """Validate, authorize, and dispatch incoming agent protocol message."""
        # 1. Protocol envelope validation
        validation_err = validate_protocol_message(msg)
        if validation_err:
            return validation_err

        # 2. Session verification
        session = session_manager.get_session(db, msg.session_id)
        if not session:
            return create_error_response(
                message_id=msg.message_id,
                session_id=msg.session_id,
                trace_id=msg.trace_id or "unknown",
                action=msg.action.value,
                code=ErrorCodes.INVALID_SESSION,
                message=f"Agent commerce session '{msg.session_id}' not found or invalid.",
            )

        if session.status == SessionStatus.EXPIRED:
            return create_error_response(
                message_id=msg.message_id,
                session_id=msg.session_id,
                trace_id=session.trace_id,
                action=msg.action.value,
                code=ErrorCodes.SESSION_EXPIRED,
                message="Session has expired. Please initiate a new commerce session.",
            )

        # 3. Authorization check
        trace_id = session.trace_id
        merchant_id = session.merchant_id

        # Route action
        if msg.action == ProtocolAction.DISCOVER:
            return self._handle_discover(db, session, msg, trace_id, merchant_id)
        elif msg.action == ProtocolAction.SEARCH:
            return self._handle_search(db, session, msg, trace_id, merchant_id)
        elif msg.action == ProtocolAction.GET_PRODUCT:
            return self._handle_get_product(db, session, msg, trace_id, merchant_id)
        elif msg.action == ProtocolAction.CHECK_INVENTORY:
            return self._handle_check_inventory(db, session, msg, trace_id, merchant_id)
        elif msg.action == ProtocolAction.CREATE_ORDER:
            return self._handle_create_order(db, session, msg, trace_id, merchant_id)
        elif msg.action == ProtocolAction.PROPOSE_PAYMENT:
            return self._handle_propose_payment(db, session, msg, trace_id, merchant_id)
        elif msg.action == ProtocolAction.GET_PAYMENT_STATUS:
            return self._handle_get_payment_status(db, session, msg, trace_id, merchant_id)
        else:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=str(msg.action),
                code=ErrorCodes.CAPABILITY_NOT_SUPPORTED,
                message=f"Action '{msg.action}' is not handled by Merchant Commerce Agent.",
            )

    # --- Action Handlers ---

    def _handle_discover(
        self,
        db: Session,
        session: AgentCommerceSession,
        msg: AgentMessage,
        trace_id: str,
        merchant_id: int,
    ) -> AgentResponse:
        contract = get_merchant_contract(db, merchant_id)
        if not contract:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.MERCHANT_NOT_FOUND,
                message=f"Merchant with ID {merchant_id} not found.",
            )

        session_manager.record_timeline_event(
            db=db,
            session=session,
            action="AGENT_MERCHANT_DISCOVERED",
            actor=msg.sender.id,
            status="SUCCESS",
            details={"merchant_name": contract.merchant_name, "capabilities": contract.capabilities},
        )

        audit_service.log_agent_action(
            db=db,
            merchant_id=merchant_id,
            action="AGENT_MERCHANT_DISCOVERED",
            entity_type="AgentCommerceContract",
            entity_id=merchant_id,
            status="SUCCESS",
            reason=f"AI buyer '{msg.sender.id}' discovered merchant capabilities.",
            metadata={"session_id": session.session_id, "trace_id": trace_id},
            actor_type=ActorType.AI_BUYER,
        )

        return create_success_response(
            message_id=msg.message_id,
            session_id=session.session_id,
            trace_id=trace_id,
            action=msg.action.value,
            data=contract.model_dump(),
        )

    def _handle_search(
        self,
        db: Session,
        session: AgentCommerceSession,
        msg: AgentMessage,
        trace_id: str,
        merchant_id: int,
    ) -> AgentResponse:
        payload = msg.payload or {}
        query = payload.get("query")
        category = payload.get("category")
        max_price = payload.get("max_price")
        in_stock_only = payload.get("in_stock_only", True)

        search_res = search_ai_products(
            db=db,
            query=query,
            merchant_id=merchant_id,
            category=category,
            max_price=max_price,
        )
        products = [r.product for r in search_res.results]

        # Transition session to BROWSING
        session_manager.update_session_state(db, session, SessionStatus.BROWSING)

        session_manager.record_timeline_event(
            db=db,
            session=session,
            action="AGENT_CATALOG_SEARCH",
            actor=msg.sender.id,
            status="SUCCESS",
            details={"query": query, "category": category, "max_price": max_price, "matches": len(products)},
        )

        audit_service.log_agent_action(
            db=db,
            merchant_id=merchant_id,
            action="AGENT_CATALOG_SEARCH",
            entity_type="ProductSearch",
            entity_id=None,
            status="SUCCESS",
            reason=f"AI buyer searched catalog for '{query or 'all'}' ({len(products)} found).",
            metadata={"session_id": session.session_id, "trace_id": trace_id, "query": query},
            actor_type=ActorType.AI_BUYER,
        )

        return create_success_response(
            message_id=msg.message_id,
            session_id=session.session_id,
            trace_id=trace_id,
            action=msg.action.value,
            data={"results_count": len(products), "products": [p.model_dump() for p in products]},
        )

    def _handle_get_product(
        self,
        db: Session,
        session: AgentCommerceSession,
        msg: AgentMessage,
        trace_id: str,
        merchant_id: int,
    ) -> AgentResponse:
        product_id = msg.payload.get("product_id")
        if not product_id:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.PRODUCT_NOT_FOUND,
                message="Field 'product_id' is required in payload.",
            )

        product = db.query(Product).filter(
            Product.id == product_id,
            Product.merchant_id == merchant_id,
        ).first()

        if not product:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.PRODUCT_NOT_FOUND,
                message=f"Product #{product_id} not found for this merchant.",
            )

        canonical = get_canonical_product(product)
        session_manager.update_session_state(db, session, SessionStatus.PRODUCT_SELECTED, product_id=product.id)

        session_manager.record_timeline_event(
            db=db,
            session=session,
            action="AGENT_PRODUCT_SELECTED",
            actor=msg.sender.id,
            status="SUCCESS",
            details={"product_id": product.id, "product_name": product.name, "price": product.price},
        )

        return create_success_response(
            message_id=msg.message_id,
            session_id=session.session_id,
            trace_id=trace_id,
            action=msg.action.value,
            data={"product": canonical.model_dump()},
        )

    def _handle_check_inventory(
        self,
        db: Session,
        session: AgentCommerceSession,
        msg: AgentMessage,
        trace_id: str,
        merchant_id: int,
    ) -> AgentResponse:
        product_id = msg.payload.get("product_id")
        requested_qty = int(msg.payload.get("quantity", 1))

        if not product_id:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.PRODUCT_NOT_FOUND,
                message="Field 'product_id' is required in payload.",
            )

        product = db.query(Product).filter(
            Product.id == product_id,
            Product.merchant_id == merchant_id,
        ).first()

        if not product:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.PRODUCT_NOT_FOUND,
                message=f"Product #{product_id} not found.",
            )

        is_in_stock = product.stock_quantity >= requested_qty and product.is_active

        session_manager.record_timeline_event(
            db=db,
            session=session,
            action="AGENT_INVENTORY_CHECKED",
            actor=msg.sender.id,
            status="SUCCESS" if is_in_stock else "OUT_OF_STOCK",
            details={
                "product_id": product.id,
                "requested_quantity": requested_qty,
                "available_stock": product.stock_quantity,
                "in_stock": is_in_stock,
            },
        )

        if not is_in_stock:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.OUT_OF_STOCK,
                message=f"Requested product '{product.name}' is out of stock (Available: {product.stock_quantity}).",
                details={"product_id": product.id, "available_stock": product.stock_quantity},
            )

        return create_success_response(
            message_id=msg.message_id,
            session_id=session.session_id,
            trace_id=trace_id,
            action=msg.action.value,
            data={
                "product_id": product.id,
                "product_name": product.name,
                "requested_quantity": requested_qty,
                "available_stock": product.stock_quantity,
                "unit_price": product.price,
                "currency": product.currency,
                "in_stock": True,
            },
        )

    def _handle_create_order(
        self,
        db: Session,
        session: AgentCommerceSession,
        msg: AgentMessage,
        trace_id: str,
        merchant_id: int,
    ) -> AgentResponse:
        payload = msg.payload or {}
        product_id = payload.get("product_id")
        quantity = int(payload.get("quantity", 1))
        customer_id = payload.get("customer_id")
        idempotency_key = payload.get("idempotency_key") or f"idemp-{session.session_id}-{msg.message_id}"

        # Construct order request
        if "items" in payload and isinstance(payload["items"], list):
            items_req = [
                AIOrderItemCreate(product_id=it["product_id"], quantity=it.get("quantity", 1))
                for it in payload["items"]
            ]
        elif product_id:
            items_req = [AIOrderItemCreate(product_id=product_id, quantity=quantity)]
        else:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.INVALID_QUANTITY,
                message="Either 'product_id' or 'items' array must be provided in payload.",
            )

        req = AIOrderCreateRequest(
            merchant_id=merchant_id,
            items=items_req,
            idempotency_key=idempotency_key,
        )

        try:
            order_res = create_ai_order(
                db=db,
                request=req,
                idempotency_key=idempotency_key,
            )

            # Update session state
            session_manager.update_session_state(
                db=db,
                session=session,
                status=SessionStatus.ORDER_CREATED,
                product_id=items_req[0].product_id if items_req else None,
                order_id=order_res.order_id,
            )

            session_manager.record_timeline_event(
                db=db,
                session=session,
                action="AGENT_ORDER_CREATED",
                actor=msg.sender.id,
                status="SUCCESS",
                details={
                    "order_id": order_res.order_id,
                    "total_amount": order_res.total_amount,
                    "currency": order_res.currency,
                },
            )

            audit_service.log_agent_action(
                db=db,
                merchant_id=merchant_id,
                action="AGENT_ORDER_CREATED",
                entity_type="Order",
                entity_id=order_res.order_id,
                status="SUCCESS",
                reason=f"Order #{order_res.order_id} created by AI buyer '{msg.sender.id}' for ₹{order_res.total_amount:,.2f}.",
                metadata={"session_id": session.session_id, "trace_id": trace_id, "idempotency_key": idempotency_key},
                actor_type=ActorType.AI_BUYER,
            )

            return create_success_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                data=order_res.model_dump(),
            )
        except Exception as e:
            err_str = str(e)
            code = ErrorCodes.OUT_OF_STOCK if "stock" in err_str.lower() else ErrorCodes.INTERNAL_ERROR
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=code,
                message=f"Failed to create order: {err_str}",
            )

    def _handle_propose_payment(
        self,
        db: Session,
        session: AgentCommerceSession,
        msg: AgentMessage,
        trace_id: str,
        merchant_id: int,
    ) -> AgentResponse:
        order_id = msg.payload.get("order_id") or session.order_id
        if not order_id:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.ORDER_NOT_FOUND,
                message="No order_id provided in payload or active in session.",
            )

        idempotency_key = msg.payload.get("idempotency_key") or f"pay-intent-{session.session_id}-{order_id}"

        try:
            intent = payment_service.propose_payment(
                db=db,
                order_id=order_id,
                merchant_id=merchant_id,
                idempotency_key=idempotency_key,
            )

            # Update session state to PAYMENT_PENDING
            session_manager.update_session_state(
                db=db,
                session=session,
                status=SessionStatus.PAYMENT_PENDING,
                payment_intent_id=intent.id,
            )

            risk_str = intent.risk_level.value if hasattr(intent.risk_level, "value") else str(intent.risk_level)

            session_manager.record_timeline_event(
                db=db,
                session=session,
                action="AGENT_PAYMENT_PROPOSED",
                actor=msg.sender.id,
                status="SUCCESS",
                details={
                    "payment_intent_id": intent.id,
                    "amount": intent.amount,
                    "currency": intent.currency,
                    "risk_level": risk_str,
                    "requires_approval": intent.requires_approval,
                },
            )

            audit_service.log_agent_action(
                db=db,
                merchant_id=merchant_id,
                action="AGENT_PAYMENT_PROPOSED",
                entity_type="PaymentIntent",
                entity_id=intent.id,
                status="SUCCESS",
                reason=f"Payment intent proposed for ₹{intent.amount:,.2f} (Risk: {risk_str}).",
                metadata={"session_id": session.session_id, "trace_id": trace_id},
                actor_type=ActorType.AI_BUYER,
            )

            return create_success_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                data=intent.model_dump(),
            )
        except Exception as e:
            err_str = str(e)
            code = ErrorCodes.PAYMENT_LIMIT_EXCEEDED if "exceed" in err_str.lower() else ErrorCodes.PAYMENT_NOT_ALLOWED
            
            session_manager.record_timeline_event(
                db=db,
                session=session,
                action="AGENT_PAYMENT_BLOCKED",
                actor=msg.sender.id,
                status="BLOCKED",
                details={"reason": err_str},
            )

            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=code,
                message=f"Payment proposal blocked: {err_str}",
            )

    def _handle_get_payment_status(
        self,
        db: Session,
        session: AgentCommerceSession,
        msg: AgentMessage,
        trace_id: str,
        merchant_id: int,
    ) -> AgentResponse:
        intent_id = msg.payload.get("payment_intent_id") or session.payment_intent_id
        if not intent_id:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.ORDER_NOT_FOUND,
                message="No payment_intent_id found in payload or active session.",
            )

        intent = db.query(PaymentIntent).filter(
            PaymentIntent.id == intent_id,
            PaymentIntent.merchant_id == merchant_id,
        ).first()

        if not intent:
            return create_error_response(
                message_id=msg.message_id,
                session_id=session.session_id,
                trace_id=trace_id,
                action=msg.action.value,
                code=ErrorCodes.ORDER_NOT_FOUND,
                message=f"Payment intent #{intent_id} not found.",
            )

        order = db.query(Order).filter(Order.id == intent.order_id).first()
        is_paid = order is not None and order.status.value == "PAID"

        if is_paid:
            session_manager.update_session_state(db, session, SessionStatus.COMPLETED)
            session_manager.record_timeline_event(
                db=db,
                session=session,
                action="AGENT_COMMERCE_COMPLETED",
                actor=msg.sender.id,
                status="SUCCESS",
                details={"order_id": order.id, "payment_status": "PAID"},
            )

        return create_success_response(
            message_id=msg.message_id,
            session_id=session.session_id,
            trace_id=trace_id,
            action=msg.action.value,
            data={
                "payment_intent_id": intent.id,
                "order_id": intent.order_id,
                "amount": intent.amount,
                "currency": intent.currency,
                "intent_status": intent.status.value,
                "order_status": order.status.value if order else "UNKNOWN",
                "payment_status": order.payment_status if order else "UNKNOWN",
                "is_completed": is_paid,
                "approved_by": intent.approved_by,
                "approved_at": intent.approved_at.isoformat() if intent.approved_at else None,
            },
        )


merchant_commerce_agent = MerchantCommerceAgent()
