"""Showcase script — demonstrates the investor memory layer shifting a ranking.

Runs in mock mode (no credentials). Seeds a prior PASS in `ai`, then runs a new
ai pitch and shows the traceable drop in rank score + the readable reasoning
trace. This is the 3-minute demo narrative for the hackathon video.
"""
import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["ENABLE_GEMINI"] = "false"
os.environ["KNOTULUS_ROOT"] = ROOT

import memory
from orchestrator import run_pipeline

PITCH = open(os.path.join("fixtures", "sample_pitch.txt")).read()
RESP = json.load(open(os.path.join("fixtures", "sample_responses.json")))

print("=" * 60)
print("STEP 1 — Investor memory BEFORE (note: a prior PASS in 'ai')")
print("=" * 60)
memory.seed_sample()
inv = memory.load_investor()
print(json.dumps(inv, indent=2))

print("\n" + "=" * 60)
print("STEP 2 — New ai pitch arrives; fleet screens it")
print("=" * 60)
out = run_pipeline(PITCH, responses=RESP, investor={"name": "partner-1"})
print(f"company : {out['classification']['company']}")
print(f"fit     : {out['classification']['fit']}")
rank = out["ranked"][0]
print(f"score   : {rank['score']}  (base high=0.9, memory-adjusted)")
print(f"why     : {rank['rationale']}")
print(f"trace   : {out['trace']}")

print("\n" + "=" * 60)
print("STEP 3 — Read the reasoning trace (Observability primitive)")
print("=" * 60)
trace_path = os.path.join(os.environ["KNOTULUS_ROOT"], out["trace"])
print(open(trace_path).read()[:1200], "...\n(truncated — full trace in %s)" % trace_path)
