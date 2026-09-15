# Judge 2 — running notes (R8/R4 blind buyer test)

Pre-flight checklist:
- [x] tooling check passed (`node -e "require('playwright')"` -> ok)
- [x] driver started, resp.jsonl shows did:"goto" (439 ms) then did:"ready"
- [x] S1 cold-landing shots + first impressions written before touching anything
- [x] S2 controls self-taught, stalls logged
- [x] S3 at least 3 lessons to pass/fail, page's exact result text captured
- [x] S4 press-hold-release-recover witnessed and described
- [x] S5 free play done
- [x] verdict block filled, honesty note included
- [x] artifacts collected

Session length: ~37 min hands-on (23:27:57Z goto -> 00:05Z quit).

## S1 — Cold landing (first impressions, written BEFORE touching anything)

Shots: 01_landing, 02_landing_settled.

What I think this is: a virtual-creature toy called CHIMERA. Tagline:
"a creature of water and skin. touch it, and it answers." So: a soft/squishy
thing on screen you poke and it reacts. Maybe a pet sim.

What I'd click first: PLAY (dead center, obviously the door).

Hesitations / first reactions (honest):
- "your name (your camera's name)" — WHAT? Why does a creature toy need my
  camera's name? Is my webcam involved? That made me pause. I do not want to
  grant camera access to a toy.
- I don't know if PLAY works without typing a name. (It did — it named me
  "wanderer" and the tutorial later explained: I AM a camera. The landing
  page alone never told me that.)
- Visual taste: high. Dark, serif, spaced letters. Feels expensive-ish.
- "the world remembers you" — mildly ominous, mildly intriguing.

## S2 — Self-taught controls

- PLAY without a name: worked, assigned "camera · wanderer". Good.
- Tutorial card: "You are a camera in one living world. Drag to look. Click
  (or SPACE) to touch — hold to press." + Begin button. Clear.
- Drag = look: works (rotated around the creature).
- Wheel = zoom: works (both directions).
- Lesson panel: ‹ 1/10 ›, progress dots, "WAKE THE CELL".
- STALL: clicking the › arrow at its visible pixel did nothing; keyboard "2"
  jumped to lesson 2. Arrows never worked for me the whole session.

## S3 — Lessons (exact page wording captured)

- L1 WAKE THE CELL — press the big body, HOLD, push torso cell past 0.02 MPa,
  let go, watch it heal. During hold the status flipped to "the goal is met —
  now LET GO, and let the body heal." Hand read "pressing — 20000 N", torso
  cell 0.956 MPa. After release: 0.956 -> 0.432 -> 0.000, volume restored.
  Result: "PASSED — you pressed, the cell woke, and the water healed itself.
  the world is real."
- STALL: first foot press for L2 landed on nothing (all cells 0.000); had to
  zoom in and re-aim; only then saw the feedback line "you touched only water."
- L2 THE GENTLE HAND — keep force under 8,000 N, press a foot past 50 kPa.
  Dragged the hand slider down (20000 -> 4300 N). Foot press: cell 0 spiked to
  2.624 MPa. Result: "PASSED — a gentle hand: the small water answered a
  small touch."
- L3 THE HEALING — wake any cell past 0.02 MPa, release, wait; "Nothing heals
  while you keep holding; the healing begins when you let go." Belly press at
  4300 N: 0.156 -> released -> 0.107 -> 0.006 -> 0.000.
  Result: "PASSED — you let go, and the body healed itself. it never needed
  you."
- L4 BEND THE KNEE — says "Set the left knee to 40" ... and shows NO control
  to set a pose with. It passed itself instantly: "PASSED — this one is yours
  already." I still do not know how a pose is "posted". Felt like a stub.

## S4 — The press test (required)

Dedicated sequence (shots 22-27, 28-30): pressed the belly at 4300 N, held
~6 s: "pressing — 4300 N", cell 1 = 0.171 MPa, V 12.509 -> 12.508 m3.
Released: 0.089 -> 0.001 -> 0.000 MPa over ~5 s, volume restored to 12.509.
Later at 35800 N the torso spiked to 1.514 MPa; a foot press spiked its cell
to 25.511 MPa; a shin spot spiked cell 2 to 14.814 MPa.
THE TAIL: pressing it drove the torso cell to -2.255 MPa — NEGATIVE pressure.
Pulling the tail sucks water. Best single moment in the demo.
Honest caveat: at no force, from no angle, did I ever SEE the skin dent.
The squish is entirely in the HUD numbers. That is the demo's biggest gap.

## S5 — Free play

- "stand at rest" button -> status "standing at rest". Creature was already
  standing; could not tell what changed.
- save progress -> "saved. the world remembers you, wanderer." Charming.
- SPACE to touch: works, hand even labels it "pressing — 35800 N (space)".
- L5 THE WHOLE BODY (torso past 0.2 MPa + "shins" past 0.1 MPa): torso goal
  met (1.514 MPa), but "shins" never registered. Probed legs at many pixels:
  mostly "you touched only water.", once cell 2 spiked 14.8 MPa, still "the
  creature waits." Never found cell 3's body part at all. Gave up.
- Cells 0 and 1 were loaded by feet/head/arms/tail; cell 2 only by one tiny
  leg hot-zone; cell 3 never. The page never says which cell is which limb.

## Stall list (buyer-blamable)

1. Landing: "your name (your camera's name)" unexplained; unclear if PLAY
   needs it. (Resolved only after entering.)
2. Lesson panel › arrow: clicked twice across the session, never advanced.
   Keyboard 2-5 works; nothing on screen taught the numbers before the
   tutorial card ("1–5 lessons" chip).
3. First foot press (L2) hit nothing; required zoom + re-aim.
4. Slider: drag aimed at the visible thumb but above the real track (y=435 vs
   443-471) — no response, no hover affordance to show the hit area.
5. Slider: FIVE failed attempts to drag it back up (thumb-grab at computed
   positions, PageUp, End, slow drags) — stuck ~4 minutes; finally moved when
   grabbed at y=451. Finicky grab zone.
6. "you touched only water." appears even when the cursor is clearly on a
   limb (legs). Cryptic copy; no hint about cell hit-zones.
7. L4 has no pose control yet passes itself — unfinished feel.
8. L5 "shins" goal uncompletable as far as I could tell (see S5).

(Technical note, MY tooling not the product: my command-file writer once lost
a race with the driver's 400 ms poller and an empty command file was consumed.
Retried; no product impact.)

## Page errors

- 2x `net::ERR_NO_BUFFER_SPACE` on `/api/verts` and `/api/state` (23:31:43Z,
  23:44:24Z). Page kept running, no freeze, no crash; recovered instantly.
  (Both look like streaming-buffer limits; possibly related to two judges
  sharing the demo. I backed off — my session is turn-based and slow.)
- No PAGEERROR, no console errors besides those two resource failures.
