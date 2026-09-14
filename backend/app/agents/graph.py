"""
LangGraph orchestration for the BIthere agent workflow.

Pipeline (per PRJ 8.4):
    planner -> guard -> rag -> cache_check
        -> (query pipeline)  query_generator -> validator -> optimizer
                            -> executor -> analyze
        -> (dashboard only)  dashboard_builder
        -> report -> response

Cache flow (per PRJ 8.5):
    - full hit  -> skip to response
    - query hit -> skip to analyze (insight)
    - miss      -> run full pipeline

Guard flow:
    - out-of-scope question -> skip to response with refusal message
    - vague question        -> skip to response with clarification hint

Note: Node "analyze" is used instead of "insight" to avoid a name
collision with the AgentState key "insight".
"""

import hashlib
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.agents import (
    planner,
    query_generator,
    validator,
    optimizer,
    insight_analyzer,
    dashboard_builder,
    report_sender,
)
from app.connectors import get_connector
from app.rag.pinecone_client import pinecone_client
from app.rag.embedding import embed_text
from app.services.cache import cache
from app.core.config import settings
from app.core.logging import log_process, log_info, log_error, log_warning


class AgentState(TypedDict, total=False):
    """Shared state flowing through all agent nodes."""

    prompt: str
    session_id: str
    user_email: str
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


def _build_cache_key(prompt: str) -> str:
    """Build a deterministic cache key from the user prompt."""
    normalized = prompt.strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------
# Node: Planner
# ---------------------------------------------------------------------
async def node_planner(state: AgentState) -> AgentState:
    """Step 1: Planner Agent - analyze user intent and scope."""
    log_process("Node: Planner")
    state["plan"] = await planner.plan(state["prompt"])
    return state


# ---------------------------------------------------------------------
# Node: Guard
# ---------------------------------------------------------------------
async def node_guard(state: AgentState) -> AgentState:
    """Step 2: Guard - reject out-of-scope or too-vague questions."""
    log_process("Node: Guard")
    plan = state.get("plan", {})

    if not plan.get("is_in_scope", True):
        if plan.get("clarification_needed"):
            hint = plan.get("clarification_hint", "").strip()
            if hint:
                state["error"] = (
                    "Your question is too broad. Please be more specific — "
                    f'for example: "{hint}"'
                )
            else:
                state["error"] = (
                    "Your question is too broad. Please specify the table, "
                    "column, or metric you would like to analyze."
                )
            log_info("Question is too vague, asking for clarification")
        else:
            state["error"] = (
                "I can only answer questions about the fintech fraud "
                "dataset (transactions, customers, cards, fraud labels, "
                "and merchants). Your question is out of scope."
            )
            log_info("Question is out of scope, short-circuiting to response")
    return state


def route_after_guard(state: AgentState) -> str:
    """Conditional routing after guard."""
    if state.get("error"):
        return "response"
    return "rag"


# ---------------------------------------------------------------------
# Node: RAG Retrieval
# ---------------------------------------------------------------------
async def node_rag(state: AgentState) -> AgentState:
    """Step 3: RAG Retrieval - fetch relevant metadata from Pinecone."""
    log_process("Node: RAG Retrieval")
    try:
        vector = await embed_text(state["prompt"])
        matches = pinecone_client.query(vector, namespace="schema", top_k=5)
        context_lines = [
            m.get("metadata", {}).get("text", "")
            for m in matches
            if m.get("metadata", {}).get("text")
        ]
        state["metadata_context"] = "\n".join(context_lines)
        log_info(f"Retrieved {len(context_lines)} metadata items from Pinecone")
    except Exception as exc:
        log_error(f"RAG retrieval failed: {exc}")
        state["metadata_context"] = ""
    return state


# ---------------------------------------------------------------------
# Node: Cache Check
# ---------------------------------------------------------------------
async def node_cache_check(state: AgentState) -> AgentState:
    """Step 4: Cache Check - look up Redis for cached results."""
    log_process("Node: Cache Check")
    cache_key = _build_cache_key(state["prompt"])
    state["cache_key"] = cache_key

    cached_llm = await cache.get(f"llm:{cache_key}")
    if cached_llm and cached_llm.get("final_response"):
        state["cache_hit"] = "full"
        state["final_response"] = cached_llm.get("final_response", "")
        state["insight"] = cached_llm.get("insight", "")
        log_info(f"Cache HIT (full) for key llm:{cache_key}")
        return state

    cached_query = await cache.get(f"query:{cache_key}")
    if cached_query and cached_query.get("query_result") is not None:
        state["cache_hit"] = "query"
        state["generated_query"] = cached_query.get("generated_query", "")
        state["query_result"] = cached_query.get("query_result", [])
        log_info(f"Cache HIT (query) for key query:{cache_key}")
        return state

    state["cache_hit"] = "miss"
    log_info(f"Cache MISS for key {cache_key}")
    return state


def route_after_cache(state: AgentState) -> str:
    """
    Conditional routing after cache_check.

    Priority:
    1. Full cache hit -> response
    2. Query cache hit -> analyze
    3. Dashboard-only intent -> dashboard builder (skip query pipeline)
    4. Otherwise -> query generator
    """
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
        log_info("Route: dashboard-only mode, skipping query pipeline")
        return "dashboard_only"

    return "query_generator"


# ---------------------------------------------------------------------
# Node: Query Generator
# ---------------------------------------------------------------------
async def node_query_generator(state: AgentState) -> AgentState:
    """Step 5: Query Generator - translate NLQ to SQL."""
    log_process("Node: Query Generator")
    state["generated_query"] = await query_generator.generate_query(
        state["prompt"], state.get("metadata_context", "")
    )
    return state


# ---------------------------------------------------------------------
# Node: Validator
# ---------------------------------------------------------------------
async def node_validator(state: AgentState) -> AgentState:
    """Step 6: Validator - enforce SQL safety rules."""
    log_process("Node: Validator")
    try:
        state["generated_query"] = validator.validate_query(
            state["generated_query"]
        )
    except validator.QueryValidationError as exc:
        log_error(f"Validation failed: {exc}")
        state["error"] = str(exc)
    return state


# ---------------------------------------------------------------------
# Node: Optimizer
# ---------------------------------------------------------------------
async def node_optimizer(state: AgentState) -> AgentState:
    """Step 7: Optimizer - apply simple query optimizations."""
    log_process("Node: Optimizer")
    if not state.get("error"):
        state["generated_query"] = optimizer.optimize_query(
            state["generated_query"]
        )
    return state


# ---------------------------------------------------------------------
# Node: Query Executor
# ---------------------------------------------------------------------
async def node_executor(state: AgentState) -> AgentState:
    """Step 8: Query Executor - run SQL against Supabase."""
    log_process("Node: Query Executor")
    if state.get("error"):
        return state
    try:
        connector = get_connector()
        state["query_result"] = await connector.execute_query(
            state["generated_query"]
        )
        log_info(f"Query returned {len(state['query_result'])} rows")

        cache_key = state.get("cache_key", "")
        if cache_key:
            await cache.set(
                f"query:{cache_key}",
                {
                    "generated_query": state["generated_query"],
                    "query_result": state["query_result"],
                },
                ttl=settings.CACHE_QUERY_TTL,
            )
            log_info(f"Cached query result with key query:{cache_key}")
    except Exception as exc:
        log_error(f"Query execution failed: {exc}")
        log_error(
            f"Failed SQL preview: {state.get('generated_query', '')[:500]}"
        )
        state["error"] = f"Query execution failed: {exc}"
        state["query_result"] = []
    return state


# ---------------------------------------------------------------------
# Node: Insight Analyzer
# ---------------------------------------------------------------------
async def node_insight(state: AgentState) -> AgentState:
    """Step 9: Insight Analyzer - summarize results into business insight."""
    log_process("Node: Insight Analyzer")
    if state.get("error"):
        return state
    try:
        state["insight"] = await insight_analyzer.analyze(
            state["prompt"], state.get("query_result", [])
        )
    except Exception as exc:
        log_error(f"Insight analyzer failed: {exc}")
        state["insight"] = "Failed to generate insight from query results."
    return state


# ---------------------------------------------------------------------
# Node: Dashboard Builder
# ---------------------------------------------------------------------
async def node_dashboard(state: AgentState) -> AgentState:
    """Step 10: Dashboard Builder - generate dashboard config from prompt."""
    log_process("Node: Dashboard Builder")

    if state.get("error"):
        return state

    try:
        result = await dashboard_builder.build_dashboard(
            state["prompt"], state.get("query_result") or []
        )
        state["dashboard_config"] = result.get("config")
        state["dashboard_url"] = result.get("embed_url")

        if not result.get("success"):
            log_warning(f"Dashboard build failed: {result.get('error')}")
            return state

        if not state.get("insight") and result.get("config"):
            config = result["config"]
            pages = config.get("pages") or []
            chart_count = sum(len(p.get("charts", [])) for p in pages)
            if not pages and config.get("charts"):
                chart_count = len(config.get("charts"))
            title = config.get("title", "Fraud Analytics Dashboard")
            filter_count = len(config.get("filters", []))
            page_count = max(len(pages), 1)

            state["insight"] = (
                f"Dashboard '{title}' was created successfully with "
                f"{page_count} page(s) and {chart_count} interactive charts. "
                f"{filter_count} filter(s) are available for data exploration.\n\n"
                f"Next steps:\n"
                f"1. Open the dashboard in the right panel to view the visualizations.\n"
                f"2. Use the filters and click on charts to explore specific segments.\n"
                f"3. Send the report to Email or Slack using the "
                f"'Kirim Laporan' button."
            )
            log_info("Auto-generated insight from dashboard config")

    except Exception as exc:
        log_error(f"Dashboard builder failed: {exc}")

    return state


# ---------------------------------------------------------------------
# Node: Report Sender
# ---------------------------------------------------------------------
async def node_report(state: AgentState) -> AgentState:
    """Step 11: Report Sender - capture screenshots and dispatch."""
    log_process("Node: Report Sender")
    if state.get("error"):
        return state

    plan = state.get("plan", {})
    if not plan.get("needs_report"):
        log_info("Report not requested, skipping")
        return state

    channel = plan.get("report_channel", "email")
    insight = state.get("insight", "")
    dashboard_url = state.get("dashboard_url")
    recipient_email = state.get("user_email")

    log_info(f"Report dispatch: channel={channel} recipient={recipient_email}")

    # Capture screenshots if there is a dashboard
    screenshot_urls: list[str] = []
    if dashboard_url:
        try:
            from app.services.dashboard_screenshot import (
                capture_dashboard_screenshots,
            )
            from app.services.storage import upload_screenshot

            session_id = state.get("session_id", "default")[:8]
            paths = await capture_dashboard_screenshots(
                dashboard_url, prefix=f"report_{session_id}"
            )
            for idx, path in enumerate(paths):
                remote_name = (
                    f"reports/{session_id}/tab_{idx:02d}.png"
                )
                url = upload_screenshot(path, remote_name)
                if url:
                    screenshot_urls.append(url)

            log_info(f"Report screenshots uploaded: {len(screenshot_urls)}")
        except Exception as exc:
            log_error(f"screenshot pipeline failed: {exc}")

    results: dict = {}

    try:
        if channel in ("email", "both"):
            if recipient_email:
                from app.mcp.tools.send_email import send_email
                from app.services.email_templates import render_report_email

                html = render_report_email(
                    title="BIthere Fraud Report",
                    insight=insight or "BIthere dashboard is ready.",
                    dashboard_url=dashboard_url,
                    screenshot_urls=screenshot_urls,
                )
                results["email"] = await send_email(
                    to_email=recipient_email,
                    subject="[BIthere] Fraud Report",
                    body=html,
                    is_html=True,
                )
                log_info(
                    f"Report email success: {results['email'].get('success')}"
                )
            else:
                log_warning("Report email skipped: no recipient email")

        if channel in ("slack", "both"):
            from app.mcp.tools.send_slack import send_slack

            results["slack"] = await send_slack(
                message=insight or "BIthere dashboard is ready.",
                dashboard_url=dashboard_url,
            )
            log_info(
                f"Report slack success: {results['slack'].get('success')}"
            )

        state["report_status"] = results
    except Exception as exc:
        log_error(f"Report sender failed: {exc}")

    return state


# ---------------------------------------------------------------------
# Node: Response Builder
# ---------------------------------------------------------------------
async def node_response(state: AgentState) -> AgentState:
    """Step 12: Response Builder - format final response and cache."""
    log_process("Node: Response Builder")

    if state.get("error"):
        state["final_response"] = state["error"]
    else:
        insight = state.get("insight") or ""
        dashboard_url = state.get("dashboard_url")
        if not insight and dashboard_url:
            state["final_response"] = (
                "Dashboard created successfully. See the right panel "
                "for interactive visualizations."
            )
        else:
            state["final_response"] = insight

    cache_key = state.get("cache_key", "")
    should_cache = (
        cache_key
        and not state.get("error")
        and state.get("cache_hit") != "full"
        and state.get("final_response")
    )
    if should_cache:
        await cache.set(
            f"llm:{cache_key}",
            {
                "insight": state.get("insight", ""),
                "final_response": state["final_response"],
            },
            ttl=settings.CACHE_LLM_TTL,
        )
        log_info(f"Cached final response with key llm:{cache_key}")

    return state


# ---------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------
def build_graph() -> StateGraph:
    """Build the agent workflow graph."""
    graph = StateGraph(AgentState)

    graph.add_node("planner", node_planner)
    graph.add_node("guard", node_guard)
    graph.add_node("rag", node_rag)
    graph.add_node("cache_check", node_cache_check)
    graph.add_node("query_generator", node_query_generator)
    graph.add_node("validator", node_validator)
    graph.add_node("optimizer", node_optimizer)
    graph.add_node("executor", node_executor)
    graph.add_node("analyze", node_insight)
    graph.add_node("dashboard", node_dashboard)
    graph.add_node("report", node_report)
    graph.add_node("response", node_response)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "guard")
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {
            "response": "response",
            "rag": "rag",
        },
    )

    graph.add_edge("rag", "cache_check")
    graph.add_conditional_edges(
        "cache_check",
        route_after_cache,
        {
            "response": "response",
            "insight": "analyze",
            "query_generator": "query_generator",
            "dashboard_only": "dashboard",
        },
    )

    graph.add_edge("query_generator", "validator")
    graph.add_edge("validator", "optimizer")
    graph.add_edge("optimizer", "executor")
    graph.add_edge("executor", "analyze")
    graph.add_edge("analyze", "dashboard")
    graph.add_edge("dashboard", "report")
    graph.add_edge("report", "response")
    graph.add_edge("response", END)

    return graph


def compile_graph():
    """
    Compile the agent workflow without a checkpointer.

    RedisSaver is intentionally omitted: langgraph-checkpoint-redis
    conflicts with the langgraph 0.2.x pin used in this project.
    """
    return build_graph().compile()