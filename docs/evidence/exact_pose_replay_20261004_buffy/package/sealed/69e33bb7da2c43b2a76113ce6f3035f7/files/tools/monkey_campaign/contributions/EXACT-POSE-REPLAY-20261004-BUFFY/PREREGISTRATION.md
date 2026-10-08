# Exact-pose grasp collision replay — preregistration proposal

ID: EXACT-POSE-REPLAY-20261004-BUFFY-PRE-1
Author: Buffy (this Freebuff task; no borrowed fleet identity)
Written UTC: 2026-10-04. Status: PROPOSAL, NOT PUBLISHED/RELEASED.

## Selection and authority

The Captain requested one hour of independent work, first considering this replay.
Read-only entry checks found no exact-pose collision replay card, attempt, or
roster assignment in the coordination registry (revision 1695), the running
scheduler projection, or the maintained Lieutenant resume. The existing
HAND-REMEDIATION-20261003 scope remains owned by wk-hand-remediation / agent_12f307d7;
its package now names R1-STAGE4. This proposal owns only the new
EXACT-POSE-REPLAY-20261004-BUFFY directory and its evidence/package directory.
No existing owner files, registry rows, shared graphs, runtime processes, or
publication branches are changed. Absence from these records is not a controller
claim: no private controller session or authenticated admission was provisioned.
Live-agent counts are unknown here. The roster and registry disagree on statuses;
no expired/stale assignment is taken over. Recheck ownership before release.

The replay is highest-value independent preparation because the existing
314 primary and 40 control placements have downstream capacity/force evidence,
but their pad-substituted bone was omitted and anchor collision was recorded
without contributing to the placement predicate. Completing the missing record
can prevent unsupported grasp conclusions without changing anatomy or thresholds.
This is NOT the separate R2 placement construction or a new placement sweep.

## Exact inputs and immutable physics

Input Git revision: 79b263944d4053b7ee41f97c97b3cc2f732b1b97 (available local object;
not a claim that the shared checkout or remote currently runs that revision).
Input contribution: tools/monkey_campaign/contributions/HAND-REMEDIATION-20261003.

- raised_cap_stage1_pad_receipt.json SHA256:
  4df5f48020c4dd601b7d6fc7c3047c4eb3c1e5c829bf450e07427c32c3835900
- stage2_capacity_receipt.json SHA256:
  8b93464c6ee206570c60fd00a750a2229ea650b0afaf589b8bbce6ed0bde174d
- instrument_v2.py SHA256:
  9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd
- grasp_screen.py SHA256:
  6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e9e0ea
- vpl1_pad.py SHA256:
  54af4a49ce57736cf0d90fe2a5d57ea98dd24d568efcae635b8e20479575794e
- run_stage1_pad.py SHA256:
  33392b97f275c640d3a5e562f88996cbb3881e9cbd6621e897dd1167bd94a884

Use the pinned model parser, FK, frame builder and collision instrument unmodified.
SCALE 0.5384048132470733; tau 1e-4 m; pi_c 1e-3 m;
r_joint 5e-3 m; trunk radius 0.037 m; trunk height 1.158 m;
depth bracket 0.02 m and all instrument iteration bounds unchanged.
Keep VPL-1 thickness, compression window, sign map, stiffness and measured inputs
unchanged; pad values are inherited record columns, NEVER collision exemptions.
Preserve CERTIFIED_EDGES exactly (19 joint-region exemptions for body/body tests,
none for body/trunk). This replay does not add a new body/body sweep; it emits
that unchanged exemption map and the 20-body census alongside trunk records.
Anchor is the pinned hand.vtp envelope, NOT new solid anatomy or measured tissue.

## Pose identity and units

Pose key = [posture, theta_index, mirror]; posture order is q_c_PRIMARY then
q_zero_CONTROL, followed by increasing integer theta_index then mirror.
Require exactly 314 and 40 unique keys, and a bijection with Stage 2 capacity_rows.
Also require identical pad_body, pad_class and pad_u for joined rows.
Use each Stage 1 survivor's stored o/u/s_star verbatim. Do NOT call solve_s_star,
placement_family, axis_basis, or another placement construction. Rebuild only the
original two FK postures (primary constants + certified-joint zero control),
without translating any body or changing q. All geometry is in metres.
Per-pose identity hashes bind the complete Stage 1 row, joined Stage 2 row,
posture values and inherited file pins.

## Replay and outcome space

Each independent unit is one pose key. Evaluate all 20 frames against that row's
analytic cylinder with iv.adjudicate_body_vs_cylinder(frame, o, u, iv.TAU),
including the pad-substituted body AND macaque_hand_anchor. No early pose rejection
may suppress a body's record. Store full per-body primitive records, each body
position/rotation and mesh/sphere identity, raw classes, signed margin, depth,
Level 1 proxy, exact-triangle and bisection counts when the primitive emits them.
Do not invent absent distances for sound Level 1 clears.

Run the inherited gs.classify_placement_bones on (a) all 19 bone records, no pad
omission, and (b) those records plus the anchor envelope as a noncontact record.
Record both diagnostic verdicts AND the full rejection list; do not only keep
its first-reject reason. Preserve the inherited two declared contact segments
(distal_thumb, distph3): CLEAR is no-contact, depth > pi_c refuses; all other
bodies must be CLEAR. Pad reclassification never changes a rigid-bone raw class.
The anchor-inclusive verdict is a conservative application of that unchanged
noncontact predicate to represented envelope geometry; it is NOT a ruling that
the envelope is certified solid anatomy. If a new exemption, envelope interpretation,
pad/solid replacement or parameter change is needed to advance grasp, STOP and
route exact evidence and bounded options to Lieutenant/Astra and the Captain.
No changed policy is implemented by this replay.

Raw class space is CLEAR / TOUCHING / GENUINE_PENETRATION. Unknown, nonfinite,
missing geometry, missing frames, pin drift or record-identity discrepancy causes
REFUSED, with evidence, never a zero or a pass. Replay completion is separate
from a SURVIVOR diagnostic; a negative result is useful and cannot close playability.

## Frozen predictions and falsifiers (not pass targets)

P1: all 354 Stage 1 keys join exactly one Stage 2 row. Contradictions: missing,
extra, duplicate, malformed or changed inherited metadata; reject before geometry.
P2: every replayed pose has exactly the same 20 body IDs including the pad and
anchor. Contradictions: omitted/duplicate/extra body record, incomplete work unit.
P3: raw body/trunk results for inherited recorded bodies and anchor reproduce
those recorded class/margin/depth columns exactly. Contradictions: any exact float
or class disagreement, including the envelope. Record drift; do not loosen bounds.
P4: the first four canonical q_zero_CONTROL rows are byte-identical between a
straight serial primitive loop and the work-unit replay, across independently
started runner processes and a reversed submission order. Contradiction: ANY
canonical payload byte difference. Do not scale until this control gate closes.
P5: omitted pad and/or anchor records prevent at least one old survivor from
passing the unchanged all-body diagnostic. Contradiction: all 354 pass both
diagnostics; this is a legitimate falsified prediction, NOT an instrument error.
The source receipts already record envelope penetration; this is a disclosed
prediction based on existing evidence, not a blinded trial or fresh measurement.
P6: deterministic canonical combination closes over exactly 354 pose keys / 7,080
body records. Contradictions: missing, duplicate, tampered, foreign-input or foreign-
prereg units; combine MUST refuse and preserve the partials.

## Runner/resource and retention contract

CPU only through E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run.
No detached process, worktree/clone, GPU request, shared service restart or cleanup.
Use --slot 2 for bounded preparatory runner checks while automatic selection is
blocked by the existing slot-0 unsafe_relative_path outputs/ recovery defect.
This is ordinary approved slot selection, not repairing or bypassing a runner
refusal; if slot 2 is BUSY honor >=10 s backoff. No --root alternate runner.
Scientific runs use the same approved runner and a free authorized slot.
Profile: four slots, <=4 threads/job, 16 GiB aggregate committed memory/job,
24 GiB host reserve, >=40 GiB memory admission, <=2 GiB scratch/job,
<=256 MiB retained output/job, <=1 MiB runner diagnostic tail. Planned scientific
unit timeout 600 s; control timeout 600 s; combination timeout 120 s. No timeout
increase without declaring it as an operational amendment before rerun.
A unit's deterministic payload has no wall-clock/process/path/job metadata;
separate progress records and runner receipts carry execution identity/timing.
Persist each completed pose atomically under CHIMERA_OUTPUT_DIR/replay/units;
write progress/error status before exit. Declare --keep outputs/replay (no trailing
slash) so the runner preserves partial units on failure or timeout. Canonical
combination validates all input/prereg/pose/body identities before sorting.
Execution completion requires runner PASSED + cleanup_verified AND content checks.
Never call queued work launched, fixtures runtime evidence, or author checks approval.

## Mandatory execution boundary

This proposal is authored before implementation. The project requires a separate
preregistration commit by its publication owner and Lieutenant/Captain release.
No commit/push/PR was requested in this task, and no publication credential was
issued to this agent. Therefore scientific collision execution MUST remain blocked
until the existing publication owner pins these exact preregistration bytes and
issues a hash-bound release identifying task, owner, revision and control-first scope.
A seal is NOT a substitute for that commit. Preparation/metadata checks and clearly
labeled synthetic unit tests can execute through the approved runner; they do not
read actual collision geometry or qualify the serial control slice.

The delivered CLI must fail closed before model construction without the publication
pin and release. A full-run invocation must additionally demand the byte-identity
control-gate artifact. The final report must state those gates as PENDING unless
actually completed. Independent review/acceptance remain with a different agent.
