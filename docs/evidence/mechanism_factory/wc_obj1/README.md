# WC-OBJ-1 part A — revised objective (corner clearance + step-gated window) — board feed

Increment: `docs/GAME_PLAN_ACTION_RPG.md` §5.1 gap table lines 573-594
("the on-screen promise must match the implemented rule"), PART A: the
player-visible HELD/LOST board feed plus these two receipts. Python-only;
no engine edits, no rebuild. The only changed source file is
`tools/construction_packet/workshop_board_feed.py` (still GET-only: it never
POSTs to the engine — the receipt script below owns the scene admits/placements
and the weld, exactly like the workshop challenge drivers own theirs).

## What changed in the board feed

1. CORNER clearance (was: axis-aligned bottom `COM y - half-height`).
   The feed now rotates the crate's 8 COM-relative corners
   (`--crate-half-extents-m`, default kit 0.05 x 0.025 x 0.025 m) by the
   crate's live `pose_q_wxyz` and requires every corner whose world x/z
   projects inside the pad-top footprint (`--pad-footprint`, default
   x 0.48..0.76, z -0.08..+0.08 m) to sit >= `--min-clearance-m` (4 mm)
   above the live slab top. Corners projecting outside the footprint do not
   count (declared footprint-projection rule). This closes the honesty gap:
   worst corner drop below the axis-aligned bottom is `0.05*sin(tilt)`, so a
   ~4.6 deg+ tilt could rest a corner ON the pad while the old rule read HELD.
2. TILT gate demoted. The up-axis clause is no longer part of HELD (mild
   tilts are legal per the plan). Tip detection (`up_y < 0.9848`) survives
   ONLY to word the LOST reason/ACTION: tipped -> "the crate TIPPED off its
   support"; non-tipped clearance failure -> "a crate corner rests on the
   hazard slab (...)" — both carry challenge 1's ACTION line "remove the
   crate and centre it over its support" (the walk harness asserts that
   substring; it is unchanged and reachable).
3. PHYSICAL-TIME freshness. The feed reads `steps` and `paused` from
   `/tick_b2_state` each poll. HELD only at the newest physical sample:
   steps advanced since the previous poll AND not paused. Paused or
   delta-steps==0 -> a distinct amber PAUSED/STALE chip (not HELD, not a
   physics LOST; a measured failure keeps its LOST wording while frozen).
   delta-steps < 0 (re-admit clock reset) restarts freshness tracking.
   Note: the pause route body is `{"on": true|false}` (engine main.cpp
   ~212-219), not `{"paused": ...}`.
4. LAW text reworded to state exactly what is enforced (verbatim):

   "objective law, measured at the newest physical sample: HELD only while the engine's step counter advances (paused or step-stalled polls show a stale chip, not a ruling); the newest crate's COM is inside the marked region x 0.54..0.70 m, -0.05..+0.05 m, and every corner of the crate box (50 x 25 x 25 mm half-extents about the COM, rotated by the crate's live pose) whose x/z projects inside the pad-top footprint x 0.48..0.76 m, z -0.08..+0.08 m sits >= 4 mm above the live slab top (corners projecting outside the footprint do not count; mild tilt is legal); supports may stand on the pad — only the crate's own corners are judged here, until gap row 4 decides otherwise; the load path is the admitted contact physics only"

## Receipts

`wc_obj1_replay.py` drives the engine at
`.tmp/body-engine/Release/chimera_engine.exe` (already built):
`chimera_engine.exe <port> --hidden --interactive --scene <repo>/tools/construction_packet/workshop1_scene.json`

### Receipt 1 — TILTED-CORNER replay (PASS)

Files: `tilt_admit_doc.json`, `tilt_weld_doc.json`, `tilt_state.json`
(live snapshot + old/new comparison), `tilt_board.json` (the feed's board).

Scene: the workshop pad, plus a crate rotated ~8 deg about z, its lowest
corners ON the live pad top, WELDed to the pad (`/tick_b2_weld`, k=400000,
c_damp=450, 4 anchor pairs at the crate's bottom-face corners). The weld is
the board's own "F weld" player tool; a free tilted box rights itself and the
soft part-pair contact sinks a resting crate ~5.8 mm into the pad, so only a
weld holds a tilted corner-on-hazard rest (measured; see limitations).

Settled measured state (steps 25196, diverged false):
- pose tilt 7.99 deg (qz 0.0698), COM (0.620, 0.0576, 0.000) — inside the region.
- OLD rule (computed from the same snapshot): axis-aligned bottom
  6.67 mm above the live slab top, up_y 0.99026 (inside the old 10 deg
  tipped band) -> OLD RULE READS **HELD**.
- NEW rule: all 8 corners project inside the pad footprint; worst corner
  -0.05 mm (resting on the slab) -> **LOST**.
- Board cell: "LOST: a crate corner rests on the hazard slab (worst
  in-footprint corner -0 mm above the slab top, below the 4 mm band).
  ACTION: remove the crate and centre it over its support." status blocked.

### Receipt 2 — PAUSE replay (PASS)

Files: `pause_scene_receipt.json` (build measurements + live state),
`pause_board.json`, `pause_poll_log.json` (steps/paused/chip per poll).

Scene built with the engine's own pair-equilibrium spawn law
(`y0 = support_top - w/pair_kt`, pre-sunk): pillar placed onto the settled
pad (pre-sink 8.9 mm), crate placed onto the live pillar top (pre-sink
6.7 mm). Result: crate HELD, worst in-footprint corner 80 mm above the slab.

Poll log (interval 0.7 s; steps per poll prove the verdict tracks the
physical clock):
- pre-0/pre-1/pre-2: steps 28045/30991/33914, paused false -> **HELD** (green).
- POST /tick_b2_pause {"on": true}
- paused-0/1/2: steps FROZEN at 33927, paused true -> **PAUSED** (amber),
  "no fresh sample to rule HELD" — not HELD, not a physics LOST.
- POST {"on": false}
- resumed-0/1/2: steps 36858/39788/42721 advancing -> **HELD** re-asserted.

## How to re-run

1. Launch the engine (background):
   `D:/Chimera-Maintenance/PythonChimera/.tmp/body-engine/Release/chimera_engine.exe 8845 --hidden --interactive --scene D:/Chimera-Maintenance/PythonChimera/tools/construction_packet/workshop1_scene.json`
2. `python wc_obj1_replay.py tilt  --port 8845 --tilt-deg 8`
3. `python wc_obj1_replay.py pause --port 8845 --interval 0.7`
   (pause mode rebuilds its scene; tilt mode rebuilds its scene)
4. Re-run the feed by hand against any scene:
   `python tools/construction_packet/workshop_board_feed.py --port 8845 --board ABS\\board.json`

## Declared limitations

- Kit-constant half-extents: the corner box uses `--crate-half-extents-m`
  (default the kit crate 0.05 x 0.025 x 0.025 m). A differently authored
  crate needs the flag (the feed reads only `com_m` + `pose_q_wxyz`).
- Footprint-projection rule: corners are judged by world x/z against the
  pad-top footprint window; a corner above the pad but outside the window
  (e.g. past the pad edge) does not count. This is declared in the LAW.
- Supports-on-pad legality: supports (pillar, pallet) standing on the pad
  are not judged; only the crate's own corners are. Gap row 4 owns that.
- The tilted fixture needs a weld: with this engine's soft pair contact a
  free tilted box cannot rest corner-on-pad (it rights itself; the pair
  equilibrium sinks any pad-resting crate ~5.8 mm). The weld is a real
  player tool, so the fixture is a legitimate player construction.
- Old-rule margin: the old rule's HELD in receipt 1 sits 1.6-2.3 mm above
  its 4 mm band (weld/contact equilibrium varies slightly run to run; the
  engine is not step-deterministic across processes). The revised rule's
  LOST margin is unambiguous (corner at/below the slab top).
- Sub-mm rests print rounded ("-0 mm") in the cell; the band clause carries
  the meaning.
- Freshness warm-up: the first poll after the feed starts is never HELD
  (no previous sample to compare steps against) — it shows the STALE chip
  for one interval. After a re-admit (delta-steps < 0) tracking restarts
  the same way.
