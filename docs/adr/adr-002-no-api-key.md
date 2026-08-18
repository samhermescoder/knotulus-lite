# ADR-002: Dual-backend model with Application Default Credentials (no API key)

- Status: Accepted (2026-08-18)
- Deciders: E F (solo)

## Context
The hackathon requires Gemini 3.5 Flash accessed via the Gemini API or Vertex AI,
plus a Google agent framework (ADK/GenAI SDK/GenKit/Antigravity) and a GCP service.
The user hit an org-policy block creating a Gemini **API key** ("no permission to
create API key"). Google's own guidance recommends **Application Default
Credentials (ADC)** as the secure, standard method — which needs no API key.

## Decision
Build a single `model.py` with a **mock backend** (default, zero credentials) and a
**real backend** (Gemini 3.5 Flash via Vertex AI + ADC) selected by `ENABLE_GEMINI`.
The same code paths run in both modes; only the backend changes.

## Consequences
- Positive: the project runs and is fully testable **today** with zero credentials,
  so the deadline is de-risked before GCP/ADC is wired up.
- Positive: sidesteps the API-key org policy entirely; compliant with Google's
  recommended auth.
- Positive: real mode degrades gracefully to mock if model output can't be parsed.
- Negative: mock outputs are heuristic, not truly "agentic"; real mode is needed
  for a faithful demo (still required before submission).
- Negative: ADC login (`gcloud auth application-default login`) is interactive and
  must be run by the user; cannot be automated by the agent.

## Confirmed
User created the GCP project and submitted the $150 credits form; will install
gcloud + run ADC login. ENABLE_GEMINI path is wired and pending real-mode test.
