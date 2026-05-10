# ── SafeSignal — Cloud Run container ─────────────────────────────────────────
#
# Single Dockerfile for both SafeSignal services.
# AGENT_MODULE env var selects which service to start at runtime,
# so each Cloud Run service gets its own deployment with a different value.
#
# Local build + test:
#   docker build -t safesignal .
#
#   # A2A agent (port 8004 locally, 8080 in Cloud Run)
#   docker run --rm -p 8080:8080 \
#     -e AGENT_MODULE=safesignal.app:a2a_app \
#     -e GOOGLE_API_KEY=your-key \
#     -e FDA_API_KEY=your-fda-key \
#     -e API_KEYS=your-api-key \
#     safesignal
#
#   # MCP server (port 8005 locally, 8080 in Cloud Run)
#   docker run --rm -p 8080:8080 \
#     -e AGENT_MODULE=safesignal_mcp.app:combined_app \
#     -e GOOGLE_API_KEY=your-key \
#     -e FDA_API_KEY=your-fda-key \
#     safesignal
#
# Cloud Run deployment (see scripts/deploy_cloud_run.ps1 for full automation):
#
#   A2A agent:
#   gcloud run deploy safesignal-agent \
#     --source . \
#     --set-env-vars "AGENT_MODULE=safesignal.app:a2a_app" \
#     --set-secrets "GOOGLE_API_KEY=google-api-key:latest,FDA_API_KEY=fda-api-key:latest,API_KEYS=safesignal-api-key:latest"
#
#   MCP server:
#   gcloud run deploy safesignal-mcp \
#     --source . \
#     --set-env-vars "AGENT_MODULE=safesignal_mcp.app:combined_app" \
#     --set-secrets "GOOGLE_API_KEY=google-api-key:latest,FDA_API_KEY=fda-api-key:latest"

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first so this layer is cached between code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full source tree.
COPY . .

# Cloud Run sets PORT=8080 automatically; override for local Docker testing.
ENV PORT=8080

# Which SafeSignal module to serve. Set via --set-env-vars at deploy time.
#   A2A agent:  safesignal.app:a2a_app
#   MCP server: safesignal_mcp.app:combined_app
ENV AGENT_MODULE=safesignal.app:a2a_app

# exec replaces the shell so uvicorn is PID 1 and receives SIGTERM from Cloud Run.
CMD ["sh", "-c", "exec uvicorn ${AGENT_MODULE} --host 0.0.0.0 --port ${PORT}"]
