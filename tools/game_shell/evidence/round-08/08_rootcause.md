# Round-08 — knee bend leaves the foot planted: root cause + STOP at pin boundary

Date: 2026-10-10 · Worker: Tiel · Status: **diagnosed, fix proven offline, NOT
applied** (regeneration breaks the graph asset pin → explicit STOP condition
per assignment contract; decision returned to Qwen).

## Symptom (user-reported)

BEND THE KNEE lesson, knee_L → 40°: the foot stays at its standing position
while the shin rotates; the triangles bridging shin to foot stretch.

## Root cause (numerically proven, three independent measurements agree)

The shipped binding pack `Saved/meshes/monkey_joints.bin` (JNT3, pinned) binds
the foot soles to **`spine_lower` — the FK ROOT — with weight 1.000**, i.e.
rigidly to the world. Bending `knee_L` cannot move them.

Evidence chain (all reproducible from this folder):

1. **Pack parse** (`_pack_probe.py` → `08_pack_probe.txt`):
   - Zero unassigned verts (JNT3 decoder rejects `owner<0`,
     `joint_binding.hpp:91`) — the "j<0 stays at rest" theory from
     `joints.comp:146` does NOT apply to the game path.
   - LEFT foot region (y<0.16, x>0; `_L` is x>0 per the mirror law):
     599/740 verts owned by `spine_lower`, 141 by `knee_L`, **0 by `ankle_L`**.
   - Sole (y<0.12, x>0.2): 434/499 owned by `spine_lower` with **w mean =
     1.000 → follow share (1−w) = 0.000** (the generator's root-band law makes
     parentless bands fully rigid, `rig_factory_fit.py:509`).
   - The `ankle_L` band (121 verts) covers y∈[0.32, 1.27] — the shin ABOVE the
     ankle pivot (y=0.34). It never touches the foot.
2. **Pure-LBS simulation** of the game's exact CPU law
   (`joint_binding.hpp:118 pose_binding`, used by `membrane_tick.cpp:393`) at
   knee_L=40°: ankle band moves mean 0.860, shin 0.339, sole only 0.164
   (and that 0.164 is just the 65 knee_L-owned toe-top verts; the
   spine_lower-owned sole moves ~0).
3. **Live engine `/verts` before/after** a real `/tick_pose` knee_L=40
   (`_live_verts_probe.py` → `08_live_verts_probe.txt`): foot 0.2373/1.3290,
   shin 0.3389/0.6316 — **bit-identical to the simulation**. The live surface
   IS the pack LBS. Matter pass is OFF in the game (`/matter` GET:
   `on:false`), so the matter/ground-clamp theory is not involved at all.

### Why the pack is like this (generator mechanism)

`tools/rig_factory_fit.py`:

- `foot_tip_L` (line 241-245) is derived as "the 30 verts farthest from the
  ankle among verts closer to the ankle than the knee and within 1.0 of the
  ankle". The foot is shorter than 1.0, so that sphere-cap is populated by
  SHIN skin: reproduced `foot_tip_L = (0.496, 1.213, 0.026)` — up the shin,
  not the toe (a true toe would be y≈0.1, z>0.4).
- The terminal segment `seg(foot_tip_L, J['ankle_L'], 'ankle_L')` (line 282)
  therefore runs UP the shin. Sole verts sit 0.25–1.65 from it.
- The OWNERSHIP SHELLS law (lines 303-312): limb claims beyond
  `LIMB_CAP = 0.7` are rejected and fall to the nearest AXIAL segment →
  **434/499 sole verts rejected → `spine_lower`** (the only axial near the
  ground), then made fully rigid by the root-band law.

This is exactly the documented gap: `docs/THE_MEMBRANE_INVENTORY.md` item 1 —
"derive segments from skeleton connectivity, including any explicitly defined
terminal segments". The foot has no terminal segment; it gets absorbed into
the root.

## Why I STOPPED (pin boundary)

The narrow fix = extend the ankle_L terminal band in
`tools/rig_factory_fit.py` + regenerate `Saved/meshes/monkey_joints.bin`.
But that asset is **pinned by sha256** in
`tools/creature_graph/data/creature_graph.json`
(`req.creature_assembly.physical.contract.current_asset.binding_sha256 =
74b3ab04…`, verified matching the shipped file today), and the pin is enforced
on the game load path: `tools/science_funnel/creature_scene.py:21`
(`asset_pin_drift` refusal) and `:68` (`compiled_binding_drift`). Any
regenerated pack changes the hash → the scene refuses to load → the fix
requires **re-pinning the graph store**, which the assignment lists as a STOP
condition. I did not regenerate, did not re-pin, did not edit the generator.

## Proposed fix (validated offline, ready for Qwen)

Scratch proof (`_pack_probe.py` FIX PROOF section): re-binding the 1776
root-owned foot verts (both feet) to `ankle_L` (w=1, blend partner `knee_L`):

- knee_L=40° sole displacement: **0.164 → 1.447** (foot follows the shin;
  larger than the shin because the sole sweeps the long arc around the knee
  pivot — correct kinematics for a hanging foot).
- Shin displacement unchanged (0.339 → 0.339).
- Rest pose **bit-identical** to the mesh (all angles 0 → identity).

Generator change (NOT applied — for Qwen's decision), in
`tools/rig_factory_fit.py`:

1. Fix `foot_tip_L` (lines 241-245): pick the true toe — e.g. among verts
   below the ankle pivot (`y < J['ankle_L'][1]`) on the +x side, the one
   extremal in +z (the foot's forward direction), instead of the
   farthest-from-ankle sphere cap.
2. Exempt the terminal foot band from `LIMB_CAP` rejection (or raise the cap
   for the ankle→toe segment), so sole verts within the foot hull claim
   `ankle_L`; keep the axial fallback for everything else.
3. Regenerate `Saved/meshes/monkey_joints.bin`, re-pin `binding_sha256` in
   `tools/creature_graph/data/creature_graph.json`, run
   `tools/creature_graph/acceptance.py`, reload via `run_creature.ps1`.

Effort: ~1-2 h including re-pin + acceptance + re-verify. Risk: the sole
becomes rigid-at-ankle (w=1) — no ankle-crease fade on the foot; acceptable
for this lesson (the ankle joint is a separate band above), can be softened
later with the envelope law.

### WIDE alternatives (NOT recommended for this defect, NOT implemented)

- Energy-based sliding attachment U=½k‖Δx‖² or capsule τ=−∂U/∂θ
  (inventory items 3/5, `tools/finite_area_attachment/DERIVATION.md`):
  production physics work, engine integration, days of effort. The defect
  needs none of it — the kinematic chain is correct, the binding is wrong.
- Engine-side load-time re-bind (`joint_binding.hpp`/`membrane_tick.cpp`):
  engine source change = WIDE per contract; also violates "one owner of the
  binding asset" (the pack would silently differ from its pin).

## Diagnostics that were blocked (and why it doesn't matter)

- Weight-paint via `POST /joint {"select":…}` is refused while the membrane
  body is active: `{"ok":false,"error":"shared_body_owns_surface"}`
  (`main.cpp:731-737` ownership guard). The pack parse replaced it 1:1.
- `POST /matter` likewise blocked; GET shows `on:false` — matter pass is not
  in the game path. The game poses via CPU `pose_binding`, not `joints.comp`.

## Evidence files (this folder)

- `08_01_knee_40.png` — BEND THE KNEE passed at 40°, defect state (pre-fix).
  `08_01_knee_0.png` — same view at rest (foot reference position).
  `08_01_drive.txt` — pageErrors=0, pass_line visible.
- `08_pack_probe.txt` / `_pack_probe.py` — ownership + simulation + fix proof.
- `08_live_verts_probe.txt` / `_live_verts_probe.py` — live `/verts` matches
  simulation bit-for-bit; matter off; pose reset verified.
- `08_04_pressure_baseline.png` — wake-the-cell PASSED pre-fix, pageErrors=0.

## Regression state (pre-fix, current build)

- bend_the_knee at 40°: PASSED (pass_line visible), pageErrors=0.
- wake_the_cell press: PASSED, pageErrors=0.
- Engine left at rest pose (verified `/verts` returned to rest).

## Files touched

Only `tools/game_shell/evidence/round-08/` (this report + drivers + probes +
screenshots). No engine source, no generator, no pinned asset, no graph store,
no commits.
