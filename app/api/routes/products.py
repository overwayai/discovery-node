from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.services.search_service import SearchService
from app.schemas.product import ProductSearchResponse
from app.db.base import get_db_session
from sqlalchemy.orm import Session
from typing import List
import logging

logger = logging.getLogger(__name__)

    
products_router = APIRouter(
    prefix="/v1",
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

@products_router.get(
    "/products",
    response_model=ProductSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for products",
    description="Search for products using a natural language query. Returns a list of relevant products ranked by similarity score.",
    response_description="List of products matching the search query",
    responses={
        200: {
            "description": "Successful product search",
            "model": ProductSearchResponse
        },
        400: {
            "description": "Invalid search query",
            "content": {
                "application/json": {
                    "example": {"detail": "Search query cannot be empty"}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Search service error"}
                }
            }
        }
    }
)
async def get_products(
    q: str = Query(
        default="James Cameron",
        description="Search query for finding products",
        min_length=1,
        max_length=500,
        example="wireless headphones"
    ),
    db: Session = Depends(get_db_session)
) -> ProductSearchResponse:
    """
    Search for products using natural language queries.
    
    The search uses hybrid search combining dense and sparse vectors for optimal results.
    
    - **q**: The search query (e.g., "gaming laptop", "wireless earbuds", "running shoes")
    
    Returns a list of products sorted by relevance score.
    """
    try:
        if not q or not q.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
            
        search_service = SearchService(db)
        results = search_service.search_products(q)
        
        logger.info(f"🔍 DEBUG: API received {len(results)} results")
        logger.info(f"🔍 DEBUG: First result type: {type(results[0]) if results else 'None'}")
        logger.info(f"🔍 DEBUG: First result: {results[0] if results else 'None'}")
        
        # Handle both SearchResult objects and dictionaries
        item_list_elements = []
        for i, result in enumerate(results):
            logger.info(f"🔍 DEBUG: Processing result {i}: type={type(result)}")
            
            # Extract product data
            if hasattr(result, 'id'):
                # SearchResult object
                product_id = result.id
                product_name = result.product_name
                product_brand = result.product_brand
                product_category = result.product_category
                product_price = result.product_price
                product_offers = result.product_offers
                product_description = result.product_description
                product_url = result.product_url
                product_media = result.product_media
                score = result.score
            else:
                # Dictionary
                product_id = result.get('id')
                product_name = result.get('product_name')
                product_brand = result.get('product_brand')
                product_category = result.get('product_category')
                product_price = result.get('product_price')
                product_offers = result.get('product_offers')
                product_description = result.get('product_description')
                product_url = result.get('product_url')
                product_media = result.get('product_media')
                score = result.get('score')
            
            # Create brand object
            brand_obj = {
                "@type": "Brand",
                "name": product_brand
            } if product_brand else None
            
            # Create image array
            images = []
            if product_media:
                for media in product_media:
                    if isinstance(media, dict) and media.get('url'):
                        image_obj = {
                            "@type": "ImageObject",
                            "url": media['url']
                        }
                        # Add optional dimensions if available
                        if 'width' in media:
                            image_obj['width'] = media['width']
                        if 'height' in media:
                            image_obj['height'] = media['height']
                        if 'encodingFormat' in media:
                            image_obj['encodingFormat'] = media['encodingFormat']
                        images.append(image_obj)
            
            # Create @cmp:media array (separate from images)
            cmp_media = []
            if product_media:
                for media in product_media:
                    if isinstance(media, dict) and media.get('url'):
                        # Only include non-image media types in @cmp:media
                        encoding_format = media.get('encodingFormat', '').lower()
                        media_type = media.get('type', 'VideoObject')
                        
                        # Skip if it's an image format
                        if encoding_format.startswith('image/'):
                            continue
                            
                        # Include video and other non-image media
                        if encoding_format.startswith('video/') or encoding_format.startswith('audio/') or media_type != 'ImageObject':
                            media_obj = {
                                "@type": media_type,
                                "url": media['url']
                            }
                            if 'encodingFormat' in media:
                                media_obj['encodingFormat'] = media['encodingFormat']
                            cmp_media.append(media_obj)
            
            # Create offers array with enhanced fields
            offers = []
            if product_offers:
                for offer in product_offers:
                    offer_obj = {
                        "@type": "Offer",
                        "price": offer['price'],
                        "priceCurrency": offer['currency'],
                        "availability": f"https://schema.org/{offer['availability']}",
                        "seller": {
                            "@type": "Organization",
                            "@id": f"urn:cmp:brand:{offer['seller_id']}"
                        }
                    }
                    
                    # Add optional offer fields if available in the database
                    if 'price_valid_until' in offer:
                        offer_obj["priceValidUntil"] = offer['price_valid_until']
                    if 'inventory_level' in offer:
                        offer_obj["inventoryLevel"] = {
                            "@type": "QuantitativeValue",
                            "value": offer['inventory_level']
                        }
                    if 'shipping_speed_tier' in offer:
                        offer_obj["shippingSpeedTier"] = offer['shipping_speed_tier']
                    if 'est_delivery_min_days' in offer:
                        offer_obj["estDeliveryMinDays"] = offer['est_delivery_min_days']
                    if 'est_delivery_max_days' in offer:
                        offer_obj["estDeliveryMaxDays"] = offer['est_delivery_max_days']
                    if 'warranty_months' in offer:
                        offer_obj["warrantyMonths"] = offer['warranty_months']
                    if 'return_window_days' in offer:
                        offer_obj["returnWindowDays"] = offer['return_window_days']
                    if 'gift_wrap' in offer:
                        offer_obj["giftWrap"] = offer['gift_wrap']
                    
                    offers.append(offer_obj)
            
            # Create product item
            product_item = {
                "@type": "Product",
                "@id": f"urn:cmp:sku:{product_id}",
                "name": product_name,
                "description": product_description,
                "category": product_category,
                "url": product_url,
                "cmp:searchScore": score
            }
            
            # Add SKU if available (extract from product_id or URL)
            if product_url and 'variant=' in product_url:
                sku = product_url.split('variant=')[1].split('&')[0]
                product_item["sku"] = sku
            
            # Add optional fields
            if brand_obj:
                product_item["brand"] = brand_obj
            if images:
                product_item["image"] = images
            if cmp_media:
                product_item["@cmp:media"] = cmp_media
            if offers:
                product_item["offers"] = offers
            
            # Add isVariantOf if we have product group info
            # This would need to be populated from the database enrichment
            if hasattr(result, 'product_group') and result.product_group:
                product_item["isVariantOf"] = {
                    "@type": "ProductGroup",
                    "@id": f"urn:cmp:product:{result.product_group.id}",
                    "name": result.product_group.name
                }
            
            # Add additionalProperty if we have variant attributes
            if hasattr(result, 'metadata') and result.metadata:
                additional_properties = []
                for key, value in result.metadata.items():
                    if key not in ['price', 'availability', 'brand', 'category']:
                        additional_properties.append({
                            "@type": "PropertyValue",
                            "name": key,
                            "value": value
                        })
                if additional_properties:
                    product_item["additionalProperty"] = additional_properties
            
            # Create list item
            list_item = {
                "@type": "ListItem",
                "position": i + 1,
                "item": product_item
            }
            
            item_list_elements.append(list_item)
        
        # Create the final response
        from datetime import datetime, timezone
        
        response_data = {
            "itemListElement": item_list_elements,
            "cmp_totalResults": len(results),
            "cmp_nodeVersion": "v1.0.0",
            "datePublished": datetime.now(timezone.utc).isoformat()
        }
        
        # Create the ProductSearchResponse object
        response = ProductSearchResponse(**response_data)
        
        logger.info(f"🔍 DEBUG: Returning {len(item_list_elements)} formatted results")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during product search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service error"
        )