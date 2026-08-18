# Knotulus Lite — CONTEXT.md (workspace nav)

**What:** Simplified, open-source reimplementation of Knotulus's ICM as a Google ADK + Gemini 3.5 Flash agent fleet — built for the All Things Agentic Hackathon (Fortified Enterprise Fleet track).
**Status:** live
**Remote:** `github.com/samhermescoder/knotulus-lite.git` (already set as origin)
**Registry:** `~/knotulus/registry.json` → `projects.knotulus-lite`

## How to run (planned)
```bash
# local dev (ADK web)
adk web .

# deploy fleet to Cloud Run
gcloud run deploy knotulus-lite --source . --region us-central1

# tests
pytest tests/
```

## Structure nav
| Path | What it is |
|------|-----------|
| `src/` | ADK agents (orchestrator, registry, memory, worker) |
| `registry.json` | Agent Registry (discovery/versioning) — ICM analog |
| `memory/` | Memory Bank (cross-session, file-backed JSON/MD) |
| `traces/` | Observability: plain-text reasoning-chain logs |
| `TRACK-ANALYSIS.md` | Why Fortified Enterprise Fleet + technique |
| `SPEC.md` | What we're building & success criteria |
| `README.md` | Submission-facing overview |

## Guardrails
- default = user is sole merger to main; feature branches + PRs, never force-push
- registry.json is canonical map — update it on any structural change

## Where state lives
- **HANDOFF.md** — where we left off. Read first; update at end of every session.
- **Registry** — `~/knotulus/registry.json` → `projects.knotulus-lite`.
