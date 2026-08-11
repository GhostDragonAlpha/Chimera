# theLight — the record player matrix, first record

Out of theZero comes theHorizon (space) and theLight (the light era): N identical
points — mass 1, charge 1, no authored properties — under two forces.

**The master algorithm is one folded walk.** Every tick: one Barnes–Hut tree,
one walk, DRAW + RESISTANCE together. The modifier M lives inside the membranes:
M < 0 is the wall (contact, radiation), M = 0 is the bond shelf, M → 1 is the
far field (pure draw). There are not two passes.

**The record player matrix** (the operator's design language, 2026-08-06):
- the **record** — `theLight.record.npz`: the trajectory, sampled; pressed once
  by `press.py`, deterministic.
- the **needle** — `physics.emit(nums, t)`: story-time t (0..1) → (N, 28) splat
  buffer, M-field colours, straight into the Chimera GPU pipeline.
- the **deck** — the HTTP viewer (`ChimeraEngine/gallery.py`, `http://localhost:8765`).
- the **DJ** — the operator: scrub t, step, pause, orbit. Changing the states
  changes the outcome; that is the game.

**The scenario.** A pinned bond-shelf seed (32 grains, amber — the anvil) at the
origin; 1968 free grains on a jittered shell at r_rain (the rain), zero initial
velocity. The draw does the falling; the walls and bonds are what pack the rain
into a membrane body around the seed. The window is the shell's own free-fall
time, not a chosen duration.

**Theory (RULE 0)** — full statement, prediction and falsifiers live in
`physics.py`'s header and are printed by `press.py`. The short form: the rain
falls, M awakens only where grains touch, a bound settled membrane forms inside
the rain shell, and the fold agrees with the two-pass referee to 1e-4.

**Chain.** The print ladder of proven shapes (bone → muscle → tendon → joint →
sheet → skin → bladder → lever → leg) is the second act: one geometric shape,
built by chaining proven shapes, run through this same single folded walk.

**Read first:** `LightEngine/modifier.py` · `LightEngine/kernel.py` ·
`docs/THE_LIGHT_SEED.md` · `ChimeraEngine/render_modifier_demo.py` (the
faithfulness demonstration this record is the matter-side of).
