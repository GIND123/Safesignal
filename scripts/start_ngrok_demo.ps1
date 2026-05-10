<#
.SYNOPSIS
    Starts SafeSignal (combined A2A + MCP server) and exposes it via ngrok.

.DESCRIPTION
    Runs everything from a single port (8005) so only one ngrok tunnel is needed.
    Both the A2A agent and MCP server are accessible at the same public URL:

      {url}/.well-known/agent-card.json  -- A2A agent card
      {url}/                             -- A2A messages
      {url}/mcp                          -- MCP Streamable HTTP (Prompt Opinion)
      {url}/sse                          -- MCP SSE (ADK MCPToolset)

.PREREQUISITES
    - .env file with GOOGLE_API_KEY, FDA_API_KEY, API_KEYS set
    - ngrok auth token configured:  ngrok config add-authtoken YOUR_TOKEN
    - (optional) Load demo patient: python scripts\load_synthetic_patient.py --case margaret_chen

.USAGE
    .\scripts\start_ngrok_demo.ps1

    Tail server logs:
      Get-Content $env:TEMP\safesignal_combined.log -Wait

    Stop everything:
      Stop-Job -Name safesignal-* ; Remove-Job -Name safesignal-*
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$VenvUvicorn = Join-Path $ProjectRoot ".venv\Scripts\uvicorn.exe"
$EnvFile     = Join-Path $ProjectRoot ".env"
$ServerLog   = Join-Path $env:TEMP "safesignal_combined.log"

function Write-Step { param([string]$msg) Write-Host "" ; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$msg) Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Info { param([string]$msg) Write-Host "    $msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$msg) Write-Host "    [ERR] $msg" -ForegroundColor Red ; exit 1 }

function Wait-ForStartup {
    param([System.Management.Automation.Job]$Job, [string]$LogPath, [string]$Name, [int]$TimeoutSec = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $dots = 0
    while ((Get-Date) -lt $deadline) {
        if ($Job.State -eq "Failed") {
            Write-Info "$Name job failed. Last output:"
            Receive-Job $Job 2>&1 | Select-Object -Last 15 | ForEach-Object { Write-Info "  $_" }
            Write-Err "$Name failed to start."
        }
        if (Test-Path $LogPath) {
            $content = Get-Content $LogPath -Raw -ErrorAction SilentlyContinue
            if ($content -match "Application startup complete") {
                Write-Ok "$Name is up."
                return
            }
        }
        $dots++
        Write-Info "Waiting for $Name... ($dots)"
        Start-Sleep -Seconds 3
    }
    Write-Info "$Name did not start within $TimeoutSec seconds. Last log:"
    if (Test-Path $LogPath) { Get-Content $LogPath | Select-Object -Last 20 | ForEach-Object { Write-Info "  $_" } }
    Write-Err "$Name timed out."
}

# ── Prerequisite checks ────────────────────────────────────────────────────────
Write-Step "Checking prerequisites"

if (-not (Test-Path $VenvUvicorn)) {
    Write-Err ".venv\Scripts\uvicorn.exe not found. Run: python -m venv .venv  then  .venv\Scripts\pip install -r requirements.txt"
}
Write-Ok "Python venv found."

if (-not (Test-Path $EnvFile)) {
    Write-Err ".env not found. Copy .env.example to .env and fill in GOOGLE_API_KEY, FDA_API_KEY, API_KEYS."
}
Write-Ok ".env found."

if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Err "ngrok not found. Run: winget install ngrok.ngrok  then  ngrok config add-authtoken YOUR_TOKEN"
}
Write-Ok "ngrok found."

# ── Read API key from .env ─────────────────────────────────────────────────────
$ApiKey = ""
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match "^API_KEYS=(.+)$"        -and -not $ApiKey) { $ApiKey = $Matches[1].Trim().Split(",")[0].Trim() }
    if ($_ -match "^API_KEY_PRIMARY=(.+)$"  -and -not $ApiKey) { $ApiKey = $Matches[1].Trim() }
}
if (-not $ApiKey) {
    Write-Info "WARNING: API_KEYS not set in .env -- the A2A agent will reject all requests."
} else {
    Write-Ok "API key loaded: $($ApiKey.Substring(0,[Math]::Min(6,$ApiKey.Length)))..."
}

# ── Kill any existing SafeSignal jobs ─────────────────────────────────────────
Get-Job -Name "safesignal-*" -ErrorAction SilentlyContinue | Stop-Job -PassThru | Remove-Job -ErrorAction SilentlyContinue

# ── Start ngrok FIRST so we know the public URL before the server starts ───────
Write-Step "Starting ngrok tunnel on port 8005"

$ngrokConfigPath = Join-Path $env:TEMP "safesignal_ngrok.yml"
$ngrokDefaultCfg = Join-Path $env:USERPROFILE "AppData\Local\ngrok\ngrok.yml"

$ngrokConfig = @"
version: "2"
tunnels:
  safesignal:
    proto: http
    addr: 8005
"@
Set-Content -Path $ngrokConfigPath -Value $ngrokConfig -Encoding utf8

Start-Job -Name "safesignal-ngrok" -ScriptBlock {
    param($cfg, $defCfg)
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
    if (Test-Path $defCfg) {
        & ngrok start --all --config $defCfg --config $cfg *>&1
    } else {
        & ngrok start --all --config $cfg *>&1
    }
} -ArgumentList $ngrokConfigPath, $ngrokDefaultCfg | Out-Null

# ── Read the ngrok URL (retry for up to 30 seconds) ───────────────────────────
Write-Info "Waiting for ngrok tunnel..."
$PublicUrl = ""
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Seconds 3
    try {
        $tunnels = (Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop).tunnels
        foreach ($t in $tunnels) {
            $u = $t.public_url -replace "^http:", "https:"
            if ($u -match "^https://") { $PublicUrl = $u ; break }
        }
        if ($PublicUrl) { break }
    } catch { }
}
if (-not $PublicUrl) {
    Write-Info "Could not auto-detect ngrok URL. Check http://localhost:4040"
    $PublicUrl = "http://localhost:8005"
}
Write-Ok "Public URL: $PublicUrl"

# ── Start combined server (A2A + MCP) on port 8005 ───────────────────────────
Write-Step "Starting SafeSignal combined server on port 8005"
Remove-Item $ServerLog -ErrorAction SilentlyContinue

$serverJob = Start-Job -Name "safesignal-server" -ScriptBlock {
    param($root, $uvicorn, $log, $pubUrl)
    Set-Location $root
    $env:SAFESIGNAL_URL = $pubUrl
    # Load remaining env vars from .env file
    if (Test-Path (Join-Path $root ".env")) {
        Get-Content (Join-Path $root ".env") | ForEach-Object {
            if ($_ -match "^([A-Z_]+)=(.+)$") {
                $n = $Matches[1] ; $v = $Matches[2].Trim()
                if (-not [System.Environment]::GetEnvironmentVariable($n)) {
                    [System.Environment]::SetEnvironmentVariable($n, $v)
                }
            }
        }
    }
    & $uvicorn safesignal_mcp.app:combined_app --host 0.0.0.0 --port 8005 --log-level info *>&1 |
        ForEach-Object { $_ | Out-File -FilePath $log -Append -Encoding utf8 ; $_ }
} -ArgumentList $ProjectRoot, $VenvUvicorn, $ServerLog, $PublicUrl

Write-Ok "Server job started. Log: $ServerLog"

# ── Wait for server startup ────────────────────────────────────────────────────
Write-Step "Waiting for combined server to be ready (up to 2 minutes)"
Wait-ForStartup -Job $serverJob -LogPath $ServerLog -Name "SafeSignal combined server"

# ── Print Prompt Opinion setup ─────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " SAFESIGNAL RUNNING -- Prompt Opinion Setup" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Public URL : $PublicUrl" -ForegroundColor White
Write-Host "  API Key    : $ApiKey" -ForegroundColor White
Write-Host "  ngrok UI   : http://localhost:4040" -ForegroundColor White
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host " Prompt Opinion steps  (app.promptopinion.ai):" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "  STEP 1 -- Register the A2A agent" -ForegroundColor Yellow
Write-Host "     Workspace Hub > Add Connection > External Agent"
Write-Host "     Agent card URL : $PublicUrl/.well-known/agent-card.json"
Write-Host "     API Key        : $ApiKey"
Write-Host "     Enable Pass FHIR context : YES"
Write-Host ""
Write-Host "  STEP 2 -- Connect the MCP server" -ForegroundColor Yellow
Write-Host "     Workspace Hub > Add MCP Server"
Write-Host "     URL       : $PublicUrl/mcp"
Write-Host "     Transport : Streamable HTTP"
Write-Host "     Enable Pass FHIR context : YES"
Write-Host ""
Write-Host "  STEP 3 -- Load demo patient (if not done already)" -ForegroundColor Yellow
Write-Host "     python scripts\load_synthetic_patient.py --case margaret_chen"
Write-Host ""
Write-Host "  STEP 4 -- Test in Prompt Opinion" -ForegroundColor Yellow
Write-Host "     Launchpad > select patient > select SafeSignal"
Write-Host "     Ask: What should I know before seeing this patient today?"
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host " Tail server log:" -ForegroundColor Yellow
Write-Host "   Get-Content $ServerLog -Wait" -ForegroundColor White
Write-Host " Stop everything:" -ForegroundColor Yellow
Write-Host "   Stop-Job -Name safesignal-* ; Remove-Job -Name safesignal-*" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
