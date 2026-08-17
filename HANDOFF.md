# Knotulus Lite — HANDOFF.md (where we left off)

> **Updated:** 2026-08-18 by side-projects orchestrator (E-noch)
> Read this FIRST before working. Update it at the END of every session.

## Current state
- Branch: `main` (NOT yet git-inited — user blocked the init/commit step) | dirty: n/a
- Last work: Scaffolded project; **PIVOTED docs to the REAL Knotulus** after user
  clarified the product = investor screening layer + investor memory layer (not the
  ICM workspace/orchestrator I initially assumed). TRACK-ANALYSIS/SPEC/README now
  center on the 6-agent screening fleet + Memory Bank. Track still recommended =
  Fortified Enterprise Fleet.
- Last verified: registry.json patched & valid (lint ok); folder + md files written.

## In flight / next steps
- [ ] **LOCK THE TRACK** — Fleet recommended (memory layer = Memory Bank + Observability). Confirm vs Taskmaster leaner framing.
- [ ] `git init` + create `samhermescoder/knotulus-lite` (was blocked; awaiting user go-ahead)
- [ ] Stand up ADK multi-agent skeleton (Intake, Assessment, Profile, Ranking, Brief, Memory)
- [ ] Wire Gemini 3.5 Flash (need API key / GCP project + $150 credits claimed)
- [ ] Cloud Run deploy (scales-to-zero) + Firestore for registry/memory
- [ ] Build investor memory layer (flagship) — persists decisions, influences ranking
- [ ] Observability: reasoning traces as plain markdown in `t�races/`
- [ ] Record demo video + write-up before Sep 1 2026 08:00 GMT+8

## Open questions / decisions needed
- Solo or team? (affects fleet scope)
- GCP project + Gemini API access confirmed? $150 credits form submitted?
- Track lock: Fleet (recommended) or Taskmaster (leaner)?

## How to resume
1. `cd C:/Users/admin/Work/Hackathons/knotulus-lite`
2. Confirm track + GCP creds (ask user)
3. `adk web .` to iterate on the agent skeleton
