# app/services/product_group_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from app.db.repositories.product_group_repository import ProductGroupRepository
from app.services.category_service import CategoryService
from app.schemas.product_group import (
    ProductGroupCreate,
    ProductGroupUpdate,
    ProductGroupInDB,
)

logger = logging.getLogger(__name__)


class ProductGroupService:
    """Service for product group-related business logic"""

    def __init__(self, db_session):
        self.product_group_repo = ProductGroupRepository(db_session)
        self.category_service = CategoryService(db_session)

    def get_product_group(self, product_group_id: UUID) -> Optional[ProductGroupInDB]:
        """Get product group by ID"""
        product_group = self.product_group_repo.get_by_id(product_group_id)
        if not product_group:
            return None
        return ProductGroupInDB.model_validate(product_group)

    def get_by_urn(self, urn: str) -> Optional[ProductGroupInDB]:
        """Get product group by URN"""
        product_group = self.product_group_repo.get_by_urn(urn)
        if not product_group:
            return None
        return ProductGroupInDB.model_validate(product_group)

    def get_by_product_group_id(
        self, product_group_id: str
    ) -> Optional[ProductGroupInDB]:
        """Get product group by external product group ID"""
        product_group = self.product_group_repo.get_by_product_group_id(
            product_group_id
        )
        if not product_group:
            return None
        return ProductGroupInDB.model_validate(product_group)

    def list_product_groups(
        self, skip: int = 0, limit: int = 100
    ) -> List[ProductGroupInDB]:
        """List product groups with pagination"""
        product_groups = self.product_group_repo.list(skip, limit)
        return [ProductGroupInDB.model_validate(pg) for pg in product_groups]

    def list_by_brand(
        self, brand_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ProductGroupInDB]:
        """List product groups by brand"""
        product_groups = self.product_group_repo.list_by_brand(brand_id, skip, limit)
        return [ProductGroupInDB.model_validate(pg) for pg in product_groups]

    def create_product_group(
        self, product_group_data: ProductGroupCreate
    ) -> ProductGroupInDB:
        """Create a new product group"""
        # Business logic validation
        existing = self.product_group_repo.get_by_urn(product_group_data.urn)
        if existing:
            logger.warning(
                f"Product group with URN {product_group_data.urn} already exists"
            )
            # Could raise an exception here, or update the existing product group

        # Create the product group
        product_group = self.product_group_repo.create(product_group_data)
        return ProductGroupInDB.model_validate(product_group)
    
    def create_product_group_from_jsonld(self, jsonld_data: Dict[str, Any], organization_id: UUID) -> ProductGroupInDB:
        """
        Create a product group from JSON-LD data, handling brand and category creation
        
        This method handles:
        - Brand creation/lookup (using provided URN or generating one)
        - Category creation/lookup
        - URN generation if not provided
        """
        from app.services.brand_service import BrandService
        from app.services.organization_service import OrganizationService
        from app.core.urn_generator import generate_brand_urn, generate_product_group_urn
        
        # Get organization for URN generation
        from app.db.base import get_db_session
        org_service = OrganizationService(self.db_session)
        organization = org_service.get_organization(organization_id)
        
        # Handle brand
        brand_id = None
        brand_data = jsonld_data.get("brand")
        if brand_data and isinstance(brand_data, dict):
            brand_service = BrandService(self.db_session)
            
            # Extract brand URN from identifier if provided
            brand_urn = None
            if "identifier" in brand_data and isinstance(brand_data["identifier"], dict):
                brand_urn = brand_data["identifier"].get("value")
            
            # Generate URN if not provided
            if not brand_urn:
                brand_urn = generate_brand_urn(brand_data.get("name", ""), organization.urn)
            
            # Check if brand exists
            existing_brand = brand_service.get_by_urn(brand_urn)
            if existing_brand:
                brand_id = existing_brand.id
            else:
                # Create brand
                from app.schemas.brand import BrandCreate
                brand_create = BrandCreate(
                    name=brand_data.get("name", ""),
                    urn=brand_urn,
                    organization_id=organization_id
                )
                new_brand = brand_service.create_brand(brand_create)
                brand_id = new_brand.id
        else:
            # No brand provided - use organization as default brand
            brand_service = BrandService(self.db_session)
            default_brand_name = organization.name
            brand_urn = generate_brand_urn(default_brand_name, organization.urn)
            
            existing_brand = brand_service.get_by_urn(brand_urn)
            if existing_brand:
                brand_id = existing_brand.id
            else:
                from app.schemas.brand import BrandCreate
                brand_create = BrandCreate(
                    name=default_brand_name,
                    urn=brand_urn,
                    organization_id=organization_id
                )
                new_brand = brand_service.create_brand(brand_create)
                brand_id = new_brand.id
        
        # Handle category
        category_name = jsonld_data.get("category", "uncategorized")
        category = self.category_service.get_or_create_by_name(category_name)
        
        # Generate URN if not provided
        pg_urn = jsonld_data.get("@id")
        if not pg_urn:
            product_group_id = jsonld_data.get("productGroupID", "")
            pg_urn = generate_product_group_urn(product_group_id, organization.urn, brand_urn)
            jsonld_data["@id"] = pg_urn
        
        # Parse JSON-LD to ProductGroupCreate schema
        from app.utils import formatters
        pg_create = formatters.parse_jsonld_to_product_group_create(
            jsonld_data,
            organization_id,
            brand_id,
            category.id
        )
        
        # Create the product group
        return self.create_product_group(pg_create)

    def update_product_group(
        self, product_group_id: UUID, product_group_data: ProductGroupUpdate
    ) -> Optional[ProductGroupInDB]:
        """Update an existing product group"""
        # Business logic validation
        if product_group_data.urn:
            existing = self.product_group_repo.get_by_urn(product_group_data.urn)
            if existing and existing.id != product_group_id:
                logger.warning(
                    f"Another product group with URN {product_group_data.urn} already exists"
                )
                # Could raise an exception here

        # Update the product group
        product_group = self.product_group_repo.update(
            product_group_id, product_group_data
        )
        if not product_group:
            return None
        return ProductGroupInDB.model_validate(product_group)

    def delete_product_group(self, product_group_id: UUID) -> bool:
        """Delete a product group by ID"""
        return self.product_group_repo.delete(product_group_id)

    def process_product_group(
        self, product_group_data: Dict[str, Any], brand_id: UUID, organization_id: UUID
    ) -> UUID:
        """
        Process product group data from the CMP product feed.
        Creates or updates the product group in the database.
        Returns the product group ID.
        """
        # Extract URN and product group ID
        urn = product_group_data.get("@id", "")

        if not urn:
            logger.error("Product group data missing required @id field")
            raise ValueError("Product group data missing required @id field")

        # Check if product group already exists
        product_group_id = None
        existing_product_group = self.product_group_repo.get_by_urn(urn)
        if existing_product_group:
            product_group_id = existing_product_group.id

        # Extract varies_by from the data
        varies_by = product_group_data.get("variesBy", [])
        if not varies_by:
            logger.warning(f"Product group {urn} is missing variesBy field")
            varies_by = []

        # Normalize varies_by to list if it's a string
        if isinstance(varies_by, str):
            varies_by = [varies_by]

        # Extract category information
        category_name = product_group_data.get("category", "")
        category = self.category_service.get_or_create_by_name(category_name)
        category_id = category.id

        # Create product group data
        product_group_create_data = ProductGroupCreate(
            name=product_group_data.get("name", ""),
            description=product_group_data.get("description", ""),
            url=product_group_data.get("url", ""),
            category=category_name,
            product_group_id=product_group_data.get("productGroupID", ""),
            varies_by=varies_by,
            brand_id=brand_id,
            urn=urn,
            raw_data=product_group_data,
            category_id=category_id,
            organization_id=organization_id,
        )

        # Create or update the product group
        if product_group_id:
            product_group_update = ProductGroupUpdate(
                **product_group_create_data.model_dump()
            )
            updated_product_group = self.product_group_repo.update(
                product_group_id, product_group_update
            )
            return updated_product_group.id
        else:
            new_product_group = self.product_group_repo.create(
                product_group_create_data
            )
            return new_product_group.id

    def _slugify(self, text: str) -> str:
        """
        Convert a string to a slug format.
        For example: "Electronics & Computers" -> "electronics-computers"
        """
        # Very basic implementation - for production, use a proper slugify library
        return text.lower().replace(" ", "-").replace("&", "").replace("_", "-")

    def bulk_process_product_groups(
        self, product_groups_data: List[Dict[str, Any]], brand_id: UUID, organization_id: UUID, batch_size: int = 1000
    ) -> List[ProductGroupInDB]:
        """
        Bulk process product groups from CMP product feed.
        Returns list of created/updated product groups.
        """
        product_group_creates = []
        
        for pg_data in product_groups_data:
            # Extract URN
            urn = pg_data.get("@id", "")
            if not urn:
                logger.warning("Skipping product group without @id")
                continue
            
            # Extract varies_by
            varies_by = pg_data.get("variesBy", [])
            if isinstance(varies_by, str):
                varies_by = [varies_by]
            
            # Extract category
            category_name = pg_data.get("category", "")
            category = self.category_service.get_or_create_by_name(category_name)
            
            # Create product group object
            product_group_create = ProductGroupCreate(
                name=pg_data.get("name", ""),
                description=pg_data.get("description", ""),
                url=pg_data.get("url", ""),
                category=category_name,
                product_group_id=pg_data.get("productGroupID", ""),
                varies_by=varies_by,
                brand_id=brand_id,
                urn=urn,
                raw_data=pg_data,
                category_id=category.id,
                organization_id=organization_id,
            )
            product_group_creates.append(product_group_create)
        
        # Bulk upsert
        upserted = self.product_group_repo.bulk_upsert(product_group_creates, batch_size)
        return [ProductGroupInDB.model_validate(pg) for pg in upserted]
    
