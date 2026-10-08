# Exact-pose grasp collision replay — preregistration proposal

ID: EXACT-POSE-REPLAY-20261004-BUFFY-PRE-1
Author: Buffy (this Freebuff task; no borrowed fleet identity)
Written UTC: 2026-10-04. Status: PROPOSAL-ONLY; offered to the existing
hand-remediation owner for review. NOT an independent execution assignment.
Ownership/scope correction: Captain direction after the interrupted preparation;
no scientific replay, control slice, competing attempt or publication is authorized
for EXACT-POSE-REPLAY-20261004-BUFFY.

## Selection and authority

The initial read-only entry checks found no separate replay assignment in the
records inspected then; that observation was not a claim or proof of availability.
The Captain has now confirmed that the hand-remediation lane owns these exact
314 primary and 40 control poses. A fresh read of its package corroborates owner
wk-hand-remediation, task HAND-REMEDIATION-20261003-R1-COLLISION-ADJ, base
adc410451951b9057a9c749e7af84cdb9a063b3a. This supersedes the earlier R1-STAGE4
status and unclaimed-task premise. No competing attempt will be created or run.

This directory contains a proposal and reusable code/safeguards for that owner's
review only. The existing lane remains the execution/publication authority; this
author has no authenticated fleet claim. Existing owner files, claims, geometry,
thresholds and exemptions remain untouched. Historical seals/receipts are preserved,
not treated as releases of the revised proposal.

Scope correction: Stage 1 ALREADY adjudicated the anchor VTP against the trunk
and recorded its result, but that result did not gate the survivor predicate.
The omitted collision check is the pad-substituted RIGID BONE. The proposed
replay re-evaluates all bodies at the same stored poses, including that missing
bone check and the already-adjudicated anchor, and reports diagnostic predicates.
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
The `pose_sha256` scope is EXACTLY the canonical JSON object
`{"key": pose_key, "stage1": complete_stage1_row, "stage2": joined_stage2_row}`
serialized by `canonical()` (sorted keys, compact separators, UTF-8, trailing
newline) and hashed with SHA256 by `join_rows()`. It does NOT additionally hash
rebuilt posture values or inherited file pins. The posture NAME is in the pose
key; posture values are separately recorded/validated as `posture_q`, and
inherited file pins are separately checked through `INPUTS.json` and bound by
`inputs_sha256`. Those safeguards are not part of the per-pose hash.

## Replay and outcome space

Each independent unit is one pose key. Evaluate all 20 frames against that row's
analytic cylinder with iv.adjudicate_body_vs_cylinder(frame, o, u, iv.TAU),
including the previously omitted pad-substituted rigid bone AND the anchor VTP
already adjudicated in Stage 1. No early pose rejection
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
P5: adding the omitted rigid-bone check and/or including the already-recorded
anchor adjudication in the diagnostic predicate prevents at least one old survivor
from passing the unchanged all-body diagnostic. Contradiction: all 354 pass both
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

The original proposal preceded implementation. This ownership/scope/hash wording
revision follows implementation and fixture-only checks; it is an unpublished
proposal correction, NOT a retroactive scientific preregistration or sealed result.
EXACT-POSE-REPLAY-20261004-BUFFY remains PROPOSAL-ONLY even if its code passes tests.
Do not request a new replay claim/release for it or run its scientific operations.

Offer code and safeguards to the existing hand-remediation owner for review. Any
adoption must follow that lane's own preregistration, pinned candidate, runner,
control-first validation and independent review rules. Old seals are historical
preparation artifacts, not approvals; a seal is not a publication commit.
Only explicitly labeled synthetic proposal regression tests may run here through
the approved runner; they do not evaluate actual collision geometry or qualify
the serial control slice. No commit, push or PR is made by this author.

The retained CLI's precommitment/control gates are proposed safeguards, not
permission to execute. Actual collision replay, serial parity, full-census checks,
policy decisions and independent acceptance belong to the existing lane.
