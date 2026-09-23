"""
FastAPI entry point for BIthere API v2.
Creates bootstrap admin user on first startup if configured.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    chat,
    chat_workspace,
    dashboard,
    dashboard_import,
    dashboard_manual,
    dashboard_patch,
    dashboard_state,
    dashboard_undo,
    dashboard_version,
    data_sources,
    datasets,
    integrations,
    knowledge_base,
    progress,
    report,
    schema_builder,
    users,
    wizard,
    workspaces,
)
from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_supabase_client


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
app.include_router(dashboard_import.router)
app.include_router(progress.router)

async def ensure_bootstrap_admin() -> None:
    """
    Create a bootstrap admin user on startup if it does not already exist.
    Idempotent: safe to run on every start.
    """
    email = settings.BOOTSTRAP_ADMIN_EMAIL
    password = settings.BOOTSTRAP_ADMIN_PASSWORD

    if not email or not password:
        logger.info("[PROCESS] Bootstrap admin skipped (not configured)")
        return

    email = email.strip().lower()
    supabase = get_supabase_client()

    try:
        existing = (
            supabase.table("profiles")
            .select("id")
            .eq("email", email)
            .execute()
        )
        if existing.data:
            logger.info(f"[PROCESS] Bootstrap admin already exists: {email}")
            return
    except Exception as exc:
        logger.error(f"[ERROR] Bootstrap check failed: {exc}")

    try:
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
        })
        user_id = auth_response.user.id

        supabase.table("profiles").insert({
            "id": user_id,
            "email": email,
            "role": "admin",
        }).execute()

        logger.info(f"[SUCCESS] Bootstrap admin created: {email}")
    except Exception as exc:
        message = str(exc).lower()
        if "already" in message or "duplicate" in message or "registered" in message:
            logger.info(f"[PROCESS] Bootstrap admin already in Auth: {email}")
        else:
            logger.error(f"[ERROR] Bootstrap admin failed: {exc}")


@app.on_event("startup")
async def on_startup() -> None:
    await ensure_bootstrap_admin()


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