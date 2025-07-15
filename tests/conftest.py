# tests/conftest.py
import pytest
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import alembic.config
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(".env.test", override=True)

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from app.db.base import Base
from app.services.organization_service import OrganizationService
from app.services.brand_service import BrandService
from app.services.category_service import CategoryService

# Test database URL - use a separate PostgreSQL database for testing
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:admin@localhost:5432/cmp_discovery_test"
)

if "cmp_discovery_test" not in TEST_DATABASE_URL:
    raise RuntimeError(f"TEST_DATABASE_URL is not using the test DB! Value: {TEST_DATABASE_URL}")

@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL)

    # Set environment variable for migrations
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    # Run Alembic downgrade to base, then upgrade to head
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = alembic.config.Config(str(alembic_ini_path.resolve()))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    try:
        alembic.command.downgrade(alembic_cfg, "base")
        alembic.command.upgrade(alembic_cfg, "head")
    except Exception as e:
        raise

    yield engine

    # No need to drop tables here; next test will reset schema

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = Session()
    
    yield session
    
    # Roll back transaction to undo any changes
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def organization_service(db_session):
    """Create an organization service for testing."""
    return OrganizationService(db_session)

@pytest.fixture(scope="function")
def brand_service(db_session):
    """Create a brand service for testing."""
    return BrandService(db_session)

@pytest.fixture(scope="function")
def category_service(db_session):
    """Create a category service for testing."""
    return CategoryService(db_session)

@pytest.fixture(scope="function")
def test_organization_data():
    """Sample organization data for testing."""
    return {
        "@context": {
            "schema": "https://schema.org",
            "cmp": "https://schema.commercemesh.ai/ns#"
        },
        "@type": "Organization",
        "name": "Acme Corporation",
        "description": "Acme Corporation is a leading provider of innovative solutions.",
        "url": "https://acme-corp.example.com",
        "logo": "https://example.com/assets/acme-logo.png",
        "brand": [
            {
                "@type": "Brand",
                "name": "WidgetCo",
                "logo": "https://example.com/assets/widgetco-logo.png",
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "cmp:brandId",
                    "value": "urn:cmp:brand:129a4567-e89b-12d3-a456-426614174000"
                }
            },
            {
                "@type": "Brand",
                "name": "GizmoWorks",
                "logo": "https://example.com/assets/gizmoworks-logo.png",
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "cmp:brandId",
                    "value": "urn:cmp:brand:129b4567-e89b-12d3-a456-426614174001"
                }
            }
            # Include more brands if needed
        ],
        "sameAs": [
            "https://www.linkedin.com/company/acme-corp",
            "https://twitter.com/acme_corp"
        ],
        "cmp:category": ["electronics", "tools", "gadgets"],
        "cmp:productFeed": {
            "@type": "DataFeed",
            "url": "https://acme-corp.example.com/feeds/products.json"
        },
        "identifier": {
            "@type": "PropertyValue",
            "propertyID": "cmp:orgId",
            "value": "urn:cmp:orgid:123e4667-e89b-12d3-a456-426614174000"
        }
    }