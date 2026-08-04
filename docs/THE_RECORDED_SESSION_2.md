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

## MEMBRANE: THE BLIND READ, AS A DRIVER (2026-08-04, Kimi) — one command when the eye is live

**STATEMENT.** The blind read of this session is a driver, not a person. Every piece of evidence
the eye must judge is already on disk in the eye's two native shapes — SEE (the master sheet and
the ten beat sheets) and WATCH (the numbered stand_on_camera and stand_in_world frame
sequences) — and `ChimeraEngine/human_messenger.py` already defines the reading protocol: blind
prompts that forbid numbers, plus `align()` as the cross-reference against the recorder's ground
truth. One command can therefore deliver the whole session to the eye blind and record every
reading verbatim; the signature stays with THE HUMAN.

**PREDICTION.** `python tools/blind_read.py`, run with the senses server live, writes
`ChimeraEngine/output/blind_read/<timestamp>/readings.json` + `verdict.md`: one entry per sheet
(SEE) and per frame sequence (WATCH), each with the reading verbatim, the expected term from the
recorder's ground truth, and the align score — and the exact prompts sent, logged, so the blind
condition is auditable.

**FALSIFIER.** Two clauses, the first testable before the server exists: (1) the eye is dark and
the driver exits LOUD without writing a verdict — a driver that silently passes with no eye is
exactly the instrument defect this project keeps paying for; (2) any outgoing prompt leaks the
answer — a number, a beat name, or the words stone/rock/grass/pile — which the prompt log makes
checkable.

**CLAUSE 1 FIRED AND HELD, write path verified** (2026-08-04): with the eye dark the driver
exits 2, loud, and writes nothing. The full loop (13 items: master + 10 beat sheets SEE,
both stand sequences WATCH, align per item, `readings.json` + `verdict.md` written) was then
exercised end-to-end against a stub senses server so the operator's one live run is not the
first execution of the write path; the stub readings were destroyed and never enter the record.

**THE FIRST LIVE READ** (2026-08-04, `output/blind_read/20260804_054003`, qwen2.5-omni-7b on
LM Studio :1234 via `CHIMERA_SENSES_URL`): the independent eye's verdict is **F2, confirmed by
a reader who built none of it.** Locomotion reads (beat08 walk+jump 0.85, beat00 standing 0.6);
the OBJECTS do not read as their materials — the stone is "a ball", "a backpack", "an object",
the tuft is "small piles of white material", the pile is "sand or dirt / white powder"
(object beats 0.2–0.25). The residual named in the re-record verdict — present, not yet
legible — is now measured by the dyad's own eye, not just asserted by its builder. Instrument
notes: (1) the eye reads the CONTACT SHEETS, so it judges tiles of ~200 px, a harder bar than
the hero frames; (2) LM Studio :1234 refused the 30-frame stand_in_world post (HTTP 400); the
first 15 frames (the hold) read as "a humanoid figure standing on a green surface, a small
patterned sphere to the right" — the stand and the stone both present — so its align (0.2)
covers the hold alone, the collapse being outside the truncated window. The signature, as
always, is THE HUMAN's.

## MEMBRANE: INK (2026-08-04, Kimi) — THE HUMAN's ruling, stated as a theory

**STATEMENT (THE HUMAN's ruling, given the theory's shape).** The object beats' low align is a
splat-DENSITY deficit, not a wrong-albedo or wrong-geometry one: the objects do not carry
enough ink at the session camera to read as their materials. Measured supports: the pile fills
its cone by volume, so only ~a third of its 400 clods sit on the visible surface — ~10%
coverage of a 4.1 m² cone, which is why the eye read "scattered white powder"; the stone's 160
surface splats were measured against a 40-splat smudge, never against material identity; the
tuft's 13 blades were derived against OVERPAINT at the probe rig, a nearer camera than the
session's. The physics rows do not move: the stone's n and the pile's clods are display-only
already, the tuft's aggregate spring is exactly count-invariant, and `_STEP0`'s own comment
names it a render budget — "if the budget changes this is the number to change." THE HUMAN
changed the budget.

**PREDICTION.** Densify — stone 160→640 surface splats (surface_grain rescales, size unmoved),
pile 4 display splats per grain (physics still counts 400), tuft 13→40 blades (count-invariant
spring), ground `_STEP0` 0.90→0.45 (near detail ×2, the sanctioned dial) — then re-record the
session and re-read it with the SAME eye, prompts, and expected terms: the object beats
(beat01–beat07) mean align rises from 0.22 to ≥ 0.50, with no physics number anywhere changed.

**FALSIFIER.** Mean object-beat align stays < 0.35 after the density step — then splat count
was not the binding constraint, the dials go back, and the gap is something else (angular size,
shading, or the sheet instrument itself).

**FALSIFIER FIRES** (2026-08-04, `blind_read/20260804_060556` vs `..._054003`, judged by
`tools/ink_ab.py`): object-beat mean 0.229 → 0.271, under the 0.35 floor. **Splat count was
not the binding constraint for material identity.** The dials STAY regardless — they are THE
HUMAN's taste rows and the world is visibly denser by eye (the pile now reads as a mound with
scatter, the stone as a solid textured body) — but the theory that density buys identity is
dead, and the run measured two things beyond itself:

1. **The instrument's noise floor is ±0.3 per beat.** beat00 (the unchanged stand beat) swung
   0.60 → 0.25 on identical content; beat07's 0.25 → 0.85 "gain" is the scorer crediting the
   background pile's "mounds" against the tuft's expected term. Omission scores 0 the same as
   misreading: the SEE prompt asks for one or two sentences about a 12-tile sheet and the eye
   spends them on the figure. Any future legibility membrane must first shrink this floor —
   per-object crops, not whole sheets — or its deltas will be noise.
2. **The remaining gap is named, not guessed:** the stone reads as a *ball* because it IS a
   fibonacci sphere — identity there is GEOMETRY (facets, fracture), not ink; the tuft's gap is
   vertical-blade shading against a sunlit slope (the residual already recorded); and
   `stand_in_world`'s 30-frame WATCH post 400ed on LM Studio a second time — a hard instrument
   limit, recorded.

## MEMBRANE: CROP (2026-08-04, Kimi) — the instrument before the verdict

**STATEMENT.** The whole-sheet read's noise floor (±0.3 per beat, measured in INK) is an
OMISSION artifact, not reader error: the SEE prompt asks for one or two sentences about a
12-tile sheet dominated by the figure, so the eye spends them on the figure and never mentions
the object — and omission scores 0 exactly like misreading. Feed the eye a frame the object
FILLS and omission becomes impossible; what remains is the render's own identity claim.

**PREDICTION.** `python tools/blind_read.py --crops` reads `output/session_legibility/`'s
per-object frames (stone_close, stone_session, pile_close, pile_session, tuft_close,
tuft_session — same session the whole-sheet read scored on) with the same eye, prompt, and
expected terms: mean align over those six ≥ 0.50, against the whole-sheet object-beat 0.271.

**FALSIFIER.** Cropped mean < 0.35 — then the instrument was never the constraint and the
renders themselves do not carry material identity, which sends the work to GEOMETRY (the
stone's sphere) and SHADING (the tuft's up-normals) with no instrument excuses left.

**FALSIFIER FIRES** (2026-08-04, `blind_read/20260804_061925`): cropped mean **0.336** over the
seven scored frames, under the 0.35 floor — and the readings are decisive in content, not just
number. With omission impossible (the eye described the object every time): `stone_close` is
"a white **spherical** object with a dotted texture" (0.0) — the eye names the geometry at
point-blank range; `tuft_close` is "an **underwater** view" (0.0) — the tuft's green glow reads
as water, not blades; the pile inverts (`pile_close` "bubbles" 0.2, `pile_session` "sandy
surface" 0.85 — its identity survives range, not proximity); `tuft_session` 0.85 ("walking on
grass" — the GROUND carries grass-ness, the tuft does not). The instrument is cleared; the
renders themselves lack identity. The next rungs are exactly the two the membrane named:
**GEOMETRY** (the stone's fibonacci sphere — a ball at any ink, any crop) and **SHADING** (the
tuft's green-on-green glow — water, not blades). Instrument note: two stale `*_before.jpg`
frames in `session_legibility/` were read harmlessly (no expected terms); the directory needs a
clean rule if it feeds future reads.

## MEMBRANE: FACETS (2026-08-04, Kimi) — the stone's geometry, not its ink

**STATEMENT.** A rock's identity to a reader is its SILHOUETTE and its FLAT SHADED PLANES, not
its point density: the CROP read proved 640 well-lit splats on a fibonacci sphere still read
"spherical" at point-blank, so identity must come from geometry. A fractured rock is a lumpy
convex body cut by planes — radially: low-frequency lumps, then the radius clamped by a few
facet planes, every splat on a cut wearing the PLANE's normal (flat shading, the facet made
visible in light). This is a render row: the physics keeps its sphere (contact, roll, carry
are already a sphere model, unchanged), and the shape is deterministic from one seed — the
same rock in every frame, every session.

**PREDICTION.** `_rock_shape()` replaces the bare fibonacci directions in `Stone.buffer`
(3 sinusoidal lump modes, 7 facet planes at 0.72–0.92 r, plane normals on cut splats);
re-rendered, the eye reads `stone_close` at align ≥ 0.50 against "a grey rock sitting on green
ground, seen up close" AND its reading carries an angular word (rock/angular/faceted/flat) with
no "spher"/"ball".

**FALSIFIER.** The eye still says sphere/ball/smooth at point-blank, or align < 0.35 — then
silhouette and flat shading do not buy identity either, and the residual gap is micro-texture
beyond what a splat surface can carry. That would be a finding, not a failure: it bounds what
the splat medium can claim.

**FALSIFIER FIRES** (2026-08-04): three eye reads, two shape iterations, two cameras — every
one "spherical", align 0.0. Iteration 1 (7 shallow planes, 0.72–0.92 r): cuts never reached the
silhouette; the perceived surface is the dot ENVELOPE. Iteration 2 (5 deep planes, 0.55–0.75 r,
grain ×1.15 — measured need: only deep planes put chords in the hull): my eye sees a loaf with
a flat base in the isolated 1.2 m probe (`facets_probe.jpg`), the eye still reads "white,
pixelated sphere… a planet". **Silhouette and flat shading do not buy rock identity in the
splat medium at this scale** — the eye keys on two things no geometry row moves: the DOT
TEXTURE ("composed of small dots" in every reading) and the WHITENESS (quartz albedo through
lit()+tone at exposure 2.0 renders near-white, and a white regular body reads as a ball, a
planet, a golf ball — never a rock). The shape stays (harmless render row, truer than a perfect
sphere; deterministic seed). The published bound: **identity at session scale does not live in
geometry; the medium's dot grain and tone decide it.** The two theories that remain, named for
the next membranes: CHUNK (fewer, larger angular splats — the pile's clods already out-read its
grains; 640 dots blur to "texture" at the eye's effective resolution, ~60–80 chunks may read as
a solid faceted body) and TONE (the whiteness is one exposure dial and one measured albedo —
THE HUMAN's row, both of them).

## MEMBRANE: CHUNK (2026-08-04, Kimi) — the dot grain IS the texture the eye reads

**STATEMENT.** At the eye's effective resolution, 640 splats of ~4 px do not read as a surface
— they read as a TEXTURE ("composed of small dots", every reading), and the brain groups dot
centres into a smooth envelope, which is why every geometry attempt read "spherical". A surface
of ~72 splats of ~13–20 px cannot blur the same way: each splat is a visible tile, tiles on a
facet are coplanar and same-lit, so the facet reads as a flat plane of colour and the body as
solid. The pile already proved the direction — its 6 cm clods out-read its 0.35 mm grains at
every distance; CHUNK is the same law applied to the stone, and `surface_grain` sizes the tiles
by derivation (close the surface with n tiles), not by choice.

**PREDICTION.** The stone at n = 72 (same `_rock_shape`, grain from `surface_grain(72, r)` ≈
3× the 640-dot grain): the eye reads the isolated probe AND `stone_close` without the words
"dots"/"pixelated", with align ≥ 0.50 against "a grey rock, seen up close".

**FALSIFIER.** The eye still reports dots/pixelation, or align < 0.35 — then the splat medium
cannot carry rock identity at ANY grain at session scale, the bound closes over CHUNK too, and
the only remaining row is TONE (THE HUMAN's exposure + the measured albedo).

**FALSIFIER FIRES** (2026-08-04): 72 tiles read "nebula / cluster of light points" (0.25) at
the derived grain and "glowing circle" (0.2) at the derived-for-scatter 0.073 grain — splat_ruler
re-measured for the derivation (bright core = 2.4× s), and it did not matter. The bound now
closes over THREE membranes in one day: density (INK: 160→640, "dots"), grain (CHUNK: 72/0.042→
0.073, "nebula"→"glow"), geometry (FACETS: lumps+planes, "sphere" at every cut). **At session
scale the splat medium renders a small pale body as an ethereal glowing abstraction, and every
reading keys on the same two words: white and glowing.** That is not a geometry, density, or
grain claim — it is the tone mapping: quartz albedo through lit()+tone at exposure 2.0 clips
toward white with a hot centre, and a hot-centred pale blob reads as a light source, never as
rock. The one remaining row is **TONE**, and it is THE HUMAN's twice over (the exposure dial is
theirs; the albedo is theGround's measured quartz). The stone reverts to 640 dots + the FACETS
shape — the best of the measured set in context.

## STATUS

- **F1 — PASS.** Every published number on the touch line traces to its membrane.
- **F2 — STILL FIRED**, and now with the cleanest evidence yet: a closed-loop recorder, all beats
  landed, physics reporting correctly, and a frame a blind reader would describe as an empty field.
- **F3 — PASS**, by `tools/f3_stand.py` (exit 0), **and now on camera**: the musculoskeletal stand
  is recorded in `tools/stand_on_camera.py`'s 30-frame two-phase video (upright hold, then the
  release slump) — the bridge named above, built 2026-08-04. What is still not on tape is the
  stand *inside the Walker session* (the mover and the musculoskeletal body remain two rigs);
  that composition is the next bridge, named here rather than glossed.

## MEMBRANE 8 — BLADE-AZIMUTH (the tuft's uniform lambert)

**STATEMENT.** The tuft's "underwater view" reading (CROP, membrane 3) is a lighting-geometry
defect, not tone: every blade splat wears the UP normal (the FLAT-GROUND lambert, sin(alt) =
0.793 at the session's 52.5 deg sun), so 60 blades render with one identical brightness — a
uniform saturated green plane has no depth cue and reads as water. A blade is a vertical
cylinder: it is lit by the HORIZONTAL beam component, and only its sun-facing side. A tuft is
blades at all azimuths — a statistical mixture of lit sides (lam = cos(alt) = 0.609), shaded
sides (lam = 0, sky+bounce only), and the spread between. The mixture is the texture that reads
as grass. Measured before building: flat ground 0.793, cylinder sun-side 0.609, cylinder mean
(2/pi·cos(alt)) 0.388 — the mixture is DARKER on average than flat ground, and real grass under
a high sun is exactly that: a field of mixed lit and shaded blades, never a uniform bright
plane. Physics, not taste: the geometry of a cylinder under a sun is not a dial.

**PREDICTION.** With per-blade horizontal normals at golden-angle azimuths (deterministic,
uniform over [0, 2pi), the same sampling the blade FEET use), the eye reads `tuft_close` and
`tuft_session` with align ≥ 0.50 against "blades of grass in a field", and the words
"underwater"/"water" do not appear.

**FALSIFIER.** The eye still reports water/underwater, or align < 0.35 — then the green glow is
albedo/tone (THE HUMAN's _TUFT_ALB row + the exposure dial), the cylinder theory is dead, and
this membrane publishes the bound and stops.

**FALSIFIER FIRES** (2026-08-04): built as stated (per-blade horizontal normals, golden-angle
azimuths). Measured before believing: flat ground lam 0.793, cylinder sun-side 0.609, cylinder
mean 0.388 — the mixture is real and visible in the frames (lit strokes AND dark strokes; the
trample trail behind the walker now reads as flattened grass). But the eye: `tuft_close` "a
serene UNDERWATER scene" 0.0, `tuft_session` 0.0. The cylinder theory is dead — lighting
geometry is not the defect. And the fired reading contains its own attribution: `tuft_close` is
a frame dominated by the GROUND, and the eye reads the whole frame as water. The "underwater"
is the world's saturated green field itself — albedo through lit()+tone at exposure 2.0 —
which is THE HUMAN's row twice over (_TUFT_ALB/theGround's grass albedo + the exposure dial),
the same TONE bound the CHUNK membrane published for the stone. The cylinder normals STAY
(truer physics — a blade is a cylinder — at a fired-but-equal reading: both shadings read 0.0;
the trample trail is a real legibility gain). What remains for vegetation identity is exactly
what remains for the stone: **TONE, THE HUMAN's dial.** This membrane publishes the bound and
stops.
