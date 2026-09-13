"""
LangGraph orchestration for the BIthere agent workflow.

Pipeline (per PRJ 8.4):
    planner -> rag -> cache_check -> query_generator -> validator
    -> optimizer -> executor -> analyze -> dashboard -> report -> response

Cache flow (per PRJ 8.5):
    - full hit  -> skip to response
    - query hit -> skip to analyze (insight)
    - miss      -> run full pipeline

Note: Node "analyze" is used instead of "insight" to avoid a name
collision with the AgentState key "insight" (LangGraph disallows
nodes and state keys sharing the same name).

MVP: no checkpointer (RedisSaver removed due to dependency conflicts).
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
from app.core.logging import log_process, log_info, log_error


class AgentState(TypedDict, total=False):
    """Shared state flowing through all agent nodes."""

    prompt: str
    session_id: str
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
    """Build a deterministic cache key from the user prompt (PRJ 5.4)."""
    normalized = prompt.strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


async def node_planner(state: AgentState) -> AgentState:
    """Step 1: Planner Agent - analyze user intent."""
    log_process("Node: Planner")
    state["plan"] = await planner.plan(state["prompt"])
    return state


async def node_rag(state: AgentState) -> AgentState:
    """Step 2: RAG Retrieval - fetch relevant metadata from Pinecone."""
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


async def node_cache_check(state: AgentState) -> AgentState:
    """Step 3: Cache Check - look up Redis for cached results (PRJ 8.5)."""
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
    """Conditional routing after cache_check (PRJ 8.5)."""
    hit = state.get("cache_hit", "miss")
    if hit == "full":
        return "response"
    if hit == "query":
        return "insight"          # maps to node "analyze" below
    return "query_generator"


async def node_query_generator(state: AgentState) -> AgentState:
    """Step 4: Query Generator - translate NLQ to SQL."""
    log_process("Node: Query Generator")
    state["generated_query"] = await query_generator.generate_query(
        state["prompt"], state.get("metadata_context", "")
    )
    return state


async def node_validator(state: AgentState) -> AgentState:
    """Step 5: Validator - enforce SQL safety rules."""
    log_process("Node: Validator")
    try:
        state["generated_query"] = validator.validate_query(
            state["generated_query"]
        )
    except validator.QueryValidationError as exc:
        log_error(f"Validation failed: {exc}")
        state["error"] = str(exc)
    return state


async def node_optimizer(state: AgentState) -> AgentState:
    """Step 6: Optimizer - apply simple query optimizations."""
    log_process("Node: Optimizer")
    if not state.get("error"):
        state["generated_query"] = optimizer.optimize_query(
            state["generated_query"]
        )
    return state


async def node_executor(state: AgentState) -> AgentState:
    """Step 7: Query Executor - run SQL against Supabase."""
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
        state["error"] = f"Query execution failed: {exc}"
        state["query_result"] = []
    return state


async def node_insight(state: AgentState) -> AgentState:
    """Step 8: Insight Analyzer - summarize results into business insight."""
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


async def node_dashboard(state: AgentState) -> AgentState:
    """Step 9: Dashboard Builder - only if requested by the plan."""
    log_process("Node: Dashboard Builder")
    if state.get("error"):
        return state
    plan = state.get("plan", {})
    if not plan.get("needs_dashboard"):
        log_info("Dashboard not requested, skipping")
        return state
    try:
        result = await dashboard_builder.build_dashboard(
            state["prompt"], state.get("query_result", [])
        )
        state["dashboard_config"] = result.get("config")
        state["dashboard_url"] = result.get("embed_url")
    except Exception as exc:
        log_error(f"Dashboard builder failed: {exc}")
    return state


async def node_report(state: AgentState) -> AgentState:
    """Step 10: Report Sender - only if requested by the plan."""
    log_process("Node: Report Sender")
    if state.get("error"):
        return state
    plan = state.get("plan", {})
    if not plan.get("needs_report"):
        log_info("Report not requested, skipping")
        return state
    try:
        state["report_status"] = await report_sender.send_report(
            insight=state.get("insight", ""),
            channel=plan.get("report_channel", "slack"),
            dashboard_url=state.get("dashboard_url"),
        )
    except Exception as exc:
        log_error(f"Report sender failed: {exc}")
    return state


async def node_response(state: AgentState) -> AgentState:
    """Step 11: Response Builder - format final response and write cache."""
    log_process("Node: Response Builder")

    if state.get("error"):
        state["final_response"] = f"Error: {state['error']}"
    else:
        state["final_response"] = state.get("insight", "")

    cache_key = state.get("cache_key", "")
    should_cache = (
        cache_key
        and not state.get("error")
        and state.get("cache_hit") != "full"
        and state.get("insight")
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


def build_graph() -> StateGraph:
    """Build the agent workflow graph (11 steps, PRJ 8.4)."""
    graph = StateGraph(AgentState)

    graph.add_node("planner", node_planner)
    graph.add_node("rag", node_rag)
    graph.add_node("cache_check", node_cache_check)
    graph.add_node("query_generator", node_query_generator)
    graph.add_node("validator", node_validator)
    graph.add_node("optimizer", node_optimizer)
    graph.add_node("executor", node_executor)
    graph.add_node("analyze", node_insight)      # renamed from "insight"
    graph.add_node("dashboard", node_dashboard)
    graph.add_node("report", node_report)
    graph.add_node("response", node_response)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "rag")
    graph.add_edge("rag", "cache_check")

    graph.add_conditional_edges(
        "cache_check",
        route_after_cache,
        {
            "response": "response",
            "insight": "analyze",              # route key -> node name
            "query_generator": "query_generator",
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
    MVP does not require cross-session persistence.
    """
    return build_graph().compile()