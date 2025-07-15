# app/services/brand_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.db.repositories.brand_repository import BrandRepository
from app.services.category_service import CategoryService
from app.schemas.brand import BrandCreate, BrandUpdate, BrandInDB


class BrandService:
    """Service for brand-related business logic"""

    def __init__(self, db_session):
        self.brand_repo = BrandRepository(db_session)
        self.category_service = CategoryService(db_session)

    def get_brand(self, brand_id: UUID) -> Optional[BrandInDB]:
        """Get brand by ID"""
        brand = self.brand_repo.get_by_id(brand_id)
        if not brand:
            return None
        return BrandInDB.model_validate(brand)

    def get_by_urn(self, urn: str) -> Optional[BrandInDB]:
        """Get brand by URN"""
        brand = self.brand_repo.get_by_urn(urn)
        if not brand:
            return None
        return BrandInDB.model_validate(brand)

    def get_by_name(self, name: str) -> Optional[BrandInDB]:
        """Get brand by name (searches across all organizations)"""
        # Search across all brands for the given name
        brands = self.brand_repo.list(
            0, 1000
        )  # Get all brands (adjust limit as needed)
        for brand in brands:
            if brand.name == name:
                return BrandInDB.model_validate(brand)
        return None

    def list_brands(self, skip: int = 0, limit: int = 100) -> List[BrandInDB]:
        """List brands with pagination"""
        brands = self.brand_repo.list(skip, limit)
        return [BrandInDB.model_validate(brand) for brand in brands]

    def list_by_organization(
        self, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[BrandInDB]:
        """List brands by organization"""
        brands = self.brand_repo.list_by_organization(organization_id, skip, limit)
        return [BrandInDB.model_validate(brand) for brand in brands]

    def create_brand(self, brand_data: BrandCreate) -> BrandInDB:
        """Create a new brand"""
        # Additional business logic/validation could go here
        brand = self.brand_repo.create(brand_data)
        return BrandInDB.model_validate(brand)

    def update_brand(
        self, brand_id: UUID, brand_data: BrandUpdate
    ) -> Optional[BrandInDB]:
        """Update an existing brand"""
        brand = self.brand_repo.update(brand_id, brand_data)
        if not brand:
            return None
        return BrandInDB.model_validate(brand)

    def delete_brand(self, brand_id: UUID) -> bool:
        """Delete a brand by ID"""
        return self.brand_repo.delete(brand_id)

    def process_brand(self, brand_data: Dict[str, Any], organization_id: UUID) -> UUID:
        """
        Process brand data from the CMP brand registry.
        Creates or updates the brand in the database.
        Returns the brand ID.
        """
        # Extract brand ID from the identifier
        brand_id = None
        brand_urn = None
        if "identifier" in brand_data and "value" in brand_data["identifier"]:
            brand_urn = brand_data["identifier"]["value"]
            existing_brand = self.brand_repo.get_by_urn(brand_urn)
            if existing_brand:
                brand_id = existing_brand.id

        # Process categories if included
        category_ids = []
        if "cmp:category" in brand_data and brand_data["cmp:category"]:
            category_slugs = brand_data["cmp:category"]
            category_ids = self.category_service.get_or_create_categories(
                category_slugs
            )

        # Prepare brand data
        brand_create_data = BrandCreate(
            name=brand_data.get("name", ""),
            logo_url=brand_data.get("logo", ""),
            urn=brand_urn,
            organization_id=organization_id,
            raw_data=brand_data,  # Store the full JSON for reference
            category_ids=category_ids,
        )

        # Create or update the brand
        if brand_id:
            brand_update = BrandUpdate(**brand_create_data.model_dump())
            updated_brand = self.brand_repo.update(brand_id, brand_update)
            return updated_brand.id
        else:
            new_brand = self.brand_repo.create(brand_create_data)
            return new_brand.id

    def list_by_category(
        self, category_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[BrandInDB]:
        """List brands by category"""
        brands = self.brand_repo.list_by_category(category_id, skip, limit)
        return [BrandInDB.model_validate(brand) for brand in brands]
