"""
Pinecone vector database client.
Supports workspace-scoped keys and namespaced isolation.
"""

from typing import Dict, List, Optional

from pinecone import Pinecone

from app.core.config import settings
from app.core.logging import logger


class PineconeClient:
    """Wrapper for Pinecone operations. Workspace-scoped when api_key/index_name given."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        self.pc = Pinecone(api_key=api_key or settings.PINECONE_API_KEY)
        self.index = self.pc.Index(index_name or settings.PINECONE_INDEX_NAME)

    def upsert(self, vectors: List[Dict], namespace: str) -> bool:
        try:
            self.index.upsert(vectors=vectors, namespace=namespace)
            logger.info(f"[SUCCESS] Upserted {len(vectors)} vectors to namespace {namespace}")
            return True
        except Exception as error:
            logger.error(f"[ERROR] Pinecone upsert failed: {error}")
            return False

    def query(
        self,
        vector: List[float],
        namespace: str,
        top_k: int = 5,
    ) -> List[Dict]:
        try:
            response = self.index.query(
                namespace=namespace,
                vector=vector,
                top_k=top_k,
                include_metadata=True,
            )
            return response.get("matches", [])
        except Exception as error:
            logger.error(f"[ERROR] Pinecone query failed: {error}")
            return []

    def delete_namespace(self, namespace: str) -> bool:
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"[SUCCESS] Deleted namespace {namespace}")
            return True
        except Exception as error:
            logger.error(f"[ERROR] Pinecone namespace delete failed: {error}")
            return False

    def list_namespaces(self) -> List[str]:
        try:
            stats = self.index.describe_index_stats()
            return list(stats.get("namespaces", {}).keys())
        except Exception as error:
            logger.error(f"[ERROR] Pinecone list namespaces failed: {error}")
            return []


# v1 singleton (backward compatibility)
pinecone_client = PineconeClient()


def build_pinecone(api_key: str, index_name: str) -> PineconeClient:
    """Build a workspace-scoped Pinecone client."""
    return PineconeClient(api_key=api_key, index_name=index_name)


def workspace_namespace(workspace_id: str, kind: str) -> str:
    """
    Namespace convention: workspace_{uuid}/{kind}
    kind: schema | glossary | query_history
    """
    return f"workspace_{workspace_id}/{kind}"