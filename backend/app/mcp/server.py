"""
MCP tool server for BIthere.
Exposes all registered tools through a single registry.
"""

from typing import Any, Awaitable, Callable

from app.core.logging import log_process, log_error

from app.mcp.tools.fetch_data import fetch_data
from app.mcp.tools.send_slack import send_slack
from app.mcp.tools.send_email import send_email
from app.mcp.tools.render_dashboard import render_dashboard
from app.mcp.tools.export_pdf import export_pdf


ToolFunc = Callable[..., Awaitable[dict[str, Any]]]


TOOLS: dict[str, ToolFunc] = {
    "fetch_data": fetch_data,
    "send_slack": send_slack,
    "send_email": send_email,
    "render_dashboard": render_dashboard,
    "export_pdf": export_pdf,
}


def list_tools() -> list[dict[str, Any]]:
    """Return metadata about every registered tool."""
    return [
        {
            "name": name,
            "description": (func.__doc__ or "").strip().split("\n")[0],
        }
        for name, func in TOOLS.items()
    ]


def get_tool(name: str) -> ToolFunc | None:
    """Return the tool function by name, or None."""
    return TOOLS.get(name)


async def call_tool(name: str, **kwargs: Any) -> dict[str, Any]:
    """Invoke a registered tool by name using keyword arguments."""
    log_process(f"mcp: call_tool name={name}")
    func = TOOLS.get(name)
    if not func:
        log_error(f"mcp: unknown tool '{name}'")
        return {"success": False, "error": f"Unknown tool: {name}"}

    try:
        return await func(**kwargs)
    except Exception as exc:
        log_error(f"mcp: tool '{name}' raised: {exc}")
        return {"success": False, "error": str(exc)}