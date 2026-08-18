# RUNBOOK — Knotulus Lite

Operate, demo, and deploy the Knotulus Lite agent fleet for the
**All Things Agentic Hackathon (Fortified Enterprise Fleet track)**.

- **Stack:** Google ADK · Gemini 3.5 Flash · Cloud Run · (optional) Firestore
- **Deadline:** Sep 1, 2026 · 08:00 GMT+8
- **Repo:** https://github.com/samhermescoder/knotulus-lite

---

## 0. Prereqs
- Python 3.11+ (dev used 3.12)
- `uv` (or `pip`) for installs
- A GCP project (for real mode + Cloud Run). **No API key required** — we use
  Application Default Credentials (ADC).
- Google ADK only needed if you run the ADK agent graph (`src/agents/adk_agents.py`).

---

## 1. Local install
```bash
cd C:/Users/admin/Work/Hackathons/knotulus-lite
uv venv .venv
. .venv/Scripts/activate
uv pip install -e ".[dev,adk]"      # adk optional; dev gives pytest
```
> **Windows note:** the shell leaks the Hermes-agent `PYTHONPATH` into the venv.
> Always run via `bash run.sh <script>` / `bash run-tests.sh` which `unset PYTHONPATH`,
> or prefix commands with `env -u PYTHONPATH`.

---

## 2. Run modes

### Mock mode (DEFAULT — zero credentials)
```bash
bash run-tests.sh                              # pytest: 4 passed
bash run.sh src/orchestrator.py                # one live screening run + trace
bash run.sh scripts/showcase.py               # memory-layer demo narrative
```
Model backend = deterministic heuristics. Pipeline, Memory Bank, and Observability
traces all work and are fully testable.

### Real mode (Gemini 3.5 Flash via Vertex AI + ADC)
1. Install gcloud (Windows): https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe
2. `gcloud auth application-default login`  ← opens browser; no API key needed
3. `gcloud config set project <YOUR_GCP_PROJECT_ID>`
4. `cp .env.example .env` and set:
   ```
   ENABLE_GEMINI=true
   GOOGLE_CLOUD_PROJECT=<YOUR_GCP_PROJECT_ID>
   GOOGLE_CLOUD_LOCATION=us-central1
   GEMINI_MODEL=gemini-3.5-flash
   ```
5. `. .venv/Scripts/activate && python -c "import dotenv; dotenv.load_dotenv()"` then run as above.

> Only `ENABLE_GEMINI` flips the backend; all code paths are identical otherwise.

---

## 3. API (FastAPI gateway — Agent Gateway primitive)
```bash
bash run.sh -m src.gateway          # or: uvicorn src.gateway:app --port 8080
```
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/pitch` | Submit a pitch (text + optional founder responses) → runs fleet |
| GET  | `/registry` | Agent Registry (discovery + versions) |
| GET  | `/memory` | Investor memory layer (decisions, passes, valued signals) |
| POST | `/decision` | Memory Agent: persist meet/pass |
| GET  | `/traces/{pitch_id}` | Reasoning-chain trace (Observability) |
| POST | `/seed` | Seed a prior PASS so memory shifts ranking |
| GET  | `/health` | mode = mock | gemini |

Example:
```bash
curl -X POST localhost:8080/pitch -H 'content-type: application/json' \
  -d '{"text":"We are building NeuroCo, an AI radiology triage platform. Raising $2M seed."}'
```

---

## 4. Deploy to Cloud Run (GCP infra requirement)
`deploy.sh` builds the image and deploys with **min-instances 0** (scales-to-zero →
near-zero idle cost). Edit `PROJECT_ID` / `REGION` / `ENABLE_GEMINI` at the top first.
```bash
bash deploy.sh
```
Then `gcloud run services describe knotulus-lite --region $REGION` to get the URL.

### Optional Firestore mirror (secondary GCP service)
Set `ENABLE_FIRESTORE=true` in `.env` and `requirements` to include `google-cloud-firestore`.
`memory.py` mirrors decisions to `knotulus_decisions/latest`. File-backed store remains
the source of truth (keeps the "interpretable" story).

---

## 5. Demo video script (3 minutes)
1. **Problem (30s):** investors drown in decks; first meeting re-discovers fit.
2. **Live screening (60s):** `POST /pitch` with NeuroCo; show JSON → ranked shortlist
   + pre-meeting brief; open `traces/<pitch>.md` and read the reasoning chain aloud.
3. **Memory layer (60s):** `GET /memory` shows a prior PASS in `ai`; re-run a new ai
   pitch → score drops 0.9→0.7 with the trace explaining *why*. Learning, visible.
4. **Fleet + compliance (30s):** `GET /registry` (6 discoverable agents); note Model
   Armor PII strip; note Cloud Run scales-to-zero. Close on "interpretable by design."

---

## 6. Troubleshooting
| Symptom | Fix |
|---------|-----|
| `import google.genai` → pydantic error | `PYTHONPATH` leak; run via `bash run.sh` / `env -u PYTHONPATH` |
| `ModuleNotFoundError: model` | run from repo root; `src/` is on path via conftest or `python src/orchestrator.py` |
| real mode auth error | re-run `gcloud auth application-default login`; check `GOOGLE_CLOUD_PROJECT` |
| `/trace` 404 | pitch_id comes from the `/pitch` response `pitch_id` field |

---

## 7. Submission checklist (due Sep 1 2026 08:00 GMT+8)
- [ ] Repo public + README + architecture notes (this file, TRACK-ANALYSIS.md, ADRs)
- [ ] Demo video (script §5) uploaded
- [ ] Architecture diagram (see TRACK-ANALYSIS.md mapping table)
- [ ] Short write-up: features, tech used, data sources, findings
- [ ] Deployed on Cloud Run with proof (video/README) — need not be live at judging
- [ ] Uses: Gemini 3.5 Flash ✔ · Google ADK ✔ · Cloud Run + (Firestore) ✔
