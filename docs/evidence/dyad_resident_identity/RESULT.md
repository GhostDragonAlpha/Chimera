# RESULT — dyad-resident-identity-01 (fresh-system re-verification)

Task: `dyad-resident-identity-01`, generation 5, slot 4, branch
`astra/tasks/dyad-resident-identity-01` (recorded base `accd15b6`, reconciled by
fast-forward merge of `origin/astra/gait-capture` at `4604de40`).
Preregistration: [PREREGISTRATION.md](PREREGISTRATION.md) (committed `bdc9f81c`
BEFORE any run of this task). Self-contained numbers: [MEASUREMENT.json](MEASUREMENT.json).

## THEORY (Rule 0, restated)

STATEMENT: reported resident identity comes only from explicit loaded-state
metadata; inference served identity remains response-derived.
PREDICTION: mocked no-model, on-disk-only, loaded, multiple-loaded, malformed
and transport-failure responses produce truthful identity or named uncertainty;
no load/pick/evict call occurs.
FALSIFIER: on-disk id reported resident, guessed served model, hidden model
selection, real inference during CPU tests, or old failed evidence overwritten.

## WHAT WAS DONE

1. Verified provisioning physically: worktree `E:\ChimeraWork\slot-04` on
   `astra/tasks/dyad-resident-identity-01` at exactly `accd15b6`, tree clean.
2. Reconciled the stale base: `git fetch origin` + merge of
   `origin/astra/gait-capture` — a fast-forward to `4604de40`, no conflicts.
3. Committed the preregistration (`bdc9f81c`) before any new run.
4. Extracted the verbatim base `senses.py`
   ([base_senses_accd15b6.py](base_senses_accd15b6.py), `git hash-object` =
   `3250ecb498df54f45fdd93db7948a793f09e420a` = the base blob) as the retained
   counterexample fixture.
5. Wrote `tools/test_dyad_resident_identity.py`: the six preregistered cases
   plus side-effect laws (only body-less `/api/v0/models` GET reads; a strict
   `eye_control` Mock asserted load/unload/evict/pick/chat_completions never
   called; `_SERVED`/`_FINISH` never written by the metadata read).
6. Ran the SAME suite against base and head.

## MEASURED VERDICTS (all CPU-synthetic; raw outputs retained verbatim)

| Run | Module under test | Command | Result |
|-----|-------------------|---------|--------|
| [base_counterexample_cpu_stderr.txt](base_counterexample_cpu_stderr.txt) | verbatim accd15b6 senses.py | env override + `python -m unittest tools.test_dyad_resident_identity -v` | FAILED (failures=3) — **exactly as preregistered** |
| [cpu_stderr.txt](cpu_stderr.txt) | branch head senses.py | `python -m unittest tools.test_dyad_resident_identity -v` | OK (6/6) |
| [related_test_dyad_model_policy_cpu_stderr.txt](related_test_dyad_model_policy_cpu_stderr.txt) | tools/test_dyad_model_policy.py | `python -m unittest tools.test_dyad_model_policy -v` | OK (13/13) |

PREDICTION case table (canonical head → all PASS; base behavior in
[MEASUREMENT.json](MEASUREMENT.json) `prediction_verification_table`):

| # | Case | Head | Base accd15b6 |
|---|------|------|---------------|
| 1 | no-model | PASS | pass |
| 2 | on-disk-only | PASS | **FAIL — returned `'on-disk-model'`: the original counterexample, reproduced fresh** |
| 3 | loaded (unambiguous) | PASS | pass |
| 4 | multiple-loaded | PASS | **FAIL — returned first loaded id (hidden selection), both state and status variants** |
| 5 | malformed | PASS | pass |
| 6 | transport-failure | PASS | pass |

Side-effect laws held in every case on both modules: only `/api/v0/models`
metadata reads, no load/pick/evict, served identity untouched. No network, no
model load, no inference, no GPU.

## THE CORRECTION, AND WHY senses.py IS NOT RE-EDITED HERE

Inspection (preregistered as METHOD before the runs): at base `accd15b6`
`resident_model()` had no production caller; the canonical history merged in
step 2 already supplies — and exceeds — the smallest coherent correction:

- base: `ids = [m.get("id") for m in payload.get("data", [])]; return ids[0] if ids else None`
- head: `_loaded_model_ids()` (explicitly-loaded-only, malformed-refusing,
  `DyadModelFailure`-named) + `return loaded[0] if len(loaded) == 1 else None`

Verbatim diff retained: [senses_base_to_head.diff](senses_base_to_head.diff).
A competing re-fix on this branch was preregistered OUT: editing the canonical
merged `senses.py` again would duplicate settled history, not correct it. This
task's deliverable is the fresh falsification, the exact preregistered
semantics, and the executable regressions the prior attempt (b8d37f1f — a
misbound review branch whose test file was a placeholder) lacked.

## RETAINED FAILURES

The base counterexample run FAILED by design and is retained verbatim
([base_counterexample_cpu_stderr.txt](base_counterexample_cpu_stderr.txt));
no test, tolerance, or expectation was weakened anywhere in this task.

## NOT_CLAIMED

- No live model load, inference, eviction, or GPU operation was performed or is claimed.
- DYAD visual acceptance NOT_CLAIMED.
- Task acceptance NOT_CLAIMED — pending lead review; slot-01 integrates after review.
- Discovery mirroring in canonical Master maintenance is the lead's call; this
  task keeps its own ledger only.
