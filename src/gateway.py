"""FastAPI gateway — the Agent Gateway (Fortified Enterprise Fleet primitive).

Single unified routing + policy enforcement: inbound pitches POST here, the
orchestrator runs the async fleet, and discovery/memory/trace/evidence endpoints
expose the registry, investor memory, and the walkable evidence graph
(auditability). GET / serves the decision dashboard (the "after interview" portal).
"""
import os
import sys

# Make `src` importable so bare `import model` / `from orchestrator import ...`
# resolve whether this file is run as a script, as `src.gateway` (uvicorn/-m),
# or inside a container. (src/ is a package, so without this the module-style
# invocations fail with ModuleNotFoundError: model.)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse

import model as M
from orchestrator import run_pipeline
from memory import (
    load_investor,
    load_decisions,
    record_decision,
    record_interview,
    seed_sample,
)
import evidence as E

app = FastAPI(title="Knotulus Lite", version="1.1.0")

ROOT = os.environ.get("KNOTULUS_ROOT", os.getcwd())
REGISTRY_PATH = os.path.join(ROOT, "registry.json")
DASHBOARD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard", "index.html")


@app.get("/")
def dashboard():
    """Decision dashboard (the 'after interview' portal)."""
    if os.path.exists(DASHBOARD_PATH):
        return FileResponse(DASHBOARD_PATH)
    return JSONResponse(status_code=200, content={"msg": "dashboard not built; API is live"})


@app.get("/registry")
def get_registry():
    """Agent Registry (discovery + versioning)."""
    import json
    return json.load(open(REGISTRY_PATH))


@app.get("/memory")
def get_memory():
    """Memory Bank inspection — what the investor values, why they passed."""
    return {"investor": load_investor(), "decisions": load_decisions()}


@app.get("/evidence")
def get_evidence():
    """The walkable evidence graph (sources + claims + edges)."""
    return E.load_graph()


@app.get("/bundle")
def get_bundle(investor: str = "default"):
    """Per-investor compiled evidence bundle (scope wall applied)."""
    return E.compile_bundle(investor)


@app.post("/decision")
def post_decision(payload: dict = Body(...)):
    """Memory Agent endpoint — persist an investor decision (meet/pass).

    Records a citable feedback claim (pair-scoped) so the NEXT ranking walks it.
    Optional `signals` (list) = which signal tags drove the decision.
    """
    inv = record_decision(
        payload.get("pitch_id", "manual"),
        payload.get("decision", "pass"),
        payload.get("sector", "other"),
        signals=payload.get("signals", []),
        note=payload.get("note", ""),
        founder=payload.get("founder", "unknown"),
        investor=payload.get("investor", "default"),
    )
    return {"ok": True, "investor": inv, "bundle": E.compile_bundle(payload.get("investor", "default"))}


@app.post("/interview")
def post_interview(payload: dict = Body(...)):
    """Post-interview capture (the 'after' loop).

    outcome: good | neutral | bad; signals = which screened signals fired.
    Writes a verified feedback claim the ranking walks next time.
    """
    inv = record_interview(
        payload.get("pitch_id", "manual"),
        payload.get("outcome", "neutral"),
        signals=payload.get("signals", []),
        note=payload.get("note", ""),
        investor=payload.get("investor", "default"),
    )
    return {"ok": True, "investor": inv, "bundle": E.compile_bundle(payload.get("investor", "default"))}


@app.post("/pitch")
def post_pitch(payload: dict = Body(...)):
    """Agent Gateway entry — run the full async screening fleet."""
    out = run_pipeline(
        payload.get("text", ""),
        responses=payload.get("responses"),
        investor=payload.get("investor"),
    )
    return out


@app.get("/traces/{pitch_id}")
def get_trace(pitch_id: str):
    """Agent Observability — read a reasoning chain."""
    path = os.path.join(ROOT, "traces", f"{pitch_id}.md")
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "trace not found"})
    return PlainTextResponse(open(path).read())


@app.post("/seed")
def post_seed():
    """Seed a prior PASS so memory demonstrably shifts a later ranking."""
    seed_sample()
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok", "mode": "gemini" if M.USE_GEMINI else "mock"}


def run():
    """Console-script / `python -m src.gateway` entrypoint."""
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
