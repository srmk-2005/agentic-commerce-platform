"""Merchant API router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate
from app.services.merchant_service import MerchantService

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.post(
    "",
    response_model=MerchantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new merchant",
)
def create_merchant(merchant_in: MerchantCreate, db: Session = Depends(get_db)):
    """Create a new merchant profile with distinct email."""
    existing = MerchantService.get_merchant_by_email(db, merchant_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Merchant with email '{merchant_in.email}' already exists.",
        )
    try:
        return MerchantService.create_merchant(db, merchant_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Merchant registration failed due to database constraint.",
        )


@router.get(
    "",
    response_model=List[MerchantResponse],
    summary="List all merchants",
)
def list_merchants(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit records per page"),
    db: Session = Depends(get_db),
):
    """Retrieve list of registered merchants."""
    return MerchantService.get_merchants(db, skip=skip, limit=limit)


@router.get(
    "/{merchant_id}",
    response_model=MerchantResponse,
    summary="Get merchant by ID",
)
def get_merchant(merchant_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a specific merchant."""
    merchant = MerchantService.get_merchant(db, merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {merchant_id} not found.",
        )
    return merchant


@router.put(
    "/{merchant_id}",
    response_model=MerchantResponse,
    summary="Update merchant details",
)
def update_merchant(
    merchant_id: int,
    merchant_in: MerchantUpdate,
    db: Session = Depends(get_db),
):
    """Update profile and settings of a merchant."""
    if merchant_in.email is not None:
        existing = MerchantService.get_merchant_by_email(db, merchant_in.email)
        if existing and existing.id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{merchant_in.email}' is already in use by another merchant.",
            )

    updated = MerchantService.update_merchant(db, merchant_id, merchant_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {merchant_id} not found.",
        )
    return updated


@router.delete(
    "/{merchant_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a merchant",
)
def delete_merchant(merchant_id: int, db: Session = Depends(get_db)):
    """Delete merchant account and associated products/orders."""
    deleted = MerchantService.delete_merchant(db, merchant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant with id {merchant_id} not found.",
        )
    return {"message": f"Merchant {merchant_id} deleted successfully."}
