> **SafeSignal** is a submission for the **Agents Assemble** hackathon (Prompt Opinion / Devpost, deadline May 11 2026, $25K prize pool).
> It builds **both hackathon tracks** — an A2A Agent (The Superhero) and an MCP Server (The Superpower) — and makes them work together.

---


<img width="1036" height="1228" alt="Architecture Diagram" src="https://github.com/user-attachments/assets/34c5397a-ff22-40b6-b3c4-dd9b8b92d6cc" />


# SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent

**SafeSignal detects hidden clinical risks in patient charts** by cross-referencing FHIR data across medications, labs, conditions, and time — catching dangerous drug-lab mismatches, lost-to-follow-up findings, and silent deterioration patterns that no individual visit note reveals.

Built on [Prompt Opinion](https://promptopinion.ai) · Google ADK · A2A Protocol · MCP · FHIR R4 · FDA OpenFDA · NLM RxNav · RxNorm

---

## The Problem

Modern EHRs store everything: every lab, every medication, every visit. But they present data in silos. The dangerous signals live in the *connections*:

- The medication that was safe when prescribed but is now contraindicated by last month's labs
- The kidney function declining visit over visit while every note says "CKD appears stable"
- The urgent care NSAID prescription written without knowing the patient's eGFR was 18

Primary care physicians have 15–18 minutes per visit. There is no time to trace a lab value across ten visits or cross-reference every active medication against every recent result. The data is there. The time is not.

**SafeSignal connects those dots.**

---

## What SafeSignal Finds

Using a synthetic demo patient (Samuel Brooks, 67M — CHF, T2DM, AFib, CKD Stage 4), SafeSignal detects **11 findings hiding in a chart whose most recent note said "stable, continue management":**

| # | Finding | Severity | Type |
|---|---|---|---|
| 1 | Metformin with eGFR 18 — FDA label: contraindicated below eGFR 30 (lactic acidosis risk) | 🔴 URGENT | Medication-Lab Mismatch |
| 2 | Spironolactone with potassium 6.2 — FDA label: contraindicated in hyperkalemia | 🔴 URGENT | Medication-Lab Mismatch |
| 3 | Ibuprofen + Warfarin — FDA drug interactions label cited, INR 4.8, bleeding risk | 🔴 URGENT | Drug-Drug Interaction |
| 4 | Ibuprofen with eGFR 18 — nephrotoxic NSAID in Stage 4 CKD, added by urgent care 13 days prior | 🔴 URGENT | Medication-Lab Mismatch |
| 5 | Lisinopril with potassium 6.2 and eGFR 18 — ACE-I exacerbating hyperkalemia and renal decline | 🔴 URGENT | Medication-Lab Mismatch |
| 6 | Warfarin INR 4.8 — FDA black box warning: major or fatal bleeding risk, urgent review | 🔴 URGENT | Monitoring Gap |
| 7 | eGFR declined 38 → 18 over 10 months (−53%) — encounter note on same day said "CKD stable" | 🟡 WARNING | Silent Deterioration + Note Contradiction |
| 8 | Potassium rising 4.9 → 6.2 over 10 months — progressive hyperkalemia | 🟡 WARNING | Silent Deterioration |
| 9 | HbA1c rising 8.4% → 9.1% — worsening glycemic control, no treatment change documented | 🟡 WARNING | Silent Deterioration |
| 10 | INR elevated at 3.4 in February — no documented dose adjustment before April visit | 🟡 WARNING | Follow-Up Gap |
| 11 | Blood pressure rising 144 → 166 systolic despite two antihypertensives | ℹ️ INFO | Silent Deterioration |

**Positive FOBT from January → colonoscopy completed February 3. Correctly identified as resolved — not a gap.**

**Validation: 12/12 automated checks pass. Three synthetic cases test cleanly.**

---

## Why This Requires Generative AI

Finding 7 — *"The encounter note from 2026-04-28 states 'CKD appear stable on current regimen.' This directly contradicts an eGFR decline of 38 → 18 over 10 months"* — is something no rule-based CDS system can produce. A rule can flag `eGFR < 30`. It cannot read a free-text clinical note, compare it to a ten-month trend, and write: *"the assessment contradicts the data."*

Finding 3 — quoting *"Per FDA Drug Label (OpenFDA) - drug interactions section: '...take a blood thinning (anticoagulant)... are age 60 or older' (severity: documented)"* — is not LLM training knowledge. It is the live regulatory label retrieved from the FDA OpenFDA API, cited against a specific patient's active medications and current INR.

That combination — multi-factor temporal reasoning plus real-time regulatory evidence citation — is the last mile.

---

## Architecture

```
Prompt Opinion Platform
        |
        |  A2A Request (SHARP context: patientId, fhirUrl, fhirToken)
        v
+----------------------------+
|  SafeSignal A2A Agent      |  ← The Superhero (port 8004)
|  safesignal/               |
|  - 4 clinical ADK tools    |
|  - SHARP context extraction|
+----------------------------+
        |
        |  tool calls
        v
+----------------------------+      +---------------------------+
|  SafeSignal MCP Server     |      |  FDA OpenFDA API          |
|  safesignal_mcp/           |      |  Boxed warnings,          |
|  - check_medication_safety |      |  contraindications,       |
|  - detect_deterioration    |      |  drug interactions text   |
|  - find_lost_followups     |      +---------------------------+
|  - generate_risk_briefing  |      +---------------------------+
+----------------------------+      |  NLM RxNav (ONCHigh)      |
        |                           |  Per-drug interaction DB  |
        |  FHIR R4 queries          +---------------------------+
        v                           +---------------------------+
+----------------------------+      |  RxNorm / RxNav (NLM)     |
|  FHIR R4 Server            |      |  Drug name → RxCUI        |
|  9 resource types:         |      +---------------------------+
|  Patient, Condition,       |
|  MedicationRequest,        |
|  Observation, Encounter,   |
|  Procedure, DiagReport,    |
|  ServiceRequest,           |
|  AllergyIntolerance        |
+----------------------------+
```

### Knowledge Enrichment Layer

Between FHIR data retrieval and LLM reasoning, SafeSignal enriches each medication with three authoritative external sources:

1. **RxNorm/RxCUI** (`rxnav.nlm.nih.gov/REST/rxcui.json`) — normalises each medication ingredient to a standard NLM identifier for database lookups.

2. **FDA OpenFDA Drug Labels** (`api.fda.gov/drug/label.json`) — fetches boxed warnings, contraindications, warnings & precautions, and drug interactions text from the official FDA-approved regulatory label.

3. **NLM RxNav Drug Interactions — ONCHigh** (`rxnav.nlm.nih.gov/REST/interaction/interaction.json`) — per-drug interaction lookup from the National Library of Medicine's high-quality curated clinical subset. Filtered to co-prescribed pairs. Where NLM finds no ONCHigh entry, the FDA label drug_interactions section is scanned as a fallback.

Each `drug_interactions` entry carries an accurate `source` field — `"NLM RxNav (ONCHigh)"` or `"FDA Drug Label (OpenFDA) - drug interactions section"` — so the LLM cites the correct regulatory authority, not just its training knowledge.

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
| `safesignal/tools/risk_briefing.py` | Tool: orchestrates full pre-visit risk briefing |
| `safesignal/tools/medication_safety.py` | Tool: medication-lab mismatch + compound risk analysis |
| `safesignal/tools/deterioration.py` | Tool: longitudinal deterioration detection |
| `safesignal/tools/lost_followups.py` | Tool: follow-up gap detection (checks Encounters, Procedures, ServiceRequests) |
| `safesignal/prompts/clinical_prompts.py` | System prompts with FDA/NLM evidence citation format |
| `safesignal_mcp/server.py` | FastMCP server — 4 self-contained clinical tools callable by any agent |
| `safesignal/synthetic_data/catalog.py` | Synthetic case catalog (3 cases) |
| `scripts/load_synthetic_patient.py` | Load any synthetic case to HAPI FHIR sandbox |
| `scripts/test_safesignal_full.py` | Full end-to-end test — 12/12 validation checks |
| `VIDEO_SCRIPT.md` | Demo video recording script with exact questions and narration |

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
# Edit .env: set GOOGLE_API_KEY and FDA_API_KEY at minimum
```

### 3 — Load a synthetic patient to the FHIR sandbox

```bash
# Primary demo patient (Samuel Brooks — extreme polypharmacy case)
python scripts/load_synthetic_patient.py --case samuel_brooks_extreme

# Baseline case (Margaret Chen — CKD, diabetes, missed FOBT)
python scripts/load_synthetic_patient.py --case margaret_chen

# Edge case (Natalie Cho — sparse chart, no meds, timely mammogram follow-up)
python scripts/load_synthetic_patient.py --case natalie_cho_sparse
```

List all cases:

```bash
python scripts/load_synthetic_patient.py --list-cases
```

### 4 — Run the full end-to-end test

```bash
python scripts/test_safesignal_full.py --case samuel_brooks_extreme --load
```

Output: MCP/LLM test path plus 12/12 validation checks.

```bash
pytest -q   # unit tests only (no API calls)
```

### 5 — Start the servers

```bash
pip install honcho
honcho start
```

Starts both the A2A agent (port 8004) and MCP server (port 8005).

Or individually:

```bash
# Terminal 1 — A2A Agent
uvicorn safesignal.app:a2a_app --host 0.0.0.0 --port 8004

# Terminal 2 — MCP Server
uvicorn safesignal_mcp.app:sse_app --host 0.0.0.0 --port 8005
```

### 6 — Verify

```bash
curl http://localhost:8004/.well-known/agent-card.json
```

---

## Deploying to Google Cloud Run

### One-time setup

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

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

### Set public URLs

```bash
AGENT_URL=https://safesignal-agent-abc123-uc.a.run.app
MCP_URL=https://safesignal-mcp-abc123-uc.a.run.app

gcloud run services update safesignal-agent --region us-central1 \
  --update-env-vars "SAFESIGNAL_URL=${AGENT_URL}"

gcloud run services update safesignal-mcp --region us-central1 \
  --update-env-vars "SAFESIGNAL_MCP_URL=${MCP_URL}"
```

---

## Connecting to Prompt Opinion

1. Deploy both services to publicly reachable HTTPS URLs
2. Register the A2A agent in your Prompt Opinion workspace:
   - Agent card URL: `https://your-agent-url/.well-known/agent-card.json`
   - API key: the value you stored in `API_KEYS`
3. Set your workspace URL in `.env`: `PO_PLATFORM_BASE_URL=https://your-workspace.promptopinion.ai`
4. Open any patient context in Prompt Opinion and type directly to SafeSignal:
   > "What should I know before seeing this patient today?"

   SafeSignal automatically reads FHIR credentials from the SHARP context Prompt Opinion injects.

5. Connect MCP tools to other agents:

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

safesignal_tools = MCPToolset(
    connection_params=SseServerParams(url="https://your-mcp-url/sse")
)
```

---

## Demo Video Questions

See [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) for the full recording script with narration. The five questions, in order:

| # | Question | Tool called | Key finding shown |
|---|---|---|---|
| 1 | "What should I know before seeing Samuel today?" | `generate_risk_briefing` | All 11 findings; the "stable note contradiction" |
| 2 | "Is it safe to keep him on his current medications given his latest labs?" | `check_medication_safety` | 6 URGENT findings with verbatim FDA label citations |
| 3 | "Has his kidney function been getting worse, and should I be worried?" | `detect_silent_deterioration` | eGFR 38→18 in 10 months; note contradicts data |
| 4 | "Are there any test results that were never properly followed up on?" | `find_lost_followups` | FOBT resolved correctly; INR and HbA1c gaps found |
| 5 | "Give me the exact FDA language I should cite when talking to him today" | `check_medication_safety` | Verbatim FDA Black Box Warning text for the conversation |

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Google AI Studio key (required for Gemini) |
| `FDA_API_KEY` | — | FDA OpenFDA API key (free; key raises rate limits) |
| `API_KEYS` | — | Comma-separated valid `X-API-Key` values |
| `SAFESIGNAL_MODEL` | `gemini/gemini-2.5-flash` | LLM for the A2A agent (LiteLLM format) |
| `SAFESIGNAL_MCP_MODEL` | `gemini/gemini-2.5-flash` | LLM for MCP server tools |
| `SAFESIGNAL_URL` | `http://localhost:8004` | Public A2A agent URL (placed in agent card) |
| `PO_PLATFORM_BASE_URL` | `http://localhost:5139` | Prompt Opinion workspace URL |

For best clinical reasoning quality use `anthropic/claude-sonnet-4-6` or `openai/gpt-4.1`.

---

## MCP Tools (The Superpower)

Any agent on the Prompt Opinion platform can call these tools independently:

| Tool | Description |
|---|---|
| `check_medication_safety` | Cross-references active meds against labs, conditions, allergies. Returns FDA-label-cited findings and NLM/FDA interaction evidence with accurate source attribution. |
| `detect_silent_deterioration` | Longitudinal trend analysis across 24 months of Observations with explicit trajectory data (first → last value, rate/month). |
| `find_lost_followups` | Finds abnormal findings with no documented follow-up (checks Encounters, Procedures, and ServiceRequests) within clinical timeframes. Reports resolved items correctly. |
| `generate_risk_briefing` | Orchestrates all three analyses into a complete severity-ordered pre-visit risk briefing. |

All tools accept `(patient_id, fhir_url, fhir_token)` and return structured analysis with FHIR evidence citations and FDA/NLM label citations.

---

## A2A Agent Skills (The Superhero)

| Skill | Trigger |
|---|---|
| Pre-Visit Risk Briefing | "What should I know before seeing this patient today?" |
| Medication Safety | "Is it safe to keep this patient on their current medications?" |
| Deterioration Detection | "Has this patient's kidney function been getting worse?" |
| Follow-Up Gap Detection | "Were there any test results that were never followed up on?" |

---

## External APIs

| API | Purpose | Auth |
|---|---|---|
| FDA OpenFDA Drug Labels (`api.fda.gov/drug/label.json`) | Boxed warnings, contraindications, drug interactions text | Free API key |
| NLM RxNav Drug Interactions (`rxnav.nlm.nih.gov/REST/interaction/`) | ONCHigh curated drug-drug interaction database | None |
| RxNorm/RxNav (`rxnav.nlm.nih.gov/REST/rxcui.json`) | Drug ingredient → RxCUI identifier | None |
| HAPI FHIR Sandbox (`hapi.fhir.org/baseR4`) | Patient data for demo and testing | None |

---

## Compliance Guardrails

- Does **not** diagnose
- Does **not** prescribe or recommend specific treatment changes
- Does **not** submit orders or modify the medical record
- Every finding uses language like *"warrants clinician review"*
- Every finding cites specific FHIR resource IDs, dates, and values
- Every output ends with a compliance disclaimer
- Agent is stateless — no patient data stored after the request
- Follow-up gap findings qualify claims against what FHIR records were actually available

---

## Demo Cases

| Case | Patient | Summary |
|---|---|---|
| `samuel_brooks_extreme` | Samuel Brooks, 67M | Extreme polypharmacy, eGFR 18, potassium 6.2, INR 4.8, encounter note contradicts labs — primary demo |
| `margaret_chen` | Margaret Chen, 71F | CKD, diabetes, anticoagulation, missed FOBT follow-up — baseline case |
| `natalie_cho_sparse` | Natalie Cho, 46F | Sparse chart, no active meds, BI-RADS 5 mammogram with timely biopsy — edge case |

Load to sandbox: `python scripts/load_synthetic_patient.py --case <case-name>`
Run full test: `python scripts/test_safesignal_full.py --case <case-name> --load`

---

## Built With

- [Prompt Opinion](https://promptopinion.ai) — agent platform, SHARP context, A2A routing
- [Google ADK](https://google.github.io/adk-docs/) — agent framework
- [A2A Protocol](https://google.github.io/A2A/) — agent-to-agent communication standard
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) — reusable tool exposure
- [FHIR R4](https://hl7.org/fhir/R4/) — patient data standard
- [FDA OpenFDA Drug Labels API](https://open.fda.gov/apis/) — regulatory drug label data
- [NLM RxNav Drug Interactions (ONCHigh)](https://rxnav.nlm.nih.gov/) — curated clinical interaction database
- [RxNorm/RxNav](https://rxnav.nlm.nih.gov/) — NLM drug identifier standard
- [LiteLLM](https://github.com/BerriAI/litellm) — multi-model LLM routing
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server framework
- Gemini 2.5 Flash (default) · Claude Sonnet 4.6 · GPT-4.1 (configurable)
- Python 3.11 · FastAPI · Uvicorn · httpx

---

## License

MIT

---

*SafeSignal — Agents Assemble Hackathon submission. The risks are in the chart. We help you find them.*
