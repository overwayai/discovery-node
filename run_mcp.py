#!/usr/bin/env python3
"""
MCP Server entry point for CMP Discovery Node
"""
import click
import uvicorn
from app.mcp.server import create_mcp_server

@click.command()
@click.option("--port", default=3001, help="Port to listen on for MCP HTTP")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR)",
)
def main(port: int, host: str, json_response: bool, log_level: str):
    """Start the MCP Discovery Node server"""
    
    # Create MCP server
    mcp_server = create_mcp_server(json_response=json_response)
    starlette_app = mcp_server.create_starlette_app()
    
    # Run with uvicorn
    uvicorn.run(
        starlette_app,
        host=host,
        port=port,
        log_level=log_level.lower()
    )

if __name__ == "__main__":
    main()