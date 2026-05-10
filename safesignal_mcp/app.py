"""
SafeSignal combined ASGI entry point.

Serves both the MCP server and the A2A agent from a single port so that a
single ngrok / Cloud Run URL covers everything:

  /mcp          → Streamable HTTP MCP   (Prompt Opinion workspace connection)
  /sse          → SSE MCP              (ADK MCPToolset, Claude Desktop)
  /messages     → SSE message handler  (part of SSE transport)
  /.well-known/ → A2A agent card       (agent registration)
  /             → A2A message handler  (Prompt Opinion A2A tasks)

Start with:
    uvicorn safesignal_mcp.app:combined_app --host 0.0.0.0 --port 8005

Prompt Opinion setup (one public URL for everything):
    A2A agent card: https://your-url/.well-known/agent-card.json
    MCP server:     https://your-url/mcp  (Streamable HTTP)
"""
import asyncio
import logging
import os

import uvicorn

from safesignal.app import a2a_app as _a2a_app  # A2A agent served alongside MCP
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


async def _dual_lifespan(scope, receive, send):
    """
    Run lifespan for both _a2a_app (which registers routes on startup via
    setup_a2a) and _http_app (MCP) concurrently so both are fully initialised
    before requests are served.
    """
    a2a_q: asyncio.Queue = asyncio.Queue()
    mcp_q: asyncio.Queue = asyncio.Queue()

    a2a_started = asyncio.Event()
    mcp_started = asyncio.Event()

    async def a2a_send(event):
        if event["type"] == "lifespan.startup.complete":
            a2a_started.set()
        elif event["type"] == "lifespan.startup.failed":
            await send(event)

    async def mcp_send(event):
        if event["type"] == "lifespan.startup.complete":
            mcp_started.set()
        elif event["type"] == "lifespan.startup.failed":
            await send(event)
        elif event["type"] == "lifespan.shutdown.complete":
            await send(event)

    a2a_task = asyncio.create_task(_a2a_app(scope, a2a_q.get, a2a_send))
    mcp_task = asyncio.create_task(_http_app(scope, mcp_q.get, mcp_send))

    startup_event = await receive()
    await a2a_q.put(startup_event)
    await mcp_q.put(startup_event)

    await asyncio.gather(a2a_started.wait(), mcp_started.wait())
    await send({"type": "lifespan.startup.complete"})

    shutdown_event = await receive()
    await a2a_q.put(shutdown_event)
    await mcp_q.put(shutdown_event)

    await asyncio.gather(a2a_task, mcp_task)


async def combined_app(scope, receive, send):
    """
    ASGI dispatcher: routes MCP paths to the MCP transport apps, and
    everything else (A2A agent card, A2A messages) to the A2A app.

      /mcp*          → Streamable HTTP MCP  (Prompt Opinion)
      /sse*          → SSE MCP              (ADK MCPToolset / Claude Desktop)
      /messages*     → SSE messages handler (part of SSE transport)
      /.well-known/* → A2A agent card       (public, no auth)
      /*             → A2A message handler  (Prompt Opinion A2A tasks)

    Both lifespans are run concurrently so A2A routes (registered during
    setup_a2a on startup) and MCP transports are ready before requests arrive.
    """
    if scope["type"] == "lifespan":
        await _dual_lifespan(scope, receive, send)
        return

    path = scope.get("path", "/")

    if path.startswith("/mcp"):
        await _http_app(scope, receive, send)
    elif path.startswith("/sse") or path.startswith("/messages"):
        await _sse_app(scope, receive, send)
    else:
        # /.well-known/agent-card.json, /, and all other A2A paths
        await _a2a_app(scope, receive, send)


# ── Backward-compatible alias ─────────────────────────────────────────────────
# Some tooling references safesignal_mcp.app:sse_app directly.
sse_app = _sse_app


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8005"))
    logger.info("Starting SafeSignal MCP server on port %d (Streamable HTTP at /mcp, SSE at /sse)", port)
    uvicorn.run(combined_app, host="0.0.0.0", port=port, log_level="info")
