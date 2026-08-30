"""Product API router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product item assigned to a valid merchant."""
    try:
        return ProductService.create_product(db, product_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List products with filtering and search",
)
def list_products(
    merchant_id: Optional[int] = Query(None, description="Filter products by merchant ID"),
    category: Optional[str] = Query(None, description="Filter products by category name"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive products"),
    search: Optional[str] = Query(None, description="Search term across name, description, SKU, category"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit records per page"),
    db: Session = Depends(get_db),
):
    """Retrieve catalog products with optional filters and keyword search."""
    return ProductService.get_products(
        db,
        merchant_id=merchant_id,
        category=category,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Retrieve product details by product ID."""
    product = ProductService.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details",
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Update existing product fields, prices, and stock."""
    updated = ProductService.update_product(db, product_id, product_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    return updated


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a product",
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product item from catalog."""
    deleted = ProductService.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    return {"message": f"Product {product_id} deleted successfully."}
