# Single-entry campaign helper verification

2026-09-24. Scope: the stateless planner, integrity checker and PowerShell wrapper.
This is not a live fleet launch or a claim that the game requirements are satisfied.

The frozen preregistration is `PREREGISTRATION.md`. Synthetic planner and integrity
tests were run with `python -B -m unittest discover -s <package> -p test_*.py -v`:
23 discovered, 22 passed, one skipped. The skipped fixture requires creating a
filesystem symlink, which this host did not permit; link-skipping behavior is not
claimed verified by that skipped test.

Covered behavior includes dependency and capacity checks, missing bindings, integration
receipts, stale snapshots, scope overlap, missing and aggregate disk forecasts,
unrelated ready tasks, bounded storage scans, and immutable planner inputs. Integrity
tests refuse changed requirements, including simultaneous replacement of the catalogue
and its adjacent hash file when the original external fingerprint is supplied. Duplicate
JSON keys and non-finite numbers are refused. Formatting changes preserve content identity.

Wrapper smoke checks:

- `validate` with the pinned fingerprint succeeded: 83 task IDs, 76 selected by default,
  valid dependency graph, external digest checked.
- `packet -TaskId W01` with the same fingerprint succeeded and retained the required
  controller claim, reconciliation, scope, preregistration and resource fields.
- `packet -TaskId W01` without a supplied fingerprint was refused with
  `TRUST_ANCHOR_REQUIRED`; an adjacent lock file cannot authorize dispatch preparation.

The first wrapper invocation encountered the host's script-execution policy. The smoke
checks used `powershell -NoProfile -ExecutionPolicy Bypass -File ...`, affecting only that
PowerShell process. No machine policy was changed.

Scope content fingerprint (`sha256-chimera-json-v1`):
`33a8fb7204e20bf71f563014c57d772dd111a198cd1d6b212fd053653858f863`

Raw catalogue file SHA-256:
`001eb42dc0a043bdb803c4645e1fcfcb07aad11e854b643dc812a6753ad34c38`

These are different claims. The first is compared during planning and packet generation;
the second identifies the exact packaged file bytes. Neither is a digital signature.

Not exercised: a live authenticated controller session, real provider/model dispatch,
live task reconciliation, OS resource enforcement, cleanup, protected training, gameplay,
or a ten-agent deployed controller. The package intentionally has no launch, controller
mutation or deletion implementation. Its entry directs the real coordinator to use the
existing authorized controller, supervisor, dispatch and cleanup mechanisms. Resource
forecasts are admission advice, not hard disk quotas. A terminated model session needs
an actual harness supervisor/resume mechanism to continue.
