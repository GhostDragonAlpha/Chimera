# V03 Qualification Pass

Corrections to V03_LEDGER.md, applied by the V03 author after ASTRA's
qualification direction. V03_LEDGER.md is preserved unchanged; this file
annotates and corrects it. Scope: read-only. No production edits, no live-
engine control, no new broad audit, no live experiment.

## Corrections made, and one self-correction

  C1. V03 section 2.5 "numerically confirm a co-phased march" is RETRACTED as
      a verified interpretation (Q3).
  C2. V03 section 7.3 "target branch ... astra/gait-capture @ e0ea5a56" is
      RETRACTED as a prescription (Q6). Big Pickle must fetch and record the
      actual remote head.
  C3. An earlier draft of this file claimed V03's arithmetic was wrong. That
      claim is itself RETRACTED: 331 x dt = 5.5167 s is correct (Q4.0).
  C4. The ZIP/upload step is withdrawn; unpacked paths are handed to Big Pickle
      instead (Q1, Q7.4).
  C5. Capture identity is separated into files / unique contents / documented
      events, and byte-equality is recorded as PLAUSIBLE-SHARED-EVENT, not
      PROVEN (Q2).
  C6. The runtime verdict UNKNOWN is reaffirmed, not resolved (Q5).
  C7. Publication metadata labels the inspected commit accurately and forbids
      prescribing the remote head (Q6).
  C8. One experiment is prioritized; the rest are queued (Q7).

## Q1. Remove the ZIP/upload instruction

The ZIP requirement is withdrawn. The unpacked owned files are handed to Big
Pickle directly (Q7.4). No upload step remains.

## Q2. Qualify capture identity

### Q2.1 Three separate counts

  FILES:              56 PNGs + 2 scripts = 58 files on disk
  UNIQUE CONTENTS:    25 distinct md5s (56 files, 25 distinct images)
  DOCUMENTED EVENTS:   9 capture filenames are named in the audit report

The audit says "59 evidence PNGs". Measured: 56. The gap is 3.

### Q2.2 What explains 59 vs 56

Three PNG pairs are byte-identical AND share a sub-second file mtime - the same
capture written under two names:

  baseline_view.png == final_baseline.png   md5 B8672C12  12:33:05.412350
  orbitOK_00.png    == orbit_view00.png      md5 48E1A0E1  12:31:53.819671
  orbitOK_05.png    == orbit_view05.png      md5 411F9DD3  12:32:04.724236

56 + 3 = 59. If the audit counted 59 filenames, 3 of them are not separate
captures. This is the explanation consistent with the data.

### Q2.3 What byte equality and nearby mtimes do NOT prove

A shared md5 proves identical bytes. A shared sub-second mtime proves the two
files were written by the same process within one write call. Together they
strongly imply one capture event saved under two names. They do not PROVE it.
Alternative explanations the data cannot exclude:

  - Two separate save calls that happened to read the same framebuffer
    (identical bytes, coincidentally near-identical mtimes).
  - One file is a later rename/copy of the other, with the mtime preserved.
  - The capture tool writes both names on every capture - but only 3 pairs
    exist, which argues against a blanket dual-write and toward ad-hoc naming.

Recorded as PLAUSIBLE-SHARED-EVENT, not PROVEN-SHARED-EVENT.

### Q2.4 The 9 named files

The audit names exactly 9 capture stems by filename: final_baseline, frame_000,
glass_001, joint_pose_base, joint_pose_kneeL_100, orbitOK_00, orbitOK_05,
showfix_frame_00, showfix_glass_00. The other 47 PNGs are never named in the
report; they are referenced only by md5, by group, or not at all. The audit's
"59" cannot be reconciled against its own named inventory: it names 9 files
and claims 59.

### Q2.5 What remains unproven

  - Which 3 filenames the audit intended as duplicates, if any.
  - Whether any capture was made and its file lost (no evidence either way).
  - The exact number of distinct capture EVENTS, as opposed to distinct files
    or distinct images. Only the audit's prose step log documents events; it is
    not machine-verifiable.---

## Q3. Correct the gait interpretation

### Q3.1 What is measured (preserved, unchanged)

  path:      E:/PythonChimera/Saved/gait/stride.json
  bytes:     80635
  SHA-256:   883ed9d87859dfe4e4126631149ca09b250e1be441357f3db4a16c468b01f50a
  format:    chimera-stride-1
  dt:        0.016666666666666666  (= 1/60 s)
  samples:   331, joints: 28

Channel categories (preserved exactly):
  constant zero ............ 22 joints
  constant nonzero ......... 2 joints  (ankle_L, ankle_R = -0.053109, range 0)
  varying and nonzero ...... 4 joints  (hip_L, hip_R, knee_L, knee_R)

Ranges (preserved):
  hip_L   [-1.114924, -0.002815]  range 1.112108
  hip_R   [-1.114896, -0.003484]  range 1.111411
  knee_L  [-0.088504,  2.507320]  range 2.595824
  knee_R  [-0.088162,  2.507284]  range 2.595446
  ankle_L  -0.053109 constant
  ankle_R  -0.053109 constant

Correlations (preserved):
  pearson r(hip_L, hip_R)  = +0.7294, same_sign_fraction = 1.000
  pearson r(knee_L, knee_R) = -0.2982, same_sign_fraction = 0.000
  pearson r(hip_L, knee_L)  = -0.7044
  pearson r(hip_R, knee_R)  = -0.5863

### Q3.2 What is RETRACTED

V03 section 2.5 called the file "a co-phased march" and said the correlations
"numerically confirm the 2026-09-06 09:22 burst eye read". Both phrasings are
RETRACTED as verified interpretations.

The file's declared top-level keys are: format, dt, n_samples, n_joints,
names, theta, prep, loop_t0, stride_t, clock, gates. It contains NO joint axis
definitions, NO rest-frame values, NO forward-kinematics evaluation, and NO
foot trajectory or ground-contact data. The theta array is a 331 x 28 matrix
of numbers named by joint label only.

Without joint axes and rest frames, a numeric channel named hip_L cannot be
identified as a hip flexion/extension, abduction/adduction, or rotation axis.
Without FK evaluation, the theta values cannot be converted to foot positions.
Without foot trajectories, there is no evidence about stance, swing, or contact.

### Q3.3 What the correlations actually establish

MEASURED, no interpretation:
  - hip_L and hip_R move together (r = +0.73, always the same sign).
  - knee_L and knee_R move independently (r = -0.30, never the same sign).
  - Within each leg, hip and knee are opposite-phase (r ~ -0.6 to -0.7).
  - The ankle channels are constant across all 331 samples.

INTERPRETATION, unverified:
  - That this pattern is a "march", "walk", "crawl", "gallop", or any gait
    category.
  - That hips moving together is anatomically co-phased rather than an artifact
    of the axis convention.
  - That independent knees represent a scissor/alternating gait rather than an
    artifact of the axis convention.
  - That the constant ankle is a plantarflexed pose, a neutral pose, or a
    missing channel.

The 09:22 burst eye read described the same pattern in gait language ("both
hips share the same sign and move together... the knees do the same... the
ankles are the giveaway: ankle_R and ankle_L read -3 degrees in all four frames,
dead constant"). The eye's description is a plausible reading of the numbers.
It is not independently verified, and the eye has no file access by contract,
so it could not have seen the axis definitions either.

### Q3.4 Constant ankle angles

A constant ankle angle is a POSE, not a defect verdict. It is consistent with
(a) a fixed plantarflex offset in the rest pose, (b) an ankle joint not driven
by this stride, or (c) a deliberate simplification. The file contains no
information that distinguishes these. I do not assert defective locomotion, and
I do not ask Alan to decide technical sufficiency from channel counts.---

## Q4. Clarify timing

### Q4.0 RETRACTION of a correction made earlier in this file

An earlier draft of this file claimed "V03 section 2.1 said 'duration: 5.5167 s
(= 331 x dt)'. That arithmetic is wrong." That claim is RETRACTED. 331 x dt =
5.516666... s, which rounds to 5.5167. V03's arithmetic was correct. The
distinction below is still worth stating and is now stated without attacking
V03.

### Q4.1 Two durations, distinguished

The file declares dt = 1/60 s and n_samples = 331.

  SPAN from first sample to one interval past the last: 331 x dt = 5.5167 s
    (this is what V03 reported, and it is correct)
  INTERVAL from first sample to last sample: 330 x dt = 5.5000 s

Both are true of the same data. Which one a reader wants depends on whether the
first sample is treated as t=0 (span) or only the gap between the first and
last samples is wanted (interval). The file does not say which.

### Q4.2 This is a sample interval, not a playback convention

dt = 1/60 s is the declared sample spacing. It says nothing about how the
engine consumes the file. The file does not declare a playback convention.

POSSIBLE but UNDECLARED playback conventions:
  (a) hold-each-sample-one-frame: each sample displayed for 1/60 s of wall
      time, total playback 5.5167 s of wall time.
  (b) resample-to-frame-rate: the 331 samples are resampled to the display
      refresh rate and the wall duration differs.
  (c) real-time-as-fast-as-possible: the samples are stepped at their own rate
      independent of wall clock.
  (d) the file is not played back at all; it is a reference trajectory.

The STATUS dock in glass_001 reads "show t=1430.65s x1.00" and the timeline
reads "t = 86.655 s / 112.0 s (lap 12)". These are the engine's own clocks and
do not name this file or its playback convention. The file's clock block
(T_stance=1.8319640364329155, omega=1.3214803476775403, speed=2.355349630370487)
is internal to the stride derivation and is not a wall-clock playback spec.

### Q4.3 Explicit timestamps

If the first sample is anchored at simulation time t0, sample i is at
t0 + i/60 s. t0 is not recorded in the file (loop_t0=1.8319640364329155 is a
stride-phase constant, not an anchor). No absolute simulation timestamp exists
in the file.

### Q4.4 What this means for diagnosing playback

A same-camera timed capture sequence (the prioritized experiment in Q7) is the
only evidence that could link the file's sample interval to the engine's wall
clock and to the on-screen show clock. Nothing in the saved evidence does.---

## Q5. Preserve the runtime verdict UNKNOWN

Restated and reaffirmed, not weakened and not resolved.

Whether E:/PythonChimera/Saved/gait/stride.json was loaded during the static
SHOW captures remains UNKNOWN. No recorded link exists:

  - The P02 audit never names stride.json. Its gait references are the branch
    name astra/gait-capture, the registry read "joints/gait/water/frost/matter
    OFF", and the observation that "no gait/steps are feeding the mesh". None
    is a load event, a path, or a hash.
  - dyad_log.txt and dyad_log.jsonl contain only the eye reading the on-screen
    STATUS dock ("gait CPG: no pack | steps 0"). The eye has no file access by
    contract (BRIEFING.md) and cannot have seen the file.
  - No capture script, request log, or engine log in the evidence tree records
    a stride/gait load event, path, or content hash.
  - The file's mtime (2026-09-05 21:50) is ~14.5 h before the 12:2x session
    (2026-09-06 12:28-12:36). A stale mtime is consistent with either "loaded
    from an old file" or "never loaded"; it discriminates nothing.

The audit's "no gait pack / steps 0" is a reading of the live STATUS dock at
capture time. It accurately describes runtime state and is NOT evidence that
this file was or was not the source.

Competing explanations remain open and are NOT chosen between:
  A. stride.json was loaded but the CPG was paused/stepped=0 at capture time.
  B. stride.json was never loaded; a different (unrecorded) gait source exists.
  C. The show clock advances but the mesh driver is disconnected upstream.
  D. The stride file is the source but only 4 joints are wired to the mesh.

The 4-joint structure of the file is a property of the FILE and would be true
under any of A-D. It cannot be used to favour one explanation.---

## Q6. Correct publication metadata

### Q6.1 What this author inspected (the inspected commit)

I inspected the working tree at E:/PythonChimera, branch master, and its HEAD:

  HEAD:  51cd7212fd6ef2cfda95c330abcc2ff154cc6141
  short:  51cd7212
  msg:   "Keep the camera above the floor: CAM_PHI_BAND, CAM_FLOOR_GATE, FIT v6"

This is the commit the P02 audit itself checked out (audit section 1: "Checkout:
51cd7212 (master)"). All V02/V03 evidence was reviewed against this commit.
This is the INSPECTED commit.

### Q6.2 RETRACTED: e0ea5a56 is NOT prescribed as the current remote target

V03 section 7.3 stated "target branch: remotes/origin/astra/gait-capture @
e0ea5a56". That value was captured from the local remote-tracking ref at the
moment of writing and is RETRACTED as a prescription. It is stale the moment it
is read: a remote branch moves without the local clone knowing. Big Pickle MUST
fetch astra/gait-capture and record its actual head at publication time. I do
not know the current remote head.

### Q6.3 What Big Pickle must record at publication time

  - actual remote head of astra/gait-capture AFTER fetch (full SHA)
  - merge-base of that head and 51cd7212 (full SHA)
  - the staged diff: file list, per-file blob SHA-256, and line-ending state
  - explicit accounting for any line-ending normalization applied to the
    staged files (see Q6.4)
  - if the remote advanced since fetch, STOP publication and report the
    conflict; do not overwrite another agent's work

### Q6.4 Line endings

The owned deliverables are written with LF line endings (Python writes \n; the
markdown chunks were written with \n). If the target repository normalizes to
CRLF on commit, the blob hashes in the manifest will not match the committed
blobs. Big Pickle must record the actual committed blob hashes and note the
normalization, rather than asserting the manifest hashes are the blob hashes.

### Q6.5 Merge-base at inspection time (informational only)

At inspection time the local remote-tracking ref was e0ea5a56 and the merge-
base of 51cd7212 and that ref was 7cafb33297e8c35c2bb32d09f812e3dafde34df3.
This is an observation from the inspection-time clone, NOT a prescription.---

## Q7. Prioritized future experiment and owned-file list

### Q7.1 Priority order

ONE experiment is prioritized. All others are queued behind it.

  PRIORITY 1 - fixed-camera timed sequence with full records attached.
  PRIORITY 2 - foot contact (queued).
  PRIORITY 3 - joint sweep (queued).
  PRIORITY 4 - self-intersection (queued).
  PRIORITY 5 - camera-POST robustness recheck (queued, non-visual).

### Q7.2 PRIORITY 1 specification (NOT performed)

Goal: the prerequisite for diagnosing playback. Nothing in the saved evidence
links the stride file's sample interval to the engine's wall clock or to the
on-screen show clock; this experiment is the only capture that could.

  camera: FIXED. Any view showing the full figure, front or side preferred.
    The current set is rear-only, which is itself a reason to move the camera.
    Do not use fit_dyad; its framing biases toward a rear view.
  endpoint: /frame only, one PNG per request. Do not batch.
  sequence: 10-12 captures at equally spaced simulation times spanning ONE
    declared stride period (stride_t = 3.6639 s), plus 2-3 extra captures
    immediately after the period to confirm repetition.
  timing: advance the show clock by a KNOWN amount between captures. Record
    the requested step and the on-screen t readout from the matching /glass at
    each capture. Do not assume the clock advanced by the requested amount.

  REQUIRED RECORD ATTACHED TO EACH CAPTURE (a JSON sidecar per PNG):
    1. cam_radius, cam_theta, cam_phi actually applied (requested AND confirmed)
    2. the full 28-joint theta vector at that instant
    3. simulation time t (from the show clock / timeline readout)
    4. wall-clock timestamp of the capture
    5. the STATUS dock's gait source field, gait steps, and steps_total
    6. the HTTP request body and the HTTP response body for the request that
       produced the capture
    7. the frame md5

  Without records 1-3 no frame is interpretable; without 4-5 the file-to-
  runtime link stays UNKNOWN (Q5); without 6 the silent-fallback class of bug
  seen in orbit_00..07 stays undiagnosable.

  Success criterion: a capture-to-capture delta in the mesh that corresponds
  to a recorded delta in the joint vector and a recorded delta in simulation
  time. If the mesh does not change between two captures whose joint vectors
  differ, playback is not driving the mesh and the diagnosis is complete.

### Q7.3 Queued experiments (brief, not specified)

  PRIORITY 2 - foot contact: low cam_phi, 4 poses (rest, knee_L=100, shallow
    ankle dorsiflexion, opposite knee also bent). Sliding requires PRIORITY 1
    first - a same-camera time series with the foot on the floor.
  PRIORITY 3 - joint sweep: knee_L at 0/15/30/45/60/75/90/100 deg, side view,
    close framing so the fold fills ~200-300 px. Continuity cannot be judged
    from the two endpoints in the current set.
  PRIORITY 4 - self-intersection: 3/4 view of knee_L=100, then both knees bent.
    The rear view cannot separate the legs in depth.
  PRIORITY 5 - re-issue the orbit_00..07 request and capture the HTTP response
    body, not just the frame. Non-visual companion.

### Q7.4 Owned files handed to Big Pickle (unpacked, on disk)

Directory: E:/PythonChimera/.tmp/v02_20260906_190511/

  README.md                        339 B
  V02_REPORT.md                    31906 B   (prior review, unchanged)
  V03_LEDGER.md                    25100 B   (V03 correction ledger)
  V03_QUALIFICATION.md             (this file)
  v03_packet_manifest.txt          4332 B
  v03_packet.zip                   3421251 B (WITHDRAWN as a required step;
                                            retained as a convenience artifact)
  v03_packet/                      unpacked packet
    analysis/  (9 files: scripts + raw extracts)
    reports/   (3 files)
    images/    (16 verbatim originals)
  evidence/                        raw extracts + audit report + dyad briefing
                                    + dyad log + stride.json

Big Pickle should use the UNPACKED paths, not the ZIP. The ZIP is retained as a
convenience artifact only; it is not a required upload.

### Q7.5 What this author did not do

No production edits. No live-engine control. No commit, push, branch switch, or
working-checkout modification. Nothing written under ChimeraEngine/engine/build/.
All original evidence verified unchanged on disk after this pass.