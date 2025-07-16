import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Optional

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from app.core.logging import get_logger
from app.core.config import settings
from app.core.dependencies import get_search_service, get_product_service
from .event_store import create_event_store
from .tools.discovery_tools import register_discovery_tools

logger = get_logger(__name__)


class MCPServer:
    def __init__(self, json_response: bool = False):
        self.app = Server("cmp-discovery-node")
        self.json_response = json_response
        self.event_store = create_event_store()
        self.session_manager: Optional[StreamableHTTPSessionManager] = None
        
        # Register tools and handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register MCP handlers"""
        # Get services via dependency injection
        search_service = get_search_service()
        product_service = get_product_service()
        
        register_discovery_tools(
            self.app, 
            search_service, 
            product_service
        )
        
    def create_starlette_app(self) -> Starlette:
        """Create the Starlette ASGI application"""
        # Create session manager without event store for now to avoid serialization issues
        self.session_manager = StreamableHTTPSessionManager(
            app=self.app,
            event_store=None,  # Disable event store temporarily
            json_response=self.json_response,
        )
        
        # ASGI handler for streamable HTTP connections
        async def handle_streamable_http(
            scope: Scope, receive: Receive, send: Send
        ) -> None:
            await self.session_manager.handle_request(scope, receive, send)

        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            """Context manager for managing session manager lifecycle."""
            logger.info("Starting MCP Discovery Node...")
            
            # Start session manager
            async with self.session_manager.run():
                logger.info("MCP Discovery Node started with StreamableHTTP and Redis event store!")
                try:
                    yield
                finally:
                    logger.info("MCP Discovery Node shutting down...")
                    # Cleanup Redis connections
                    await self.event_store.close()

        # Create Starlette app
        starlette_app = Starlette(
            debug=settings.DEBUG,
            routes=[
                Mount("/sse", app=handle_streamable_http),
            ],
            lifespan=lifespan,
        )
        
        return starlette_app

    async def cleanup_old_events(self):
        """Periodic cleanup of old events"""
        await self.event_store.cleanup_old_streams(max_age_seconds=3600)


def create_mcp_server(json_response: bool = False) -> MCPServer:
    """Factory function to create MCP server instance"""
    return MCPServer(json_response=json_response)


# Health check endpoint (optional)
async def health_check() -> dict:
    """Simple health check for MCP server"""
    return {
        "status": "healthy",
        "service": "cmp-discovery-mcp",
        "event_store": "redis"
    }