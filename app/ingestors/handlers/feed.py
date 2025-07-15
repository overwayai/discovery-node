# app/ingestors/handlers/feed.py
"""
Handler for product feed data.
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.ingestors.base import validate_json, validate_cmp_data, ProcessingError
from app.services.product_service import ProductService
from app.services.product_group_service import ProductGroupService
from app.services.offer_service import OfferService
from app.services.brand_service import BrandService

logger = logging.getLogger(__name__)


class FeedHandler:
    """
    Handler for processing product feed data.
    """

    def __init__(self, db_session, brand_id: Optional[UUID] = None):
        """
        Initialize the handler with database session.

        Args:
            db_session: SQLAlchemy database session
            brand_id: Optional brand ID to associate products with
        """
        self.db_session = db_session
        self.brand_id = brand_id
        self.product_service = ProductService(db_session)
        self.product_group_service = ProductGroupService(db_session)
        self.offer_service = OfferService(db_session)
        self.brand_service = BrandService(db_session)

    def process(self, data: str) -> Dict[str, Any]:
        """
        Process raw feed data.

        Args:
            data: Raw feed data as string

        Returns:
            Processing result

        Raises:
            ProcessingError: If data cannot be processed
        """
        logger.info("Processing product feed data")
        print("Processing product feed data")

        try:
            # Parse and validate JSON
            json_data = validate_json(data)
            validate_cmp_data(json_data, "feed")

            # Extract items
            items = json_data.get("itemListElement", [])

            # Track processing statistics
            product_groups_processed = 0
            products_processed = 0
            offers_processed = 0

            # Process each item
            for item in items:
                if "item" not in item:
                    logger.warning("Item missing 'item' field, skipping")
                    continue

                item_data = item["item"]
                item_type = item_data.get("@type")

                # Get brand_id for this item (either from constructor or from item data)
                item_brand_id = self._get_brand_id(item_data)

                # Skip items without brand information
                if item_brand_id is None:
                    logger.warning(
                        f"Skipping {item_type} '{item_data.get('name', 'unknown')}' - no brand information"
                    )
                    continue

                if item_type == "ProductGroup":
                    # Process product group
                    print(f"Processing product group: {item_data.get('name')}")
                    # Get the brand object to extract organization_id
                    brand = self.brand_service.get_by_name(
                        item_data.get("brand", {}).get("name")
                    )
                    if not brand:
                        logger.warning(
                            f"Skipping ProductGroup '{item_data.get('name', 'unknown')}' - brand not found"
                        )
                        continue
                    organization_id = brand.organization_id
                    self.product_group_service.process_product_group(
                        item_data, item_brand_id, organization_id
                    )
                    product_groups_processed += 1

                elif item_type == "Product":
                    # Process product
                    print(f"Processing product: {item_data.get('name')}")

                    # Get category name for this product
                    category_name = self._get_category_name(item_data)
                    if category_name is None:
                        logger.warning(
                            f"Skipping product '{item_data.get('name', 'unknown')}' - no category information"
                        )
                        continue

                    # Process product with category information
                    self.product_service.process_product(
                        item_data, item_brand_id, category_name
                    )
                    products_processed += 1

                    # Check for offers
                    if "offers" in item_data:
                        offers_processed += 1

                else:
                    logger.warning(f"Unknown item type: {item_type}")

            return {
                "product_groups_processed": product_groups_processed,
                "products_processed": products_processed,
                "offers_processed": offers_processed,
            }
        except Exception as e:
            logger.exception(f"Error processing feed data: {str(e)}")
            raise ProcessingError(f"Error processing feed data: {str(e)}")

    def _get_brand_id(self, item_data: Dict[str, Any]) -> Optional[UUID]:
        """
        Get brand ID for an item, either from constructor or by looking up brand name.

        Args:
            item_data: The item data containing brand information

        Returns:
            Brand UUID if found, None if brand information is missing
        """
        # If brand_id was provided in constructor, use it
        if self.brand_id:
            return self.brand_id

        # Try to extract brand information from item data
        brand_info = item_data.get("brand")
        brand_name = None

        if brand_info:
            # Extract brand name from item
            brand_name = (
                brand_info.get("name")
                if isinstance(brand_info, dict)
                else str(brand_info)
            )

        # If item doesn't have brand info and it's a Product, try to get brand from product group
        if not brand_name and item_data.get("@type") == "Product":
            product_group_urn = None
            if "isVariantOf" in item_data and "@id" in item_data["isVariantOf"]:
                product_group_urn = item_data["isVariantOf"]["@id"]

            if product_group_urn:
                # Look up the product group to get its brand
                product_group = self.product_group_service.get_by_urn(product_group_urn)
                if product_group and product_group.brand_id:
                    return product_group.brand_id
                else:
                    logger.warning(
                        f"Product {item_data.get('name', 'unknown')} references product group {product_group_urn} but no brand found"
                    )
                    return None

        # If we have a brand name, look it up
        if brand_name:
            try:
                brand = self.brand_service.get_by_name(brand_name)
                if brand:
                    return brand.id
                else:
                    logger.warning(f"Brand '{brand_name}' not found in registry")
                    return None
            except Exception as e:
                logger.error(f"Error looking up brand '{brand_name}': {str(e)}")
                return None

        # No brand information found
        logger.warning(
            f"Item {item_data.get('name', 'unknown')} has no brand information"
        )
        return None

    def _get_category_name(self, item_data: Dict[str, Any]) -> Optional[str]:
        """
        Get category name for an item, either from item data or from product group.

        Args:
            item_data: The item data containing category information

        Returns:
            Category name if found, None if category information is missing
        """
        # Try to extract category information from item data
        category_name = item_data.get("category", "").strip()

        # If item doesn't have category info and it's a Product, try to get category from product group
        if not category_name and item_data.get("@type") == "Product":
            product_group_urn = None
            if "isVariantOf" in item_data and "@id" in item_data["isVariantOf"]:
                product_group_urn = item_data["isVariantOf"]["@id"]

            if product_group_urn:
                # Look up the product group to get its category
                product_group = self.product_group_service.get_by_urn(product_group_urn)
                if product_group and product_group.category:
                    # Get the category name from the relationship
                    category_name = product_group.category.name
                    logger.info(
                        f"Product {item_data.get('name', 'unknown')} using category '{category_name}' from product group {product_group_urn}"
                    )
                else:
                    logger.warning(
                        f"Product {item_data.get('name', 'unknown')} references product group {product_group_urn} but no category found"
                    )
                    return None

        # Return category name if found
        if category_name:
            return category_name

        # No category information found
        logger.warning(
            f"Item {item_data.get('name', 'unknown')} has no category information"
        )
        return None
