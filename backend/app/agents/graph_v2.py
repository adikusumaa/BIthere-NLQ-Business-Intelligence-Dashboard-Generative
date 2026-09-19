"""
LangGraph orchestration v2: workspace-aware agent pipeline.

Key differences vs v1 (graph.py):
- AgentState carries AgentContext (keys, namespace, connector).
- Nodes read connector + api_key from state["context"].
- Cache keys are prefixed with workspace_id.
- RAG uses workspace namespace.
- LLM calls pass workspace Groq key.
"""

import hashlib
from typing import Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents import (
    dashboard_builder,
    insight_analyzer,
    optimizer,
    planner,
    query_generator,
    query_executor,
    report_sender,
    validator,
)
from app.agents.context import AgentContext
from app.core.config import settings
from app.core.logging import log_error, log_info, log_process, log_warning
from app.rag.embedding import embed_text
from app.rag.pinecone_client import build_pinecone, pinecone_client
from app.services.cache import cache


class AgentState(TypedDict, total=False):
    """Shared state flowing through all v2 nodes."""

    prompt: str
    session_id: str
    user_email: str

    context: Optional[AgentContext]

    plan: dict
    metadata_context: str
    generated_query: str
    query_result: list
    insight: str
    dashboard_config: dict
    dashboard_url: str | None
    report_status: dict
    final_response: str
    error: str | None
    cache_key: str
    cache_hit: str


def _scoped_cache_key(ctx: Optional[AgentContext], prompt: str) -> str:
    """Build workspace-scoped cache key."""
    normalized = prompt.strip().lower()
    h = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    prefix = ctx.redis_prefix if ctx else ""
    return f"{prefix}chat:{h}"


def _pinecone_for(ctx: Optional[AgentContext]):
    """Return workspace Pinecone client if context present, else v1 singleton."""
    if ctx and ctx.pinecone_key:
        return build_pinecone(ctx.pinecone_key, ctx.pinecone_index or settings.PINECONE_INDEX_NAME)
    return pinecone_client


def _namespace_for(ctx: Optional[AgentContext], kind: str) -> str:
    """Return namespace: v2 uses workspace_{id}/{kind}, v1 uses '{kind}'."""
    if ctx:
        return f"{ctx.pinecone_namespace}/{kind}"
    return kind


def _llm_key(ctx: Optional[AgentContext]) -> Optional[str]:
    return ctx.groq_key if ctx else None


def _google_key(ctx: Optional[AgentContext]) -> Optional[str]:
    return ctx.google_key if ctx else None


# =====================================================
# Nodes
# =====================================================

async def node_planner(state: AgentState) -> AgentState:
    log_process("Node: Planner (v2)")
    ctx = state.get("context")
    state["plan"] = await planner.plan(
        state["prompt"],
        api_key=_llm_key(ctx),
    )
    return state


async def node_guard(state: AgentState) -> AgentState:
    log_process("Node: Guard (v2)")
    plan = state.get("plan", {})

    if not plan.get("is_in_scope", True):
        if plan.get("clarification_needed"):
            hint = plan.get("clarification_hint", "").strip()
            state["error"] = (
                f'Your question is too broad. Try: "{hint}"'
                if hint
                else "Your question is too broad. Please specify the table, column, or metric."
            )
        else:
            state["error"] = (
                "I can only answer questions about this workspace's data. "
                "Your question is out of scope."
            )
    return state


def route_after_guard(state: AgentState) -> str:
    if state.get("error"):
        return "response"
    return "rag"


async def node_rag(state: AgentState) -> AgentState:
    log_process("Node: RAG Retrieval (v2)")
    ctx = state.get("context")

    try:
        vector = await embed_text(
            state["prompt"],
            api_key=_google_key(ctx),
            redis_prefix=ctx.redis_prefix if ctx else "",
        )
        client = _pinecone_for(ctx)
        matches = client.query(vector, _namespace_for(ctx, "schema"), top_k=5)
        context_lines = [
            m.get("metadata", {}).get("text", "")
            for m in matches
            if m.get("metadata", {}).get("text")
        ]
        state["metadata_context"] = "\n".join(context_lines)
        log_info(f"Retrieved {len(context_lines)} metadata items")
    except Exception as exc:
        log_error(f"RAG retrieval failed: {exc}")
        state["metadata_context"] = ""
    return state


async def node_cache_check(state: AgentState) -> AgentState:
    log_process("Node: Cache Check (v2)")
    ctx = state.get("context")
    key = _scoped_cache_key(ctx, state["prompt"])
    state["cache_key"] = key

    cached_llm = await cache.get(f"{key}:llm")
    if cached_llm and cached_llm.get("final_response"):
        state["cache_hit"] = "full"
        state["final_response"] = cached_llm["final_response"]
        state["insight"] = cached_llm.get("insight", "")
        return state

    cached_query = await cache.get(f"{key}:query")
    if cached_query and cached_query.get("query_result") is not None:
        state["cache_hit"] = "query"
        state["generated_query"] = cached_query.get("generated_query", "")
        state["query_result"] = cached_query.get("query_result", [])
        return state

    state["cache_hit"] = "miss"
    return state


def route_after_cache(state: AgentState) -> str:
    hit = state.get("cache_hit", "miss")
    if hit == "full":
        return "response"
    if hit == "query":
        return "insight"

    plan = state.get("plan", {})
    intent = plan.get("intent", "query_data")
    needs_dashboard = plan.get("needs_dashboard", False)
    needs_report = plan.get("needs_report", False)

    if intent == "create_dashboard" or (needs_dashboard and not needs_report):
        return "dashboard_only"

    return "query_generator"


async def node_query_generator(state: AgentState) -> AgentState:
    log_process("Node: Query Generator (v2)")
    ctx = state.get("context")
    dialect = ctx.dialect if ctx else "postgresql"

    state["generated_query"] = await query_generator.generate_query(
        state["prompt"],
        state.get("metadata_context", ""),
        api_key=_llm_key(ctx),
        dialect=dialect,
    )
    return state


async def node_validator(state: AgentState) -> AgentState:
    log_process("Node: Validator (v2)")
    try:
        state["generated_query"] = validator.validate_query(state["generated_query"])
    except validator.QueryValidationError as exc:
        log_error(f"Validation failed: {exc}")
        state["error"] = str(exc)
    return state


async def node_optimizer(state: AgentState) -> AgentState:
    log_process("Node: Optimizer (v2)")
    if not state.get("error"):
        state["generated_query"] = optimizer.optimize_query(state["generated_query"])
    return state


async def node_executor(state: AgentState) -> AgentState:
    log_process("Node: Query Executor (v2)")
    if state.get("error"):
        return state

    ctx = state.get("context")
    connector = ctx.connector if ctx else None

    if connector is None:
        log_error("No connector available in AgentContext")
        state["error"] = "Workspace has no data source configured"
        state["query_result"] = []
        return state

    try:
        state["query_result"] = await query_executor.execute(
            state["generated_query"], connector
        )
        log_info(f"Query returned {len(state['query_result'])} rows")

        key = state.get("cache_key", "")
        if key:
            await cache.set(
                f"{key}:query",
                {
                    "generated_query": state["generated_query"],
                    "query_result": state["query_result"],
                },
                ttl=settings.CACHE_QUERY_TTL,
            )
    except Exception as exc:
        log_error(f"Query execution failed: {exc}")
        state["error"] = f"Query execution failed: {exc}"
        state["query_result"] = []
    return state


async def node_insight(state: AgentState) -> AgentState:
    log_process("Node: Insight Analyzer (v2)")
    if state.get("error"):
        return state
    ctx = state.get("context")

    try:
        state["insight"] = await insight_analyzer.analyze(
            state["prompt"],
            state.get("query_result", []),
            api_key=_llm_key(ctx),
        )
    except Exception as exc:
        log_error(f"Insight analyzer failed: {exc}")
        state["insight"] = "Failed to generate insight."
    return state


async def node_dashboard(state: AgentState) -> AgentState:
    log_process("Node: Dashboard Builder (v2)")
    if state.get("error"):
        return state

    ctx = state.get("context")
    try:
        result = await dashboard_builder.build_dashboard(
            state["prompt"], state.get("query_result") or []
        )
        state["dashboard_config"] = result.get("config")
        state["dashboard_url"] = result.get("embed_url")

        if not result.get("success"):
            log_warning(f"Dashboard build failed: {result.get('error')}")

        if not state.get("insight") and result.get("config"):
            config = result["config"]
            pages = config.get("pages") or []
            chart_count = sum(len(p.get("charts", [])) for p in pages)
            if not pages and config.get("charts"):
                chart_count = len(config.get("charts"))
            title = config.get("title", "Dashboard")
            state["insight"] = (
                f"Dashboard '{title}' created with {max(len(pages),1)} page(s) "
                f"and {chart_count} chart(s)."
            )
    except Exception as exc:
        log_error(f"Dashboard builder failed: {exc}")
    return state


async def node_report(state: AgentState) -> AgentState:
    log_process("Node: Report Sender (v2)")
    if state.get("error"):
        return state

    plan = state.get("plan", {})
    if not plan.get("needs_report"):
        return state

    channel = plan.get("report_channel", "email")
    insight = state.get("insight", "")
    dashboard_url = state.get("dashboard_url")
    recipient_email = state.get("user_email")

    results: dict = {}
    try:
        if channel in ("email", "both") and recipient_email:
            from app.mcp.tools.send_email import send_email
            from app.services.email_templates import render_report_email

            html = render_report_email(
                title="BIthere Report",
                insight=insight or "Dashboard ready.",
                dashboard_url=dashboard_url,
                screenshot_urls=[],
            )
            results["email"] = await send_email(
                to_email=recipient_email,
                subject="[BIthere] Report",
                body=html,
                is_html=True,
            )

        if channel in ("slack", "both"):
            from app.mcp.tools.send_slack import send_slack

            results["slack"] = await send_slack(
                message=insight or "Dashboard ready.",
                dashboard_url=dashboard_url,
            )

        state["report_status"] = results
    except Exception as exc:
        log_error(f"Report sender failed: {exc}")
    return state


async def node_response(state: AgentState) -> AgentState:
    log_process("Node: Response (v2)")

    if state.get("error"):
        state["final_response"] = state["error"]
    else:
        state["final_response"] = state.get("insight") or (
            "Dashboard created. See the right panel." if state.get("dashboard_url") else ""
        )

    key = state.get("cache_key", "")
    should_cache = (
        key and not state.get("error") and state.get("cache_hit") != "full"
        and state.get("final_response")
    )
    if should_cache:
        await cache.set(
            f"{key}:llm",
            {
                "insight": state.get("insight", ""),
                "final_response": state["final_response"],
            },
            ttl=settings.CACHE_LLM_TTL,
        )
    return state


# =====================================================
# Graph
# =====================================================

def build_graph_v2() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("planner", node_planner)
    g.add_node("guard", node_guard)
    g.add_node("rag", node_rag)
    g.add_node("cache_check", node_cache_check)
    g.add_node("query_generator", node_query_generator)
    g.add_node("validator", node_validator)
    g.add_node("optimizer", node_optimizer)
    g.add_node("executor", node_executor)
    g.add_node("analyze", node_insight)
    g.add_node("dashboard", node_dashboard)
    g.add_node("report", node_report)
    g.add_node("response", node_response)

    g.set_entry_point("planner")
    g.add_edge("planner", "guard")
    g.add_conditional_edges(
        "guard",
        route_after_guard,
        {"response": "response", "rag": "rag"},
    )
    g.add_edge("rag", "cache_check")
    g.add_conditional_edges(
        "cache_check",
        route_after_cache,
        {
            "response": "response",
            "insight": "analyze",
            "query_generator": "query_generator",
            "dashboard_only": "dashboard",
        },
    )
    g.add_edge("query_generator", "validator")
    g.add_edge("validator", "optimizer")
    g.add_edge("optimizer", "executor")
    g.add_edge("executor", "analyze")
    g.add_edge("analyze", "dashboard")
    g.add_edge("dashboard", "report")
    g.add_edge("report", "response")
    g.add_edge("response", END)

    return g


def compile_graph_v2():
    """Compile v2 workspace-aware graph."""
    return build_graph_v2().compile()