# The Circadian Layer (Generation Protocol + Sleepwalker era)

Spec: `Chimera/docs/GENERATION_PROTOCOL.md` (incl. the Sleepwalking amendment) and
`Chimera/docs/SLEEPWALKER_DESIGN.md`. Digest:

## Verification is AUTOMATED (full-automation amendment 2026-07-07 — human verification removed)
- **Gardener (delegated)**: `core/gardener.py --tend` (inside dream_loop) auto-rules
  `docs/PENDING_HEURISTICS.md` — doc-organ rules self-promote, gate-organ approvals queue for
  capable implementation, subsumed entries tombstone. Automated rejection is final. (A human
  MAY veto-after by editing a status to `vetoed` -> auto-demotion, but nothing waits for one.)
- **Observer (whole-experience)**: the AUTOMATED system rules on the EXPERIENCE AS A WHOLE via
  sleepwalker simulations + telemetry + result grading — never feature-by-feature guessing.
  A SimPlaytest is the temperature -> quote-tier attributions -> `core.collapse_proxy
  --from-simtest <id> --valence <v>` sweeps accepted-tacit across everything exercised. Nightly
  `--tend` collapses sim-evidenced features. The automated observation IS the measure; a human
  sentence may still redirect it, but the system finishes features on its own.

## The automation half (balance of automation and control)
- **Sleepwalker** (`python -m core.sleepwalker --beats docs/beats/<demo>.beats.json
  --session <name>`): plays PIE beat scripts, records SimPlaytest evidence + surprises.
  Runs under CHIMERA_AGENT_SIM=1. Failures cluster as `sim_rejection` — the automated
  measure; an optional human sentence may still redirect, but does not gate.
- **Rehearsal** (`python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json
  --decide`): simulates candidate next-moves over graph priors, prints a VETO TABLE, records
  a SimulationRollout, and prepends a recipe-carrying NEXT item. This is duty-cycle
  **branch C2** — use it when the NEXT list is empty, BEFORE the pipeline-health fallback.
- The human may veto any rehearsal decision with one sentence; record it as
  `surprise --source human` and rerun.

## Night
- `python -m core.dream_loop` — clusters failures/surprises into <=2 staged candidates/night
  (Gardener's queue). `--tend` auto-promotes doc-organ rules; gate-organ rules queue for a
  capable cycle. No human approval step.
- Nightly rhythm ARMED: unblock 00:45 -> sleepwalk 01:00 -> dream+tend 02:15 (schtasks).
- Blockers: known -> `core.unblock --ensure all`; unknown -> `core.solver --blocker ...` (fix-or-draft;
  bare 'blocked' notes forbidden); floor work (`Groundskeeping_floor`) can never be blocked.

## Handoff invariant
Every NEXT item you write must be executable without searching: exact commands inline or a
feature name whose graph node carries the study guide, plus a skip-condition. Judgment-heavy
items are marked `capable sessions only`. An item without a recipe is a wish — do not write wishes.
