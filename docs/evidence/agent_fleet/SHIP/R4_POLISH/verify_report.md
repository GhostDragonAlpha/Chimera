# R4-polish — E2 seam tint fix, live verification

Agent: R4-polish (fleet 3) · Engine: 127.0.0.1:8107 (live, untouched) · 2026-09-13
Branch: `astra/tasks/matter-kernel-format-01` · Camera: `knee_close` (saved + recalled, v=[2.0, 1.35, 0.15, 0.483, 1.903, -0.0155, 0, 0])

## What was tested

The E2 seam fix: the per-cell linear press-tint write was replaced with a
per-vertex-averaged saturating load. Prediction: the boundary ring around a pressed
joint reads as a soft gradient, not a hard band. Frames (2560x1369 PNG):

1. `knee_posed.png` — `/tick_pose` joint 13 = 20 deg (hip), joint 15 = 45 deg (knee), 1.5 s settle.
2. `knee_pressed.png` — `/tick_intent` joint 15, force_n = 30000, 1.5 s settle (pose still held).
3. `knee_rest.png` — `/tick_touch_clear` + joint 15 back to 0 deg, 2 s settle.

## Numbers

**1. Deformation at the knee (posed vs rest, PIL/numpy abs diff, knee region = knee-cell patch x[1154,1377] y[596,793]):**

- mean diff **16.25 / 255** (gate: > 5) — PASS
- max pixel diff 112.3 / 255; full change bbox x[1026,1346] y[456,1258], 52,279 px above threshold
- visually: the leg bends 45 deg at the knee, deformation field (`pose_stretch.png`) is smooth across the limb

**2. Press tint visibility (pressed vs posed — isolates the tint from the held pose):**

- max pixel diff **15.7 / 255**; 1,291 px above 5/255; tint bbox x[1194,1337] y[636,753], centroid (1270, 703)
- localized exactly at the knee cells; nothing elsewhere changed (global mean 0.005)

**3. Gradient vs hard band (radial profile of tint-only diff from tint centroid, 5 px bins):**

- profile rises 0.30 → 1.30 (peak at r≈32 px), then decays 1.12 → 0.89 → 0.72 → 0.77 → 0.94 → 0.89 → 0.52 → 0.23 → **0.05 by r≈87 px**
- max adjacent-bin drop on the outer falloff: **0.36 / 255 = 28 % of peak** spread over ~20-30 px — a hard band would cliff ~100 % of peak to zero in one bin
- the stretched tint map (`tint_stretch.png`) is an airbrushed blob with soft edges, no ring cliff
- combined pressed-vs-rest field in the same region: peak bin 63.9/255, max adjacent-bin drop 23 % of peak — same conclusion

## Verdict

**The shading fix is LIVE.** The press tint boundary is a soft saturating gradient:
visible (1,291 px over the 5/255 gate), localized to the knee cells, and decaying
smoothly over ~20-30 px with no band edge. The old per-cell linear write would have
produced a stepped plateau with a cliff at the cell boundary; that signature is gone
from the radial profile and from the stretched visualization.

**The seam reads as: polished shading over a prototype joint.** At 45 deg of knee
bend the tint and limb shading blend continuously across the former seam, but a
geometric crease/pinch is visible at the joint fold (see `knee_posed_crop.png`,
inner side of the bend). That crease is **not a shading artifact** — the tint
profile is clean exactly there, so no shader work will remove it. It is a vertex
binding defect: the skinning weights need regeneration (`vertbind`), which is a
mesh/bind-geometry fix, out of scope for a polish pass and documented here as the
binding defect.

Honest one-liner: tint seam = fixed and verified live; knee crease = binding
geometry, needs vertbind regeneration, shader cannot fix it.

## Evidence

All in `C:\Users\allen\Desktop\CHIMERA_PROOF\R4_POLISH\`:

- `knee_rest.png`, `knee_posed.png`, `knee_pressed.png` — full 2560x1369 frames, capture order per protocol
- `knee_rest_crop.png`, `knee_posed_crop.png`, `knee_pressed_crop.png` — 2x native-res knee close-ups
- `tint_stretch.png` — contrast-stretched tint-only diff (soft blob, no band)
- `pose_stretch.png` — contrast-stretched pose deformation diff
