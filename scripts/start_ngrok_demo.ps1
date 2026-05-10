<#
.SYNOPSIS
    Starts SafeSignal servers locally and exposes them via ngrok for demo.

.DESCRIPTION
    Fastest path to connecting SafeSignal to Prompt Opinion without Cloud Run.
    Use this to record your demo video or test the PO integration.

    Steps performed automatically:
      1. Start A2A agent on port 8004
      2. Start MCP server  on port 8005
      3. Create ngrok tunnels for both ports
      4. Print the URLs and exact steps to follow in Prompt Opinion

.PREREQUISITES
    - Python venv at .venv\  (run: python -m venv .venv then pip install -r requirements.txt)
    - .env file with GOOGLE_API_KEY, FDA_API_KEY, API_KEYS set
    - ngrok installed: https://ngrok.com/download
      (free account needed, then: ngrok config add-authtoken YOUR_TOKEN)
    - Margaret Chen loaded: python scripts\load_synthetic_patient.py --case margaret_chen

.USAGE
    .\scripts\start_ngrok_demo.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot  = Split-Path $PSScriptRoot -Parent
$VenvPython   = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
$EnvFile      = Join-Path $ProjectRoot ".env"

function Write-Step { param([string]$msg) Write-Host "" ; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$msg) Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Info { param([string]$msg) Write-Host "    $msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$msg) Write-Host "    [ERR] $msg" -ForegroundColor Red ; exit 1 }

# ── Prerequisite checks ────────────────────────────────────────────────────────
Write-Step "Checking prerequisites"

if (-not (Test-Path $VenvPython)) {
    Write-Err ".venv not found. Run: python -m venv .venv  then  .venv\Scripts\pip install -r requirements.txt"
}
Write-Ok "Python venv found."

if (-not (Test-Path $EnvFile)) {
    Write-Err ".env not found. Copy .env.example to .env and fill in GOOGLE_API_KEY, FDA_API_KEY, API_KEYS."
}
Write-Ok ".env found."

$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokPath) {
    Write-Err "ngrok not found. Install from https://ngrok.com/download then run: ngrok config add-authtoken YOUR_TOKEN"
}
Write-Ok "ngrok found at $($ngrokPath.Source)."

# ── Read API key from .env for display ─────────────────────────────────────────
$ApiKey = ""
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match "^API_KEYS=(.+)$"       -and -not $ApiKey) { $ApiKey = $Matches[1].Trim().Split(",")[0].Trim() }
    if ($_ -match "^API_KEY_PRIMARY=(.+)$" -and -not $ApiKey) { $ApiKey = $Matches[1].Trim() }
}

if (-not $ApiKey) {
    Write-Info "WARNING: API_KEYS not set in .env. The A2A agent will reject all requests."
    Write-Info "         Add  API_KEYS=your-secret-key  to .env then re-run this script."
} else {
    $preview = $ApiKey.Substring(0, [Math]::Min(6, $ApiKey.Length))
    Write-Ok "API key found: $preview..."
}

# ── Start A2A agent in a new terminal ─────────────────────────────────────────
Write-Step "Starting A2A agent on port 8004"

$agentArgs = @(
    "-NoExit",
    "-Command",
    "cd '$ProjectRoot'; & '$VenvActivate'; uvicorn safesignal.app:a2a_app --host 0.0.0.0 --port 8004 --log-level info"
)
Start-Process powershell -ArgumentList $agentArgs
Write-Ok "A2A agent starting in new terminal window."
Start-Sleep -Seconds 4

# ── Start MCP server in a new terminal ────────────────────────────────────────
Write-Step "Starting MCP server on port 8005"

$mcpArgs = @(
    "-NoExit",
    "-Command",
    "cd '$ProjectRoot'; & '$VenvActivate'; uvicorn safesignal_mcp.app:combined_app --host 0.0.0.0 --port 8005 --log-level info"
)
Start-Process powershell -ArgumentList $mcpArgs
Write-Ok "MCP server starting in new terminal window."
Start-Sleep -Seconds 4

# ── Wait for servers to be ready ───────────────────────────────────────────────
Write-Step "Waiting for servers to be ready"

$agentOk = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8004/.well-known/agent-card.json" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $agentOk = $true ; break }
    } catch { }
    Write-Info "Waiting for A2A agent... ($i/15)"
    Start-Sleep -Seconds 2
}

$mcpOk = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8005/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $mcpOk = $true ; break }
    } catch { }
    Write-Info "Waiting for MCP server... ($i/15)"
    Start-Sleep -Seconds 2
}

if (-not $agentOk) { Write-Err "A2A agent not responding on port 8004. Check the agent terminal window for errors." }
Write-Ok "A2A agent is up on port 8004."

if (-not $mcpOk) { Write-Err "MCP server not responding on port 8005. Check the MCP terminal window for errors." }
Write-Ok "MCP server is up on port 8005."

# ── Start ngrok with both tunnels ──────────────────────────────────────────────
Write-Step "Creating ngrok tunnels for both ports"

$ngrokConfig = @"
version: "2"
tunnels:
  safesignal-agent:
    proto: http
    addr: 8004
  safesignal-mcp:
    proto: http
    addr: 8005
"@

$ngrokConfigPath = Join-Path $env:TEMP "safesignal_ngrok.yml"
Set-Content -Path $ngrokConfigPath -Value $ngrokConfig -Encoding utf8

Start-Process ngrok -ArgumentList "start", "--all", "--config", $ngrokConfigPath
Write-Info "ngrok starting... waiting 6 seconds for tunnels to open."
Start-Sleep -Seconds 6

# ── Read tunnel URLs from ngrok API ───────────────────────────────────────────
$AgentUrl = ""
$McpUrl   = ""

try {
    $tunnels = (Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop).tunnels
    foreach ($t in $tunnels) {
        $pub = $t.public_url -replace "^http:", "https:"
        if ($t.config.addr -match ":8004") { $AgentUrl = $pub }
        if ($t.config.addr -match ":8005") { $McpUrl   = $pub }
    }
} catch {
    Write-Info "Could not auto-read ngrok URLs from API."
    Write-Info "Open http://localhost:4040 in your browser to find the tunnel URLs."
}

# ── Print setup instructions ───────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " SERVERS RUNNING -- Prompt Opinion Setup" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

if ($AgentUrl) {
    Write-Host "  A2A Agent URL  : $AgentUrl" -ForegroundColor White
} else {
    Write-Host "  A2A Agent URL  : see ngrok dashboard at http://localhost:4040  (port 8004 tunnel)" -ForegroundColor Yellow
}

if ($McpUrl) {
    Write-Host "  MCP Server URL : $McpUrl" -ForegroundColor White
} else {
    Write-Host "  MCP Server URL : see ngrok dashboard at http://localhost:4040  (port 8005 tunnel)" -ForegroundColor Yellow
}

Write-Host "  API Key        : $ApiKey" -ForegroundColor White
Write-Host "  ngrok dashboard: http://localhost:4040" -ForegroundColor White
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host " Prompt Opinion steps (app.promptopinion.ai):" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "  STEP 1 -- Register the A2A agent" -ForegroundColor Yellow
Write-Host "     Workspace Hub > Add Connection > External Agent"
if ($AgentUrl) {
    Write-Host "     Agent card URL : $AgentUrl/.well-known/agent-card.json"
} else {
    Write-Host "     Agent card URL : {port-8004-ngrok-url}/.well-known/agent-card.json"
}
Write-Host "     API Key        : $ApiKey"
Write-Host "     Enable 'Pass FHIR context': YES"
Write-Host ""
Write-Host "  STEP 2 -- Connect the MCP server" -ForegroundColor Yellow
Write-Host "     Workspace Hub > Add MCP Server (or 'Add Superpower')"
if ($McpUrl) {
    Write-Host "     URL       : $McpUrl/mcp"
} else {
    Write-Host "     URL       : {port-8005-ngrok-url}/mcp"
}
Write-Host "     Transport : Streamable HTTP"
Write-Host "     Pass FHIR context: YES"
Write-Host ""
Write-Host "  STEP 3 -- Load Margaret Chen to HAPI FHIR (if not done already)" -ForegroundColor Yellow
Write-Host "     python scripts\load_synthetic_patient.py --case margaret_chen"
Write-Host ""
Write-Host "  STEP 4 -- Test in PO" -ForegroundColor Yellow
Write-Host "     Launchpad > select a patient > select SafeSignal agent"
Write-Host "     Ask: What should I know before seeing this patient today?"
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "  Keep ALL terminal windows open while using the demo." -ForegroundColor Yellow
Write-Host "  ngrok tunnels close when the ngrok window is closed." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
