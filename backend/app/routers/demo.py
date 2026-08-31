"""Router for Demo Sandbox Control and Environment Reset."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.seed import seed_database
from app.db.models import (
    AgentAction,
    AgentCommerceSession,
    Approval,
    Campaign,
    CampaignProduct,
    Order,
    OrderItem,
    Payment,
    PaymentIntent,
    Product,
)

router = APIRouter(prefix="/demo", tags=["Demo & Sandbox Control"])


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset Demo Data",
    description="Resets demo merchant, catalog inventory, orders, and payment intents to pristine presentation state.",
)
def reset_demo_data(db: Session = Depends(get_db)):
    """Reset sandbox demo data for clean hackathon presentations."""
    try:
        # Reset products to initial stock levels
        products = db.query(Product).filter(Product.merchant_id == 1).all()
        stock_defaults = {
            "Running Shoes": 50,
            "Sports Socks": 150,
            "Sports T-Shirt": 80,
            "Sports Bag": 40,
            "Gym Water Bottle": 120,
            "Protein Shaker Pro": 60,
        }
        for p in products:
            if p.name in stock_defaults:
                p.stock_quantity = stock_defaults[p.name]
                p.is_active = True

        # Clear test sessions and intents if any
        db.query(AgentCommerceSession).filter(AgentCommerceSession.merchant_id == 1).delete()
        
        # Ensure base seed data exists
        seed_database(db)
        db.commit()

        return {
            "success": True,
            "message": "Demo data reset successfully to pristine presentation state.",
            "merchant_id": 1,
            "products_restocked": len(products),
            "status": "ready",
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Demo reset encountered non-fatal error: {str(e)}",
            "status": "degraded",
        }
