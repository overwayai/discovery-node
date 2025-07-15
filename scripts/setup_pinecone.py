#!/usr/bin/env python3
"""
Pinecone index setup script for CMP Discovery Node
Run once per environment during deployment
"""

import os
import sys
import logging
from pinecone import Pinecone
from typing import Optional
from app.core.config import settings

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PineconeIndexSetup:
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.cloud = settings.PINECONE_CLOUD
        self.region = settings.PINECONE_REGION
        self.dense_index_name = settings.PINECONE_DENSE_INDEX
        self.sparse_index_name = settings.PINECONE_SPARSE_INDEX

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY environment variable required")

        self.pinecone_client = Pinecone(api_key=self.api_key)

    def create_dense_index(self) -> bool:
        """Create the main discovery index for product search"""

        try:
            # Check if index already exists
            existing_indexes = [idx.name for idx in self.pinecone_client.list_indexes()]
            if self.dense_index_name in existing_indexes:
                logger.info(
                    f"Index {self.dense_index_name} already exists, skipping creation"
                )
                return True

            logger.info(f"Creating Pinecone index: {self.dense_index_name}")

            response = self.pinecone_client.create_index_for_model(
                name=self.dense_index_name,
                cloud=self.cloud,
                region=self.region,
                embed={
                    "model": "llama-text-embed-v2",
                    "dimension": 1024,  # 1024 is default & good balance
                    "metric": "cosine",
                    "field_map": {"text": "canonical_text"},
                    "write_parameters": {
                        "input_type": "passage",
                        "truncate": "END",
                        "normalize": True,
                        "max_length": 512,
                    },
                    "read_parameters": {
                        "input_type": "query",  # optimise for short queries
                        "truncate": "END",  # chop overflow tokens at tail
                        "dimension": 1024,  # must match index dimension
                    },
                    "write_parameters": {
                        "input_type": "passage",  # optimise for document chunks
                        "truncate": "END",
                        "dimension": 1024,
                    },
                },
                tags={
                    "environment": self.environment,
                    "type": "product-discovery",
                    "protocol": "cmp",
                },
            )

            logger.info(
                f"Index {self.dense_index_name} created successfully: {response}"
            )
            return True

        except Exception as e:
            logger.error(f"Error creating index {self.dense_index_name}: {e}")
            raise

    def create_sparse_index(self) -> bool:
        """Create the sparse index for product search"""

        try:
            # Check if index already exists
            existing_indexes = [idx.name for idx in self.pinecone_client.list_indexes()]
            if self.sparse_index_name in existing_indexes:
                logger.info(
                    f"Index {self.sparse_index_name} already exists, skipping creation"
                )
                return True

            logger.info(f"Creating Pinecone index: {self.sparse_index_name}")

            response = self.pinecone_client.create_index_for_model(
                name=self.sparse_index_name,
                cloud=self.cloud,
                region=self.region,
                embed={
                    "model": "pinecone-sparse-english-v0",
                    "metric": "dotproduct",
                    "field_map": {"text": "canonical_text"},
                    "write_parameters": {
                        "input_type": "passage",
                        "truncate": "END",
                        "normalize": True,
                        "max_length": 512,
                    },
                    "read_parameters": {  # ← query-time embeds
                        "input_type": "query",
                        "truncate": "END",
                    },
                    "write_parameters": {  # ← ingest-time embeds
                        "input_type": "passage",
                        "truncate": "END",
                    },
                },
                tags={
                    "environment": self.environment,
                    "type": "product-discovery",
                    "protocol": "cmp",
                },
            )

            logger.info(
                f"Index {self.sparse_index_name} created successfully: {response}"
            )
            return True

        except Exception as e:
            logger.error(f"Error creating index {self.sparse_index_name}: {e}")
            raise

    def verify_index(self) -> bool:
        """Verify the index exists and is ready"""
        try:
            index = self.pinecone_client.Index(self.dense_index_name)
            stats = index.describe_index_stats()
            logger.info(f"Index {self.dense_index_name} verified - stats: {stats}")
            index = self.pinecone_client.Index(self.sparse_index_name)
            stats = index.describe_index_stats()
            logger.info(f"Index {self.sparse_index_name} verified - stats: {stats}")
            return True
        except Exception as e:
            logger.error(f"Index verification failed: {e}")
            return False


def main():
    """Main setup function"""
    try:
        setup = PineconeIndexSetup()

        logger.info("Starting Pinecone index setup...")
        logger.info(f"Environment: {setup.environment}")
        logger.info(f"Cloud: {setup.cloud}")
        logger.info(f"Region: {setup.region}")

        # Create discovery index
        setup.create_dense_index()
        setup.create_sparse_index()

        # Verify it's working
        setup.verify_index()

        logger.info("✅ Pinecone setup completed successfully!")

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
