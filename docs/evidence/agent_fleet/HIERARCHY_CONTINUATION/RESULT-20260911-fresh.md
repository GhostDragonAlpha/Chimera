# RESULT — fleet-orient-continuation-02 (fresh-system re-verification)

- Agent: subagent-worker-04 · slot 3 · generation 1 · lead glm53-lead-02 epoch 5
- Branch: `astra/tasks/fleet-orient-continuation-02` · PR base: `astra/gait-capture`
- Preregistration: `PREREGISTRATION-20260911-fresh.md` (committed BEFORE any run, 6bcb2153)

## Lineage

1. Provisioned fresh worktree at base `6e240af1` (HEAD verified = provision_base).
2. Merged `origin/astra/tasks/fleet-orient-continuation-01` @ `6a03ae91`
   (fast-forward; 4 commits: route / refine / finalize + gen3 logs). No source edits.
3. Re-verified merge safety: scoped-file diffs base↔tip `c1a1ec5a` are empty, so
   `git merge origin/astra/gait-capture` reconciled clean (merge commit `0bf09e09`);
   all 6 tracked scoped files verified byte-identical to their 6a03ae91 versions after.
4. No source file touched by this task. Only NEW-named evidence files added.

## Fresh-run table (all runs from worktree root, python 3.14.3, win32)

| # | Surface | Command | Expected (prereg) | Measured fresh | Verdict |
|---|---------|---------|-------------------|----------------|---------|
| S1 | Inherited continuation suite | `python -m unittest tools.test_orient_continuation -v` | 9/9 pass, no weakening | `Ran 9 tests ... OK`, exit 0 (`RAW_test_orient_continuation_20260911_fresh.log`) | PASS |
| S2 | Orient store suite | `python -m unittest tools.test_orient_store -v` | green | `Ran 5 tests ... OK (skipped=1)`, exit 0 (`RAW_test_orient_store_20260911_fresh.log`) | PASS |
| S4 | Fleet discover suite | `python -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v` | 0 failures, 1 Windows-symlink skip | `Ran 187 tests ... OK (skipped=1)` — skip is `test_unsafe_arguments_and_symlink_escape_refuse ... skipped 'symlink creation unavailable'`, exit 0 (`RAW_fleet_discover_20260911_fresh.log`) | PASS |
| P-A | Real CLI, store-less fresh checkout | `python tools/orient.py --json` | fail-closed refusal, no store write, unclaimed continuation | exit 3, `oriented:false`, `reason:"no term store"`, `owner:null`, `eligible_tasks:null`, store NOT created (`orient-json-fresh-20260911.txt`) | PASS |
| P-B1 | CLI --json on ephemeral COMPLETED store | driver, real `orient.main()` | hierarchy_complete true, canonical route, CONTINUATION_ACTION, unclaimed, store hash-unchanged | exit 0, all fields exact, sha256 before==after, bytes unchanged (`orient-json-fresh-20260911.txt`) | PASS |
| P-B1t | CLI text mode on completed store | driver | action + sha12 present, no write | exit 0, both present, bytes unchanged | PASS |
| P-B2 | Missing store | driver | exit 3, no file created | exact | PASS |
| P-B3 | Malformed store | driver | exit 4, bytes unchanged | exact (`json decode failed` recorded) | PASS |
| P-B4 | Synthetic store | driver, `--allow-synthetic` | exit 0, synthetic:true, no file, unclaimed | exact | PASS |
| PIN | Source pins | normalized-LF sha256 ×3 | hold unchanged, no re-pinning | `c1a5f578…` / `d9944a02…` / `3d899219…` — all equal inherited pins | PASS |

## Deviation recorded honestly (not a routing falsifier)

`ChimeraEngine/tests/test_engine_gates.py` is a standalone script (its unittest
invocation collects 0 tests). Standalone it reports **6/9 passed** with FAILs in
`test_prove_refuses_until_both_messengers_agree`, `test_next_descends_the_started_branch_first`,
`test_measured_compression_beats_declared_order`. Measured IDENTICALLY (same FAIL set)
at base `6e240af1`, inherited `6a03ae91`, and tip `c1a1ec5a` via throwaway
`git archive` exports (deleted after comparison): the failures **pre-date the routing
work**, are **outside this task's 7-file scope**, and the merged branch introduces
**zero regression** (byte-identical behavior on that suite). The file was NOT modified.
The prereg's "related suites green" expectation is therefore PARTIAL: green for
test_orient_store and the fleet discover suite; pre-existing-red-equivalent for
engine gates. This is listed under NOT_CLAIMED in the worker report.

## Preservation statement

All gen1–gen3 artifacts in `docs/evidence/agent_fleet/HIERARCHY_CONTINUATION/`
(`PREREGISTRATION.md`, `RUN_RECORD.md`, `CURRENT_RESULT.md`, `SUPERSEDED_NOTICE.md`,
`correction-gen2-20260910T234000Z.txt`, `gen3_*`, `orient-json.txt`,
`superseded-gen1-20260910/`) are **preserved untouched** and are hereby explicitly
**superseded in verification-scope** by THIS fresh run: the fresh-system re-verification
(PASS rows above) replaces them as the current evidence that the orientation/continuation
routing fix behaves truthfully, while their historical content remains part of the record.
This run only added NEW-named files (`*-20260911-fresh.*`); nothing was overwritten.

## Verdict

No preregistered falsifier fired: no fabricated ownership/readiness (owner and
eligible_tasks null on every surface), no store write during read-only orientation
(bytes hash-unchanged everywhere predicted), no weakened assertion or re-pinned hash
(9/9 inherited tests unmodified, pins byte-verified), no prior evidence overwritten,
no stale hierarchy-complete stop instruction (completed surfaces emit the canonical
continuation route). The routing fix **survives fresh-system re-verification**.

Agent: subagent-worker-04
