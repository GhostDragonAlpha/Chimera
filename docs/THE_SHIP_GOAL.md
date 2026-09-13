# THE SHIP GOAL — Steam-ready feature product (operator directive, 2026-09-13)

The operator set the goal, 2026-09-13: bring the project to a state
where it is ready to put on Steam — a FEATURE product — positioned to
make $100,000 or more over its lifetime. The Steam account itself is
THE OPERATOR'S move and waits for the finished product. This file is
the goal of record; every requirement carries PASS/OPEN and is
refreshed as work lands.

## THE BAR (what "ready" means)

A stranger who has never seen this project can: download it,
double-click it, play it without help, learn real physics by touching
it, and want to show someone else. No developer knowledge, no special
window tricks, no excuses.

## THE REQUIREMENTS (R-items, plain words)

- R1. DOUBLE-CLICK LAUNCH — PASS/OPEN: **PASS.** The game runs on a
  clean ordinary Windows machine from one double-click. Today the
  engine needs a maximised window or it stalls (measured law); the
  game must behave like a product, not a lab instrument.
- R2. THE GAME LOOP — PASS/OPEN: **OPEN.** Start screen -> play ->
  lessons -> progress saved. Something to do, a reason to continue.
- R3. THE HOOK IN MOTION — PASS/OPEN: **OPEN.** The water-physics
  answer works while the creature moves: press it anywhere and the
  sealed cells answer (dimple, pressure, recovery). Verified physics
  exists; the player-facing touch is OPEN (press where you point,
  press + pose together).
- R4. THE LESSONS — PASS/OPEN: **OPEN.** First slice: five teaching
  lessons, each with a question the player answers BY TOUCHING
  ("press until the beam bends — how much force?"). Pass/fail
  feedback. The lessons are the product.
- R5. SOUND — PASS/OPEN: **OPEN.** Effects and ambience. Silence is
  the number-one mark of an unfinished game.
- R6. ORDINARY-MACHINE PERFORMANCE — PASS/OPEN: **OPEN.** 60 fps on a
  mid-range machine (GTX 1060 class), measured, not claimed.
- R7. THE STORE PACKAGE — PASS/OPEN: **OPEN.** Trailer (the
  press-and-answer clip is the spine), screenshots, capsule art,
  description. Built AFTER R1-R4 so it shows the real game.
- R8. THE STRANGER TEST — PASS/OPEN: **OPEN.** A blind dyad judge
  (your law) looks at the demo the way a buyer would and answers:
  does this look worth paying for? The judge's verdict is the gate.
- R9. OUR OWN WEBSITE — PASS/OPEN: **OPEN** (operator directive,
  2026-09-13: "we don't have to use Steam"). A landing page that
  hosts the free demo, lets a stranger play first, and asks them to
  sign up afterwards — our page, our player list, no store gate.
  Selling later needs the operator's payment account (Stripe or
  PayPal, his identity); everything else on this page is buildable
  without him. The engine already speaks web (the browser viewer),
  so a browser-playable demo is in reach.

## THE REVENUE POSITION (why this can reach $100,000+)

- The hook is novel and provable in ten seconds of video — novelty is
  the rarest thing on any store.
- OUR OWN CHANNEL FIRST (operator, 2026-09-13): the demo lives on our
  website, players sign up after playing. A store takes 30%; our own
  page with a payment processor keeps ~95% — $100,000 needs ~7,000
  copies at $15, not 10,000. The sign-up list is ours: every demo
  player is a launch-day customer we can reach directly, and each
  lesson pack after launch is a reason to return.
- Steam remains OPEN as a second shelf later (not required): the same
  package serves both.
- The teaching angle carries school/home-school licences (a second
  lifetime channel).
- Price target: $15-20. With the demo funnel — play free, sign up,
  buy — the copy count is reachable without a festival slot.

## THE ORDER OF WORK (one feature at a time, your law)

1. R1 double-click launch (the window law is the blocker — kill it
   first).
2. R3 hook in motion (press where you point, posed press).
3. R2 game loop around the hook.
4. R4 five lessons.
5. R5 sound, R6 performance pass.
6. R7 package, R8 stranger test — then it is Steam-ready and the
   operator opens the account.

## STATUS LEDGER (updated as work lands)

| Date       | Event                                   |
|------------|-----------------------------------------|
| 2026-09-13 | Goal set by the operator; 8/8 R-items OPEN |
| 2026-09-13 | **R1 DOUBLE-CLICK LAUNCH: PASS** — R1a foreground independence (law retired, operator-verified) + R1b launcher (hidden console, payload auto-restore incl. the seal history, one double-click -> live creature, no console) |
| 2026-09-13 | R1a foreground independence PASS (law retired, operator-verified); R1b double-click package OPEN, in build |
| 2026-09-13 | R9 our-own-website channel added (demo first, sign-up after); revenue position re-framed — our page keeps ~95%, sign-up list is ours, Steam demoted to optional second shelf |

## LEDGER UPDATE (2026-09-13, R1)

- R1a FOREGROUND INDEPENDENCE: **PASS** — the recorded stall does not
  reproduce (frames 1.09 s minimized AND occluded, ticks advancing,
  picture answers poses; the operator independently interacted with
  the restored window with time advancing). The law of record was
  retired in THE_CELL_MODEL.md.
- R1b DOUBLE-CLICK PACKAGE: **OPEN** — the launch still needs its
  special working directory, hidden developer console, and manual
  payload re-posts. In build now.

## RUN RECORD (2026-09-13, R1 — the double-click launch)

- R1b PASS: the launcher `launch_chimera.bat` (deployed next to the
  exe by the build) starts the game in its own working directory with
  `--hidden` (the developer console retires; the studio overlay and
  HTTP remain). One double-click on a fresh kill: window up at
  299 fps, NO console, and the creature restored AS ITSELF — mesh,
  classification, travel bindings, measured pins, and the whole
  mitosis tree (4 cells, exact volumes) from the session snapshot.
  Zero hand-run scripts. Verified behaviorally: a knee pose changes
  the picture with no payload posted after boot.
- The mechanism: /tick_classify, /tick_vertbind, /tick_joints now
  write THROUGH to session_snapshot/<endpoint>.blob on success;
  /tick_seal APPENDS to tick_seal_history.log (the cell tree is a
  history, replayed in order); boot restore replays the shared list
  in dependency order (mesh -> pins -> classify -> bindings -> other
  uploads -> seals). /session clear wipes the history too.
- Honesty note: the .bat launcher may flash a console frame for
  ~100 ms before the engine hides it; the polished no-flash launcher
  belongs to R7 packaging.

R1 DOUBLE-CLICK LAUNCH: **PASS** (R1a foreground independence +
R1b package; the ONLY remaining caveat is the cosmetic bat flash).
