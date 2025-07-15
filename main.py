import click
from app.core.logging import get_logger
import uvicorn

logger = get_logger(__name__)


@click.group()
def cli():
    """Ingestor CLI"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000)
@click.option("--workers", default=1)
@click.option("--production", is_flag=True, help="Run in production mode")
def serve(host, port, workers, production):
    """Start the API server"""
    reload = not production  # Auto-reload unless production mode

    uvicorn.run(
        "app.api.web_app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if production else 1,
        log_level="info" if production else "debug",
    )


if __name__ == "__main__":
    cli()
