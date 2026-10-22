# WC-OBJ-1 part B — the scripted evaluator matches the on-screen promise

Extends part A. Changed source files (no engine edits, no rebuild, no
commits): `tools/construction_packet/workshop_challenge1.py` (check/measure/
board law), the harness WORKING COPY `.tmp/wc_play1_walk/walk_player_arc.py`
(one assert), and these receipts. The committed copies under
`docs/evidence/mechanism_factory/wc_play1/` and `.../workshop_challenge1|2/`
are untouched, and `workshop_challenge2.py` is untouched: **challenge 2
inherits check/measure via Run2 (it imports workshop_challenge1), so these
receipts cover both challenges.**

## 1. measure() — the continuity window is declared in STEPS

The exact window rule (verbatim from the code):

  WINDOW_STEPS = 20000   # declared continuity window in ENGINE SUBSTEPS:
                         # 20000 x dt_substep_s 0.00025 (verified from
                         # /tick_b2_state) = 5 s physical. Judged by the
                         # step span first->last row, never wall samples;
                         # a paused/starved engine accrues nothing, and a
                         # deadline hit first records INCOMPLETE.

with HISTORY_S = 8.0 as the wall DEADLINE (was 5.0 total window). measure()
records per row `steps` and `paused`; the window is the LATEST-starting
trailing run of rows whose first->last step span reaches WINDOW_STEPS; when
the span cannot reach WINDOW_STEPS inside the wall deadline the receipt row
records `"incomplete": true, "passed": false` — never a physics pass. Each
row carries `dt_substep_s` (verified 0.00025 in the receipt run) and
`paused`, so a frozen stretch is visible in the evidence.

## 2. check() — the corner rule, single source of truth

check() now calls `workshop_board_feed.corner_clearance` (imported — no
cycle, no CLI coupling): the crate's 8 COM-relative corners (kit 0.05 x
0.025 x 0.025 m) rotated by the live `pose_q_wxyz`; every corner whose x/z
projects inside the pad-top footprint (PAD x0..x1, z0..z1 = the same window
the feed uses) must clear the live slab top by CLEAR_OK (4 mm). COM-in-region
kept; the tilt gate is dropped as a pass requirement and TILT_MIN_UP_Y
survives only to word the LOST reason ("the crate TIPPED off its support",
ACTION unchanged — the walk harness's asserted substring stays reachable).
`crate_bottom_m` stays in the rows (history continuity); `clearance_m` is
the worst in-footprint corner clearance — for upright crates it reproduces
the published numbers exactly (see receipt 2: 0.079882 m == challenge 2's
79.882 mm).

board() law text mirrors the feed's LAW wording (corner rule + footprint
projection + step-gated window + the honest supports-on-pad sentence), and
the falsifier now reads "a crate corner resting at/below the slab top at
settle (on the hazard) or COM out of the region".

## 3. Harness working copy

One deliberate assert update (line ~596): "upright" in law -> "corner" in
law, label "board feed states the corner law". Nothing else in the harness
changed (diffed against the committed copy).

## 4. Receipts (this directory)

- `partb_receipt.json` + `partb_run/` — the run receipt (label: part B;
  challenge 2 inherits check/measure via Run2 — no wc2 edit).
  - solution_B_stepwindow: **PASS** — pillar-on-pad tower (wc1's own
    analytic docs, edits paused on the analytic base), window judged by
    steps: span 20059 >= WINDOW_STEPS 20000 over 20 rows, settled clearance
    0.079882 m, and check() on the settled state: ok, in_region, corner
    clearance 0.079882 m (B2 regression).
  - window_paused_midwindow: **INCOMPLETE, not a pass** — the engine paused
    2 s into the measure and resumed at 6 s; 16 rows show paused=true with
    steps frozen at 43747; span 15909 < 20000 at the deadline.
  - window_short_deadline: **INCOMPLETE, not a pass** — HISTORY_S patched to
    0.6 s; span 2096 < 20000.
- Player-arc regression: `.tmp/wc_play1_walk/walk_obj1_partb.log` — 26
  asserts, VERDICT PASS, F9/F10 beats green ("board feed states the corner
  law" is the updated assert; "board verdict HELD after the build settles"
  now shows the corner-rule cell).
- pytest: `python -m pytest tools/construction_packet -q` -> **88 passed**.

## 5. Declared limitations

- The bench-UI toggle: the walk harness's slab-hover step is sensitive to a
  zoom race — in today's session the zoomed camera placed the aim pixel at
  (198, 469), inside the Studio editor's fixed left panel, and the engine's
  ui_.wants_mouse law (panels are not transparent to input) blocks POSTed
  hovers there (measured: the same aim pixel reproduced three times; the
  engine's posted-move hover proven working at viewport pixels, e.g.
  (384, 474) -> hovered hazard_pad). Yesterday's run 9 passed only because
  its camera zoom raced differently (7 pick hits vs 59) and the aim pixel
  fell in the viewport. The receipt run used `hide_studio_chrome.py` (this
  directory's neighbour in .tmp/wc_play1_walk): a companion that posts the
  Studio bar's own "[F1] hide" once the window exists. It touches no
  predicate, no board file, no engine state; the walk's asserts are
  HTTP/board-file-based and unaffected. Without the toggle the gate fails
  on bench geometry, not on the objective.
- WINDOW_STEPS=20000 needs ~5 s of unpaused sim inside the 8 s wall
  deadline; a heavily starved engine (sim_over_wall << 1) would record
  INCOMPLETE honestly rather than stretch the window.
- challenge 2's receipts inherit the step window via Run2 unchanged; its
  recorded clearances for upright crates are numerically identical to the
  old bottom metric (upright crate: every in-footprint corner sits at the
  same height).
