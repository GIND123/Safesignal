"""
SafeSignal MCP Server — ASGI entry point.

Start the SSE server with:
    uvicorn safesignal_mcp.app:sse_app --host 0.0.0.0 --port 8005

The MCP server is accessible at:
    http://localhost:8005/sse           (SSE transport endpoint)
    http://localhost:8005/              (health check / server info)

Connecting from an ADK agent via MCPToolset:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
    safesignal_tools = MCPToolset(
        connection_params=SseServerParams(url="http://safesignal-mcp:8005/sse")
    )

Connecting from Claude Desktop / other MCP clients:
    Use the SSE URL: http://localhost:8005/sse
"""
import logging
import os

import uvicorn

from .server import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Build the SSE ASGI application from the FastMCP instance.
sse_app = mcp.sse_app()


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8005"))
    logger.info("Starting SafeSignal MCP server on port %d", port)
    uvicorn.run(sse_app, host="0.0.0.0", port=port, log_level="info")
