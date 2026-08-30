"""Business logic service for Customer entity."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Customer
from app.schemas.customer import CustomerCreate


class CustomerService:
    @staticmethod
    def create_customer(db: Session, customer_in: CustomerCreate) -> Customer:
        """Create a new customer record."""
        customer = Customer(
            name=customer_in.name,
            email=customer_in.email,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
        """Fetch single customer by ID."""
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
        """Fetch single customer by email address."""
        return db.query(Customer).filter(Customer.email == email).first()

    @staticmethod
    def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Fetch customers list with pagination."""
        return db.query(Customer).order_by(Customer.id.desc()).offset(skip).limit(limit).all()
