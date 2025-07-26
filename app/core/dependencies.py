from contextlib import contextmanager
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.services.search.factory import SearchServiceFactory as SearchFactory
from app.services.product_service import ProductService
from app.db.repositories.product_repository import ProductRepository
from app.db.repositories.vector_repository import VectorRepository

@contextmanager
def get_db_session():
    """Create a database session with proper cleanup"""
    db_session = SessionLocal()
    try:
        yield db_session
    except Exception:
        db_session.rollback()
        raise
    finally:
        db_session.close()

# For MCP server, we need to create services per request to avoid stale sessions
class SearchServiceFactory:
    """Factory for creating SearchService instances with fresh DB sessions"""
    
    def create(self):
        """Create a new SearchService instance with a fresh DB session"""
        db_session = SessionLocal()
        return SearchFactory.create(db_session)
    
    def create_with_cleanup(self):
        """Create SearchService with automatic session cleanup"""
        with get_db_session() as db_session:
            yield SearchFactory.create(db_session)

class ProductServiceFactory:
    """Factory for creating ProductService instances with fresh DB sessions"""
    
    def create(self) -> ProductService:
        """Create a new ProductService instance with a fresh DB session"""
        db_session = SessionLocal()
        return ProductService(db_session=db_session)
    
    def create_with_cleanup(self):
        """Create ProductService with automatic session cleanup"""
        with get_db_session() as db_session:
            yield ProductService(db_session=db_session)

# Keep the original functions for backward compatibility
def get_search_service():
    """Get search service instance with DB session"""
    factory = SearchServiceFactory()
    return factory.create()

def get_product_service() -> ProductService:
    """Get product service instance with dependencies"""
    factory = ProductServiceFactory()
    return factory.create()