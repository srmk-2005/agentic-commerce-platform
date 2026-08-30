"""Database seeding script for demo data."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.database import Base, SessionLocal, engine
from app.db.models import (
    ActorType,
    AgentAction,
    AgentActionStatus,
    Approval,
    ApprovalActionType,
    ApprovalStatus,
    Campaign,
    CampaignProduct,
    CampaignStatus,
    CampaignType,
    Customer,
    DiscountType,
    Merchant,
    MerchantAiPolicy,
    Offer,
    OfferType,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductCampaignRole,
)


def seed_database(db: Session) -> None:
    """Populate database with initial merchant, catalog products, customers, orders, policies, and demo approvals."""
    print("[SEED] Starting database seeding...")
    Base.metadata.create_all(bind=engine)

    # 1. Seed Merchant
    merchant = db.query(Merchant).filter(Merchant.email == "contact@chennaisports.com").first()
    if not merchant:
        merchant = Merchant(
            name="Chennai Sports Store",
            email="contact@chennaisports.com",
            description="Premier sports gear, footwear, and athletic performance equipment retailer in Chennai.",
            currency="INR",
            is_active=True,
        )
        db.add(merchant)
        db.flush()
        print(f"  [+] Seeded Merchant: {merchant.name} (ID: {merchant.id})")
    else:
        print(f"  [i] Merchant already exists: {merchant.name} (ID: {merchant.id})")

    # 2. Seed Merchant AI Safety Policy (Phase 3)
    policy = db.query(MerchantAiPolicy).filter(MerchantAiPolicy.merchant_id == merchant.id).first()
    if not policy:
        policy = MerchantAiPolicy(
            merchant_id=merchant.id,
            max_discount_percentage=20.0,
            max_discount_amount=1000.0,
            auto_approve_non_financial=False,
            require_approval_for_campaigns=True,
            require_approval_for_discounts=True,
            max_campaign_duration_days=30,
            is_enabled=True,
        )
        db.add(policy)
        db.flush()
        print(f"  [+] Seeded AI Safety Policy for Merchant ID {merchant.id} (Max Discount: {policy.max_discount_percentage}%)")
    else:
        print(f"  [i] AI Safety Policy already exists for Merchant ID {merchant.id}")

    # 3. Seed Products
    products_data = [
        {
            "name": "Running Shoes",
            "price": 2499.0,
            "sku": "CSS-RUN-001",
            "category": "Footwear",
            "stock_quantity": 50,
            "description": "High-performance cushioned running shoes engineered for road and marathon training.",
        },
        {
            "name": "Premium Running Shoes",
            "price": 3499.0,
            "sku": "CSS-RUN-002",
            "category": "Footwear",
            "stock_quantity": 30,
            "description": "Carbon-plated ultra-responsive running shoes designed for elite racing performance.",
        },
        {
            "name": "Running Socks",
            "price": 299.0,
            "sku": "CSS-ACC-001",
            "category": "Accessories",
            "stock_quantity": 150,
            "description": "Anti-blister moisture-wicking compression athletic socks (pack of 3).",
        },
        {
            "name": "Sports T-Shirt",
            "price": 999.0,
            "sku": "CSS-APP-001",
            "category": "Apparel",
            "stock_quantity": 80,
            "description": "Breathable quick-dry moisture-management athletic training t-shirt.",
        },
        {
            "name": "Sports Bag",
            "price": 1499.0,
            "sku": "CSS-BAG-001",
            "category": "Accessories",
            "stock_quantity": 40,
            "description": "Water-resistant gym and travel duffel bag with dedicated shoe compartment.",
        },
    ]

    products_map = {}
    for p_data in products_data:
        prod = db.query(Product).filter(Product.sku == p_data["sku"]).first()
        if not prod:
            prod = Product(
                merchant_id=merchant.id,
                name=p_data["name"],
                price=p_data["price"],
                sku=p_data["sku"],
                category=p_data["category"],
                stock_quantity=p_data["stock_quantity"],
                description=p_data["description"],
                currency=merchant.currency,
                is_active=True,
            )
            db.add(prod)
            db.flush()
            print(f"  [+] Seeded Product: {prod.name} (SKU: {prod.sku}, Price: Rs.{prod.price})")
        else:
            print(f"  [i] Product already exists: {prod.name} (SKU: {prod.sku})")
        products_map[prod.name] = prod

    # 4. Seed Customers
    customers_data = [
        {"name": "Ananya Sharma", "email": "ananya.sharma@example.com"},
        {"name": "Rahul Verma", "email": "rahul.verma@example.com"},
        {"name": "Priya Sundaram", "email": "priya.sundaram@example.com"},
        {"name": "Karthik Raja", "email": "karthik.raja@example.com"},
        {"name": "Deepa Narayanan", "email": "deepa.narayanan@example.com"},
    ]

    customers_map = {}
    for c_data in customers_data:
        cust = db.query(Customer).filter(Customer.email == c_data["email"]).first()
        if not cust:
            cust = Customer(name=c_data["name"], email=c_data["email"])
            db.add(cust)
            db.flush()
            print(f"  [+] Seeded Customer: {cust.name} (Email: {cust.email})")
        else:
            print(f"  [i] Customer already exists: {cust.name} (Email: {cust.email})")
        customers_map[cust.name] = cust

    # 5. Seed Historical Orders
    now = datetime.now(timezone.utc)
    existing_orders_count = db.query(Order).filter(Order.merchant_id == merchant.id).count()
    if existing_orders_count == 0:
        sample_orders = [
            {
                "customer": "Ananya Sharma",
                "days_ago": 18,
                "status": OrderStatus.CONFIRMED,
                "items": [
                    ("Running Shoes", 1),
                    ("Running Socks", 2),
                ],
            },
            {
                "customer": "Rahul Verma",
                "days_ago": 15,
                "status": OrderStatus.CONFIRMED,
                "items": [
                    ("Running Shoes", 1),
                    ("Running Socks", 1),
                ],
            },
            {
                "customer": "Priya Sundaram",
                "days_ago": 12,
                "status": OrderStatus.CONFIRMED,
                "items": [
                    ("Premium Running Shoes", 1),
                    ("Sports T-Shirt", 1),
                ],
            },
            {
                "customer": "Karthik Raja",
                "days_ago": 10,
                "status": OrderStatus.CONFIRMED,
                "items": [
                    ("Running Socks", 3),
                    ("Sports Bag", 1),
                ],
            },
            {
                "customer": "Deepa Narayanan",
                "days_ago": 8,
                "status": OrderStatus.CONFIRMED,
                "items": [
                    ("Running Socks", 2),
                    ("Sports Bag", 1),
                ],
            },
            {
                "customer": "Ananya Sharma",
                "days_ago": 5,
                "status": OrderStatus.CONFIRMED,
                "items": [
                    ("Running Socks", 1),
                    ("Sports Bag", 1),
                ],
            },
            {
                "customer": "Rahul Verma",
                "days_ago": 3,
                "status": OrderStatus.CONFIRMED,
                "items": [
                    ("Running Shoes", 1),
                    ("Sports T-Shirt", 2),
                ],
            },
            {
                "customer": "Priya Sundaram",
                "days_ago": 1,
                "status": OrderStatus.PENDING,
                "items": [
                    ("Running Socks", 1),
                ],
            },
        ]

        for ord_spec in sample_orders:
            cust = customers_map[ord_spec["customer"]]
            order_date = now - timedelta(days=ord_spec["days_ago"])
            
            total_amount = 0.0
            order_items = []
            for prod_name, qty in ord_spec["items"]:
                p = products_map[prod_name]
                subtotal = round(float(p.price) * qty, 2)
                total_amount += subtotal
                order_items.append((p.id, qty, float(p.price), subtotal))
            
            order = Order(
                merchant_id=merchant.id,
                customer_id=cust.id,
                status=ord_spec["status"],
                total_amount=round(total_amount, 2),
                currency=merchant.currency,
                created_at=order_date,
                updated_at=order_date,
            )
            db.add(order)
            db.flush()

            for pid, qty, uprice, sub in order_items:
                item = OrderItem(
                    order_id=order.id,
                    product_id=pid,
                    quantity=qty,
                    unit_price=uprice,
                    subtotal=sub,
                )
                db.add(item)
            print(f"  [+] Seeded Order #{order.id} for {cust.name} (Rs.{order.total_amount}, {order.status.value})")

    # 6. Seed Demo Campaigns & Approvals (Phase 3)
    existing_campaigns = db.query(Campaign).filter(Campaign.merchant_id == merchant.id).count()
    if existing_campaigns == 0:
        shoes = products_map["Running Shoes"]
        socks = products_map["Running Socks"]

        # Active demo campaign
        active_camp = Campaign(
            merchant_id=merchant.id,
            name="Runner Essentials Cross-Sell",
            description="Automatic checkout add-on promotion offering 10% discount on athletic compression socks when purchasing running shoes.",
            campaign_type=CampaignType.CROSS_SELL,
            status=CampaignStatus.ACTIVE,
            start_date=now - timedelta(days=2),
            end_date=now + timedelta(days=12),
            created_by=ActorType.AI_AGENT,
        )
        db.add(active_camp)
        db.flush()

        db.add(CampaignProduct(campaign_id=active_camp.id, product_id=shoes.id, role=ProductCampaignRole.PRIMARY))
        db.add(CampaignProduct(campaign_id=active_camp.id, product_id=socks.id, role=ProductCampaignRole.RECOMMENDED))
        db.add(Offer(
            merchant_id=merchant.id,
            campaign_id=active_camp.id,
            product_id=socks.id,
            offer_type=OfferType.CROSS_SELL,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=10.0,
            maximum_discount_amount=100.0,
            status="ACTIVE",
        ))
        print(f"  [+] Seeded Demo Campaign: '{active_camp.name}' (Status: ACTIVE)")

        # Pending Approval Proposal
        bag = products_map["Sports Bag"]
        agent_action = AgentAction(
            merchant_id=merchant.id,
            agent_session_id="session-init-001",
            action_type="CREATE_BUNDLE",
            target_type="PRODUCT",
            target_id=shoes.id,
            status=AgentActionStatus.PENDING_APPROVAL,
            reason="High affinity pair (Running Shoes + Sports Bag) identified from order history.",
            input_data='{"primary_product_id": %d, "recommended_product_ids": [%d], "discount_percentage": 10.0, "duration_days": 7}' % (shoes.id, bag.id),
        )
        db.add(agent_action)
        db.flush()

        approval = Approval(
            merchant_id=merchant.id,
            action_type=ApprovalActionType.CREATE_CAMPAIGN,
            action_id=agent_action.id,
            status=ApprovalStatus.PENDING,
            reason="AI identified strong co-purchase opportunity to bundle 'Running Shoes' with 'Sports Bag' at a 10% discount for 7 days.",
            metadata_json='{"title": "Marathon Starter Bundle", "campaign_type": "BUNDLE", "products": ["Running Shoes", "Sports Bag"], "product_ids": [%d, %d], "discount_type": "PERCENTAGE", "discount_value": 10.0, "duration_days": 7, "original_total": 3998.0, "bundle_price": 3598.20, "estimated_revenue_impact": 12500.0}' % (shoes.id, bag.id),
        )
        db.add(approval)
        print(f"  [+] Seeded Pending Approval #{approval.id}: '{approval.reason}'")

    db.commit()
    print("[SUCCESS] Seeding completed successfully!\n")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
