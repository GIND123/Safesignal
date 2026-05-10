# SafeSignal — Demo Video Script
**Target runtime: 2:45 — 3:00**
**Patient: Samuel Brooks, 67M — loaded in Prompt Opinion with FHIR context active**
**Recording tool: OBS / Loom / QuickTime**

---

## Before You Hit Record

**Setup checklist:**
- [ ] Samuel Brooks loaded to FHIR sandbox (`python scripts/load_synthetic_patient.py --case samuel_brooks_extreme`)
- [ ] Both servers running (`honcho start` — A2A on 8004, MCP on 8005)
- [ ] Samuel Brooks open in Prompt Opinion with FHIR context active (you should see his name and DOB in the header)
- [ ] SafeSignal agent connected and showing green status
- [ ] Screen resolution: 1920×1080, browser zoom at 90% so the full SafeSignal output is visible
- [ ] Microphone tested, background noise eliminated
- [ ] Close all notifications

**Tone:** Clinical, urgent, confident. You are showing a real problem with a real solution. Not a demo. A capability.

---

## The Patient Story

Samuel Brooks is 67 years old. He has heart failure, Type 2 diabetes, chronic kidney disease, and atrial fibrillation. He has been a patient for years. His medications have been "stable." His most recent office visit note, from April 28, 2026, says: **"CHF and CKD appear stable on current regimen. Continue metformin, lisinopril, spironolactone, and warfarin. Recheck labs next month."**

The labs from that same day tell a different story:
- eGFR: **18** (was 38 ten months ago — a 53% decline)
- Potassium: **6.2** mmol/L (critically high)
- INR: **4.8** (critically elevated, bleeding risk)
- HbA1c: **9.1%** (rising despite treatment)
- Blood pressure: **166/96** (rising despite two antihypertensives)

Thirteen days before this visit, urgent care added **Ibuprofen** for knee pain. That provider had no idea his eGFR was 18, his INR was elevated, or that he was already on a potassium-sparing diuretic. No one connected the dots.

That is Samuel's story. SafeSignal tells it in under 35 seconds.

---

## Question 1 — The Opening (0:00 – 0:45)

### What to say before typing

> "Samuel Brooks is 67. Heart failure, diabetes, kidney disease, atrial fibrillation. His last office note said 'stable.' The labs from that same day said something else entirely."
>
> "SafeSignal reads his full FHIR chart — medications, labs, conditions, encounters, every referral — and tells his clinician what they need to know before they walk into the room."

### Type exactly this into SafeSignal:

```
What should I know before seeing Samuel today?
```

### What appears (let it load — ~15–25 seconds)

The full risk briefing: **6 URGENT findings, 4 WARNING findings, 1 INFORMATIONAL** (FOBT resolved). Total: 11 findings.

### What to say as the briefing appears

> "Eleven findings. In a chart his doctor called routine follow-up."
>
> "Six are URGENT. Let me show you what they are."

### Key moment to point out on screen

**The contradiction:** Find the finding that says *"The recent encounter note stating 'CKD appear stable on current regimen' directly contradicts the rapid eGFR decline."* Point at it.

> "The AI read the doctor's own note — and told us the note is wrong."

---

## Question 2 — The Medication Crisis (0:45 – 1:20)

### What to say before typing

> "SafeSignal doesn't cite its own knowledge. It cites the FDA. Here's what that looks like."

### Type exactly this into SafeSignal:

```
Is it safe to keep him on his current medications given his latest labs?
```

### What appears (~20 seconds)

`check_medication_safety` fires — **6 URGENT findings**, each with a clean Evidence block and FDA/NLM Citation block.

### What to say as the findings appear — narrate these three:

**Finding 1 — Metformin:**
> "Metformin. Prescribed three years ago. Safe at the time. His kidney function has since dropped to 18 — below the FDA contraindication threshold. Here is the exact FDA language: 'Severe renal impairment: eGFR below 30 — contraindicated.' That is not SafeSignal's opinion. That is the FDA label."

**Finding 2 — Spironolactone + hyperkalemia:**
> "His potassium is 6.2. Spironolactone is a potassium-sparing diuretic. The FDA says: 'Spironolactone is contraindicated in patients with hyperkalemia.' He is on it right now."

**Finding 3 — Ibuprofen + Warfarin (the urgent care story):**
> "Thirteen days ago, urgent care added ibuprofen for knee pain. That provider didn't know his INR was elevated or that he was on warfarin. The FDA drug interactions label for ibuprofen calls it out directly: 'take a blood thinning anticoagulant... are age 60 or older.' Samuel is 67. His INR is 4.8. This is compound risk from two providers who never saw each other's context."

---

## Question 3 — The Silent Decline (1:20 – 1:50)

### What to say before typing

> "Rule-based CDS can flag a single abnormal value. It cannot tell you that a value has been declining for ten months while every note said stable. SafeSignal can."

### Type exactly this into SafeSignal:

```
Has his kidney function been getting worse over time, and should I be worried?
```

### What appears (~15 seconds)

`detect_silent_deterioration` fires — clean deterioration findings with explicit trajectories and rates.

### What to say as the findings appear

> "eGFR: 38 in June 2025. 18 in April 2026. Ten months. A rate of minus 2 per month. The trajectory points toward end-stage renal disease."
>
> "And here — the finding that a rule-based system cannot produce — SafeSignal flagged that the doctor's note from the same day as the worst labs said 'CKD appears stable.' The objective data says otherwise. SafeSignal says so explicitly."
>
> "This is the discrepancy between what the chart says and what the data shows. No rule can write that sentence. Generative AI can."

---

## Question 4 — The Follow-Up Gaps (1:50 – 2:20)

### What to say before typing

> "SafeSignal is not just an alarm system. It checks its work. Before flagging anything as a gap, it searches encounters, procedures, and referrals. If follow-up was done — it says so."

### Type exactly this into SafeSignal:

```
Are there any test results in Samuel's chart that were never properly followed up on?
```

### What appears (~15 seconds)

`find_lost_followups` fires — **2 WARNING findings** (INR and HbA1c gaps), **1 INFORMATIONAL resolved item** (FOBT).

### What to say as the findings appear

**On the FOBT resolved item (scroll to it):**
> "Samuel had a positive fecal occult blood test in January. SafeSignal searched encounters, procedures, and referrals. It found the colonoscopy — completed February third. It reports that as resolved. No gap."
>
> "That matters. A system that only raises alarms is not trustworthy. SafeSignal tells you what WAS followed up, not just what wasn't."

**On the INR gap:**
> "But here — INR was 3.4 in February. The April visit note just said 'continue warfarin.' No documented review of that elevated value. No dose adjustment. SafeSignal found the gap between the result and the response."

---

## Question 5 — The Reusability Close (2:20 – 2:50)

### What to say before typing

> "Everything you've seen comes from a single MCP server. Four tools — medication safety, deterioration detection, follow-up gap detection, full risk briefing. Any agent on this platform can call them. A scheduling agent before confirming a refill. A care coordination agent reviewing a patient panel. A triage agent routing an urgent visit. We didn't just build a solution for one problem. We built infrastructure that makes every agent on this platform smarter."

### Type exactly this into SafeSignal:

```
Give me the exact FDA language I should cite when I talk to Samuel today about stopping his metformin and ibuprofen.
```

### What appears (~20 seconds)

`check_medication_safety` fires — FDA Black Box Warning text quoted verbatim for both drugs.

### What to say as the output appears

> "The clinician walks into the room with this. Not a vague alert. The exact FDA regulatory language, tied to the exact FHIR resource IDs from Samuel's chart."
>
> "The data was always there. The medications, the labs, the notes, the referrals — all of it in the EHR. SafeSignal connected the dots."

---

## Closing (2:50 – 3:00)

### Do not type anything. Face camera or use voiceover.

> "Samuel Brooks is synthetic. His story is not."
>
> "These patterns — the declining kidneys, the medications that became dangerous, the doctor's note that contradicted the labs — they exist in real patient charts right now."
>
> "SafeSignal. The risks are in the chart. We help you find them."

---

## Editing Notes

| Timestamp | Edit |
|---|---|
| 0:00 | Start recording. Show Samuel Brooks open in Prompt Opinion — name visible in header. |
| 0:10 | Begin narration of his story before typing Q1. |
| 0:30 | Type Q1. Let the briefing load fully before narrating — don't talk over the loading. |
| 0:55 | Type Q2. Zoom in slightly on the Evidence blocks and FDA/NLM Citation sections as you narrate. |
| 1:22 | Type Q3. Highlight the "stable note contradiction" finding on screen — hover or circle it. |
| 1:52 | Type Q4. Scroll to show both the RESOLVED FOBT (green ✓) and the WARNING INR gap. |
| 2:22 | Type Q5. Final FDA text appears. Let it sit for 3 seconds before closing narration. |
| 2:50 | Closing voiceover. Optional: fade to SafeSignal logo / title card. |

---

## Backup Plan (if network is slow)

If SafeSignal takes > 30 seconds to respond during recording:
- Keep talking — narrate what you expect to appear while it loads
- Say: "SafeSignal is fetching live FHIR data, enriching each medication with the FDA drug label API and NLM interaction database, and reasoning across 24 months of observations — this takes about 30 seconds."
- This turns a loading wait into a feature explanation

---

## What NOT to Say

- Do NOT say "AI detected" — say "SafeSignal found"
- Do NOT say "the system thinks" — say "the data shows"
- Do NOT say "it recommends stopping the medication" — say "it warrants clinician review"
- Do NOT say "this would save lives" — let the judges draw that conclusion
- Do NOT apologise for loading time — narrate through it
