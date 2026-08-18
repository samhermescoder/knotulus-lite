"""ADK agent entrypoint (Google Agent Development Kit).

The hackathon requires building with Google ADK. This module registers the
Knotulus Lite fleet as an ADK agent graph: an Orchestrator root that delegates to
the Intake/Assessment/Profile/Ranking/Brief/Memory sub-agents. The same logic
also runs under the FastAPI gateway (gateway.py) for deployment; ADK is the
canonical "agent framework" deliverable.

Mock mode (ENABLE_GEMINI=false) requires no credentials; set ENABLE_GEMINI=true
+ ADC to route model calls to real Gemini 3.5 Flash via Vertex AI.
"""
import os

from google.adk import Agent, SequentialAgent

import model as M


def _make_agent(name, desc, instruction):
    return Agent(
        name=name,
        model=(M.MODEL if M.USE_GEMINI else "mock"),
        description=desc,
        instruction=instruction,
    )


root = SequentialAgent(
    name="knotulus_orchestrator",
    description="Routes a pitch through the Knotulus screening fleet.",
    sub_agents=[
        _make_agent("intake", "Read + classify inbound pitch", "Extract company/ask, classify fit, strip PII."),
        _make_agent("assessment", "Draft behavioral assessment", "Generate 3 questions from deck signals."),
        _make_agent("profile", "Build behavioral profile", "Score founder traits from responses + signals."),
        _make_agent("ranking", "Rank with memory", "Adjust scores using prior investor decisions."),
        _make_agent("brief", "Write pre-meeting brief + trace", "Produce readable brief and reasoning trace."),
        _make_agent("memory", "Persist decision", "Store meet/pass and update investor memory."),
    ],
)


def main():
    from google.adk.runners import CLI  # placeholder for adk run
    CLI().run(root)


if __name__ == "__main__":
    main()
