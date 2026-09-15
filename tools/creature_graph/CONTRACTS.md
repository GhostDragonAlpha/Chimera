# Creature graph contracts

The graph is a planning and evidence index, not a physical oracle. Authored implementation status, the result of a past measurement, and whether that result applies to today's declared inputs are separate facts.

## New measurements and historical records

`CreatureGraph.record_evidence(record)` accepts a **new evidence ID**, a passing/failing result, an explicit timezone-aware measurement time, and nonempty unique `deps`. Invoke it with the graph representing the actual measurement inputs; do not use it to retroactively stamp old results against today's graph. It captures object content versions and the incident physical/provenance relations, preserving direction, relation identity and multiplicity. It does not promote implementation status or certify that the caller's experiment was valid.

`capture_contract: 1` identifies this format. `captured_dependencies` pins the declared input scope; `captured_relations` pins its incident physical/provenance subgraph. Current scope does not automatically expand through arbitrary graph paths: the experiment must name all relevant object inputs. Relationship additions/removals/changes within scope invalidate freshness. Bookkeeping edges and unrelated changes do not. Selected parameter value/units/source/applicability participate in content versions; cosmetic object names/notes do not.

Builders preserve `captured` and `captured_utc`. They never fill an empty capture. Missing/incomplete/unsupported captures are stale-by-unknown, preserving `last_result`. The seven historical evidence records currently have empty authored captures, so the rebuilt graph marks all seven stale; their original five passing and two failing results and artifact provenance remain visible. This is a graph-freshness limitation, not a retraction of the native test observations.

New object hashes preserve the prior projection for objects without the newly covered keys. Generated relation IDs are deterministic from edge content plus duplicate ordinal, independent of unrelated insertion order; explicitly loaded legacy IDs are preserved. A changed capture contract requires a new measurement record, not a rewritten historical record.

`load` supports `2.0.0`, explicit `1.0.0-unversioned`, and the original version-less legacy store. Foreign versions refuse with their version named. Load retains graph bytes/semantics for round-trip identity; call `refresh_validation` before relying on old validity. Builds and projections refresh deterministically without fabricating a detection timestamp.

## Query contracts

`q_evidence_at_risk` now returns an object: `if_changed`, `evidence_records_considered`, `at_risk`, `unverifiable_captures`, and `coverage`. It no longer returns an ambiguous bare list. `run_all_six` nests these reports for its Q5 object/material cases. Zero evidence is explicitly `no evidence`; incomplete capture is explicit. The list of declared dependencies is not proof of exhaustive causal coverage.

Q1 deduplicates membrane IDs per region and reports `distinct_supported_membranes`. **Wall count never establishes enclosure.** `closed_by_built_walls` is null and `closure_verification` names the missing proof. One continuous surface can enclose; two independent planes need not. This deliberately strengthens the packet's proposed two-wall heuristic. Topology, seal integrity and load-bearing behavior require their own measured evidence.

Runtime matching uses the existing band geometry only when it uniquely identifies a cell and no other instance competes for it. Ambiguous candidates produce no cell assignment and a named ambiguity with candidate indices/count. Explicit stable engine-instance mapping is future work. Conservation handles zero correctly and refuses missing/nonfinite/invalid values. Sampling frequency is read from telemetry or left unknown, never invented as 300 Hz.

Task readiness remains the existing authored prerequisite-availability query, not automatic experiment acceptance or an execution claim. Name `gaps.q_next_ready_task` versus `queries.next_work` explicitly. On the integrated store the former currently returns **work.partition_leg_l**, not the report's asserted work.septa_leg_l. Do not rerun completed geometry blindly; reconcile its evidence and completion criteria with the native result first.

## Graphify boundary

`make_projection` builds the projection; `export` publishes it. Sanitizer collisions refuse before replacing an existing output. Collision-free node IDs remain compatible. Edges export native `rid`, with `key == rid`; the old numeric sort index was not durable identity. The payload carries its native `graph_hash`.

`graphify_consumer.ingest_projection(gi, projection, authoritative_graph)` validates schema, inverse node identity, relation IDs/direction and the complete projected fields against the authoritative graph **before writing**. A post-write comparison alone is not an admission gate. Foreign consumer-node collisions and orphaned foreign edges refuse.

The command-line consumer uses only `.tmp/creature_graph_projection_demo` in its own checkout. Inherited database/snapshot paths outside it refuse, and resolved backend globals are checked. Shared production DNA ingestion and concurrent multi-writer read/modify/write remain unqualified. The bridge is a real, isolated consumer integration; it is not deployment into the user's production Graphify surface. `name=label` remains the documented FTS alias, avoiding an unrelated shared-index change.

## Tests

Run `python -B tools/creature_graph/tests/test_contracts.py` (standard library, positive assertions). Historical F2 `test_d*.py` files intentionally assert broken behavior; they remain unchanged as baseline reproducers and are not the repaired acceptance suite. `tests/pytest.ini` selects the positive suite for pytest discovery.

`acceptance.py --offline` exercises broader graph contracts and reports the live-engine block as NOT_TESTED. It needs the original hash-verified cached reference artifacts; offline mode refuses network fetches. Never re-pin because a fresh download differs. Private Graphify first/repeated round trips are separate from native-engine and player acceptance.
