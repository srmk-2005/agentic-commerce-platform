"""API Router for Offers."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Offer
from app.schemas.offer import OfferCreate, OfferResponse

router = APIRouter(prefix="/offers", tags=["Offers"])


def _format_offer(off: Offer) -> OfferResponse:
    p_name = off.product.name if off.product else None
    return OfferResponse(
        id=off.id,
        merchant_id=off.merchant_id,
        campaign_id=off.campaign_id,
        product_id=off.product_id,
        product_name=p_name,
        offer_type=off.offer_type,
        discount_type=off.discount_type,
        discount_value=off.discount_value,
        maximum_discount_amount=off.maximum_discount_amount,
        status=off.status,
        created_at=off.created_at,
        updated_at=off.updated_at,
    )


@router.get(
    "",
    response_model=List[OfferResponse],
    summary="List offers with optional merchant and campaign filters",
)
def list_offers(
    merchant_id: Optional[int] = Query(None, gt=0),
    campaign_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(Offer)
    if merchant_id:
        query = query.filter(Offer.merchant_id == merchant_id)
    if campaign_id:
        query = query.filter(Offer.campaign_id == campaign_id)

    offers = query.order_by(Offer.created_at.desc()).all()
    return [_format_offer(o) for o in offers]


@router.get(
    "/{offer_id}",
    response_model=OfferResponse,
    summary="Get offer details by ID",
)
def get_offer(
    offer_id: int,
    db: Session = Depends(get_db),
):
    off = db.query(Offer).filter(Offer.id == offer_id).first()
    if not off:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Offer #{offer_id} not found.")
    return _format_offer(off)
