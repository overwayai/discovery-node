from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import re

from app.storage.s3_reader import S3Reader
from app.core.dependencies import get_organization_context
from app.core.config import settings
from app.db.base import get_db_session
from app.services.organization_service import OrganizationService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

feed_router = APIRouter()

@feed_router.get("/feed/{filename:path}")
async def serve_feed(
    filename: str,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Serve feed files from S3 bucket based on subdomain.
    
    The flow:
    1. Extract subdomain from host header (e.g., overway-inc from overway-inc.localhost:8000)
    2. Get organization by subdomain to retrieve URN
    3. Extract UUID from URN
    4. Use UUID as S3 folder path (e.g., 6794c67d-8258-5273-a8f7-612f3bfdfe79/feed.json)
    
    Args:
        filename: Feed filename (e.g., feed.json, feed-001.json)
        request: FastAPI request object
        db: Database session
        
    Returns:
        JSON content of the feed file
    """
    logger.info(f"Serving feed file: {filename}")
    logger.info(f"Request host: {request.headers.get('host', 'no host header')}")
    
    # Validate filename - must be JSON
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON feed files are supported")
    
    # Extract subdomain from host header
    host = request.headers.get("host", "")
    if not host:
        raise HTTPException(status_code=400, detail="Host header not found")
    
    # Remove port if present
    host_without_port = host.split(':')[0]
    
    # First, check if this is a custom domain
    org_service = OrganizationService(db)
    
    # Try to find organization by custom domain
    from app.db.models.organization import Organization
    organization = db.query(Organization).filter(Organization.domain == host_without_port).first()
    
    if not organization:
        # Not a custom domain, extract subdomain
        host_parts = host_without_port.split('.')
        
        if len(host_parts) >= 2:
            # Take the first part as subdomain
            subdomain = host_parts[0]
            logger.info(f"Extracted subdomain: {subdomain}")
            
            # Get organization by subdomain
            organization = org_service.get_by_subdomain(subdomain)
        else:
            raise HTTPException(status_code=400, detail="Invalid host format - subdomain not found")
    
    if not organization:
        logger.warning(f"Organization not found for host: {host_without_port}")
        raise HTTPException(status_code=404, detail=f"Organization not found for host: {host_without_port}")
    
    # Get URN from organization
    if not organization.urn:
        logger.error(f"Organization {organization.name} has no URN")
        raise HTTPException(status_code=500, detail="Organization URN not found")
    
    logger.info(f"Found organization URN: {organization.urn}")
    
    # Use the full URN as the S3 folder path
    # S3 path format: urn:cmp:org:6794c67d-8258-5273-a8f7-612f3bfdfe79/feed.json
    org_urn = organization.urn
    logger.info(f"Using full URN for S3 path: {org_urn}")
    
    # Initialize S3 reader
    s3_reader = S3Reader()
    
    if not s3_reader.bucket_name:
        raise HTTPException(status_code=503, detail="S3 storage not configured")
    
    try:
        # Construct S3 key using URN/filename pattern (matching OpenFeed's storage)
        s3_key = f"{org_urn}/{filename}"
        logger.info(f"Reading from S3: s3://{s3_reader.bucket_name}/{s3_key}")
        
        # Get object from S3
        response = s3_reader.s3_client.get_object(
            Bucket=s3_reader.bucket_name,
            Key=s3_key
        )
        
        # Read content
        content = response['Body'].read()
        
        # Parse JSON to validate it
        import json
        feed_data = json.loads(content)
        
        # Return with appropriate headers for crawlers/bots
        return JSONResponse(
            content=feed_data,
            headers={
                # Allow all origins for feed access
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, User-Agent",
                
                # Cache for 1 hour
                "Cache-Control": "public, max-age=3600",
                
                # Indicate content type
                "Content-Type": "application/json; charset=utf-8",
                
                # Allow robots
                "X-Robots-Tag": "all",
                
                # No authentication required
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except s3_reader.s3_client.exceptions.NoSuchKey:
        logger.warning(f"Feed file not found in S3: {s3_key}")
        # Try with feeds/ prefix as fallback (some feeds might be stored with prefix)
        try:
            s3_key_with_prefix = f"feeds/{org_urn}/{filename}"
            logger.info(f"Trying with feeds/ prefix: s3://{s3_reader.bucket_name}/{s3_key_with_prefix}")
            
            response = s3_reader.s3_client.get_object(
                Bucket=s3_reader.bucket_name,
                Key=s3_key_with_prefix
            )
            
            content = response['Body'].read()
            import json
            feed_data = json.loads(content)
            
            return JSONResponse(
                content=feed_data,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, User-Agent",
                    "Cache-Control": "public, max-age=3600",
                    "Content-Type": "application/json; charset=utf-8",
                    "X-Robots-Tag": "all",
                    "X-Content-Type-Options": "nosniff",
                }
            )
        except s3_reader.s3_client.exceptions.NoSuchKey:
            logger.warning(f"Feed file not found with or without prefix: {s3_key}")
            raise HTTPException(status_code=404, detail="Feed file not found")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in feed file: {s3_key}")
        raise HTTPException(status_code=500, detail="Invalid feed format")
    except Exception as e:
        logger.error(f"Error serving feed {filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving feed: {str(e)}")

@feed_router.options("/feed/{filename:path}")
async def feed_options(filename: str):
    """
    Handle OPTIONS requests for CORS preflight.
    This ensures crawlers and bots can access the feed.
    """
    # filename parameter is required for route matching but not used
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, User-Agent",
            "Access-Control-Max-Age": "86400",  # 24 hours
        }
    )