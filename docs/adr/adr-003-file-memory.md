# ADR-003: File-backed memory and traces as the differentiator

- Status: Accepted (2026-08-18)
- Deciders: E F (solo)

## Context
The Fortified Enterprise Fleet track recommends Google's managed Gemini Enterprise
Agent Platform (GEAP): a managed Agent Registry, Runtime, Memory Bank, Identity,
Gateway, Model Armor, and Observability. These are powerful but **opaque** — registry,
memory, and reasoning live inside managed black boxes a judge cannot inspect.
Knotulus's methodology (ICM) is built on *interpretable, human-editable files*.

## Decision
Reimplement each GEAP primitive as an **open, file-backed** analog:
- Registry → `registry.json`
- Memory Bank → `memory/*.json` (+ optional Firestore mirror)
- Observability → `traces/<pitch>.md` (readable reasoning chains)
- Model Armor → `screen_pii()` runs locally before any storage
- Identity/Gateway → FastAPI router with investor/founder role checks

## Consequences
- Positive: a judge can open a trace and read exactly what the agent knew and why
  it acted — the strongest possible answer to the Fleet track's "audit their
  reasoning, trust their data handling" requirement, and the literal "Interpretable"
  in ICM.
- Positive: no dependency on gated/paid GEAP services; cheap and self-contained.
- Positive: memory/traces double as the submission's evidence and docs.
- Negative: less "enterprise-grade" than managed services; horizontal scale and
  concurrency are out of scope for this demo (single-tenant, file-locked).
- Negative: Firestore mirror is optional; if omitted, the only GCP *infra* services
  are Cloud Run — still satisfies the "at least one GCP service" rule, but we
  recommend enabling Firestore to demonstrate two.

## Confirmed
Reflects the user's stated product (Knotulus as investor memory layer) and the
"interpretable by design" thesis. File layout is canonical and human-navigable.
