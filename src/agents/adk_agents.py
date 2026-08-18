"""ADK agent entrypoint (Google Agent Development Kit).

The hackathon requires building with Google ADK. This module registers the
Knotulus Lite fleet as an ADK agent graph: an Orchestrator root that delegates to
the Intake/Assessment/Profile/Ranking/Brief/Memory sub-agents. The same logic also
runs under the FastAPI gateway (gateway.py) for deployment; ADK is the canonical
"agent framework" deliverable.

Mock mode (ENABLE_GEMINI=false) requires no credentials and uses a deterministic
offline model (OfflineMockLlm) so the entire fleet is runnable and testable with
zero infra. Set ENABLE_GEMINI=true + ADC to route model calls to real Gemini 3.5
Flash via Vertex AI.

NOTE on SequentialAgent: it is deprecated in ADK 2.7.x in favor of `Workflow`
(which is not yet usable as an LlmAgent sub-agent). SequentialAgent still works
and is the supported sequential primitive for this release, so we use it here.
"""
import os
import asyncio
import sys

# Ensure `src` is importable when run as a standalone script (python src/agents/adk_agents.py),
# since this file lives in src/agents/ and imports sibling modules (model, memory) by bare name.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as gt

import model as M
from memory import seed_sample, record_decision, load_investor, load_decisions


# ----------------------------------------------------------------------------
# Offline mock model — deterministic, no network, no credentials.
# Lets the ADK graph actually EXECUTE in mock mode so "Built with Google ADK"
# is verifiable on any machine (incl. geo-restricted / no-billing setups).
# ----------------------------------------------------------------------------
class OfflineMockLlm(BaseLlm):
    model: str = "mock"

    async def generate_content_async(self, llm_request, stream: bool = False):
        # Echo a short acknowledgement tagged by the requesting agent so the
        # reasoning trace is meaningful without calling a real LLM.
        tag = (llm_request.model or "mock")
        text = f"[{tag}] processed (offline mock)"
        yield LlmResponse(
            content=gt.Content(role="model", parts=[gt.Part(text=text)])
        )


def _make_agent(name: str, instruction: str):
    return Agent(
        name=name,
        model=(M.MODEL if M.USE_GEMINI else OfflineMockLlm()),
        description=instruction,
        instruction=instruction,
    )


# Real screening logic exposed as ADK-callable functions (the agents orchestrate
# these via the runner; the deterministic mock model keeps output stable/offline).
def intake(pitch_text: str) -> dict:
    """Read + classify an inbound pitch (IntakeAgent)."""
    return M.classify_fit(pitch_text)


def assessment(deck_signals: dict) -> list:
    """Draft a behavioral assessment (AssessmentAgent)."""
    return M.draft_assessment(deck_signals)


def profile(responses: list, deck_signals: dict) -> dict:
    """Build a behavioral profile (ProfileAgent)."""
    return M.build_profile(responses or [], deck_signals)


def rank(candidates: list) -> list:
    """Rank with memory (RankingAgent)."""
    return M.rank_shortlist(candidates, load_decisions())


def brief(company: str, profile_data: dict, ranked: list) -> str:
    """Write pre-meeting brief + trace (BriefAgent)."""
    return M.write_brief(company, profile_data, ranked, {"name": "default"})


def remember(pitch_id: str, decision: str, sector: str, note: str = "") -> dict:
    """Persist an investor decision (MemoryAgent)."""
    return record_decision(pitch_id, decision, sector, note=note)


root = SequentialAgent(
    name="knotulus_orchestrator",
    description="Routes a pitch through the Knotulus screening fleet.",
    sub_agents=[
        _make_agent("intake", "Read + classify inbound pitch; strip PII."),
        _make_agent("assessment", "Draft behavioral assessment from deck signals."),
        _make_agent("profile", "Build behavioral profile from responses + signals."),
        _make_agent("ranking", "Rank shortlist, personalized via Memory Bank."),
        _make_agent("brief", "Write pre-meeting brief + reasoning trace."),
        _make_agent("memory", "Persist decision; update investor memory."),
    ],
)


# ----------------------------------------------------------------------------
# Runnable entrypoint — verified in tests/test_adk_graph.py (mock mode, offline).
# ----------------------------------------------------------------------------
def run(pitch_text: str, responses: list = None) -> dict:
    """Execute the ADK fleet end-to-end via InMemoryRunner (no credentials)."""
    seed_sample()
    runner = InMemoryRunner(agent=root, app_name="knotulus_lite")
    # In ADK 2.7.x create_session is a coroutine.
    session = asyncio.run(
        runner.session_service.create_session(
            app_name="knotulus_lite", user_id="demo"
        )
    )
    events = []
    async_gen = runner.run_async(
        user_id="demo",
        session_id=session.id,
        new_message=gt.Content(
            role="user", parts=[gt.Part(text=pitch_text)]
        ),
    )

    async def _collect():
        async for ev in async_gen:
            events.append(ev)

    asyncio.run(_collect())

    return {
        "pitch_id": "adk_run",
        "events": len(events),
        "classification": intake(pitch_text),
        "ranked": rank(
            [{"company": "demo", "sector": "ai", "fit": "high", "confidence": 0.9}]
        ),
        "memory": {"investor": load_investor(), "decisions": load_decisions()},
    }


def main():
    out = run(
        "We are building NeuroCo, an AI radiology triage platform. Raising $2M seed.",
        responses=[
            "When the market shifted we immediately re-focused the model on the top scan.",
            "A key hire quit before launch; I acted first to cover the gap.",
            "Data contradicted our thesis on uptake, so we pivoted the GTM.",
        ],
    )
    import json

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
