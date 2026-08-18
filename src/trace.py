"""Agent Observability — readable reasoning-chain traces.

Every run appends a markdown trace a judge can literally open and read:
classification -> profile -> ranking rationale -> brief. This is the
"Interpretable" in ICM and the strongest answer to the Fleet track's
auditability requirement.
"""
import os
import json
import datetime

ROOT = os.environ.get("KNOTULUS_ROOT", os.getcwd())
TRACE_DIR = os.path.join(ROOT, "traces")


class Trace:
    def __init__(self, pitch_id: str):
        self.pitch_id = pitch_id
        self.steps = []
        self.started = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def log(self, agent: str, thought: str, action: str, result):
        self.steps.append(
            {"agent": agent, "thought": thought, "action": action, "result": result}
        )

    def save(self) -> str:
        os.makedirs(TRACE_DIR, exist_ok=True)
        path = os.path.join(TRACE_DIR, f"{self.pitch_id}.md")
        out = [f"# Reasoning trace — `{self.pitch_id}`", f"_started: {self.started}_", ""]
        for i, s in enumerate(self.steps, 1):
            out.append(f"## {i}. {s['agent']}")
            out.append(f"**thought:** {s['thought']}")
            out.append(f"**action:** {s['action']}")
            try:
                rendered = json.dumps(s["result"], indent=2, default=str)
            except Exception:
                rendered = str(s["result"])
            out.append(f"**result:**\n```json\n{rendered}\n```\n")
        with open(path, "w") as f:
            f.write("\n".join(out))
        return path
