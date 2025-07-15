# app/ingestors/sources/local.py
"""
Local file source implementation.
"""
import os
import logging

from app.ingestors.sources.base import BaseSource
from app.ingestors.base import SourceError, ValidationError

logger = logging.getLogger(__name__)

class LocalSource(BaseSource):
    """
    Source for local file system.
    """
    
    def fetch(self, path: str) -> str:
        """
        Fetch data from a local file.
        
        Args:
            path: Path to the local file
            
        Returns:
            File contents as string
            
        Raises:
            SourceError: If file cannot be read
        """
        logger.info(f"Fetching data from local file: {path}")
        print(f"Fetching data from local file: {path}")
        
        try:
            if not os.path.exists(path):
                raise SourceError(f"File not found: {path}")
            
            # Read the file and return its contents
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            
            return data
            
        except Exception as e:
            logger.exception(f"Error reading local file {path}: {str(e)}")
            raise SourceError(f"Error reading local file: {str(e)}")
        

    def get_org_urn(self, data: dict) -> str:
        """
        Get the organization ID from the data.
        Expected structure:
        {
          "identifier": {
            "@type": "PropertyValue",
            "propertyID": "cmp:orgId",
            "value": "urn:cmp:orgid:123e4667-e89b-12d3-a456-426614174000"
          }
        }
        """
        print(f"Getting org ID from data: {data}")
        print(f"Data type: {type(data)}")
        print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        try:
            identifier = data.get("identifier", {})
            print(f"Identifier: {identifier}")
            print(f"Identifier type: {type(identifier)}")
            
            if isinstance(identifier, dict):
                value = identifier.get("value")
                print(f"Value: {value}")
                print(f"Value type: {type(value)}")
                return value
            else:
                print(f"Identifier is not a dict, it's: {type(identifier)}")
                return None
        except (KeyError, AttributeError) as e:
            print(f"Exception in getting org id: {e}")
            return None
    
    def validate_connection(self) -> bool:
        """
        Validate that the local file system is accessible.
        
        Returns:
            True if the file system is accessible, False otherwise
        """
        logger.info("Validating local file system access")
        print("Validating local file system access")
        
        try:
            # Check if we can create a temporary file
            temp_file = os.path.join(os.path.dirname(__file__), ".test_access")
            with open(temp_file, "w") as f:
                f.write("test")
            os.remove(temp_file)
            return True
        except Exception as e:
            logger.warning(f"Local file system not accessible: {str(e)}")
            return False