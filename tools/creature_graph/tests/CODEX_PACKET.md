# CODEX PACKET SECTION — creature-graph contract repairs (Stage 3)

Prepared by F2 "graph-regressions", 2026-09-15. This section is PACKET CONTENT
ONLY — nothing here has been repaired. Every defect below is REPRODUCED on the
pinned base by a committed, runnable adversarial test; each carries a proposed
contract and a PREREGISTERED falsifier (the measurement that decides whether
the repair works, fixed before the repair is written).

## Ground truth (exact)

- Base commit: `a12bfbcc494a273b4739f86a83e19001343ee70c` (branch
  `glm53/graph-tests` in `E:\ChimeraWork\codex-limb-state-20260915`).
  `git diff 63805f41 a12bfbcc -- tools/creature_graph` is EMPTY — the defect
  line numbers verified at 63805f41 hold verbatim at this base.
- Schema under test: `2.0.0` (schema.py:135).
- Reproduction suite: `tools/creature_graph/tests/` — run
  `python run_reproduction.py` (plain) or `python -m pytest -q` (10 passed at
  base). Recorded output at base: `tests/reproduction_output.json`.
  Full per-defect narrative: `tests/REPRODUCTION_REPORT.md`.
- Suite convention: tests assert the DEFECTIVE behavior, so the suite is green
  at base and turns RED when a repair lands. `REPRODUCED` = defect live;
  `REFUTED` = measured exoneration.
- Source sha256 (first 16 hex, `sha256sum`, worktree == base for these files):
  - schema.py `214B956D9CC489CB…`
  - store.py `7D7C2713801BD0E3…`
  - build_graph.py `A31B15E217AFD4CD…`
  - graphify_projection.py `8277B1BE0C0DF14E…`
  - engine_live.py `812706213CC402E6…`
  - gaps.py `76CA396E36332B2B…`
  - queries.py `66D58B6ED6D112F5…`
  - seed/build_seed.py `C85F27E4EDB4CEEE…`

## Defects, minimal reproducers, proposed contracts, preregistered falsifiers

### D1 — schema.py:141 `PHYSICS_FIELDS` omits top-level `value`/`units`/`source`/`applicability`
- Reproducer: `tests/test_d1_physics_fields_omit_value.py` (param `value`
  4.6e-10 → 9.9e-10: content_version unchanged, evidence never stales).
- Proposed contract: a SELECTED parameter's physics IS its top-level
  value/units/source/applicability; `content_projection` must include them
  (per-kind physics key sets, or add these keys to PHYSICS_FIELDS), so any
  change changes `content_version` and stales dependent evidence.
- Preregistered falsifier: after repair, `test_d1` must flip to REFUTED —
  content_version differs AND `refresh_validation` flips `ev.conservation` to
  `stale` with `last_result="passing"` kept visible. Additional bar: objects
  whose projection did not change must keep the SAME content_version (no
  global rehash drift). If value changes still leave the version unchanged,
  the repair failed.

### D2 — build_graph.py:64 capture holds object content_versions only
- Reproducer: `tests/test_d2_relation_capture_missing.py` (delete the measured
  `carries_signal_to` relation, rebuild: capture unchanged, no stale).
- Proposed contract: evidence capture must cover the measured SUBGRAPH —
  relation identity (src, rel, dst) and direction — not only object content
  versions; removing/changing a captured relation must stale the evidence.
- Preregistered falsifier: after repair, removing the relation + rebuild must
  flip `ev.reflex_path` to `stale` (test_d2 REFUTED). Symmetric bar: two
  consecutive builds on unchanged inputs must produce identical capture bytes
  and must NOT stale anything (no false positive from rebuild ordering).

### D3 — store.py:180 `captured or {}`: empty capture passes
- Reproducer: `tests/test_d3_empty_capture_passes.py` (captured={} survives a
  physics mutation AND dep deletion, staying `passing`).
- Proposed contract: an evidence record with an empty capture must NEVER
  assert freshness — either refuse at build/load (capture is mandatory when
  `deps` is non-empty) or treat as stale-by-unknown with `last_result` kept
  visible. Absence of information must not render as absence of risk.
- Preregistered falsifier: after repair, the captured={} record must end up
  `stale` (named reason "capture empty/missing") or the API must raise
  (test_d3 REFUTED). Bar: a fully captured, unchanged record must remain
  `passing` (no false staleness).

### D4 — build_graph.py:64 unconditional re-stamp; validation/captured_utc untouched
- Reproducer: `tests/test_d4_rebuild_restamps_capture.py` (PHYSICS_FIELDS
  change + rebuild: captured rewritten, captured_utc frozen at
  2026-09-15T13:47:00Z, no stale — change becomes undetectable).
- Proposed contract: `captured` + `captured_utc` are a measurement record.
  Builds must be capture-preserving; re-stamping is an EXPLICIT recapture that
  updates `captured_utc` and marks prior validation stale. The stored pair
  must never describe two different moments.
- Preregistered falsifier: after repair, rebuild-on-changed-dep must leave
  EITHER captured == historical bytes (diff remains detectable) OR captured
  updated AND captured_utc updated AND validation stale. If captured_utc still
  reads 13:47:00Z while captured differs from the historical dict, the repair
  failed (test_d4 REFUTED).

### D5 — graphify_projection.py:36-41/48-74 sanitizer collision, docstring claims "collision-safe"
- Reproducer: `tests/test_d5_projection_id_collision.py` (`probe/a.b` and
  `probe_a_b` both export as node id `probe_a_b`; edge self-loops).
- Proposed contract: projection node ids are identity — the original→sanitized
  map must be injective (e.g. deterministic suffixing on collision) or export
  must FAIL on collision; the docstring's "collision-safe" claim must be true.
- Preregistered falsifier: after repair, exporting the collision fixture must
  either raise or produce `len(set(node_ids)) == len(nodes)` with a reversible
  id_map (test_d5 REFUTED). Bar: collision-free stores must keep byte-identical
  id_maps to the current exporter (no gratuitous renaming).

### D6 — store.py:247-248 load never compares schema_version
- Reproducer: `tests/test_d6_load_ignores_schema_version.py`
  (`0.0.9-from-the-future` loads silently, meta merely notes it).
- Proposed contract: load refuses any `schema_version` outside the supported
  set {`2.0.0`, `1.0.0-unversioned`}, with an error naming the file's version;
  migrations, if any, are explicit and versioned.
- Preregistered falsifier: after repair, loading the foreign-version store
  must raise (test_d6 REFUTED); loading a `2.0.0` store and a legacy
  `1.0.0-unversioned` store must still succeed bit-exactly
  (`graph_hash()` unchanged).

### D7 — engine_live.py:129/139/142 greedy matches[0]; :65-74 used-exclusion still greedy/unflagged
- Reproducer: `tests/test_d7_greedy_cell_matching.py` (two instances, one band,
  two cells with swapped v0: join double-books cell 0; cross_check fails BOTH
  v0 checks though a perfect assignment exists; no ambiguity flag).
- Proposed contract: ambiguous band matches must be surfaced (row/check-level
  ambiguity marker with candidate count); verification must not depend on
  greedy iteration order when a consistent assignment exists.
- Preregistered falsifier: after repair, the ambiguous fixture must either
  pass both v0 checks via a consistent assignment or fail with an EXPLICIT
  "ambiguous: 2 candidates" marker (test_d7 REFUTED); disambiguated inputs
  (distinct bands) must behave exactly as today.

### D8 — engine_live.py:61 `abs(tick.get("conserve_pct") or 1.0)`
- Reproducer: `tests/test_d8_conservation_falsy_zero.py` (exact 0.0 fails,
  1e-6 passes, all other checks green).
- Proposed contract: the check tests the VALUE (`conserve_pct is None` →
  "missing" failure detail; otherwise `abs(float(v)) < 0.01`), never its
  truthiness. Zero is the best case and must pass.
- Preregistered falsifier: after repair, conserve_pct=0.0 → ok=True;
  conserve_pct=None → failing check whose detail says missing (not a silent
  sentinel swap) (test_d8 REFUTED).

### D9 — gaps.py:49-66/73 duplicate bounds_region edges manufacture closure
- Reproducer: `tests/test_d9_duplicate_boundary_closure.py` (one wall
  registered twice: verdict flips to "physically bounded").
- Proposed contract: boundary closure counts DISTINCT membranes (dedup by
  wall object id); relation multiplicity must never multiply support. "One
  shared septum appears once per side" (the query's own note at :76-77) must
  also hold within a side.
- Preregistered falsifier: after repair, the duplicate registration must keep
  verdict "boundary pending build" with the wall listed once (test_d9
  REFUTED); a genuinely two-walled verified compartment must still reach
  "physically bounded" (no over-tightening).

### QS — query semantics (record, informs packet wording, no repair claimed)
- Record: `tests/test_qs_query_semantics.py`.
- `queries.next_work` answers "next unfinished STRUCTURE for
  press_and_response by inventory priority" (kind `work` EXCLUDED,
  queries.py:58). `gaps.q_next_ready_task` answers "next WORK ITEM for
  local_withdrawal by authored_priority" (kind==work filter, gaps.py:230).
  Different subjects, different defaults, different ranking keys — any packet
  step or planning query must name which one it means.
- Empty-risk trap: `q_evidence_at_risk` returns `[]` both when nothing was
  checkable (no evidence records) and — via D3 — when records exist but
  captured nothing; Q5 output can read "no risk" with zero evidence in the
  store. Proposed contract: risk answers must state
  `evidence_records_considered: N`.

## Repair-order note (dependency, not preference)
D3 and D4 bound what D1/D2 repairs can prove: re-stamping (D4) erases the very
diff D1/D2 repairs exist to catch, and an empty capture (D3) blinds Q5. A
repair series should land D3+D4 (capture integrity) before or with D1+D2
(capture coverage), then D6 (refuse foreign stores) before trusting any
re-verified store, then D5/D7/D8/D9 (consumers) independently. Every step is
decided by the preregistered falsifiers above — the suite decides, not taste.
