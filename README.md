# Knotulus Lite

**A simplified, open, interpretable reimplementation of Knotulus's investor-screening
layer — built as a Google ADK + Gemini 3.5 Flash agent fleet for the
All Things Agentic Hackathon 2026 (Fortified Enterprise Fleet track).**

This README is written so *anyone* can clone the repo and run it end-to-end without
prior context. No Google Cloud account or API key is required to see the whole system
work — it runs fully offline in "mock mode."

---

## 1. What this actually is (in plain English)

Investors get flooded with pitches. Knotulus sits between a pitch landing in the inbox
and the partner meeting, and does the first-pass screening **with a memory of what
this investor actually values**.

Knotulus Lite reproduces that as a small **fleet of 6 agents**:

1. **Intake** — reads the pitch, strips personal data (PII), classifies company / ask / sector / fit.
2. **Assessment** — drafts behavioral questions for the founder.
3. **Profile** — builds a behavioral profile from founder responses.
4. **Ranking** — ranks the opportunity, *personalized by the investor's memory*.
5. **Brief** — writes a pre-meeting brief + a readable reasoning trace.
6. **Memory** — records the investor's decision so the next pitch is ranked smarter.

The differentiator — and the part that maps to the hackathon's "Fortified Enterprise
Fleet" track — is the **investor memory layer**, built as a **walkable evidence graph**
(port of the real Knotulus/knotty evidence model):

- **Sources** = first-hand artifacts (a pitch email, a deck, an interview note). Immutable.
- **Claims** = extracted facts / scores / asks / preferences / feedback that **cite ≥1 source**.
  This is the *only* unit the ranking may consume — raw text never flows into a score.
- **Bundles** = a per-investor compiled snapshot (the cheap view the ranking reads),
  with a **scope wall** so one investor's claims never leak into another's.

You can literally open `memory/evidence-graph.json` and read *why* a pitch was ranked
the way it was, and trace any claim back to the artifact that backs it.

---

## 2. Quick start (zero credentials — mock mode)

```bash
cd knotulus-lite

# 1. Create the venv (Python 3.11+)
uv venv .venv
. .venv/Scripts/activate          # (Windows)  — or: source .venv/bin/activate on Mac/Linux

# 2. Install deps
uv pip install -e ".[dev,adk]"     # (or: pip install -e ".[dev,adk]")

# 3. Run the test suite — proves the fleet + evidence graph work
bash run-tests.sh                  # → 9 passed

# 4. Run one screening end-to-end (prints classification → ranking → brief → trace)
bash run.sh src/orchestrator.py

# 5. Start the web dashboard (the "after interview" decision portal)
bash run.sh -m src.gateway
#   → open http://localhost:8080
```

> **Why `bash run.sh`?** The project lives in a `src/` package. The launcher clears a
> leaked `PYTHONPATH` and puts `src` on the path so every entry point resolves. If you
> prefer raw commands, prefix with `env -u PYTHONPATH KNOTULUS_ROOT="$PWD"`.

### Using the dashboard (http://localhost:8080)
- **Screen a pitch** — paste a pitch, hit *Run fleet*. You get a score, the extracted
  signals, the memory rationale, and a link to the readable trace.
- **Seed sample memory** — loads a prior "pass" so you can see memory shift a later rank.
- **Record decision** — after screening, save a meet/pass + which *signals* drove it.
  This writes a citable evidence claim.
- **Post-interview** — the "after" loop: record good/neutral/bad + which signals fired.
  The next ranking walks this.
- **Evidence graph** — a live SVG of sources → claims (cited-by edges). The audit trail.
- **Investor memory** — the file-backed `memory/investor.json`.

### Or drive it from the terminal / curl
```bash
curl -s -X POST localhost:8080/pitch -H 'content-type: application/json' \
  -d '{"text":"We are building NeuroCo, an AI radiology triage platform. Raising $2M seed."}'

curl -s -X POST localhost:8080/interview -H 'content-type: application/json' \
  -d '{"pitch_id":"<from the /pitch response>","outcome":"good","signals":["technical moat"]}'

curl -s localhost:8080/evidence      # the walkable graph
curl -s "localhost:8080/bundle?investor=default"   # per-investor snapshot
```

---

## 3. What's real vs. what's mocked (be honest about this)

| Piece | Status | Notes |
|-------|--------|-------|
| Evidence graph (sources/claims/bundles + walk + scope wall) | **REAL** | Runs offline, file-backed, tested. This is the actual memory engine. |
| Ranking that walks the evidence graph | **REAL** | Verified: a signal the investor rejected drops a future pitch's score. |
| Agent fleet orchestration (6 agents) | **REAL** | `orchestrator.py` runs them in order; ADK graph runs via `InMemoryRunner`. |
| API gateway (FastAPI) | **REAL** | `/pitch`, `/decision`, `/interview`, `/evidence`, `/bundle`, `/memory`, `/registry`, `/traces`, `/health`. |
| **Intake classification (`classify_fit`)** | **MOCKED** | Heuristic keyword extraction (company/ask/sector/fit/signals). This is the *only* mocked stage. Swap to Gemini later by flipping `ENABLE_GEMINI=true` — no other code changes. |
| Gemini 3.5 Flash inference (real mode) | **Wired, not run here** | Code path exists (Vertex AI + ADC, and a Gemini API-key fallback). Requires a GCP project + billing to execute from this machine (see §5). |
| Cloud Run deployment | **Deploy-ready, not deployed** | `Dockerfile` + `deploy.sh` are correct; deploying needs a billing account. |

**Bottom line:** everything except the Intake classifier and the live LLM call is real
and demonstrable offline. The mock Intake is a stand-in for the real Gemini extractor —
the rest of the pipeline consumes its *output*, so swapping Intake to Gemini later
doesn't touch the evidence graph, ranking, or dashboard.

---

## 4. APIs / endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/pitch` | Run the full fleet on a pitch text → ranked shortlist + brief + trace |
| POST | `/decision` | Record meet/pass + signals → writes a citable feedback claim |
| POST | `/interview` | Post-interview capture (good/neutral/bad + signals) → evidence claim |
| GET | `/evidence` | The walkable evidence graph (nodes + edges) |
| GET | `/bundle?investor=default` | Per-investor compiled snapshot (scope wall applied) |
| GET | `/memory` | `memory/investor.json` (sector pass/meet history) |
| GET | `/registry` | The 6-agent Agent Registry (Fleet primitive) |
| GET | `/traces/{pitch_id}` | Readable reasoning chain (Observability) |
| POST | `/seed` | Load a prior PASS so memory is visible |
| GET | `/health` | `{"mode": "mock" | "gemini"}` |
| GET | `/` | The decision dashboard (HTML) |

### Are we missing an API?
For a *complete* submission the following are optional but would strengthen it:
- **`GET /shortlist`** — a standalone ranked-shortlist view (today it's returned inside `/pitch`; not a separate GET).
- **`GET /claims/{id}`** and **`GET /sources/{id}`** — direct provenance lookups
  (today you get the whole graph via `/evidence` and walk it client-side).
- **Auth / Agent Identity** — the spec lists "investor vs founder roles + scoped keys"
  as a primitive; today the gateway is open (no auth). Fine for a demo, but a judge
  auditing the Fleet track may look for it.
- **Firestore mirror** — optional secondary GCP store (code present in `memory.py`,
  off by default; needs billing).
- **ADK `adk web` UI** — the repo references `adk web .` in older docs; the runnable
  ADK path is `src/agents/adk_agents.py` (offline `InMemoryRunner`). Align docs if a
  judge runs it.

---

## 5. Real mode (Gemini 3.5 Flash via Vertex AI) — needs GCP

Mock mode needs nothing. To use the real LLM:

1. Install gcloud: `winget install --id Google.CloudSDK` (or the macOS/Linux installer).
2. `gcloud auth application-default login` — opens a browser; **no API key needed** (ADC).
3. `cp .env.example .env` and set:
   ```
   ENABLE_GEMINI=true
   GOOGLE_CLOUD_PROJECT=<your-project-id>
   GOOGLE_CLOUD_LOCATION=us-central1
   GEMINI_MODEL=gemini-3.5-flash
   ```
4. Re-run `bash run-tests.sh` and `bash run.sh src/orchestrator.py`.

> **Two real-world constraints we hit (so you don't repeat them):**
> - A **Gemini Developer API key** path exists in code but is **geo-blocked from Hong
>   Kong** (`FAILED_PRECONDITION`) — unusable from this machine. Vertex AI + ADC is the
>   working path.
> - **Cloud Run deploy requires a billing account** on the GCP project. The project
>   used here has none attached, so the deploy step is left as deploy-ready code, not a
>   live URL. If a judge requires a live URL, attach billing and run `bash deploy.sh`.

---

## 6. How this fits the hackathon submission

- **Track:** Fortified Enterprise Fleet (All Things Agentic Hackathon 2026).
- **Deadline:** Sep 1, 2026 · 08:00 GMT+8.
- **Mandatory tech coverage:**
  - ✅ **Gemini 3.5 Flash** — wired (Vertex AI + ADC); runs in real mode with a GCP project.
  - ✅ **Google ADK** — the fleet is a real `SequentialAgent` graph that executes via
    `InMemoryRunner` (offline test proves it).
  - ✅ **Google Cloud** — Cloud Run + (optional) Firestore. Deploy-ready; live deploy
    needs billing (see §5).
- **All 7 Fleet primitives demonstrated:**
  Registry (`/registry`), Runtime (ADK pipeline), Memory Bank (`memory/` + evidence
  graph), Identity (roles defined; auth not enforced — see §4), Gateway (`/pitch`),
  Model Armor (PII strip in `model.screen_pii`), Observability (`traces/`).
- **The story to tell judges:** "Transparent by design." A judge opens
  `memory/evidence-graph.json` (or the dashboard graph) and reads exactly *why* a pitch
  was ranked the way it was, and traces any claim to the artifact that backs it. The
  investor memory layer is real, walkable, and auditable — not a black box.

### Submission checklist
- [ ] Repo public + this README + `TRACK-ANALYSIS.md` + `docs/adr/`
- [ ] Demo video: pitch → ranked brief + trace; memory drops a future rank; evidence graph
- [ ] Architecture diagram (the 6-agent fleet + 7 primitives — see `TRACK-ANALYSIS.md`)
- [ ] Short write-up: features, tech used, data sources, findings
- [ ] Deployed on Cloud Run (or note deploy-ready + local demo if no billing)
- [ ] Uses: Gemini 3.5 Flash ✔ · Google ADK ✔ · Cloud Run + (Firestore) ✔

---

## 7. Project layout

```
src/
  model.py          # LLM abstraction; Intake classifier (mocked) + ranking (real, graph-aware)
  orchestrator.py   # runs the 6-agent fleet; emits pitch as citable evidence
  gateway.py        # FastAPI — the Agent Gateway + dashboard host
  memory.py         # Memory Bank: decisions/interviews → citable evidence claims
  evidence.py       # the evidence graph engine (sources/claims/bundles + walk + scope wall)
  trace.py          # Observability — readable reasoning-chain traces
  agents/adk_agents.py  # the Google ADK fleet graph (runs offline via InMemoryRunner)
  dashboard/index.html  # the decision portal (vanilla JS, calls the API)
memory/             # generated: evidence-graph.json, investor.json, decisions.json (gitignored)
traces/             # generated: readable reasoning chains (gitignored)
tests/              # pytest: pipeline + ADK graph + evidence walk/bundle/ranking
deploy.sh, Dockerfile, registry.json, SPEC.md, TRACK-ANALYSIS.md, RUNBOOK.md
```

**To pick this up later:** read `HANDOFF.md` (where we left off) and `CONTEXT.md` (nav)
first. Everything is plain files — no hidden state.
