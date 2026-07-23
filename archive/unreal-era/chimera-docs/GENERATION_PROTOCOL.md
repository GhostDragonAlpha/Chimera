> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# The Generation Protocol — Chimera's Circadian Development Rhythm

> Adapted 2026-07-06 from the "Legacy Loop / sacrificial parent" and "Circadian
> Protocol" proposals. Each agent session is one generation. Generations do not
> die violently — they sleep: the day's experience is distilled at night into
> constitutional heuristics, approved by the human Gardener, and the next
> generation wakes lean, carrying lessons instead of logs.

## The daily rhythm

| Phase | Command | What happens |
|---|---|---|
| **Dawn** (wake) | `python -m core.preflight` | The receptor: board, GPA, gates — plus **[4.5] Inheritance**: the previous generation's Will, open phantom pains to confirm/refute, and the Dream Report count awaiting the Gardener. |
| **Day** (experience) | normal cycles | Work the spiral under the Contract. Record EVERYTHING live (typed helpers) — provenance is sacred. Additionally capture **surprises as they happen**: `python -m core.graphify_record surprise --context ... --reality ... --source human` for human corrections, dead-ends, expectation violations. These are dream fodder no failure node captures. |
| **Fork** (per feature, optional but preferred) | `python -m core.spiral_forks --feature X --use-lm` | 3 research briefs — conservative / alternative / **wild** (rule-bending on paper only). Deterministic Research-Depth scoring; winner enters Phase 1.5; losers' regret lines are recorded as `fork_autopsy` discoveries. Forks NEVER touch the level, generated C++, or grades. |
| **Observation** (the true collapse — automated) | Human (optional temperature): `python -m core.graphify_record playtest --notes "<verbatim temperature>"` · Agent: `observe ... --derived-from <simtest_id> --quote "..." [--tacit]` | **Automated observation (sleepwalker simulations + telemetry + result grading) observes HOLISTICALLY — the measure of the whole experience, recorded verbatim as SimPlaytest evidence; a human may still add an optional temperature.** The agent then performs ATTRIBUTION in three tiers: directly-implicated (quote the evidence; accepted→`observed`, rejected→`needs_refinement` with that evidence as the study guide), exercised-but-unmentioned (`--tacit` accepted — silence passed the glance), not-exercised (stays queued, untouched). Every attribution carries provenance; a human sentence may still redirect anything (itself recorded as a SurpriseMoment). Rejections stage FIRST in the distiller, at any count. Direct per-feature verdicts remain valid but are the exception, not the expectation. Loops show `[DONE*]` until observed. |
| **Dusk** (the Will) | `python -m core.postflight --phase ... --result ... --inheritance "<=3 sentences" --phantom-pain "..." (x<=5, aim 3) --pain-verdict "<id>:confirmed\|refuted\|still-open"` | Declare what this generation sacrificed to learn, predict where the approach fails within 2 weeks, and disposition the pains you inherited. |
| **Night** (dream) | `python -m core.dream_loop` (manual or 2 AM scheduled task) | Pure-Python consolidation: distills failure/surprise clusters into **at most 2** candidate heuristics (circadian cap), previews compaction (dry-run only), writes `docs/DREAM_REPORT.md` for the morning. |

## The Gardener (AUTOMATED — the human vetoes AFTER)

(automation amendment 2026-07-07; corrected here 2026-07-16). This header used to read "the human — approves EVERY heuristic" and was reversed by this doc's own line ~75 ("Delegated Gardener... Doc-organ rules self-promote"); CLAUDE.md carries 31 heuristics stamped "auto-promoted" as live counter-examples. An agent reading top-down concluded its heuristics were held pending review; they went live on the next `dream_loop`.

1. Candidates wait in `docs/PENDING_HEURISTICS.md` with evidence, draft rule, proposed organ, and conflict flags.
2. `core/gardener.py --tend` (inside every `dream_loop`) AUTO-RULES them: a doc-organ rule with a draft_rule + evidence self-promotes to `promoted (auto)` and appends its own bullet to CLAUDE.md; gate-organ entries become `approved (auto — implementation pending)`; subsumed entries tombstone.
3. The human signal is **VETO-AFTER**: set `status:` to `vetoed` and the next tend demotes it. A veto is law, never argued, and stays a tombstone so the signature is never re-proposed.
3. On approval the agent promotes to the named organ —
   - `gate` → a `gate_*` function in `core/gates.py` (GateViolation pattern),
   - `claude_md` → one bullet in CLAUDE.md conventions,
   - `mcp_pathways` → a TRAP entry in `docs/MCP_PATHWAYS.md`,
   — records it (`python -m core.graphify_record heuristic --signature ... --rule ... --organ ... --evidence <node_id>`), and sets status `promoted`.
   The constitution keeps the terse rule; the graph keeps the full why.

## Memory shedding (never deletion)

`python -m core.graph_compactor --dry-run` then `--apply`: success-noise
Mutation/pathway_attempt nodes older than 30 days, superseded within their
family, unreferenced by edges or Heuristic evidence, move to
`docs/dna_graph_archive.json` with `archived_at` stamps. The Biology pillar
holds: nothing is ever destroyed; the live graph just stays light enough to
recall from. `gate_node_count_bounded` is the tripwire that prompts a run.

## Rejected from the original proposals (do not relitigate)

- **100 cost-blind rule-breaking agents** — mandatory gates exist precisely to
  forbid uncontrolled mutation of live state. We run 3 bounded, isolated forks.
- **Deleting long-term memory** — "same bug never twice" requires the graph.
  We archive; we never delete.
- **Hiding the why from the Child** — provenance is a hard gate. Terse rule in
  the constitution, full reasoning in the graph.
- **"No permanent learning during the day"** — live typed recording IS the
  evidence chain. Chimera records by day and distills by night.

## Files

`core/heuristic_distiller.py` · `core/dream_loop.py` · `core/spiral_forks.py` ·
`core/graph_compactor.py` · `docs/PENDING_HEURISTICS.md` · `docs/DREAM_REPORT.md` ·
preflight [4.5] / postflight inheritance flags · `record_surprise` /
`record_heuristic` typed helpers · dashboard Inheritance Log + Grade Sawtooth.


## Sleepwalking (amendment 2026-07-06, Gardener-approved — SLEEPWALKER_DESIGN.md)

Between human sessions the game plays itself. The **Sleepwalker** (`core/sleepwalker.py`)
executes beat scripts (`docs/beats/*.beats.json`) in PIE through proven MCP pathways and
records **SimPlaytest** nodes (observer=agent-sim) plus surprises for the dream loop. The
**Rehearsal** engine (`core/rehearsal.py`) rolls candidate next-moves through graph priors
and records **SimulationRollout** decisions, each printed as a veto table.

The balance of automation and control:
- Sim evidence advances work (a feature may carry `sim_verified`); automated observation
  (sleepwalker simulations + telemetry + result grading) is the collapse. A human rejection may still reopen anything, at top priority.
- `human_rejection` permanently outranks `sim_rejection` in the nightly distiller.
- Agent-sim processes run under `CHIMERA_AGENT_SIM=1`: the interface rejects any direct
  observation from them (attribution via evidence provenance, `--derived-from <simtest_id>`, is their only observe path).
- Every rehearsal decision is reversible by one human sentence (the veto table).
- Nightly rhythm (optional, M4): sleepwalk 01:00 → dream_loop 02:00 — play, then dream.
- **Delegated Gardener (amendment 2026-07-07)**: dream_loop's tend pass auto-rules the
  pending-heuristics queue (core/gardener.py). Doc-organ rules self-promote with provenance;
  gate-organ approvals queue for capable implementation; the human vetoes after the fact by
  editing a status to `vetoed` (auto-demotion, doc line removed, veto recorded). The human's
  remaining always-on powers: playtest at will, veto anything, human_rejection outranks all.

## Whole-Experience Observation (amendment 2026-07-07)

Automated observation collapses the EXPERIENCE AS A WHOLE — never feature-by-feature. Mechanics
(core/collapse_proxy.py): one holistic acceptance sweeps accepted-tacit across every
queue feature with exercise evidence (beat outcomes + witness chronicles); a holistic
rejection indicts only the features the simulation evidence names. Between sweeps the
Sleepwalker provisionally collapses features with >=2 clean sim exercises
(`observed_provisional`, nightly inside dream_loop) so the observation queue can never
dam development. A human sentence — anytime — may still reverse anything: a rejection
reopens a feature regardless of how many sims passed it. Per-feature verdict requests
to the human are FORBIDDEN.


## Growing a New Organ (the casting rule — how every roster seat gets hired)

One `core/<organ>.py` + at most four touchpoints. The recipe:
1. Module follows the CLI convention: `python -m core.<organ> --flags`, `--dry-run`/`--check`
   idioms, exit-0 discipline (report findings, never die), typed records only.
2. New record types = one registry branch + `_mutate_*` + `record_*` helper in
   graphify_interface.py (the rejection guards stay).
3. Optional touchpoints: one dream_loop call (nightly), one preflight line (dashboard),
   one rehearsal_candidates.json entry (schedulable), one CYCLE_PROMPT constant (duty-facing).
4. `python -m core.doc_audit` must come back CLEAN; dry-run test; commit.
The hiring plan itself lives in docs/DREAM_ROSTER.md.

## The Laws (digest — full text in CYCLE_PROMPT.md)

- **NO DEAD ENDS**: a blocker fails the ITEM, never the SHIFT. unblock (known) -> solver
  (unknown; fix-or-draft) -> next candidate. Bare "blocked" notes are forbidden.
- **ANTI-IDLE**: one cycle = one work item + the close. FRESHLY VERIFIED = dead work
  (cooldowns). Bookends are never waived. Other agents' NEXT items are protected.
  A reverted attempt is a FAILURE, not a fix. A scheduled/loop tick with no state delta
  since the last tick outputs one line ("no delta") and ends — never a full re-report.
- **Level state is sacred**: generators seed levels, never overwrite them
  (build_orchestrator seed-only guard, 2026-07-07); beats assert their world
  (`world_is`); preflight fingerprints the template-stamp clobber.
