# STORE_COPY.md — R7 store copy, honest by construction

Every claim below traces to `docs/THE_SHIP_GOAL.md` (a PASS line, a run record,
or the ledger). No superlative appears that the goal book does not earn; the word
"measured" appears only where a number exists. British-friendly English throughout.

---

## SHORT DESCRIPTION (89 characters, limit 100)

> Touch a living creature of sealed water cells. Real pressure, real healing, five lessons.

---

## DESCRIPTION (~195 words)

Chimera is a creature you touch, and the touch means something.

Under its skin sit sealed cells of water. Press anywhere and the cells answer:
the skin dimples, the pressure rises, and the rest of the body feels it — because
that is what water does. The pressure follows the compressibility law of water,
the same law that governs every drop, including yours. Let go and the creature
heals on the relaxation clock of real tissue, returning exactly to rest.

There is nothing to read and nothing to memorise. Five short lessons each ask one
question, and you answer it by touching: wake a cell past its sleeping pressure,
learn a gentle hand, bend a knee and feel the force travel. Passing is decided by
the physics, not a quiz, and your progress is saved.

One world runs, and every player joins it as another camera. There is only one
creature; what one player touches, every camera sees. And the world keeps its
memory between visits — a world, not a screensaver.

Underneath, the physics steps about three hundred times a second, measured.

No manual, no menus to learn. Just reach out and press it.

---

## FIVE BULLET FEATURES (each a verified fact, with its trace)

1. **Sealed water cells with real pressure, by the compressibility law of water.**
   Trace: R3 PASS — "press it anywhere and the sealed cells answer (dimple,
   pressure, recovery)"; the kappa answer, belly 30 kN -> torso +0.534 MPa;
   "volumes conserved, pressures honest".

2. **Touch anywhere and it answers.**
   Trace: R3 PASS — camera-ray pick with a closed loop of 0.0 px; the press lands
   where you point, under pose and at rest; posed touch sub-millimetre on the
   moved knee.

3. **Healing on a real tissue-relaxation clock.**
   Trace: R3 PASS — "tau recovery exact"; R2 run record — "release healed
   (dimple 0, all P 0)"; W5 PASS — "rest exactness untouched".

4. **Five teaching lessons you pass by touching.**
   Trace: R4 — five lessons live on the rail (wake the cell, gentle hand,
   healing, bend the knee, whole body), each judged from the live physics;
   wake_the_cell and bend_the_knee PASSED and SAVED; thresholds re-tuned to
   measurement (wake 20 kPa, gentle 200 Pa).

5. **One living world — every player another camera.**
   Trace: THE WORLD LAW — one world, one creature; a player is a viewpoint plus
   the intents they speak into it; "what one player touches, every camera sees";
   the session snapshot persists between visits (R1 PASS restore).

---

## FAQ (three questions)

**Is the physics real?**
Yes. The creature is sealed cells of water. Squeeze one and its pressure rises
the way the compressibility law of water requires, and its neighbours feel it.
The lessons are tuned to what the physics actually measures — a cell wakes at
20 kilopascals, a gentle hand is 200 pascals — and letting go returns the body
to rest exactly.

**What do I do?**
You press, hold and pose. Each lesson asks one question — wake a cell past its
sleeping pressure, press until the beam bends, how much force? — and you answer
by touching the creature. The physics judges the answer, and your progress is
saved.

**Who is it for?**
Anyone who wants to feel physics rather than read about it: curious hands of any
age, and classrooms and home-schoolers — the lessons were built to carry school
use. No developer knowledge is needed: download it, double-click it, play.

---

## TAG SUGGESTIONS (5)

1. Physics
2. Education
3. Simulation
4. Relaxing
5. Sandbox

---

## HONESTY LEDGER (claims deliberately NOT made)

- No "60 fps on mid-range machines" — R6 is OPEN (the bench run rides the
  integration milestone). The only performance sentence is the measured
  295-302 ticks/s.
- No multiplayer-concurrency promise — THE WORLD LAW is the architecture and
  the camera model; the copy quotes the law, no more.
- No launch-date, price, or store-availability claims — those are the
  operator's moves.
