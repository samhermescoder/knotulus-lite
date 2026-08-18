#!/usr/bin/env bash
# Launch helper for Knotulus Lite.
# Clears the leaked Hermes-agent PYTHONPATH so the project .venv resolves cleanly.
set -u
unset PYTHONPATH
cd "$(dirname "$0")"
. .venv/Scripts/activate 2>/dev/null || true
exec .venv/Scripts/python.exe "$@"
