"""
Application configuration for BIthere v2.
Platform-level settings + temporary v1 compatibility fields.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Centralized platform settings for BIthere v2.
    """

    # --- Security ---
    MASTER_ENCRYPTION_KEY: str
    JWT_SECRET: str

    # --- Supabase ---
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_DB_URL: str

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_WORKSPACE_PREFIX: str = "ws:"

    # --- Embedding ---
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # --- Metabase (platform default) ---
    METABASE_URL: str = "http://localhost:3000"
    METABASE_PUBLIC_URL: str = "http://localhost:3000"
    METABASE_USERNAME: str = "admin@bithere.com"
    METABASE_PASSWORD: str = "admin123456"

    # --- Upload & Analytics ---
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 500
    DUCKDB_DIR: str = "./duckdb"

    # --- MinIO (optional) ---
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None

    # --- Rate limit ---
    RATE_LIMIT_MAX_CONCURRENT: int = 5
    RATE_LIMIT_BACKOFF_MAX: int = 60

    # --- LLM defaults ---
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096

    # --- Cache TTL ---
    CACHE_QUERY_TTL: int = 3600
    CACHE_LLM_TTL: int = 3600
    CACHE_EMBEDDING_TTL: int = 86400
    CACHE_DASHBOARD_TTL: int = 3600
    CACHE_METADATA_TTL: int = 21600
    CACHE_WORKSPACE_CONTEXT_TTL: int = 300

    # --- Test ---
    TEST_MODE: str = "live"

    # ============================================
    # TEMPORARY: v1 compatibility. Hapus setelah
    # semua agent v2 pakai workspace-level secrets.
    # ============================================
    GROQ_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM: Optional[str] = None
    DB_TYPE: str = "postgres"

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()