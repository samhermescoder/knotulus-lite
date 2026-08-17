# Knotulus Lite — Track Analysis & Technique

## What Knotulus actually is (the product we're simplifying)
A **screening layer between investor deck intake and the partner interview**:
1. A pitch email lands → read + classify (company + ask)
2. Founder is invited to a short **behavioral assessment**
3. A **behavioral profile** is built from responses + signals already in the deck
4. The shortlist is **ranked**
5. A **pre-meeting brief** is written
Long-term vision = an **investor memory layer**: learns from decisions investors
make (and eventually meetings) — remembers what they value, why they passed,
which signals predicted a good conversation. Today it's a dev-mode prototype; the
learning engine is early/validating, not finished.

## The three tracks (from devpost)
1. **Taskmaster** — one event-driven workflow that takes action end-to-end.
2. **Collaborative Partner** — stateful, RAG-backed tutor/co-pilot that adapts.
3. **Fortified Enterprise Fleet** — multi-agent discovery, orchestration at scale,
   long-term state, observability, security. Maps to Google's GEAP primitives.

## Why Fortified Enterprise Fleet is the best fit
Knotulus's real architecture is a **fleet of agents** around a **persistent memory
layer** — exactly the Fleet spec. The investor memory layer = Memory Bank; the
"why we ranked / why we passed" brief = Observability; founder/investor access =
Identity; intake routing = Gateway; PII in decks = Model Armor; the agent catalog
= Registry. Taskmaster would only capture step 1→5 (one workflow); it would miss
the memory/observability differentiator that IS the product's vision.

### Primitive mapping (the technique)
| GEAP primitive (managed) | Knotulus-lite open analog | Knotulus source |
|---|---|---|
| Agent Registry | `registry.json` + `/registry` route | catalog of the 6 agents |
| Agent Runtime (async) | ADK long-running agent on Cloud Run | background pitch pipeline |
| Memory Bank | `memory/*.json` (+ Firestore) | **investor memory layer** |
| Agent Identity | investor vs founder roles + scoped keys | zero-trust access |
| Agent Gateway | `POST /pitch` router + policy | unified intake |
| Model Armor | PII strip + injection guard | protect deck/founder text |
| Agent Observability | `traces/<pitch>.md` reasoning log | audit "why ranked X" |

## Required-tech coverage (mandatory for every track)
- [x] **Gemini 3.5 Flash** (or newer) via Gemini API / Vertex AI — model
- [x] **Google ADK** (or GenAI SDK / GenKit) — agent framework
- [x] **Google Cloud** — Cloud Run (host, scales-to-zero) + Firestore (registry/memory)

## Build technique (how we make it work, cheaply, in 14 days)
1. **ADK multi-agent fleet** (6 agents, see SPEC.md): Intake → Assessment →
   Profile → Ranking → Brief → Memory. One orchestrator routes a pitch through them.
2. **Gemini 3.5 Flash** for all inference (cheap; reserve Pro only if needed).
3. **Cloud Run** host, min-instances=0 → near-zero idle cost; pitch pipeline runs async.
4. **Firestore** for registry + memory persistence (satisfies GCP requirement);
   **mirror to readable files** so the "interpretable" story holds.
5. **Investor memory layer (flagship):** Memory Agent persists each decision
   (met / passed / signal-value) in `memory/`. Ranking Agent personalizes using
   it — "remembers what this investor values, why they passed." This is the
   long-term vision, demonstrable in simplified form.
6. **Observability as markdown:** every pitch appends a reasoning trace a judge
   can literally read — classification → profile → ranking rationale → brief.
7. **Model Armor:** strip PII before any memory write; guard founder free-text
   against prompt injection.

## The demo narrative (3-min video)
- Pitch email arrives at `POST /pitch` → agents run in background → ranked
  shortlist + pre-meeting brief appears, with a readable reasoning trace.
- Then: a past "pass" is in Memory; a new similar pitch is ranked lower with the
  trace explaining *why* — the learning/memory layer, live.
- `GET /registry` shows the discoverable agent fleet; `GET /memory` shows the
  investor memory; `GET /traces` shows auditability.

## Alternative: Taskmaster framing
If we want a leaner, tighter demo, we can submit under **Taskmaster** and present
the screening pipeline (steps 1→5) as the single autonomous workflow, while still
keeping the memory layer + traces as the differentiator. **Recommendation: submit
under Fleet** — the memory layer is the product's soul and maps to the most
defensible, distinctive Fleet primitives (Memory Bank + Observability).
