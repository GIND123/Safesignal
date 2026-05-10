> **SafeSignal** is a submission for the **Agents Assemble** hackathon (Prompt Opinion / Devpost, deadline May 11 2026, $25K prize pool).
> It builds **both hackathon tracks** — an A2A Agent (The Superhero) and an MCP Server (The Superpower) — and makes them work together.

---

# SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent

**SafeSignal detects hidden clinical risks in patient charts** by cross-referencing FHIR data across medications, labs, conditions, and time — catching dangerous drug-lab mismatches, lost-to-follow-up findings, and silent deterioration patterns that no individual visit note reveals.

Built on [Prompt Opinion](https://promptopinion.ai) · Google ADK · A2A Protocol · MCP · FHIR R4 · FDA OpenFDA · NLM RxNav · RxNorm

---

## The Problem

Modern EHRs store everything: every lab, every medication, every visit. But they present data in silos. The dangerous signals live in the *connections*:

- The medication that was safe when prescribed but is now contraindicated by last month's labs
- The abnormal cancer screening from five months ago with no colonoscopy, no GI referral, no follow-up
- The kidney function declining visit over visit while each note says "stable, continue management"

Primary care physicians have 15-18 minutes per visit. There is no time to trace a lab value across six visits or cross-reference every active medication against every recent result. The data is there. The time is not.

**SafeSignal connects those dots.**

---

## What SafeSignal Finds

Using a synthetic demo patient (Margaret Chen, 71F with T2DM, HTN, AFib, CKD Stage 4), SafeSignal detects **9 findings hiding in a chart a PCP would call "routine follow-up":**

| # | Finding | Severity | Type |
|---|---|---|---|
| 1 | Metformin with eGFR 27 — below discontinuation threshold (FDA label: eGFR <30 contraindicated) | URGENT | Medication-Lab Mismatch |
| 2 | Lisinopril + potassium 5.3 + eGFR 27 — hyperkalemia risk with 38% renal decline | URGENT | Medication-Lab Mismatch |
| 3 | Ibuprofen + Warfarin — bleeding interaction (FDA drug interactions label cited, severity: documented) | URGENT | Drug-Drug Interaction |
| 4 | Ibuprofen with eGFR 27 — nephrotoxic NSAID in Stage 4 CKD, compound with Lisinopril | URGENT | Medication-Lab Mismatch |
| 5 | Positive FOBT 157 days ago — no colonoscopy, no GI referral in ServiceRequests, Encounters, or Procedures | WARNING | Lost Follow-Up |
| 6 | eGFR declining 52→27 over 14 months — no nephrology referral documented | WARNING | Silent Deterioration |
| 7 | A1c rising 7.1→8.2 over 18 months despite Metformin | WARNING | Silent Deterioration |
| 8 | Blood pressure rising 138/82→155/94 over 14 months despite Lisinopril | WARNING | Silent Deterioration |
| 9 | Warfarin INR last measured 65 days ago (FDA boxed warning: regular monitoring required) | INFO | Monitoring Gap |

**Validation: 12/12 automated checks pass. Three synthetic cases now load and test cleanly, including an extreme polypharmacy case and a sparse-chart edge case.**

---

## Architecture

```
Prompt Opinion Platform
        |
        |  A2A Request (SHARP context: patientId, fhirUrl, fhirToken)
        v
+----------------------------+
|  SafeSignal A2A Agent      |  <-- The Superhero (port 8004)
|  safesignal/               |
|  - 4 clinical ADK tools    |
|  - SHARP context extraction|
+----------------------------+
        |
        |  orchestrates
        v
+----------------------------+      +---------------------------+
|  SafeSignal MCP Server     |      |  FDA OpenFDA API          |
|  safesignal_mcp/           |      |  api.fda.gov/drug/label   |
|  - check_medication_safety |      |  Boxed warnings,          |
|  - detect_deterioration    |      |  contraindications,       |
|  - find_lost_followups     |      |  drug interactions text   |
|  - generate_risk_briefing  |      +---------------------------+
+----------------------------+      +---------------------------+
        |                           |  NLM RxNav (ONCHigh)     |
        |  FHIR R4 queries          |  rxnav.nlm.nih.gov        |
        v                           |  Per-drug interaction DB  |
+----------------------------+      +---------------------------+
|  FHIR R4 Server            |      +---------------------------+
|  9 resource types          |      |  RxNorm / RxNav (NLM)    |
|  Patient, Condition,       |      |  Drug ingredient ->       |
|  MedicationRequest,        |      |  RxCUI identifier         |
|  Observation, Encounter,   |      +---------------------------+
|  Procedure, DiagReport,    |
|  ServiceRequest,           |
|  AllergyIntolerance        |
+----------------------------+
```

### Knowledge Enrichment Layer

Between FHIR data retrieval and LLM reasoning, SafeSignal enriches each medication with data from three authoritative external sources:

1. **RxNorm/RxCUI** (`rxnav.nlm.nih.gov/REST/rxcui.json`) — normalises each medication ingredient to a standard NLM identifier, enabling database lookups.

2. **FDA OpenFDA Drug Labels** (`api.fda.gov/drug/label.json`) — fetches boxed warnings, contraindications, warnings & precautions, and drug interactions text from the official FDA-approved regulatory label.

3. **NLM RxNav Drug Interactions — ONCHigh** (`rxnav.nlm.nih.gov/REST/interaction/interaction.json?rxcui=...&sources=ONCHigh`) — per-drug interaction lookup from the National Library of Medicine's high-quality clinical subset. Filtered to co-prescribed pairs only. Where NLM finds no ONCHigh entry, the FDA drug label drug_interactions section is scanned as a fallback.

Each `drug_interactions` entry carries an accurate `source` field — `"NLM RxNav (ONCHigh)"` or `"FDA Drug Label (OpenFDA) - drug interactions section"` — so the LLM cites the correct regulatory authority.

This means the LLM can cite: *"Per FDA Drug Label (OpenFDA) - drug interactions section: ...take a blood thinning (anticoagulant)... (severity: documented)"* — not just its training knowledge.

---

## Modules

| Module | Description | Port |
|---|---|---|
| `safesignal/` | A2A Agent — The Superhero | 8004 |
| `safesignal_mcp/` | MCP Server — The Superpower | 8005 |
| `shared/` | Shared ADK infrastructure (middleware, FHIR hook, app factory) | — |

### Key Files

| File | Purpose |
|---|---|
| `safesignal/agent.py` | ADK root agent with SafeSignal identity and 4 clinical tools |
| `safesignal/app.py` | A2A app with FHIR scopes and 4 AgentSkills |
| `safesignal/tools/fhir_client.py` | FHIRClient — 9 FHIR resource types including ServiceRequest |
| `safesignal/tools/knowledge_enrichment.py` | FDA OpenFDA + NLM ONCHigh + RxNorm enrichment layer |
| `safesignal/tools/risk_briefing.py` | Tool 4: orchestrates full risk briefing |
| `safesignal/tools/medication_safety.py` | Tool 1: medication-lab mismatch analysis |
| `safesignal/tools/deterioration.py` | Tool 2: longitudinal deterioration detection |
| `safesignal/tools/lost_followups.py` | Tool 3: follow-up gap detection |
| `safesignal/prompts/clinical_prompts.py` | System prompts with FDA/NLM evidence citation instructions |
| `safesignal_mcp/server.py` | FastMCP server with 4 self-contained clinical tools |
| `safesignal_mcp/app.py` | ASGI entry point for MCP SSE server |
| `safesignal/synthetic_data/catalog.py` | Synthetic case catalog and expected test signals |
| `safesignal/synthetic_data/margaret_chen.json` | Baseline portable FHIR collection bundle |
| `safesignal/synthetic_data/samuel_brooks_extreme.json` | Extreme polypharmacy / lab-derangement collection bundle |
| `safesignal/synthetic_data/natalie_cho_sparse.json` | Sparse-chart / completed-follow-up collection bundle |
| `scripts/load_synthetic_patient.py` | Load any packaged synthetic case to HAPI FHIR sandbox |
| `scripts/load_margaret_chen.py` | Backward-compatible wrapper for the original demo case |
| `scripts/test_safesignal_full.py` | Full end-to-end test — 12/12 validation checks |
| `tests/test_enrichment_unit.py` | Unit tests for enrichment logic (pytest -q) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Google AI Studio API key (for Gemini 2.5 Flash — default model)
- FDA OpenFDA API key (free at [open.fda.gov](https://open.fda.gov/apis/authentication/))

### 1 — Clone and install

```bash
git clone https://github.com/your-org/safesignal.git
cd safesignal
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows:    .venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Configure environment

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY and FDA_API_KEY
```

### 3 — Load a synthetic patient to the FHIR sandbox

```bash
python scripts/load_synthetic_patient.py --case margaret_chen
```

Available cases:

- `margaret_chen` — baseline CKD, diabetes, anticoagulation, and missed FOBT follow-up
- `samuel_brooks_extreme` — severe CKD decline, hyperkalemia, supratherapeutic INR, polypharmacy, documented GI/nephrology follow-up
- `natalie_cho_sparse` — sparse chart with no active meds and timely mammogram-to-biopsy follow-up

List them from the CLI with:

```bash
python scripts/load_synthetic_patient.py --list-cases
```

### 4 — Run the full end-to-end test

```bash
python scripts/test_safesignal_full.py
```

Example alternate cases:

```bash
python scripts/test_safesignal_full.py --case samuel_brooks_extreme --load
python scripts/test_safesignal_full.py --case natalie_cho_sparse --load
```

Output: complete MCP/LLM test path plus 12/12 validation checks for the selected case.

Run unit tests only (no API calls):

```bash
pytest -q
```

### 5 — Start the servers

```bash
pip install honcho          # if not installed
honcho start
```

This starts both the A2A agent (port 8004) and MCP server (port 8005).

Or individually:
```bash
# Terminal 1 — A2A Agent
uvicorn safesignal.app:a2a_app --host 0.0.0.0 --port 8004

# Terminal 2 — MCP Server
uvicorn safesignal_mcp.app:sse_app --host 0.0.0.0 --port 8005
```

### 6 — Verify the agent card

```bash
curl http://localhost:8004/.well-known/agent-card.json
```

---

## Deploying to Google Cloud Run

Each module deploys as its own Cloud Run service from the same Dockerfile.

### One-time setup

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

# Store secrets
echo -n "your-google-api-key" | gcloud secrets create google-api-key --data-file=-
echo -n "your-fda-api-key"    | gcloud secrets create fda-api-key    --data-file=-
echo -n "your-x-api-key"      | gcloud secrets create safesignal-api-key --data-file=-
```

### Deploy the A2A Agent

```bash
gcloud run deploy safesignal-agent \
  --source . \
  --region us-central1 \
  --set-env-vars "AGENT_MODULE=safesignal.app:a2a_app" \
  --set-secrets "GOOGLE_API_KEY=google-api-key:latest,FDA_API_KEY=fda-api-key:latest,API_KEYS=safesignal-api-key:latest" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3
```

### Deploy the MCP Server

```bash
gcloud run deploy safesignal-mcp \
  --source . \
  --region us-central1 \
  --set-env-vars "AGENT_MODULE=safesignal_mcp.app:sse_app,PORT=8080" \
  --set-secrets "GOOGLE_API_KEY=google-api-key:latest,FDA_API_KEY=fda-api-key:latest" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3
```

### Set public URLs on deployed services

```bash
AGENT_URL=https://safesignal-agent-abc123-uc.a.run.app
MCP_URL=https://safesignal-mcp-abc123-uc.a.run.app

gcloud run services update safesignal-agent \
  --region us-central1 \
  --update-env-vars "SAFESIGNAL_URL=${AGENT_URL}"

gcloud run services update safesignal-mcp \
  --region us-central1 \
  --update-env-vars "SAFESIGNAL_MCP_URL=${MCP_URL}"
```

---

## Connecting to Prompt Opinion

1. **Deploy both services** to publicly reachable HTTPS URLs (Cloud Run or ngrok)

2. **Register the A2A agent** in your Prompt Opinion workspace:
   - Agent card URL: `https://your-agent-url/.well-known/agent-card.json`
   - API key: the value you stored in `API_KEYS`

3. **Set your workspace URL** in the agent card:
   ```bash
   PO_PLATFORM_BASE_URL=https://your-workspace.promptopinion.ai
   ```

4. **Invoke SafeSignal** from any patient context in Prompt Opinion:
   > "What should I know before seeing this patient today?"

   SafeSignal automatically reads FHIR credentials from the SHARP context Prompt Opinion injects.

5. **Connect the MCP tools** to other agents via MCPToolset:
   ```python
   from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

   safesignal_tools = MCPToolset(
       connection_params=SseServerParams(url="https://your-mcp-url/sse")
   )
   ```

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Google AI Studio key (required for Gemini) |
| `FDA_API_KEY` | — | FDA OpenFDA API key (free tier works; key raises rate limits) |
| `API_KEYS` | — | Comma-separated valid `X-API-Key` values for the A2A agent |
| `SAFESIGNAL_MODEL` | `gemini/gemini-2.5-flash` | LLM for the A2A agent (LiteLLM format) |
| `SAFESIGNAL_MCP_MODEL` | `gemini/gemini-2.5-flash` | LLM for MCP server tools |
| `SAFESIGNAL_URL` | `http://localhost:8004` | Public A2A agent URL (placed in agent card) |
| `PO_PLATFORM_BASE_URL` | `http://localhost:5139` | Prompt Opinion workspace URL (for FHIR extension URI) |
| `MCP_PORT` | `8005` | MCP server port (local) |

Use `anthropic/claude-sonnet-4-6` or `openai/gpt-4.1` for best clinical reasoning quality.

---

## External APIs

| API | Purpose | Auth |
|---|---|---|
| FDA OpenFDA Drug Labels (`api.fda.gov/drug/label.json`) | Boxed warnings, contraindications, warnings & precautions, drug interactions text | Free API key |
| NLM RxNav Drug Interactions (`rxnav.nlm.nih.gov/REST/interaction/`) | ONCHigh curated drug-drug interaction database, per-drug lookup | None |
| RxNorm/RxNav (`rxnav.nlm.nih.gov/REST/rxcui.json`) | Drug ingredient normalisation to RxCUI identifiers | None |
| HAPI FHIR Sandbox (`hapi.fhir.org/baseR4`) | Patient data for demo/testing | None |

---

## MCP Tools (The Superpower)

Any agent on the Prompt Opinion platform can call these tools independently:

| Tool | Description |
|---|---|
| `check_medication_safety` | Cross-reference active meds against labs, conditions, allergies. Returns FDA-label-cited findings and NLM/FDA interaction evidence with accurate source attribution. |
| `detect_silent_deterioration` | Longitudinal trend analysis across 24 months of Observations. Identifies progressive decline individual notes miss. |
| `find_lost_followups` | Finds abnormal diagnostic results with no documented follow-up (checking Encounters, Procedures, and ServiceRequests) within clinical timeframes. |
| `generate_risk_briefing` | Orchestrates all three analyses into a complete severity-ordered pre-visit risk briefing. |

All tools accept `(patient_id, fhir_url, fhir_token)` and return structured natural-language analysis with FHIR evidence citations and FDA/NLM label citations.

---

## A2A Agent Skills (The Superhero)

| Skill | Trigger |
|---|---|
| Pre-Visit Risk Briefing | "What should I know before seeing this patient today?" |
| Medication Safety Analysis | "Check this patient's medications against their labs" |
| Silent Deterioration Detection | "Are any of this patient's trends concerning?" |
| Lost Follow-Up Detection | "What abnormal results never got followed up on?" |

---

## Compliance Guardrails

SafeSignal is designed to support — not replace — clinical judgment:

- Does **not** diagnose
- Does **not** prescribe or recommend treatment changes
- Does **not** submit orders or modify the medical record
- Every finding uses language like *"warrants clinician review"* and *"consider evaluating"*
- Every briefing cites specific FHIR resources (resource IDs, dates, values)
- Every briefing ends with a compliance disclaimer
- Agent is stateless — no patient data stored after the request
- Follow-up gap findings qualify claims against what FHIR records were available (Encounters, Procedures, ServiceRequests)

---

## Demo Cases

- `margaret_chen` (`patient-mc-071`) — baseline happy path with nine hidden risks and missed FOBT follow-up
- `samuel_brooks_extreme` (`patient-sb-067`) — extreme polypharmacy, hyperkalemia, INR 4.8, rapid CKD decline, documented colonoscopy and nephrology follow-up
- `natalie_cho_sparse` (`patient-nc-046`) — sparse chart, no active meds, BI-RADS 5 mammogram with timely biopsy and post-biopsy follow-up

Load to HAPI FHIR sandbox: `python scripts/load_synthetic_patient.py --case <case-name>`
Run full briefing/test path: `python scripts/test_safesignal_full.py --case <case-name> --load`

---

## Built With

- [Prompt Opinion](https://promptopinion.ai) — agent platform, SHARP context
- [Google ADK](https://google.github.io/adk-docs/) — agent framework
- [A2A Protocol](https://google.github.io/A2A/) — agent-to-agent communication
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) — reusable tool exposure
- [FHIR R4](https://hl7.org/fhir/R4/) — patient data standard
- [FDA OpenFDA Drug Labels API](https://open.fda.gov/apis/) — regulatory drug label data
- [NLM RxNav Drug Interactions (ONCHigh)](https://rxnav.nlm.nih.gov/) — curated clinical interaction database
- [RxNorm/RxNav](https://rxnav.nlm.nih.gov/) — NLM drug identifier standard
- [LiteLLM](https://github.com/BerriAI/litellm) — multi-model LLM routing
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server framework
- Python 3.11 · FastAPI · Uvicorn · httpx

---

## License

MIT

---

*SafeSignal — Agents Assemble Hackathon submission. The risks are in the chart. We help you find them.*

