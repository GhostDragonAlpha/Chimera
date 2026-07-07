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
| **Observation** (the true collapse) | Human: `python -m core.graphify_record playtest --notes "<verbatim temperature>"` · Agent: `observe ... --derived-from <playtest_id> --quote "..." [--tacit]` | **The human observes HOLISTICALLY — a playtest temperature, a few sentences about the whole experience, recorded verbatim.** The agent then performs ATTRIBUTION in three tiers: directly-implicated (quote the human's phrase; accepted→`observed`, rejected→`needs_refinement` with their words as the study guide), exercised-but-unmentioned (`--tacit` accepted — silence passed the glance), not-exercised (stays queued, untouched). Every attribution carries provenance and is reversible by one human sentence (which is itself recorded as a human SurpriseMoment). Human rejections stage FIRST in the distiller, at any count. Direct per-feature verdicts remain valid but are the exception, not the expectation. Loops show `[DONE*]` until observed. |
| **Dusk** (the Will) | `python -m core.postflight --phase ... --result ... --inheritance "<=3 sentences" --phantom-pain "..." (x<=5, aim 3) --pain-verdict "<id>:confirmed\|refuted\|still-open"` | Declare what this generation sacrificed to learn, predict where the approach fails within 2 weeks, and disposition the pains you inherited. |
| **Night** (dream) | `python -m core.dream_loop` (manual or 2 AM scheduled task) | Pure-Python consolidation: distills failure/surprise clusters into **at most 2** candidate heuristics (circadian cap), previews compaction (dry-run only), writes `docs/DREAM_REPORT.md` for the morning. |

## The Gardener (the human — approves EVERY heuristic)

1. Candidates wait in `docs/PENDING_HEURISTICS.md` with evidence, draft rule, proposed organ, and conflict flags. **Nothing is active while pending.**
2. The human edits `status:` to `approved` or `vetoed` (vetoed entries STAY in the file as tombstones so the signature is never re-proposed).
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
- Sim evidence advances work (a feature may carry `sim_verified`); the human observation
  remains the ONLY collapse. A human rejection reopens anything, at top priority.
- `human_rejection` permanently outranks `sim_rejection` in the nightly distiller.
- Agent-sim processes run under `CHIMERA_AGENT_SIM=1`: the interface rejects any direct
  observation from them (attribution of a real human playtest is their only observe path).
- Every rehearsal decision is reversible by one human sentence (the veto table).
- Nightly rhythm (optional, M4): sleepwalk 01:00 → dream_loop 02:00 — play, then dream.
