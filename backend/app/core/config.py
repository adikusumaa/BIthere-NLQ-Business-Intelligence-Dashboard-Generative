"""
Application configuration for BIthere.
Loads all environment variables from .env file using pydantic-settings.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Centralized settings management for BIthere application.
    All sensitive values are loaded from environment variables.
    """

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    JWT_SECRET: str

    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str

    GROQ_API_KEY: str

    GOOGLE_API_KEY: str

    REDIS_URL: str = "redis://localhost:6379/0"

    METABASE_URL: str = "http://localhost:3000"
    METABASE_USERNAME: str = "admin@bithere.com"
    METABASE_PASSWORD: str = "admin123456"

    SMTP_HOST: str = "sandbox.smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    SLACK_WEBHOOK_URL: str = ""

    DB_TYPE: str = "postgres"

    TEST_MODE: str = "live"

    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096

    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSIONS: int = 768

    CACHE_QUERY_TTL: int = 3600
    CACHE_LLM_TTL: int = 3600
    CACHE_EMBEDDING_TTL: int = 86400
    CACHE_DASHBOARD_TTL: int = 3600
    CACHE_METADATA_TTL: int = 21600

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()