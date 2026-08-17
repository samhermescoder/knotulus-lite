# Knotulus Lite — SPEC.md (real product, simplified for hackathon)

## Problem
Investors drown in inbound decks and spend the first meeting re-discovering basic
fit. Knotulus screens between deck intake and the partner interview — but the
"learning" (using past decisions to sharpen future ranking) is early and
unvalidated. This hackathon build proves the **investor memory layer** concept as
a working, interpretable ADK fleet on Google Cloud.

## What we're building (simplified Knotulus)
A small **agent fleet** that runs the Knotulus screening loop + a working
**investor memory layer**, built open on ADK + Gemini 3.5 Flash + minimal GCP.

### Agents (the fleet)
| Agent | Job | Fleet primitive |
|-------|-----|-----------------|
| `IntakeAgent` | Read pitch email, extract company + ask, classify fit | Gateway + Model Armor (PII strip) |
| `AssessmentAgent` | Generate short behavioral assessment from deck signals | — |
| `ProfileAgent` | Build behavioral profile from responses + deck signals | — |
| `RankingAgent` | Rank shortlist, personalized via Memory Agent | Memory Bank (read) |
| `BriefAgent` | Write pre-meeting brief + reasoning trace | Observability (write trace) |
| `MemoryAgent` | Persist decisions (met/passed/signal-value) across sessions | **Memory Bank (write)** |

### Fortified Enterprise Fleet primitives (all covered)
- **Agent Registry** — `registry.json` + `/registry` (publish/version/discover)
- **Agent Runtime** — ADK long-running async pipeline on Cloud Run
- **Memory Bank** — `memory/*.json` (investor memory layer) + Firestore mirror
- **Agent Identity** — investor vs founder roles + scoped API keys
- **Agent Gateway** — `POST /pitch` single router, policy-enforced
- **Model Armor** — PII strip + founder free-text injection guard
- **Agent Observability** — `traces/<pitch>.md` readable reasoning chain

## Success criteria
- [ ] Runs on Gemini 3.5 Flash via Vertex AI / Gemini API
- [ ] Built with Google ADK
- [ ] Deployed on ≥1 GCP service (Cloud Run + Firestore)
- [ ] All 7 Fleet primitives demonstrably present
- [ ] Investor memory layer actually persists + influences a later ranking
- [ ] Live demo video: pitch → ranked brief + trace; memory changes a future rank
- [ ] Submitted before Sep 1 2026 08:00 GMT+8

## Non-goals (honest scope)
- NOT a finished learning engine — simplified, demonstrable memory layer only
- NOT production multi-tenant / real Gmail integration (use a pitch-submit API or sample inbox)
- NOT rebuilding full Knotulus (knotty, screening-core) — analog slice only
- No paid GEAP managed services required

## Interfaces
- `POST /pitch` — submit a pitch (email text / deck signals) → async pipeline
- `GET /shortlist` — ranked shortlist + briefs
- `GET /registry` — list registered agents + versions
- `GET /memory` — inspect investor memory (decisions, passes, signal value)
- `GET /traces/<pitch_id>` — read the reasoning chain (observability)

## Data model (simplified)
- `memory/investor.json` — preferences, passes, valued signals
- `memory/decisions.json` — per-pitch: met/passed + which signals fired
- `registry.json` — agent catalog (id, version, capabilities, endpoint)
- `traces/<pitch_id>.md` — readable reasoning chain
