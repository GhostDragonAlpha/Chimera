# L1_LESSONS_BYHAND — the by-hand audit that closed the walker/judge gap

The headless walker passed 10/10 while BOTH blind judges stalled and diverged.
This lane built the by-hand instrument (`tools/game_shell/byhand_lessons.js`:
headless Chrome driving the page like a slow human — stepped pointer moves,
200–400 ms pauses, seconds-long holds, drags on the visible sliders, releases
through the visible "let go" button, navigation by the visible arrows; zero
scripted POSTs, none of the walker's API shortcuts) and ran it BEFORE and
AFTER the fixes. Every defect below follows RULE 0: mechanism → before-repro →
fix → after-gone.

Runs (JSON in this directory):
- `byhand_byhand-before.json` — BEFORE any fix: **7/10 by hand**, every defect live
- `byhand_byhand-after.json` / `-after2.json` — intermediate (probe-side artifacts
  named and fixed; the page-side honest-refusal hints first captured here)
- `byhand_byhand-after3.json` — AFTER all fixes: **10/10 by hand, ten distinct
  pass sentences, zero page errors**
- `walker_run/` — the formal walker on the SAME page: **10/10 fresh passes,
  progress 10/10, zero page errors**

## THE FINAL PER-LESSON VERDICT TABLE (by hand, run byhand-after3)

| # | lesson | control (all visible on the page) | action required | verdict sentence (all distinct) |
|---|--------|-----------------------------------|-----------------|---------------------------------|
| 1 | wake_the_cell | force slider + click-hold the belly + "let go" | press belly past 0.02 MPa, release, heal | PASSED — you pressed, the cell woke, and the water healed itself. the world is real. |
| 2 | the_gentle_hand | force slider + click-hold a foot + "let go" | foot past 50 kPa at ≤ 8000 N | PASSED — a gentle hand: the small water answered a small touch. |
| 3 | the_healing | click-hold any part + "let go" + wait | wake any cell, release, wait the heal | PASSED — you let go, and the body healed itself. it never needed you. |
| 4 | bend_the_knee | **knee_L angle slider + "post"** | set 40° yourself and post the wish | PASSED — the creature obeyed a wish, not a touch. |
| 5 | the_whole_body | click-hold belly, then the shins + "let go" | torso past 0.05 MPa AND shins past 0.02 MPa, then calm | PASSED — two rooms woke under one hand, and the whole body went quiet together. |
| 6 | the_balance | **two wish chips (ankle_L, ankle_R), each slider + "post"** | post BOTH wishes yourself | PASSED — two opposite wishes held at once. that balance is yours. |
| 7 | the_heavy_hand | force slider to max + click-hold the belly + "let go" | torso past 1.5 MPa (reachable: 2.735 measured) | PASSED — the same body, your whole strength: pressure follows force. |
| 8 | the_cascade | force slider + click-hold belly + "let go" | torso wakes while feet/shins stay quiet | PASSED — the belly woke and the legs slept through it. sealed means sealed. |
| 9 | the_stand | **"wake the world's weight" button** | press it, watch the settle (real fall measured: root_y 9.5 mm) | PASSED — the world turned on its own weight, and the creature stood still in it. |
| 10 | the_graduation | click-hold three different parts + "let go" | 3 distinct cells past 20 kPa, then calm | PASSED — three rooms woke for your hand, and you let them all go quiet. |

---

## THE DEFECTS, EACH CLOSED BY MEASUREMENT

### D1 — L4 "passed itself with no control offered" (judge 2's exact verdict text)
- **Mechanism.** One button posted the lesson's goal verbatim (`/api/pose knee_L 40`): one
  click = pass, no angle ever chosen. On a saved-passed lesson the handler early-returned —
  the chip stayed visible but inert under "PASSED — this one is yours already." And a
  1800 ms auto-reset re-posed the body so fast judge 1 "never saw the knee bend".
- **Before-repro** (byhand-before): `bend_the_knee PASS, "PASSED — and the body stands at
  rest again.", DEFECT: no angle control — one chip posts the goal verbatim`; the second
  click did nothing.
- **Fix.** The pose wish is now a CONTROL (`index.html::buildPoseCtrl`): one row per wish —
  joint name, an angle slider the player sets, a "post" button per wish. Judge unchanged
  (accepted post within ±2° of the goal). Passed lessons stay replayable (a matching
  re-post re-speaks the pass line). The 1800 ms auto-reset is REMOVED — the knee keeps its
  bend until the player leaves (entering any pressure lesson resets, `showLesson`).
- **After-gone** (byhand-after3): wrong wish first (60°) → honest refusal "the wish held
  knee_L at 60° — this lesson waits for knee_L at 40°.", then 40° posted → PASS with the
  lesson's OWN line. Walker L4: slider fill 40 + post → PASS.

### D2 — L5 stuck at "the creature waits." (the shins goal)
- **Mechanism (three stacked causes, all measured).**
  1. **The foot/leg CLICK rail missed the skin entirely.** The pack's foot targets
     `[±0.46, 0.18, 0.3]` sit ~0.5 m off, in the GAP between the feet (the pick probe shows
     the feet's skin at |x| ≥ 0.5). The page's pick demanded a pixel-exact first hit —
     a ~12 px foot at the default camera. The SPACE rail never noticed because
     `snapToVertex` lands on a foot vertex anyway — the exact walker/hand divergence.
     Both judges: leg presses "mostly returned 'you touched only water.'"
  2. **Zero feedback while half awake.** The "one compartment is awake" note sat behind the
     `goalMet` flag — it fired on the SAME poll the release verdict replaced it (dead code),
     and with ONE room awake the verdict stayed "the creature waits." Judge 2 sat on that
     line with a leg at 14.8 MPa.
  3. **Cells were anonymous.** "cell 3" meant nothing; the lesson says "shins".
- **Before-repro** (byhand-before): L2 and L10-foot pressed the projected target pixel —
  `hand: "you touched only water."`, all cells 0.0, lesson unwinnable by clicks.
- **Fix.** (a) Pack: foot targets re-measured on-skin (`the_gentle_hand` → [1.03, 0.25, 0.79];
  `the_graduation` feet → [1.03, 0.25, 0.79] / [-0.51, 0.26, 0.41]); torso/shin bars
  15k/5k → 50k/20k Pa so the BODY COPY states the judge's real numbers. (b) Page: a ~14 px
  near-miss pick grace (`pickNearMiss` — nearest-to-camera vertex within 14 px and ≤ 0.75 m
  of the ray; open water still misses); blood panel rows labeled `feet/torso/thighs/shins
  (cell N)`; the hand NAMES the part it is pressing ("pressing the shins — 20000 N");
  single-room latch now speaks ("the shins are awake — the lesson still waits for the
  torso."); pressing the WRONG part says so, once per press; the 25 s stall hint (SPEC §4's
  HINT_AFTER_MS) is now real; the water miss names the aim ("…aim for the shins, then
  hold."). (c) `pressFresh()` stays open while the engine holds the press (the walker's
  2.0–2.2 s scripted holds fit the old 2.5 s window; a human's 5 s holds did not — latent
  divergence, fixed).
- **After-gone** (byhand-after3): "pressing the shins — 20200 N", cell 3 → 13.57 MPa under a
  5 s human hold, latch inside the hold, PASS. L2 foot presses land ("pressing the feet").

### D3 — L6 "declared after ONE of the two wishes; second chip inert" (judge 1)
- **Mechanism.** The single chip posted BOTH ankle wishes in one click; after the pass the
  chip stayed on screen and the handler early-returned — inert.
- **Before-repro** (byhand-before): PASS on one click, chip inert, sentence shared with L4.
- **Fix.** Per-joint wish rows; each post sends ONLY its own wish; a latched row marks
  itself ("held", green). Pass requires BOTH posts (any order).
- **After-gone**: "one wish is held — the other waits." after the first post, PASS on the
  second. Walker L6: two slider posts → PASS.

### D4 — L7 the_heavy_hand was UNWINNABLE where it points (by-hand discovery)
- **Mechanism.** The lesson demanded torso ≥ 3 MPa "at the very top" of the slider.
  Measured by hand at the 50 kN max: the camera-facing belly peaks **2,734,980 Pa** (and the
  old SPACE-rail vertex 1.93 MPa). No verb the page offers reaches 3 MPa at the belly.
  Falsifier stated before measuring: if the belly at max measures ≥ 3 MPa, the lesson is
  winnable and the defect lies elsewhere — it measured 2.735.
- **Fix.** Threshold 3.0 → **1.5 MPa** (under the weakest measured belly answer with ~25%
  headroom; P linear in F → reachable from ~28 kN at the pointed vertex, ~39 kN at the
  weakest); `touch_target` re-pointed to the measured strong vertex [-0.23, 4.71, 0.74] so
  BOTH rails reach it; body copy and hint renumbered; walker L7 back to the pack's own
  SPACE press (click-spiral kept as a logged fallback).
- **After-gone**: byhand L7 PASS at the slider max ("the same body, your whole strength…");
  walker L7 PASS via SPACE.

### D5 — L9 the_stand passed with ZERO player action
- **Before-repro** (byhand-before): "DEFECT: nothing to do … PASSED WITH ZERO PLAYER ACTION".
- **Fix.** The page no longer enables gravity at lesson start. The lesson card carries
  "wake the world's weight"; the judge arms only on that click's `ok:true` (H10's false-arm
  rules carry over). "stand at rest" now also lays gravity back down — the page finally has
  a player-surfaced way back to the authored rest (the by-hand audit itself uses it).
- **After-gone**: byhand L9: click → real fall (root_y 0 → 9.5 mm) → settle → PASS.
  Walker L9: button click → armed=true → PASS (no diagnostic fallback).

### D6 — Judge 2's navigation stall list
- **Dead arrows: NOT REPRODUCIBLE** on the current page — the audit clicks › and ‹ ten
  times per run, both directions verified (before AND after). The judges ran a pre-G5
  five-lesson build; their report is preserved as evidence of that build, not this one.
- **Keyboard mapped only 1–5 for a TEN lesson pack** (reproduced: key "7" dead before) →
  keys 1–9 + 0 reach all ten; intro diagram now says 1–0. After: "7 / 10" shown.
- **"you touched only water."** → now says WHY and WHAT to aim for (D2), and the near-miss
  grace makes the message rare instead of routine.
- **Unexplained cell labels** → every row labeled (D2); distinct pass sentences confirmed
  for all ten (L4/L6 used to share the reset-overwritten "and the body stands at rest
  again.").

## Page-integrity notes
- Engine untouched (another lane owns it); all traffic through the page's 8206 doors;
  engine 8107 only ever read via GET through the proxy. No shell restart needed
  (server.py serves static files per request; page-only change).
- Stream purity, H7 release funnels, W2 dent shader, H16 pick parity all untouched; the
  near-miss pick only runs on a MISSED pickWorld ray.
- Walker AND hand both 10/10 on the same served page — the divergence the judges
  measured is closed from both sides.
