# The Circadian Layer (Generation Protocol + Sleepwalker era)

Spec: `Chimera/docs/GENERATION_PROTOCOL.md` (incl. the Sleepwalking amendment) and
`Chimera/docs/SLEEPWALKER_DESIGN.md`. Digest:

## The human's two roles (inviolable)
- **Gardener (delegated, amendment 2026-07-07)**: `core/gardener.py --tend` (inside dream_loop)
  auto-rules `docs/PENDING_HEURISTICS.md` — doc-organ rules self-promote, gate-organ approvals
  queue for capable implementation, subsumed entries tombstone. The human vetoes after the fact
  (edit status to `vetoed` -> auto-demotion); their rejections outrank everything.
- **Observer**: the true collapse. Features finish only under human eyes. The human gives a
  HOLISTIC temperature (`graphify_record playtest --notes "<verbatim>"`); the agent ATTRIBUTES
  it across the queue (`observe --derived-from <id> --quote|--tacit`) and presents the
  attribution table for one-sentence overrules. Agents never originate verdicts.

## The automation half (balance of automation and control)
- **Sleepwalker** (`python -m core.sleepwalker --beats docs/beats/<demo>.beats.json
  --session <name>`): plays PIE beat scripts, records SimPlaytest evidence + surprises.
  Runs under CHIMERA_AGENT_SIM=1. Failures cluster as `sim_rejection` — permanently ranked
  BELOW `human_rejection` in the distiller.
- **Rehearsal** (`python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json
  --decide`): simulates candidate next-moves over graph priors, prints a VETO TABLE, records
  a SimulationRollout, and prepends a recipe-carrying NEXT item. This is duty-cycle
  **branch C2** — use it when the NEXT list is empty, BEFORE the pipeline-health fallback.
- The human may veto any rehearsal decision with one sentence; record it as
  `surprise --source human` and rerun.

## Night
- `python -m core.dream_loop` — clusters failures/surprises into <=2 staged candidates/night
  (Gardener's queue). Never promote without approval.
- Nightly rhythm ARMED: unblock 00:45 -> sleepwalk 01:00 -> dream+tend 02:15 (schtasks).
- Blockers: known -> `core.unblock --ensure all`; unknown -> `core.solver --blocker ...` (fix-or-draft;
  bare 'blocked' notes forbidden); floor work (`Groundskeeping_floor`) can never be blocked.

## Handoff invariant
Every NEXT item you write must be executable without searching: exact commands inline or a
feature name whose graph node carries the study guide, plus a skip-condition. Judgment-heavy
items are marked `capable sessions only`. An item without a recipe is a wish — do not write wishes.
