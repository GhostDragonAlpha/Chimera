# V03 Correction Ledger

Directory: E:/PythonChimera/.tmp/v02_20260906_190511
V02 report preserved at V02_REPORT.md. This is a correction ledger.

Scope: read-only. No live-engine requests, camera control, code changes,
installation, commits, or pushes. All originals preserved.

---

## 1. Reconcile capture counts: 59 (audit) vs 56 (measured)

### 1.1 Exact measured inventory

Directory: E:/PythonChimera/.tmp/p02_visual_20260906_122824/
56 PNGs + 2 Python scripts = 58 files. Every PNG is 2560x1440 RGBA,
exactly 14748233 bytes. The 2 non-PNGs are _dyad_baseline.py (1177 B) and
_dyad_reads.py (3966 B).

### 1.2 Inclusion rules

All 56 share: .png extension, 2560x1440, 14748233 bytes, mtime in
12:28:31 - 12:33:05 2026-09-06. Nothing outside this directory was counted.
The audit's "59 evidence PNGs" is the only place 59 appears.

### 1.3 The 3-count gap is explained by 3 exact duplicates

56 measured + 3 counted-twice = 59. Three PNG pairs are byte-identical AND
share the same sub-second file mtime - the same capture written under two
names:

  baseline_view.png  ==  final_baseline.png   md5 B8672C12  12:33:05.412350
  orbitOK_00.png     ==  orbit_view00.png      md5 48E1A0E1  12:31:53.819671
  orbitOK_05.png     ==  orbit_view05.png      md5 411F9DD3  12:32:04.724236

If the audit counted 59 names, 3 of them are not separate captures. This is the
only explanation consistent with the measured data.

### 1.4 Larger md5 groups (repeated captures of one static pose, not copies)

Three md5s recur across files written at DIFFERENT times:

  3C1E06EA  17 files: cam_post_orbit, joint_pose_base, orbit_00..07,
            orbit_corr_pre, showplay_00..05  -> rest pose + failed orbit
  F4355D89   8 files: cam_pre_orbit, frame_000..004, frame_verifyA/B
            -> SHOW-static /frame pose
  48E1A0E1   7 files: orbitOK_00, orbit_view00, showfix_frame_00..04
            -> orbit-start / showfix-static pose

25 distinct md5s across 56 files.

### 1.5 V02 correction

V02 Appendix A1 left the gap open. This ledger closes it: the audit double-
counted 3 exact duplicates. No missing files are asserted.

### 1.6 Files NOT counted and why

  _dyad_baseline.py, _dyad_reads.py - capture scripts, not evidence images.
  P02_PLATFORM_AUDIT.md - the report, not a capture.
  Saved/dyad/2026-09-06_*_burst/ - five dirs with NO PNGs; dyad read text only.
  Saved/dyad/dyad_log.jsonl - the eye log, not a capture.---

## 2. Audit stride data numerically

### 2.1 File identity

  path:      E:/PythonChimera/Saved/gait/stride.json
  bytes:     80635
  SHA-256:   883ed9d87859dfe4e4126631149ca09b250e1be441357f3db4a16c468b01f50a
  format:    chimera-stride-1
  dt:        0.016666666666666666  (= 1/60 s)
  samples:   331
  joints:    28
  duration:  5.5167 s  (= 331 x dt)
  loop_t0:   1.8319640364329155
  stride_t:  3.663928072865831
  clock:     {"T_stance":1.8319640364329155,"omega":1.3214803476775403,
              "h_com":5.6156399855089,"leg":3.0912846784860637,
              "speed":2.355349630370487}
  gates:     {"foot_max":9.542e-05,"gate":0.0280781999275445,
              "jump_max":0.09524731203134795,"jump_bound":0.11637817184894707,
              "velocity_jump":2.739e-15,"startup_closure":8.882e-16,
              "tracking":"PASS","physical_contact":"UNVERIFIED"}

Units: the file declares no unit string; the joint values are radians and the
clock fields are seconds. dt=1/60 s is the declared sample interval.

### 2.2 V02 statement corrected

V02 said "26 of 28 joints zero, only hips/knees move". Measured:
  constant zero ............ 22 joints
  constant NONZERO ......... 2 joints  (ankle_L, ankle_R = -0.053109)
  varying and nonzero ...... 4 joints  (hip_L, hip_R, knee_L, knee_R)
V02's "26" was wrong in both numbers. The correct constant-zero count is 22,
and the nonzero channels are 6, not 2. V02's shorthand "only hips/knees move"
happened to be directionally right but numerically incomplete: the ankles are
nonzero-but-constant, which V02 folded into "zero".

### 2.3 Full channel table (331 samples each)

CONSTANT ZERO (22): neck, jaw, spine_upper, spine_mid, spine_lower, tail_base,
tail_mid, shoulder_L, shoulder_R, elbow_L, elbow_R, wrist_L, wrist_R,
tail_tip, ear_L, ear_R, lid_L, lid_R, brow_L, brow_R, mouth_L, mouth_R.
min=0 max=0 range=0 nonzero=0 varying=NO uniq=1.

CONSTANT NONZERO (2):
  ankle_L  min=-0.053109 max=-0.053109 range=0.000000 nonzero=331 varying=NO
  ankle_R  min=-0.053109 max=-0.053109 range=0.000000 nonzero=331 varying=NO

VARYING AND NONZERO (4):
  hip_L   min=-1.114924 max=-0.002815 range=1.112108 nonzero=331 varying=YES uniq=331
  hip_R   min=-1.114896 max=-0.003484 range=1.111411 nonzero=331 varying=YES uniq=331
  knee_L  min=-0.088504 max= 2.507320 range=2.595824 nonzero=331 varying=YES uniq=331
  knee_R  min=-0.088162 max= 2.507284 range=2.595446 nonzero=331 varying=YES uniq=331

### 2.4 Constant nonzero pose vs animation

ankle_L and ankle_R are a CONSTANT NONZERO POSE, not animation: all 331
samples equal -0.053109 to 6 decimal places, range exactly 0.000000. This is
a fixed plantarflex offset baked into every frame. It is a pose, identical to
the rest pose's ankle value, and it contributes nothing temporal.

hip_L/R and knee_L/R are genuine animation: 331 unique values each, full-range
oscillation, Pearson r(hip_L, knee_L) = -0.7044 (opposite phase within a leg).

### 2.5 L/R relationship - independent confirmation of the 09:22 eye read

  hip_L  vs hip_R:  pearson_r =  0.7294, same_sign_fraction = 1.000
  knee_L vs knee_R:  pearson_r = -0.2982, same_sign_fraction = 0.000
  ankle_L vs ankle_R: identical (diff = 0.000000 everywhere)

The hips move TOGETHER (same sign always, r=+0.73) and the knees move
INDEPENDENTLY (never the same sign, r=-0.30). This is a co-phased march, not an
opposite-phase scissor gait. This numerically confirms the 2026-09-06 09:22
burst eye read ("both hips share the same sign and move together... the knees
do the same... the ankles are the giveaway: ankle_R and ankle_L read -3 degrees
in all four frames, dead constant").

### 2.6 What the file is and is not

It is a 5.5 s, 4-joint, co-phased march with a fixed ankle offset and a static
upper body. It is NOT a full 28-joint walk: 22 joints never move, 2 are frozen
nonzero, 4 animate. Whether it is a correct or a defective walk is a question
for the gait author, not for this review.---

## 3. Separate file content from runtime cause

### 3.1 What is proven about the stride file's content

- It exists at E:/PythonChimera/Saved/gait/stride.json, 80635 bytes,
  SHA-256 883ed9d8..., mtime 2026-09-05 21:50:04 (verified).
- It contains a 4-joint co-phased march over 5.5167 s (see section 2).
- Its gates field reports tracking=PASS, physical_contact=UNVERIFIED.

### 3.2 What is NOT proven, and the UNKNOWN

**Whether this exact file was loaded during the static SHOW captures is
UNKNOWN.** No recorded link exists. Specifically searched and found absent:

- The P02 audit never names stride.json. Its only gait references are:
  (a) line 16 - the branch name remotes/origin/astra/gait-capture;
  (b) line 165 - the registry read "joints/gait/water/frost/matter OFF";
  (c) lines 189, 194, 219 - the observation that "no gait/steps are feeding
      the mesh" and "gait CPG: no pack | steps 0".
  None of these is a load event, a path, or a hash.
- dyad_log.txt and dyad_log.jsonl: the only gait mentions are the eye reading
  the on-screen STATUS dock ("gait CPG: no pack | steps 0", "gait steps=0
  omega=7.85"). The eye has no file access by contract (BRIEFING.md line 3);
  it cannot have seen the file.
- No capture script, no request log, no engine log in the evidence tree records
  a stride/gait load event, path, or content hash.
- The file's mtime (2026-09-05 21:50) is ~14.5 hours BEFORE the 12:2x
  capture session (2026-09-06 12:28-12:36). A stale mtime is consistent with
  either "loaded from an old file" or "never loaded"; it discriminates
  nothing.

### 3.3 The audit's explanation is a runtime readout, not a causal claim

The audit says SHOW was static because "no gait pack" and "steps 0". That is
a reading of the live STATUS dock at capture time. It is accurate as a
description of runtime state and it is NOT evidence that stride.json was or
was not the source. A "no pack" readout is compatible with (a) the file
existing but not wired, (b) the file being wired but the CPG not running, or
(c) a different gait source entirely.

### 3.4 Competing explanations - deliberately not chosen between

  A. stride.json was loaded but the CPG was paused/stepped=0 at capture time.
  B. stride.json was never loaded; a different (unrecorded) gait source exists.
  C. The show clock advances but the mesh driver is disconnected upstream.
  D. The stride file is the source but only 4 joints are wired to the mesh.
The saved evidence supports none of these over the others. The 4-joint
structure of stride.json (section 2) is a property of the FILE and would be
true under any of A-D; it cannot be used to favour one.

### 3.5 What WOULD settle it

A recorded load event naming the path and hash, or a same-engine capture
showing the STATUS dock's gait source field pointing at this file. Neither
exists in the saved evidence. Marked UNKNOWN, not resolved.---

## 4. Reconstruct the failed camera attempt (orbit_00..07)

### 4.1 The evidence, exactly

  orbit_00..07.png: 8 files, mtimes 12:31:00.35 -> 12:31:14.24 (2.0 s apart),
  ALL md5 3C1E06EA, all 14748233 bytes.
  That md5 is shared with 9 other files: cam_post_orbit, joint_pose_base,
  orbit_corr_pre, showplay_00..05.
  orbit_corr_pre.png (12:31:40.21) is ALSO 3C1E06EA.
  orbit_corr_post.png (12:31:42.53) is E9F5A0F3 - DISTINCT.

### 4.2 What the equal images demonstrate

Eight POSTs at 2.0 s spacing, each nominally a different cam_theta, produced
eight byte-identical frames. The camera did not move. The mesh did not move.
Nothing in the rendered 3D scene changed across 14 seconds of POSTs.

### 4.3 What they do NOT demonstrate

They do not establish the API's CAUSE. Equal images show no visual change; they
do not say whether the request was rejected, silently defaulted, applied to a
different parameter, or applied but the camera was clamped to a constant.

### 4.4 What IS known about acceptance, parameter names and timing

KNOWN:
  - The audit's HTTP trap note (line 171): /camera requires keys
    cam_radius, cam_theta, cam_phi. Posting radius/theta/phi silently falls
    back to defaults. This is a documented key-name sensitivity.
  - The working orbit (orbitOK_00..09, 12:31:53.8 -> 12:32:13.4, 2.15 s apart,
    10 distinct md5s) used the same endpoint and DID change the frame. So the
    endpoint is capable of moving the camera and the renderer is capable of
    re-projecting.
  - The failed attempt (orbit_00..07) precedes the working attempt (orbitOK_*)
    by ~40 s. orbit_corr_pre (12:31:40, 3C1E06EA) sits between them and is
    still the rest pose; orbit_corr_post (12:31:42, E9F5A0F3) is the first
    distinct frame after the failed run.
  - The audit's section 7.1 table lists the working sweep's requested values
    (cam_theta 0.5 -> 6.15 rad) but does NOT record the values requested during
    the orbit_00..07 run, nor the HTTP response bodies for any POST.

UNKNOWN (not inferrable from images):
  - The exact request body sent for orbit_00..07.
  - The HTTP status or response body for any POST.
  - Whether the failure was a key-name mismatch, a value out of range, a
    clamping to a band (CAM_FLOOR_GATE / CAM_PHI_BAND are in the commit
    message), or a client-side scripting error.
  - Whether orbit_corr_pre/post were a deliberate correction step or a
    separate probe.

### 4.5 Reconstructed timeline

  12:29:57  cam_pre_orbit.png    F4355D89  (SHOW-static pose, pre-orbit)
  12:29:59  cam_post_orbit.png   3C1E06EA  (rest pose - first rest-pose capture)
  12:30:13  joint_pose_base.png  3C1E06EA  (rest pose)
  12:30:15  joint_pose_kneeL_100  0464E3EA  (POSED - distinct)
  12:30:31-42 showplay_00..05     3C1E06EA  (6 captures, all rest pose)
  12:31:00-14 orbit_00..07        3C1E06EA  (8 POSTs, NO CHANGE)
  12:31:40  orbit_corr_pre        3C1E06EA  (still rest)
  12:31:42  orbit_corr_post       E9F5A0F3  (first distinct frame)
  12:31:53-13:4 orbitOK_00..09     10 distinct md5s  (WORKING orbit)
  12:32:29-44 showfix_frame_00..04  48E1A0E1  (static /frame)
  12:32:30-45 showfix_glass_00..04  5 distinct  (changing HUD only)
  12:33:05  baseline_view == final_baseline  B8672C12  (duplicate pair)

### 4.6 Net result

The failed attempt is real, reproducible evidence of a silent camera-POST
failure, and it is the only negative result in the set. Its cause is not
recoverable from the saved images. It is a contract/robustness observation for
the API author, not a rendering defect.---

## 5. Refined verdicts - what each claim is supported by

### 5.1 Two different captured poses

SUPPORTED. joint_pose_base.png (md5 3C1E06EA) vs joint_pose_kneeL_100.png
(md5 0464E3EA). Evidence: the two md5s differ; a pixel diff (threshold 10/255)
shows 69,768 changed pixels confined to bbox x 1079-1240, y 291-972 - a narrow
region around the screen-left leg. The screen-left leg gains a forward knee
bend while the screen-right leg and everything else is unchanged. This is a
single-joint edit (knee_L theta=100) applied to an otherwise identical camera
and scene. CONFIRMED as two distinct poses.

### 5.2 A timed deformation sequence

NOT SUPPORTED. No capture in the set shows the same camera at two different
simulation times with a deforming mesh. The only time-varying element is the
HUD (showfix_glass_00..04). The /frame captures at different times
(frame_000..004, showfix_frame_00..04, showplay_00..05) are all byte-identical
to their group md5. There is no evidence of mesh deformation over time.

The 2026-09-06 09:xx burst session (dyad_log lines 83-84) DOES describe frames
with real gait joint values, but those images are not in this capture set and
were captured ~3 hours earlier under a different session. They are prior-session
evidence, not evidence about the 12:2x P02 session.

### 5.3 Camera movement

SUPPORTED, with the caveat that one attempt failed. orbitOK_00..09 are 10
distinct md5s at 2.15 s spacing; between orbitOK_00 and orbitOK_05 the tail
flips from screen-right to screen-left (parallax), the foot toe visibility
changes, and 125,889 pixels change across bbox x 1004-1530, y 0-769. The figure
size stays roughly constant, consistent with a rotation at fixed radius.
Between orbitOK_00 and orbitOK_09, 123,315 pixels change across bbox
x 0-2559, y 0-1017. This is a camera rotating around a static mesh.

FAILED INSTANCE: orbit_00..07 (8 POSTs, 2.0 s spacing) are all md5 3C1E06EA -
no camera movement at all. See section 4.

### 5.4 Changing HUD content

SUPPORTED and cleanly separated from the 3D scene. showfix_glass_00..04 are 5
distinct md5s while the corresponding showfix_frame_00..04 are one md5
(48E1A0E1). A pixel diff between showfix_glass_00 and showfix_glass_04 shows
29,530 changed pixels in bbox x 410-2537, y 128-1434. The visible changes are
confined to HUD readouts: FPS 103 -> 74 -> 34 -> 7, frame-time 7.05 -> 10.77 ->
26.77 -> 143.00 ms, SHOW label cycling ear_R/lid_R/mouth_R/brow_L, timeline
t advancing 86.655 -> 93.742 -> 108.765 s, and the REEL gaining thumbs. The 3D
creature in the embedded viewport does not move. This is the strongest
separation of HUD from scene in the whole set.

### 5.5 A successful live request

SUPPORTED for camera and joint POSTs. The camera orbit (5.3) and the knee
joint POST (5.1) are both successful, distinct, reproducible request->frame
pairs. The /glass endpoint also responds (5.4). No other endpoint was tested
in this set.

### 5.6 Text on screen claiming "live"

PRESENT but NOT VERIFIED AS MOTION. glass_001 and showfix_glass_* contain a
STATUS (live) header, running counters (FPS, ft, show t, timeline t, wall
clock), a PLAYING flag, and an advancing playhead. These are text fields of a
type that updates in real time. Whether the window was actually updating at
the instant each PNG was written cannot be determined from a single still per
capture. The eye's "reads as live" judgment is an inference from the presence
of live-type counters, not a demonstration. I record it as a separate confidence
tier from 5.3/5.1, which ARE demonstrated.

### 5.7 Explicit non-claims

- No continuous motion is inferred from the two endpoint poses in 5.1.
- No velocity, acceleration, or smoothness is claimed anywhere.
- No joint angle in degrees is asserted (no pixel-to-world calibration exists).
- The creature's planted-vs-hovering status is not claimed (rear view; feet and
  reflection overlap in projection).
- The knee bend's anterior/posterior axis is not claimed (rear view).---

## 6. Next visual experiment specification (NOT performed)

Design goal: smallest front/side/rear sequence that can inspect a joint sweep,
foot contact, and possible self-intersection. Nothing below has been run.

### 6.1 Common setup

  - Endpoint: /frame only (no UI). Camera bookmark: a NEW one named
    review_v03, distinct from fit_dyad, so framing does not inherit the
    fit_dyad bias toward a rear view.
  - Numerical companion required for every capture: a JSON sidecar recording
    cam_radius, cam_theta, cam_phi, the full 28-joint theta vector, the show
    clock t, and the STATUS dock's gait source field. Without the sidecar no
    frame is interpretable.
  - Strain tint must be ON (STATUS strain != "no hinge") or the skin
    deformation question is untestable by construction.
  - Capture one PNG per request. Do not batch.

### 6.2 Joint sweep (tests continuity and surface deformation)

  - Camera: SIDE view, 3/4 front preferred. cam_phi low enough that the knee
    is not foreshortened to a sliver (~20-30 deg above floor).
  - Sequence: knee_L at 0, 15, 30, 45, 60, 75, 90, 100 deg - 8 captures, one
    POST each, same camera, rest pose otherwise.
  - Why 8: the current set has the two endpoints only (0 and 100). Intermediates
    are the whole point. Continuity cannot be judged from endpoints.
  - Close framing so the knee fold fills ~200-300 px vertically; a fold that is
    30 px cannot be distinguished from a kink.
  - Occlusion risk: at high flexion the shin may cross the torso in a side view.
    Record the sidecar joint vector so a pixel ambiguity can be resolved
    numerically.

### 6.3 Foot contact (tests planted vs hovering vs sliding)

  - Camera: LOW cam_phi, near floor level, looking slightly up at the feet.
    A rear or high view cannot establish contact - the feet and their
    reflection overlap in projection at those angles.
  - Sequence: 4 poses - rest, knee_L=100, shallow ankle dorsiflexion, and one
    pose with the opposite knee also bent. One capture each, same camera.
  - Required numerical companion per capture: the ankle joint value, the foot
    vertex z (or the lowest vertex height relative to the floor plane), and a
    pixel measurement of the contact patch centroid.
  - Sliding cannot be seen in one still. To test sliding, capture the SAME foot
    at two simulation times with the foot on the floor; the current set has no
    same-camera time series with a deforming mesh, so this is the missing
    primitive and must be added first.

### 6.4 Self-intersection

  - Camera: 3/4 side view (not rear). The rear view cannot separate the legs in
    depth, which is exactly why self-intersection is untestable in the current
    set.
  - Sequence: the knee_L=100 pose, then the same pose with knee_R also bent to
    a symmetric value. 2 captures.
  - Occlusion to watch: the bent shin and its cast shadow column. In
    joint_pose_kneeL_100 the shadow column below the bent knee is unusually long
    and dark and does not obviously connect to a foot contact patch. Flag it
    for a low-angle re-check.

### 6.5 The missing primitive: a same-camera time series

  - Camera: fixed (any view that shows the full figure, front or side preferred).
  - Sequence: /frame at 10-12 equally spaced simulation times across ONE gait
    cycle, plus the matching /glass at the same times for HUD correlation.
  - This is the only capture that could establish that the mesh actually moves
    over time. Nothing in the current set can. It should be shot FIRST, before
    6.2-6.4, because 6.3 (sliding) depends on it.

### 6.6 Camera-POST robustness recheck

  - Re-issue the exact request that produced orbit_00..07 and capture the HTTP
    response BODY, not just the frame. The silent fallback is a contract issue,
    not a rendering issue, and no image can diagnose it. This is a non-visual
    companion to 6.1.

### 6.7 Ordering

  6.5 (time series) -> 6.3 (contact at low angle) -> 6.2 (sweep at side) ->
  6.4 (self-intersection) -> 6.6 (API recheck). Total ~28 captures plus sidecars.---

## 7. Handoff and publication

### 7.1 Publication boundary

This authorizes evidence/source-packet publication only. It does NOT authorize
production engine changes or merging. Per the handoff, Big Pickle is the single
publisher after collecting the three completed handoffs (G01, P04, V03).

My deliverables as the V03 author:
  - V03_LEDGER.md  (this file)
  - V02_REPORT.md  (prior review, unchanged)
  - README.md
  - _audit_stride.py, _audit_phase.py, _audit_links.py, _l1.py, _l2.py, _dup.py
    (reproducible analysis scripts)
  - _links_raw.txt, v02_dyad_reports.txt, v02_burst_reports.txt (raw extracts)
  - Representative original PNGs copied verbatim from the evidence dir

### 7.2 What I did NOT do

I did not commit, push, switch branches, or modify any tracked file. I did not
write under ChimeraEngine/engine/build/. I did not alter the working checkout.
All analysis was read-only against the saved evidence.

### 7.3 Source state at handoff

  working tree: E:/PythonChimera, branch master
  HEAD:        51cd7212fd6ef2cfda95c330abcc2ff154cc6141
               "Keep the camera above the floor: CAM_PHI_BAND, CAM_FLOOR_GATE, FIT v6"
  tracked modifications (pre-existing, NOT mine):
               Chimera/docs/DREAM_REPORT.md, Chimera/docs/HERALD.md,
               Chimera/docs/HISTORY_BOOK.md,
               ChimeraEngine/engine/_native_end.png,
               ChimeraEngine/engine/_native_start.png
  target branch: remotes/origin/astra/gait-capture @ e0ea5a56
               "Define material foundation and GLM implementation packet"
  merge-base of HEAD and astra/gait-capture: 7cafb33297e8c35c2bb32d09f812e3dafde34df3
  docs/evidence/ on astra/gait-capture: DOES NOT EXIST - the publisher must create it.

### 7.4 Proposed publication layout (for the publisher to execute)

  docs/evidence/v03/
    V03_LEDGER.md
    README.md
    analysis/
      _audit_stride.py
      _audit_phase.py
      _audit_links.py
      _l1.py
      _l2.py
      _dup.py
      _links_raw.txt
      v02_dyad_reports.txt
      v02_burst_reports.txt
    reports/
      V02_REPORT.md
    images/
      <representative originals, copied verbatim, unchanged bytes>
  docs/evidence/g01/   (G01 author's packet)
  docs/evidence/p04/   (P04 author's packet)

### 7.5 Questions reserved for Alan

Appearance, usefulness and perceived quality only. I do not ask Alan to
diagnose API or stride-data defects; those are out of scope for a visual
reviewer and are recorded as technical open items below.

  1. Is the co-phased (hips together, knees independent) march the intended
     gait for this creature, or should the legs be opposite-phase? (This is a
     data question, but its answer determines what "a good walk" looks like,
     which is a perceptual quality question for Alan.)
  2. Does the frozen-ankle pose (-0.053109 rad constant) read as acceptable, or
     should the foot articulate through the cycle?
  3. Is the 4-joint-only stride sufficient to judge locomotion quality, or is
     a fuller joint set needed before the visual experiment in section 6?
  4. Should "reads as live" (inferred from live-type counters) be recorded as a
     separate confidence tier from "demonstrated live" (a same-camera time
     series) in future reviews?

### 7.6 Technical open items (NOT for Alan)

  - stride.json: 22 constant-zero, 2 constant-nonzero, 4 varying joints.
  - Runtime association of stride.json with the 12:2x SHOW session: UNKNOWN.
  - Cause of the orbit_00..07 silent camera-POST failure: UNKNOWN.
  - docs/THE_PLATFORM_BOUNDATION.md, docs/FOUNDATION_P01_REPORT.md,
    docs/FOUNDATION_CONTEXT.md, docs/THE_MATERIAL_FOUNDATION.md, and
    tools/platform_probe/: absent at this checkout.