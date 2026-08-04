# THE SECOND RECORDED SESSION — the physics is live and the picture does not show it

> Goal rung 9: *"re-record with everything above in… F1–F3 all PASS on video."* Recorded
> 2026-08-04, 121 frames across 10 beats, all beats landed. **The recording is the finding, and
> the finding is negative.**

## WHAT THE SESSION LOG PROVES — the world is real and reports itself

Straight from `session_log.txt`, unedited:

```
"touch": "E: pick up the stone (65.1 kg)"
"touch": "the stone -- 65.1 kg of basalt (Quaglio 2020), mu 0.84 = tan(40.03 deg repose)"
"touch": "the pile -- 400 grains of regolith (d50 0.35 mm, 0.06 mg each),
          repose cone 0.84 m tall -- footprint 1.08 m"
```

Every number traces. The stone's mass is basalt density on its measured volume; its friction is
`tan(40.03°)` — the repose angle the granular membrane *emerged*, not a coefficient anyone typed.
The pile's footprint reads **1.08 m**, the same number the HUD proved in the rung-3 session. The
GRAB fires, the load is priced, the drop deforms the pile. **F1 holds: everything on the line
traces to a membrane.**

## WHAT THE FRAMES SHOW — none of it

`04_picked.jpg` (the stone in hand) and `07_pile.jpg` (standing at the pile) both show: **a pale
mannequin on a featureless dark-green plane under a dark blue sky.** No stone reading as rock. No
pile. No vegetation. The carried object is a small grey slab with no material identity; at the
pile beat there is nothing on the ground at all.

**This is F2, stated exactly.** The touch line carries the world; the picture does not. And it is
a sharper statement than the rung-3 blind read could make, because that read had a recorder fault
mixed into it — this recorder is the fixed one, closed-loop, all beats landed. **The remaining
gap is purely render.**

## AND IT DOES NOT REPRODUCE TWO CLAIMS MADE THIS WEEK

Recorded as a disagreement, not an accusation — both were validated in their own instruments and
neither appears in the product:

| claim | its own instrument | this recording |
|---|---|---|
| *M5: stone reads as rock (denser splat sphere)* | PASS | carried object is a grey slab; no rock |
| *M6 membrane 4: 13 blades, the tuft reads as stalks* | PASS | **no vegetation visible in any hero frame** |

A membrane can pass its own falsifier and still not reach the screen — the legibility instruments
measure the object in isolation; the session measures it **at the camera the player uses**, at
that exposure, over that ground. Those are different questions and only the second one is the
game. **Which of the two is wrong is not settled here**; what is settled is that they disagree,
and the disagreement is the next rung's work.

## THE INSTRUMENT DEFECT THIS COST, paid in evidence

`slice_record.py` named its output `slice_session_{YYYYMMDD}` — **date only**. Re-recording on the
same day overwrote the previous session frame for frame, and the path is gitignored, so **the
rung-3/4 session the earlier blind read was taken from is gone.** Not recoverable. My run did it.

Fixed: the name now carries seconds, and an existing directory is **refused**, never entered. A
recording is evidence, and an instrument that overwrites evidence without saying so is the same
species as a witness keeping a stale copy — the failure this project has a rule for.

## MEMBRANE: ABSENT OR ILLEGIBLE — the fork that decides the fix (2026-08-04, Kimi)

The disagreement above names two suspect classes and settles neither. This membrane settles it.

**STATEMENT.** The touchables are IN the session scene's uploaded buffer — the third-person path
concatenates `touchables_buffer` every frame (`live_viewer.py:160-164`), and the same code drew a
legible stone in the isolated probe. The hero-frame absence is therefore **camera-object geometry
and splat presentation at that geometry**, not absence. My own M5/M6 "PASS" frames are on record
as weak evidence: re-read with fresh eyes, `stone_after.jpg` is a faint smudge and `tuft_cov1.jpg`
a faint streak — the isolated probes were judged generously, at the wrong camera, against no
occluding body.

**PREDICTION.** `tools/session_legibility.py` renders the session scene (ground + body +
touchables, the same buffers, the same exposure, the same sun) from two cameras per object:
a close diagnostic camera (2 m, aimed) will show stone, pile, and tuft clearly, and the session's
own beat camera (the `live_viewer` third-person formula, walker at the beat position, body in
frame) will reproduce the hero-frame absence — including testing whether the carried stone at
waist height is occluded by the head from the behind-above camera.

**FALSIFIER.** If a close-up ALSO shows nothing, the objects are absent from the buffer — a
spawn/upload defect, a different class, and this membrane is wrong. If the session-camera renders
show the objects clearly, the defect is in the recorder's capture path, not the scene — also a
different class. Either fires this membrane and reroutes the fix.

### VERDICT (2026-08-04, measured by `tools/session_legibility.py`, seven frames read by eye)

**Neither falsifier clause fires. The membrane's STATEMENT holds, with three measured parts:**

1. **ABSENT is refuted.** All three classes are in the uploaded buffer and render at the session
   camera: `stone_carried.jpg` (the stone at the waist, clearly an object), `pile_session.jpg`
   (grains around the feet), `tuft_session.jpg` (blades at the legs). The 22:41 session's own
   contact sheets corroborate independently: `sheet_beat03` shows the carried stone in every tile;
   `sheet_beat06` shows pile grains and the dropped stone.

2. **The dominant defect is BEAT GEOMETRY.** The beats `goto()` the object's own position, so the
   walker stands ON its subject; the chest-aimed camera 3.2 m behind and above then occludes the
   object with the walker's own legs (`stone_session.jpg`: the stone is inside the legs;
   `tuft_session.jpg`: same). The isolated probes looked AT the object; the session stood ON it.
   That is the whole disagreement between the two instruments, and it reconciles both.

3. **The secondary defect is TUFT CONTRAST.** Even at 2 m the blades measured DARKER than the
   sunlit slope behind them: they shade with an up-normal (`lam = sun_z`, the minimum) while the
   ground's slope normals tilt toward the sun. Fixed by a second step on the established
   legibility dial (`_TUFT_ALB` → (0.28, 0.45, 0.18), same step size as rung 3's; before/after
   frames `tuft_close_before.jpg` / `tuft_close.jpg`): blades now read as bright-green strokes.

**The instrument defect that contaminated both reads:** the hero frames `01..09_*.jpg` in
`slice_session_20260803/` are from **16:16** — before the n=160 stone, ball-chain tuft, and
0.06 clod fixes (18:12–18:27) — while `session_log.json` and `sheet_beat*.jpg` are from the
**22:41** re-record. Both the "grey slab / no vegetation" read above and my own earlier
corroboration of it judged the stale heroes against the new log. The seconds-named directories
landed at 22:53, after that session — so its heroes overwrote the older run's in place.

**The fixes, per the fork:** standoff heroes in the recorder (beats 01/05/07 now take the picture
from 2.5–3 m out, facing the object; the physics beats still close in — `tools/slice_record.py`
`standoff()`), the tuft dial step, and a full re-record as the evidence (this session's directory,
`slice_session_20260804_*`).

### RE-RECORD VERDICT (`slice_session_20260804_040936`, all beats landed, sheets read by eye)

Every object beat's subject is now on camera. The master sheet: the stone reads ahead of the
walker on approach (hero[1]) and carried at the waist (hero[2], hero[3]); the dropped stone reads
at the feet (hero[4]) and on the ground in later beats (hero[6], hero[7]); the pile's repose cone
reads whole from the standoff (hero[5]) and in the background of the entire tuft beat; the tuft
reads at its standoff (hero[7]).

**Residual, measured and named:** the tuft is the weakest object — a 0.4 m disk of 0.35 m blades
is a dot at the 4–8 m approach distances (beat07 sheet: present, not yet grass). No albedo fixes
angular size; the next legibility step on it is the blade display-width dial (0.02 m, already
12.5× measured) or more blades — THE HUMAN's render row, the operator's to move. The stone's
close-up silhouette reads spiky (`stone_close.jpg`: 160 normal-discs); at session range it reads
as a rock, so the normals stay. Both are recorded here so the next read judges them knowingly.

## MEMBRANE: THE STAND, ON CAMERA (2026-08-04, Kimi) — the bridge named below, built

**STATEMENT.** The musculoskeletal stand can be witnessed as a VIDEO record without touching the
Walker session: `f3_stand.py`'s own rollout already drives the proven `stand_theta` through the
real parser and renders frames via `mujoco.Renderer`; a denser frame grab over the same two
phases, saved as a numbered sequence (the shape the blind read's WATCH prompt consumes), IS the
stand on camera. The video and the number come from the same rollout, so they cannot disagree
silently.

**PREDICTION.** `tools/stand_on_camera.py` renders the two-phase rollout (5 s STAND on, then
released) to ~28 frames at 640×480. The sequence shows the musculoskeletal body upright and
un-arched through the hold, then visibly slumping after the button releases — the same verdict
`f3_stand.py`'s numbers give (phase 1 PASS, phase 2 slump), in pixels.

**FALSIFIER.** The frames show the body falling or hunched during phase 1 — then the on-camera
claim is false no matter what the numbers say — or they render empty/garbled, meaning the
renderer does not carry this body and the bridge claim is wrong.

**PREDICTION HOLDS, falsifier does not fire** (2026-08-04): `tools/stand_on_camera.py` rendered 30
frames over the same two-phase rollout `f3_stand.py` judges — same proven `stand_theta`, same real
parser, same construction — at 640×480 with the pelvis percentage printed on every frame. Read by
eye: the body stands visibly upright through the hold (phase 1 pelvis MIN 102.9% of target), then
folds forward after the button releases (slump to the bar in 2.30 s; the last frames show the
fold at 61% and falling). The number and the video come from one rollout; they agree. The frames
are the blind read's WATCH shape — numbered, in order — at
`ChimeraEngine/output/ports/stand_on_camera/`.

## MEMBRANE: THE STAND, IN THE PLACE (2026-08-04, Kimi) — the two rigs composed

**STATEMENT.** The musculoskeletal body can stand *inside the carved ground* — the same splat
scene the session records — without new physics: the stand rollout runs on its own flat plane
exactly as `f3_stand.py` judges it, and the body's MuJoCo geoms are emitted as splats (mesh
vertices and capsule chains, the tuft's zero-normal tube trick for shape, `touchables._shade`'s
one sun for light) into the walker's ground+touchables buffer. The physics is unchanged; only
the render composes the two rigs, and the doc says so on the tin.

**PREDICTION.** `tools/stand_in_world.py` renders the two-phase rollout composited onto the
carved ground near spawn, from the session's third-person camera: the frames show the
musculoskeletal body standing on the terrain with the stone, tuft, and pile in the scene,
holding upright through phase 1, then folding after release — readable as *a figure standing in
the place*, not in the vendor's white room.

**FALSIFIER.** The composited body renders garbled or unrecognizable (geom→splat does not carry
this body), or the frames show it down during phase 1 (the composition broke something — it
should be impossible: rendering is read-only on the sim). Either fires and the bridge claim is
wrong.

**PREDICTION HOLDS, falsifier does not fire** (2026-08-04): `tools/stand_in_world.py` rendered 30
frames of the two-phase rollout composited onto the carved ground at (1.5, 3.0), from the
session's third-person camera. Read by eye: the musculoskeletal figure stands on the terrain
with the stone right of frame and the pile cone behind (frame_10, t=2.50 s, pelvis 104%),
holding its measured −16° stand pitch, then folds forward after the release (frame_29, t=7.25 s,
61% and falling — the slump, unmistakable). Phase 1 pelvis MIN 102.9%, phase 2 slump in 2.30 s —
identical to `stand_on_camera.py`'s numbers, as they must be: same rollout, two renderers.
Frames at `ChimeraEngine/output/ports/stand_in_world/`. One honest note: the body renders in its
geom colours (pale), not MuJoCo red — the red muscles in the vendor renderer are a *tendon
rendering* feature, not geom albedo, so the splat body's pallor is the model's own claim, not a
defect introduced here.

## STATUS

- **F1 — PASS.** Every published number on the touch line traces to its membrane.
- **F2 — STILL FIRED**, and now with the cleanest evidence yet: a closed-loop recorder, all beats
  landed, physics reporting correctly, and a frame a blind reader would describe as an empty field.
- **F3 — PASS**, by `tools/f3_stand.py` (exit 0), **and now on camera**: the musculoskeletal stand
  is recorded in `tools/stand_on_camera.py`'s 30-frame two-phase video (upright hold, then the
  release slump) — the bridge named above, built 2026-08-04. What is still not on tape is the
  stand *inside the Walker session* (the mover and the musculoskeletal body remain two rigs);
  that composition is the next bridge, named here rather than glossed.
