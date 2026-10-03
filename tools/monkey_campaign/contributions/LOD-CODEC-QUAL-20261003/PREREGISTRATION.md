# PREREGISTRATION (DRAFT) — LOD storage-codec + acceptance-policy qualification

Status: DRAFT authored by `wk-lod-codec` for the Lieutenant. Chain stop 1 ONLY
(inventory + this prereg draft). Per the separate-first/publication law the
Lieutenant commits this file ALONE FIRST; the committed bytes are the freeze and
every later receipt of this lane must embed `preregistration_sha256` of exactly
those bytes and refuse any mismatch. No qualification measurement, runner job,
or code change of this lane exists at draft time. Write scope of the draft: the
NEW lane dir `E:/ChimeraWork/monkey-coordination/lod-codec/` (NO_WORKTREES law
honored: no worktree, no clone; the later gated CPU run goes through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`).

This is an INFRASTRUCTURE QUALIFICATION. No physics claim, no game claim, no
engine-runtime qualification, no GPU claim follows from it.

## 0. Reconciliation — WHICH "LOD codec" this prereg qualifies (reconcile-first law)

Captain's order #13 follow-up, quoted verbatim from the frozen mathspec
baseline receipt (`mathspec_assembly_completion.v1.json`, phase 4, field
`4b_baseline_order.not_folded_in`): "any LOD codec / acceptance-policy
qualification is a SEPARATE follow-up that must preserve this baseline for
comparison; none was attempted here".

The existing machinery this prereg qualifies is the DELIVERED fixed
storage-precision pilot (`REVIEW_CANDIDATE_NOT_INSTALLED`,
`E:/Chimera/LOD_DELIVERY.json`): an IEEE FP64/FP32/FP16 storage codec
(`codec.py`), a dual state-and-energy acceptance checker (`policy.py`), and an
owner-routed precision proposal adapter (`adapter.py`), delivered as sealed
package `E:/Chimera/physics-lod-package/sealed/35f53134732744e1a1590ee73f899517`
(manifest sha256 `325a447418769d710fd53c80e1b44e27f0be99dc18510f136e4d462fe330a04a`,
re-hashed and verified this session). Its delivery record is
`codex-parallel-development/LOD_HANDOFF.txt` (sha256
`f3ad0f63e56e334162fe6f0583763f06fb7f0be8bf01e82ba97cb5946870fa08`,
matching `LOD_DELIVERY.json.handoff_sha256`).

Reconciliation of the name collisions found in the corpus (all READ-ONLY for
this lane; none of them is the object of this prereg):

| machinery | location | what it is | relation |
|---|---|---|---|
| `codec.py`/`policy.py`/`adapter.py` | sealed physics-lod package (NOT in any git branch; verified: no commit touches `tools/monkey_campaign/physics_lod`) | numeric storage-precision codec + acceptance policy | THE QUALIFICATION OBJECT |
| `ChimeraEngine/lod.py` + `lod_train.py` + `lod.trained.json` | repo master (rendering stack) | VISUAL splat-body mip-pyramid LOD (trained rho/beta, pop-probe 8x bar) | different domain; untouched |
| `CODEC_STANDARD.md` (lane codec-benchmark) | coordination tree | CAPTURE VIDEO codec acceptance (FFV1 bitexact, pixel gates bind frames) | different codec; untouched |
| `req.matter_variables_lod` (active graph spec) | selected graph | the physics-LOD CONTRACT the pilot's prereg explicitly extends | consumed as contract text; no graph amendment here |

Installation status (verified this session): `tools/monkey_campaign/physics_lod/`
exists on NO branch of the repository; the eight-file owner patch
(`OWNER_PATCH.patch` sha256 `2ba8fb592a27f6133a3cfcd260ed41f3a029422fb57445f118059fc4e1552451`)
is UNAPPLIED. Applying it is the publication owner's step 1 of
`LOD_HANDOFF.txt NEXT OWNER INTEGRATION` and is NOT this lane's action. The
qualification runs the SEALED bytes in an isolated runner package; it applies
nothing to any checkout.

## 1. The qualification object (inventory of record; all hashes re-verified this session)

Final seal root: `E:/Chimera/physics-lod-package/sealed/35f53134732744e1a1590ee73f899517`
(schema `chimera.sealed_package.v1`; 26 files; outer `change.patch` sha256
`2972321cf0bbe841ba66ddb6ae91cb5e8148ee11dc80d95b4d93c40c028e94be` =
manifest `patch_sha256`). Earlier seals `05c5fb75…`/`2ef5eb26…` in the same
tree are superseded attempts and are not consumed.

Components (paths relative to `files/tools/monkey_campaign/physics_lod/`):

| file | sha256 | role |
|---|---|---|
| `CONTRACT.json` | `8be6e3598cf1068949bca8ed51beb3e753e65708b5dec226491d765441d0a01c` | the frozen contract both workers consumed (schema `chimera.precision_pilot.contract.v1`) |
| `codec.py` | `d781eb8ee8eec071fe3dc218d1c7df951d5e094bfd3583063a6b0570561872b3` | `roundtrip(values, precision)`: IEEE binary64/32/16 little-endian encode+decode via `struct d/f/e`; refusals prefixed `lod_codec_invalid` (bool, non-numeric, complex, empty, NaN, inf, conversion/storage overflow, unknown precision); pure; never mutates input |
| `policy.py` | `1bf2cd09e37bc1d6d6672afd2e7206c265baf4a196aea9096dad637977aabb2b` | `assess(reference, candidate, weights, initial_energy, state_atol, energy_atol)`: accepted iff max(abs(candidate-reference)) <= state_atol AND abs(fsum(weight*candidate)-initial_energy) <= energy_atol; reason order [state_error, energy_error], only exceeded constraints; refusals prefixed `lod_policy_invalid`; no codec import |
| `adapter.py` | `e68fc9130f0f28f30252b7bd1d28a7507be1f12d19685f325ce2c9fa5d2a64fa` | `apply_precision(...)`: owner-checked proposal; quantizes stored absolute temperatures, converts to T_ref offsets for the energy check; commits only on accept; refusal leaves store unchanged (hash-asserted, `lod_refusal_changed_state`); reports `quantization_energy_delta_J` labelled "numerical discrepancy, not physical heat" |
| `run_tests.py` | `9cd730d1d5e6976b030ea7c2a24f60ec1d606676b22df4f4b6e166410e1f864f` | the canonical sealed executor (fixture-hash gate, contract-hash assert, unit battery, owner-patch scratch isolation check, per-tick fixed-tier runs, 1-vs-2-worker byte-identity assert) |
| `test_codec.py` / `test_policy.py` / `test_adapter.py` | `63e31608…` / `b851a769…` / `dd1120aa…` | 24 portable unit tests (malformed inputs, overflow, ownership, boundary inclusivity, silent bias, refusal preservation) |
| `PREREGISTRATION.txt` | `890e2ba5b74aef7af7800726fa63ba0f3c65bdc1396f10f86a222844733419eb` | the delivery's own prereg (declared before their experiments); its laws are carried forward, including "Never enlarge bounds after observing a refusal" |
| `FIXTURE_INPUTS.json` | `1efa5d4dcf39cb249e2a009d0329d8b7a24726e063dd1ec78854ed28da095f8f` | fixture manifest; all 10 listed hashes re-verified OK this session |
| `DEVELOPMENT_PROOF.json` / `OWNERSHIP_CODEC.json` / `OWNERSHIP_POLICY.json` | `c50ddc55…` / (in seal) / (in seal) | two-lane provenance (codec_worker, policy_worker) bound to the one contract hash |
| `OWNER_PATCH.patch` | `2ba8fb592a27f6133a3cfcd260ed41f3a029422fb57445f118059fc4e1552451` | the eight-file owner patch — hash-verified by the sealed executor in scratch; NOT applied by this lane |

Consumers: inside the seal, only `run_tests.py` and the three test modules.
In the repository: NOTHING yet (not installed). The future consumer named by
the handoff ("the intended mathspec/game consumer") does not exist yet; this
qualification is a prerequisite input to that integration decision, not the
integration itself.

Acceptance-policy thresholds are NOT restated by this lane. They are read at
run time by the sealed executor from the fixture spec's
`numerics.admissibility` row at the declared `dt_s` (0.005 s → state_linf_tol
0.25 K, conserved_drift_tol 0.05 J; a second admissible row at 0.001 s declares
0.05 K / 0.01 J). The executor hard-asserts the contract hash and refuses
modified components (`component_changed_after_delivery`).

## 2. The preserved full-precision baseline (order #13 preservation duty)

The frozen baseline that must survive untouched for comparison:

- Mathspec lane `E:/ChimeraWork/monkey-coordination/mathspec`, git HEAD
  `887706ade0b8e8840c082b2e7ffe49bb93b45321`, working tree clean (verified).
- `spec/thermal_two_membrane.spec.v1.json` sha256
  `008aac7fe7e15529f5e9caf58d25714664827b72c8d5fd0c14df1a4092b87e4a` — the ONE
  mathematical source pinned in both phase receipts.
- Phase-3 pinned receipt
  `mathspec/pinned_baseline/phase3-2196518023bd48d8b37b9439216d6149/mathspec_assembly_completion.v1.json`
  sha256 `4d5cfe7cee6b3a801e5f695ce4c5d9f02609dff0d1cdb005d9f9f3642949df5f`
  (runner job `21965180…`); phase-4 pinned receipt
  `mathspec/pinned_baseline/phase4-8b8e3f382bf744dca905299967d48b03/mathspec_assembly_completion.v1.json`
  sha256 `1442daa39919b2c7ed785d27ccb8a18cd1ef1eba8fa949fd6a3bd7abdcde98b5`
  (runner job `8b8e3f38…`). Its `4b_baseline_order.primary_result`: "the
  FULL-PRECISION coupled baseline (declared float64 explicit Euler at the
  declared admissible dts) -- completed FIRST by this assembly".
- Bitwise baseline identity VERIFIED this session: the seal's fixture copy
  `mathspec_fixture/spec/thermal_two_membrane.spec.v1.json` is sha256-identical
  to the mathspec lane's spec (`008aac7f…`), and the seal's pinned runtime
  inputs match the mathspec reuse table exactly (`PORT_CONTRACT_V2.py`
  `0f1b7dfe…`, `combine_core.py` `8bfe6949…`, `port_contract_schema.v2.json`
  `69161d32…`).

Preservation obligations of this lane: no write to the mathspec lane, the
delivered seals, `E:/Chimera/physics-lod-package/`, the rendering LOD files,
the capture codec standard, or the selected graph. The in-run full-precision
comparison law is inherited unchanged: the reference is the analytic solution
computed from declared parameters (`analytic_reference`), never read from the
runtime store.

## 3. Declared comparisons, predictions, falsifiers

Executor for the later gated run (chain stop 2): the sealed `run_tests.py`,
byte-identical to the hashes in section 1, executed through the canonical CPU
runner against a freshly sealed package built from an unmodified copy of the 26
sealed files. The package build re-verifies all file hashes against the seal's
`manifest.json`; any mismatch is BLOCKED (no run, data preserved). The package
is pinned to the published prereg commit recorded in the lane EVIDENCE.

Reference rows of record (delivery qualification, runner job
`8884a2b059964cc981b448799389241d`, PASSED, slot 2; receipt sha256
`c9b43e95687fd96320b7e937ced272862a9442ed598c41e7beadadd384f260a7`;
`outputs/result.json` sha256
`f752e1047d1fc29ff938361bd082f6af45e8078fa3adc989934f62234d73b157`; dt 0.005 s,
horizon 4.0 s, 800 ticks; bounds 0.25 K / 0.05 J):

| case | precision | qualified | first refusal | peak state err (K) | peak energy err (J) | trace_sha256 |
|---|---|---|---|---|---|---|
| nominal | fp64 | yes | none | 0.023012444625464923 | 2.2168933355715126e-12 | `d57e544a8044…` |
| nominal | fp32 | yes | none | 0.022861058782552846 | 0.002166748046875 | `756cced54ae0…` |
| nominal | fp16 | NO | tick 3, reasons ["state_error"] | 0.37383056259631076 | 0.0 | `c6b45c3c38df…` |
| equal_temperatures | fp64 | yes | none | 0.0 | 0.0 | `5a8c5aca27b7…` |
| equal_temperatures | fp32 | yes | none | 0.0 | 0.0 | `4ebaaeae352b…` |
| equal_temperatures | fp16 | yes | none | 0.0 | 0.0 | `ca1957ee2dce…` |

Packed state sizes 16/8/4 bytes (fp64/fp32/fp16, two states).

### C1 — fp64 value identity (the decode must be exact at full precision)

P1: for every finite fixture state sequence, `roundtrip(v,'fp64')` decodes to
values exactly equal to the inputs (element-wise `==`), payload 8 bytes/value,
re-encode stable. This is the value-identity bound that makes fp64 the
control tier. F1 (falsifier): any fp64 decoded value differing from its input,
or any unstable payload.

### C2 — reduced-precision value-identity bounds (where difference is bounded)

P2: fp32/fp16 decodes are IEEE round-to-nearest results and are NOT
value-identical to fp64 by design. The committed-path deviation from the
full-precision analytic reference is bounded ONLY by the declared per-tick
gates (0.25 K state, 0.05 J energy at dt 0.005), evaluated EVERY tick (800 of
them), and the reported `quantization_energy_delta_J` is a signed numerical
discrepancy, never physical heat. F2: any accepted tick whose reported
state/energy error exceeds its gate, any gate value in the report differing
from the spec's declared row, or any quantization delta labelled or booked as
heat.

### C3 — tolerance behavior at the declared thresholds (partition of record)

P3: the accept/refuse partition reproduces the reference table exactly:
nominal fp64 accept 800 ticks; nominal fp32 accept 800 ticks; nominal fp16
refuse at tick 3 with reasons exactly ["state_error"] and the store unchanged;
equal_temperatures all three tiers accept with zero measured error. Refusals
are retained as results — never repaired, no bound enlarged (delivery prereg
law carried forward). F3: any partition change (e.g. fp16 nominal surviving
800 ticks, or an fp32 first-refusal), any refusal reason outside the declared
vocabulary/order, or any repaired refusal.

### C4 — determinism of the decode and of the whole qualified path

P4: (a) repeated decode is byte-stable — `roundtrip` is a pure function, and
each case's `trace_sha256` (a canonical hash over all 800 per-tick verdict
dicts) is the fingerprint; (b) every case/precision row is byte-identical
between 1 and 2 runtime workers (the sealed `schedule_changed_result` assert);
(c) every declared field of the new run's `fixed_tiers` rows (case, precision,
qualified_for_this_fixture, first_refusal, max_state_error_K,
max_energy_error_J, sum_committed_quantization_energy_delta_J,
trace_sha256, packed_state_bytes, state_bound_K, energy_bound_J) equals the
reference table above, because sealed bytes + fixture are identical and the
computation is deterministic. The delivery itself already demonstrated
cross-slot row identity (its initial PASSED job `993f8128…`); this rerun
re-establishes it now. F4: any row-level deviation from the reference table,
any 1-vs-2-worker divergence, or any trace_sha256 mismatch. A firing F4 is a
RETAINED result reported to the Lieutenant — never tuned, filtered or retried
into agreement.

### C5 — refusal state preservation and unit battery

P5: at every refusal the store snapshot is byte-identical before/after (the
sealed in-run assert plus `lod_refusal_changed_state`), and the 24-test unit
battery passes with 0 failures / 0 errors, including the owner-patch scratch
isolation check (byte-verified targets, scratch removed). F5: any state change
at refusal, any unit-test failure, or a scratch residue.

### Top-level prereg integrity

F6: a qualification claim whose receipt does not come from the canonical
runner (`task_package.py run`), is not bound to the committed prereg bytes, or
whose package bytes fail the pinned-hash gate. Only an actual receipt stating
PASSED with `cleanup_verified: true` counts; missing/skipped checks are
reported as missing, never implied.

## 4. Honest failure modes (declared in advance)

- LOD loss is EXPECTED: reduced-precision decoded paths differ from full
  precision. Equality is claimed at fp64 only (C1). For fp32/fp16 the prereg
  claims a BOUNDED difference (C2) at the declared gates on THIS fixture only.
- NOT bounded / NOT claimed: values outside a tier's finite range are refused,
  not bounded (fp16 storage range ends at 65504; the unit battery covers the
  refusal); trajectory error beyond the 4 s horizon; any other dynamical
  system, topology, or state space; GPU storage or arithmetic (CPU emulation
  only); process-memory savings or FPS; adaptive/load-driven tier selection
  (the delivery recorded `adaptive_selection_enabled: false`); spatial
  coarsening or contact-critical accuracy; game integration; refusal rollback
  of the already-integrated solver tick (declared by the delivery prereg).
- The fixture is synthetic with explicit synthetic provenance (the mathspec
  spec's own declaration); nothing here measures physical fidelity.
- A falsified prediction (any F above) is preserved with its receipt and
  reported as a failure of this qualification; no threshold is moved, no code
  is edited to convert a failure into a pass, and no second metric is
  substituted after the fact.

## 5. Execution plan for the gated run (chain stop 2 — only after the Lieutenant commits this prereg)

1. Build `lod-codec/package/` containing an unmodified copy of the 26 sealed
   files under `files/tools/monkey_campaign/physics_lod/`; verify every file
   against the seal manifest before sealing; record the new package's
   `package.json` (base `7222729eca6e9f97f25061c8b1dc3d229bb703d8`, the same
   base the delivery sealed against, matching this checkout's HEAD), the sealed
   manifest hash and changed-file list in EVIDENCE.
2. Run (CPU only, canonical runner, absolute paths):
   `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal <ABS_PACKAGE_DIR>`
   then
   `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py run --sealed <ABS_SEALED_DIR> --keep outputs/result.json -- python -B tools/monkey_campaign/physics_lod/run_tests.py`
   (slot auto-selected; on BUSY/exit 75 wait >= 10 s and retry; use `--slot 2/3`
   only if the pool refuses slots 0/1). The executor writes `outputs/result.json`
   relative to its cwd; it is the only declared retained output.
3. Bind in EVIDENCE: the committed `preregistration_sha256`, the package
   manifest hash, the job id, the receipt path + sha256, exit status,
   `cleanup_verified`, and the `result.json` sha256. Compare `fixed_tiers`
   rows against the section-3 table by the declared fields. State every
   missing/skipped check explicitly.
4. BLOCKED conditions (preserve data, report, stop): any pinned-hash mismatch
   at package build; runner BLOCKED; repeated BUSY beyond the campaign's retry
   patience; absence of the committed prereg (the run does not start).

## 6. Explicitly not claimed by this lane

No physics claim; no game claim; no engine qualification; no GPU result; no
adaptive LOD; no installation or integration of the owner patch (that remains
the publication owner's serialized step); no graph amendment; no modification
of any preserved baseline artifact, seal, lane, or checkout file. The
qualification of the RENDERING LOD (`ChimeraEngine/lod.py`, pop-probe 8x bar)
and of the CAPTURE VIDEO codec (`CODEC_STANDARD.md`) is OUT OF SCOPE here; the
reconciliation table in section 0 exists so nobody later mistakes one for
another.
