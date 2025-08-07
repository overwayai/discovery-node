"""HTML formatter for converting JSON responses to HTML format."""

from typing import Dict, Any, Optional
import json
from jinja2 import Environment, BaseLoader
import logging
import urllib.parse

logger = logging.getLogger(__name__)


class HTMLFormatter:
    """Formats JSON responses as HTML for browser-friendly viewing."""
    
    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        self.env = Environment(loader=BaseLoader())
    
    def format_product_list(self, data: Dict[str, Any]) -> str:
        """Format a product list (ItemList) as HTML."""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Product Search Results</title>
</head>
<body>
    {% for item_wrapper in items %}
    {% set product = item_wrapper.item %}
    <div class="product">
        <h2>{{ product.name }}</h2>
        {% if product['@cmp:media'] and product['@cmp:media']|length > 0 %}
        <a href="{{ product.url }}">
            <img src="{{ product['@cmp:media'][0].url }}" alt="{{ product.name }} Cover" />
        </a>
        {% endif %}
        {% if product.brand %}
        <p><strong>Brand:</strong> {{ product.brand.name }}</p>
        {% endif %}
        {% if product.offers %}
        <p><strong>Price:</strong> ${{ "%.2f"|format(product.offers.price) }}</p>
        {% if product.offers.availability == "https://schema.org/InStock" %}
        <p><strong>Availability:</strong> In Stock{% if product.offers.inventoryLevel %} ({{ product.offers.inventoryLevel.value }} units){% endif %}</p>
        {% else %}
        <p><strong>Availability:</strong> Out of Stock</p>
        {% endif %}
        {% endif %}
        {% if product.description %}
        <p>{{ product.description[:300] }}{% if product.description|length > 300 %}...{% endif %}</p>
        {% endif %}
    </div>
    {% endfor %}
    
    <div class="links">
        {% if has_next %}
        <p><strong>Find More:</strong> <a href="{{ base_url }}/api/v1/query/search?q={{ query_encoded }}&skip={{ next_skip }}&limit={{ limit }}">{{ base_url }}/api/v1/query/search?q={{ query_encoded }}&skip={{ next_skip }}&limit={{ limit }}</a></p>
        {% endif %}
        {% if request_id %}
        <p><strong>Compare by Index (POST):</strong> {{ base_url }}/api/v1/query/compare</p>
        <p>Example: {"request_id": "{{ request_id }}", "indices": [0, 1, 2], "format": "table"}</p>
        {% else %}
        <p><strong>Compare by Index (POST):</strong> {{ base_url }}/api/v1/query/compare</p>
        <p>Example: {"request_id": "ABC123", "indices": [0, 1, 2], "format": "table"}</p>
        {% endif %}
        <p><strong>Compare by URN (POST):</strong> {{ base_url }}/api/v1/query/compare/products</p>
        <p>Example: {"urns": ["urn:cmp:sku:{{sku1}}", "urn:cmp:sku:{{sku2}}", "urn:cmp:sku:{{sku3}}"], "format": "table"}</p>
    </div>
</body>
</html>
        """
        
        template = self.env.from_string(template_str)
        
        # Extract data for template
        query = data.get('query', '')
        context = {
            'items': data.get('itemListElement', []),
            'total_results': data.get('cmp:totalResults', 0),
            'skip': data.get('cmp:skip', 0),
            'limit': data.get('cmp:limit', 20),
            'has_next': data.get('cmp:hasNext', False),
            'has_previous': data.get('cmp:hasPrevious', False),
            'next_skip': data.get('cmp:nextSkip', 0),
            'previous_skip': data.get('cmp:previousSkip', 0),
            'base_url': self.base_url,
            'query': query,
            'query_encoded': urllib.parse.quote(query),  # URL-encode the query
            'request_id': data.get('cmp:requestId', '')  # Get request ID for compare
        }
        
        return template.render(**context)
    
    def format_single_product(self, product: Dict[str, Any]) -> str:
        """Format a single product as HTML."""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ product.name }}</title>
</head>
<body>
    <div class="product">
        <h1>{{ product.name }}</h1>
        
        {% if product['@cmp:media'] and product['@cmp:media']|length > 0 %}
        <a href="{{ product.url }}">
            <img src="{{ product['@cmp:media'][0].url }}" alt="{{ product.name }}" />
        </a>
        {% endif %}
        
        {% if product.brand %}
        <p><strong>Brand:</strong> {{ product.brand.name }}</p>
        {% endif %}
        
        {% if product.offers %}
        <p><strong>Price:</strong> ${{ "%.2f"|format(product.offers.price) }} {{ product.offers.priceCurrency }}</p>
        
        {% if product.offers.availability == "https://schema.org/InStock" %}
        <p><strong>Availability:</strong> In Stock{% if product.offers.inventoryLevel %} ({{ product.offers.inventoryLevel.value }} units available){% endif %}</p>
        {% else %}
        <p><strong>Availability:</strong> Out of Stock</p>
        {% endif %}
        {% endif %}
        
        {% if product.category %}
        <p><strong>Category:</strong> {{ product.category }}</p>
        {% endif %}
        
        {% if product.sku %}
        <p><strong>SKU:</strong> {{ product.sku }}</p>
        {% endif %}
        
        {% if product.description %}
        <h3>Description</h3>
        <p>{{ product.description }}</p>
        {% endif %}
        
        {% if product.url %}
        <p><a href="{{ product.url }}">View on Store</a></p>
        {% endif %}
    </div>
</body>
</html>
        """
        
        template = self.env.from_string(template_str)
        return template.render(product=product)
    
    def format_feed(self, feed: Dict[str, Any]) -> str:
        """Format a feed.json response as HTML."""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ org_name }} - Product Feed</title>
</head>
<body>
    <h1>{{ org_name }}</h1>
    {% if org_url %}
    <p><a href="{{ org_url }}">{{ org_url }}</a></p>
    {% endif %}
    
    <h2>Search API</h2>
    <p><strong>Template:</strong> {{ search_template }}</p>
    <h3>Parameters:</h3>
    <ul>
    {% if search_params %}
    {% for param, desc in search_params.items() %}
        <li><strong>{{ param }}:</strong> {{ desc }}</li>
    {% endfor %}
    {% endif %}
    </ul>
    
    {% if categories %}
    <h3>Categories:</h3>
    <ul>
    {% for category in categories %}
        <li>{{ category }}</li>
    {% endfor %}
    </ul>
    {% endif %}
    
    {% if attributes %}
    <h3>Attributes:</h3>
    <ul>
    {% for attr in attributes %}
        <li><strong>{{ attr['name'] }}:</strong> {{ attr['values'][:5]|join(', ') if attr['values'] else '' }}{% if attr['values'] and attr['values']|length > 5 %}...{% endif %}</li>
    {% endfor %}
    </ul>
    {% endif %}
    
    {% if examples %}
    <h3>Example Searches:</h3>
    <ul>
    {% for example in examples %}
        <li>
            <strong>{{ example['intent'] }}:</strong><br>
            <a href="{{ example['ready_link'] }}">{{ example['ready_link'] }}</a>
        </li>
    {% endfor %}
    </ul>
    {% endif %}
    
    {% if quick_access %}
    <h3>Quick Access:</h3>
    <ul>
    {% for name, url in quick_access.items() %}
        <li><strong>{{ name|replace('_', ' ')|title }}:</strong> <a href="{{ url }}">{{ url }}</a></li>
    {% endfor %}
    </ul>
    {% endif %}
    
    <hr>
    <p><small>Generated at {{ generated_at }}</small></p>
    <p><small>OpenAPI Spec: <a href="{{ openapi_spec }}">{{ openapi_spec }}</a></small></p>
</body>
</html>
        """
        
        template = self.env.from_string(template_str)
        
        # Extract data for template
        context = {
            'org_name': feed.get('organization', {}).get('name', 'Organization'),
            'org_url': feed.get('organization', {}).get('url', ''),
            'search_template': feed.get('search_template', ''),
            'search_params': feed.get('search_parameters', {}),
            'categories': feed.get('facets', {}).get('categories', []),
            'attributes': feed.get('facets', {}).get('attributes', []),
            'examples': feed.get('examples', []),
            'quick_access': feed.get('quick_access', {}),
            'generated_at': feed.get('generated_at', ''),
            'openapi_spec': feed.get('openapi_spec', '')
        }
        
        return template.render(**context)
    
    def format_error(self, error: Dict[str, Any]) -> str:
        """Format an error response as HTML."""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error</title>
</head>
<body>
    <h1>Error</h1>
    <p>{{ detail }}</p>
    {% if errors %}
    <ul>
    {% for error in errors %}
        <li>{{ error }}</li>
    {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
        """
        
        template = self.env.from_string(template_str)
        return template.render(
            detail=error.get('detail', 'An error occurred'),
            errors=error.get('errors', [])
        )
    
    def format_response(self, data: Dict[str, Any], response_type: Optional[str] = None) -> str:
        """
        Format a response based on its type.
        
        Args:
            data: The JSON response data
            response_type: Optional hint about response type
            
        Returns:
            HTML formatted string
        """
        try:
            # Check if it's an error response
            if 'detail' in data or 'error' in data:
                return self.format_error(data)
            
            # Check if it's an ItemList (product list)
            if data.get('@type') == 'ItemList' or 'itemListElement' in data:
                return self.format_product_list(data)
            
            # Check if it's a single Product
            if data.get('@type') == 'Product':
                return self.format_single_product(data)
            
            # Default: return formatted JSON in HTML
            return self._format_json_as_html(data)
            
        except Exception as e:
            logger.error(f"Error formatting HTML response: {e}")
            return self._format_json_as_html(data)
    
    def _format_json_as_html(self, data: Dict[str, Any]) -> str:
        """Fallback: format JSON data as pretty HTML."""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>API Response</title>
</head>
<body>
    <h1>API Response</h1>
    <pre>{{ json_data }}</pre>
</body>
</html>
        """
        
        template = self.env.from_string(template_str)
        return template.render(json_data=json.dumps(data, indent=2))