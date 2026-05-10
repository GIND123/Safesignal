<#
.SYNOPSIS
    Deploys SafeSignal A2A agent and MCP server to Google Cloud Run.

.DESCRIPTION
    Full Cloud Run deployment sequence:
      1. Set GCP project and enable required APIs
      2. Store secrets (Google API key, FDA API key, SafeSignal API key)
      3. Deploy the A2A agent  (safesignal-agent)
      4. Deploy the MCP server (safesignal-mcp)
      5. Wire public URLs back into each service
      6. Print the Prompt Opinion setup steps

.USAGE
    .\scripts\deploy_cloud_run.ps1
    .\scripts\deploy_cloud_run.ps1 -SkipSecrets    # if secrets already exist in Secret Manager

.PREREQUISITES
    - gcloud CLI installed: https://cloud.google.com/sdk/docs/install
    - Run once before this script: gcloud auth login
    - Billing enabled on the GCP project
#>

param(
    [string]$Region = "us-central1",
    [switch]$SkipSecrets
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step { param([string]$msg) Write-Host "" ; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$msg) Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Info { param([string]$msg) Write-Host "    $msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$msg) Write-Host "    [ERR] $msg" -ForegroundColor Red ; exit 1 }

function Write-SecretFile {
    param([string]$Value, [string]$SecretName)
    $bytes   = [System.Text.Encoding]::UTF8.GetBytes($Value)
    $tmpFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllBytes($tmpFile, $bytes)

    & gcloud secrets create $SecretName --data-file=$tmpFile
    if ($LASTEXITCODE -ne 0) {
        Write-Info "Secret '$SecretName' already exists -- adding new version."
        & gcloud secrets versions add $SecretName --data-file=$tmpFile
    }
    Remove-Item $tmpFile
    Write-Ok "Secret '$SecretName' stored."
}

# ── Collect inputs ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "SafeSignal -- Cloud Run Deployment" -ForegroundColor White
Write-Host "===================================" -ForegroundColor White

$ProjectId        = Read-Host "`nEnter your GCP Project ID"
if (-not $ProjectId) { Write-Err "Project ID is required." }

$GoogleApiKey     = Read-Host "Enter your Google AI Studio API key (GOOGLE_API_KEY)"
if (-not $GoogleApiKey) { Write-Err "Google API key is required." }

$FdaApiKey        = Read-Host "Enter your FDA OpenFDA API key (FDA_API_KEY) -- press Enter to skip"

$SafesignalApiKey = Read-Host "Enter an API key for the SafeSignal A2A agent (any secret string)"
if (-not $SafesignalApiKey) { Write-Err "SafeSignal API key is required." }

# ── Step 1: Set project ────────────────────────────────────────────────────────
Write-Step "Setting GCP project to $ProjectId"
& gcloud config set project $ProjectId
Write-Ok "Project set."

# ── Step 2: Enable APIs ────────────────────────────────────────────────────────
Write-Step "Enabling Cloud Run, Cloud Build, Artifact Registry, Secret Manager"
& gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    secretmanager.googleapis.com
Write-Ok "APIs enabled."

# ── Step 3: Store secrets ──────────────────────────────────────────────────────
if (-not $SkipSecrets) {
    Write-Step "Storing secrets in Secret Manager"
    Write-SecretFile -Value $GoogleApiKey     -SecretName "google-api-key"
    if ($FdaApiKey) {
        Write-SecretFile -Value $FdaApiKey    -SecretName "fda-api-key"
    }
    Write-SecretFile -Value $SafesignalApiKey -SecretName "safesignal-api-key"
} else {
    Write-Info "Skipping secret creation (-SkipSecrets flag set)."
}

# ── Build secret args string ───────────────────────────────────────────────────
$secretsAgent = "GOOGLE_API_KEY=google-api-key:latest,API_KEYS=safesignal-api-key:latest"
$secretsMcp   = "GOOGLE_API_KEY=google-api-key:latest"
if ($FdaApiKey) {
    $secretsAgent += ",FDA_API_KEY=fda-api-key:latest"
    $secretsMcp   += ",FDA_API_KEY=fda-api-key:latest"
}

# ── Step 4: Deploy A2A agent ───────────────────────────────────────────────────
Write-Step "Deploying SafeSignal A2A agent (safesignal-agent)"
& gcloud run deploy safesignal-agent `
    --source . `
    --region $Region `
    --set-env-vars "AGENT_MODULE=safesignal.app:a2a_app" `
    --set-secrets $secretsAgent `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 3 `
    --timeout 300

if ($LASTEXITCODE -ne 0) { Write-Err "A2A agent deployment failed." }
Write-Ok "A2A agent deployed."

$AgentUrl = (& gcloud run services describe safesignal-agent --region $Region --format "value(status.url)").Trim()
Write-Ok "A2A agent URL: $AgentUrl"

# ── Step 5: Deploy MCP server ──────────────────────────────────────────────────
Write-Step "Deploying SafeSignal MCP server (safesignal-mcp)"
& gcloud run deploy safesignal-mcp `
    --source . `
    --region $Region `
    --set-env-vars "AGENT_MODULE=safesignal_mcp.app:combined_app" `
    --set-secrets $secretsMcp `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 3 `
    --timeout 300

if ($LASTEXITCODE -ne 0) { Write-Err "MCP server deployment failed." }
Write-Ok "MCP server deployed."

$McpUrl = (& gcloud run services describe safesignal-mcp --region $Region --format "value(status.url)").Trim()
Write-Ok "MCP server URL: $McpUrl"

# ── Step 6: Wire URLs back into each service ───────────────────────────────────
Write-Step "Setting public URLs on each service"
& gcloud run services update safesignal-agent --region $Region --update-env-vars "SAFESIGNAL_URL=$AgentUrl"
& gcloud run services update safesignal-mcp   --region $Region --update-env-vars "SAFESIGNAL_MCP_URL=$McpUrl"
Write-Ok "URLs configured."

# ── Step 7: Print Prompt Opinion setup instructions ───────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  A2A Agent URL  : $AgentUrl" -ForegroundColor White
Write-Host "  MCP Server URL : $McpUrl"   -ForegroundColor White
Write-Host "  API Key        : $SafesignalApiKey" -ForegroundColor White
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host " Prompt Opinion steps (app.promptopinion.ai):" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "  STEP 1 -- Register the A2A agent" -ForegroundColor Yellow
Write-Host "     Workspace Hub > Add Connection > External Agent"
Write-Host "     Agent card URL : $AgentUrl/.well-known/agent-card.json"
Write-Host "     API Key        : $SafesignalApiKey"
Write-Host "     Enable 'Pass FHIR context': YES"
Write-Host ""
Write-Host "  STEP 2 -- Connect the MCP server" -ForegroundColor Yellow
Write-Host "     Workspace Hub > Add MCP Server (or 'Add Superpower')"
Write-Host "     URL       : $McpUrl/mcp"
Write-Host "     Transport : Streamable HTTP"
Write-Host "     Pass FHIR context: YES"
Write-Host ""
Write-Host "  STEP 3 -- Load Margaret Chen to HAPI FHIR (if not done already)" -ForegroundColor Yellow
Write-Host "     python scripts\load_synthetic_patient.py --case margaret_chen"
Write-Host ""
Write-Host "  STEP 4 -- Test in PO" -ForegroundColor Yellow
Write-Host "     Launchpad > select patient > select SafeSignal agent"
Write-Host "     Ask: What should I know before seeing this patient today?"
Write-Host ""
