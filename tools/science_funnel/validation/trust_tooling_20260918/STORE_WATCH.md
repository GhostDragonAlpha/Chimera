# STORE WATCH — unreproduced-with-cause (never silently closed)

Anomaly: a single build died with `TypeError: 'set' object is not subscriptable`
at `tools/creature_graph/store.py` in `relate()` (trainer lane: 1 of 5 builds;
4 subsequent builds + all suites clean).

## Read

- `relate()` rid logic (`stem` + ordinal over `used = {r["rid"] ...}`) unchanged
  since the fail-closed commit; no subscript of a set in the logic itself.
- The only line in `relate()` that can raise exactly this TypeError is the
  `used` comprehension when an entry of `self.relations` is itself a `set`
  (`r["rid"]` on a set). List/str entries raise different messages (verified).
- Unguarded entry paths: `CreatureGraph.load()` (`g.relations =
  payload["relations"]`, no validation), `graph.graph_from()`,
  `agent_fleet/graph_workflow.unpack()` (`g.relations = deepcopy(...)`), all
  bypassing `relate()`. A corrupt edge planted by any of those (or a direct
  append) detonates at the next `relate()` — matching the single-build shape.

## Stress (bounded, recorded)

Harness: `tools/science_funnel/validation/trust_tooling_20260918/stress_relate.py`,
driven 5x via `.ps1` (mirroring the trainer lane's five-build window).

- Honest use: 5 passes x 100 builds = **500 builds**, varied sets
  (10/15, 20/30, 50/80, 100/150, 5/50 objects/relations + 5 duplicate edges
  exercising the ordinal path per build), **125 file roundtrips**
  (save/load, hash-compared, temp dirs only). **0 honest failures.**
- Adversarial injection (same process, after honest builds):
  - set edge -> `TypeError: 'set' object is not subscriptable` (exact match,
    both via append and via wholesale `relations = [...]` load shape).
  - list/str edges -> their own distinct TypeErrors (shape-specificity proof).

Conclusion: **NOT reproduced under honest use** after the bounded effort above
(coverage: in-memory builds across 5 size classes + duplicates + roundtrips).
Failure shape proven to be a corrupt set edge, not the ordinal logic.

## Hardening (minimal, honest-path unchanged)

- `tools/creature_graph/store.py`: added `StoreRefusal(code, detail)` and a
  guard at the top of `relate()` validating every existing entry is a dict
  with a non-empty string `rid` before building the `used` set. Corrupt entry
  now raises `StoreRefusal("store_corrupt_relation_edge", "relations[i] is
  <type> ... refusing to append src -rel-> dst")` naming the offending index,
  type and attempted edge — instead of the bare TypeError.
- Post-guard stress (same harness): 100 honest builds green; all four
  injections now raise the named `StoreRefusal` with index/type.
- Regression test: `tools/science_funnel/tests/test_store_relate_guard.py`
  (4 tests: honest ordinal unaffected, set/list/str/missing-rid refused by
  name, missing endpoint still ValueError). Green.

Status: **UNREPRODUCED-WITH-CAUSE** (honest stress green at 500+125; shape
proven by injection; guard + test landed). Any future recurrence will arrive
as a named refusal pointing at the corrupting path instead of a bare
TypeError.
