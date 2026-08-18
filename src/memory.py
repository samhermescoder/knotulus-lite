"""Memory Bank — the investor memory layer (file-backed + optional Firestore).

This is the long-term state primitive from the Fortified Enterprise Fleet track
and the core of Knotulus's vision: it remembers what investors value, why they
passed, and which signals predicted a good conversation. Persisted as plain
JSON so it is human-auditable, with an optional Firestore mirror for the GCP
infra requirement.
"""
import os
import json

import evidence as E

ROOT = os.environ.get("KNOTULUS_ROOT", os.getcwd())
MEM_DIR = os.path.join(ROOT, "memory")
INVESTOR_F = os.path.join(MEM_DIR, "investor.json")
DECISIONS_F = os.path.join(MEM_DIR, "decisions.json")


def _ensure():
    os.makedirs(MEM_DIR, exist_ok=True)
    if not os.path.exists(INVESTOR_F):
        json.dump(
            {
                "preferences": {},
                "valued_signals": [],
                "pass_reasons": {},
                # Learning state for the investor memory layer:
                # signal_weights: learned per-signal value (higher = investor weights it more)
                # signals_observed: how many times each signal has appeared in a decision
                "signal_weights": {},
                "signals_observed": {},
            },
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


def _learn_signals(inv: dict, signals: list, direction: float):
    """Fast-cache mirror of signal preference (authoritative memory = evidence graph)."""
    for s in signals or []:
        s = str(s).strip().lower()
        if not s:
            continue
        inv["signals_observed"][s] = inv["signals_observed"].get(s, 0) + 1
        cur = inv["signal_weights"].get(s, 0.0)
        inv["signal_weights"][s] = round(max(-1.0, min(1.0, cur + direction * 0.2)), 3)


def _pair_ref(pitch_id: str) -> str:
    """Derive a stable pair_ref (founder<->investor scope key) from a pitch id."""
    return f"pair:{pitch_id}"


def record_decision(pitch_id, decision, sector, signals=None, note="",
                    founder: str = "unknown", investor: str = "default"):
    """Persist an investor decision: file log + citable evidence claim (pair-scoped).

    decision: "meet" | "pass"
    signals: candidate signal tags that drove the decision (become feedback claims).
    """
    _ensure()
    decisions = load_decisions()
    decisions.append(
        {
            "pitch_id": pitch_id,
            "decision": decision,
            "sector": sector,
            "signals": signals or [],
            "note": note,
        }
    )
    json.dump(decisions, open(DECISIONS_F, "w"), indent=2)

    inv = load_investor()
    pair = _pair_ref(pitch_id)
    # Source artifact = this investor's decision on the pitch (immutable)
    src = E.add_source("investor_feedback", "investor", investor,
                       content=f"Decision {decision} on {pitch_id} ({sector}): {note}",
                       pair_ref=pair, ref=pitch_id)
    # Feedback claim(s): one per signal that drove the decision (citable, verified)
    for s in (signals or []):
        E.add_claim("feedback", "investor", investor,
                     text=f"Investor {investor} {('valued' if decision=='meet' else 'rejected')} signal '{s}' on {sector} ({note})",
                     source_ids=[src], pair_ref=pair, status="verified")

    if decision == "pass":
        inv["pass_reasons"].setdefault(sector, []).append(note or "passed")
        _learn_signals(inv, signals, direction=-1.0)
    elif decision == "meet":
        inv["valued_signals"].append(sector)
        _learn_signals(inv, signals, direction=+1.0)
    json.dump(inv, open(INVESTOR_F, "w"), indent=2)

    _maybe_sync_firestore()
    return inv


def record_interview(pitch_id: str, outcome: str, signals: list = None, note: str = "",
                     investor: str = "default"):
    """Post-interview capture (the 'after' loop) — writes a citable feedback claim.

    outcome: "good" | "neutral" | "bad"
    signals: which screened signals fired/validated in the meeting.
    The interview outcome becomes verified evidence the ranking walks next time.
    """
    _ensure()
    decisions = load_decisions()
    direction = {"good": +1.0, "neutral": 0.0, "bad": -1.0}.get(outcome.lower(), 0.0)
    decisions.append(
        {
            "pitch_id": pitch_id,
            "decision": "interview",
            "outcome": outcome,
            "sector": load_decisions_sector(pitch_id),
            "signals": signals or [],
            "note": note,
        }
    )
    json.dump(decisions, open(DECISIONS_F, "w"), indent=2)

    inv = load_investor()
    pair = _pair_ref(pitch_id)
    src = E.add_source("investor_feedback", "investor", investor,
                       content=f"Interview outcome {outcome} on {pitch_id}: {note}",
                       pair_ref=pair, ref=pitch_id)
    for s in (signals or []):
        E.add_claim("feedback", "investor", investor,
                    text=f"After interview, investor {investor} {('validated' if direction>0 else 'discounted' if direction<0 else 'neutral on')} signal '{s}' ({outcome})",
                    source_ids=[src], pair_ref=pair, status="verified")
    _learn_signals(inv, signals, direction=direction)
    if outcome.lower() == "good":
        inv["valued_signals"].append(f"interview:{pitch_id}")
    json.dump(inv, open(INVESTOR_F, "w"), indent=2)

    _maybe_sync_firestore()
    return inv


def load_decisions_sector(pitch_id: str) -> str:
    """Best-effort lookup of a pitch's sector from prior decisions."""
    for d in load_decisions():
        if d.get("pitch_id") == pitch_id and d.get("sector"):
            return d["sector"]
    return "other"


def seed_sample():
    """Seed a prior PASS in 'ai' as REAL evidence: source + claims (knotty-shaped)."""
    _ensure()
    decisions = load_decisions()
    if any(d.get("pitch_id") == "seed_neuro_past" for d in decisions):
        return
    pitch_id = "seed_neuro_past"
    decisions.append(
        {
            "pitch_id": pitch_id,
            "decision": "pass",
            "sector": "ai",
            "signals": ["overconfident on unproven model", "weak go-to-market"],
            "note": "strong tech, weak go-to-market",
        }
    )
    json.dump(decisions, open(DECISIONS_F, "w"), indent=2)
    inv = load_investor()
    inv["pass_reasons"].setdefault("ai", []).append("strong tech, weak go-to-market")
    json.dump(inv, open(INVESTOR_F, "w"), indent=2)
    # Evidence graph: a pitch source + a verified 'rejected' feedback claim.
    # The investor rejected the 'technical moat' signal on ai pitches (strong tech
    # but weak GTM) — so a future ai pitch the classifier tags 'technical moat' is
    # penalized by the evidence walk (demonstrable signal-level memory).
    pair = _pair_ref(pitch_id)
    src = E.add_source("pitch", "founder", "NeuroCo",
                       content="NeuroCo AI radiology triage pitch — strong tech, weak GTM.",
                       pair_ref=pair, ref=pitch_id)
    E.add_claim("feedback", "investor", "default",
                text="Investor rejected signal 'technical moat' on ai (strong tech, weak go-to-market)",
                source_ids=[src], pair_ref=pair, status="verified")
    E.add_claim("feedback", "investor", "default",
                text="Investor rejected signal 'strong gtm' on ai (strong tech, weak go-to-market)",
                source_ids=[src], pair_ref=pair, status="verified")


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
