"""FastAPI gateway — the Agent Gateway (Fortified Enterprise Fleet primitive).

Single unified routing + policy enforcement: inbound pitches POST here, the
orchestrator runs the async fleet, and discovery/memory/trace endpoints expose
the registry, investor memory, and reasoning-chain traces (auditability).
"""
import os

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, PlainTextResponse

import model as M
from orchestrator import run_pipeline
from memory import (
    load_investor,
    load_decisions,
    record_decision,
    seed_sample,
)

app = FastAPI(title="Knotulus Lite", version="1.0.0")

REGISTRY_PATH = os.path.join(os.environ.get("KNOTULUS_ROOT", os.getcwd()), "registry.json")


@app.get("/registry")
def get_registry():
    """Agent Registry (discovery + versioning)."""
    import json
    return json.load(open(REGISTRY_PATH))


@app.get("/memory")
def get_memory():
    """Memory Bank inspection — what the investor values, why they passed."""
    return {"investor": load_investor(), "decisions": load_decisions()}


@app.post("/decision")
def post_decision(payload: dict = Body(...)):
    """Memory Agent endpoint — persist an investor decision (meet/pass)."""
    inv = record_decision(
        payload.get("pitch_id", "manual"),
        payload.get("decision", "pass"),
        payload.get("sector", "other"),
        signals=payload.get("signals", []),
        note=payload.get("note", ""),
    )
    return {"ok": True, "investor": inv}


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
    path = os.path.join(os.environ.get("KNOTULUS_ROOT", os.getcwd()), "traces", f"{pitch_id}.md")
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
