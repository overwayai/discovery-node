# app/db/repositories/product_group_repository.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.product_group import ProductGroup
from app.db.models.category import Category
from app.schemas.product_group import ProductGroupCreate, ProductGroupUpdate


class ProductGroupRepository:
    """Repository for CRUD operations on ProductGroup model"""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_id(self, product_group_id: UUID) -> Optional[ProductGroup]:
        """Get product group by ID"""
        return (
            self.db_session.query(ProductGroup)
            .filter(ProductGroup.id == product_group_id)
            .first()
        )

    def get_by_urn(self, urn: str) -> Optional[ProductGroup]:
        """Get product group by CMP URN"""
        return (
            self.db_session.query(ProductGroup).filter(ProductGroup.urn == urn).first()
        )

    def get_by_product_group_id(self, product_group_id: str) -> Optional[ProductGroup]:
        """Get product group by external product group ID"""
        return (
            self.db_session.query(ProductGroup)
            .filter(ProductGroup.product_group_id == product_group_id)
            .first()
        )

    def list(self, skip: int = 0, limit: int = 100) -> List[ProductGroup]:
        """List product groups with pagination"""
        return self.db_session.query(ProductGroup).offset(skip).limit(limit).all()

    def list_by_brand(
        self, brand_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ProductGroup]:
        """List product groups by brand"""
        return (
            self.db_session.query(ProductGroup)
            .filter(ProductGroup.brand_id == brand_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_category(
        self, category: str, skip: int = 0, limit: int = 100
    ) -> List[ProductGroup]:
        """List product groups by category string"""
        return (
            self.db_session.query(ProductGroup)
            .filter(ProductGroup.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_organization(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ProductGroup]:
        """List product groups by organization"""
        return (
            self.db_session.query(ProductGroup)
            .filter(ProductGroup.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, product_group_data: ProductGroupCreate) -> ProductGroup:
        """Create a new product group"""
        # No more category_ids or association table logic needed
        product_group_dict = product_group_data.model_dump(exclude={"category"})
        db_product_group = ProductGroup(**product_group_dict)
        self.db_session.add(db_product_group)
        self.db_session.commit()
        self.db_session.refresh(db_product_group)
        return db_product_group

    def update(
        self, product_group_id: UUID, product_group_data: ProductGroupUpdate
    ) -> Optional[ProductGroup]:
        """Update an existing product group"""
        db_product_group = self.get_by_id(product_group_id)
        if not db_product_group:
            return None
        product_group_data_dict = product_group_data.model_dump(
            exclude_unset=True, exclude={"category"}
        )
        for key, value in product_group_data_dict.items():
            setattr(db_product_group, key, value)
        self.db_session.commit()
        self.db_session.refresh(db_product_group)
        return db_product_group

    def delete(self, product_group_id: UUID) -> bool:
        """Delete a product group by ID"""
        db_product_group = self.get_by_id(product_group_id)

        if not db_product_group:
            return False

        self.db_session.delete(db_product_group)
        self.db_session.commit()

        return True

    def list_by_category_id(
        self, category_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ProductGroup]:
        """List product groups by category ID (using category_id column)"""
        return (
            self.db_session.query(ProductGroup)
            .filter(ProductGroup.category_id == category_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
