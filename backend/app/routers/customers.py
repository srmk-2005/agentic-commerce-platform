"""Customer API router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    """Register a new customer."""
    existing = CustomerService.get_customer_by_email(db, customer_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email '{customer_in.email}' already exists.",
        )
    try:
        return CustomerService.create_customer(db, customer_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer creation failed due to database constraint.",
        )


@router.get(
    "",
    response_model=List[CustomerResponse],
    summary="List all customers",
)
def list_customers(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit records per page"),
    db: Session = Depends(get_db),
):
    """Retrieve list of customers."""
    return CustomerService.get_customers(db, skip=skip, limit=limit)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer by ID",
)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a single customer."""
    customer = CustomerService.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found.",
        )
    return customer
