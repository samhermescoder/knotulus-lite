"""LLM backend abstraction for Knotulus Lite.

Mock by default so the entire fleet runs with zero credentials. Set
ENABLE_GEMINI=true (plus GOOGLE_CLOUD_PROJECT) to use real Gemini 3.5 Flash via
Vertex AI + Application Default Credentials (ADC) — no API key required.

Every function has a mock (heuristic) path and a real (Gemini) path. The real
path falls back to mock if the model output can't be parsed, so the system never
hard-fails.

Model Armor note: screen_pii() is a local guardrail that ALWAYS runs, even in
real mode, before any text reaches memory or traces.
"""
import os
import re
import json

USE_GEMINI = os.environ.get("ENABLE_GEMINI", "false").lower() == "true"
PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - optional dep
    genai = None


# ----------------------------------------------------------------------------
# Local guardrail (Model Armor analog) — always runs, no LLM
# ----------------------------------------------------------------------------
def screen_pii(text: str) -> str:
    """Redact emails and phone numbers before storage or tracing."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
    text = re.sub(
        r"\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
        "[PHONE]",
        text,
    )
    return text


# ----------------------------------------------------------------------------
# Real (Gemini) helpers
# ----------------------------------------------------------------------------
def _gem_json(prompt: str, system: str = "") -> dict:
    if genai is None:
        raise RuntimeError("google-genai not installed")
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    cfg = types.GenerateContentConfig(
        system_instruction=system, response_mime_type="application/json"
    )
    resp = client.models.generate_content(model=MODEL, contents=prompt, config=cfg)
    return json.loads(resp.text or "{}")


# ----------------------------------------------------------------------------
# 1. classify_fit — IntakeAgent
# ----------------------------------------------------------------------------
def classify_fit(text: str) -> dict:
    clean = screen_pii(text)
    if not USE_GEMINI:
        return _mock_classify(clean)
    try:
        sys = ("You are the Intake agent of an investor screening system. "
               "Extract company name, the funding ask, sector, and a fit rating "
               "(high/medium/low) with a confidence in [0,1]. Respond JSON.")
        return _gem_json(f"Pitch email:\n{clean}", sys)
    except Exception:
        return _mock_classify(clean)


def _mock_classify(text: str) -> dict:
    t = text.lower()
    company = "Unknown Co"
    m = re.search(r"(?:building|founded|start(?:ed|ing)?|we are)\s+([A-Z][\w\-]+)", text)
    if m:
        company = m.group(1)
    ask = "undisclosed"
    m = re.search(r"\$\s*([\d\.]+)\s*(m|million|k|thousand|b|bn)?", t)
    if m:
        unit = m.group(2) or ""
        ask = f"${m.group(1)}{unit}"
    sectors = ["ai", "saas", "fintech", "health", "climate", "logistics",
               "hr", "security", "education", "bio"]
    sector = next((s for s in sectors if s in t), "other")
    score = 0
    if sector in ("ai", "saas", "fintech", "bio", "health"):
        score += 2
    if ask != "undisclosed":
        score += 1
    if "seed" in t or "series" in t:
        score += 1
    fit = "high" if score >= 3 else "medium" if score >= 1 else "low"
    return {
        "company": company,
        "ask": ask,
        "sector": sector,
        "fit": fit,
        "confidence": round(min(0.99, 0.6 + 0.1 * score), 2),
    }


# ----------------------------------------------------------------------------
# 2. draft_assessment — AssessmentAgent
# ----------------------------------------------------------------------------
def draft_assessment(deck_signals: dict) -> list:
    sector = deck_signals.get("sector", "your")
    if not USE_GEMINI:
        return [
            f"Describe a time the {sector} market shifted unexpectedly — how did you respond?",
            "A key hire quit two weeks before launch. What did you do first?",
            "What belief about your business did data later contradict, and what did you change?",
        ]
    try:
        sys = ("You are the Assessment agent. Given deck signals, write 3 short "
               "behavioral questions for a founder. Respond JSON: {\"questions\": [...]}.")
        return _gem_json(f"deck_signals: {json.dumps(deck_signals)}", sys)["questions"]
    except Exception:
        return draft_assessment.__wrapped__(deck_signals) if hasattr(draft_assessment, "__wrapped__") else [
            f"Describe a time the {sector} market shifted unexpectedly — how did you respond?",
            "A key hire quit two weeks before launch. What did you do first?",
            "What belief about your business did data later contradict, and what did you change?",
        ]


# ----------------------------------------------------------------------------
# 3. build_profile — ProfileAgent
# ----------------------------------------------------------------------------
def build_profile(responses: list, deck_signals: dict) -> dict:
    if not USE_GEMINI:
        return _mock_profile(responses, deck_signals)
    try:
        sys = ("You are the Profile agent. From founder assessment responses and "
               "deck signals, produce a behavioral profile with trait scores in "
               "[0,1] and a one-line summary. Respond JSON.")
        return _gem_json(
            f"responses: {json.dumps(responses)}\nsignals: {json.dumps(deck_signals)}",
            sys,
        )
    except Exception:
        return _mock_profile(responses, deck_signals)


def _mock_profile(responses: list, deck_signals: dict) -> dict:
    t = " ".join(responses).lower()
    coachability = 0.85 if ("data" in t and ("contradict" in t or "wrong" in t)) else 0.5
    decisiveness = 0.8 if ("immediately" in t or "first" in t or "acted" in t) else 0.5
    risk = 0.75 if ("risk" in t or "bet" in t or "pivot" in t) else 0.5
    vision = 0.7 if len(responses) >= 3 else 0.4
    return {
        "traits": {
            "coachability": round(coachability, 2),
            "decisiveness": round(decisiveness, 2),
            "risk_tolerance": round(risk, 2),
            "vision_clarity": round(vision, 2),
        },
        "summary": f"Founder shows {'high' if coachability > 0.7 else 'mixed'} coachability "
                   f"and {'decisive' if decisiveness > 0.7 else 'deliberate'} execution style.",
    }


# ----------------------------------------------------------------------------
# 4. rank_shortlist — RankingAgent (uses Memory Bank)
# ----------------------------------------------------------------------------
def rank_shortlist(candidates: list, decisions: list) -> list:
    """Score candidates, adjusting for past investor decisions (Memory Bank)."""
    for c in candidates:
        base = {"high": 0.9, "medium": 0.6, "low": 0.3}.get(c.get("fit", "low"), 0.3)
        adj = 0.0
        reasons = []
        for d in decisions:
            if d.get("sector") == c.get("sector"):
                if d.get("decision") == "pass":
                    adj -= 0.2
                    reasons.append(f"prior PASS in {c['sector']} ({d.get('note','')})")
                elif d.get("decision") == "meet":
                    adj += 0.1
                    reasons.append(f"prior MEET in {c['sector']}")
        c["score"] = round(min(0.99, max(0.01, base + adj)), 3)
        c["rationale"] = reasons
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates


# ----------------------------------------------------------------------------
# 5. write_brief — BriefAgent
# ----------------------------------------------------------------------------
def write_brief(company: str, profile: dict, ranked: list, investor: dict) -> str:
    c = ranked[0] if ranked else {"score": 0, "rationale": []}
    if not USE_GEMINI:
        return _mock_brief(company, profile, c, investor)
    try:
        sys = ("You are the Brief agent. Write a tight pre-meeting brief for an "
               "investor: 3 bullets on what to probe, grounded in the profile and "
               "the ranking rationale. Plain text.")
        return _gem_json(
            f"company: {company}\nprofile: {json.dumps(profile)}\nrank: {json.dumps(c)}",
            sys,
        ).get("brief", _mock_brief(company, profile, c, investor))
    except Exception:
        return _mock_brief(company, profile, c, investor)


def _mock_brief(company, profile, ranked, investor) -> str:
    traits = profile.get("traits", {})
    lines = [
        f"PRE-MEETING BRIEF — {company}",
        f"Rank score: {ranked.get('score')}  |  fit: {ranked.get('fit','?')}",
    ]
    if ranked.get("rationale"):
        lines.append("Memory signal: " + "; ".join(ranked["rationale"]))
    lines.append("Probe:")
    if traits.get("coachability", 0) < 0.7:
        lines.append(" - Push on a time data contradicted them — do they update?")
    else:
        lines.append(" - They self-correct well; test with a contrary market signal.")
    if traits.get("decisiveness", 0) < 0.7:
        lines.append(" - Ask who makes the call under time pressure.")
    else:
        lines.append(" - Delegate a live decision scenario in the meeting.")
    lines.append(f" - {profile.get('summary','')}")
    return "\n".join(lines)
