# Standard library
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import uuid

# Third party
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import text

# Local imports
from app.core.config import settings
from app.core.logging import get_logger
import app.api as api


logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application startup and shutdown events"""
    # Startup
    logger.info("🚀 Discovery API starting up...")
    
    # Test database connection
    try:
        from app.db.base import get_db_session
        session_gen = get_db_session()
        session = next(session_gen)
        session.execute(text("SELECT 1")).fetchone()
        session.close()
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    yield  # This is where FastAPI serves the application

    # Shutdown
    logger.info("🛑 Openfeed API shutting down...")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Overway Discovery",
        description="Overway Discovery is a product discovery engine that uses AI to find products that match your search query.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # Mount API routes - automatically mount all routers from api/__init__.py
    for router_name in api.__all__:
        router = getattr(api, router_name)
        # Extract tag from router name (e.g., "organization_router" -> "organizations")
        tag = router_name.replace("_router", "").replace("_", "")
        app.include_router(router, prefix="/api", tags=[tag])

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add detailed request/response logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid.uuid4())
        print(f"[{request_id}] Incoming request: {request.method} {request.url}")
        logger.info(f"[{request_id}] {'='*60}")
        logger.info(f"[{request_id}] REQUEST START")
        logger.info(f"[{request_id}] Method: {request.method}")
        logger.info(f"[{request_id}] URL: {request.url}")
        
        # Log headers (filter sensitive ones in production)
        headers = dict(request.headers)
            # Remove sensitive headers in non-debug mode
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[REDACTED]'
        logger.info(f"[{request_id}] Headers: {headers}")
        logger.info(f"[{request_id}] Query Params: {dict(request.query_params)}")
        
        # Log request body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to decode as JSON for better readability
                    try:
                        import json
                        body_json = json.loads(body.decode())
                        logger.info(f"[{request_id}] Request Body: {json.dumps(body_json, indent=2)}")
                    except:
                        logger.info(f"[{request_id}] Request Body: {body.decode()}")
                else:
                    logger.info(f"[{request_id}] Request Body: (empty)")
                
                # Recreate the request body since we consumed it
                from starlette.requests import Request as StarletteRequest
                request._body = body
            except Exception as e:
                logger.warning(f"[{request_id}] Could not read request body: {e}")
   
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response details

            logger.info(f"[{request_id}] RESPONSE")
            logger.info(f"[{request_id}] Status Code: {response.status_code}")
            logger.info(f"[{request_id}] Response Headers: {dict(response.headers)}")
            logger.info(f"[{request_id}] Process Time: {process_time:.4f}s")
            
            # Log response body for error status codes or in debug mode
            if response.status_code >= 400:
                try:
                    # For streaming responses, we can't easily read the body
                    if hasattr(response, 'body'):
                        response_body = response.body
                        if response_body:
                            try:
                                import json
                                body_json = json.loads(response_body.decode())
                                logger.info(f"[{request_id}] Response Body: {json.dumps(body_json, indent=2)}")
                            except:
                                logger.info(f"[{request_id}] Response Body: {response_body.decode()}")
                        else:
                            logger.info(f"[{request_id}] Response Body: (empty)")
                    else:
                        logger.info(f"[{request_id}] Response Body: (streaming response)")
                except Exception as e:
                    logger.warning(f"[{request_id}] Could not read response body: {e}")
            
            logger.info(f"[{request_id}] REQUEST END")
            logger.info(f"[{request_id}] {'='*60}")

            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"[{request_id}] Request failed after {process_time:.4f}s: {str(e)}", exc_info=True)
            logger.info(f"[{request_id}] REQUEST END (ERROR)")
            logger.info(f"[{request_id}] {'='*60}")
            
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancers and monitoring"""
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

    # OpenAPI specification endpoints
    @app.get("/openapi.yaml")
    async def get_openapi_yaml():
        """Serve OpenAPI specification in YAML format"""
        from fastapi.openapi.utils import get_openapi
        from yaml import dump
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Convert to YAML
        yaml_content = dump(openapi_schema, default_flow_style=False, sort_keys=False)
        
        from fastapi.responses import Response
        return Response(content=yaml_content, media_type="application/x-yaml")

    @app.get("/openapi.json")
    async def get_openapi_json():
        """Serve OpenAPI specification in JSON format"""
        from fastapi.openapi.utils import get_openapi
        import json
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Convert to JSON
        json_content = json.dumps(openapi_schema, indent=2)
        
        from fastapi.responses import Response
        return Response(content=json_content, media_type="application/json")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Validation error handler for detailed logging
    from fastapi.exceptions import RequestValidationError
    from pydantic import ValidationError
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        logger.error(f"Request body: {exc.body}")
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": exc.errors()}
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        logger.error(f"Pydantic validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": exc.errors()}
        )
    
    return app

# Create the app instance
app = create_app()

