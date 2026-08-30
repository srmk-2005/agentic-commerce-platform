"""API Router for Campaigns Management."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import (
    Campaign,
    CampaignProduct,
    CampaignStatus,
    CampaignType,
    Merchant,
    Product,
)
from app.schemas.campaign import (
    CampaignCreate,
    CampaignProductResponse,
    CampaignResponse,
    CampaignUpdate,
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def _format_campaign(camp: Campaign) -> CampaignResponse:
    products_res = []
    for cp in camp.products:
        p_name = cp.product.name if cp.product else None
        products_res.append(
            CampaignProductResponse(
                id=cp.id,
                product_id=cp.product_id,
                product_name=p_name,
                role=cp.role,
            )
        )

    return CampaignResponse(
        id=camp.id,
        merchant_id=camp.merchant_id,
        name=camp.name,
        description=camp.description,
        campaign_type=camp.campaign_type,
        status=camp.status,
        start_date=camp.start_date,
        end_date=camp.end_date,
        created_by=camp.created_by,
        created_at=camp.created_at,
        updated_at=camp.updated_at,
        products=products_res,
    )


@router.get(
    "",
    response_model=List[CampaignResponse],
    summary="List campaigns with optional merchant and status filters",
)
def list_campaigns(
    merchant_id: Optional[int] = Query(None, gt=0),
    campaign_status: Optional[CampaignStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(Campaign)
    if merchant_id:
        query = query.filter(Campaign.merchant_id == merchant_id)
    if campaign_status:
        query = query.filter(Campaign.status == campaign_status)

    campaigns = query.order_by(Campaign.created_at.desc()).all()
    return [_format_campaign(c) for c in campaigns]


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get campaign by ID",
)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    camp = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not camp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign #{campaign_id} not found.")
    return _format_campaign(camp)


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campaign directly (Manual Merchant creation)",
)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
):
    merchant = db.query(Merchant).filter(Merchant.id == payload.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Merchant #{payload.merchant_id} not found.")

    camp = Campaign(
        merchant_id=payload.merchant_id,
        name=payload.name,
        description=payload.description,
        campaign_type=payload.campaign_type,
        status=payload.status,
        start_date=payload.start_date or datetime.now(timezone.utc),
        end_date=payload.end_date,
        created_by=payload.created_by,
    )
    db.add(camp)
    db.flush()

    for cp_in in payload.products:
        prod = db.query(Product).filter(Product.id == cp_in.product_id, Product.merchant_id == payload.merchant_id).first()
        if prod:
            db.add(CampaignProduct(campaign_id=camp.id, product_id=prod.id, role=cp_in.role))

    db.commit()
    db.refresh(camp)
    return _format_campaign(camp)


@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Update campaign details or status",
)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
):
    camp = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not camp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign #{campaign_id} not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(camp, field, val)

    camp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(camp)
    return _format_campaign(camp)


@router.post(
    "/{campaign_id}/pause",
    response_model=CampaignResponse,
    summary="Pause an active campaign",
)
def pause_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    camp = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not camp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign #{campaign_id} not found.")

    camp.status = CampaignStatus.PAUSED
    camp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(camp)
    return _format_campaign(camp)


@router.post(
    "/{campaign_id}/activate",
    response_model=CampaignResponse,
    summary="Activate a paused or approved campaign",
)
def activate_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    camp = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not camp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign #{campaign_id} not found.")

    camp.status = CampaignStatus.ACTIVE
    camp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(camp)
    return _format_campaign(camp)
