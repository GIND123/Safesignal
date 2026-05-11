# SafeSignal — Devpost Submission
# Copy-paste each section into Devpost. Fill in [BRACKETED] placeholders before submitting.

---

## Project Title

SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent

---

## Short Description (tagline)

SafeSignal uncovers hidden clinical risks across EHR silos by linking medications, labs, conditions, and timelines to detect drug-lab conflicts, silent deterioration, and missed follow-ups.

---

## Full Description

### The Last Mile Problem

A 67-year-old man comes in for a routine follow-up. His physician's note from the previous visit reads: *"CHF and CKD appear stable on current regimen. Continue metformin, lisinopril, spironolactone, and warfarin. Recheck labs next month."*

His labs from that same day:

- eGFR: **18** mL/min/1.73m² (was 38 ten months ago — a 53% decline)
- Potassium: **6.2** mmol/L (critically high)
- INR: **4.8** (significantly supratherapeutic)
- HbA1c: **9.1%** (rising despite treatment)

Thirteen days before this visit, urgent care added ibuprofen for knee pain. That provider had no idea his eGFR was 18 or that he was on warfarin with a rising INR. No one connected those dots.

This is not a rare edge case. This is what the EHR looks like when data lives in silos.

### The Solution

SafeSignal is a **dual MCP + A2A healthcare system** built on Prompt Opinion that finds the clinical risks hiding between EHR data silos.

**MCP Superpower — The Reusable Weapons:**
Four FHIR-powered clinical reasoning tools exposed as an MCP server that any agent on Prompt Opinion can invoke:

- `check_medication_safety` — cross-references active medications against current lab values, conditions, and allergies; cites verbatim FDA drug label text alongside FHIR evidence
- `detect_silent_deterioration` — longitudinal trend analysis across 24 months of Observations with explicit trajectory data; detects discrepancies between clinical note language and objective data
- `find_lost_followups` — identifies abnormal findings with no documented follow-up in Encounters, Procedures, or ServiceRequests within clinical timeframes; correctly identifies resolved items
- `generate_risk_briefing` — orchestrates all three into a complete pre-visit risk briefing

**A2A Agent — The Superhero:**
An intelligent agent published to the Prompt Opinion Marketplace that uses SHARP context to receive patient credentials, retrieves FHIR data, and delivers a severity-ordered risk briefing to clinicians before patient visits.

### What Makes This Require Generative AI

Finding #7 in Samuel's briefing: *"The encounter note from 2026-04-28 states 'CKD appear stable on current regimen.' This directly contradicts an eGFR decline of 38 → 18 over 10 months."*

A rule-based CDS system can flag `eGFR < 30`. It cannot read a free-text clinical note, compare it to a ten-month trend, and write: *"the assessment contradicts the data."*

Finding #3: *"Per FDA Drug Label (OpenFDA) - drug interactions section: '...take a blood thinning (anticoagulant)... are age 60 or older' (severity: documented)"* — this is not LLM training knowledge. It is the live regulatory label retrieved from the FDA OpenFDA API, cited against a specific patient's active medications and current INR of 4.8.

Multi-factor temporal reasoning combined with real-time regulatory evidence citation is genuine generative AI territory.

### The Knowledge Enrichment Layer (Novel Addition)

Before passing data to the LLM, SafeSignal enriches each medication with evidence from three authoritative public sources:

- **RxNorm/RxCUI** (rxnav.nlm.nih.gov) — standardised NLM drug identifiers for each medication ingredient, enabling database lookups
- **FDA OpenFDA Drug Labels** (api.fda.gov) — official boxed warnings, contraindications, and drug interactions text from FDA-approved regulatory labelling
- **NLM RxNav Drug Interactions — ONCHigh** (rxnav.nlm.nih.gov/REST/interaction/) — per-drug interaction lookup from the National Library of Medicine's high-quality curated clinical subset, filtered to co-prescribed pairs. Where NLM finds no ONCHigh entry, FDA label drug_interactions text is scanned as a fallback.

Each interaction entry carries an accurate `source` field — `"NLM RxNav (ONCHigh)"` or `"FDA Drug Label (OpenFDA) - drug interactions section"` — so the LLM cites the correct regulatory authority.

### Demo Results — Samuel Brooks, 67M (CHF, T2DM, AFib, CKD Stage 4)

**11 findings detected from a chart whose most recent note said "stable, continue management":**

🔴 URGENT — Metformin contraindicated — eGFR 18 (FDA: eGFR < 30 contraindicated; lactic acidosis Black Box Warning)
🔴 URGENT — Spironolactone contraindicated — potassium 6.2 (FDA: contraindicated in hyperkalemia)
🔴 URGENT — Ibuprofen + Warfarin — bleeding risk (FDA drug interactions label cited; INR 4.8, patient age 67)
🔴 URGENT — Ibuprofen with eGFR 18 — nephrotoxic NSAID added by urgent care 13 days prior; prescriber had no FHIR context
🔴 URGENT — Lisinopril (ACE-I) exacerbating hyperkalemia — potassium 6.2, eGFR 18, combined with Spironolactone
🔴 URGENT — Warfarin INR 4.8 — FDA Black Box Warning: major or fatal bleeding risk; immediate review
🟡 WARNING — eGFR 38 → 18 over 10 months (−53%) — encounter note on same day said "CKD stable" — contradiction flagged
🟡 WARNING — Potassium 4.9 → 6.2 over 10 months — progressive hyperkalemia trend
🟡 WARNING — HbA1c 8.4% → 9.1% — worsening glycemic control; encounter note: "continue metformin"
🟡 WARNING — INR 3.4 in February — no documented dose review before April visit
ℹ️ INFO — Systolic BP 144 → 166 over 10 months despite two antihypertensives

✓ RESOLVED — Positive FOBT January 2026 → colonoscopy with polypectomy February 3, 2026 (correctly identified as addressed, not flagged as a gap)

**12/12 automated validation checks pass. Three synthetic cases run cleanly (baseline, extreme polypharmacy, sparse-chart edge case).**

### Why This Architecture Wins

The MCP tools are designed to be **reusable**: a scheduling agent can call `check_medication_safety` before confirming a refill; a care coordination agent can call `find_lost_followups` across a patient panel; a triage agent can call `generate_risk_briefing` before routing. SafeSignal built infrastructure that makes the entire ecosystem smarter, not just one demo.

### Compliance

SafeSignal is designed to support — not replace — clinical judgement. It does not diagnose, prescribe, or make treatment recommendations. Every finding uses language like "warrants clinician review." Every briefing cites specific FHIR resources with dates, values, and IDs. Every output ends with a compliance disclaimer. Follow-up gap findings qualify claims against what FHIR records were actually available (Encounters, Procedures, ServiceRequests) rather than asserting categorically that no action was taken. The system is functionally equivalent to clinical decision support, which the FDA has exempted from device regulation under the 21st Century Cures Act (Section 3060).

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
- FDA OpenFDA Drug Labels API (api.fda.gov)
- NLM RxNav Drug Interactions — ONCHigh (rxnav.nlm.nih.gov)
- RxNorm / RxNav (NLM)
- Gemini 2.5 Flash (default) / Claude Sonnet 4.6 / GPT-4.1 (configurable)
- Python 3.11 · FastAPI · Uvicorn · httpx

---

## Category

- Agent (A2A) — The Superhero ✓
- Superpower (MCP) — The Superpower ✓
- Both tracks ✓

---

## Try It Out

- Prompt Opinion Marketplace: [YOUR MARKETPLACE LINK]
- MCP SSE endpoint: [YOUR MCP SERVER URL]/sse
- GitHub: [YOUR GITHUB REPO URL]

---

## Demo Video

[YOUR VIDEO LINK — under 3 minutes]

---

## Team

[YOUR NAME(S)]

---

---

# Submission Checklist

Complete ALL items before submitting to Devpost by May 11 2026, 11:00 PM EDT.

### Step 1: Deploy

Option A — Cloud Run (permanent URL, recommended):
```bash
# Full deploy instructions in README.md → Deploying to Google Cloud Run
gcloud run deploy safesignal-agent ...
gcloud run deploy safesignal-mcp ...
```

Option B — ngrok (demo recording only):
```bash
honcho start    # Terminal 1
ngrok start --all    # Terminal 2 (configure ngrok.yml with ports 8004 and 8005)
```

### Step 2: Register in Prompt Opinion

1. Add agent card URL to your Prompt Opinion workspace:
   `https://your-agent-url/.well-known/agent-card.json`
2. Set API key to your `API_KEYS` value
3. Test: open Samuel Brooks in Prompt Opinion, type the first demo question
4. Confirm briefing appears with URGENT findings

### Step 3: Record Demo Video (target 2:45–3:00)

Follow [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) exactly. Five questions, exact wording:

1. `What should I know before seeing Samuel today?`
2. `Is it safe to keep him on his current medications given his latest labs?`
3. `Has his kidney function been getting worse, and should I be worried?`
4. `Are there any test results that were never properly followed up on?`
5. `Give me the exact FDA language I should cite when talking to him today about stopping his metformin and ibuprofen`

Tools for recording: OBS Studio (free), Loom, or QuickTime

### Step 4: Fill In Placeholders

Update this file:
- [ ] [YOUR MARKETPLACE LINK] — Prompt Opinion marketplace URL for SafeSignal agent
- [ ] [YOUR MCP SERVER URL] — deployed MCP server base URL
- [ ] [YOUR VIDEO LINK] — uploaded demo video link (YouTube unlisted or Loom)
- [ ] [YOUR GITHUB REPO URL] — public GitHub repository URL
- [ ] [YOUR NAME(S)] — team member name(s)

### Step 5: Submit on Devpost

Go to the Agents Assemble hackathon page and submit with:
- [ ] Project title: SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent
- [ ] Short description (tagline) from this file
- [ ] Full description from this file
- [ ] Demo video link
- [ ] GitHub link
- [ ] Built With tags (list above)
- [ ] Screenshots from Prompt Opinion showing SafeSignal output
- [ ] Category: Both tracks (Agent + Superpower)

**Deadline: May 11 2026, 11:00 PM EDT**
**Winners announced: on or around May 27 2026**
