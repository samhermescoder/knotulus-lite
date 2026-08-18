import os
import json
import pytest

# Knotulus Lite runs with zero credentials in mock mode.
os.environ["ENABLE_GEMINI"] = "false"
os.environ["KNOTULUS_ROOT"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import model as M
from orchestrator import run_pipeline
from memory import load_decisions, record_decision, seed_sample, load_investor

SAMPLE_PITCH = (
    "We are building NeuroCo, an AI platform for radiology triage. "
    "Raising $2M seed. Contact founder@neuroco.com or +1 555 0100."
)
SAMPLE_RESP = [
    "When the market shifted we immediately re-focused the model on the top scan.",
    "A key hire quit before launch; I acted first to cover the gap.",
    "Data contradicted our thesis on uptake, so we pivoted the GTM.",
]


def test_classify_fit_mock():
    cls = M.classify_fit(SAMPLE_PITCH)
    assert cls["company"] == "NeuroCo"
    assert cls["ask"].startswith("$2m") or cls["ask"].startswith("$2M")
    assert cls["sector"] == "ai"
    assert cls["fit"] in ("high", "medium", "low")
    # Model Armor: PII stripped (no email/phone in output fields)
    blob = json.dumps(cls)
    assert "@" not in blob and "555" not in blob


def test_pipeline_end_to_end():
    seed_sample()
    out = run_pipeline(SAMPLE_PITCH, responses=SAMPLE_RESP)
    assert out["pitch_id"].startswith("pitch_")
    assert out["classification"]["company"] == "NeuroCo"
    assert isinstance(out["assessment"], list) and len(out["assessment"]) == 3
    assert "traits" in out["profile"]
    assert out["ranked"][0]["score"] > 0
    assert "PRE-MEETING BRIEF" in out["brief"]
    assert os.path.exists(os.path.join(os.environ["KNOTULUS_ROOT"], out["trace"]))


def test_memory_persists_and_influences_ranking():
    # fresh-ish: record a PASS in 'ai' then rank a new ai candidate
    record_decision("test_pitch_ai", "pass", "ai", note="weak GTM")
    decisions = load_decisions()
    assert any(d["pitch_id"] == "test_pitch_ai" for d in decisions)

    candidates = [{"company": "NewAI", "sector": "ai", "fit": "high", "confidence": 0.9}]
    ranked = M.rank_shortlist(candidates, decisions)
    # PASS in same sector lowers the score below the base high (0.9)
    assert ranked[0]["score"] < 0.9
    assert any("PASS" in r for r in ranked[0]["rationale"])


def test_registry_discovery(tmp_path):
    reg = json.load(open(os.path.join(os.environ["KNOTULUS_ROOT"], "registry.json")))
    ids = {a["id"] for a in reg["agents"]}
    assert {"intake", "assessment", "profile", "ranking", "brief", "memory"} <= ids
