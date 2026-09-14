# judge1 running notes

## S1 · Cold landing (written BEFORE touching anything)

Landing page loaded fast (<1s). Very dark, moody, serif type. Big title "CHIMERA"
with wide letter-spacing. Tagline: "a creature of water and skin. touch it, and it
answers."

**What I think this is:** some kind of virtual pet / interactive creature toy on the
web. "Touch it and it answers" suggests you poke it and it reacts — a digital pet
with a personality, maybe AI-driven. The name field says "your name (your camera's
name)" — that wording is odd. "Camera"? I had to reread it twice (stall candidate
already, and I haven't clicked anything). Maybe "camera" = persona/observer? It's
unclear. "Your progress is kept under your name — the world remembers you" implies
a server keeps progress per name, and maybe other people exist in the same world.

**What I would click first and why:** the name field, then PLAY. The page tells me
progress is kept under my name, so I want a name in before pressing PLAY — PLAY is
the only obvious action on the page. Aesthetically it's confident: minimal, no
instructions dumped on me. Slightly intimidating as a buyer — nothing here tells me
what I actually DO in it.

Reaction in the moment: "pretty. ominous. I still don't know what I just opened."

## S2 · Self-taught controls

Typed name "Mira", pressed PLAY. A modal taught everything up front: "You are a camera in
one living world. Drag to look. Click (or SPACE) to touch — hold to press. The body
answers: watch its blood." Keys 1–5 jump to lessons. No stalls getting into the scene —
the tutorial did its job. The landing page's "camera" wording still cost me two rereads.

## S3 · Lessons

- L1 WAKE THE CELL: press torso, hold. Goal text flipped to "the goal is met — now LET GO"
  mid-hold; PASSED after release. Pressure 0.889 MPa @20000 N.
- L2 THE GENTLE HAND: needed hand < 8000 N. SLIDER STALL — 4 failed attempts (see verdict),
  clicks fell through to scene and re-pressed torso (P=0.956 with hand "open"). Bounding
  box showed the real input 9 px lower; worked instantly. 11200 N → 5700 N. Foot press
  spiked cell 0 to 3.059 MPa. PASSED after settle.
- L3 THE HEALING: press, release, wait. "it never needed you." PASSED.
- L4 BEND THE KNEE: clicked the "knee_L → 40°" chip. PASSED immediately — never saw the
  knee move. Felt unearned.
- L5 THE WHOLE BODY: torso 0.255 MPa + shin press; shin cell lingered at 0.005 MPa ~10 s
  before PASSED ("two rooms woke under one hand...").
- L6 THE BALANCE: clicked ankle_L; blood showed the lean (cell 0 = 6.010 MPa, cell 2 =
  -0.009 MPa) — the lesson's claim, visible in numbers. PASSED fired after ONE wish;
  ankle_R chip inert afterwards.

## S4 · Press test (dedicated)

5700 N (slider wouldn't go back up on first try — stall #3). Held belly ~6 s: dent visible,
P pinned 0.256 MPa, V 12.509→12.508. Release: dent gone in ~1 s, all-quiet by ~8 s.
The heal is honest and slightly slow — which makes it believable.

## S5 · Free play

Orbit drag + wheel zoom: both work, smooth. Poked the head from behind → answered in the
TORSO cell (0.105 MPa) — compartments ≠ visible parts. Press-and-drag on the body rotates
the camera instead of shearing flesh. Panel has nothing below "save progress"; wheel there
does nothing. SPACE works as a touch but with no cursor I couldn't tell where. Lessons 7–10
not reached; dots show 6 of 10 lit.

Session: ~20 min hands-on. Server errors: 2 transient REQFAIL (ERR_NO_BUFFER_SPACE),
recovered. No crashes.

