# Workshop challenge 1 — keep the salvage load above the marked hazard

**Date:** 2026-10-18
**Driver:** `tools/construction_packet/workshop_challenge1.py` (run:
`python tools/construction_packet/workshop_challenge1.py run --out DIR --port N`;
`... compare RUN1 RUN2 --out comparison.json`)
**Runtime:** B-suite construction engine
`.tmp/body-engine/Release/chimera_engine.exe`,
sha256 `47bbf42a7437089264a9f830f832f7432dfc2deb48680330ce4478134b278406`
(the separate Oct-17 B-suite build the B4/B8 tests already use — not the
membrane-loop pinned exe).
**Runs:** `run1/` (port 8803), `run2/` (port 8804), `comparison.json`.
**Gate:** `docs/GAME_PLAN_ACTION_RPG.md` §5.1 workshop challenge + §13.1
worker handoff ("exercise the resulting action in the native scene").

## Player benefit

This is the first real *game decision* in the matter workshop: the player is
shown a marked hazard (the granite slab), a kit (two granite piers, a timber
deck, a granite pillar, a steel crate) and an objective law, and must build a
structure that keeps the crate above the hazard. The evidence shows the player
can genuinely do this two structurally different ways, can fail in a way the
game *names* with an actionable fix, can recover cheaply, and can save a
solution and restore it bit-exactly later.

## Objective law and falsifier (as shown on the Studio board)

- LAW: "the crate's COM stays inside the marked region with its bottom >= 4 mm
  above the slab top for the whole window; load path is admitted contact/weld
  physics only."
- FALSIFIER: "crate bottom <= slab top + 3 mm at settle, or COM out of region;
  rejected edits move the hash."
- Referee tools: `/tick_b2_place|weld|remove|save|restore` (B2 transactions).

## What the walkthrough demonstrated (both runs)

1. **Failure with named feedback.** Crate placed off-centre on the pillar
   topples. Predicate `attempt1`: **FAIL**, clearance 19.1 mm, tipped, COM out
   of region. The board verdict names it and the fix: "LOST SUPPORT: the crate
   TIPPED off its support (clearance 19 mm). ACTION: remove the crate and
   centre it over its support before loading." (`3-failure-glass.png` shows
   the WS3 chip red with LAW/FALSIFIER/VERDICT/REFEREE TOOL/ARTIFACT.)
2. **Cheap recovery.** Remove + re-centre the crate, then continue — no
   scene restart needed; the run proceeds into solution B.
3. **Solution B — contact tower** (`4-solB-*`): granite pillar on the slab,
   crate centred, **no connectors**. Settle passes: clearance 79.882 mm
   constant over the 8-sample window, total reaction **115.03 N**, weld list
   empty. Load path is pure contact.
4. **Solution A — welded span** (`5a`–`6-solA-*`): two piers flank the
   hazard, timber deck rests on the pier tops with live weld connectors,
   crate yawed 90°. Settle passes: clearance ~304.8 mm, total reaction
   **393.60 N**, weld forces 20.25 N / 19.39 N at k = 20 000 N/m. A mid-run
   revision (B4 connection-improvement pattern: re-weld both connectors 20×
   stiffer, same anchors) cut deck sag from 10.7 mm to 1.0 mm — the player's
   edit measurably improved the structure, and the board verdict reads
   "HELD: crate 305 mm above the hazard; sag 1.0 mm after the stiff re-weld
   (was 10.7 mm). SOLUTION A accepted." (`6-solA-glass.png`, green chip.)
5. **§6 gate — two solutions produce different measured histories:**
   `gate_two_solutions_different: true`. Contact-only 115.0 N / no welds vs
   welded span 393.6 N / two ~20 N welds, 79.9 mm vs 304.8 mm clearance.
6. **Save/restore across sessions:** each solution saved via
   `/tick_b2_save`; after clear + `/tick_b2_restore`,
   `restore_bit_exact: true` in both runs. Saved documents:
   `save_solution_A.json`, `save_solution_B.json` (sha256 in receipts).
7. **Rejected edits move the hash / refused edits don't:** refusal probes
   (`place mass_kg=-1` → "refused: place.mass_kg: must be positive";
   `patch` unknown part → "refused: patch: no part with id 'nope'") both
   refused **with hash unchanged**; the falsifier's rejected-edit clause is
   exercised by the same hash machinery.
8. **Inspector scoping:** `/tick_b2_inspect crate` answered; detailed
   reactions stay in the inspector (`failure_inspect` in receipt).

## Determinism (two independent runs, honestly scoped)

- Analytic (unadvanced, rest-pose) states: **byte-identical modulo the step
  counter** (`analytic_states_byte_identical_modulo_steps: true`); all six
  analytic states within band, 0 violations.
- Settled save documents: both solutions within the jitter band
  (`settled_save_docs` 0 violations each) — granite yaw jitter ~0.5 deg is
  documented B3 behaviour.
- Frame shots: 8 of 11 byte-identical between runs, including **all three
  Studio-board glass shots**; the 3 differing shots
  (`3-failure-topple`, `6-solA-terminal`, `7-restored`) are settled-physics
  frames inside the documented jitter band.

## Measured cost

- Frame time (39 samples): mean of per-run averages **1.142 ms**, worst
  average 10.13 ms, single-frame max 71.31 ms (first frame, shader warm-up).
- Clock: 4133 ticks, sim/wall ratio 1.0, 0 catch-up clamps, 2 slow ticks,
  max gap 4.16 ms.
- Memory: RSS 168.7 MB at scene → **200.0 MB peak** at solution A.
- Routes used: 16 (B2 transaction API + `/studio`, `/cameras`, `/ui_click`).

## Preregistration disclosure (deviation)

The design (objective law, falsifier, predicate thresholds, shot list,
comparison bands) was frozen in the driver script before either run, and the
driver is committed with this evidence — but there is **no separate
UTC-stamped preregistration JSON** as the membrane-loop increments used.
Disclosed deviation from the house pattern; the script text is the frozen
artifact and both runs postdate it.

## Process record

- Maya authored the 953-line driver and the `cradle_recipe.py` extraction but
  timed out twice (~5 h each) before executing the final capture. The lead
  ran her complete driver directly instead of re-dispatching (process
  improvement: execution of a finished driver does not need an agent).
- First captures showed no board overlay: the engine resolves `argv[2]`
  against **its** cwd (`native/`), so a relative `--out` produced a board path
  the engine never found. Fixed with `self.out.resolve()`
  (workshop_challenge1.py:512); both runs and the comparison were re-captured
  with the board visible (glass shots above).
- `test_b4_assembly.py` now imports the extracted `cradle_recipe.py`
  (−42/+4); the acceptance suite re-ran green after extraction:
  **Ran 6 tests in 26.160 s — OK**.

## Verdict against §5.1

This satisfies the §5.1 workshop slice **minus transfer**: a build→test→
feedback→failure/named-recovery→save→restore loop with two structurally
different, measured solutions in the native scene, readable Studio feedback,
and honest determinism scoping. **Not yet shown:** saved-recipe *transfer*
(load a saved solution into a fresh world and reuse it under a varied
constraint) — that is workshop challenge 2. Human playability remains
unobserved: this is a scripted walkthrough, engineering evidence that the
mechanics work, not that a human enjoys them.
