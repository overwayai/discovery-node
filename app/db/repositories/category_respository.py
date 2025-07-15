# app/db/repositories/category_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryRepository:
    """Repository for CRUD operations on Category model"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """Get category by ID"""
        return self.db_session.query(Category).filter(Category.id == category_id).first()
    
    def get_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug"""
        return self.db_session.query(Category).filter(Category.slug == slug).first()
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name (case-insensitive, space-stripped comparison)"""
        if not name:
            return None
        
        # Normalize the input name
        normalized_name = name.strip().lower()
        
        # Use SQLAlchemy func to perform case-insensitive comparison
        from sqlalchemy import func
        return self.db_session.query(Category).filter(
            func.lower(func.trim(Category.name)) == normalized_name
        ).first()
    
    def list(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """List categories with pagination"""
        return self.db_session.query(Category).offset(skip).limit(limit).all()
    
    def create(self, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        # Convert Pydantic model to dict
        category_dict = category_data.model_dump()
        
        # Normalize name: strip spaces and convert to lowercase
        if 'name' in category_dict and category_dict['name']:
            category_dict['name'] = category_dict['name'].strip().lower()
        
        # Normalize slug: strip spaces and convert to lowercase
        if 'slug' in category_dict and category_dict['slug']:
            category_dict['slug'] = category_dict['slug'].strip().lower()
        
        # Create new Category model instance
        db_category = Category(**category_dict)
        
        # Add to session and commit
        self.db_session.add(db_category)
        self.db_session.commit()
        self.db_session.refresh(db_category)
        
        return db_category
    
    def update(self, category_id: UUID, category_data: CategoryUpdate) -> Optional[Category]:
        """Update an existing category"""
        db_category = self.get_by_id(category_id)
        
        if not db_category:
            return None
        
        # Update model with data from Pydantic model
        category_data_dict = category_data.model_dump(exclude_unset=True)
        for key, value in category_data_dict.items():
            setattr(db_category, key, value)
        
        # Commit changes
        self.db_session.commit()
        self.db_session.refresh(db_category)
        
        return db_category
    
    def delete(self, category_id: UUID) -> bool:
        """Delete a category by ID"""
        db_category = self.get_by_id(category_id)
        
        if not db_category:
            return False
        
        self.db_session.delete(db_category)
        self.db_session.commit()
        
        return True
    
    def get_or_create(self, slug: str, name: str, description: str = None) -> Category:
        """Get a category by slug or create it if it doesn't exist"""
        # Normalize slug and name before lookup/creation
        normalized_slug = slug.strip().lower() if slug else ""
        normalized_name = name.strip().lower() if name else ""
        
        category = self.get_by_slug(normalized_slug)
        if category:
            return category
        
        # Create new category with normalized values
        category_data = CategoryCreate(
            slug=normalized_slug,
            name=normalized_name,
            description=description
        )
        return self.create(category_data)