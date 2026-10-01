# Phase-1 sealed-cell inventory/telemetry/persistence — evidence of record

This file is the repo-local evidence of record for VERDICT 66. The canonical RAW
artifacts live at `E:\PythonChimera\agent_logs\glm53\partition_reconciliation_20260915\{phase1_evidence,phase1_runtime,phase1_regression,phase1_review}\`;
CPU results live at the worktree's `.tmp\` (`p1_inventory_result.txt`,
`p1_persistence_results.txt`). All paths are listed in the body below.
Implementation commit: `8d18ddf05e00b7955566e84e5788e338cbcf4b3a`.

The body below is a verbatim copy of the completed home-side record
(`...\phase1_evidence\EVIDENCE_RECORD.md`); sections describing the close attempt and
commit hold are historical fact as of their writing.

---

# Phase-1 Evidence Record — Sealed-Cell Fluid Inventory w (VERDICT 66)

Worker 8 (graph + evidence integration). Worktree:
`E:\ChimeraWork\codex-graph-contracts-20260915` (branch `codex/graph-contract-repairs`).
Prepared 2026-09-16 before measurement (Rule 0); completed 2026-09-16 with the measured
results below. Implementation commit: `8d18ddf05e00b7955566e84e5788e338cbcf4b3a`
(parent `38a6d156`).

---

## (a) Verdict registration (Rule-0 membrane, opened BEFORE measured results)

- **Verdict entry number:** 66 — status **OPEN** (close attempted and REFUSED by a CLI
  path restriction — refusal preserved verbatim below; the PASS case itself is fully
  measured in sections b–c. Closing is the lead's next action once the evidence-path
  handling is decided.)
- **Registered:** created_at `2026-09-16T02:54:47+00:00` (from ledger entry 66)
- **Exact command:**

```
python tools/verdict.py new --statement 'Sealed-cell state can carry an explicit per-cell fluid inventory w (initialized w := v0 at every cell creation; mass = 1000 kg/m^3 * w) with all-cell telemetry and a versioned backward-compatible seal-state snapshot, while every existing measured physical output stays identical under identical inputs.' --prediction 'CPU tests pass: fresh cells w == v0 exactly, p == 0 exactly at authored rest, all cells (incl. shin_L, cell 9) exported with {v0, vol, w, p, flags}, w invariant across ticks and deformation, kappa pressure law unchanged; SEL2 snapshots round-trip w exactly; legacy SEL1 snapshots restore via a named logged migration (legacy_no_w) without mutating source files; invalid w refused by name (seal_state_invalid_w); and the delivered 34/19/4/7 baseline checks reproduce identically on the patched engine (excluding added telemetry fields and nondeterministic timestamps).' --falsifier 'P1.1 any existing physical output changes under identical inputs vs the delivered baselines (34 state/recipe, 19 live-control, 4 cold-restart, 7 history; partition numbers) | P1.2 any sealed cell missing v0/vol/w/p/flags in telemetry, or w != v0 or p != 0 exactly at authored rest | P1.3 a legacy snapshot fails to restore, is mutated on disk, a new snapshot fails to round-trip w exactly, or invalid supplied w is silently replaced | P1.4 any route or state can create an opening/connection or move inventory between cells in Phase 1'
```

- **Registration output (verbatim):**

```
VERDICT 66 OPENED (Rule 0: statement + prediction + falsifier all named).
  statement:  Sealed-cell state can carry an explicit per-cell fluid inventory w (initialized w := v0 at every cell creation; mass = 1000 kg/m^3 * w) with all-cell telemetry and a versioned backward-compatible seal-state snapshot, while every existing measured physical output stays identical under identical inputs.
  prediction: CPU tests pass: fresh cells w == v0 exactly, p == 0 exactly at authored rest, all cells (incl. shin_L, cell 9) exported with {v0, vol, w, p, flags}, w invariant across ticks and deformation, kappa pressure law unchanged; SEL2 snapshots round-trip w exactly; legacy SEL1 snapshots restore via a named logged migration (legacy_no_w) without mutating source files; invalid w refused by name (seal_state_invalid_w); and the delivered 34/19/4/7 baseline checks reproduce identically on the patched engine (excluding added telemetry fields and nondeterministic timestamps).
  falsifier:  P1.1 any existing physical output changes under identical inputs vs the delivered baselines (34 state/recipe, 19 live-control, 4 cold-restart, 7 history; partition numbers) | P1.2 any sealed cell missing v0/vol/w/p/flags in telemetry, or w != v0 or p != 0 exactly at authored rest | P1.3 a legacy snapshot fails to restore, is mutated on disk, a new snapshot fails to round-trip w exactly, or invalid supplied w is silently replaced | P1.4 any route or state can create an opening/connection or move inventory between cells in Phase 1
  ledger: tools/verdict_registry.json
```

- Falsifiers P1.1–P1.4 are joined with `|` in the single `--falsifier` field (the CLI
  accepts exactly one falsifier string per entry).

**CLOSE ATTEMPT (2026-09-16, from the worktree) — REFUSED, preserved verbatim:**

Command run exactly as instructed (`--help` confirmed arg names first: `close number
--result {PASS,FALSIFIED,MARGINAL} --evidence EVIDENCE [--note NOTE]`):

```
python tools/verdict.py close 66 --result PASS --evidence "E:\PythonChimera\agent_logs\glm53\partition_reconciliation_20260915\phase1_evidence\EVIDENCE_RECORD.md"
```

```
Traceback (most recent call last):
  File "E:\ChimeraWork\codex-graph-contracts-20260915\tools\verdict.py", line 241, in <module>
    sys.exit(main())
             ~~~~^^
  File "E:\ChimeraWork\codex-graph-contracts-20260915\tools\verdict.py", line 213, in main
    r = L.close(a.number, a.result, a.evidence, note=a.note)
  File "E:\ChimeraWork\codex-graph-contracts-20260915\tools\verdict.py", line 115, in close
    evidence = ev.resolve().relative_to(ROOT).as_posix()
               ~~~~~~~~~~~~~~~~~~~^^^
  File "C:\Python314\Lib\pathlib\__init__.py", line 490, in relative_to
    raise ValueError(f"{str(self)!r} is not in the subpath of {str(other)!r}")
ValueError: 'E:\\PythonChimera\\agent_logs\\glm53\\partition_reconciliation_20260915\\phase1_evidence\\EVIDENCE_RECORD.md' is not in the subpath of 'E:\\ChimeraWork\\codex-graph-contracts-20260915'
exit=1
```

FINDING (not forced, per contract): `verdict.py close` (line 115) rewrites the evidence
pointer to a repo-relative path and CRASHES on any existing pointer outside the repo —
the record legitimately lives on the home side, so no meaning-preserving flag adaptation
exists. The crash precedes all state mutation; ledger verified untouched after
(`verdict.py status`: V66 OPEN, 5 closed; `git status --porcelain`: empty). PASS
justification for when the close is re-run: all four falsifier groups measured (sections
b–c), none fired.

## (b) CPU test results — MEASURED

| Suite | Expected | Measured | Raw output path |
|---|---|---|---|
| P1_INVENTORY | all PASS | **165/165 PASS** | `.tmp\p1_inventory_result.txt` (worktree) |
| P1_PERSISTENCE | 8/8 | **9/9 PASS** (adds R2b byte-level w round-trip) | `.tmp\p1_persistence_results.txt` (worktree) |
| creature_graph | 19 OK | **19 OK** | `phase1_regression\pytest_creature_graph_tests.txt` + `phase1_regression\pytest_creature_graph_standalone_reproducers.txt` |
| matter_kernel | 46/46 | **46/46 PASS** | `phase1_regression\pytest_matter_kernel.txt` |
| contracts direct | — | run delivered | `phase1_regression\test_contracts_direct.txt` |
| elastic foundation | — | run delivered | `phase1_regression\pytest_elastic_foundation.txt` |
| baseline inventory / plan | reference | n/a | `phase1_regression\BASELINE_INVENTORY.md` + `phase1_regression\COMPARISON_PLAN.md` |

Worktree raw-output tails (verbatim, read at record-completion time):

```
P1_INVENTORY: 165/165 PASS
```

```
R1 NEW-FORMAT ROUND-TRIP: PASS
R2 W ROUND-TRIP EXACTNESS: PASS
R2b EXPORT BYTES == CRAFTED INPUT: PASS
R3 LEGACY MIGRATION: PASS  [; fixture: stripped the 4 per-cell w bytes from the SEL2 export, magic rewound to 0x31534553]
R4a REFUSAL NaN w: PASS
R4b REFUSAL NEGATIVE w: PASS
R4c REFUSAL TRAILING GARBAGE: PASS
R4d REFUSAL VOLUME WITNESS (v0 off 5%): PASS
R5 RESTORE SEMANTICS: PASS
P1_PERSISTENCE: 9/9 PASS
```

History note: at scaffold time `.tmp\p1_inventory_result.txt` held a stale/pre-patch run
(27/71, missing telemetry keys). That file was regenerated on the patched engine and now
reads 165/165; the stale read is superseded and no number above is cited from it.

## (c) Runtime qualification — 34/19/4/7 baseline groups — MEASURED (window granted)

Engine binary of record: `7C63…8882E`. Windows/logs under
`E:\PythonChimera\agent_logs\glm53\partition_reconciliation_20260915\phase1_runtime\`
(`raw\`, `window\`, `window2\`, `window3\` incl. `window3\scratch\`; runbook/recovery:
`RUNBOOK.md`, `RECOVERY_LOG.md`).

| Group | Baseline size | Result | Byte-identical | Primary log |
|---|---|---|---|---|
| state/recipe | 34 | PASS ×34 | **yes** | `phase1_runtime\raw\g1_qualify.log` |
| live-control | 19 | PASS ×19 | **yes** (+0.014% worst gate vs ±1% tolerance) | `phase1_runtime\raw\g2_causal.log` |
| cold-restart | 4 | PASS 4/4 | **yes** | `phase1_runtime\raw\g3_cold.log` (+ `g3_addendum_state.log`) |
| history | 7 | PASS 7/7 | **yes**; history log IDENTICAL | `phase1_runtime\raw\g4_history.log` |

**Partition addendum (window3):** partition `n_cells=11`; report compact-sha
`8867911d…` matches the pinned fixture prefix. 11 seal_cells with w==v0 and p==0 in all
cells; w_sum 13.8246; seal_mass_kg 13824.6 (= 1000 × w_sum); `seal_w_init: "legacy_no_w"`
with stdout `seal_state: legacy SEL1 (no inventory) -> w := v0 for 4 cells`
(`raw\legacy_sel1_stdout.txt`, also `window3\runtime_round2.stdout.log` lines 38/58).
Fixture blob SES1 → new export SES2; `POST /tick_seal_state` round-trip preserved all
11 w values (`raw\addendum_roundtrip.json`, `raw\addendum_roundtrip_import_response*`,
`raw\addendum_magics.json`, `raw\addendum_final_tick_state.json`, `raw\g5_addendum.log`,
`raw\g5_addendum_retry.log`).

**Falsifier ledger: P1.1–P1.4 all measured, none fired.**

## (d) Commit

- **Commit sha:** `8d18ddf05e00b7955566e84e5788e338cbcf4b3a`
- Branch: `codex/graph-contract-repairs`; parent `38a6d156`; post-commit porcelain empty.
- Commit scope: `ChimeraEngine/engine/membrane_tick.{cpp,hpp}`,
  `ChimeraEngine/engine/tests_p1/*` (5 files), `tools/verdict_registry.json` (V66).

## (e) Limitations and notes

- Runtime window WAS granted and executed; all four groups measured (section c). No
  NOT_TESTED caveat remains.
- Group-19 worst gate moved +0.014% against a ±1% gate tolerance while all 19 recorded
  checks stayed byte-identical; recorded here verbatim for completeness (consistent with
  V66's declared exclusion of nondeterministic values).
- Independent review (Worker 7): `phase1_review\REVIEW.md` — **PASS, no BLOCKER, no
  MAJOR**; four MINOR findings, resolved pre-commit (per lead). Raw review artifacts:
  `phase1_review\cpp_diff.txt`, `seal_cells_sites.txt`, `head_state_json.txt`,
  `cur_state_json.txt`.
- Operator isolation held. For the record: port 8107 / PID 40976 was observed down at
  ~04:25Z by external cause — never touched by this work.
- The evidence record and graph-update tooling live on the home side
  (`agent_logs\glm53\partition_reconciliation_20260915\phase1_evidence\`), outside the
  repo, by design.

## (f) Graph update (executed)

- **Script:** `E:\PythonChimera\agent_logs\glm53\partition_reconciliation_20260915\phase1_evidence\graph_update_phase1.py`
  (dry-run default; `--apply --commit-sha <sha>` writes; `--claim <id>` optionally adds
  ONE because-edge; `--repo` aims the store).
- **Node id:** `bb9a6af91417261f` = `hash_node_id("Evidence",
  "phase1_sealed_cell_inventory_membrane_20260915")` (deterministic -> idempotent).
- **Pre-apply dry-run (phase-1, PREPARE):** planned single-node append 3970→3971 nodes;
  guards PASS; forbidden-claim probe REFUSED (exit 1); store verified untouched.
- **Pre-apply fix (documented, before execution):** the post-write verifier compared the
  reloaded because-edge by object identity (`is`) — a SQLite round-trip returns a new
  dict, so the check would have false-FALSIFIED. Corrected to content equality (`==`)
  before any apply run; the planned node payload is unchanged.
- **Apply (2026-09-16) — EXECUTED, verification PASSED:**

```
store target : JSON snapshot (db absent, nothing created): E:\ChimeraWork\codex-graph-contracts-20260915\Chimera\docs\chimera_dna_graph.json
graph size   : 3970 nodes / 1874 edges
planned node : type=Evidence id=bb9a6af91417261f

-- scope guards (HARD LAW) --
  ok: payload names no work.septa_leg_l / memb.septum.* / thigh_l_shin_l /
      load-bearing / experiences / pay25; no Phase-2 (openings/connections/
      transfer) vocabulary; claim endpoint (if any) exists and is in scope.

applied: node bb9a6af91417261f
post-write size: 3971 nodes / 1874 edges
verified: every pre-existing node and edge is byte-identical; exactly one node (and at most one edge) appended.
evidence node: bb9a6af91417261f
RESULT: APPLIED.
exit=0
```

- **On-disk mutation surface (git):** exactly one tracked file changed —
  `Chimera/docs/chimera_dna_graph.json`, +18 lines = the single node block (verified by
  `git diff --stat` and diff inspection). `Chimera/docs/world/dna.db` was created by the
  sqlite backend and is gitignored (`.gitignore:134`). No other file touched.
- **Provenance note:** the interface's `_stamp_provenance` string-compares the node's
  tz-aware timestamp (`…+00:00`) against its naive `_PROVENANCE_LOADED_AT`
  (`utcnow().isoformat()`), so the node was stamped `recorded_by: "legacy_pre_provenance"`
  rather than the script name. Standard interface behavior for tz-aware timestamps; the
  node's own fields carry full attribution (verdict 66, record path, commit sha).
- **Commit status:** HELD. The instructed commit 2 asserts "close verdict 66 PASS" and
  expects `tools/verdict_registry.json` in its path list; the close was refused (section
  a) and the registry is unchanged, so committing would create a commit contradicting its
  own tree. Everything preserved: snapshot modification sits in the working tree
  uncommitted, awaiting the lead's decision on the close (fix verdict.py's external-path
  handling, authorize a repo-local evidence pointer, or authorize the commit as
  graph-snapshot-only with a corrected message).
