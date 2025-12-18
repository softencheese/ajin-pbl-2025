import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from fastapi import FastAPI
from main import app

# Use in-memory SQLite for testing to avoid side effects on real DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    
    # Disable lifespan events or override them to use test engine
    # Since lifespan is a context manager, we can just replace it for testing if needed
    # But connecting to valid DB is better.
    # We will override the 'bind' argument in create_all if possible, or just mock lifespan.
    # Simpler: just set the dependency and use TestClient with lifespan disabled context logic if possible?
    # No, FastAPI TestClient runs lifespan by default.
    
    # Monkeypatch the engine used in main.py lifespan if it was imported directly
    # Since main.py imports engine from app.database, we cannot easily change it after import.
    # However, we can mock the lifespan function or context.
    
    # Effective workaround: Context manager that does nothing for lifespan in tests
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def mock_lifespan(app: FastAPI):
        # Create tables on the TEST engine, not the REAL engine
        Base.metadata.create_all(bind=engine)
        yield
        
    app.router.lifespan_context = mock_lifespan

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
