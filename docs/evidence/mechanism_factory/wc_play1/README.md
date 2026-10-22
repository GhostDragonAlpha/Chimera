# WC-PLAY-1 — Matter workshop: double-click launch + player-key save/load

Milestone increment GAME_PLAN_ACTION_RPG.md §5.1 "Matter workshop" (WC-PLAY-1):
the workshop boots from a double click (`launch_chimera.bat` now passes
`--interactive --scene <exe-dir>/workshop1_scene.json`) and the player's
invention saves/restores on **F9/F10** — no terminal commands anywhere.

## What was proven (walkthrough run 9, VERDICT PASS, 26/26 asserts)

All through REAL Win32 window messages (PostMessageW mouse + keys), HTTP
read-only (`/tick_b2_state`, `/tick_b2_interactive`, `/tick_b2_pick`,
`/glass`, `/log`); no POST mutates the scene:

1. `chimera_engine.exe <port> --hidden --interactive --scene workshop1_scene.json`
   boots `/tick_b2_state` **active** with exactly `hazard_pad` + `kit_pallet`
   — no HTTP admit. Refusals are player-visible: a malformed `--scene` doc
   boots empty and the named reason lands in `/log` (kind `scene`), which the
   board feed reads — stderr is retired under `--hidden`.
2. Tab → `place_2`, hover the pad, Enter → pillar settles upright
   (attempt 1); Tab → `place_4`, hover the pillar top, Enter → crate;
   board flips **HELD** (green chip, screenshot `3-crate-HELD.png`).
3. **F9** wrote `workshop_save.json` + logged `saved 4 parts to
   workshop_save.json`; X-wipe → board **LOST** "place a crate";
   **F10** logged `loaded 4 parts from workshop_save.json`, the 4-part
   invention returned, board **HELD** again. The keys really execute.
4. Failure beat: off-centre crate at the pillar's edge pixel topples
   (up_y −0.027) → board **LOST** with the challenge-1 ACTION line.
5. Regression battery at the same exe: `python -m pytest
   tools/construction_packet -q` → **88 passed** (the WC-INTERACT-2 bar).

## Settle blocker: root cause (run 8 receipt, closed)

Run 8's "pillar never settled within 120 s" receipt claimed a stale pick
surface (pick y = 0.0300 vs "live sunk top 0.0268"). The discriminator probe
(`probe_flip.py`, `probe_flip.log`, `probe_flip2.log`, `probe_flip_trace.json`)
refutes that: **the pick and commit are live and correct** — pick top-face
hits track the live pad pose, and a centred anchor settles in <1 s
(up_y 1, speed 0, 4 pair contacts). The 0.0268 in the receipt is the
post-commit pad state, not a stale pick.

True cause (the "anchor aim" branch): run 8's over-zoomed scan retry served
a sparse hit set whose best top-face pixel sat 36 mm off-centre in z; the
120 mm pillar spawned with a 16 mm bottom-face overhang, wedged into a lean
against the pad, and crept at sub-gate speed (8e-5 m/s, constant for 120 s).
Probe evidence: a forced near-edge anchor either falls upright to rest
(clean overhang) or wedges into the lean-creep class (reproduced: up_y
0.9807, pp contact 1, ~5.9e-5 m/s for 30 s+).

Fixes shipped:
- Harness aim (`walk_player_arc.py`): deterministic camera recovery on a
  missed scan (Ctrl zoom-out to the default radius, then the proven 1.1 s
  zoom-in; the old per-attempt zoom-in only deepened an over-zoomed camera)
  and a **fitting-anchor aim gate** — the pillar (and preferably the crate)
  commits only on a top-face pixel whose world x/z puts the kit part's WHOLE
  bottom face inside the support's top footprint (B9 base-band margin).
  The strict settle predicates are untouched.
- Engine `part_k_total` (b2_scene.cpp): the support's total rung stiffness
  now uses the B9-measured base-vertex count (`n_sites`, cached in
  `parse_part_`) instead of a hardcoded 4.0 — silently wrong for non-box
  supports. Boxes (the whole workshop kit) are unchanged: 4 sites.

## Residual engine finding (flagged, NOT changed here)

The lean-creep class is real: the pp contact's sticking regime is a
**linear viscous damper** (capped; regularized-Coulomb by design) and the
ground rung has **no tangential friction**, so a persistent mN-level lateral
drive (a part leaning on a support edge) slips at ~0.03-0.09 mm/s forever
instead of statically sticking. Players who place parts half-off a support
see a slow endless slide in some wedge configurations. Bounded proposal:
ground-run Coulomb friction (or static-stick in the pp sticking regime).
Not done here: it changes tangential dynamics everywhere and needs the
88-test battery re-derived; the arc gates green without it.

## Caveats

- **`workshop_save.json` lands in the engine's CWD** — for the double-click
  launch that is the directory next to the exe (`cd /d "%~dp0"` in the bat);
  for walkthrough runs it is the run's `native/` dir. Acceptable for this
  milestone (stated per the task); a per-invention named save dialog is
  deferred.
- F10 restores the FULL last save (all 4 parts incl. the two boot parts),
  not a delta — fine for this increment.

## Deferred (stays with workshop_challenge1/2)

Two-demonstrated-solutions and the transfer beat (saved recipe into a fresh
world; varied load naming the failure; one-edit recovery).

## Files

- `walk_player_arc.py` — the walkthrough (copy of `.tmp/wc_play1_walk/`
  at the green run; run from repo root:
  `C:/Python314/python.exe .tmp/wc_play1_walk/walk_player_arc.py`)
- `results.json`, `walk_run9.log` — run 9 receipts (exe sha256 ce032e9dfe0ccf01...)
- `1..6-*.png` — /glass screenshots (sha256-verified against results.json)
- `probe_flip.py`, `probe_flip{,2}.log`, `probe_flip_trace.json` — the
  root-cause discriminator (live pick, centred-vs-off-centre commits)
- `run8_wait_settled_trace.json` — the original failure receipt
