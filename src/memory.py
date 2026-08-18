"""Memory Bank — the investor memory layer (file-backed + optional Firestore).

This is the long-term state primitive from the Fortified Enterprise Fleet track
and the core of Knotulus's vision: it remembers what investors value, why they
passed, and which signals predicted a good conversation. Persisted as plain
JSON so it is human-auditable, with an optional Firestore mirror for the GCP
infra requirement.
"""
import os
import json

ROOT = os.environ.get("KNOTULUS_ROOT", os.getcwd())
MEM_DIR = os.path.join(ROOT, "memory")
INVESTOR_F = os.path.join(MEM_DIR, "investor.json")
DECISIONS_F = os.path.join(MEM_DIR, "decisions.json")


def _ensure():
    os.makedirs(MEM_DIR, exist_ok=True)
    if not os.path.exists(INVESTOR_F):
        json.dump(
            {"preferences": {}, "valued_signals": [], "pass_reasons": {}},
            open(INVESTOR_F, "w"),
            indent=2,
        )
    if not os.path.exists(DECISIONS_F):
        json.dump([], open(DECISIONS_F, "w"), indent=2)


def load_investor() -> dict:
    _ensure()
    return json.load(open(INVESTOR_F))


def load_decisions() -> list:
    _ensure()
    return json.load(open(DECISIONS_F))


def record_decision(pitch_id, decision, sector, signals=None, note=""):
    """Persist an investor decision and update the investor memory layer."""
    _ensure()
    decisions = load_decisions()
    decisions.append(
        {
            "pitch_id": pitch_id,
            "decision": decision,  # "meet" | "pass"
            "sector": sector,
            "signals": signals or [],
            "note": note,
        }
    )
    json.dump(decisions, open(DECISIONS_F, "w"), indent=2)

    inv = load_investor()
    if decision == "pass":
        inv["pass_reasons"].setdefault(sector, []).append(note or "passed")
    elif decision == "meet":
        inv["valued_signals"].append(sector)
    json.dump(inv, open(INVESTOR_F, "w"), indent=2)

    _maybe_sync_firestore()
    return inv


def seed_sample():
    """Seed a prior PASS in 'ai' so memory demonstrably shifts a later ranking."""
    _ensure()
    decisions = load_decisions()
    if any(d.get("pitch_id") == "seed_neuro_past" for d in decisions):
        return
    decisions.append(
        {
            "pitch_id": "seed_neuro_past",
            "decision": "pass",
            "sector": "ai",
            "signals": ["overconfident on unproven model"],
            "note": "strong tech, weak go-to-market",
        }
    )
    json.dump(decisions, open(DECISIONS_F, "w"), indent=2)
    inv = load_investor()
    inv["pass_reasons"].setdefault("ai", []).append("strong tech, weak go-to-market")
    json.dump(inv, open(INVESTOR_F, "w"), indent=2)


def _maybe_sync_firestore():
    """Optional mirror to Firestore (GCP infra). No-op unless ENABLE_FIRESTORE=true."""
    if os.environ.get("ENABLE_FIRESTORE", "false").lower() != "true":
        return
    try:
        from google.cloud import firestore  # lazy import
    except Exception:
        return
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        return
    db = firestore.Client(project=project)
    db.collection("knotulus_decisions").document("latest").set(
        {"decisions": load_decisions(), "investor": load_investor()}
    )
