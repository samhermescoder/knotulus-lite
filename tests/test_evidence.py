import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import evidence as E
import memory as M
import model as M2

REPO_ROOT = os.environ.get("KNOTULUS_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def _restore_root():
    """Evidence tests switch KNOTULUS_ROOT + cached module paths to a temp dir.
    Restore everything afterwards so sibling test files (test_pipeline) see the
    real repo root and registry.json."""
    saved_env = os.environ.get("KNOTULUS_ROOT")
    saved = {mod: {"ROOT": mod.ROOT, "MEM_DIR": getattr(mod, "MEM_DIR", None)}
             for mod in (E, M)}
    yield
    if saved_env is not None:
        os.environ["KNOTULUS_ROOT"] = saved_env
    for mod, vals in saved.items():
        mod.ROOT = vals["ROOT"]
        if vals["MEM_DIR"] is not None:
            mod.MEM_DIR = vals["MEM_DIR"]
    E.EVID_FILE = os.path.join(REPO_ROOT, "memory", "evidence-graph.json")


def _fresh():
    """Each call gets a brand-new isolated root — no cross-test contamination.

    Modules cache ROOT at import, so we must also re-point their module-level
    path vars after switching KNOTULUS_ROOT.
    """
    root = tempfile.mkdtemp()
    os.environ["KNOTULUS_ROOT"] = root
    os.environ["ENABLE_GEMINI"] = "false"
    os.makedirs(os.path.join(root, "memory"), exist_ok=True)
    for mod in (E, M):
        mod.ROOT = root
        mod.MEM_DIR = os.path.join(root, "memory")
    if hasattr(M, "EVID_DIR"):
        M.EVID_DIR = os.path.join(root, "memory")
    E.EVID_DIR = os.path.join(root, "memory")
    E.EVID_FILE = os.path.join(root, "memory", "evidence-graph.json")
    M.MEM_DIR = os.path.join(root, "memory")
    M.INVESTOR_F = os.path.join(root, "memory", "investor.json")
    M.DECISIONS_F = os.path.join(root, "memory", "decisions.json")
    return root


def test_evidence_sources_claims_edges():
    _fresh()
    sid = E.add_source("pitch", "founder", "NeuroCo", "NeuroCo AI pitch", pair_ref="pair:x")
    cid = E.add_claim("fact", "founder", "NeuroCo", "Company NeuroCo, sector ai",
                      source_ids=[sid], pair_ref="pair:x", status="verified")
    g = E.load_graph()
    assert any(n["type"] == "source" for n in g["nodes"])
    assert any(n["type"] == "claim" for n in g["nodes"])
    assert any(e["source"] == cid and e["target"] == sid for e in g["edges"])
    # forward walk: claim -> source
    chain = E.walk_claim(cid)
    assert chain["claim"]["id"] == cid
    assert chain["sources"][0]["id"] == sid


def test_bundle_scope_wall_no_cross_investor_leak():
    _fresh()
    # investor A rejects a signal
    M.record_decision("p1", "pass", "ai", signals=["technical moat"], note="n",
                      investor="A")
    # investor B has no claims
    bA = E.compile_bundle("A")
    bB = E.compile_bundle("B")
    assert any(c["kind"] == "feedback" for c in bA["claims"])
    assert not any(c["kind"] == "feedback" for c in bB["claims"])
    assert bB["claims"] == []  # hard scope wall: B sees nothing of A


def test_ranking_signal_memory_shifts_future_rank():
    _fresh()
    M.seed_sample()  # investor 'default' rejected 'technical moat' & 'strong gtm' on ai
    # A new ai pitch the classifier tags 'technical moat' -> penalized by evidence walk
    cand_rejected = [{"company": "NewRad", "sector": "ai", "fit": "high",
                      "confidence": 0.9, "signals": ["technical moat"]}]
    r1 = M2.rank_shortlist(cand_rejected, M.load_decisions(), investor="default", evidence=E)
    # Control: same pitch, signal the investor never rejected
    cand_ctrl = [{"company": "Safe", "sector": "ai", "fit": "high",
                  "confidence": 0.9, "signals": ["capital efficiency"]}]
    r2 = M2.rank_shortlist(cand_ctrl, M.load_decisions(), investor="default", evidence=E)
    assert r1[0]["score"] < r2[0]["score"], (r1[0]["score"], r2[0]["score"])
    assert any("rejected" in x for x in r1[0]["rationale"])
