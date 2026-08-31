"""Unit tests for Phase 6 AI Commerce Readiness Scoring Engine."""
import pytest
from sqlalchemy.orm import Session
from app.agent_commerce.policies import readiness_scorer
from app.db.models import Merchant, MerchantAiPolicy, Product


def test_calculate_readiness_complete_merchant(db: Session, sample_merchant: Merchant, sample_product: Product):
    """Test fully configured merchant achieves high readiness score (>= 80%)."""
    res = readiness_scorer.calculate_readiness(db, sample_merchant.id)
    assert res is not None
    assert res.readiness_score >= 80
    assert res.is_ready is True
    assert len(res.checklist) == 8

    # Verify category names
    categories = [it.category for it in res.checklist]
    assert "Catalog" in categories
    assert "Search" in categories
    assert "Inventory" in categories
    assert "Orders" in categories
    assert "Payments" in categories


def test_calculate_readiness_nonexistent_merchant(db: Session):
    """Test readiness scoring for invalid merchant returns None."""
    res = readiness_scorer.calculate_readiness(db, 999999)
    assert res is None
