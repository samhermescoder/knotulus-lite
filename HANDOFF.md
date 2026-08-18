# Knotulus Lite — HANDOFF.md (where we left off)

> **Updated:** 2026-08-18 by side-projects orchestrator (E-noch)
> Read this FIRST before working. Update it at the END of every session.

## Current state
- Branch: `master` (pushed) | dirty: 0 | last commit: working build (6-agent fleet + tests)
- Last work: Built the full codebase. Decisions locked: **Fortified Enterprise
  Fleet track, solo**. Code runs end-to-end in MOCK mode (no credentials).
- **VERIFIED today:**
  - venv + deps install OK (`google-genai`, fastapi, uvicorn, pytest)
  - `pytest tests/` → **4 passed** (classify, e2e pipeline, memory→ranking, registry)
  - Live `python src/orchestrator.py` prints real classification + memory-adjusted
    ranking (prior PASS in `ai` dropped NeuroCo 0.9→0.7) + brief + trace file
  - `registry.json` (Agent Registry) + `memory/` (investor memory layer) + `traces/`
    (Observability) all working as plain files

## What is DONE
- [x] Track analysis + primitive mapping (TRACK-ANALYSIS.md)
- [x] 6-agent fleet: Intake, Assessment, Profile, Ranking, Brief, Memory
- [x] Orchestrator (Agent Runtime) + FastAPI gateway (Agent Gateway)
- [x] Model Armor (PII strip) + Memory Bank + Observability traces
- [x] Mock/real backend toggle (`ENABLE_GEMINI` env; ADC, no API key)
- [x] Dockerfile + Cloud Run deploy.sh + ADK agent entrypoint (src/agents/adk_agents.py)
- [x] Tests passing

## In flight / next steps (YOU + me)
- [ ] **YOU:** install gcloud (Windows installer) + `gcloud auth application-default login`
      (ADC — no API key; the key-creation block you hit is expected org policy)
- [ ] Flip `ENABLE_GEMINI=true` with project set; re-run tests in real mode
- [ ] `gcloud builds submit` + `gcloud run deploy` (scales-to-zero) — meets GCP-infra requirement
- [ ] Optional Firestore mirror (`ENABLE_FIRESTORE=true` in memory.py)
- [ ] Record demo video: pitch → ranked brief + trace; memory changes a future rank
- [ ] Write-up before **Sep 1 2026 08:00 GMT+8**

## Run commands (venv python — avoid Hermes PYTHONPATH leak)
- tests:        `bash run-tests.sh`
- live pipeline:`env -u PYTHONPATH KNOTULUS_ROOT="$PWD" ENABLE_GEMINI=false .venv/Scripts/python.exe src/orchestrator.py`
- API server:   `uvicorn src.gateway:app --port 8080`

## Open questions
- GCP project id? (for ENABLE_GEMINI + Cloud Run deploy)
- Firestore mirror wanted, or file-backed memory enough for submission?

## How to resume
1. `cd C:/Users/admin/Work/Hackathons/knotulus-lite`
2. Confirm gcloud/ADC done → set ENABLE_GEMINI in `.env`
3. `bash run-tests.sh` in real mode, then `./deploy.sh`
