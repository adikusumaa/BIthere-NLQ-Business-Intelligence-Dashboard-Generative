"""
Pinecone vector database client.
Supports workspace-scoped keys and namespaced isolation.
Upsert automatically batches to stay under Pinecone's 2 MB limit.
"""

from typing import Dict, List, Optional

from pinecone import Pinecone

from app.core.config import settings
from app.core.logging import logger


UPSERT_BATCH_SIZE = 100


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
        """
        Upsert vectors to Pinecone in batches.
        Keeps each request below Pinecone's 2 MB size limit.
        """
        if not vectors:
            return True

        total = len(vectors)
        total_upserted = 0

        for start in range(0, total, UPSERT_BATCH_SIZE):
            batch = vectors[start:start + UPSERT_BATCH_SIZE]
            try:
                self.index.upsert(vectors=batch, namespace=namespace)
                total_upserted += len(batch)
                logger.info(
                    f"[PROCESS] Upserted batch {total_upserted}/{total} "
                    f"to namespace {namespace}"
                )
            except Exception as error:
                logger.error(
                    f"[ERROR] Pinecone upsert failed at batch "
                    f"{start}-{start + len(batch)}: {error}"
                )
                return False

        logger.info(
            f"[SUCCESS] Upserted {total_upserted} vectors to namespace {namespace}"
        )
        return True

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
        """
        Delete all vectors in a namespace.
        A missing namespace is treated as success (nothing to delete).
        """
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"[SUCCESS] Deleted namespace {namespace}")
            return True
        except Exception as error:
            message = str(error).lower()
            if "not found" in message or "404" in message:
                logger.info(
                    f"[PROCESS] Namespace {namespace} did not exist yet, "
                    "skipping delete"
                )
                return True
            logger.error(f"[ERROR] Pinecone namespace delete failed: {error}")
            return False

    def list_namespaces(self) -> List[str]:
        try:
            stats = self.index.describe_index_stats()
            return list(stats.get("namespaces", {}).keys())
        except Exception as error:
            logger.error(f"[ERROR] Pinecone list namespaces failed: {error}")
            return []


pinecone_client = PineconeClient()


def build_pinecone(api_key: str, index_name: str) -> PineconeClient:
    return PineconeClient(api_key=api_key, index_name=index_name)


def workspace_namespace(workspace_id: str, kind: str) -> str:
    return f"workspace_{workspace_id}/{kind}"