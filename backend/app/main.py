"""
FastAPI entry point for BIthere API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, dashboard, report, users
from app.core.config import settings
from app.core.logging import logger


app = FastAPI(
    title="BIthere API",
    description="AI Business Intelligence Analyst",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(report.router)
app.include_router(users.router)


@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint for API status verification."""
    logger.info("Root endpoint accessed")
    return {
        "status": "ok",
        "app": "BIthere",
        "version": "0.1.0",
        "mode": settings.TEST_MODE,
    }


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint for service monitoring."""
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "database": settings.DB_TYPE,
        "llm_model": settings.LLM_MODEL,
    }