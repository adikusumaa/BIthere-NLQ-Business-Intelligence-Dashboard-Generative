"""
Pinecone vector database client for metadata storage and retrieval.
"""

from typing import Dict, List, Optional

from pinecone import Pinecone

from app.core.config import settings
from app.core.logging import logger


class PineconeClient:
    """
    Wrapper for Pinecone operations.
    """

    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)

    def upsert(self, vectors: List[Dict], namespace: str) -> bool:
        """
        Upsert vectors to Pinecone namespace.
        Each vector: {"id": str, "values": List[float], "metadata": Dict}
        """

        try:
            self.index.upsert(vectors=vectors, namespace=namespace)
            logger.success(f"Upserted {len(vectors)} vectors to namespace {namespace}")
            return True
        except Exception as error:
            logger.error(f"Pinecone upsert failed: {str(error)}")
            return False

    def query(
        self,
        vector: List[float],
        namespace: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Query Pinecone for similar vectors.
        """

        try:
            response = self.index.query(
                namespace=namespace,
                vector=vector,
                top_k=top_k,
                include_metadata=True,
            )
            return response.get("matches", [])
        except Exception as error:
            logger.error(f"Pinecone query failed: {str(error)}")
            return []

    def delete_namespace(self, namespace: str) -> bool:
        """
        Delete all vectors in namespace.
        """

        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.success(f"Deleted all vectors in namespace {namespace}")
            return True
        except Exception as error:
            logger.error(f"Pinecone namespace delete failed: {str(error)}")
            return False


pinecone_client = PineconeClient()