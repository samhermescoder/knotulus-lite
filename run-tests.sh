#!/usr/bin/env bash
# Run the pytest suite in mock mode (no credentials needed).
set -u
unset PYTHONPATH
export ENABLE_GEMINI=false
export KNOTULUS_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$(dirname "$0")"
. .venv/Scripts/activate 2>/dev/null || true
exec .venv/Scripts/python.exe -m pytest tests/ -v
