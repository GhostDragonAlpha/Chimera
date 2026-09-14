# R8 MEDIA — asset manifest (agent D2, fleet 2)

Written 2026-09-13 ~22:55, as soon as the assets existed. Every asset below is a
LIVE capture of the running engine (sealed 4-cell creature, 127.0.0.1:8107 /
game page 127.0.0.1:8206) made today. Nothing is mocked, painted, or taken from
another build. Each section maps assets to the judge-named defect they answer.

## defect: motion-absent

Answers "the creature never moves" — the press-and-answer arc, from the
delivered trailer and as single frames:

| asset | what it shows |
|---|---|
| `C:\Users\allen\Desktop\CHIMERA_PROOF\TRAILER\chimera_trailer.mp4` | the 28.04 s spine: orbit → push-in → 30 kN belly press (ramped, held) → release → tau = 0.5 s healing → knee pose 40° → end card. 1920x1080, 3.3 MB. |
| `trailer_press_peak.png` | frame @ 16.2 s — "03 · 30,000 N HELD": torso P=2.309 MPa (accent), dimple 0.451 m, press 30,000 N in the HUD. |
| `trailer_healing.png` | frame @ 19.5 s — "04 · RELEASE — TAU = 0.5 S HEALING": P decayed to 0.332 MPa, dimple 0.065 m, "healing · tau = 0.5 s". |
| `trailer_end_card.png` | frame @ 26.3 s — the end card over a darkened real capture. |

Honesty: the trailer was captured live at ~1 fps and time-remapped to 24 fps
(held frames + short crossfades, no optical-flow interpolation — every visible
frame is a genuine engine render; method recorded in tools/trailer/make_trailer.py).
The stills are straight `ffmpeg -ss T -frames:v 1` pulls from that MP4 (already
1080p; no crop or resize). Trailer built 2026-09-13 22:09; stills extracted 22:54.

## defect: water-invisible

Answers "the water is a metaphor" — one PAIR, same camera, same page, seconds
apart. The blood panel is the page's live read of the engine's cell pressures
(P in MPa, drawn from /api/state = /tick_state):

| asset | what it shows |
|---|---|
| `blood_rest.png` | all four cells `P=0.000 MPa`, verdict "the creature waits." — the sealed body at rest. |
| `blood_press.png` | mid-press: slider 30000 N, torso (cell 1) `P=1.270 MPa` in the awake accent, verdict "the goal is met — now LET GO, and let the body heal." (accent), judge line `wake_the_cell phase=release goalMet=true`. The same panel, seconds later, now carries a live number. |

Read them side by side: identical scene, identical panel — the only thing that
changed is the water answering a 30 kN touch. Captured 22:47:47 / 22:47:48
(1 s apart).

## defect: prototype-look

Answers "it looks like a tech-demo dummy" — three framed beauty shots of the
creature standing at rest, full body, face and tail reading, contact shadow and
floor grid for grounding. 1920x1080 (16:9 center-crop of the native 2560x1369
render, Lanczos):

| asset | camera (v[8] = r, theta, phi, target, pan) |
|---|---|
| `beauty_01.png` | hero front 3/4 — [14.0, -2.60, 0.25, 0, 4, 0, 0, 0] |
| `beauty_02.png` | mirrored front 3/4 — [14.0, +2.60, 0.25, 0, 4, 0, 0, 0] |
| `beauty_03.png` | near-frontal, wide — [14.0, -3.30, 0.20, 0, 4, 0, 0, 0] |

Method: POST /cameras save+recall of exact 8-float bookmarks (bookmark
`d2_media`), GET /frame (one real engine render each), captured 22:51:38-42.
Six candidates were grabbed (`cand_0..5`, kept for the record) and the three
above were chosen by inspection: the others crop the crown at these radii.
Thetas measured from the first probe round — the face fronts theta ~ -2.6..-3.3;
the plan's assumed ±1.45 turned out to be side profiles (that measurement is
why cand_4/cand_5 exist).

## defect: teaching-payoff

Answers "the lessons teach nothing" — the judge's own verdict, on camera:

| asset | what it shows |
|---|---|
| `blood_lesson_passed.png` | lesson 2/5 "THE GENTLE HAND" PASSED: verdict "PASSED — you felt the water. it was always there." in the good (green) tone, 6000 N (under the 8000 N cap), judge line `the_gentle_hand phase=release goalMet=true passed=true`, all cells back to 0.000 MPa after the release+heal. Captured 22:47:57. |

The full walk (all five lessons passed by a scripted walker with measured
peak-vs-threshold numbers) is `C:\Users\allen\Desktop\CHIMERA_PROOF\R4_WALK`;
this shot is the payoff moment itself.

## previews

Every PNG above has a 1280-px JPG preview beside it (`<name>_preview.jpg`,
written 22:54). The PNGs are the deliverables; previews are the review surface.

## capture chain (for reproduction)

- `tools/r8_media/capture_blood_panel.js` — Node + playwright-core, real Chrome,
  headed, 1920x1080 @ dpr 1, driving the game page like a player: name `media`,
  PLAY, dismiss intro, then per shot: snap the touch target to its nearest skin
  vertex via /api/verts (u32 count + n*9 f32; an unsnapped point presses
  NOTHING — the kernel is a 3 cm Gaussian), POST /api/touch_hit, poll /api/state
  until the judge latches, screenshot. Restore: touch clear + verified calm
  (all |P| < 1000 Pa).
- `tools/r8_media/capture_beauty.py` — mirrors tools/trailer/make_trailer.py's
  HTTP+PIL helpers (10 s retry/backoff, shared engine): /cameras save+recall
  bookmarks, /frame grabs, 16:9 center-crop + Lanczos 1920x1080. Restore:
  touch clear, knee 0, recall `wide`.
- `tools/r8_media/extract_trailer_stills.py` — ffmpeg single-frame pulls +
  the preview pass.
- Engine state after capture: touch cleared, knee 0, camera `wide`, all cells
  calm (verified in the run logs: final |P| = 0 0 0 0 Pa).
