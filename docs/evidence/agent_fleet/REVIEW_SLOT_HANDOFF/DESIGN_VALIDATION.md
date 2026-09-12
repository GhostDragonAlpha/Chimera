# Private candidate report

## Result

The final candidate satisfies the preregistered review-slot, capacity,
correction, recovery, provisioning, and acknowledgement-response predictions in
ephemeral SQLite and loopback HTTP fixtures.  It has not been deployed and did
not alter either live task or slot.

The initial compatibility-runner attempt against the old source failed before
collecting tests because that checkout has no `test_resource_lifecycle` module.
The runner was corrected to load each named suite only when that source tree
contains it.  This changes no acceptance rule: integrated source runs all four
requested suites; old source runs its three available suites.  All final logs
are retained beside this report.

## Final commands and outcomes

All commands ran from this directory.  `FLEET_CONTROL_ROOT` is an explicit
private compatibility override; when installed, `test_review_handoff.py`
defaults to its own source directory.

| Command binding | Outcome | Raw log |
|---|---:|---|
| integrated `control.py`, `python -m unittest -v test_review_handoff.py` | 13/13 PASS, 2.033 s | `focused_integrated.log` |
| old deployed `control.py`, same focused command | 13/13 PASS, 2.034 s | `focused_old.log` |
| integrated base, `python run_extension_legacy_tests.py` | 74/74 PASS, 17.750 s | `legacy_integrated.log` |
| old deployed base, same rebound runner | 62/62 PASS, 16.397 s | `legacy_old.log` |

`python -m py_compile review_handoff.py service.py test_review_handoff.py
run_extension_legacy_tests.py` also exited 0 before the final runs.

The integrated base used for compatibility had SHA-256
`02308724817b919eae9a4c638a67faa9c484d95b7a47b04963bae64ffd016715`.
The old deployed base had SHA-256
`87e6046638cfd552f4a986a2775afc84d6bd2c95d5996c3acc34080d2403dadd`.

## Frozen candidate identities

| File | SHA-256 |
|---|---|
| `review_handoff.py` | `51b975478c44f6fa610c7fba7da2ecd6b43ff2982bbcd22a7a8f7bab6ff0ae77` |
| `service.py` | `2ea4a29feb5df43b33510c4d10f9f5784fa5bef3f2f72138d64455d97ae60284` |
| `test_review_handoff.py` | `333efd905f75f316e6344ef48ff3033b9c0438f255b19a9c47e80231cfb65c8d` |
| `run_extension_legacy_tests.py` | `7f71f4f1af94e482ab2d106daf54becb588199dbc25742ddd8fd2330df666cec` |
| `focused_integrated.log` | `97d1d67383e03cf19d3f1b5d36e06203e32a7950094a5fffe2492a937363c513` |
| `focused_old.log` | `0026d68100becbc5074cfc412d9582c48ae463e88c0e9d412d5f16a2e5a9e0f2` |
| `legacy_integrated.log` | `6f24a65e33c9d962bc40ba55368cf472295d6f251d8da3437406702b81f7b4b2` |
| `legacy_old.log` | `9444a4057001948a9f2f3f103f3d13e737cc18c76310963b3f8f83b547c9d94b` |

The earlier source/test hashes `e0c11538...` and `30c57d08...` are superseded.
Their lifecycle logic passed, but their inherited slotless acknowledgement text
incorrectly claimed that a slot was still held.  The final candidate corrects
that response and adds paired slotless/slotted tests without changing inherited
acknowledgement gates or state transitions.
