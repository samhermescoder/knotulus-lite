import os
import json

# Mock mode: the ADK graph runs fully offline (no credentials, no billing).
os.environ["ENABLE_GEMINI"] = "false"
os.environ["KNOTULUS_ROOT"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import src.agents.adk_agents as adk  # noqa: E402
from google.adk.agents import SequentialAgent  # noqa: E402


def test_adk_graph_is_sequential_fleet():
    # The canonical ADK artifact is a SequentialAgent orchestrating the fleet.
    assert isinstance(adk.root, SequentialAgent)
    ids = [a.name for a in adk.root.sub_agents]
    assert ids == ["intake", "assessment", "profile", "ranking", "brief", "memory"]


def test_adk_run_executes_offline():
    # Verifies "Built with Google ADK" actually RUNS (not just imported) in mock mode.
    out = adk.run(
        "We are building NeuroCo, an AI radiology triage platform. Raising $2M seed.",
        responses=["When the market shifted we immediately re-focused."],
    )
    # the runner produced a reasoning event stream
    assert out["events"] >= 1
    # real screening logic fired through the graph
    assert out["classification"]["company"] in ("NeuroCo", "Unknown Co")
    assert any(d.get("sector") == "ai" for d in out["memory"]["decisions"])
    # memory-adjusted ranking is present
    assert out["ranked"][0]["score"] > 0
