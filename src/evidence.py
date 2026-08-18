"""Evidence graph — the investor memory layer (real, runnable, LLM-agnostic).

Faithful, dependency-free port of Knotulus/knotty's evidence model
(src/evidence/*): the three layers that make screening *evidence-based*.

    SOURCES  — first-hand artifacts (pitch email, deck, screening result,
               investor feedback). Immutable, content-addressed.
    CLAIMS   — extracted facts / scores / asks / preferences / feedback /
               decisions that CITE >=1 source. The ONLY citable unit the
               ranking/agent may consume. raw artifact text never flows into
               a claim — only scored output + citations.
    BUNDLES  — per-investor compiled snapshot (the cheap view the ranking reads).

Edges: claim -> source, relation "cited by", weight. The graph is WALKABLE:
    - forward:  claim -> sources that back it (the "why do we believe X?")
    - reverse:  source -> claims citing it (audit: "what rests on this?")
    - entity:   all verified claims + sources for an investor (the memory)

This is the REAL memory engine. Only Intake classification (model.classify_fit)
is mocked; everything here operates on data we feed it and is tested against
structured fixtures. Swap Intake to Gemini later without touching this module.

Store: memory/evidence-graph.json  (knotty-shaped: nodes + edges, human-readable,
renderable by the dashboard). No DB, no GCP — plain files per ICM.
"""
import os
import json
import hashlib
import datetime

ROOT = os.environ.get("KNOTULUS_ROOT", os.getcwd())
EVID_DIR = os.path.join(ROOT, "memory")
EVID_FILE = os.path.join(EVID_DIR, "evidence-graph.json")

SOURCE_KINDS = {
    "founder_email", "founder_info", "pitch", "deck", "assessment_response",
    "screening_result", "assessment_interpretation", "investor_preference",
    "investor_feedback",
}
CLAIM_KINDS = {
    "fact", "score", "ask", "preference", "feedback", "interpretation", "decision",
}


# ---------------------------------------------------------------------------
# IDs + helpers (content-addressed, deterministic — mirrors knotty sha256 ids)
# ---------------------------------------------------------------------------
def _sha(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return h[:16]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------
def _ensure():
    os.makedirs(EVID_DIR, exist_ok=True)
    if not os.path.exists(EVID_FILE):
        json.dump(
            {"meta": {"name": "Evidence graph", "updated": _now(),
                      "note": "Knotulus-lite investor memory (port of knotty evidence model)"},
             "nodes": [], "edges": []},
            open(EVID_FILE, "w"), indent=2,
        )


def load_graph() -> dict:
    _ensure()
    return json.load(open(EVID_FILE))


def save_graph(g: dict):
    g["meta"]["updated"] = _now()
    json.dump(g, open(EVID_FILE, "w"), indent=2)


def _nodes(g: dict):
    return {n["id"]: n for n in g["nodes"]}


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
def add_source(kind: str, entity_type: str, entity_ref: str, content: str,
               pair_ref: str = None, ref: str = None) -> str:
    """Add an immutable first-hand artifact. Returns its id."""
    assert kind in SOURCE_KINDS, f"bad source kind {kind}"
    _ensure()
    g = load_graph()
    sid = _sha(kind, entity_type, entity_ref, str(pair_ref), str(ref), content)
    if any(n["id"] == sid for n in g["nodes"]):
        return sid  # dedupe by content
    g["nodes"].append({
        "id": sid, "type": "source", "kind": kind,
        "entity_type": entity_type, "entity_ref": entity_ref,
        "pair_ref": pair_ref, "ref": ref, "content": content,
        "state": "active",
    })
    save_graph(g)
    return sid


# ---------------------------------------------------------------------------
# Claims (cite >=1 source)
# ---------------------------------------------------------------------------
def add_claim(kind: str, entity_type: str, entity_ref: str, text: str,
              source_ids: list, pair_ref: str = None,
              status: str = "verified") -> str:
    """Add a citable claim. source_ids must be non-empty (provenance enforced)."""
    assert kind in CLAIM_KINDS, f"bad claim kind {kind}"
    assert source_ids, "a claim must cite >=1 source"
    _ensure()
    g = load_graph()
    cid = _sha(text, "|".join(sorted(source_ids)))
    # update-or-insert (keep cited sources cumulative)
    for n in g["nodes"]:
        if n["id"] == cid:
            n["status"] = status
            return cid
    g["nodes"].append({
        "id": cid, "type": "claim", "kind": kind,
        "entity_type": entity_type, "entity_ref": entity_ref,
        "pair_ref": pair_ref, "text": text, "status": status, "state": "active",
    })
    for s in source_ids:
        g["edges"].append({"source": cid, "target": s,
                            "relation": "cited by", "weight": 0.9})
    save_graph(g)
    return cid


# ---------------------------------------------------------------------------
# Walk (provenance — the "why")
# ---------------------------------------------------------------------------
def walk_claim(claim_id: str):
    """Forward: claim -> the sources that back it."""
    g = load_graph()
    nodes = _nodes(g)
    claim = nodes.get(claim_id)
    if not claim:
        return None
    return {"claim": claim,
            "sources": [nodes.get(e["target"]) for e in g["edges"]
                        if e["source"] == claim_id]}


def claims_citing_source(source_id: str) -> list:
    """Reverse: every claim that cites a source (audit trail)."""
    g = load_graph()
    nodes = _nodes(g)
    return [nodes[e["source"]] for e in g["edges"] if e["target"] == source_id]


def evidence_for_entity(entity_type: str, entity_ref: str) -> dict:
    """All verified claims + their sources for an entity (the memory)."""
    g = load_graph()
    nodes = _nodes(g)
    claims = [n for n in g["nodes"]
              if n["type"] == "claim" and n["status"] == "verified"
              and n["entity_type"] == entity_type and n["entity_ref"] == entity_ref]
    cited = {s for e in g["edges"] for s in ([e["target"]] if e["source"] in
              {c["id"] for c in claims} else [])}
    sources = [nodes[s] for s in cited if s in nodes]
    return {"claims": claims, "sources": sources}


# ---------------------------------------------------------------------------
# Bundle (per-investor compiled snapshot; scope wall = no cross-investor leak)
# ---------------------------------------------------------------------------
def compile_bundle(investor_id: str, scope_pairs: set = None) -> dict:
    """Compact, citable snapshot for one investor.

    - rejected claims excluded
    - pair-scoped claims outside scope_pairs excluded (hard scope wall)
    - sourceIndex carries METADATA ONLY (never full source content)
    """
    g = load_graph()
    nodes = _nodes(g)
    included = []
    for n in g["nodes"]:
        if n["type"] != "claim":
            continue
        if n["status"] == "rejected":
            continue
        if n["entity_type"] == "investor" and n["entity_ref"] == investor_id:
            # Investor-level claim: always in. Pair-scoped investor claims (feedback
            # on a specific pitch) also belong to this investor -> include when no
            # explicit scope given, or when within the requested scope wall.
            if scope_pairs is None or (n.get("pair_ref") in scope_pairs):
                included.append(n)
        elif scope_pairs is not None and n.get("pair_ref") in scope_pairs:
            included.append(n)
        elif scope_pairs is None and n["entity_type"] == "founder" and n.get("pair_ref"):
            included.append(n)
    cited_ids = {s for e in g["edges"] for s in ([e["target"]] if e["source"] in
                  {c["id"] for c in included} else [])}
    source_index = {}
    for sid in cited_ids:
        s = nodes.get(sid)
        if s:
            source_index[sid] = {"kind": s["kind"], "entity_ref": s["entity_ref"],
                                  "ref": s.get("ref")}
    return {
        "investor_id": investor_id,
        "built_at": _now(),
        "claims": [{"id": c["id"], "text": c["text"], "kind": c["kind"],
                    "entity_ref": c["entity_ref"], "status": c["status"],
                    "sources": [e["target"] for e in g["edges"] if e["source"] == c["id"]]}
                   for c in included],
        "source_index": source_index,
    }


def bundle_to_context(bundle: dict, entity_ref: str = None, max_claims: int = 60) -> str:
    """Render a bundle as a compact, citable context slice (LLM-agnostic)."""
    claims = [c for c in bundle["claims"] if (entity_ref is None or c["entity_ref"] == entity_ref)]
    lines = []
    for c in claims[:max_claims]:
        refs = [bundle["source_index"].get(s, {}).get("kind", s[:8]) for s in c["sources"]]
        lines.append(f"- [{c['kind']}] {c['text']}  (src: {', '.join(refs)})")
    return "\n".join([
        f"# Evidence ({len(claims)} claims, built {bundle['built_at'][:10]})",
        'Cite claims by their text. If no claim covers the question, say "no source in the data".',
        *lines,
    ])
