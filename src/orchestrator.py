"""OrchestratorAgent — routes a pitch through the fleet end-to-end.

This is the long-running async pipeline (Agent Runtime primitive). It calls the
6 agents in order, writes the reasoning trace (Observability), and returns a
ranked shortlist + brief. Model Armor (screen_pii) runs inside model.py before
any text is stored or traced.
"""
import os
import uuid

import model as M
from trace import Trace
from memory import load_decisions, load_investor, seed_sample


def run_pipeline(pitch_text: str, responses: list = None, investor: dict = None):
    investor = investor or {"name": "default"}
    pitch_id = "pitch_" + uuid.uuid4().hex[:8]
    tr = Trace(pitch_id)

    # 1. Intake
    tr.log("IntakeAgent", "Read inbound pitch, strip PII, classify fit.",
           "classify_fit(pitch)", None)
    cls = M.classify_fit(pitch_text)
    tr.steps[-1]["result"] = cls

    # 1b. Emit the pitch as CITABLE EVIDENCE (knotty-shaped): one source + claims.
    # This is the intake output becoming part of the walkable graph.
    import evidence as EV
    pair = f"pair:{pitch_id}"
    src = EV.add_source("pitch", "founder", cls.get("company", "Unknown Co"),
                         content=M.screen_pii(pitch_text), pair_ref=pair, ref=pitch_id)
    EV.add_claim("fact", "founder", cls.get("company", "Unknown Co"),
                 text=f"Company: {cls.get('company')}, sector: {cls.get('sector')}",
                 source_ids=[src], pair_ref=pair, status="verified")
    if cls.get("ask") and cls["ask"] != "undisclosed":
        EV.add_claim("ask", "founder", cls.get("company", "Unknown Co"),
                     text=f"Raising {cls['ask']}", source_ids=[src], pair_ref=pair,
                     status="verified")
    for s in cls.get("signals", []):
        EV.add_claim("fact", "founder", cls.get("company", "Unknown Co"),
                     text=f"Signal present: {s}", source_ids=[src], pair_ref=pair,
                     status="verified")

    # 2. Assessment
    tr.log("AssessmentAgent", "Draft a short behavioral assessment from deck signals.",
           "draft_assessment(signals)", None)
    questions = M.draft_assessment(cls)
    tr.steps[-1]["result"] = questions

    # 3. Profile (use provided responses, else empty placeholder)
    tr.log("ProfileAgent", "Build behavioral profile from responses + deck signals.",
           "build_profile(responses, signals)", None)
    profile = M.build_profile(responses or [], cls)
    tr.steps[-1]["result"] = profile

    # 4. Memory read -> Ranking (personalized via prior decisions + signal weights)
    tr.log("RankingAgent", "Read investor memory, rank with memory-adjusted scores.",
           "rank_shortlist(candidates, decisions, signal_weights)", None)
    decisions = load_decisions()
    inv = load_investor()
    signal_weights = inv.get("signal_weights", {})
    candidates = [
        {
            "company": cls.get("company"),
            "sector": cls.get("sector"),
            "fit": cls.get("fit"),
            "confidence": cls.get("confidence"),
            "signals": cls.get("signals", []),
        }
    ]
    ranked = M.rank_shortlist(candidates, decisions, investor=investor.get("name", "default"),
                                evidence=__import__("evidence"))
    tr.steps[-1]["result"] = ranked

    # 5. Brief + trace (Observability)
    tr.log("BriefAgent", "Write pre-meeting brief grounded in profile + memory.",
           "write_brief(...)", None)
    brief = M.write_brief(cls.get("company"), profile, ranked, investor)
    tr.steps[-1]["result"] = brief

    trace_path = tr.save()
    return {
        "pitch_id": pitch_id,
        "classification": cls,
        "assessment": questions,
        "profile": profile,
        "ranked": ranked,
        "brief": brief,
        "trace": os.path.relpath(trace_path, os.environ.get("KNOTULUS_ROOT", os.getcwd())),
    }


def main():
    seed_sample()
    out = run_pipeline(
        "We are building NeuroCo, an AI platform for radiology triage. "
        "Raising $2M seed. Contact us at founder@neuroco.com or +1 555 0100.",
        responses=[
            "When the market shifted we immediately re-focused the model on the highest-volume scan.",
            "A key hire quit before launch; I acted first to cover the gap myself.",
            "Data contradicted our thesis on uptake, so we pivoted the GTM.",
        ],
    )
    import json
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
