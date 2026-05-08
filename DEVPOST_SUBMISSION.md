# SafeSignal — Devpost Submission Text

Copy-paste each section into Devpost. Fill in [BRACKETED] placeholders after deployment.

---

## Project Title

SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent

---

## Short Description (tagline)

SafeSignal detects hidden clinical risks in patient charts by cross-referencing FHIR data across medications, labs, conditions, and time — catching dangerous drug-lab mismatches, lost-to-follow-up findings, and silent deterioration patterns that individual visit notes miss.

---

## Full Description

SafeSignal is a dual MCP + A2A healthcare system built on Prompt Opinion that finds the clinical risks hiding between EHR data silos.

### The Problem

Modern EHRs store comprehensive patient data — medications, labs, conditions, encounters — but present it in separate screens and tabs. The dangerous signals live in the connections: the medication that was safe when prescribed but is now contraindicated by recent labs. The abnormal test from five months ago that no one followed up on. The kidney function that's been declining visit over visit while each note says "stable."

Primary care physicians have 15-18 minutes per patient visit. There is no time to trace a lab value backward across six visits or cross-reference every active medication against every recent lab. The data is there. The time is not.

### The Solution

SafeSignal addresses this by building **both tracks of the hackathon**:

**MCP Superpower — The Reusable Weapons:**
Four FHIR-powered clinical reasoning tools exposed as an MCP server that any agent on the Prompt Opinion platform can invoke:
- `check_medication_safety` — cross-references active medications against current lab values, conditions, and allergies
- `detect_silent_deterioration` — longitudinal trend analysis across 24 months of Observations
- `find_lost_followups` — identifies abnormal findings with no documented follow-up within clinical timeframes
- `generate_risk_briefing` — orchestrates all three into a complete pre-visit risk briefing

**A2A Agent — The Superhero:**
An intelligent agent published to the Prompt Opinion Marketplace that uses SHARP context to receive patient credentials, retrieves FHIR data, and delivers a severity-ordered risk briefing to clinicians before patient visits.

### What Makes This Require Generative AI

Rule-based CDS can flag "eGFR < 30." But it cannot reason: "eGFR has declined from 52 to 27 over 14 months. The rate of decline suggests progression toward ESRD within 1-2 years. Each individual visit note says 'CKD, monitoring.' The concurrent diabetes with worsening A1c may be accelerating renal decline. No nephrology referral is documented. The metformin prescribed 3 years ago is now contraindicated by the current lab value." This kind of multi-factor, temporal, contextual reasoning is genuine generative AI territory.

### The Knowledge Enrichment Layer (Novel Addition)

Before passing data to the LLM, SafeSignal enriches each medication with:
- **FDA OpenFDA Drug Labels** (api.fda.gov) — official boxed warnings, contraindications, and drug interactions text from FDA-approved labeling
- **RxNorm/RxCUI** (rxnav.nlm.nih.gov) — standardized NLM drug identifiers

This means the LLM cites regulatory evidence, not just training knowledge: *"Per FDA Drug Label (OpenFDA) for Metformin: Severe renal impairment (eGFR below 30 mL/min/1.73 m²)"*. This is evidence that pure rule-based CDS cannot produce and that a raw LLM call without enrichment cannot cite.

### Demo Results

Using the synthetic demo patient Margaret Chen (71F, T2DM, HTN, AFib, CKD Stage 4):

**7 findings detected from a chart a PCP would call "routine follow-up":**

🔴 URGENT — Metformin with eGFR 27 (FDA label: contraindicated below eGFR 30)
🔴 URGENT — Ibuprofen + Warfarin + CKD Stage 4 (FDA + NLM interaction evidence)
🟡 WARNING — Positive FOBT 157 days ago, no colonoscopy or GI referral
🟡 WARNING — eGFR declining 52→27 over 14 months, no nephrology referral
🟡 WARNING — A1c rising 7.1→8.2 over 18 months, no treatment change
🟡 WARNING — Lisinopril + potassium 5.3 + declining eGFR
ℹ️ INFO — Warfarin INR overdue by 7 weeks (FDA boxed warning cited)

9/9 automated validation checks pass. Briefing generated in ~29 seconds.

### Why This Architecture Wins

This is not just an entry — it is a demonstration of the platform's value proposition. The MCP tools are designed to be **reusable**: a scheduling agent can call `check_medication_safety` before confirming a refill; a care coordination agent can call `find_lost_followups` across a patient panel; a triage agent can call `generate_risk_briefing` before routing. We built infrastructure that makes the entire ecosystem smarter.

### Compliance

SafeSignal is designed to support — not replace — clinical judgment. It does not diagnose, prescribe, or make treatment recommendations. Every finding uses language like "warrants clinician review." Every briefing cites specific FHIR resources with dates, values, and IDs. Every briefing ends with a compliance disclaimer. The system is functionally equivalent to clinical decision support, which the FDA has exempted from device regulation under the 21st Century Cures Act (Section 3060) when it supports rather than replaces clinical decision-making.

---

## Built With

- Prompt Opinion Platform
- A2A Protocol (Agent-to-Agent)
- MCP (Model Context Protocol)
- FHIR R4
- SHARP Extension Specs
- Google ADK (Agent Development Kit)
- LiteLLM (multi-model routing)
- FastMCP
- FDA OpenFDA Drug Labels API
- RxNorm / RxNav (NLM)
- Gemini 2.5 Flash (default) / Claude / GPT-4.1 (configurable)
- Python 3.11 · FastAPI · Uvicorn · httpx

---

## Category

- Agent (A2A) — The Superhero
- Superpower (MCP) — The Superpower
- Both tracks

---

## Try It Out

- Prompt Opinion Marketplace: [YOUR MARKETPLACE LINK]
- MCP SSE endpoint: [YOUR MCP SERVER URL]/sse

---

## Demo Video

[YOUR VIDEO LINK — under 3 minutes]

---

## GitHub

[YOUR GITHUB REPO URL]

---

## Team

[YOUR NAME(S)]

---

# Deployment Checklist (complete before submitting)

Before submitting to Devpost, complete these steps:

### Step 1: Deploy to Cloud Run (or use ngrok for demo)

Option A — Cloud Run (recommended for permanent link):
```bash
# One-time
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com

# Store secrets
echo -n "YOUR_GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=-
echo -n "YOUR_FDA_API_KEY"    | gcloud secrets create fda-api-key    --data-file=-
echo -n "safesignal-demo-key" | gcloud secrets create safesignal-api-key --data-file=-

# Deploy A2A agent
gcloud run deploy safesignal-agent \
  --source . \
  --region us-central1 \
  --set-env-vars "AGENT_MODULE=safesignal.app:a2a_app" \
  --set-secrets "GOOGLE_API_KEY=google-api-key:latest,FDA_API_KEY=fda-api-key:latest,API_KEYS=safesignal-api-key:latest" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3

# Deploy MCP server
gcloud run deploy safesignal-mcp \
  --source . \
  --region us-central1 \
  --set-env-vars "AGENT_MODULE=safesignal_mcp.app:sse_app" \
  --set-secrets "GOOGLE_API_KEY=google-api-key:latest,FDA_API_KEY=fda-api-key:latest" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3

# Update with public URLs after deploy
AGENT_URL=https://safesignal-agent-HASH-uc.a.run.app
MCP_URL=https://safesignal-mcp-HASH-uc.a.run.app

gcloud run services update safesignal-agent --region us-central1 \
  --update-env-vars "SAFESIGNAL_URL=${AGENT_URL}"
gcloud run services update safesignal-mcp --region us-central1 \
  --update-env-vars "SAFESIGNAL_MCP_URL=${MCP_URL}"
```

Option B — ngrok (for demo recording only):
```bash
# Terminal 1
honcho start

# Terminal 2 - expose both ports
ngrok start --all  # configure ngrok.yml with both 8004 and 8005
```

### Step 2: Register in Prompt Opinion

1. Go to your Prompt Opinion workspace
2. Add agent: paste the agent card URL
   `https://safesignal-agent-HASH-uc.a.run.app/.well-known/agent-card.json`
3. Set API key: `safesignal-demo-key` (or whatever you used in API_KEYS)
4. Test: open a patient context, type "What should I know before seeing this patient today?"
5. Take a screenshot of the response

### Step 3: Record Demo Video (target: 2:30-2:50)

Follow the script in SafeSignal_Blueprint.md Section 16:
1. 0:00-0:15 — The Hook (narrate while showing the chart)
2. 0:15-0:40 — What SafeSignal Is (show agent card + MCP tools in Prompt Opinion)
3. 0:40-0:50 — Invoke: type "What should I know before seeing this patient today?"
4. 0:50-1:50 — Show the 7 findings appearing, narrate the 3 URGENT/WARNING ones
5. 1:50-2:20 — Call check_medication_safety directly as MCP tool (reusability story)
6. 2:20-2:50 — Impact statement
7. 2:50-3:00 — Close

Tools for recording: OBS Studio (free), Loom, or QuickTime

### Step 4: Update DEVPOST_SUBMISSION.md

Fill in:
- [YOUR MARKETPLACE LINK]
- [YOUR MCP SERVER URL]
- [YOUR VIDEO LINK]
- [YOUR GITHUB REPO URL]
- [YOUR NAME(S)]

### Step 5: Submit

Deadline: May 11 2026, 11:00 PM EDT

Go to the Devpost hackathon page and submit with:
- Project title and description (from this file)
- Demo video link
- GitHub link
- Built With tags
- Screenshots from Prompt Opinion

---

# Demo Script (condensed for recording)

## Words to say on camera / in voiceover:

**[0:00]** "Every piece of data in Margaret's chart was visible to her doctors. The declining kidney function. The medication that should have been stopped. The cancer screening with no follow-up. Each one was in the EHR. No one connected the dots. SafeSignal connects them."

**[0:15]** "SafeSignal is two things. An MCP server — reusable clinical reasoning tools any agent on Prompt Opinion can call. And an A2A agent that orchestrates those tools into a pre-visit risk briefing. We built both hackathon tracks and made them work together."

**[0:40]** [Type in Prompt Opinion]: "What should I know before seeing this patient today?"

**[0:50]** [As briefing appears]: "SafeSignal found seven things hiding in this chart."

"First: Margaret has been on metformin for three years. But her kidney function has dropped to 27 — below the threshold where the FDA says to stop it. Per the FDA drug label: 'Severe renal impairment — eGFR below 30 — contraindicated.' Nobody changed the medication because nobody looked at the trend."

"Second: An urgent care visit added ibuprofen for knee pain. That provider didn't know her eGFR was 27. An NSAID in stage 4 CKD, on warfarin — that's compound risk from two prescribers who didn't see each other's context. NLM Drug Interaction Database confirms the Ibuprofen-Warfarin interaction."

"Third: A positive fecal occult blood test from five months ago. No colonoscopy. No GI referral. One hundred fifty-seven days and counting."

**[1:50]** [Show direct MCP tool call]: "The clinical reasoning lives in an MCP server. Any agent on this platform can call these tools. A scheduling agent. A care coordination agent. A triage agent. We didn't just solve one problem — we built infrastructure that makes the whole ecosystem smarter."

**[2:20]** "Margaret Chen is synthetic. But her story is not. These patterns hide in FHIR data that already exists. They just need someone to look across the silos."

**[2:50]** "SafeSignal. The risks are in the chart. We help you find them."
