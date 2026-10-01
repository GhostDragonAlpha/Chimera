# REPRODUCTION_REPORT — F2 graph-regressions — 2026-09-15

Agent: F2 "graph-regressions" (GLM 5.3 fleet, graph-reliability assignment).
Base: `a12bfbcc494a273b4739f86a83e19001343ee70c` (branch `glm53/graph-tests`),
worktree `E:\ChimeraWork\codex-limb-state-20260915`. Schema under test 2.0.0.
No commits touched `tools/creature_graph` between the line-verification tip
`63805f41` and this base (measured: `git diff 63805f41 a12bfbcc --stat --
tools/creature_graph` is empty), so the D3 defect line numbers hold verbatim.

**Verdict convention.** Every test states the architectural contract
(expected-honest) FIRST, then records observed behavior. `REPRODUCED` = the
observed behavior violates the contract — the defect is live. `REFUTED` = the
measurement exonerates the defect (an exoneration is a finding, never a
failure). The pytest wrappers assert `REPRODUCED`, so the suite is GREEN on
this defective base and turns RED the moment a repair lands — that red is the
signal to re-run and update this report.

**Run it:**
```
cd tools/creature_graph/tests
python run_reproduction.py          # plain runner, writes reproduction_output.json
python -m pytest -q                 # same tests under pytest (10 passed at base)
```

**Isolation.** All inputs are committed fixtures (`fixtures/authored_min/`,
copied to per-test temp dirs before any mutation); the canonical
`data/creature_graph.json` is never read by the suite and `save()`/`export()`
are always pointed at temp paths. Machine evidence: `reproduction_output.json`
(committed, this directory).

**RESULT: 9/9 defects REPRODUCED** (prediction was 9/9; no exoneration). One
additional query-semantics record (QS) — not a defect claim — documenting that
`queries.next_work` and `gaps.q_next_ready_task` are different queries and
where an empty risk query passes despite absent evidence.

---

## D1 — PHYSICS_FIELDS omits top-level `value`/`units`/`source`/`applicability`
**Verdict: REPRODUCED.** Test: `test_d1_physics_fields_omit_value.py`.

- Input (immutable): `fixtures/authored_min/` built through the REAL
  `build_graph.build()`; `param.water_compressibility` carries top-level
  `value: 4.6e-10` exactly as the seed authors parameters; `ev.conservation`
  (passing) captured it at build time.
- Expected-honest: `value` is the parameter's physics (schema.py:139-142 says a
  change to physics-relevant fields "stales dependent validation evidence").
  Changing 4.6e-10 → 9.9e-10 Pa⁻¹ MUST change `content_version` and MUST stale
  `ev.conservation` (validation → `stale`, `last_result` keeps `passing`
  visible).
- Observed: `content_version` **identical** before/after (`PHYSICS_FIELDS` =
  physical/spatial/geometry/status/attachments/unknowns — schema.py:141 — and
  `content_projection` picks only those keys, schema.py:220-223);
  `stale_evidence()` → `[]`; `refresh_validation()` flipped `[]`; validation
  remains `passing`.
- Consequence chain: store.py:185 compares content_versions, so a
  physical-value change can never fire the staleness it exists for.
- Contract refs: schema.py:139-142, 212-216, 220-223; store.py:37-40, 176-189.

## D2 — capture records object content_versions only; relations never stale
**Verdict: REPRODUCED.** Test: `test_d2_relation_capture_missing.py`.

- Input: same fixture; `ev.reflex_path` measured a signal PATH that includes
  the `carries_signal_to` relation sensor→pathway (authored in
  `fixtures/authored_min/relations.json`). Then a full second build runs on a
  copy whose `relations.json` has that relation deleted (objects byte-identical).
- Expected-honest: removing a relation the measurement covered MUST stale the
  evidence (store.py:26-29: "any of the above → stale (a physics-relevant
  input changed)").
- Observed: `ev["captured"]` is `{object_id: content_version}` only
  (build_graph.py:59-64) — relation identity is not representable in the
  capture; after rebuild `captured` is unchanged, `refresh_validation()` →
  `[]`, validation remains `passing`, and the build raises no warning.
- Contract refs: build_graph.py:57-64; store.py:26-29, 166-189.

## D3 — `captured or {}`: empty capture passes; dep deletion invisible
**Verdict: REPRODUCED.** Test: `test_d3_empty_capture_passes.py`.

- Input: fixture-built store, then the evidence reset to exactly what the seed
  AUTHORS — `"captured": {}` (seed/build_seed.py:807) — saved to a temp store
  and reloaded through `CreatureGraph.load` (the store API's only view).
- Expected-honest: an empty capture MUST NOT pass. With no captured versions,
  staleness is UNKNOWABLE; honest behavior is refuse-to-assert (flip to stale
  with a named "capture missing/empty" reason, or raise) — never a clean bill
  of health.
- Observed: with `captured == {}` the record stayed `passing` through (a) a
  physics-relevant mutation (`spatial.v0_m3` 0.287914 → 0.5, a PHYSICS_FIELDS
  member) and (b) **complete deletion of the dep object**;
  `stale_evidence()` → `[]` in both; `refresh_validation()` flipped `[]` in
  both. `ev.get("captured") or {}` (store.py:180) turns absence of information
  into absence of risk.
- Contract refs: store.py:176-189, 191-208; seed/build_seed.py:807.

## D4 — unconditional re-stamp rewrites historical capture; captured_utc lies
**Verdict: REPRODUCED.** Test: `test_d4_rebuild_restamps_capture.py`.

- Input: two builds of the fixture — v1 as committed, v2 with
  `inst.band.feet.spatial.v0_m3` 0.287914 → 0.5 (a PHYSICS_FIELDS member, so
  this defect is independent of D1).
- Expected-honest: `captured` + `captured_utc` are a MEASUREMENT RECORD. A
  rebuild MUST NOT rewrite what the evidence measured; if it re-stamps, it
  MUST update `captured_utc` and/or stale the evidence. The pair must never
  describe two different moments.
- Observed: rebuild silently rewrote `captured` to the NEW versions
  (`build_graph.py:64` is unconditional) while `captured_utc` still reads
  `2026-09-15T13:47:00Z` (the seed's historical moment, untouched);
  `refresh_validation()` → `[]`; validation remains `passing`. After the
  rebuild the v0 change is **undetectable through the store API** — the
  re-stamp destroyed the very diff staleness exists to catch.
- Real-world instance: `ev.band_seal_conservation` (captured 13:47:00Z) was
  re-committed by the 14:31:44Z rebuild recorded in DISCOVERY_EVIDENCE D5.
- Contract refs: build_graph.py:57-64; store.py:191-208.

## D5 — projection sanitizer collision; docstring claims "collision-safe"
**Verdict: REPRODUCED.** Test: `test_d5_projection_id_collision.py`.

- Input: in-memory store with two distinct stable ids `probe/a.b` and
  `probe_a_b`, one `inside` edge between them; `graphify_projection.export()`
  with the output repointed to a temp dir (the real projection directory is
  never touched).
- Expected-honest: the projection must preserve object identity across the
  boundary (graphify_projection.py:9-12); either `_sanitize` is injective or
  export refuses/renames a collision EXPLICITLY (the docstring at :37 claims
  "collision-safe").
- Observed: export succeeded; the projection carries **2 nodes with the same
  id `probe_a_b`**; `id_map` folds both originals onto one sanitized id; the
  `inside` edge now has identical source and target. No error, no warning, no
  duplicate check anywhere in the export loop (:48-74).
- Contract refs: graphify_projection.py:9-12, 36-41, 48-74.

## D6 — load records `loaded_schema_version` without comparing
**Verdict: REPRODUCED.** Test: `test_d6_load_ignores_schema_version.py`.

- Input: fixture store saved to a temp path, persisted `schema_version`
  rewritten to `0.0.9-from-the-future`.
- Expected-honest: `load` MUST refuse (or explicitly migrate) a store whose
  schema_version is outside the supported set {`2.0.0`, `1.0.0-unversioned`}
  (schema.py:135-137 exists precisely so this is decidable). Writing the
  version into meta is bookkeeping, not a check.
- Observed: `CreatureGraph.load` succeeded with no error;
  `meta.loaded_schema_version = "0.0.9-from-the-future"` (store.py:247-248 —
  recorded, never compared); all objects served as-is; no migration.
- Contract refs: store.py:238-249; schema.py:135-137.

## D7 — runtime-to-graph matching chooses ambiguous cells greedily
**Verdict: REPRODUCED.** Test: `test_d7_greedy_cell_matching.py`.

- Input: two verified instances claiming the SAME band `[0.0, 0.338]` (v0_A =
  0.287914, v0_B = 0.105210) and two live cells at that band carrying each
  other's v0 — a perfect assignment exists (_a→cell1, _b→cell0).
- Expected-honest: ambiguous band matches MUST be surfaced (e.g. `match:
  "ambiguous: 2 candidates"`); a verification verdict must not depend on
  instance iteration order when a consistent assignment exists.
- Observed: `map_cells_to_instances` (engine_live.py:129/139/142) double-books
  live cell 0 — both rows get `engine_cell_index=0`, cell 1 unused, both rows
  say `match: "by band geometry"`, no ambiguity flag. `cross_check`
  (:65-74) excludes used cells but is STILL greedy `matches[0]`: instance
  order decides, and **both** v0 checks FAIL although the consistent
  assignment exists — a wrong-cell assignment decided pass/fail, silently.
- Contract refs: engine_live.py:55-86, 107-153.

## D8 — exact conservation zero fails via `or 1.0`
**Verdict: REPRODUCED.** Test: `test_d8_conservation_falsy_zero.py`.

- Input: store with no verified instances; ticks with `conserve_pct` exactly
  `0.0` and `1e-6` (every other field identical and green).
- Expected-honest: `|conserve_pct| < 0.01` must pass INCLUDING exactly `0.0`
  — the BEST physical outcome; absence (`None`) must be reported as missing,
  not substituted with a sentinel.
- Observed: `engine_live.py:61` `abs(tick.get("conserve_pct") or 1.0)` —
  `conserve_pct=0.0` → check `ok=False` (sentinel 1.0 substituted); the same
  report's every other check is green, so the falsy-zero alone fails a
  perfectly conserved world. `conserve_pct=1e-6` → `ok=True`.
- Contract refs: engine_live.py:59-62.

## D9 — duplicate boundary edges manufacture closure
**Verdict: REPRODUCED.** Test: `test_d9_duplicate_boundary_closure.py`.

- Input: one compartment (verified), exactly ONE physical wall
  (`memb.septum.solo`, geometry_built, not placeholder), the wall's
  `bounds_region` relation registered (a) once and (b) twice — multiplicity
  is preserved BY DESIGN (store.py:63-72).
- Expected-honest: "physically bounded" (gaps.py:73) must require DISTINCT
  bounding walls — an enclosure needs more than one wall; one wall registered
  twice is one wall. With one wall the verdict must be `boundary pending
  build` regardless of registration count.
- Observed: one registration → `boundary pending build`; the SAME wall
  registered twice → **`physically bounded`**. gaps.py:49-66 emits one row
  per relation (no wall-id dedup) and :66 sums `n_support` over rows, so
  duplicate edges alone manufacture closure; `bounding_membranes` lists the
  same membrane twice.
- Contract refs: gaps.py:37-79; store.py:63-72.

---

## QS — query semantics record (not a defect claim)
Test: `test_qs_query_semantics.py`. Verdict basis: all documented divergences
and traps observed as described.

**`queries.next_work` (queries.py:48-92)** answers: *which unfinished
STRUCTURES transitively enable the experience, have all prerequisites ≥
geometry_built, and lack a passing falsifier* — ranked by inventory priority
(P0/P1/P2), then build_rank, then order_hint, then id. It **excludes**
kind `work` at :58, so a work item can never be its answer. Default
experience: `experience.press_and_response`.

**`gaps.q_next_ready_task` (gaps.py:224-242)** answers: *which WORK ITEM is
ready now, by authored_priority* — it filters `kind == "work"` at :230, so a
structure can never be its answer; its closure additionally follows
requires_implementation dependents (`q_blockers_for`, gaps.py:141-184), and
`verified` short-circuits at :172 (next_work skips verified at :60 with no
such closure difference). Default experience: `experience.local_withdrawal`.

**Observed divergence on one store:** `next_work` → `['inst.comp.shin_l']`
(a structure); `q_next_ready_task` → `work.partition_leg_l` (a work item).
Same store, both read as "what's next" — two different questions with
different subjects, defaults, and ranking keys.

**The empty-risk trap (gaps.py:191-217 + store.py:176-189):**
- With ZERO evidence records in the store, `q_evidence_at_risk` returns `[]` —
  indistinguishable from "checked, nothing at risk". In `run_all_six` (Q5)
  this renders as a normal answer: an empty risk query passes despite absent
  evidence.
- With a hollow record (exists, `captured: {}`), the same query NAMES it as at
  risk — while its staleness machinery is inert: `stale_evidence` → `[]` and
  `refresh_validation` flips nothing even after a real PHYSICS_FIELDS change
  to the measured object. The risk query promises a protection the capture
  does not implement (D3 inside Q5).

---

## Shared-worktree note (isolation evidence)
While this suite ran, sibling lanes worked in the same worktree: F3's writes
appeared (authored data edits, a rebuilt store, `graphify_consumer.py`) and
the worktree HEAD was moved to `glm53/graph-consumer` with two commits landed
mid-task (`1f3c062c` lead, `c99d6b6b` F3). None of it is this suite's output —
the suite only writes per-test temp dirs and `tests/`, and it never reads the
canonical store, so all measurements above are unaffected (they are pinned to
base `a12bfbcc`, where no graph-source commit differs from `63805f41`). This
commit contains `tools/creature_graph/tests/` ONLY and was made on the
`glm53/graph-tests` ref through a temporary linked worktree, leaving the
shared worktree exactly as the sibling lanes hold it (branch, files, and
in-flight state untouched).
