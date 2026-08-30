"""Business logic service for Merchant entity."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Merchant
from app.schemas.merchant import MerchantCreate, MerchantUpdate


class MerchantService:
    @staticmethod
    def create_merchant(db: Session, merchant_in: MerchantCreate) -> Merchant:
        """Create a new merchant record."""
        merchant = Merchant(
            name=merchant_in.name,
            email=merchant_in.email,
            description=merchant_in.description,
            currency=merchant_in.currency.upper(),
            is_active=merchant_in.is_active,
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def get_merchant(db: Session, merchant_id: int) -> Optional[Merchant]:
        """Fetch single merchant by ID."""
        return db.query(Merchant).filter(Merchant.id == merchant_id).first()

    @staticmethod
    def get_merchant_by_email(db: Session, email: str) -> Optional[Merchant]:
        """Fetch single merchant by email address."""
        return db.query(Merchant).filter(Merchant.email == email).first()

    @staticmethod
    def get_merchants(db: Session, skip: int = 0, limit: int = 100) -> List[Merchant]:
        """Fetch multiple merchants with pagination."""
        return db.query(Merchant).offset(skip).limit(limit).all()

    @staticmethod
    def update_merchant(
        db: Session, merchant_id: int, merchant_in: MerchantUpdate
    ) -> Optional[Merchant]:
        """Update existing merchant details."""
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            return None

        update_data = merchant_in.model_dump(exclude_unset=True)
        if "currency" in update_data and update_data["currency"]:
            update_data["currency"] = update_data["currency"].upper()

        for key, value in update_data.items():
            setattr(merchant, key, value)

        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def delete_merchant(db: Session, merchant_id: int) -> bool:
        """Delete merchant by ID."""
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            return False
        db.delete(merchant)
        db.commit()
        return True
