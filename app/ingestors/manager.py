# app/ingestors/manager.py
"""
Manager for orchestrating the ingestion process.
"""
import logging
import yaml
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.db.base import SessionLocal
from app.ingestors.sources.factory import SourceFactory
from app.ingestors.handlers.registry import RegistryHandler
from app.ingestors.handlers.feed import FeedHandler
from app.ingestors.base import IngestorError, SourceError, ValidationError, ProcessingError
from app.core.config import settings
from app.ingestors.handlers.vector import VectorHandler

logger = logging.getLogger(__name__)

class IngestorManager:
    """
    Manager for orchestrating the ingestion process.
    """
    
    def __init__(self):
        """Initialize the ingestor manager."""
        self.config_path = settings.INGESTION_CONFIG_PATH
        logger.info(f"Initialized IngestorManager with config path: {self.config_path}")
        print(f"Initialized IngestorManager with config path: {self.config_path}")
    
    def get_ingestors(self) -> List[Dict[str, Any]]:
        """
        Get all ingestors from configuration.
        
        Returns:
            List of ingestor configurations
        """
        logger.info("Getting ingestors from configuration")
        print("Getting ingestors from configuration")
        
        try:
            # Check if config file exists
            if not os.path.exists(self.config_path):
                logger.warning(f"Ingestion configuration file not found: {self.config_path}")
                return []
            
            print(f"Loading configuration from {self.config_path}")
            
            # Load configuration
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # Check if configuration is valid
            if not config or "ingestion" not in config:
                logger.warning("No ingestors defined in configuration")
                return []
            
            return config["ingestion"]
        except Exception as e:
            logger.exception(f"Error loading ingestion configuration: {str(e)}")
            return []
    
    def ingest_registry(self, source_type: str, registry_path: str) -> Dict[str, Any]:
        """
        Ingest a brand registry.
        
        Args:
            source_type: Type of source ("local", "remote", "ftp")
            registry_path: Path or URL to the registry
            
        Returns:
            Ingestion result
            
        Raises:
            IngestorError: If ingestion fails
        """
        logger.info(f"Ingesting registry from {source_type} source: {registry_path}")
        print(f"Ingesting registry from {source_type} source: {registry_path}")
        
        start_time = datetime.now()
        
        try:
            # Create source
            source = SourceFactory.create(source_type)
            
            # Fetch data
            data = source.fetch(registry_path)
            
            # Create database session
            db_session = SessionLocal()
            
            try:
                # Create registry handler
                handler = RegistryHandler(db_session)
                
                # Process data
                result = handler.process(data)
                
                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()
                
                return {
                    "status": "success",
                    "source_type": source_type,
                    "path": registry_path,
                    "duration_seconds": duration,
                    "result": result
                }
            finally:
                db_session.close()
        except Exception as e:
            logger.exception(f"Error ingesting registry: {str(e)}")
            
            # Calculate duration even on error
            duration = (datetime.now() - start_time).total_seconds()
            
            error_type = type(e).__name__
            error_message = str(e)
            
            return {
                "status": "error",
                "source_type": source_type,
                "path": registry_path,
                "duration_seconds": duration,
                "error_type": error_type,
                "error_message": error_message
            }
    
    def ingest_feed(self, source_type: str, feed_path: str, brand_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest a product feed.
        
        Args:
            source_type: Type of source ("local", "remote", "ftp")
            feed_path: Path or URL to the feed index file
            brand_id: Optional brand ID to associate products with
            
        Returns:
            Ingestion result
            
        Raises:
            IngestorError: If ingestion fails
        """
        logger.info(f"Ingesting feed from {source_type} source: {feed_path}")
        print(f"Ingesting feed from {source_type} source: {feed_path}")
        
        start_time = datetime.now()
        
        try:
            # Create source
            source = SourceFactory.create(source_type)
            
            # Fetch feed index data
            data = source.fetch(feed_path)
            
            # Create database session
            db_session = SessionLocal()
            
            try:
                # Parse the feed index data
                import json
                feed_index = json.loads(data)
                
                # Validate it's a ProductFeedIndex
                if feed_index.get("@type") != "ProductFeedIndex":
                    raise IngestorError(f"Expected ProductFeedIndex, got {feed_index.get('@type')}")
                
                logger.info(f"Processing {len(feed_index.get('shards', []))} shards from feed index")
                print(f"Processing {len(feed_index.get('shards', []))} shards from feed index")
                
                # Process each shard individually
                total_product_groups = 0
                total_products = 0
                total_offers = 0
                shards_processed = 0
                
                for shard in feed_index.get("shards", []):
                    shard_url = shard.get("url")
                    if not shard_url:
                        logger.warning("Shard missing URL, skipping")
                        continue
            
                    
                    try:
                        # Fetch shard data
                        shard_data = source.fetch(shard_url)
                        
                        # Create feed handler for this shard
                        handler = FeedHandler(db_session, brand_id)
                        
                        # Process shard data
                        shard_result = handler.process(shard_data)
                        
                        # Accumulate results
                        total_product_groups += shard_result.get("product_groups_processed", 0)
                        total_products += shard_result.get("products_processed", 0)
                        total_offers += shard_result.get("offers_processed", 0)
                        shards_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing shard {shard_url}: {str(e)}")
                        continue
                
                result = {
                    "shards_processed": shards_processed,
                    "product_groups_processed": total_product_groups,
                    "products_processed": total_products,
                    "offers_processed": total_offers
                }
                
                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()
                
                return {
                    "status": "success",
                    "source_type": source_type,
                    "path": feed_path,
                    "duration_seconds": duration,
                    "result": result
                }
            finally:
                db_session.close()
        except Exception as e:
            logger.exception(f"Error ingesting feed: {str(e)}")
            
            # Calculate duration even on error
            duration = (datetime.now() - start_time).total_seconds()
            
            error_type = type(e).__name__
            error_message = str(e)
            
            return {
                "status": "error",
                "source_type": source_type,
                "path": feed_path,
                "duration_seconds": duration,
                "error_type": error_type,
                "error_message": error_message
            }
    
    def ingest_vector(self, source_type: str, registry_path: str) -> Dict[str, Any]:
        """
        Ingest a vector.
        """
        logger.info(f"Ingesting vector from {source_type} source: {registry_path}")
        print(f"Ingesting vector from {source_type} source: {registry_path}")

        source = SourceFactory.create(source_type)
        data = source.fetch(registry_path)

        # Parse JSON string into dictionary
        import json
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from registry: {e}")
            raise IngestorError(f"Invalid JSON in registry file: {e}")

        org_urn = source.get_org_urn(data_dict)
        logger.info(f"Org ID: {org_urn}")


        db_session = SessionLocal()
        handler = VectorHandler(db_session, org_urn)

        handler.process(org_urn)





    def has_feed_updates(self, source_type: str, feed_path: str) -> bool:
        """
        Check if a feed has updates.
        
        Args:
            source_type: Type of source ("local", "remote", "ftp")
            feed_path: Path or URL to the feed
            
        Returns:
            True if the feed has updates, False otherwise
        """
        logger.info(f"Checking for updates to feed: {feed_path}")
        print(f"Checking for updates to feed: {feed_path}")
        
        # For simplicity, this implementation always returns True
        # In a real implementation, you would check for changes in the feed
        return True