"""
SafeSignal MCP Server — ASGI entry point.

Exposes TWO MCP transports from a single port so both connection styles work:

  /mcp   → Streamable HTTP transport  (Prompt Opinion workspace connection)
  /sse   → SSE transport              (ADK MCPToolset, Claude Desktop, legacy clients)
  /      → health check               (Cloud Run health probe)

Start with:
    uvicorn safesignal_mcp.app:combined_app --host 0.0.0.0 --port 8005

Prompt Opinion workspace connection (streamable HTTP):
    URL:       https://your-mcp-url/mcp
    Transport: Streamable HTTP
    Pass FHIR context: yes

ADK MCPToolset connection (SSE):
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
    safesignal_tools = MCPToolset(
        connection_params=SseServerParams(url="https://your-mcp-url/sse")
    )
"""
import logging
import os

import uvicorn

from .server import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Build both transport apps from the same FastMCP instance ──────────────────
# Streamable HTTP — the modern MCP transport; what Prompt Opinion uses.
# Prompt Opinion connects to: POST /mcp
_http_app = mcp.streamable_http_app()

# SSE — legacy transport; used by ADK MCPToolset and Claude Desktop.
# ADK connects to: GET /sse
_sse_app = mcp.sse_app()

# ── Health check response body ─────────────────────────────────────────────────
_HEALTH_BODY = (
    b'{"status":"ok","service":"SafeSignal MCP Server","version":"1.0.0",'
    b'"endpoints":{"/mcp":"Streamable HTTP (Prompt Opinion)","/sse":"SSE (ADK MCPToolset)"}}'
)
_HEALTH_HEADERS = [
    (b"content-type", b"application/json"),
    (b"content-length", str(len(_HEALTH_BODY)).encode()),
]


async def combined_app(scope, receive, send):
    """
    ASGI dispatcher that routes to the correct MCP transport based on path:

      /mcp*      → Streamable HTTP app  (Prompt Opinion)
      /sse*      → SSE app              (ADK MCPToolset / Claude Desktop)
      /messages* → SSE messages handler (part of SSE transport)
      /*         → JSON health check    (Cloud Run probe / browser check)

    Lifespan events are forwarded to the HTTP app as the primary transport.
    """
    if scope["type"] == "lifespan":
        await _http_app(scope, receive, send)
        return

    path = scope.get("path", "/")

    if path.startswith("/mcp"):
        await _http_app(scope, receive, send)
    elif path.startswith("/sse") or path.startswith("/messages"):
        await _sse_app(scope, receive, send)
    elif scope["type"] == "http":
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": _HEALTH_HEADERS,
        })
        await send({"type": "http.response.body", "body": _HEALTH_BODY})
    else:
        await _http_app(scope, receive, send)


# ── Backward-compatible alias ─────────────────────────────────────────────────
# Some tooling references safesignal_mcp.app:sse_app directly.
sse_app = _sse_app


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8005"))
    logger.info("Starting SafeSignal MCP server on port %d (Streamable HTTP at /mcp, SSE at /sse)", port)
    uvicorn.run(combined_app, host="0.0.0.0", port=port, log_level="info")
