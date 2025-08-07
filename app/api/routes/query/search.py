from fastapi import APIRouter, HTTPException, Query, status, Depends, Path, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from app.services.search import SearchServiceFactory
from app.services.product_service import ProductService
from app.schemas.product import ProductSearchResponse, ProductByUrnResponse
from app.db.base import get_db_session
from app.services.cache_service import get_cache_service
from app.core.dependencies import OrganizationId
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from app.utils.formatters import format_product_search_response, format_product_by_urn_response
from app.utils.html_formatter import HTMLFormatter
from app.utils.content_negotiation import should_return_html, get_preferred_content_type
import logging
import urllib.parse

logger = logging.getLogger(__name__)


search_router = APIRouter(
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


@search_router.get(
    "/search",
    response_model=None,  # We'll handle response model based on content type
    status_code=status.HTTP_200_OK,
    summary="Search for products",
    description="Search for products using a natural language query. Returns a list of relevant products ranked by similarity score.",
    response_description="List of products matching the search query",
    responses={
        200: {
            "description": "Successful product search",
            "content": {
                "application/json": {"model": ProductSearchResponse},
                "text/html": {"description": "HTML formatted product list"}
            }
        },
        400: {
            "description": "Invalid search query",
            "content": {
                "application/json": {
                    "example": {"detail": "Search query cannot be empty"}
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"detail": "Search service error"}}
            },
        },
    },
)
@search_router.head(
    "/search",
    response_model=None,
    status_code=status.HTTP_200_OK,
    include_in_schema=False  # HEAD methods usually not shown in docs
)
async def get_products(
    request: Request,
    q: str = Query(
        default="James Cameron",
        description="Search query for finding products",
        min_length=1,
        max_length=500,
        example="wireless headphones",
    ),
    limit: int = Query(
        default=20,
        description="Maximum number of results to return",
        ge=1,
        le=100,
        example=20,
    ),
    skip: int = Query(
        default=0,
        description="Number of results to skip for pagination",
        ge=0,
        example=0,
    ),
    category: Optional[str] = Query(
        default=None,
        description="Filter results by category name",
        example="books",
    ),
    price_max: Optional[float] = Query(
        default=None,
        description="Maximum price filter",
        ge=0,
        example=100.0,
    ),
    organization_id: OrganizationId = None,
    db: Session = Depends(get_db_session),
) -> Union[Response, ProductSearchResponse]:
    """
    Search for products using natural language queries.

    The search uses hybrid search combining dense and sparse vectors for optimal results.

    - **q**: The search query (e.g., "gaming laptop", "wireless earbuds", "running shoes")
    - **limit**: Maximum number of results to return (1-100, default: 20)
    - **skip**: Number of results to skip for pagination (default: 0)
    - **category**: Optional category filter (e.g., "books", "electronics")
    - **price_max**: Optional maximum price filter

    Returns a list of products sorted by relevance score.
    """
    try:
        if not q or not q.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty",
            )

        # Get cache service
        cache_service = get_cache_service()
        
        # Generate cache key and add to response
        cache_key = cache_service.generate_cache_key("search")
        request_id = cache_key.split(":")[-1]  # Extract request ID from key
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if price_max is not None:
            filters["price_max"] = price_max
            
        search_service = SearchServiceFactory.create(db)
        results = search_service.search_products(
            q, 
            top_k=limit, 
            skip=skip,
            filters=filters,
            organization_id=organization_id
        )

        response_data = format_product_search_response(results)
        
        # Add request ID and pagination metadata to response
        response_data["cmp:requestId"] = request_id
        response_data["cmp:skip"] = skip
        response_data["cmp:limit"] = limit
        
        # Add pagination helpers
        if len(results) == limit:
            response_data["cmp:hasNext"] = True
            response_data["cmp:nextSkip"] = skip + limit
        else:
            response_data["cmp:hasNext"] = False
            
        if skip > 0:
            response_data["cmp:hasPrevious"] = True
            response_data["cmp:previousSkip"] = max(0, skip - limit)
        else:
            response_data["cmp:hasPrevious"] = False

        # Cache the response
        cache_service.cache_response(cache_key, response_data)

        # Check if HTML response is preferred
        if should_return_html(request):
            # Format as HTML
            html_formatter = HTMLFormatter(base_url=str(request.base_url).rstrip('/'))
            
            # Add query to context for pagination links
            response_data_with_query = response_data.copy()
            response_data_with_query['query'] = q
            
            html_content = html_formatter.format_response(response_data_with_query, "product_list")
            return HTMLResponse(content=html_content)
        else:
            # Return JSON response
            response = ProductSearchResponse(**response_data)
            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during product search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service error",
        )
