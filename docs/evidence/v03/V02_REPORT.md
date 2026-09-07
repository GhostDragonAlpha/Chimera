# V02 Visual Evidence Review — Dots-3-note independent pass

Directory: `E:/PythonChimera/.tmp/v02_20260906_190511`
Written 2026-09-06 19:05 CDT.

Scope: review saved P02 evidence only. No engine, camera, joint, or playback
control. No code, dependency, branch, commit, or push. Nothing written under
`ChimeraEngine/engine/build/`. All original evidence preserved unchanged.

---

## 1. Evidence files reviewed

- `P02_PLATFORM_AUDIT.md` (E:/PythonChimera/.tmp/p02_20260906_122252/) — 302 lines, dated 2026-09-06 12:22 CDT, agent "Big Pickle".
- Capture set: `E:/PythonChimera/.tmp/p02_visual_20260906_122824/` — 59 PNGs, all 2560x1440 RGBA, all exactly 14748233 bytes.
- DYAD log: `E:/PythonChimera/Saved/dyad/dyad_log.jsonl` (578996 bytes) + `dyad_log.txt` (27112 bytes); model `qwen3.8-27b-nvfp4-mtp`.
- `E:/PythonChimera/Saved/dyad/BRIEFING.md` — the eye knowledge contract.
- `E:/PythonChimera/Saved/gait/stride.json` — 331 samples x 28 joints, dt=1/60 s.
- Prior verdicts: `Saved/dyad/2026-09-04_*` and the 2026-09-06 09:xx burst reads.

### Missing / unavailable

- `docs/THE_PLATFORM_BOUNDARY.md`, `docs/FOUNDATION_P01_REPORT.md`,
  `docs/FOUNDATION_CONTEXT.md`, `docs/THE_MATERIAL_FOUNDATION.md` — absent at
  this checkout (per audit; not re-verified by me).
- `tools/platform_probe/` — absent entirely.
- The report references "recent Saved/dyad/2026-09-06_... runs"; the only
  `Saved/dyad/2026-09-06_*` dirs present are five 08:5x–10:00 `_burst` dirs that
  contain **no PNGs**, plus `dyad_log.jsonl`/`dyad_log.txt`.
  **No Saved/dyad capture images from the 12:2x visual session exist on disk.**
  That session's images live only under `.tmp/p02_visual_20260906_122824/`.---

## 2. Provenance

All 59 captures: 2560x1440, RGBA, **exactly 14748233 bytes each** (verified by
me with PIL). Disk creation times span 12:28 PM to 12:36 PM 2026-09-06.
**No embedded EXIF/timestamp metadata was found in the PNGs.** The only
temporal evidence is (a) the audit's own step log and (b) the on-screen
readouts visible inside the `/glass` captures.

| Group | Files | md5 (first 8) | Endpoint | Camera/scene |
|---|---|---|---|---|
| SHOW static /frame | frame_000..004, frame_verifyA/B, cam_pre_orbit | F4355D89 | /frame | fit_dyad bookmark, rear view |
| Orbit sweep | orbitOK_00..09 | 48E1A0E1, B01CF902, 1693966C, CF85D31B, B3BF5BEE, 411F9DD3, 48D1B510, 4CFCDECA, CADDD993, 67CD3E7A | /frame | cam_theta 0.5->6.15 rad |
| Orbit (failed key test) | orbit_00..07 | all 3C1E06EA | /frame | **no change — camera POST did not take** |
| Orbit pre/post | orbit_corr_pre / orbit_corr_post | 3C1E06EA / E9F5A0F3 | /frame | pre = same as failed set; post = distinct |
| Joint baseline | joint_pose_base, orbit_00.., cam_post_orbit, showplay_00..05 | 3C1E06EA | /frame | rest pose, both legs straight |
| Joint posed | joint_pose_kneeL_100 | 0464E3EA | /frame | knee_L theta=100, left knee bent |
| /glass studio | glass_000..004 | 88D95F05, 2F686C45, EB1E015C, C19B013A, F766432F | /glass | full composited window |
| showfix /frame | showfix_frame_00..04 | all 48E1A0E1 | /frame | static |
| showfix /glass | showfix_glass_00..04 | 0772563C, 5FE75B41, 1771A159, 9C8EAE1C, 83EDD2DF | /glass | changing HUD/clocks only |
| Baseline / final | baseline_view, final_baseline | B8672C12 | /frame | same image, two names |

**UNKNOWN (marked absent, not inferred):** exact wall-clock of each individual
POST; the camera `cam_phi`/`cam_radius` numeric values actually applied (the
audit records the *requested* values, not the confirmed ones); the engine PID
at each capture; which physical key/event produced each step.

**File creation time does NOT establish simulation time.** The 12:28–12:36
disk timestamps are ~10-20 min after the 12:22 report start and overlap the
report's own 12:2x session; the only reliable simulation-time evidence is the
in-image readouts (e.g. `show t=1430.65s`, `t = 86.655 s`, `t1429.21`).

**Key provenance finding:** `orbit_00..07` (all md5 3C1E06EA, identical to the
joint baseline) prove a camera POST that **did not move the camera**. Two
separate orbit attempts were made; only the second (`orbitOK_*`) produced
distinct frames.---

## 3. Independent visual pass

I inspected 10 images before reading any prior model verdict: baseline_view,
orbitOK_00, orbitOK_05, orbitOK_09, orbitOK_03, joint_pose_base,
joint_pose_kneeL_100, glass_001, showfix_glass_00, showfix_glass_04.
All are 2560x1440. Coordinates below are image-space (x from left, y from top).

### 3.1 Baseline creature — baseline_view.png (md5 B8672C12)

OBSERVATION: A tan/clay humanoid, seen from behind, centered horizontally
(x~530-810 for the body). Head is cropped by the top edge (only neck/jaw
visible at y~0-30). Two arms hang at the sides; left arm (screen-left,
x~530-600) and right arm (screen-right, x~730-810) both end in long splayed
fingers. Two thin straight legs descend to flat feet at y~350-380. A tube-like
tail emerges from the lower back and curves to screen-right (anatomical left),
tip at x~790, y~175. Below the feet is a dark reflection blob with finger-like
mirrored shapes and a thin vertical spike descending from x~675, y~390 to
y~550. Background: solid black band across the top y~0-60, then a flat
dark-gray floor plane filling the rest. No UI, no text, no grid lines.

INTERPRETATION: Rear view of a standing humanoid in a neutral A-pose. The
dark shape below is consistent with a glossy-floor reflection plus a contact
shadow. The vertical spike is an axis/gizmo line or a tail reflection artifact.

UNCERTAINTY: Whether the black top band is sky/backdrop or a rendering void
cannot be determined from one frame. The reflection's meaning (shadow vs.
mirror vs. artifact) is ambiguous — it does not track the feet crisply.
Whether the creature is actually standing *on* the floor plane or hovering is
not determinable from perspective alone; the feet and the reflection blob
overlap in projection.

### 3.2 Camera-orbit sequence — orbitOK_00 / _03 / _05 / _09

OBSERVATION (orbitOK_00, md5 48E1A0E1): rear view, tail sweeps to
screen-right (anatomical left), tip up at x~790 y~175. Feet at y~350-375.
OBSERVATION (orbitOK_05, md5 411F9DD3): still a rear view but the tail now
sweeps to screen-left (anatomical right), tip down at x~590-640 y~150-230.
The feet read as more splayed, toes visible at y~370-400. The torso shows a
slight front-ward lean. OBSERVATION (orbitOK_03, md5 CF85D31B): the figure
reads as a three-quarter rear/side — the right arm (screen-right) is clearly
separated from the body and the tail crosses behind the torso. OBSERVATION
(orbitOK_09, md5 67CD3E7A): near-symmetric rear view again, tail tip nearly
retracted toward the cleft, both arms hanging similarly.

INTERPRETATION: The 10-frame orbitOK set is a genuine camera rotation around
a **static mesh**. The tail's apparent side-to-side flip is parallax from the
camera moving, not the tail moving. The mesh silhouette, joint angles, and
foot positions are consistent with one unchanging pose across all 10 frames.

UNCERTAINTY: The exact azimuth between frames is not recoverable from pixels
alone — the report's requested cam_theta values are not printed on the frames.
No frame shows the face or front of the creature, so "rear view" is the only
defensible orientation statement. Whether the camera also changed radius or
elevation cannot be judged; the figure size stays roughly constant, which
suggests radius was held, but small elevation changes are indistinguishable
from radius changes in a single-axis sweep.### 3.3 Joint baseline and posed image — joint_pose_base / kneeL_100

OBSERVATION (joint_pose_base, md5 3C1E06EA): a closer crop — the figure fills
more of the frame. Both legs are straight, parallel, vertical. Left leg at
screen x~600-660, right leg at x~690-760. Knees show no angular break. Feet
splay outward symmetrically at y~340-370. Arms hang at the frame edges
(x~410-490 left, x~830-930 right). Same dark reflection + vertical spike
below as the baseline. No UI.

OBSERVATION (joint_pose_kneeL_100, md5 0464E3EA): the screen-left leg
(anatomical left) is now clearly bent — the thigh descends to y~250, then the
knee juts forward (toward the camera) and the shin drops nearly vertically to
y~500, ending in a foot at y~350-380 that reads as foreshortened. The bend is
a hard, faceted kink, not a rounded bulge. A dark shadow column extends below
the bent knee to y~510. The screen-right leg (anatomical right) remains
straight, x~690-760, unchanged from the base. The pose is strongly asymmetric.

INTERPRETATION: A direct joint POST (knee_L theta=100) produced a real, large
mesh deformation — the left knee is bent forward roughly 30-45 degrees. This
is the strongest evidence in the whole set that the rig can move the mesh.

UNCERTAINTY: The exact knee angle cannot be measured from pixels — I will not
infer degrees from a single perspective view. Whether the bend is anatomically
correct (knee protruding anteriorly while viewed from behind) is plausible but
the rear view makes anterior/posterior ambiguous; the shin could equally be
rotating away. The bent knee's shadow column is unusually long and dark and
does not obviously connect to a foot contact patch, so foot placement under the
bent leg is uncertain.### 3.4 /glass studio view — glass_001 (md5 2F686C45)

OBSERVATION: The full composited 2560x1440 window. Top chrome bar reads
"THE ENGINE STUDIO" with help text "[F1] hide [click bar] collapse [drag edge]
resize [ ] console". Below it a full-width stage-tab strip: B0 ACQUIRE,
B1 REPAIR, B2 REGISTER, B3 SKELETON, B4 FACTORY, B5 ANATOMY REF..,
B6 DYNAMICS REF.., B7 ARTICULATE (highlighted), B8 BEHAVE, B9 APPEAR,
B10 DYAD & SHIP. A sub-header reads "EARLIEST NON-GREEN GATE: B7 articulate
-- the next stage [next]" on the left and "docs/THE_BODY_PIPELINE.md
2026-08-30" on the right.

Left dock: "DOCS - the browser (E1)" with a list (THE_BODY_PIPELINE selected,
THE_ARTISTS_SOLID, THE_MASTER_LIST, THE_TRIANGLE_GUIDE, THE_OPERATING_MANUAL,
DYAD LOG, ENGINE LOG, SESSIONS) and a body of document text including
"R(N_B, N_mjc) = 0.955/0.953" and "**Verdict: our G3 contact solve is NOT
wrong**".

Center viewport: the tan creature from a rear three-quarter angle on a
perspective grid floor. A blue skeleton overlay traces every joint with cyan
labels (brow_L +0, lid_L +0, ear_R +0, jaw +0, mouth_R +0, mouth_L +0,
neck +0, spine_upper +0, shoulder_R +0, shoulder_L +0, elbow_R +0,
spine_mid +0, elbow_L +0, wrist_R +0, tail_base +0, tail_tip +0, wrist_L +0,
tail_mid +0, hip_R +0, spine_lower +0, hip_L +0, knee_R +0, knee_L +0,
ankle_R +0, ankle_L +0). Top overlay strip reads "SHOW ear_R theta 0.00 deg
ROM [-35.0 .. 40.0]" and "EYE last report 8.1 h ago", plus camera buttons
[1 alpha] [2 beta] [3 closeup] [4 monkey_full] [5 cam7] [6 cam8]
[7 fit_dyad] [8 operator_pre_tierA] [+ cam].

Right dock "STATUS (live)": FPS 103 | ft 7.05 ms | max 1287.76; mesh: see
viewport | splats: 0; hinge: off; joints_show: loaded; gait CPG: no pack |
steps 0; water clock: off | macro steps 0; volp-ARAP: no pack | mode volp;
frost decode: off | frames 0; SCENE - live systems (view_only); body 36424
tris, 18459 verts, r=10.0; overlay none; show t=1430.65s x1.00; joints 28
joints; volp no kernel; gait steps=0 omega=7.85; water clock steps_total=0;
inj=0/-1; water vis the field, drawn; frost no pack; strain no hinge; matter
54771 edges, k=0.20, 48 it; chrome the studio bar.

Bottom-center REEL (D3): "every /frame grab lands here [2/12]" with two thumbs
(t1429.21 ear_R +0.0d 12:28:34; t1425.75 ear_L +0.0d 12:28:31).
TIMELINE (D1): "the show clock is a parameter"; control row
[PAUSE] [-1f] [+1f] [1x] KEY  t = 86.655 s / 112.0 s (lap 12) | ear_R theta
= +0.00 deg | PLAYING; joint 22/28: ear_R; UNKEYED.

Bottom status bar: ARTICULATE (B7) | 103 fps 9.70 ms/frame |
next partial green/done | 08:12:07 | EYE: DEFECTS | NVIDIA GeForce RTX 4090
| 2560x1440.

INTERPRETATION: A complete, live three-column studio. Every readout the
BRIEFING scaffolding demands is present and legible. The creature pose in this
composited view matches the rear three-quarter view seen in the raw /frame
captures — consistent.

UNCERTAINTY: This is one instant. The many "live" counters (FPS, ft, show t,
timeline t, wall clock) strongly imply the window is updating, but a single
still cannot demonstrate motion. The gait/steps counters being 0 is consistent
with the report's "no gait pack" finding, but the *reason* (missing pack vs.
wired-but-zero) is not visually separable.---

## 4. Review of comparisons

I compared descriptions made from separate images, one image per read, rather
than diffing pixels directly (pixel diffing is reported separately below as
corroboration, not as the primary evidence).

### 4.1 Camera movement versus object deformation

The orbitOK set (10 distinct md5, figure size roughly constant, tail flipping
side-to-side between _00 and _05) is consistent with a camera rotating around a
static mesh. The silhouette, the joint angles, and the foot positions do not
change in a way that suggests the mesh itself is deforming. The tail's apparent
side-to-side flip is parallax from the camera moving, not the tail moving.

The joint_pose pair (base vs kneeL_100, md5 3C1E06EA -> 0464E3EA) is the
opposite case: same camera, mesh genuinely deformed. The screen-left leg gains
a clear forward knee bend; everything else in the frame is unchanged.

Pixel corroboration (image-space, threshold 10/255):
- orbitOK_00 vs orbitOK_05: 125,889 changed px, bbox x 1004-1530, y 0-769.
- orbitOK_00 vs orbitOK_09: 123,315 changed px, bbox x 0-2559, y 0-1017.
- joint_pose_base vs kneeL_100: 69,768 changed px, bbox x 1079-1240, y 291-972.
- frame_000 vs frame_004: **0 changed px** (byte-identical).

The changed-pixel bbox for the joint pair (x 1079-1240, 161 px wide) is
narrow and localized to one leg, exactly what a single-joint edit should look
like. The orbit bboxes are wide and tall, consistent with a whole-frame
re-projection.

### 4.2 Silhouette and joint changes

Between orbitOK_00 and _05 the silhouette does not change shape — the arms,
torso, and legs keep the same outline; only the tail's apparent side and the
foot toe visibility change. This is camera motion, not pose change.

Between joint_pose_base and kneeL_100 the silhouette changes decisively: the
left leg gains a protruding knee and the foot reads as foreshortened. This is a
real joint change.

### 4.3 HUD changes versus changes in the 3D scene

showfix_frame_00..04 are byte-identical (md5 48E1A0E1, 0 changed px) while the
corresponding showfix_glass_00..04 are all distinct (0772563C -> 83EDD2DF,
29,530 changed px between _00 and _04, bbox x 410-2537, y 128-1434). The
glass diffs are confined to the HUD readouts — the STATUS dock shows FPS
dropping 103 -> 74 -> 34 -> 7 and frame-time rising 7.05 -> 10.77 -> 26.77 ->
143.00 ms, the SHOW label cycles ear_R/lid_R/mouth_R/brow_L, the timeline t
advances 86.655 -> 93.742 -> 108.765 s, and the REEL gains thumbs. The 3D
creature in the viewport does not move between showfix_glass_00 and _04.

**This cleanly separates HUD from scene.** The HUD is live and the 3D scene is
not — which is exactly the audit's finding #4 and is confirmed independently.

### 4.4 Do the captures support a motion claim or only two different poses?

The captures support **two different poses** (rest vs knee_L=100) and **one
static pose viewed from 10 different cameras** (the orbit). They do **not**
support any claim about motion, velocity, smoothness, or continuity. There is
no capture in the set that shows the same camera at two different simulation
times with a deforming mesh — the only time-varying element is the HUD.

The one exception is the 2026-09-06 09:xx burst reads (4-image walls, dyad_log
lines 83-84), which describe a *different* session's frames with real gait
joint values. Those are not part of this 12:2x capture set and I treat them as
prior-session evidence, not as evidence about the P02 visual session.---

## 5. Comparison with prior verdicts

I recorded all observations in §3-4 before reading the existing eye reports.
The prior verdicts are the 7 dyad reads at dyad_log lines 85-91 (the 12:2x
session) plus the earlier 2026-09-03/04 reports.

### Agreements

1. **Rear view, no UI in the raw /frame captures.** Prior reads (lines 86-88)
   and my own agree: the viewport is a full-bleed 3D view with no chrome, and
   the creature is seen from behind.
2. **Tail side flips between orbit frames.** Prior reads (lines 87, 89) say the
   tail sweeps viewer-right in orbitOK_00 and viewer-left in orbitOK_05. My
   independent read agrees exactly, and I add that this is parallax from a
   camera rotation, not tail motion.
3. **joint_pose_base is symmetric with both legs straight.** Prior read (line
   90) and mine agree.
4. **joint_pose_kneeL_100 shows a moderate forward knee bend on the left leg
   with the right leg straight.** Prior read (line 91) and mine agree on the
   asymmetry and the rough magnitude. We both stop short of a degree claim.
5. **glass_001 is a live, full studio.** Prior read (line 92) transcribes the
   same panels, readouts, and clocks I read. We agree the window reads as live
   because of the counters, not because of any demonstrated motion.
6. **SHOW produces no mesh deformation.** Prior verdict (audit §7.3/8.2) and my
   pixel evidence (frame_000..004 byte-identical, showfix_frame_00..04 byte-
   identical) agree: the show clock advances but /frame does not change.

### Disagreements

1. **"The automated SHOW currently produces no mesh deformation" — I sharpen
   this to a stronger statement.** The audit attributes the stasis to "no gait
   pack, joints_show present but theta stays 0". My read of the in-image data
   adds: the gait stride data that *does* exist on disk
   (`Saved/gait/stride.json`) has **26 of 28 joints identically zero across all
   331 samples** — only hip_L/R, knee_L/R, ankle_L/R move, and ankle_L/R are
   constant at -0.053. So the stasis is not merely "no pack loaded at audit
   time"; the stored stride itself drives only 4 joints. The prior verdict's
   framing ("no gait pack") is a runtime-state explanation; the data-level
   explanation is that the stride file is mostly zeros. I consider the data
   explanation stronger and independent of runtime state.
2. **On what the orbit proves.** The audit's §7.3 verdict #1 says "PASS —
   renderer is camera-responsive" based on "10 distinct /frame outputs for the
   10-step cam_theta orbit". I note the audit's own table also lists an
   `orbit_00..07` set that is **not** distinct (all md5 3C1E06EA). The camera-
   responsiveness claim rests on the `orbitOK_*` set only, and the audit does
   not disclose in §7.3 that a first orbit attempt produced no change at all.
   My provenance table (§2) makes both attempts visible.
3. **I do not call the glass a "live composited window" in the same sense.**
   The prior read concludes "It reads as a live, updating UI" from the presence
   of live-type counters. I agree it *reads* live but I will not call it
   demonstrated-live: within this capture set the only thing that demonstrably
   changes over time is the HUD, and the 3D scene is provably static. The prior
   verdict's phrasing slightly overstates what the stills establish.

### Claims the images cannot establish

- Any joint angle in degrees (no calibration between pixels and world).
- That the creature is standing on the floor vs. hovering (the feet and the
  reflection overlap in projection; no depth cue separates them).
- That the tail is a rigid limb vs. a soft appendage (one pose, no motion).
- Smoothness, velocity, acceleration, or continuity of any kind (no
  same-camera time series with a deforming mesh).
- Whether the engine is "actually animating" at capture time (only the HUD
  animates in this set).
- That the knee bend is anatomically anterior vs. posterior (rear view).
- The exact camera radius, phi, or azimuth at any frame (not printed on frames).---

## 6. Audit of visual coverage

### 6.1 What is missing for each criterion

**Foot contact and sliding.** No capture shows a foot from a low or level
angle, and none shows two frames of the same foot at different times. The
reflection/spike under the feet in every /frame is a dark blob that does not
resolve into a per-sole contact patch. The BRIEFING demands a "dark flattened
copy on the grid floor under it" that "must track the pose"; in this set it
does not visibly track anything because the pose never changes.

**Joint continuity.** Only one joint (knee_L) is ever moved, and only to one
value. There is no sweep of a joint through its range, no intermediate
frames, and no second joint moved in the same session. Continuity of the mesh
through an intermediate angle is completely untested.

**Self-intersection.** No pose in the set puts two limbs near each other. The
bent-knee frame has the shin dropping nearly vertically and its shadow column
is long and dark — worth checking whether the bent foot intersects the
reflection plane or the spike, but the resolution and the rear view make this
inconclusive rather than clean.

**Surface deformation.** The knee bend reads as a "hard, faceted kink" (a
previous eye's phrase, which I independently confirm) rather than a bulging/
compressing skin fold. No strain-tint overlay is visible (STATUS reads
"strain no hinge"), so the compression/stretch gradient the BRIEFING expects
is both absent from the data and absent from the pixels.

**Camera/control responsiveness.** Well covered — the orbitOK set proves the
renderer re-projects on camera change, and the joint POST proves the rig
responds. The one negative result (orbit_00..07, no change) is itself evidence
that a camera POST can silently fail; that is useful, not wasted.

### 6.2 Smallest future capture sequence to resolve each uncertainty

1. **Foot contact:** 4 captures at a low camera phi (near floor level), same
   camera, rest pose then knee_L=100 then a shallow ankle flex. One frame per
   pose is enough to see whether the sole sits on the plane and whether the
   contact shadow tracks it.
2. **Joint continuity:** a 6-frame sweep of knee_L at 0 / 20 / 40 / 60 / 80 /
   100 deg, same camera, /frame each. Intermediates are the whole point; the
   current set has the two endpoints only.
3. **Self-intersection:** the bent-knee frame from a 3/4 side view (not rear),
   plus the same pose with the opposite knee also bent. The rear view cannot
   separate the legs in depth.
4. **Surface deformation:** the knee sweep above, shot close enough that the
   fold fills ~200 px, with strain tint turned on. Without tint there is no
   visible gradient to judge.
5. **Motion (the big gap):** a same-camera /frame series at ~8-12 equally
   spaced simulation times across one gait cycle, plus the matching /glass for
   HUD correlation. This is the only capture that could establish that the mesh
   actually moves over time. Nothing in the current set can.
6. **Camera POST failure:** re-issue the exact orbit_00..07 request and capture
   the HTTP response body, not just the frame. The silent fallback is a
   contract issue, not a rendering issue, and no image can diagnose it.---

## 7. Reusable visual evidence rubric

All measurements below are **image-space** unless labelled otherwise. No
world-space calibration exists in this project, so no pixel measurement is
reported as a physical distance.

### R1 — Renderer re-projects on camera change

- **STATEMENT:** Changing the camera produces a genuinely different /frame.
- **PREDICTION:** N distinct camera POSTs yield N distinct /frame md5s; the
  silhouette of a static mesh shifts, and parallax-dependent features (e.g. a
  tail on one side of the body) flip side between viewpoints.
- **FALSIFIER:** Two camera POSTs with different parameters produce identical
  /frame bytes (this happened: orbit_00..07, all md5 3C1E06EA).
- **LIMIT:** A distinct frame proves the camera was used; it does not prove the
  camera parameter the operator intended was the one applied. Silent fallback
  to defaults is indistinguishable from a real move at the pixel level.

### R2 — Joint POST deforms the mesh

- **STATEMENT:** A /joints POST changes the mesh geometry.
- **PREDICTION:** The silhouette changes locally around the named joint; the
  changed-pixel bbox is narrow and adjacent to that joint; the rest of the
  frame is unchanged.
- **FALSIFIER:** The frame is byte-identical to the pre-POST frame, or the
  changed pixels are scattered across the whole image (which would mean the
  camera moved, not the joint).
- **LIMIT:** A changed mesh proves the joint value was applied; it says nothing
  about whether the resulting angle is anatomically correct, nor the magnitude
  in degrees. Perspective from a single viewpoint cannot separate rotation
  axes.

### R3 — Show clock advances without mesh motion

- **STATEMENT:** The automated show can run without deforming the creature.
- **PREDICTION:** /frame captures taken at different show times are
  byte-identical while the /glass captures at the same times differ (in HUD
  readouts only).
- **FALSIFIER:** /frame bytes differ between two show times.
- **LIMIT:** Byte-identical /frame proves the *rendered 3D scene* did not change;
  it does not prove the show clock is advancing, nor that no gait pack is
  loaded. Both must be read from the /glass STATUS dock.

### R4 — HUD is separable from the 3D scene

- **STATEMENT:** UI overlays live above the 3D viewport and can change
  independently of it.
- **PREDICTION:** /glass captures differ in text/numbers while the embedded 3D
  viewport region is unchanged.
- **FALSIFIER:** /glass captures differ *and* the 3D region differs — then the
  change is in the scene, not the HUD.
- **LIMIT:** This test requires the /glass endpoint. /frame alone can never
  establish HUD behaviour because /frame contains no HUD.

### R5 — Foot contact reads as planted

- **STATEMENT:** A foot is on the floor, not hovering or clipping.
- **PREDICTION:** At a low camera angle the sole is coincident with the floor
  plane; a dark flattened contact patch sits directly under the sole and moves
  with it between poses; no part of the foot is below the plane.
- **FALSIFIER:** The foot floats above the plane with no contact patch, or the
  foot/leg passes through the plane while the contact shadow stays put.
- **LIMIT:** A rear or high-angle view cannot establish contact — the feet and
  their reflection overlap in projection. Contact is only legible near floor
  level. A single still also cannot show *sliding*, which needs two frames of
  the same foot.---

## 8. Handoff

### 8.1 Evidence files reviewed

`P02_PLATFORM_AUDIT.md`; all 59 PNGs in `.tmp/p02_visual_20260906_122824/`;
`Saved/dyad/dyad_log.jsonl` + `dyad_log.txt`; `Saved/dyad/BRIEFING.md`;
`Saved/gait/stride.json`; prior 2026-09-03/04 and 09-06 09:xx verdicts.

### 8.2 Independent observations (summary)

- The 12:2x capture set contains **two genuinely different poses** (rest and
  knee_L=100) and **one static pose seen from 10 different cameras**. It
  contains no evidence of mesh motion over time.
- Camera responsiveness and joint-rig responsiveness are both demonstrated,
  and one camera POST is demonstrated to have **silently failed**
  (`orbit_00..07`, all md5 3C1E06EA).
- The HUD demonstrably changes while the 3D scene demonstrably does not
  (`showfix_glass_*` vs `showfix_frame_*`).
- The stored gait data (`Saved/gait/stride.json`) is 26-of-28 joints zero
  across all 331 samples; only hips, knees, and ankles move, and the ankles are
  constant. The SHOW stasis is therefore a data property, not only a runtime
  "no pack" state.
- Every /frame in the set is a rear view. No front, side, or low-angle view
  exists. No foot contact, joint sweep, self-intersection, or surface-deformation
  evidence exists.

### 8.3 Unsupported claims

- Any motion, velocity, smoothness, or continuity claim.
- Any joint angle in degrees.
- That the creature is planted rather than hovering.
- That the knee bend is anterior or posterior.
- That the engine is "animating" at capture time (only the HUD animates here).
- That the tail is a limb vs. an appendage.

### 8.4 Proposed capture rubric

See §6.2 for the minimal sequences and §7 for the five reusable criteria
(camera response, joint POST, show-clock stasis, HUD/scene separation, foot
contact), each with statement, prediction, falsifier, and limit.

### 8.5 Questions requiring Alan's judgment

1. Is the `orbit_00..07` silent camera-POST failure a contract bug to fix, or
   an acceptable fallback? It is the only capture in the set that shows a
   *negative* result, and it is not disclosed in the audit's verdicts.
2. Is a mostly-zero stride file (26/28 joints) acceptable as a gait source, or
   is that itself the defect to fix before any "gait works" claim is made?
3. The knee bend reads as a hard faceted kink with no strain tint and no skin
   bulge. Is that a rendering-quality defect to fix, or within tolerance for
   this stage (B7 ARTICULATE)?
4. The reflection/spike under the feet never resolves into a contact patch and
   never tracks the pose. Should foot contact be judged from pixels at all at
   this stage, or deferred to a numerical gate?
5. Is a rear-only camera acceptable for the next review, or is a side/front
   view mandatory? Every criterion in §6.1 is untestable from the rear.
6. Should the eye's "reads as live" judgment (based on live-type counters) be
   recorded as a separate confidence tier from "demonstrated live" (based on a
   same-camera time series)? My read is that this set only ever produces the
   former.

---

## Confirmation

- Files written: `E:/PythonChimera/.tmp/v02_20260906_190511/README.md` and
  `E:/PythonChimera/.tmp/v02_20260906_190511/V02_REPORT.md`.
- Original evidence under `.tmp/p02_visual_20260906_122824/`,
  `.tmp/p02_20260906_122252/`, and `Saved/dyad/` is **unchanged** — I read only.
- No engine, camera, joint, or playback control was exercised. No code,
  dependency, branch, commit, or push. Nothing was written under
  `ChimeraEngine/engine/build/`.
- Human acceptance remains Alan's. Nothing in this report claims his approval.---

## Appendix A — Corrections to the audit's own counts

- **A1.** The audit §11 says "59 evidence PNGs". The directory contains **56**
  PNGs plus 2 Python scripts (`_dyad_baseline.py`, `_dyad_reads.py`) = 58 files.
  Either the count or the directory is wrong; I report the measured 56.
- **A2.** The audit §7.1 table presents the `cam_theta` orbit as a single working
  sweep. The directory contains **two** orbit attempts: `orbit_00..07` (all
  md5 3C1E06EA — the camera POST produced no change) and `orbitOK_00..09` (10
  distinct md5s — the working sweep). The verdicts in §7.3 cite only the
  working set and do not disclose the failed attempt.
- **A3.** The audit §8.1 read table lists `final_baseline` as "Tan/clay
  humanoid, rear/back, arms down, tail out, flat gray floor, **no UI**" and
  separately `frame_000` as "Same figure rear view, symmetric, **no UI**".
  `final_baseline.png` and `baseline_view.png` are the **same file** (both
  md5 B8672C12), so the two rows describe one image under two names.