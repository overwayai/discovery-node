# app/ingestors/handlers/registry.py
"""
Handler for brand registry data.
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.ingestors.base import validate_json, validate_cmp_data, ProcessingError
from app.services.organization_service import OrganizationService
from app.services.brand_service import BrandService
from app.services.category_service import CategoryService

logger = logging.getLogger(__name__)


class RegistryHandler:
    """
    Handler for processing brand registry data.
    """

    def __init__(self, db_session):
        """
        Initialize the handler with database session.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.organization_service = OrganizationService(db_session)
        self.brand_service = BrandService(db_session)
        self.category_service = CategoryService(db_session)

    def process(self, data: str) -> Dict[str, Any]:
        """
        Process raw registry data.

        Args:
            data: Raw registry data as string

        Returns:
            Processing result

        Raises:
            ProcessingError: If data cannot be processed
        """
        logger.info("Processing registry data")
        print("Processing registry data")

        try:
            # Parse and validate JSON
            json_data = validate_json(data)
            validate_cmp_data(json_data, "registry")

            # Process organization
            org_id = self.organization_service.process_organization(json_data)

            # Get number of brands processed
            brands_processed = 0

            # Check if brand field exists and is a list
            if "brand" in json_data:
                if isinstance(json_data["brand"], list):
                    for brand in json_data["brand"]:
                        self.brand_service.process_brand(brand, org_id)
                        brands_processed += 1
                else:
                    # Single brand
                    self.brand_service.process_brand(json_data["brand"], org_id)
                    brands_processed += 1

            return {
                "organization_id": str(org_id),
                "brands_processed": brands_processed,
                "categories_processed": len(json_data.get("cmp:category", [])),
            }
        except Exception as e:
            logger.exception(f"Error processing registry data: {str(e)}")
            raise ProcessingError(f"Error processing registry data: {str(e)}")
