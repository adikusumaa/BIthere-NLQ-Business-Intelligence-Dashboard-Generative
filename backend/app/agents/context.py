"""
AgentContext: per-workspace runtime resources for the agent pipeline.
Passed via AgentState["context"] to make all nodes workspace-aware.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.connectors.base import BaseConnector
from app.workspace.context import WorkspaceContext


@dataclass
class AgentContext:
    """
    Bundle of per-workspace resources for the agent pipeline.
    When None is passed, agents fall back to global v1 settings.
    """
    workspace_id: str
    redis_prefix: str
    pinecone_namespace: str

    groq_key: Optional[str] = None
    google_key: Optional[str] = None
    pinecone_key: Optional[str] = None
    pinecone_index: Optional[str] = None
    metabase_key: Optional[str] = None
    slack_webhook: Optional[str] = None
    email_key: Optional[str] = None

    connector: Optional[BaseConnector] = None
    dialect: str = "postgresql"
    supports_sql: bool = True

    @classmethod
    def from_workspace_context(
        cls,
        ctx: WorkspaceContext,
        connector: Optional[BaseConnector] = None,
        pinecone_index: Optional[str] = None,
    ) -> "AgentContext":
        dialect = connector.get_dialect() if connector else "postgresql"
        supports_sql = connector.supports_sql() if connector else True
        return cls(
            workspace_id=ctx.workspace_id,
            redis_prefix=ctx.redis_prefix,
            pinecone_namespace=ctx.pinecone_namespace,
            groq_key=ctx.groq_key,
            google_key=ctx.google_key,
            pinecone_key=ctx.pinecone_key,
            pinecone_index=pinecone_index,
            metabase_key=ctx.metabase_key,
            slack_webhook=ctx.slack_webhook,
            email_key=ctx.email_key,
            connector=connector,
            dialect=dialect,
            supports_sql=supports_sql,
        )

    def namespace(self, kind: str) -> str:
        """Return workspace-scoped namespace: workspace_{id}/{kind}."""
        return f"{self.pinecone_namespace}/{kind}"