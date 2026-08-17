# Knotulus Lite

**Track:** Fortified Enterprise Fleet — All Things Agentic Hackathon 2026
**Stack:** Google ADK · Gemini 3.5 Flash · Cloud Run · Firestore
**Deadline:** Sep 1, 2026 · 08:00 GMT+8

## What it is
A simplified, **open and interpretable** reimplementation of **Knotulus** — the
investor screening layer between deck intake and the partner interview — built as
a Google ADK agent fleet. Where Google's Gemini Enterprise Agent Platform keeps
registry, memory, and reasoning inside managed black boxes, Knotulus Lite stores
them as **human-readable files**, proving the same Fortified Enterprise Fleet
primitives can be built cheaply on ADK + Gemini + minimal GCP.

Knotulus's long-term vision is an **investor memory layer** — it remembers what
investors value, why they passed, and which signals predicted a good conversation.
Knotulus Lite makes that memory layer *work*, demonstrably, in simplified form.

## The screening loop (fleet of 6 agents)
Pitch lands → **Intake** reads + classifies → **Assessment** invites founder →
**Profile** builds behavioral profile → **Ranking** ranks shortlist (using Memory)
→ **Brief** writes pre-meeting brief + reasoning trace → **Memory** persists the
decision so the next pitch is ranked smarter.

## Fortified Enterprise Fleet primitives (all covered)
- **Agent Registry** — `registry.json` + `/registry`
- **Agent Runtime** — ADK async pipeline on Cloud Run
- **Memory Bank** — `memory/*.json` investor memory layer (+ Firestore)
- **Agent Identity** — investor vs founder roles + scoped keys
- **Agent Gateway** — `POST /pitch` router + policy
- **Model Armor** — PII strip + injection guard
- **Observability** — `traces/<pitch>.md` readable reasoning chain

## Flagship demo
The **investor memory layer**: a past "pass" lives in Memory; a new similar pitch
is ranked lower, and the reasoning trace explains *why*. Learning, made visible.

## Run
```bash
adk web .                                 # local agent UI
gcloud run deploy knotulus-lite --source . --region us-central1   # deploy
pytest tests/                             # tests
```

## Why it wins
Transparent by design. A judge opens `traces/<pitch>.md` and reads exactly what the
agent knew and why it acted — the "Interpretable" edge, and the strongest answer to
the Fleet track's auditability requirement.
