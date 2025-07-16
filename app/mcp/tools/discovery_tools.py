import logging
import json
from typing import List

import mcp.types as types
from mcp.server.lowlevel import Server

from app.core.logging import get_logger
from app.services.search_service import SearchService
from app.services.product_service import ProductService
from app.utils.formatters import format_product_search_response

logger = get_logger(__name__)


def register_discovery_tools(
    app: Server,
    search_service: SearchService,
    product_service: ProductService
) -> None:
    """Register all discovery-related MCP tools"""
    
    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="search-products",
                description="Search for products using hybrid vector search",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for products"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10
                        },
                        "org_id": {
                            "type": "string",
                            "description": "Organization ID to filter results (optional)"
                        }
                    }
                }
            ),
            types.Tool(
                name="get-product-details",
                description="Get detailed information about a specific product",
                inputSchema={
                    "type": "object",
                    "required": ["product_id"],
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID to retrieve details for"
                        }
                    }
                }
            ),
            types.Tool(
                name="get-products-by-category",
                description="Get products filtered by category",
                inputSchema={
                    "type": "object",
                    "required": ["category"],
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Product category to filter by"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results (default: 20)",
                            "default": 20
                        }
                    }
                }
            )
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
        """Handle tool calls"""
        ctx = app.request_context
        
        try:
            if name == "search-products":
                return _handle_search_products(
                    search_service, arguments, ctx
                )
            elif name == "get-product-details":
                return _handle_get_product_details(
                    product_service, arguments, ctx
                )
            elif name == "get-products-by-category":
                return _handle_get_products_by_category(
                    product_service, arguments, ctx
                )
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )
                ]
        except Exception as e:
            logger.error(f"Error handling tool {name}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )
            ]


def _handle_search_products(
    search_service: SearchService, 
    arguments: dict, 
    ctx
) -> List[types.TextContent]:
    """Handle product search requests"""
    query = arguments["query"]
    limit = arguments.get("limit", 10)
    org_id = arguments.get("org_id")
    
    # Send progress notification
    # Note: We can't use async ctx.session.send_log_message in sync function
    logger.info(f"Searching for products: '{query}'")
    
    # Perform search
    results = search_service.search_products(
        query=query,
        top_k=limit
    )
    
    # Format results
    if not results:
        return [
            types.TextContent(
                type="text",
                text=f"No products found for query: '{query}'"
            )
        ]
    
    response_data = format_product_search_response(results)
    
    # Convert dictionary to JSON string for MCP TextContent
    response_text = json.dumps(response_data, indent=2)
   
    return [
        types.TextContent(
            type="text",
            text=response_text
        )
    ]


def _handle_get_product_details(
    product_service: ProductService,
    arguments: dict,
    ctx
) -> List[types.TextContent]:
    """Handle product details requests"""
    product_id = arguments["product_id"]
    
    logger.info(f"Fetching details for product: {product_id}")
    
    product = product_service.get_product_by_id(product_id)
    
    if not product:
        return [
            types.TextContent(
                type="text",
                text=f"Product not found: {product_id}"
            )
        ]
    
    # Format detailed product information
    details = f"**Product Details**\n\n"
    details += f"**Name:** {product.name}\n"
    details += f"**SKU:** {product.sku or 'N/A'}\n"
    details += f"**Brand:** {product.brand.name if product.brand else 'Unknown'}\n"
    details += f"**Category:** {product.category.name if product.category else 'Unknown'}\n"
    details += f"**Description:** {product.description or 'No description available'}\n"
    details += f"**Price:** ${product.price or 'N/A'}\n"
    
    # Add more details if available
    if product.url:
        details += f"**URL:** {product.url}\n"
    if product.media:
        details += f"**Media:** {len(product.media)} items\n"
    if product.offers:
        details += f"**Offers:** {len(product.offers)} available\n"
    
    return [
        types.TextContent(
            type="text",
            text=details
        )
    ]


def _handle_get_products_by_category(
    product_service: ProductService,
    arguments: dict,
    ctx
) -> List[types.TextContent]:
    """Handle category-based product requests"""
    category = arguments["category"]
    limit = arguments.get("limit", 20)
    
    logger.info(f"Fetching products in category: {category}")
    
    products = product_service.get_products_by_category(
        category=category,
        limit=limit
    )
    
    if not products:
        return [
            types.TextContent(
                type="text",
                text=f"No products found in category: '{category}'"
            )
        ]
    
    # Format category results
    response_text = f"Found {len(products)} products in category '{category}':\n\n"
    for i, product in enumerate(products, 1):
        response_text += f"{i}. **{product.name}**\n"
        response_text += f"   Brand: {product.brand.name if product.brand else 'Unknown'}\n"
        response_text += f"   Price: ${product.price or 'N/A'}\n"
        response_text += f"   ID: {product.id}\n\n"
    
    return [
        types.TextContent(
            type="text",
            text=response_text
        )
    ]