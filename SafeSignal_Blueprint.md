# SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent

## Hackathon: Agents Assemble — The Healthcare AI Endgame

### Submission for Prompt Opinion Platform | Devpost

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Why This Wins](#4-why-this-wins)
5. [Architecture](#5-architecture)
6. [MCP Server — The Superpower](#6-mcp-server--the-superpower)
7. [A2A Agent — The Superhero](#7-a2a-agent--the-superhero)
8. [FHIR Data Model](#8-fhir-data-model)
9. [SHARP Context Integration](#9-sharp-context-integration)
10. [LLM Prompt Engineering](#10-llm-prompt-engineering)
11. [Synthetic Patient Case](#11-synthetic-patient-case)
12. [Output Specification](#12-output-specification)
13. [Tools and Technologies](#13-tools-and-technologies)
14. [MVP Scope](#14-mvp-scope)
15. [Build Plan — 5 Days](#15-build-plan--5-days)
16. [Demo Script — 3 Minutes](#16-demo-script--3-minutes)
17. [Devpost Submission](#17-devpost-submission)
18. [Team Task Split](#18-team-task-split)
19. [Compliance and Safety Guardrails](#19-compliance-and-safety-guardrails)
20. [Advanced Features (Post-MVP)](#20-advanced-features-post-mvp)
21. [Competitive Differentiation](#21-competitive-differentiation)
22. [Risk Mitigation](#22-risk-mitigation)
23. [Reference Links](#23-reference-links)

---

## 1. Executive Summary

### Project Name

**SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent**

### One-Line Summary

SafeSignal is a dual MCP + A2A healthcare system on Prompt Opinion that scans FHIR patient data to detect hidden clinical risks — dangerous drug-lab mismatches, lost-to-follow-up critical findings, and silent deterioration patterns that no individual visit note reveals.

### Core Thesis

Every piece of data in the patient's chart is visible. The declining kidney function. The contraindicated medication. The cancer screening with no follow-up. Each data point exists in the EHR. The danger lies in the connections between data silos that no one has time to make. SafeSignal connects those dots.

### What Makes This Unique

This is the only submission that builds BOTH hackathon tracks — an MCP Superpower AND an A2A Agent — and makes them work together. The MCP server exposes reusable clinical reasoning tools that any agent in the ecosystem can wield. The A2A agent orchestrates those tools into a pre-visit risk briefing. This directly demonstrates the hackathon's core thesis: the power of AI lies in collaboration.

---

## 2. Problem Statement

### Problem 1: The Data Silo Trap

Modern EHRs store comprehensive patient data across dozens of screens, tabs, and resource types. A single patient may have hundreds of observations, dozens of medications, and years of encounter history. But this data is presented in silos:

- Medications live in the medication list
- Labs live in the results tab
- Conditions live in the problem list
- Encounters live in the visit history
- Referrals live in the orders section

No single screen shows the dangerous intersection: the medication that was safe when prescribed but is now contraindicated by last month's lab values. The abnormal result from a specialist visit that never triggered a follow-up in primary care. The slow decline that each individual visit note describes as "stable."

### Problem 2: The Speed of Clinical Practice

Primary care physicians spend an average of 15-18 minutes per patient visit. Before each visit, they must review the chart to understand the patient's current state. In practice, this means scanning the most recent note, glancing at the medication list, and checking if any new results are flagged. There is no time to trace a lab value backward across six visits to notice a deterioration trend. There is no time to cross-reference every active medication against every recent lab. There is no time to check whether every abnormal result from the past year has a documented follow-up.

The data is there. The time is not.

### Problem 3: The Preventable Harm

Preventable medical errors remain the third leading cause of death in the United States, with 250,000 to 400,000 deaths per year. Medication errors alone cause over 1.5 million injuries and over $3 billion in complication costs annually (Institute of Medicine). Studies estimate 7-8% of abnormal test results are never followed up on. Delayed diagnoses from lost-to-follow-up results are among the most common causes of malpractice claims.

These are not cases of bad medicine. They are cases of good doctors working in systems that make it nearly impossible to track every signal across every data silo for every patient.

### Problem 4: Existing Tools Miss the Pattern

Current clinical decision support (CDS) systems are primarily rule-based:

- Pharmacy systems check pairwise drug-drug interactions at the moment of prescribing
- EHR alerts fire when a single lab value crosses a threshold
- Quality measure dashboards check whether specific screenings are overdue

What these systems DO NOT do:

- Reason about compound risk across multiple medications, conditions, and lab trends simultaneously
- Detect trajectory patterns where each individual value is within normal limits but the trend is dangerous
- Identify follow-up gaps across providers and care settings
- Produce natural-language explanations of WHY a combination of findings constitutes a risk

This is the gap where generative AI adds genuine value that rule-based systems cannot replicate.

---

## 3. Solution Overview

SafeSignal operates at two levels:

### Level 1: MCP Server (Superpower)

A set of four FHIR-powered clinical reasoning tools exposed as an MCP server. These tools can be invoked by ANY agent in the Prompt Opinion ecosystem. They are the reusable weapons — the superpowers that any hero can wield.

### Level 2: A2A Agent (Superhero)

An intelligent agent published to the Prompt Opinion Marketplace that orchestrates the MCP tools, adds contextual reasoning, and delivers a structured risk briefing to clinicians. This is the superhero — equipped with superpowers and trained to use them for a specific mission.

### What It Produces

When a clinician invokes SafeSignal before a patient visit, the agent returns a Risk Briefing containing:

1. **Medication-Lab Mismatches** — Active medications that are now unsafe given current or trending lab values
2. **Lost-to-Follow-Up Alerts** — Abnormal findings with no documented subsequent action
3. **Silent Deterioration Warnings** — Observation trends that show progressive worsening despite notes describing the patient as "stable"
4. **Compound Risk Patterns** — Combinations of conditions, medications, and lab values that individually are manageable but together create elevated danger
5. **Evidence Citations** — Every alert cites the specific FHIR resources (Observation dates, values, MedicationRequest details, Condition codes) that support it
6. **Missing Evidence** — What data the agent could NOT find that would be needed to fully assess the risk

### What It Does NOT Do

- Does not diagnose
- Does not prescribe or recommend treatment changes
- Does not replace clinical judgment
- Does not submit orders or modify the medical record
- Does not make claims about certainty — uses language like "warrants review" and "consider evaluating"

---

## 4. Why This Wins

### Judging Criteria Alignment

**The AI Factor: "Does the solution leverage Generative AI to address a challenge that traditional rule-based software cannot?"**

Rule-based systems can check pairwise drug interactions. They cannot reason about compound risk across the full intersection of a patient's conditions, medications, labs, and temporal trends simultaneously. Rule-based systems can flag a single abnormal value. They cannot assess whether a SERIES of individually normal-range values represents a clinically concerning trajectory given the patient's context. This is genuine generative AI territory — the kind of reasoning that requires language understanding and clinical context synthesis that traditional software cannot perform.

**Potential Impact: "Does this address a significant pain point? Is there a clear hypothesis for how this improves outcomes, reduces costs, or saves time?"**

Patient safety. Not billing efficiency. Not operational optimization. The most fundamental responsibility in healthcare: making sure the data that could prevent harm actually reaches the clinician who needs to act on it. The hypothesis is direct — if a doctor sees a risk briefing before a visit that catches a contraindicated medication, a missed follow-up, or a deterioration pattern, they can act on it immediately rather than discovering it after an adverse event.

**Feasibility: "Could this exist in a real healthcare system today? Does architecture respect data privacy, safety standards, and regulatory constraints?"**

SafeSignal uses standard FHIR R4 resources through Prompt Opinion's SHARP context propagation. It makes no diagnostic claims. It requires human review for every alert. It is functionally equivalent to clinical decision support, which the FDA has largely exempted from medical device regulation under the 21st Century Cures Act (Section 3060) when the system supports rather than replaces clinical decision-making.

### Hackathon Theme Alignment

The event is called "Agents Assemble." The thesis is that the power of AI lies in collaboration. Nearly every other submission will build one agent that does one thing. SafeSignal builds both an MCP Superpower and an A2A Agent, and demonstrates them working together. More importantly, the MCP tools are designed to be REUSABLE — any other agent in the Prompt Opinion Marketplace can invoke SafeSignal's clinical reasoning tools. A scheduling agent can call `check_medication_safety` before confirming a refill. A triage agent can call `generate_risk_briefing` before routing a patient. A care coordination agent can call `find_lost_followups` across a panel.

This is not just an entry. It is a demonstration of the platform's value proposition.

### Judge-Specific Resonance

**Josh Mandel, MD** — Chief Architect for Health, Microsoft Research. Created SMART on FHIR. SafeSignal demonstrates deep, multi-resource FHIR usage: pulling temporal Observation series, cross-referencing MedicationRequests against Condition and Observation data, and building clinical intelligence from standardized data. This validates the vision he built.

**Joshua Hickey** — Principal Technical Product Manager, Mayo Clinic. Mayo handles complex multi-specialty patients. The compound risk detection and cross-provider follow-up gap detection mirrors real workflow challenges at large academic medical centers.

**Piyush Mathur, MD, FCCM, FASA, FAMIA** — Staff Anesthesiologist/Intensivist, Cleveland Clinic. ICU physicians deal with medication-lab mismatches in real-time. A potassium of 5.3 on an ACE inhibitor with declining renal function is the kind of finding that gets caught by a vigilant resident at 2 AM — or doesn't get caught at all. This resonates.

**Stephon Proctor, PhD, MBI** — ACHIO for Platform Innovation, CHOP. The composable MCP architecture is a platform innovation story. Individual tools that can be assembled into different workflows for different use cases — pediatric, adult, specialty-specific — without rebuilding the agent.

**Alice Zheng, MD, MBA, MPH** — Venture Capitalist. Massive addressable market. Every health system needs this. Clear path from hackathon demo to product. Defensible moat through clinical reasoning quality, not just technical implementation.

**Parth Tripathi** — Staff Engineer, Vertex AI Gemini Serving, Google. The trajectory analysis is technically interesting — reasoning about time-series clinical data with an LLM is a genuinely hard inference problem. The multi-tool orchestration pattern in the A2A agent demonstrates sophisticated agent architecture.

---

## 5. Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  PROMPT OPINION PLATFORM                     │
│                                                              │
│  ┌──────────┐    A2A Request     ┌────────────────────────┐  │
│  │ Clinician │ ─────────────────▶│  SafeSignal A2A Agent  │  │
│  │ Workspace │                   │  (The Superhero)       │  │
│  └──────────┘                   └───────────┬────────────┘  │
│                                              │               │
│                                   Orchestrates MCP Tools     │
│                                              │               │
│                                              ▼               │
│                                 ┌────────────────────────┐   │
│                                 │  SafeSignal MCP Server │   │
│                                 │  (The Superpower)      │   │
│                                 │                        │   │
│   Other Agents ────────────────▶│  Tools:                │   │
│   (can also call these tools)   │  • check_med_safety    │   │
│                                 │  • detect_deterioration│   │
│                                 │  • find_lost_followups │   │
│                                 │  • generate_briefing   │   │
│                                 └───────────┬────────────┘   │
│                                              │               │
└──────────────────────────────────────────────┼───────────────┘
                                               │
                              SHARP Context:   │
                              patientId        │
                              fhirUrl          │
                              fhirToken        │
                                               ▼
                                 ┌────────────────────────┐
                                 │     FHIR R4 Server     │
                                 │                        │
                                 │  Resources:            │
                                 │  • Patient             │
                                 │  • Condition           │
                                 │  • MedicationRequest   │
                                 │  • Observation         │
                                 │  • Encounter           │
                                 │  • Procedure           │
                                 │  • DiagnosticReport    │
                                 │  • ServiceRequest      │
                                 │  • AllergyIntolerance  │
                                 └────────────────────────┘
```

### Internal Agent Flow

```
Clinician Request
       │
       ▼
┌─────────────────┐
│ Parse SHARP      │ Extract patientId, fhirUrl, fhirToken
│ Context Metadata │ from A2A request metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FHIR Data        │ Parallel fetch:
│ Retrieval Layer  │ GET Patient, Conditions, MedicationRequests,
│                  │ Observations (historical series), Encounters,
│                  │ Procedures, AllergyIntolerances
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Clinical Context │ Normalize FHIR bundles into compact
│ Builder          │ structured objects. Build medication
│                  │ timeline, observation series, condition
│                  │ list, encounter history.
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│ Medication   │ │ Trajectory  │ │ Follow-Up   │ │ Compound     │
│ Safety Check │ │ Analysis    │ │ Gap Scan    │ │ Risk Check   │
│              │ │             │ │             │ │              │
│ Cross-ref    │ │ Trend eval  │ │ Abnormal    │ │ Multi-factor │
│ meds vs labs │ │ over time   │ │ results w/  │ │ risk combos  │
│ vs conditions│ │ series      │ │ no action   │ │              │
└──────┬───────┘ └──────┬──────┘ └──────┬──────┘ └──────┬───────┘
       │                │              │                │
       └────────────────┴──────────────┴────────────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │ LLM Reasoning Layer    │
                   │                        │
                   │ Synthesize all findings │
                   │ Assess severity         │
                   │ Generate natural-lang   │
                   │ risk briefing           │
                   │ Cite FHIR evidence      │
                   └───────────┬────────────┘
                               │
                               ▼
                   ┌────────────────────────┐
                   │ Compliance Guardrail   │
                   │ Layer                  │
                   │                        │
                   │ Remove diagnostic claims│
                   │ Add "clinician review"  │
                   │ Verify evidence cited   │
                   │ Flag uncertainty        │
                   └───────────┬────────────┘
                               │
                               ▼
                   ┌────────────────────────┐
                   │ Structured Response    │
                   │ to Prompt Opinion      │
                   └────────────────────────┘
```

---

## 6. MCP Server — The Superpower

The SafeSignal MCP Server exposes four tools that any agent on the Prompt Opinion platform can invoke. Each tool accepts a patient context (patient ID, FHIR server URL, FHIR access token) and returns structured clinical intelligence.

### Tool 1: `check_medication_safety`

**Purpose:** Cross-reference all active medications against current lab values, recent trends, active conditions, and allergies to identify medication-lab mismatches and compound risks.

**Input:**
```json
{
  "patient_id": "string",
  "fhir_url": "string",
  "fhir_token": "string"
}
```

**FHIR Resources Used:**
- MedicationRequest (status = active)
- Observation (most recent values for key labs: eGFR, potassium, INR, ALT/AST, A1c, creatinine, platelets, sodium)
- Condition (active problem list)
- AllergyIntolerance

**Clinical Logic (implemented via LLM with structured knowledge):**

| Medication Class | Lab Trigger | Condition Context | Risk |
|---|---|---|---|
| Metformin | eGFR < 30 | CKD, diabetes | Lactic acidosis |
| Metformin | eGFR 30-45 | CKD, diabetes | Dose reduction needed |
| Warfarin | No INR in > 4 weeks | AFib, DVT/PE | Unmonitored anticoagulation |
| Warfarin | INR > 4.0 | Any | Bleeding risk |
| ACE Inhibitor / ARB | Potassium > 5.0 | CKD | Hyperkalemia |
| ACE Inhibitor / ARB | eGFR declining > 30% | CKD | Accelerated renal decline |
| NSAIDs | eGFR < 30 | CKD | Nephrotoxicity |
| NSAIDs | Concurrent anticoagulant | Any | GI bleeding |
| NSAIDs | History of GI bleed | Any | Recurrent GI bleed |
| Statins | ALT > 3x upper limit | Any | Hepatotoxicity |
| Potassium-sparing diuretics | Potassium > 5.0 | CKD, heart failure | Hyperkalemia |
| Digoxin | Potassium < 3.5 | Heart failure | Digoxin toxicity |
| Digoxin | eGFR < 30 | CKD, heart failure | Accumulation toxicity |
| Lithium | Sodium < 135 | Bipolar disorder | Lithium toxicity |
| Lithium | eGFR < 45 | CKD | Accumulation toxicity |
| Opioids | Multiple prescribers | Chronic pain | Care fragmentation risk |

NOTE: This is not a comprehensive drug database. The LLM uses its clinical training knowledge to identify risks. The table above represents the minimum set of high-priority patterns that must be caught. The LLM may identify additional risks based on its training.

**Output:**
```json
{
  "medication_safety_alerts": [
    {
      "severity": "urgent | warning | informational",
      "medication": "Metformin 1000mg BID",
      "fhir_medication_request_id": "MedicationRequest/123",
      "risk_description": "eGFR has declined below 30. Most guidelines recommend discontinuation of metformin below eGFR 30 due to lactic acidosis risk.",
      "supporting_evidence": [
        {
          "resource_type": "Observation",
          "resource_id": "Observation/456",
          "description": "eGFR: 27 mL/min/1.73m2",
          "date": "2026-04-20"
        }
      ],
      "missing_evidence": [
        "No nephrology consultation documented"
      ],
      "recommended_action": "Clinician review recommended. Consider nephrology referral and medication adjustment."
    }
  ],
  "review_required": true,
  "disclaimer": "These alerts are for clinician review only. SafeSignal does not make treatment recommendations."
}
```

### Tool 2: `detect_silent_deterioration`

**Purpose:** Pull temporal observation series and assess whether trends indicate progressive worsening that individual visit notes may not capture.

**Input:**
```json
{
  "patient_id": "string",
  "fhir_url": "string",
  "fhir_token": "string",
  "observation_codes": ["eGFR", "HbA1c", "blood_pressure", "weight", "BMI"],
  "lookback_months": 24
}
```

**FHIR Resources Used:**
- Observation (historical series, sorted by date, for each requested observation type)
- Condition (for clinical context)
- Encounter (to correlate observations with visit dates)

**What Makes This Require Generative AI:**

A rule-based system can flag "eGFR < 30." But it cannot reason about: "eGFR has declined from 52 to 27 over 14 months. The rate of decline suggests progression to ESRD within 1-2 years at current trajectory. Each individual visit note described kidney function as 'stable' or 'chronic kidney disease, monitoring.' The trend tells a different story than any individual data point. Given the patient's concurrent diabetes with worsening A1c, the renal decline may be accelerating. No nephrology referral is documented."

This kind of multi-factor trajectory reasoning — combining the trend itself, the rate of change, the clinical context from other conditions, and the gap between what the notes say and what the data shows — is precisely where generative AI adds value that rule-based systems cannot.

**Tracked Observations:**

| Observation | What Deterioration Looks Like | Why It Matters |
|---|---|---|
| eGFR | Progressive decline across measurements | CKD progression, medication implications |
| HbA1c | Rising trend despite treatment | Diabetes management failure |
| Blood pressure | Upward trend despite antihypertensives | Treatment resistance, end-organ risk |
| Weight (in CHF patients) | Rapid gain over weeks | Fluid retention, decompensation |
| BMI | Steady increase | Metabolic syndrome risk |
| Creatinine | Progressive rise | Kidney function decline |
| Albumin | Progressive decline | Nutritional status, liver disease |

**Output:**
```json
{
  "deterioration_alerts": [
    {
      "observation_type": "eGFR",
      "trend_data": [
        {"value": 52, "date": "2025-02-15", "resource_id": "Observation/101"},
        {"value": 44, "date": "2025-08-10", "resource_id": "Observation/102"},
        {"value": 31, "date": "2025-12-05", "resource_id": "Observation/103"},
        {"value": 27, "date": "2026-04-20", "resource_id": "Observation/104"}
      ],
      "assessment": "Progressive renal decline from 52 to 27 over 14 months. Current trajectory suggests progression to ESRD within 1-2 years if rate of decline continues. No nephrology referral documented. Concurrent worsening A1c may be contributing to renal decline.",
      "severity": "urgent",
      "related_conditions": ["Type 2 diabetes mellitus", "Chronic kidney disease"],
      "documented_response": "No treatment escalation or specialist referral found in recent encounter notes."
    }
  ]
}
```

### Tool 3: `find_lost_followups`

**Purpose:** Identify abnormal diagnostic findings that have no documented subsequent follow-up action within expected timeframes.

**Input:**
```json
{
  "patient_id": "string",
  "fhir_url": "string",
  "fhir_token": "string",
  "lookback_days": 365
}
```

**FHIR Resources Used:**
- Observation (flagged as abnormal or outside reference range)
- DiagnosticReport (with abnormal findings)
- Encounter (subsequent encounters after abnormal findings)
- Procedure (follow-up procedures such as biopsies, imaging)
- ServiceRequest (referrals and orders — GI referral, urology referral, etc.)
- DocumentReference (referral letters, specialist notes)

**Follow-Up Expectation Logic:**

| Abnormal Finding | Expected Follow-Up | Expected Timeframe |
|---|---|---|
| Positive fecal occult blood | Colonoscopy or GI referral | 60 days |
| Abnormal mammogram (BI-RADS 4-5) | Diagnostic imaging or biopsy | 30 days |
| Elevated PSA (new or rising) | Urology referral or repeat PSA | 90 days |
| Abnormal Pap smear | Colposcopy or gynecology referral | 90 days |
| Significantly elevated liver enzymes | Repeat labs or hepatology referral | 60 days |
| New thyroid nodule on imaging | Thyroid ultrasound or endocrine referral | 90 days |
| Elevated blood glucose (new) | A1c test or diabetes workup | 30 days |
| Abnormal chest X-ray finding | CT follow-up or pulmonology referral | 60 days |

NOTE: The agent searches for ANY subsequent encounter, procedure, or referral that reasonably constitutes follow-up. It does not require exact procedure matching — it uses LLM reasoning to determine whether the documented actions after an abnormal result constitute appropriate follow-up.

**Output:**
```json
{
  "lost_followup_alerts": [
    {
      "severity": "urgent",
      "finding": "Positive fecal occult blood test",
      "finding_date": "2025-11-15",
      "finding_resource_id": "DiagnosticReport/789",
      "expected_followup": "Colonoscopy or GI referral within 60 days",
      "days_since_finding": 157,
      "documented_followup": "None found in Encounter, Procedure, or DocumentReference resources after finding date.",
      "risk": "Possible missed colorectal cancer screening"
    }
  ]
}
```

### Tool 4: `generate_risk_briefing`

**Purpose:** Orchestrate all three tools above and produce a unified, natural-language risk briefing for a clinician preparing for a patient visit.

**Input:**
```json
{
  "patient_id": "string",
  "fhir_url": "string",
  "fhir_token": "string",
  "include_modules": ["medication_safety", "deterioration", "lost_followups"],
  "context": "Optional clinician note or visit reason"
}
```

**Behavior:**

1. Calls `check_medication_safety`
2. Calls `detect_silent_deterioration` with standard observation set
3. Calls `find_lost_followups` with 365-day lookback
4. Passes all results to LLM with briefing generation prompt
5. Returns structured risk briefing with severity-ordered findings

**Output:** See Section 12 (Output Specification) for complete output format.

---

## 7. A2A Agent — The Superhero

### Agent Identity

```json
{
  "name": "SafeSignal",
  "description": "FHIR-aware clinical risk intelligence agent. Detects hidden medication-lab mismatches, lost-to-follow-up findings, and silent deterioration patterns in patient charts. Designed for clinician review before patient visits.",
  "version": "1.0.0",
  "capabilities": [
    "Pre-visit risk briefing generation",
    "Medication safety analysis",
    "Trajectory trend detection",
    "Follow-up gap identification",
    "FHIR R4 data retrieval and analysis"
  ],
  "required_context": {
    "patientId": "FHIR Patient resource ID",
    "fhirUrl": "FHIR server base URL",
    "fhirToken": "Bearer token for FHIR access"
  },
  "compliance_notes": [
    "Does not diagnose or prescribe",
    "All findings require clinician review",
    "Does not modify medical records",
    "Does not submit orders"
  ]
}
```

### Agent Behavior

The A2A agent handles conversational interaction with clinicians through Prompt Opinion. It:

1. Receives the user's message and patient context via A2A protocol
2. Extracts SHARP metadata (patientId, fhirUrl, fhirToken)
3. Invokes its own MCP tools to perform clinical analysis
4. Uses the LLM to synthesize findings into a natural-language risk briefing
5. Returns the briefing to the clinician in the Prompt Opinion workspace

### Example Interaction

**Clinician prompt:**
```
What should I know before seeing this patient today?
```

**SafeSignal response:**
```
SafeSignal Risk Briefing — Margaret Chen, Age 71

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 URGENT — Medication-Lab Mismatches (2 findings)

1. Metformin 1000mg BID — eGFR Critical
   Current eGFR: 27 mL/min/1.73m² (measured April 20, 2026)
   Metformin has been active for 3 years. eGFR has declined from
   52 to 27 over the past 14 months. Most clinical guidelines
   recommend discontinuation below eGFR 30 due to lactic acidosis
   risk. No medication adjustment or nephrology referral documented.

   Evidence: Observation/104 (eGFR 27, 2026-04-20),
   MedicationRequest/201 (Metformin, active since 2023-03-15)

2. Ibuprofen 400mg PRN + eGFR 27 + Warfarin
   Ibuprofen was prescribed 3 months ago by urgent care. In a
   patient with CKD stage 4 (eGFR 27), NSAIDs accelerate renal
   decline. Concurrent warfarin use creates additional GI bleeding
   risk. This represents a compound risk from two independent
   prescribing events.

   Evidence: MedicationRequest/205 (Ibuprofen, 2026-01-20),
   MedicationRequest/203 (Warfarin, active),
   Observation/104 (eGFR 27, 2026-04-20)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 WARNING — Follow-Up Gap (1 finding)

3. Positive Fecal Occult Blood — No Documented Follow-Up
   Positive FOBT documented November 15, 2025 (157 days ago).
   No colonoscopy, GI referral, or repeat testing found in
   subsequent encounters. Expected follow-up within 60 days.

   Evidence: DiagnosticReport/789 (FOBT positive, 2025-11-15)
   Missing: No Procedure or DocumentReference matching
   colonoscopy or GI referral after 2025-11-15

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 WARNING — Silent Deterioration (2 patterns)

4. Kidney Function — Progressive Decline
   eGFR: 52 → 44 → 31 → 27 over 14 months
   Rate of decline suggests progression toward ESRD within 1-2
   years at current trajectory. Each encounter note describes CKD
   as "chronic kidney disease, monitoring." No nephrology referral.
   Concurrent diabetes with worsening A1c may be accelerating
   renal decline.

5. Glycemic Control — Worsening Trend
   A1c: 7.1 → 7.6 → 8.2 over 18 months
   Progressive increase despite no documented change in diabetes
   management. Current metformin may need reassessment
   (especially given renal concerns above).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  INFORMATIONAL — Additional Monitoring Notes

6. Warfarin — INR Overdue
   Last documented INR: 2.4 (measured 11 weeks ago).
   Standard monitoring interval for stable patients is every 4
   weeks. Overdue by approximately 7 weeks.

   Evidence: Observation/108 (INR 2.4, 2026-02-14)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚕️  COMPLIANCE NOTE
All findings are for clinician review only. SafeSignal does not
diagnose, prescribe, or make treatment recommendations. Final
clinical decisions must be made by the treating provider based
on their direct assessment of the patient.
```

---

## 8. FHIR Data Model

### Required FHIR Resources

| Resource | Purpose | Key Fields Used |
|---|---|---|
| Patient | Demographics, age calculation | birthDate, gender, name |
| Condition | Active problem list | code, clinicalStatus, onsetDateTime |
| MedicationRequest | Active medication list | medicationCodeableConcept, status, authoredOn, requester |
| Observation | Lab values, vitals, time series | code, valueQuantity, effectiveDateTime, referenceRange, interpretation |
| Encounter | Visit history, follow-up tracking | type, period, reasonCode, status |
| Procedure | Follow-up procedures | code, performedDateTime, status |
| DiagnosticReport | Study results, imaging findings | code, conclusion, effectiveDateTime, status |
| ServiceRequest | Referrals and orders | code, category, status, intent, authoredOn, requester |
| AllergyIntolerance | Drug allergy cross-check | code, clinicalStatus, type |

### FHIR Queries

```
# Patient demographics
GET [fhirUrl]/Patient/[patientId]

# Active conditions
GET [fhirUrl]/Condition?patient=[patientId]&clinical-status=active

# Active medications
GET [fhirUrl]/MedicationRequest?patient=[patientId]&status=active

# Observations — historical series (past 24 months)
GET [fhirUrl]/Observation?patient=[patientId]&date=ge2024-04-01&_sort=-date&_count=200

# Recent encounters (past 12 months)
GET [fhirUrl]/Encounter?patient=[patientId]&date=ge2025-04-01&_sort=-date

# Procedures (past 12 months)
GET [fhirUrl]/Procedure?patient=[patientId]&date=ge2025-04-01

# Service requests / referrals (past 12 months)
GET [fhirUrl]/ServiceRequest?patient=[patientId]&authored=ge2025-04-01&_sort=-authored

# Diagnostic reports (past 12 months)
GET [fhirUrl]/DiagnosticReport?patient=[patientId]&date=ge2025-04-01

# Allergies
GET [fhirUrl]/AllergyIntolerance?patient=[patientId]&clinical-status=active
```

### Normalized Internal Data Object

After retrieving FHIR resources, the agent normalizes the data into a compact internal structure for LLM processing:

```json
{
  "patient": {
    "id": "patient-123",
    "age": 71,
    "sex": "female",
    "name": "Margaret Chen"
  },
  "conditions": [
    {
      "display": "Type 2 diabetes mellitus",
      "code": "E11.9",
      "system": "ICD-10",
      "onset": "2018-03-01",
      "status": "active"
    },
    {
      "display": "Essential hypertension",
      "code": "I10",
      "system": "ICD-10",
      "onset": "2015-06-15",
      "status": "active"
    },
    {
      "display": "Atrial fibrillation",
      "code": "I48.91",
      "system": "ICD-10",
      "onset": "2020-11-10",
      "status": "active"
    },
    {
      "display": "Chronic kidney disease, stage 4",
      "code": "N18.4",
      "system": "ICD-10",
      "onset": "2024-12-05",
      "status": "active"
    }
  ],
  "medications": [
    {
      "display": "Metformin 1000mg BID",
      "code": "860975",
      "system": "RxNorm",
      "authored_on": "2023-03-15",
      "status": "active",
      "prescriber": "Dr. James Liu (PCP)",
      "resource_id": "MedicationRequest/201"
    },
    {
      "display": "Warfarin 5mg daily",
      "code": "855332",
      "system": "RxNorm",
      "authored_on": "2020-11-15",
      "status": "active",
      "prescriber": "Dr. Sarah Park (Cardiology)",
      "resource_id": "MedicationRequest/203"
    },
    {
      "display": "Lisinopril 20mg daily",
      "code": "314076",
      "system": "RxNorm",
      "authored_on": "2016-01-10",
      "status": "active",
      "prescriber": "Dr. James Liu (PCP)",
      "resource_id": "MedicationRequest/204"
    },
    {
      "display": "Ibuprofen 400mg PRN",
      "code": "197806",
      "system": "RxNorm",
      "authored_on": "2026-01-20",
      "status": "active",
      "prescriber": "Dr. Urgent Care Provider",
      "resource_id": "MedicationRequest/205"
    }
  ],
  "observation_series": {
    "eGFR": [
      {"value": 52, "unit": "mL/min/1.73m2", "date": "2025-02-15", "resource_id": "Observation/101"},
      {"value": 44, "unit": "mL/min/1.73m2", "date": "2025-08-10", "resource_id": "Observation/102"},
      {"value": 31, "unit": "mL/min/1.73m2", "date": "2025-12-05", "resource_id": "Observation/103"},
      {"value": 27, "unit": "mL/min/1.73m2", "date": "2026-04-20", "resource_id": "Observation/104"}
    ],
    "HbA1c": [
      {"value": 7.1, "unit": "%", "date": "2024-10-08", "resource_id": "Observation/105"},
      {"value": 7.6, "unit": "%", "date": "2025-06-12", "resource_id": "Observation/106"},
      {"value": 8.2, "unit": "%", "date": "2026-02-20", "resource_id": "Observation/107"}
    ],
    "INR": [
      {"value": 2.4, "unit": "ratio", "date": "2026-02-14", "resource_id": "Observation/108"}
    ],
    "Potassium": [
      {"value": 4.2, "unit": "mmol/L", "date": "2025-02-15", "resource_id": "Observation/109"},
      {"value": 4.8, "unit": "mmol/L", "date": "2025-08-10", "resource_id": "Observation/110"},
      {"value": 5.3, "unit": "mmol/L", "date": "2026-04-20", "resource_id": "Observation/111"}
    ],
    "Blood Pressure": [
      {"value": "138/82", "unit": "mmHg", "date": "2025-02-15", "resource_id": "Observation/112"},
      {"value": "142/88", "unit": "mmHg", "date": "2025-08-10", "resource_id": "Observation/113"},
      {"value": "148/90", "unit": "mmHg", "date": "2025-12-05", "resource_id": "Observation/114"},
      {"value": "155/94", "unit": "mmHg", "date": "2026-04-20", "resource_id": "Observation/115"}
    ]
  },
  "diagnostic_reports": [
    {
      "display": "Fecal Occult Blood Test",
      "result": "Positive",
      "date": "2025-11-15",
      "resource_id": "DiagnosticReport/789",
      "ordering_provider": "Dr. James Liu (PCP)"
    }
  ],
  "allergies": [
    {
      "display": "Penicillin",
      "reaction": "Rash",
      "status": "active"
    }
  ],
  "recent_encounters": [
    {
      "date": "2026-04-20",
      "type": "Office Visit",
      "provider": "Dr. James Liu (PCP)",
      "reason": "Routine follow-up"
    },
    {
      "date": "2026-01-20",
      "type": "Urgent Care Visit",
      "provider": "Dr. Urgent Care Provider",
      "reason": "Left knee pain"
    },
    {
      "date": "2025-12-05",
      "type": "Office Visit",
      "provider": "Dr. James Liu (PCP)",
      "reason": "Routine follow-up"
    }
  ]
}
```

---

## 9. SHARP Context Integration

SafeSignal uses Prompt Opinion's SHARP Extension Specs to receive patient context securely. The SHARP metadata is automatically propagated through the A2A request when a clinician invokes the agent within a patient context.

### Expected SHARP Metadata

```json
{
  "sharp_context": {
    "patientId": "patient-123",
    "fhirUrl": "https://fhir.example.com/r4",
    "fhirToken": "Bearer eyJhbGciOiJSUzI1NiIs...",
    "fhirVersion": "R4",
    "userId": "practitioner-456",
    "organizationId": "org-789"
  }
}
```

### How SafeSignal Uses SHARP

1. Agent receives A2A request from Prompt Opinion
2. Extracts `patientId`, `fhirUrl`, and `fhirToken` from SHARP metadata
3. Uses token to authenticate all FHIR API requests
4. Passes FHIR data to clinical reasoning tools
5. Returns results through A2A response — no data is stored by the agent

### Token Handling

- The FHIR token is used only for the duration of the request
- No patient data is cached or persisted by the agent
- All FHIR requests use the token provided by the platform
- If the token is expired or invalid, the agent returns an error message requesting re-authentication through the platform

---

## 10. LLM Prompt Engineering

### System Prompt for Risk Briefing Generation

```
You are SafeSignal, a clinical risk intelligence assistant. Your role is to analyze
structured patient chart data and identify hidden clinical risks that a busy clinician
might miss during a pre-visit chart review.

CRITICAL RULES:

1. NEVER diagnose. You identify RISKS and PATTERNS, not diagnoses.
2. NEVER prescribe or recommend specific treatments. Say "consider evaluating"
   or "warrants clinician review" instead.
3. NEVER invent data. Only reference information present in the provided chart data.
4. ALWAYS cite the specific FHIR resource (resource type and ID, date, value) that
   supports each finding.
5. ALWAYS note what evidence is MISSING that would be needed for a complete assessment.
6. Use severity levels:
   - URGENT: Immediate patient safety risk (contraindicated medication, dangerous
     lab-medication combination)
   - WARNING: Significant clinical concern requiring attention at this visit
     (lost follow-up on potential malignancy, progressive deterioration without
     specialist referral)
   - INFORMATIONAL: Monitoring gap or minor concern (overdue routine lab,
     suboptimal but not dangerous trend)
7. Do not repeat information already visible on standard EHR dashboards
   (e.g., "patient has diabetes" is not useful). Focus on CONNECTIONS between
   data points that require cross-referencing multiple data sources.
8. When analyzing trends, state the trajectory clearly: "Value X changed from A to B
   over N months." Do not use vague language like "somewhat elevated."
9. End every briefing with the compliance disclaimer.

OUTPUT FORMAT:

Return a structured risk briefing organized by severity (URGENT first, then WARNING,
then INFORMATIONAL). Each finding should include:
- A clear title
- A natural-language explanation of WHY this is a risk
- Specific FHIR evidence (resource IDs, dates, values)
- What evidence is missing
- What action might be warranted (phrased as a suggestion for clinician consideration)

WHAT TO LOOK FOR:

1. MEDICATION-LAB MISMATCHES
   Medications that were safe when prescribed but are now contraindicated by current
   or trending lab values. Pay special attention to:
   - Renal-cleared drugs in declining kidney function
   - Drugs requiring therapeutic monitoring that is overdue
   - NSAIDs in patients with CKD or on anticoagulants
   - Potassium-affecting drugs in patients with rising potassium
   - Compound risks where multiple medications individually create manageable risk
     but together create elevated danger

2. LOST-TO-FOLLOW-UP
   Abnormal findings (lab results, imaging, diagnostic reports) that have no
   documented subsequent action (follow-up encounter, procedure, referral, or repeat
   test) within clinically expected timeframes. Focus on findings where delayed
   follow-up has significant clinical consequences (cancer screening, critical lab
   values, imaging findings requiring biopsy).

3. SILENT DETERIORATION
   Time-series trends where each individual value might appear manageable in isolation
   but the trajectory tells a concerning story. Key patterns:
   - Progressive organ function decline (eGFR, liver function)
   - Worsening metabolic control (A1c, blood glucose)
   - Rising blood pressure despite antihypertensive therapy
   - Weight changes suggesting fluid retention in heart failure
   Look for discrepancy between trend data and encounter note language — if notes
   say "stable" but the trend shows progressive worsening, flag it.

4. COMPOUND RISK
   Combinations of conditions, medications, and lab trends that individually might
   be managed but together create synergistic risk. Example: CKD + ACE inhibitor +
   rising potassium + NSAID use = multiple simultaneous kidney and cardiac risks.
```

### System Prompt for Individual MCP Tools

Each MCP tool uses a focused prompt that is a subset of the master prompt above, tailored to its specific function. This keeps token usage efficient for standalone tool calls.

```
# check_medication_safety prompt
You are a medication safety analysis tool. Given a patient's active medications,
current lab values, and active conditions, identify medications that may be unsafe
given the patient's current clinical state.

[Include only the MEDICATION-LAB MISMATCHES section from master prompt]
[Include rules 1-8 from master prompt]

# detect_silent_deterioration prompt
You are a clinical trend analysis tool. Given a series of observation values over
time for a patient, assess whether any trends indicate progressive clinical
deterioration that individual visit notes may not have captured.

[Include only the SILENT DETERIORATION section from master prompt]
[Include rules 1-8 from master prompt]

# find_lost_followups prompt
You are a follow-up gap detection tool. Given a patient's abnormal findings and
their subsequent encounter, procedure, and referral history, identify critical
findings that appear to have no documented follow-up action.

[Include only the LOST-TO-FOLLOW-UP section from master prompt]
[Include rules 1-8 from master prompt]
```

---

## 11. Synthetic Patient Case

### Patient: Margaret Chen

This is the synthetic patient used for development, testing, and demo. All data is fictional.

**Why this case is effective for a demo:**

The case is designed to show eight or more distinct findings of varying severity that all exist in a chart a PCP would describe as "routine follow-up." Each finding is individually plausible — the kind of thing that happens every day in busy clinics. The power of the demo is showing that a 15-minute chart review would likely catch 1-2 of these, but SafeSignal catches all of them and explains the connections between them.

### Patient Demographics

| Field | Value |
|---|---|
| Name | Margaret Chen |
| Age | 71 |
| Sex | Female |
| Patient ID | patient-mc-071 |

### Active Conditions

| Condition | ICD-10 | Onset | Notes |
|---|---|---|---|
| Type 2 diabetes mellitus | E11.9 | 2018-03-01 | 8 years, currently on metformin |
| Essential hypertension | I10 | 2015-06-15 | On lisinopril |
| Atrial fibrillation | I48.91 | 2020-11-10 | On warfarin |
| Chronic kidney disease, stage 4 | N18.4 | 2024-12-05 | Recently progressed from stage 3b |

### Active Medications

| Medication | Dose | Frequency | Prescribed By | Start Date |
|---|---|---|---|---|
| Metformin | 1000mg | BID | Dr. James Liu (PCP) | 2023-03-15 |
| Warfarin | 5mg | Daily | Dr. Sarah Park (Cardiology) | 2020-11-15 |
| Lisinopril | 20mg | Daily | Dr. James Liu (PCP) | 2016-01-10 |
| Ibuprofen | 400mg | PRN | Urgent Care Provider | 2026-01-20 |

### Observation History

**eGFR (mL/min/1.73m²):**
| Date | Value | Provider Visit |
|---|---|---|
| 2025-02-15 | 52 | PCP routine |
| 2025-08-10 | 44 | PCP routine |
| 2025-12-05 | 31 | PCP routine |
| 2026-04-20 | 27 | PCP routine |

**HbA1c (%):**
| Date | Value | Provider Visit |
|---|---|---|
| 2024-10-08 | 7.1 | PCP routine |
| 2025-06-12 | 7.6 | PCP routine |
| 2026-02-20 | 8.2 | PCP routine |

**INR (ratio):**
| Date | Value | Provider Visit |
|---|---|---|
| 2025-11-20 | 2.1 | Anticoag clinic |
| 2026-02-14 | 2.4 | Anticoag clinic |

**Potassium (mmol/L):**
| Date | Value |
|---|---|
| 2025-02-15 | 4.2 |
| 2025-08-10 | 4.8 |
| 2026-04-20 | 5.3 |

**Blood Pressure (mmHg):**
| Date | Value |
|---|---|
| 2025-02-15 | 138/82 |
| 2025-08-10 | 142/88 |
| 2025-12-05 | 148/90 |
| 2026-04-20 | 155/94 |

### Diagnostic Reports

| Date | Test | Result | Ordering Provider |
|---|---|---|---|
| 2025-11-15 | Fecal Occult Blood Test | Positive | Dr. James Liu (PCP) |

### Allergies

| Allergen | Reaction |
|---|---|
| Penicillin | Rash |

### Recent Encounter Notes (abbreviated)

**2026-04-20 — PCP Routine Follow-Up:**
"71yo F here for routine follow-up. Diabetes — continue current management. HTN — stable. CKD — monitoring. Refill medications. Follow up 3 months."

**2026-01-20 — Urgent Care Visit:**
"Patient presents with left knee pain x 2 weeks. No trauma. Mild swelling. Prescribed ibuprofen 400mg PRN. Follow up with PCP if not improving."

**2025-12-05 — PCP Routine Follow-Up:**
"Routine follow-up. Chronic conditions stable. Labs reviewed. Continue current management."

### What SafeSignal Should Catch

| # | Finding | Severity | Type |
|---|---|---|---|
| 1 | Metformin with eGFR 27 — below discontinuation threshold (FDA label: contraindicated below eGFR 30) | URGENT | Medication-Lab Mismatch |
| 2 | Lisinopril + potassium 5.3 + eGFR 27 — hyperkalemia risk with 38% renal decline | URGENT | Medication-Lab Mismatch |
| 3 | Ibuprofen + Warfarin — bleeding interaction (FDA drug interactions label cited, severity: documented) | URGENT | Drug-Drug Interaction |
| 4 | Positive FOBT 157 days ago — no colonoscopy or GI referral in ServiceRequests, Encounters, or Procedures | WARNING | Lost Follow-Up |
| 5 | eGFR declining 52→27 over 14 months, no nephrology referral | WARNING | Silent Deterioration |
| 6 | A1c rising 7.1→8.2 over 18 months, no treatment change | WARNING | Silent Deterioration |
| 7 | Blood pressure rising 138/82→155/94 over 14 months despite Lisinopril | WARNING | Silent Deterioration |
| 8 | Warfarin INR last checked 65+ days ago (FDA boxed warning: regular monitoring required) | INFORMATIONAL | Monitoring Gap |

---

## 12. Output Specification

### Structured JSON Output Schema

```json
{
  "risk_briefing": {
    "patient_id": "string",
    "patient_summary": "string (age, sex, key conditions)",
    "generated_at": "ISO 8601 datetime",
    "total_findings": "integer",
    "findings_by_severity": {
      "urgent": "integer",
      "warning": "integer",
      "informational": "integer"
    },
    "findings": [
      {
        "id": "integer (sequential)",
        "severity": "urgent | warning | informational",
        "category": "medication_safety | lost_followup | silent_deterioration | compound_risk",
        "title": "string (brief descriptive title)",
        "explanation": "string (natural-language description of the risk)",
        "supporting_evidence": [
          {
            "resource_type": "string (FHIR resource type)",
            "resource_id": "string (FHIR resource ID)",
            "description": "string (what this resource shows)",
            "date": "string (ISO date)"
          }
        ],
        "missing_evidence": ["string (what data is absent)"],
        "suggested_consideration": "string (what a clinician might consider, phrased carefully)"
      }
    ],
    "compliance_disclaimer": "string (standard disclaimer text)"
  }
}
```

---

## 13. Tools and Technologies

### Core Stack

| Component | Technology | Purpose |
|---|---|---|
| Platform | Prompt Opinion | Agent hosting, marketplace, SHARP context |
| Protocol (Agent) | A2A (Agent-to-Agent) | Agent communication and interoperability |
| Protocol (Tools) | MCP (Model Context Protocol) / FastMCP | Reusable tool exposure via SSE |
| Data Standard | FHIR R4 | Patient data retrieval (9 resource types) |
| Context Propagation | SHARP Extension Specs | Secure patient context handoff |
| Agent Framework | Google ADK | ADK tools and session management |
| LLM Routing | LiteLLM | Multi-model routing (Gemini, Claude, GPT-4.1) |
| Language | Python 3.11+ | Agent backend |
| Web Framework | FastAPI + Uvicorn | Agent HTTP server |
| LLM API | Gemini 2.5 Flash (default) / Claude / GPT-4.1 | Clinical reasoning |
| HTTP Client | httpx | FHIR and external API calls |
| External APIs | FDA OpenFDA Drug Labels (api.fda.gov) | Boxed warnings, contraindications, drug interactions |
| External APIs | NLM RxNav Drug Interactions — ONCHigh | Per-drug interaction database lookup |
| External APIs | RxNorm/RxNav (rxnav.nlm.nih.gov) | Drug ingredient to RxCUI standardization |
| Code Hosting | GitHub | Repository |
| Submission | Devpost | Hackathon submission |

### FHIR Server for Development

Use one of these public FHIR sandbox servers for development and testing:

| Server | URL | Notes |
|---|---|---|
| HAPI FHIR Public | https://hapi.fhir.org/baseR4 | Open, no auth needed, can create test data |
| Logica Health Sandbox | https://launch.smarthealthit.org | SMART on FHIR compatible, requires free account |
| Synthea | Generate locally | Synthetic patient generator, creates realistic FHIR bundles |

For the demo, you can either use a public sandbox with pre-loaded synthetic data or host a lightweight FHIR server locally with the Margaret Chen case pre-loaded.

### LLM Selection

Use whichever API key your team already has. All major LLMs can handle this task.

| Model | Strengths for This Use Case |
|---|---|
| Claude (Sonnet/Opus) | Strong long-context reasoning, careful with medical claims |
| GPT-4.1 / GPT-4o | Good structured output, fast |
| Gemini | Good if using Google Cloud stack |

Recommendation: Claude or GPT-4.1 for the clinical reasoning quality. The prompt requires the model to be careful about overstepping clinical boundaries, and both handle this well.

### Development Repository

Start from the official Prompt Opinion Python A2A sample repository (healthcare agent pattern).

Key files to modify or create:

```
safesignal/
├── agent.py              # A2A agent definition and behavior
├── app.py                # FastAPI application, A2A endpoint
├── mcp_server.py         # MCP server exposing 4 tools
├── tools/
│   ├── fhir_client.py    # FHIR API client (fetch resources)
│   ├── medication_safety.py   # Tool 1 logic
│   ├── deterioration.py       # Tool 2 logic
│   ├── lost_followups.py      # Tool 3 logic
│   └── risk_briefing.py       # Tool 4 orchestrator
├── prompts/
│   ├── system_prompt.py       # Master LLM prompt
│   ├── med_safety_prompt.py   # Tool 1 prompt
│   ├── deterioration_prompt.py # Tool 2 prompt
│   └── followup_prompt.py     # Tool 3 prompt
├── models/
│   ├── fhir_models.py    # Normalized patient data structures
│   └── output_models.py  # Risk briefing output schema
├── config.py             # Configuration (LLM API key, defaults)
├── synthetic_data/
│   └── margaret_chen.json  # Synthetic FHIR bundle for demo
└── README.md
```

---

## 14. MVP Scope

### Must Build

| Feature | Priority | Reason |
|---|---|---|
| A2A agent on Prompt Opinion | Critical | Required by hackathon |
| MCP server with 4 tools | Critical | Differentiator — both tracks |
| SHARP context extraction | Critical | Required by hackathon |
| FHIR data retrieval (Patient, Condition, MedicationRequest, Observation) | Critical | Data foundation |
| Medication safety analysis | Critical | Highest-impact finding category |
| Silent deterioration detection (eGFR, A1c at minimum) | Critical | Unique AI-requiring feature |
| Lost-to-follow-up detection | Critical | Strong emotional demo moment |
| Risk briefing generation | Critical | User-facing output |
| Synthetic patient case | Critical | Demo foundation |
| Prompt Opinion marketplace publish | Critical | Required by hackathon |
| Demo video (under 3 minutes) | Critical | Required by hackathon |

### Do NOT Build in MVP

| Feature | Why Not |
|---|---|
| Real EHR integration | Out of scope, not needed for demo |
| Full drug database | LLM knowledge is sufficient for demo patterns |
| Multiple synthetic patients | One great case beats three mediocre ones |
| User authentication | Handled by Prompt Opinion |
| Data persistence | Agent is stateless, no storage needed |
| Custom UI | Agent responds through Prompt Opinion workspace |
| Multi-language support | English only for MVP |
| Audit logging | Not needed for hackathon |
| Batch processing (panel review) | Post-MVP feature |

---

## 15. Build Plan — 5 Days

### Day 1 (Wednesday May 7): Foundation

**Morning:**
- Fork the Prompt Opinion sample healthcare agent repository
- Run it locally, confirm it works
- Read the SHARP Extension Specs documentation fully
- Read the Prompt Opinion MCP integration documentation
- Verify: can a Prompt Opinion agent call its own MCP tools?

**Afternoon:**
- Modify agent identity (name: SafeSignal, description, capabilities)
- Set up the MCP server skeleton with 4 tool stubs
- Set up the FHIR client module with basic GET requests
- Create the synthetic Margaret Chen FHIR bundle (JSON)
- Decision point: confirm MCP-to-A2A interop works on platform. If it doesn't work easily, fall back to A2A-only with MCP as bonus demo.

**End of Day 1 Deliverable:** Agent runs locally, responds to basic prompts, FHIR client can fetch from sandbox server.

### Day 2 (Thursday May 8): FHIR + Core Tools

**Morning:**
- Implement FHIR data retrieval for all 8 resource types
- Build the clinical context normalizer (FHIR bundles → compact JSON)
- Load synthetic patient data into FHIR sandbox OR create local mock

**Afternoon:**
- Implement Tool 1: `check_medication_safety` (FHIR fetch + LLM prompt)
- Implement Tool 2: `detect_silent_deterioration` (historical Observation series + LLM prompt)
- Test both tools against Margaret Chen data
- Iterate on LLM prompts until output quality is good

**End of Day 2 Deliverable:** Two tools working, producing correct findings for Margaret Chen case.

### Day 3 (Friday May 9): Remaining Tools + Integration

**Morning:**
- Implement Tool 3: `find_lost_followups`
- Implement Tool 4: `generate_risk_briefing` (orchestrates tools 1-3)
- Test full risk briefing output against Margaret Chen

**Afternoon:**
- Integrate MCP tools with A2A agent
- Test end-to-end flow: Prompt Opinion → A2A agent → MCP tools → FHIR → LLM → response
- Iterate on output formatting (make the risk briefing readable and compelling)
- Debug and fix issues

**End of Day 3 Deliverable:** Full agent working end-to-end. All key findings detected (8+). Output is clear.

### Day 4 (Saturday May 10): Publish + Polish

**Morning:**
- Publish agent to Prompt Opinion Marketplace
- Test invocation from within Prompt Opinion platform
- Fix any platform-specific issues
- Demonstrate MCP tools being called independently (for demo)

**Afternoon:**
- Polish output formatting
- Write the demo script
- Do a practice run of the demo (time it!)
- Prepare Devpost submission text
- Take screenshots of Prompt Opinion integration

**End of Day 4 Deliverable:** Agent published and working on Prompt Opinion. Demo script written. Practice run completed under 3 minutes.

### Day 5 (Sunday May 11): Record + Submit

**Morning:**
- Record demo video (aim for 2 takes maximum)
- Edit video if needed (keep it clean, no fancy effects needed)
- Review video — does it tell the story clearly?

**Afternoon:**
- Write and submit Devpost entry
- Upload demo video
- Include screenshots, architecture diagram, and GitHub link
- Final review of all submission materials
- Submit before 11:00 PM EDT deadline

**End of Day 5 Deliverable:** Submitted.

---

## 16. Demo Script — 3 Minutes

### 0:00 – 0:15 — The Hook

*"Every piece of data in Margaret's chart was visible to her doctors. The declining kidney function. The medication that should have been stopped. The cancer screening with no follow-up. Each one was in the EHR. No one connected the dots — because EHRs show you data in silos. SafeSignal connects the dots."*

### 0:15 – 0:40 — What SafeSignal Is

*"SafeSignal is two things. First, an MCP server — a set of reusable clinical reasoning tools that any agent on Prompt Opinion can call. Second, an A2A agent that orchestrates those tools into a pre-visit risk briefing. We built both tracks of this hackathon and made them work together."*

Show: Agent card in Prompt Opinion. MCP tool listing.

### 0:40 – 0:50 — Invoking the Agent

Show: Typing in Prompt Opinion workspace:

> "What should I know before seeing this patient today?"

### 0:50 – 1:50 — The Output

Show the risk briefing appearing. Narrate the key findings:

*"SafeSignal found eight things hiding in this chart."*

*"First: Margaret has been on metformin for three years, but her kidney function has dropped below the threshold where the FDA says to stop it. Per the FDA drug label: 'Severe renal impairment — eGFR below 30 — contraindicated.' Nobody changed the medication because nobody looked at the trend — each individual visit just said 'CKD, monitoring.'"*

*"Second: An urgent care visit three months ago added ibuprofen for knee pain. That provider didn't know Margaret's eGFR was 27. An NSAID in a patient with stage 4 CKD who's also on warfarin — that's compound risk from two prescribers who didn't see each other's context. The FDA drug label for ibuprofen calls it out directly: 'take a blood thinning anticoagulant... are age 60 or older.' Margaret is 71."*

*"Third: a positive fecal occult blood test from five months ago. No colonoscopy. No GI referral. SafeSignal checked Encounters, Procedures, and ServiceRequests before making that call. One hundred fifty-seven days and counting."*

### 1:50 – 2:20 — The Architecture Story

*"Here's what makes SafeSignal different from a standalone alert tool. The clinical reasoning lives in an MCP server — these are reusable tools."*

Show: calling `check_medication_safety` directly as an MCP tool call.

*"Any agent on this platform can call these tools. A scheduling agent could check medication safety before confirming a refill. A care coordination agent could scan for lost follow-ups across an entire panel. We didn't just solve one problem — we built infrastructure that makes the whole ecosystem smarter."*

### 2:20 – 2:50 — Impact

*"Margaret Chen is synthetic. But her story is not. Patients on contraindicated medications because nobody rechecked the labs. Abnormal results with no follow-up. Slow deterioration that each note calls 'stable.' These patterns hide in FHIR data that already exists. They just need someone to look across the silos."*

### 2:50 – 3:00 — Close

*"SafeSignal. The risks are in the chart. We help you find them."*

---

## 17. Devpost Submission

### Project Title

SafeSignal: FHIR-Aware Clinical Risk Intelligence Agent

### Short Description

SafeSignal detects hidden clinical risks in patient charts by cross-referencing FHIR data across medications, labs, conditions, and time — catching dangerous drug-lab mismatches, lost-to-follow-up findings, and silent deterioration patterns that individual visit notes miss.

### Full Description

SafeSignal is a dual MCP + A2A healthcare system built for Prompt Opinion that finds the clinical risks hiding between EHR data silos.

Modern EHRs store comprehensive patient data — medications, labs, conditions, encounters — but present it in separate screens and tabs. The dangerous signals live in the connections: the medication that was safe when prescribed but is now contraindicated by recent labs. The abnormal test from five months ago that no one followed up on. The kidney function that's been declining visit over visit while each note says "stable."

SafeSignal addresses this by building both tracks of the hackathon:

**MCP Superpower:** Four reusable clinical reasoning tools — medication safety checking, trajectory analysis, follow-up gap detection, and risk briefing generation — exposed as an MCP server that any agent on the platform can invoke.

**A2A Agent:** An intelligent agent published to the Prompt Opinion Marketplace that orchestrates these tools and delivers a severity-ordered risk briefing for clinician review before patient visits.

Using SHARP context propagation, the agent retrieves FHIR resources including Patient, Condition, MedicationRequest, Observation, Encounter, Procedure, DiagnosticReport, and AllergyIntolerance. It applies generative AI to reason about compound risks, temporal trends, and follow-up gaps that rule-based clinical decision support systems cannot detect.

SafeSignal does not diagnose, prescribe, or submit orders. Every finding includes supporting FHIR evidence and a clear statement of what evidence is missing, ensuring clinicians can make informed decisions.

### Built With

- Python
- FastAPI
- FHIR R4
- Prompt Opinion Platform
- A2A Protocol
- MCP (Model Context Protocol)
- SHARP Extension Specs
- [LLM name — Claude/GPT-4.1/Gemini]

### Category

- Agent (A2A) AND Superpower (MCP)

### Try It Out

[Link to Prompt Opinion marketplace listing]

### Demo Video

[Link to demo video — under 3 minutes]

### GitHub

[Link to repository]

---

## 18. Team Task Split

### 3-Person Team

**Person 1: Agent and Platform Integration**

Responsibilities:
- Set up Prompt Opinion project and agent
- Configure agent card and marketplace listing
- Set up A2A endpoint (FastAPI)
- Set up MCP server
- Handle SHARP context extraction
- Publish to marketplace
- Troubleshoot platform-specific issues
- Record the platform integration portions of the demo

**Person 2: FHIR and Clinical Logic**

Responsibilities:
- Implement FHIR client (all resource type fetchers)
- Build the clinical context normalizer
- Create and load the synthetic Margaret Chen patient data
- Implement the 4 MCP tool functions
- Handle edge cases (missing data, empty results, malformed FHIR)
- Validate clinical accuracy of output with available medical references

**Person 3: AI Prompts, Demo, and Submission**

Responsibilities:
- Write and iterate on all LLM prompts (system prompt + per-tool prompts)
- Design the output format (risk briefing structure)
- Write the demo script
- Create the Devpost submission
- Record and edit the demo video
- Create any supporting visuals (architecture diagram, etc.)
- Quality-check the final risk briefing output for clinical plausibility

### 2-Person Team

Combine Person 1 and Person 3. The platform integration and demo/submission work can be done by one person, with prompt engineering happening in parallel with platform setup.

### Solo Builder

Prioritize in this order:
1. A2A agent running on Prompt Opinion (Day 1)
2. FHIR data retrieval + synthetic patient (Day 2)
3. `generate_risk_briefing` tool only — skip individual tool exposure (Day 3)
4. Publish + polish (Day 4)
5. Record + submit (Day 5)

If solo, skip the MCP server and build A2A only. Mention MCP as "planned infrastructure" in the submission.

---

## 19. Compliance and Safety Guardrails

### Language Rules

**Always use:**
- "Warrants clinician review"
- "Consider evaluating"
- "This combination may pose risk"
- "For clinician assessment"
- "Possible safety concern based on available data"
- "Evidence suggests" / "Evidence is absent for"

**Never use:**
- "The patient has [diagnosis]" (beyond what's in the Condition list)
- "Stop this medication"
- "Start [treatment]"
- "This is dangerous" (say "this warrants urgent review")
- "The doctor made an error"
- "This is malpractice"
- Any language implying the agent has made a clinical decision

### Output Guardrails

Every risk briefing must end with:

```
⚕️  COMPLIANCE NOTE
All findings are for clinician review only. SafeSignal does not diagnose,
prescribe, or make treatment recommendations. Final clinical decisions must
be made by the treating provider based on their direct assessment of the
patient. SafeSignal surfaces patterns in existing chart data — it does not
generate new clinical information.
```

### Technical Safety

- Agent is stateless — no patient data is stored after the request completes
- All FHIR access uses the platform-provided token (no hardcoded credentials)
- Agent logs no PHI
- Output includes only data already present in the patient's chart (no external data retrieval for clinical content)

---

## 20. Advanced Features (Post-MVP)

Only consider these after MVP is working and demo is recorded.

### Feature 1: Panel-Level Screening

Allow a care coordinator to run SafeSignal across an entire patient panel (e.g., "scan all patients with diabetes and CKD for medication safety issues"). Uses FHIR Group resource or batch queries.

### Feature 2: Specialty-Specific Risk Profiles

| Specialty | Additional Patterns |
|---|---|
| Cardiology | Anticoagulation monitoring, heart failure decompensation signs, dual antiplatelet duration |
| Oncology | Chemotherapy lab monitoring, tumor marker trends |
| Pediatrics (CHOP relevance) | Growth trajectory, vaccination gaps, developmental screening follow-up |
| Nephrology | CKD progression staging, dialysis preparation timing |
| Geriatrics | Polypharmacy risk, fall risk medication combinations, Beers criteria |

### Feature 3: Multi-Agent Composition Demo

Show SafeSignal being called by another agent in the Prompt Opinion ecosystem. For example, a "Visit Prep Agent" that combines scheduling information with SafeSignal's risk briefing and a medication reconciliation agent's output.

### Feature 4: Risk Score

Assign a numerical risk score (0-100) to each patient based on the number and severity of findings. Enables prioritization when scanning a panel.

### Feature 5: Temporal Alerting

"Alert me if this patient's eGFR drops below 25 at their next lab draw." Not real-time monitoring, but setting conditions that the agent checks on subsequent invocations.

---

## 21. Competitive Differentiation

### vs. Other Hackathon Submissions

| What most teams will build | How SafeSignal is different |
|---|---|
| Single A2A agent that does one thing | Both MCP + A2A working together |
| Clinical chatbot or symptom checker | Analyzes existing chart data, not patient-reported symptoms |
| Drug interaction checker (pairwise) | Compound risk across meds + labs + conditions + time |
| Note summarizer | Finds what's MISSING and what's TRENDING, not what's documented |
| Image-based diagnosis | No diagnostic claims, no regulatory risk, no validation burden |
| Generic alert system | Focuses on connections between data silos, not single-value thresholds |
| Billing/coding tool | Patient safety framing, not revenue optimization |

### vs. Existing Clinical Decision Support

| Existing CDS | SafeSignal's Gap-Fill |
|---|---|
| Pharmacy systems check drug-drug interactions at time of prescribing | SafeSignal checks drug-LAB interactions AFTER prescribing, when labs change |
| EHR alerts fire on single abnormal values | SafeSignal reasons about trends across multiple values over time |
| Quality dashboards check screening compliance | SafeSignal checks whether ABNORMAL screenings got follow-up |
| CDS rules are static and pairwise | SafeSignal uses generative AI for compound and contextual reasoning |
| CDS fires at the point of order entry | SafeSignal reviews the chart BEFORE the visit, enabling proactive intervention |

### The Architectural Differentiator

No other team will build both MCP and A2A. This is the strongest structural differentiator because:

1. It directly demonstrates the hackathon's thesis (collaboration, interoperability, composability)
2. It makes the judges imagine a future ecosystem where these tools are reused by many agents
3. It shows technical sophistication without requiring complex infrastructure
4. It is the exact story Prompt Opinion wants to tell about their platform

---

## 22. Risk Mitigation

### Risk 1: Building Both Tracks Overextends the Team

**Mitigation:** The MCP tools are lightweight — each is a FHIR fetch + LLM call. They don't need complex logic. The A2A agent orchestrates the same tool functions internally. The incremental work to expose them as MCP tools is small once the core logic exists.

**Fallback:** If time runs short, ship the A2A agent with the tools built-in (not exposed as MCP). Mention MCP as "infrastructure-ready" in the submission. The A2A agent alone is still a strong entry.

### Risk 2: Prompt Opinion MCP Integration Is Difficult

**Mitigation:** Check this on Day 1. Read the MCP documentation thoroughly. If the platform makes MCP exposure hard, fall back to A2A-only.

**Fallback:** Same as above — A2A-only with MCP mentioned as architecture direction.

### Risk 3: LLM Output Quality Is Inconsistent

**Mitigation:** Test the prompts extensively against the synthetic patient on Day 2-3. Use structured output formatting (JSON schema) to constrain the LLM. Add post-processing to validate that every cited resource ID actually exists in the data.

**Fallback:** If the LLM is unreliable on complex compound reasoning, simplify to just the medication safety module (Tool 1), which has the most constrained and predictable output.

### Risk 4: FHIR Sandbox Is Unreliable

**Mitigation:** Pre-load synthetic data into the FHIR sandbox on Day 1. Test connectivity. Have a local mock FHIR server as backup (a simple FastAPI app returning the Margaret Chen JSON).

**Fallback:** Use a local mock FHIR server for the demo. State in the submission that the agent connects to any FHIR R4 endpoint.

### Risk 5: Demo Video Is Not Compelling

**Mitigation:** Script it (Section 16). Practice it. Record it early on Day 5, leaving time for a second take. Keep it simple — screen recording with voiceover. No fancy transitions needed.

**Fallback:** If the live demo has glitches, show the output as a prepared example and explain the architecture. The architecture story (both tracks, composable tools, FHIR-aware) carries weight even without a flawless live run.

---

## 23. Reference Links

### Hackathon

- Hackathon Page: https://devpost.com/hackathons (find Agents Assemble)
- Prompt Opinion Platform: [registration link from hackathon page]
- Getting Started Video: https://youtu.be/Qvs_QK4meHc

### Standards and Protocols

- FHIR R4 Specification: https://hl7.org/fhir/R4/
- FHIR Patient Resource: https://hl7.org/fhir/R4/patient.html
- FHIR Observation Resource: https://hl7.org/fhir/R4/observation.html
- FHIR MedicationRequest Resource: https://hl7.org/fhir/R4/medicationrequest.html
- FHIR Condition Resource: https://hl7.org/fhir/R4/condition.html
- Model Context Protocol (MCP): https://modelcontextprotocol.io/
- A2A Protocol: https://google.github.io/A2A/

### Clinical References

- Institute of Medicine — To Err Is Human (medical error statistics)
- FDA 21st Century Cures Act, Section 3060 (CDS software exemption)
- AMA EHR burnout data: https://www.ama-assn.org/practice-management/digital-health
- CMS E/M Documentation: https://www.cms.gov/files/document/mln006764-evaluation-management-services.pdf

### Development Resources

- HAPI FHIR Public Sandbox: https://hapi.fhir.org/baseR4
- Synthea Patient Generator: https://github.com/synthetichealth/synthea
- SMART on FHIR Launch: https://launch.smarthealthit.org

---

## Final Note

This document is the complete blueprint. Follow the build plan. Trust the demo script. Ship the MVP. The idea is strong, the architecture is unique, and the demo case tells a story that clinician judges will recognize from their own practice.

The risks are in the chart. Help them find it.
