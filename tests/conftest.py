import os
import sys

# Make src/ importable for tests (model, orchestrator, etc.)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
