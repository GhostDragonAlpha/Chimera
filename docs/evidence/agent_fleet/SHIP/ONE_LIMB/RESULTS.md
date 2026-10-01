# ONE LIMB — MEASURED RESULTS (physics half, AN2)

Everything measured before the build window is on the CURRENT binary
(scratch engines only; the code written this lane is desk-checked, NOT
compiled — the lead owns the build window, see WINDOW10.md).

## 1. The segment derivation (prereg P1 — PASS)

`derive_limb.py` over the engine's own snapshot blobs (mesh_bin,
tick_vertbind, tick_joints — 18,459 verts, 36,630 tris, 28 pins):

| quantity | value |
|---|---|
| derived chain | hip_L(13) → knee_L(15) → ankle_L(17) — exact match to the pinned chain |
| crossing mesh edges hip–knee | 112 (adjacent, 1% floor rule) |
| crossing mesh edges knee–ankle | 100 (adjacent) |
| crossing mesh edges hip–ankle | **0** |
| verdict | **P1 PASS** — the chain is derived from CONNECTIVITY, not names, bands, or nearest-pin |

Seed-vs-wall populations (P2/P3 — the 90% bar was **FALSIFIED**, see the
PREREG addendum): hip-dominant 243/243 = 100% thigh-side; knee-dominant
108/256 = 42% shin-side (the knee joint saddle splits 148/108 — the
binding is a smooth blend and no plane can match it); ankle-dominant
1287/1477 = 87% foot-side. Agreement is REPORTED DATA in the engine's
partition report; the pass bars are P1 + M2's physical invariants.

## 2. The partition design (executes at the build window)

`POST /tick_limb {"side":"L"}` on the new code: split the thigh/calf/feet
band cells per connected component, take the side's components by rest
centroid sign (x ≥ 0 = L, the house law measured from the pins), merge
the three into ONE leg cell (interior band walls removed — both windings,
the divergence-cancelling pairs), then TWO OBLIQUE walls through the
joint pins: knee plane normal (knee−hip)/|·| = (0.200, −0.977, −0.085),
ankle plane normal (0.014, −0.998, 0.053)... (the engine computes them
from the live pins; the derivation table records the geometry). Each
wall is the welded cross-section — ONE physical septum, opposite winding
per neighbor's volume sum. The hip wall (one winding here, one in the
torso cell) stays the single septum to the torso. Ownership is fixed at
build: piece lists are immutable afterwards; nothing reclassifies per
frame.

Predicted daughters from the wall sides (measured vertex populations):
thigh ≈ 391 seed-verts, shin ≈ 298, foot ≈ 1287. Expected volumes:
thigh+shin+foot ≈ 0.693 + 0.335 + 0.288 = 1.316 m³ of the current bands
(actual daughters split at the oblique planes will differ slightly — the
report carries the numbers).

## 3. The causal demo — MEASURED on the current binary
(`demo_nerve_cut_scratch8172.json`, fresh scratch, port 8172)

The existing C1 nerve (pressure→intent) is the coarse sensory path; the
patch layer this lane adds gives the same cut per-path with location,
filter, saturation, and finite delay. Demo A disconnects the path;
Demo B is isolation by controlled boundary loading.

| bar | connected case | path-cut case | verdict |
|---|---|---|---|
| flinch envelope (ACTIVE contribution) | 0.993, fired 14.8 ms after the touch POST (poll dt 12 ms; the detector runs at the 3.34 ms tick) | **exactly 0** | **A fires / A silent when cut: PASS** |
| pressed-cell pressure (PASSIVE) | 35.94 MPa max | 34.77 MPa max — **the passive response remains** | **PASS** |
| skin dimple (PASSIVE) | 0.397887 m | 0.397887 m — bit-identical | **PASS** |
| active delta on the pressed cell | — | 1.165 MPa = the reflex's own mechanical back-coupling, gone with the cut | measured |
| reflex-mediated REMOTE response (foot cell) | 4.36 MPa | **exactly 0** | the causal signature: the remote load path dies with the sensory path |
| reconnect, no stimulus | — | env stays exactly 0 (no synthesized spike; prereg P10) | **PASS** |
| IDs + timestamps | touch → `ts_us`/`ticks` → env fire (`reflex_flinch_last_tick`, pin id 17) → pressure (`cells[i].P`) — one clock, one ID space | | **PASS** (acceptance 9) |

Demo B — isolation by controlled boundary loading (the open-wound
transfer is NOT implemented; this is the honest substitute, prereg G-1):
pressing inside the foot cell at 20 kN drives the foot cell to
**8.16 MPa** while the torso, thigh, and calf cells hold **exactly
0 Pa** — no unintended exchange across the intact septum (acceptance 3);
volume books balanced throughout (conserve_pct −0.000117%).

## 4. What the current binary could NOT demonstrate

- The partition itself (new code) — desk-checked + window procedure.
- Per-patch cuts with finite delay (new code) — the nerve cut is its
  coarse ancestor; the demo above is the same causal pattern.
- Actuator obstruction with reaction loads — **not demonstrated because
  it does not exist**: the actuators are kinematic pose writes (see
  STALE.md F-2). Obstruction of a pose servo reduces to the existing
  pin-ownership law; reaction loads need an actuator force state.
- Puncture/open-wound isolation with fluid transfer — not implemented
  (prereg G-1); the boundary-loading demo is the named substitute and
  two auto-sealed daughters are never called leakage.

## 5. Mass conservation

Measured on the current tree: sum of cell volumes = V_whole to
−0.000117% (live) and −0.000117282% under the 8.16 MPa foot load. Mass
inventory: 13.8246 m³ × 1000 kg/m³ = 13,824.6 kg against the
13,824.5 kg constant (1e-5 relative). The partition preserves this by
construction (divergence over shared welded geometry; the validation
gates re-measure it at the window; prereg P4).
