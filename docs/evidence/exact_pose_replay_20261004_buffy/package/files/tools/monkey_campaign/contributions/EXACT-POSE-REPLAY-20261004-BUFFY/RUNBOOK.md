# Exact-pose replay — operator/independent-review handoff

Proposal: EXACT-POSE-REPLAY-20261004-BUFFY. PROPOSAL-ONLY, offered to
wk-hand-remediation for review. The existing HAND-REMEDIATION-20261003-R1-COLLISION-ADJ
lane owns the same exact 314 primary and 40 control poses. No competing attempt,
scientific control slice, replay launch or publication is authorized here.
No scientific control slice or 354-pose collision replay has run in this proposal.

Read PREREGISTRATION.md and INPUTS.json first. The replay never invokes a
placement construction: only stored Stage 1 o/u/s_star and the original two FK
postures. Existing anatomy, constants and 19 exemption edges are unchanged.
Stage 1 already adjudicated the anchor VTP against the trunk; its recorded
result did not gate the survivor predicate. The omitted check was the
pad-substituted rigid bone, NOT anchor adjudication.
The existing receipt records all 354 anchor depths at
0.019999999999999997 m, the inherited 20 mm search-bracket edge. New records
explicitly flag that edge; never describe it as an unbounded exact maximum
or change the bracket. Collision classes/depth bytes still compare exactly.

## Mandatory admission, not a checklist to bypass

The instructions/schema/commands below are retained design reference for the
existing owner's review, NOT a procedure to launch this proposal. Adopt any
useful code in the owner's existing lane and authority, not a new competing task.

1. Ownership is already assigned to wk-hand-remediation. Offer this code and
   safeguards to that lane; do not provision a second replay task for Buffy.
   This author has no authenticated fleet claim.
2. Publication owner commits PREREGISTRATION.md alone first through the existing
   serialized publication path. Never stage unrelated shared-checkout changes.
   Publish/verify the exact pin as the project requires. The author did not commit,
   push, or open a PR; a package seal is not a precommitment publication.
3. Confirm the policy boundary: anchor-included results are a conservative
   diagnostic on hand.vtp, NOT a ruling that it is solid anatomy. Raw rigid bone
   penetration stays a raw failure and cannot be masked by PAD_CONTACT/ABSORBED.
   A requested geometry/exemption change must go to Astra/Lieutenant and Captain.
4. Re-create the package against the published prereg pin (or a verified descendant),
   preserving the old package/seals. Select the pinned HAND-REMEDIATION inputs,
   this contribution, hand.vtp and vendor meshes, with write scope only this
   contribution. Verify every INPUTS.json hash; do not silently re-pin changed inputs.
5. Copy reviewed implementation into that package and seal. Lieutenant supplies
   an add-only release JSON matching the exact prereg, input, implementation,
   profile, published pin, sealed base and sealed manifest. This JSON is a
   cooperative audit record, NOT cryptographic authentication or independent approval.

Release schema (values must be supplied by the designated authority, not fabricated):

```json
{
  "schema": "chimera.exact_pose_replay.release.v1",
  "task": "EXACT-POSE-REPLAY-20261004-BUFFY",
  "preregistration_sha256": "FULL_SHA256",
  "inputs_sha256": "FULL_SHA256",
  "implementation_sha256": "FULL_SHA256",
  "authority": "Lieutenant",
  "authority_reference": "ACTUAL_DISPATCH_OR_CAPTAIN_RULING_REFERENCE",
  "release_id": "ACTUAL_RELEASE_IDENTIFIER",
  "observed_utc": "ACTUAL_OWNERSHIP_RECHECK_TIME",
  "owner": "ACTUAL_ISSUED_OWNER",
  "handoff_reference": "ACTUAL_HANDOFF_IF_OWNER_CHANGED",
  "ownership_rechecked": true,
  "source_input_commit": "79b263944d4053b7ee41f97c97b3cc2f732b1b97",
  "published_prereg_commit": "ACTUAL_40_HEX_COMMIT",
  "sealed_base_commit": "ACTUAL_40_HEX_COMMIT",
  "sealed_manifest_sha256": "FULL_SHA256",
  "resource_profile_sha256": "FULL_SHA256_OF_CURRENT_APPROVED_PROFILE",
  "unit_timeout_seconds": 600,
  "geometry_scope": "EXACT_STORED_STAGE1_POSES_NO_PLACEMENT_SOLVE",
  "anchor_policy": "DIAGNOSTIC_ONLY_NO_SOLID_ANATOMY_RULING",
  "operations": ["control", "compare-control"],
  "independent_approval_claimed": false
}
```

Do not call schema placeholders credentials or launch evidence. After the control
slice passes, append a separately authorized release for `replay`/`combine` with
`control_gate_sha256` binding the retained gate artifact. No implementation or
sealed-input change between control and scaling. Release files live outside the
sealed package; otherwise adding the release would change the seal it binds.

## Proposed command interface (owner-review reference ONLY; do not execute here)

Use C:/Python314/python.exe and the canonical task_package.py.
Run synchronously, no detached processes. Each job has the approved 16 GiB
committed-memory limit, 24 GiB reserve, <=4 threads, <=2 GiB scratch,
<=256 MiB retained outputs, <=1 MiB runner log tail. Set 600 seconds per
control/unit and 120 seconds for combine; budgets are operational, not physics.
Slot 0 currently has an unrelated unsafe_relative_path outputs/ recovery defect.
Use `--slot 2` only while that verified-free slot is available; BUSY waits >=10 s.
Do not repair leases, move old scratch, use an alternate runner root, or infer
other processes are dead. Runner owns cleanup.

```bash
PY=C:/Python314/python.exe
RUNNER=E:/PythonChimera/tools/monkey_campaign/task_package.py
CODE=tools/monkey_campaign/contributions/EXACT-POSE-REPLAY-20261004-BUFFY/replay.py
# SEALED and RELEASE are actual authority-approved absolute paths.
"$PY" -B "$RUNNER" run --sealed "$SEALED" --slot 2 --timeout 600 \
  --keep outputs/replay -- "$PY" -B "$CODE" control --route serial --release "$RELEASE"
"$PY" -B "$RUNNER" run --sealed "$SEALED" --slot 2 --timeout 600 \
  --keep outputs/replay -- "$PY" -B "$CODE" control --route units_reversed --release "$RELEASE"
```

The two independent processes each replay the first FOUR canonical
q_zero_CONTROL rows, all 20 bodies. Take SERIAL_RESULT and UNITS_RESULT from
their completed actual runner receipts, not a queued job file.

```bash
"$PY" -B "$RUNNER" run --sealed "$SEALED" --slot 2 --timeout 120 \
  --keep outputs/replay -- "$PY" -B "$CODE" compare-control --release "$RELEASE" \
  --serial-run "$SERIAL_RESULT" --units-run "$UNITS_RESULT"
```

Comparator requires distinct actual runner jobs, PASSED + cleanup_verified,
identical base and seal, verified retained artifact hashes, exact four-key census,
zero inherited raw-column drift, and byte-identical canonical payloads. Fixture
parity is explicitly not this gate. Copy/reference retained control_gate.json;
ask the authority for the control-hash-bound scaling release before scaling.

## Independent work units and deterministic combination

A `--keys` file is a JSON list of [posture, theta_index, mirror]. Use the
canonical metadata preflight keys to partition it; each pose unit depends only
on pinned input geometry, its original row and the fixed two postures. Select
one or several keys per runner job to amortize model loading, never >4 local
jobs total or >4 threads/job. Completion order is irrelevant. The payload has
no clock/path/PID/job fields. `pose_sha256` binds only the pose key and full
original Stage 1/2 rows. Candidate/input pins have separate identity fields;
posture values are separately recorded and validated, not in that pose hash.
Atomic per-body checkpoints and per-pose units survive a nonzero/timeout under
declared `--keep outputs/replay`; failed runs remain evidence and do not count
as completed eligible units for final combination.

```bash
"$PY" -B "$RUNNER" run --sealed "$SEALED" --slot 2 --timeout 600 \
  --keep outputs/replay -- "$PY" -B "$CODE" replay --release "$SCALING_RELEASE" \
  --control-gate "$GATE" --keys "$KEY_SELECTION"
# Without --keys replay requests the entire 354 set; only do this if measured
# control timing supports the declared timeout. No unsupported timing estimate.
```

Final combiner takes one or more exact retained runner unit directories:
RESULT_DIRECTORY/artifacts/outputs/replay/units. It refuses noncanonical result
roots, failed/incomplete runner receipts, wrong base/seal, hash drift, duplicates,
missing/foreign keys, body omissions, source drift, nonfinite/unknown classes and
promoted scope. Only a complete 354-pose / 7,080-body census may be a full result.

```bash
"$PY" -B "$RUNNER" run --sealed "$SEALED" --slot 2 --timeout 120 \
  --keep outputs/replay -- "$PY" -B "$CODE" combine --release "$SCALING_RELEASE" \
  --control-gate "$GATE" --unit-dir "$UNITS_A" --unit-dir "$UNITS_B"
```

A raw negative is not an execution failure; any record-identity drift is a stop
with retained evidence. Independent reviewer must rerun the slice, verify exact
source identities and full census, and assess the bone-vs-pad and envelope
interpretation. Author tests cannot certify independence, supported climbing,
training readiness, real forces, or player runtime.

## Fixture-only proposal regression checks

`test_replay.py` runs only labeled synthetic packaging fixtures, parser/syntax
checks, hash/combination/gate failures and a fail-closed scientific CLI probe.
Historical `replay.py preflight` jobs checked pinned bytes and recorded key
metadata only; none were scientific replay evidence. Under the current
proposal-only direction, do not launch new preflights, control slices or replay
attempts here. Only fixture regression checks for this proposal correction run
through the approved runner with `--keep outputs/replay`; no collision geometry
is evaluated. No typechecker is configured for this stdlib contribution;
AST/compile checks are syntax checks, not static type inference.
