# app/mcp/prompts/discovery_prompts.py
import logging
from typing import List

import mcp.types as types
from mcp.server.lowlevel import Server

from app.core.logging import get_logger

logger = get_logger(__name__)


def register_discovery_prompts(app: Server) -> None:
    """Register discovery-related MCP prompts based on current implementation"""
    
    @app.list_prompts()
    async def list_prompts() -> List[types.Prompt]:
        """List available prompt templates"""
        return [
            types.Prompt(
                name="product-search",
                description="Search for products effectively using the search tool",
                arguments=[
                    types.PromptArgument(
                        name="query",
                        description="What to search for",
                        required=True
                    )
                ]
            ),
            types.Prompt(
                name="search-analysis",
                description="Analyze search results and understand product data",
                arguments=[
                    types.PromptArgument(
                        name="search_term",
                        description="Search term to analyze",
                        required=True
                    )
                ]
            )
        ]
    
    @app.get_prompt()
    async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
        """Get a specific prompt template"""
        try:
            if name == "product-search":
                return _get_product_search_prompt(arguments)
            elif name == "search-analysis":
                return _get_search_analysis_prompt(arguments)
            else:
                raise ValueError(f"Unknown prompt: {name}")
        except Exception as e:
            logger.error(f"Error getting prompt {name}: {e}")
            return types.GetPromptResult(
                description="Error loading prompt",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text", 
                            text=f"Error: {str(e)}"
                        )
                    )
                ]
            )


def _get_product_search_prompt(arguments: dict) -> types.GetPromptResult:
    """Generate product search prompt"""
    query = arguments.get("query", "products")
    
    prompt_content = f"""You are searching for "{query}" using a CMP Discovery Node. Use the available search tool effectively and present results in a user-friendly way.

## Search Strategy:

1. **Understand the Data**: First, read the resources to understand what data is available
   - Check `cmp://products/schema` to understand the field structure
   - Look at `cmp://products/sample` to see example products

2. **Execute Search**: Use the search-products tool
   - Search for: "{query}"
   - Pay attention to search scores (higher = more relevant)
   - Note the limit parameter (default 10, you can request more)

3. **Present Results**: Make results user-friendly
   - **Create clickable links**: Use the `url` field to link to the product's website page
   - **Show product images**: Render the first image from the `image` array if available
   - **Format pricing clearly**: Display prices and availability prominently
   - **Highlight relevance**: Mention search scores for context

## Key Data Points to Extract:

- **Product Information**: Names, descriptions, SKUs
- **Product Links**: Use `url` field to create clickable links to product pages
- **Images**: Display the first image from `image` array for visual appeal
- **Pricing**: Current prices and currencies from offers
- **Availability**: Stock status (InStock/OutOfStock) and inventory levels
- **Brands**: Which brands offer these products
- **Categories**: How products are classified
- **Media**: Any images or rich media available
- **Relevance**: How well results match your search (cmp:searchScore)

## Presentation Guidelines:

- **Product Names**: Make them clickable links using the `url` field
- **Images**: Display the first image from the `image` array when available
- **Pricing**: Show price clearly with currency and availability status
- **Descriptions**: Include helpful product descriptions
- **Search Context**: Mention search scores to show relevance

## Search Tips:

- Try different search terms if initial results aren't relevant
- Use broader terms for discovery, specific terms for targeted results
- Product names, brands, and categories are all searchable
- Search scores help identify the most relevant matches

Present your findings in a visually appealing way with images and clickable product links where available."""

    return types.GetPromptResult(
        description=f"Search for '{query}' and present results with images and links",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=prompt_content
                )
            )
        ]
    )


def _get_search_analysis_prompt(arguments: dict) -> types.GetPromptResult:
    """Generate search analysis prompt"""
    search_term = arguments.get("search_term", "products")
    
    prompt_content = f"""You are analyzing search results for "{search_term}" to understand the product catalog and search effectiveness. Present your analysis with visual elements.

## Analysis Process:

1. **Read Schema Documentation**: 
   - Use `cmp://products/schema` to understand all available fields
   - This will help you interpret the search results correctly

2. **Perform Search**:
   - Use search-products tool with query: "{search_term}"
   - Request a reasonable number of results (10-20)

3. **Analyze and Present Results**:
   
   **Visual Presentation**:
   - **Show product images**: Display the first image from each product's `image` array
   - **Create product links**: Use the `url` field to link to actual product pages
   - **Format pricing**: Make prices and availability easy to scan

   **Relevance Analysis**:
   - Review search scores (cmp:searchScore) - how relevant are results?
   - Do the top results actually match what you searched for?
   - Are there any surprising or irrelevant results?

   **Product Data Analysis**:
   - What types of products were found?
   - Price ranges and availability patterns
   - Brand distribution in results
   - Category coverage

   **Data Quality Assessment**:
   - Are product descriptions complete and helpful?
   - Is pricing information available and current?
   - Do products have good images/media?
   - Are product URLs working and pointing to correct pages?
   - Are variant attributes (additionalProperty) useful?

## Deliverable:

Provide a structured analysis including:

1. **Visual Product Overview**: Show key products with images and links
2. **Search Summary**: What was found, how many results, relevance quality
3. **Product Breakdown**: Types of products, price ranges, key brands
4. **Data Quality**: Completeness of URLs, images, descriptions, pricing
5. **Search Effectiveness**: How well the search worked for this term
6. **Insights**: Notable patterns or interesting findings

**Important**: When displaying products, always:
- Show the first image from the `image` array if available
- Make product names clickable using the `url` field
- Display prices and availability clearly

Include specific examples from the search results to support your analysis."""

    return types.GetPromptResult(
        description=f"Analyze search results for '{search_term}' with visual presentation",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=prompt_content
                )
            )
        ]
    )