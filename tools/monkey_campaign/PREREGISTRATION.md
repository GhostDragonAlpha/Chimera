# Single-entry continuous monkey campaign: implementation contract

Recorded before helper implementation or tests, 2026-09-24.

Statement: a stateless helper can turn the existing 83-item completion map and an
authenticated controller snapshot into bounded next-work recommendations, without
inventing acceptance, launching processes, deleting files, or duplicating live state.

Prediction: it refuses stale/incomplete snapshots, unresolved task mappings, unsupported
states, false integrated claims without evidence, invalid dependency graphs, unknown
task IDs, overlapping writer scopes, and insufficient disk headroom. It never admits
more new assignments than the actual harness or available controller worker slots.
Blocked tasks do not prevent unrelated ready work. All required selected tasks must
be integrated with receipts before completion can be reported.

Falsifiers, frozen before tests:

1. Duplicate/missing/cyclic task identifiers are accepted.
2. A dependency or goal is treated as complete without controller integration evidence.
3. Stale snapshots produce dispatch recommendations or completion claims.
4. Recommendations exceed harness capacity, available controller slots, or campaign cap.
5. An overlapping writer scope or unknown disk forecast is silently admitted.
6. Aggregate forecast is not subtracted before admitting the next concurrent job.
7. Storage scans follow symlinks/reparse points or claim a complete scan after an error.
8. The helper mutates a project/controller/graph, launches a worker, or deletes any file.
9. A blocked task prevents an unrelated eligible task being recommended.
10. Absence of a binding is interpreted as unfinished implementation or triggers duplication.

The tests exercise policy and dependency behavior with synthetic controller records;
they do not demonstrate provider dispatch, hardware quotas, cleanup, or live integration.
The agent's actual dispatch tools and existing controller/supervisor remain required.

Additional operator requirement, before integrity implementation/tests:
the approved task list must have a content fingerprint. JSON object key order and
line-ending changes may preserve semantic identity under the explicitly named
canonicalization; task, dependency, scope or criterion changes must not. Duplicate
JSON keys and non-finite numbers are refused. Dispatch/packet generation requires
an expected digest pinned outside the worker's editable catalogue/lock pair.
A colocated lock alone is change detection, not human-only authentication.
Progress continues in the existing controller and cannot rewrite requirements.
