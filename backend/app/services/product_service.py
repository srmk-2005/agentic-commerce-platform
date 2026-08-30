"""Business logic service for Product entity."""
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db.models import Merchant, Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    @staticmethod
    def create_product(db: Session, product_in: ProductCreate) -> Product:
        """Create a new product under a verified merchant."""
        merchant = db.query(Merchant).filter(Merchant.id == product_in.merchant_id).first()
        if not merchant:
            raise ValueError(f"Merchant with id {product_in.merchant_id} does not exist.")

        product = Product(
            merchant_id=product_in.merchant_id,
            name=product_in.name,
            description=product_in.description,
            category=product_in.category,
            price=product_in.price,
            currency=product_in.currency.upper(),
            stock_quantity=product_in.stock_quantity,
            sku=product_in.sku,
            is_active=product_in.is_active,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_product(db: Session, product_id: int) -> Optional[Product]:
        """Fetch single product by ID."""
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def get_products(
        db: Session,
        merchant_id: Optional[int] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Product]:
        """Fetch products with filtering and keyword search."""
        query = db.query(Product)

        if merchant_id is not None:
            query = query.filter(Product.merchant_id == merchant_id)

        if category is not None and category.strip():
            query = query.filter(Product.category.ilike(f"%{category.strip()}%"))

        if is_active is not None:
            query = query.filter(Product.is_active == is_active)

        if search is not None and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.description.ilike(term),
                    Product.sku.ilike(term),
                    Product.category.ilike(term),
                )
            )

        return query.order_by(Product.id.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_product(
        db: Session, product_id: int, product_in: ProductUpdate
    ) -> Optional[Product]:
        """Update existing product details."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        update_data = product_in.model_dump(exclude_unset=True)
        if "currency" in update_data and update_data["currency"]:
            update_data["currency"] = update_data["currency"].upper()

        for key, value in update_data.items():
            setattr(product, key, value)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """Delete product by ID."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        db.delete(product)
        db.commit()
        return True
