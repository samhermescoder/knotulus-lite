# Knotulus Lite — HANDOFF.md (where we left off)

> **Updated:** 2026-08-18 (resume + ADK-fix session) by side-projects orchestrator (E-noch)
> Read this FIRST before working. Update it at the END of every session.

## Current state
- Branch: `master` (pushed) | last commit: `a56fc6b` (ADK runnable + dual auth + gunicorn)
- **Fully verified working this session (mock mode, zero creds/billing):**
  - `pytest tests/` → **6 passed** (4 pipeline + 2 ADK-graph)
  - Live `python src/orchestrator.py` → full fleet, memory-adjusted ranking + trace
  - Live gateway `bash run.sh -m src.gateway` → `/health`, `/registry` (6 agents),
    `/pitch` (full run) all 200 OK. **Agent Gateway primitive confirmed live.**
  - ADK graph runs via `InMemoryRunner` (offline mock model) — `Built with Google ADK`
    is now EXERCISED, not just claimed.

## Hard constraints (do NOT violate)
- **GCP scope lock:** the ADC login on this machine (enochfyw@gmail.com) and ALL
  gcloud/Vertex usage MUST stay inside project `knotulus-lite` ONLY. User explicitly
  forbade touching any other project with these creds. Always pass `--project knotulus-lite`.
- **Auth:** Active path = Vertex AI + ADC (real mode). Gemini Developer API key path is
  geo-blocked from HK (FAILED_PRECONDITION) — unusable here; kept only as fallback code.
- **No billing (user choice, 2026-08-18):** project `knotulus-lite` has NO billing
  account attached. Therefore Cloud Run deploy + (likely) real Gemini inference are
  BLOCKED. Decision: stay fully mock-mode + local live demo. Do NOT enable billing
  or run gcloud deploy without explicit user go-ahead.

## What is DONE
- [x] Track analysis + primitive mapping (TRACK-ANALYSIS.md)
- [x] 6-agent fleet: Intake, Assessment, Profile, Ranking, Brief, Memory
- [x] Orchestrator (Agent Runtime) + FastAPI gateway (Agent Gateway) — **live-verified**
- [x] Model Armor (PII strip) + Memory Bank + Observability traces
- [x] Mock/real backend toggle (Vertex+ADC active; API-key fallback, HK-blocked)
- [x] **Google ADK graph actually runs** (SequentialAgent + InMemoryRunner, offline mock;
      `tests/test_adk_graph.py` proves it) — fixes prior "claimed not runnable" gap
- [x] Dockerfile + Cloud Run deploy.sh (deploy BLOCKED by no-billing; code is deploy-ready)
- [x] gunicorn added to requirements.txt (was missing — would have crashed Cloud Run boot)
- [x] `src`-on-path bootstrap in gateway.py/adk_agents.py (fixed import bug that broke
      `-m src.gateway` / uvicorn / Docker invocations)
- [x] Tests passing (6)

## Blocker (no-billing)
- Cloud Run deploy requires a billing account on `knotulus-lite`. User chose free path,
  so submission will show: local live demo + deploy-ready code (Cloud Run scales-to-zero).
  If a judge strictly requires a live URL, revisit billing decision.

## Remaining hackathon tasks (no creds needed)
- [ ] Record demo video: `POST /pitch` NeuroCo → ranked brief + trace; memory seed drops a
      future ai rank (run `bash run.sh scripts/showcase.py` or the gateway live)
- [ ] Write-up before **Sep 1 2026 08:00 GMT+8** (features, tech, findings)
- [ ] README/architecture diagram (TRACK-ANALYSIS.md mapping already covers primitives)
- [ ] Optional Firestore mirror (would also need billing → skip under no-billing)

## Run commands (venv python — avoids Hermes PYTHONPATH leak)
- tests:        `bash run-tests.sh`
- live pipeline:`env -u PYTHONPATH KNOTULUS_ROOT="$PWD" ENABLE_GEMINI=false .venv/Scripts/python.exe src/orchestrator.py`
- API server:   `bash run.sh -m src.gateway`   (then curl :8080/health, /registry, /pitch)
- ADK graph:    `env -u PYTHONPATH ENABLE_GEMINI=false .venv/Scripts/python.exe src/agents/adk_agents.py`

## How to resume
1. `cd C:/Users/admin/Work/Hackathons/knotulus-lite`
2. Mock-mode work needs no creds — just run the commands above.
3. Real mode / Cloud Run ONLY if user attaches billing + re-approves (scope-locked to knotulus-lite).
