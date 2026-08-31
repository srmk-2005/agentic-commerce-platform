"""SQLAlchemy ORM Models for AI Merchant Commerce Platform."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def utc_now():
    """Return current UTC timestamp with timezone."""
    return datetime.now(timezone.utc)


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


# --- Phase 3 Enums ---

class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CampaignType(str, enum.Enum):
    CROSS_SELL = "CROSS_SELL"
    UPSELL = "UPSELL"
    BUNDLE = "BUNDLE"
    SLOW_MOVING_PRODUCT = "SLOW_MOVING_PRODUCT"
    GENERAL_PROMOTION = "GENERAL_PROMOTION"


class ProductCampaignRole(str, enum.Enum):
    PRIMARY = "PRIMARY"
    RECOMMENDED = "RECOMMENDED"
    BUNDLE_ITEM = "BUNDLE_ITEM"
    TARGET = "TARGET"


class OfferType(str, enum.Enum):
    UPSELL = "UPSELL"
    CROSS_SELL = "CROSS_SELL"
    BUNDLE = "BUNDLE"
    PRODUCT_DISCOUNT = "PRODUCT_DISCOUNT"


class DiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalActionType(str, enum.Enum):
    CREATE_CAMPAIGN = "CREATE_CAMPAIGN"
    CREATE_OFFER = "CREATE_OFFER"
    ACTIVATE_CAMPAIGN = "ACTIVATE_CAMPAIGN"
    UPDATE_OFFER = "UPDATE_OFFER"


class AgentActionStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ActorType(str, enum.Enum):
    MERCHANT = "MERCHANT"
    AI_AGENT = "AI_AGENT"
    AI_BUYER = "AI_BUYER"
    SYSTEM = "SYSTEM"


# --- Core Commerce Models ---

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    products = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="merchant")
    campaigns = relationship("Campaign", back_populates="merchant", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="merchant", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="merchant", cascade="all, delete-orphan")
    agent_actions = relationship("AgentAction", back_populates="merchant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="merchant", cascade="all, delete-orphan")
    ai_policy = relationship("MerchantAiPolicy", back_populates="merchant", uselist=False, cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    sku = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_product_price_non_negative"),
        CheckConstraint("stock_quantity >= 0", name="check_product_stock_non_negative"),
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    campaign_products = relationship("CampaignProduct", back_populates="product", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="product", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    payment_status = Column(String(50), default="NOT_AVAILABLE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="check_order_total_non_negative"),
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_order_item_unit_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="check_order_item_subtotal_non_negative"),
    )

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# --- Phase 3 Revenue Growth & Approval Models ---

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    campaign_type = Column(Enum(CampaignType), nullable=False, index=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Enum(ActorType), default=ActorType.AI_AGENT, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    merchant = relationship("Merchant", back_populates="campaigns")
    products = relationship("CampaignProduct", back_populates="campaign", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="campaign", cascade="all, delete-orphan")


class CampaignProduct(Base):
    __tablename__ = "campaign_products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(ProductCampaignRole), default=ProductCampaignRole.PRIMARY, nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="products")
    product = relationship("Product", back_populates="campaign_products")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    offer_type = Column(Enum(OfferType), nullable=False, index=True)
    discount_type = Column(Enum(DiscountType), default=DiscountType.PERCENTAGE, nullable=False)
    discount_value = Column(Float, nullable=False)
    maximum_discount_amount = Column(Float, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("discount_value >= 0", name="check_offer_discount_value_non_negative"),
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="offers")
    campaign = relationship("Campaign", back_populates="offers")
    product = relationship("Product", back_populates="offers")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(Enum(ApprovalActionType), nullable=False, index=True)
    action_id = Column(Integer, nullable=True, index=True)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True)
    requested_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

    # Relationships
    merchant = relationship("Merchant", back_populates="approvals")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_session_id = Column(String(100), nullable=True, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    target_type = Column(String(100), nullable=True)
    target_id = Column(Integer, nullable=True)
    status = Column(Enum(AgentActionStatus), default=AgentActionStatus.PROPOSED, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    merchant = relationship("Merchant", back_populates="agent_actions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_type = Column(Enum(ActorType), default=ActorType.AI_AGENT, nullable=False, index=True)
    actor_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    merchant = relationship("Merchant", back_populates="audit_logs")


class MerchantAiPolicy(Base):
    __tablename__ = "merchant_ai_policies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    max_discount_percentage = Column(Float, default=20.0, nullable=False)
    max_discount_amount = Column(Float, default=1000.0, nullable=False)
    auto_approve_non_financial = Column(Boolean, default=False, nullable=False)
    require_approval_for_campaigns = Column(Boolean, default=True, nullable=False)
    require_approval_for_discounts = Column(Boolean, default=True, nullable=False)
    max_campaign_duration_days = Column(Integer, default=30, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("max_discount_percentage >= 0 AND max_discount_percentage <= 100", name="check_max_discount_percentage_range"),
        CheckConstraint("max_discount_amount >= 0", name="check_max_discount_amount_non_negative"),
        CheckConstraint("max_campaign_duration_days > 0", name="check_max_duration_positive"),
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="ai_policy")
