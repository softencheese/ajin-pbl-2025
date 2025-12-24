import pytest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from fastapi import FastAPI
from main import app
from scripts.init_db import init_db as seed_data
from app.core.config import settings
import logging

# Use MySQL Test Database
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://ajin_user:ajin_password@db:3306/ajin_rfid_test?charset=utf8mb4"

# Disable echo for cleaner output, use NullPool to avoid connection holding issues in tests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    This fixture:
    1. Drops all tables
    2. Creates all tables
    3. Seeds initial data (using init_db.py)
    4. Yields a session
    5. Cleans up
    """
    # 1 & 2. Reset Tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # 3. Seed Data
    # init_db.py uses its own SessionLocal/engine, we need to make sure 
    # it uses OUR test engine/session or we manually seed here.
    # Since init_db imports engine from app.core.database, we cannot easily patch it 
    # unless we patch sys.modules or refactor init_db.
    # Instead, let's just inspect init_db structure. 
    # It imports SessionLocal from app.core.database.
    
    # Better approach: We can use the logic from init_db functions but pass our db session.
    # Refator init_db.py slightly to accept a db session for main init_db function?
    # Or just copy the calling logic here since we imported functions.
    from scripts.init_db import create_processes, create_items, create_reader_locations, create_lots, create_pallets
    
    db = TestingSessionLocal()
    try:
        # Disable logging for seed to keep output clean
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        
        create_processes(db)
        create_items(db)
        create_reader_locations(db)
        create_lots(db)
        create_pallets(db)
        # db.commit() is called inside these functions
        
        yield db
    finally:
        db.close()
        # Drop tables after test to ensure clean state
        # Base.metadata.drop_all(bind=engine) 

@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    
    # Context manager that does nothing for lifespan in tests 
    # to avoid double DB initialization if main.py does it
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def mock_lifespan(app: FastAPI):
        yield
        
    app.router.lifespan_context = mock_lifespan

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
