#!/usr/bin/env bash
# Launch helper for Knotulus Lite.
# Clears the leaked Hermes-agent PYTHONPATH so the project .venv resolves cleanly,
# and puts project/src on the path so `bash run.sh -m src.gateway` resolves
# bare imports like `import model`.
set -u
unset PYTHONPATH
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
. .venv/Scripts/activate 2>/dev/null || true
exec .venv/Scripts/python.exe "$@"
