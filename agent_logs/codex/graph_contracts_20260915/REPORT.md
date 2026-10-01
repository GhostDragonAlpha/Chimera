# Graph contract repairs — 2026-09-15

## Outcome

Implemented the nine relayed graph contract repairs in a new PythonChimera worktree, integrated F1/F2/F3 non-destructively, and qualified the real private Graphify consumer. **19 positive contract tests pass; 25 broader offline checks pass; the live-engine block is NOT_TESTED; the real consumer passes all seven checks on first, repeated and final-graph ingestion.** No engine was operated and no production DNA store was written.

Worktree: `E:\ChimeraWork\codex-graph-contracts-20260915`; branch `codex/graph-contract-repairs`. Base F1: `1f3c062c`. F2 `0284daac` and F3 `c99d6b6b` were cherry-picked as `1f94491b` and `728e7280`; their source branches and original shared checkout are untouched. The final implementation revision is recorded in `INTEGRATION.json`.

## Changes

| Packet issue | Implemented contract |
|---|---|
| D1 | Selected parameter value, units, source and applicability affect content versions. Objects without those keys retain their previous hash projection. |
| D2 | New captures include incident physical/provenance relations, their identities, direction and multiplicity. Stable generated relation IDs do not depend on unrelated insertion order. |
| D3 | Empty/partial/unsupported captures cannot assert current validity. Last passing/failing results remain visible. |
| D4 | Builds preserve historical captures/times; only a new evidence ID can be recorded through the measurement API. Rebuilds remain deterministic. |
| D5 | Sanitizer collisions refuse before export replaces a file; collision-free node mappings retain their IDs. Edges retain native `rid` and `key`. |
| D6 | Foreign schema versions refuse by name; supported 2.0.0 and legacy stores round-trip without changing graph hash. |
| D7 | Nonunique or competing band matches produce explicit ambiguity, no guessed cell assignment. Distinct bands retain normal matching. |
| D8 | Exact zero conservation passes; absent/nonfinite/invalid values fail explicitly. Unreported sampling rates remain unknown. |
| D9 | Duplicate membrane registrations count once. Wall counts do not claim physical enclosure. |

**D9 intentionally strengthens one packet expectation:** two walls do not mathematically establish closure, and one continuous surface can enclose. Q1 now exposes distinct registered support with `closed_by_built_walls: null` and a named unverified closure. This amendment was preregistered before the final implementation; a two-wall count is not accepted as physical proof.

Q5 now reports considered evidence count, affected records and unverifiable captures instead of a bare list that looks safe when empty. The current query callers and acceptance harness were updated. See `tools/creature_graph/CONTRACTS.md` for API details and compatibility changes.

The Graphify bridge now compares the projection to its authoritative graph **before any consumer write**. It preserves relation IDs, rejects stale/tampered projections, checks inverse node identity, and refuses collisions with foreign consumer nodes or orphaned foreign edges. Its actual SQLite and snapshot globals must point into the private `.tmp/creature_graph_projection_demo` directory; inherited outside paths are rejected. Production/shared concurrent ingestion remains unqualified. The documented `name=label` alias keeps FTS working without a shared-index redesign.

## Evidence and graph state

- Original F2 reproductions: all nine defects plus the query-semantics case reproduced before repair (`baseline_reproduction.json`). The originals intentionally assert broken behavior and remain unchanged. They are historical diagnostics, not the repaired green suite.
- New standard-library suite: `tests/test_contracts.py`, **19 PASS** (`contracts_recorded_measurement.log`). Its subcases cover changed fields, relation mutations, unrelated changes, missing/partial scope, stable rebuild, foreign schemas, ambiguity, zero/nonfinite values, duplicate walls, pre-write bridge refusal and inherited-store refusal.
- Broader suite: **25 PASS / 0 FAIL / 1 NOT_TESTED block**, `acceptance_results.json`. The excluded block is live-engine integration, not a passing test.
- Real Graphify API/SQLite round trips: **7/7** on first/repeat and the final authored graph, including native relation IDs, multiplicity, traversal, health and FTS. No in-memory fake is substituted for these runs.
- Final graph: **1,488 objects / 144 relations**. The two new objects are `work.graph_contract_repairs_20260915` and `ev.graph_contracts_20260915`; their three edges are two experience-enablement links and one evidence link. The new measurement has a valid current capture and source/artifact hashes. Only this scoped graph repair task was completed.
- All seven older evidence records have incomplete authored captures. Their graph validation is now **stale-by-unknown**, retaining **five passing and two failing historical results** and original provenance/times. Their native measurements have not been retracted or secretly re-run. No old capture was reconstructed from today's graph.
- The actual next-ready-task query still returns **`work.partition_leg_l`**, not the supplied report's `work.septa_leg_l`. This is a completion/evidence reconciliation problem, not a reason to repeat already-built surgery. Readiness is still authored prerequisite availability, not physical acceptance or an execution claim.

## Boundary findings and limits

The first broad import check refused a changed BodyParts3D artifact against its pin. A fresh worktree did not carry the ignored reference cache, so the old importer attempted downloads. That refusal is retained in `acceptance_offline.log`. No pin was refreshed. The repeat used **all 33 original cached artifacts**, each verified against the unchanged pins, and offline acceptance now disables network fetches. `pinned_cache_inputs.json` records those inputs. Importer outputs were semantically unchanged; incidental key-order rewrites were restored.

Pytest is absent from the installed `.venv-hy3d`; no installation was needed. Both baseline and repaired suites ran with standard Python. `tests/pytest.ini` makes future pytest collection select the positive suite rather than the frozen green-on-broken-code probes.

Capture freshness covers the declared object scope and incident physical/provenance edges, not every conceivable transitive dependency. Correct scope remains an experiment responsibility. Generic persistence hardening, runtime stable-ID mapping, concurrent production Graphify ingestion, force-state/XPBD integration, open-wound transfer, independent DYAD and pay25 remain open. Native source files were unchanged by this assignment. No whole-architecture production qualification is claimed.

## Handoff

Use `KILO_HANDOFF.md`. Reconcile the finished partition's scoped evidence and completion criteria before advancing to septum puncture work. The existing press-isolation result is not an open-wound transfer measurement. Do not refresh old timestamps/captures or auto-promote the old native evidence to make the roadmap look current.
