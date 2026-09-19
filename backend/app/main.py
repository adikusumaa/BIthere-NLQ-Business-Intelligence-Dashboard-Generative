"""
FastAPI entry point for BIthere API v2.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    chat,
    chat_workspace,
    dashboard,
    dashboard_manual,
    dashboard_patch,
    dashboard_state,
    dashboard_undo,
    dashboard_version,
    data_sources,
    datasets,
    integrations,
    knowledge_base,
    report,
    schema_builder,
    users,
    wizard,
    workspaces,
)
from app.core.config import settings
from app.core.logging import logger


app = FastAPI(
    title="BIthere API",
    description="Multi-Tenant AI Business Intelligence Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(integrations.router)
app.include_router(data_sources.router)
app.include_router(datasets.router)
app.include_router(schema_builder.router)
app.include_router(knowledge_base.router)
app.include_router(wizard.router)
app.include_router(chat_workspace.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(report.router)
app.include_router(users.router)
app.include_router(dashboard_state.router)
app.include_router(dashboard_patch.router)
app.include_router(dashboard_version.router)
app.include_router(dashboard_undo.router)
app.include_router(dashboard_manual.router)


@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint for API status verification."""
    logger.info("[PROCESS] Root endpoint accessed")
    return {
        "status": "ok",
        "app": "BIthere",
        "version": "2.0.0",
        "mode": settings.TEST_MODE,
    }


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint for service monitoring."""
    logger.info("[PROCESS] Health check accessed")
    return {
        "status": "healthy",
        "database": settings.DB_TYPE,
        "llm_model": settings.LLM_MODEL,
    }