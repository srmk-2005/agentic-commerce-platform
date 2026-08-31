"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app

# Create in-memory SQLite engine for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable SQLite foreign key pragma
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_session):
    """Alias for db_session fixture."""
    return db_session


@pytest.fixture(scope="function")
def sample_merchant(db_session):
    """Provide a persisted sample merchant with policy."""
    from app.db.models import Merchant, MerchantAiPolicy
    merchant = Merchant(
        name="Test Chennai Sports",
        email="test_sports@example.com",
        description="Sports gear and footwear store",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.commit()
    db_session.refresh(merchant)

    policy = MerchantAiPolicy(
        merchant_id=merchant.id,
        max_ai_transaction_amount=5000.0,
        daily_ai_transaction_limit=25000.0,
        require_payment_approval=True,
        allow_ai_payment=True,
    )
    db_session.add(policy)
    db_session.commit()

    return merchant


@pytest.fixture(scope="function")
def sample_product(db_session, sample_merchant):
    """Provide a persisted sample product."""
    from app.db.models import Product
    product = Product(
        merchant_id=sample_merchant.id,
        name="Running Shoes",
        description="High performance shoes",
        category="Footwear",
        price=2499.0,
        stock_quantity=50,
        sku="RUN-SHOE-001",
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture(scope="function")
def client(db_session):
    """Provide TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
