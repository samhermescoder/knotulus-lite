# ADR-001: Submit under the Fortified Enterprise Fleet track

- Status: Accepted (2026-08-18)
- Deciders: E F (solo)

## Context
The hackathon offers three tracks: Taskmaster (single workflow agent),
Collaborative Partner (stateful tutor), and Fortified Enterprise Fleet
(multi-agent discovery, orchestration at scale, long-term state, observability,
security). Knotulus is an investor screening layer whose long-term vision is an
**investor memory layer** — it remembers what investors value, why they passed,
and which signals predicted a good conversation.

## Decision
Submit under **Fortified Enterprise Fleet**.

## Consequences
- Positive: the product's core (memory + observability) maps line-for-line onto
  the Fleet's headline primitives (Memory Bank, Agent Observability), giving a
  defensible, distinctive submission rather than a generic single-agent demo.
- Positive: the 6-agent fleet (Intake, Assessment, Profile, Ranking, Brief,
  Memory) naturally exercises Registry, Runtime, Memory, Identity, Gateway,
  Model Armor, and Observability.
- Negative: broader surface to build/demo than Taskmaster; acceptable for a
  14-day solo build because the memory layer is the flagship and the rest is
  thin wrappers.
- Alternative considered: Taskmaster framing of the same screening pipeline.
  Rejected as it would hide the memory/observability differentiator.

## Confirmed
Track lock and solo build confirmed by the user on 2026-08-18.
