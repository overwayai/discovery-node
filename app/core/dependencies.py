from app.db.base import SessionLocal
from app.services.search_service import SearchService
from app.services.product_service import ProductService
from app.db.repositories.product_repository import ProductRepository
from app.db.repositories.vector_repository import VectorRepository

def get_search_service() -> SearchService:
    """Get search service instance with DB session"""
    db_session = SessionLocal()
    return SearchService(db_session=db_session)

def get_product_service() -> ProductService:
    """Get product service instance with dependencies"""
    db_session = SessionLocal()
    return ProductService(db_session=db_session)