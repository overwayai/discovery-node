# app/db/repositories/organization_repository.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.organization import Organization
from app.db.models.category import Category
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

class OrganizationRepository:
    """Repository for CRUD operations on Organization model"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def get_by_id(self, org_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        return self.db_session.query(Organization).filter(Organization.id == org_id).first()
    
    def get_by_urn(self, urn: str) -> Optional[Organization]:
        """Get organization by CMP URN"""
        return self.db_session.query(Organization).filter(Organization.urn == urn).first()
    
    def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name"""
        return self.db_session.query(Organization).filter(Organization.name == name).first()
    
    def list(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """List organizations with pagination"""
        return self.db_session.query(Organization).offset(skip).limit(limit).all()
    
    def create(self, org_data: OrganizationCreate) -> Organization:
        """Create a new organization"""
        # Handle categories separately
        category_ids = org_data.category_ids or []
        
        # Create dict without category_ids for SQLAlchemy model
        org_dict = org_data.model_dump(exclude={"category_ids"})
        
        # Create new Organization model instance
        db_org = Organization(**org_dict)
        
        # Add to session
        self.db_session.add(db_org)
        
        # Add categories if provided
        if category_ids:
            categories = self.db_session.query(Category).filter(Category.id.in_(category_ids)).all()
            db_org.categories = categories
        
        # Commit changes
        self.db_session.commit()
        self.db_session.refresh(db_org)
        
        return db_org
    
    def update(self, org_id: UUID, org_data: OrganizationUpdate) -> Optional[Organization]:
        """Update an existing organization"""
        db_org = self.get_by_id(org_id)
        
        if not db_org:
            return None
        
        # Handle categories separately
        category_ids = None
        if "category_ids" in org_data.model_dump(exclude_unset=True):
            category_ids = org_data.category_ids
        
        # Update model with data from Pydantic model (excluding category_ids)
        org_data_dict = org_data.model_dump(exclude={"category_ids"}, exclude_unset=True)
        for key, value in org_data_dict.items():
            setattr(db_org, key, value)
        
        # Update categories if provided
        if category_ids is not None:
            categories = self.db_session.query(Category).filter(Category.id.in_(category_ids)).all()
            db_org.categories = categories
        
        # Commit changes
        self.db_session.commit()
        self.db_session.refresh(db_org)
        
        return db_org
    
    def delete(self, org_id: UUID) -> bool:
        """Delete an organization by ID"""
        db_org = self.get_by_id(org_id)
        
        if not db_org:
            return False
        
        self.db_session.delete(db_org)
        self.db_session.commit()
        
        return True
    
    def list_by_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[Organization]:
        """List organizations by category"""
        return self.db_session.query(Organization)\
            .join(Organization.categories)\
            .filter(Category.id == category_id)\
            .offset(skip).limit(limit).all()