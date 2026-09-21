# Pulley Re-Derivation - the Two Falsified Muscle-Path Directions (2026-09-20 lane)

Branch: `agent/pulley-rederivation-20260920` (sparse clone of `osim-agent` @ `aede5de9`).
Deliverable: `tools/science_funnel/validation/pulley_rederivation_20260920/pulley_arms_derivation.json`
(schema `chimera.pulley_rederivation.v1`, sha256 `2a99cd2becaf4b0a8d4dda176cca23af05397906ba43dcd504c06a1b6c8f76d5`).
Receipt (Rule-0 pre-registration written BEFORE the first arm was computed, measured
section appended after): `tools/science_funnel/validation/pulley_rederivation_20260920/receipt.json`.

## The question

The muscle-path lane of 2026-09-18 (branch `lane/muscle-paths-20260918`, commit
`95794334`, a DIFFERENT lineage from this clone) falsified two hindlimb directions
because a straight-line proxy has no pulleys: **knee extension (ratio 0.00)** and
**MTP flexion (ratio 0.00)**. The Wiseman 2026 RSOS macaque model
(`tools/science_funnel/data/wiseman2026/models/Macaque_model.osim`, CC BY 4.0) ships
the wrap geometry. This lane re-derives both directions WITH the pulleys and checks
against the independent SI 2 moment-arm table (672 rows, 8 taxa x 36 muscles x 6 DOF).

## Machinery provenance

The 2026-09-18 derivation machinery lives on another lineage. Per the task contract,
the MINIMAL derivation was RE-IMPLEMENTED from that lane's documented method
(`docs/research/20260918_muscle_path_derivation.md` on `lane/muscle-paths-20260918`):
parse .osim path points + wrap references; exact tangent wrapping in the plane
perpendicular to the cylinder axis (Z of the wrap frame), quadrant rule, arcs <= pi,
endpoint-inside raises; moment arms twice (signed perpendicular distance from the
physical joint axis to the joint-spanning line of action, advisory; `-dL/dq` central
differences, step 1e-4 rad, authoritative). Extensions declared in the receipt:
sphere tangent-cone construction and an iterative ellipsoid tangent resolution (the
old lane left ellipsoid/torus contacts UNRESOLVED with bounds; FDL V wraps an
ellipsoid). Socket-driven FK works across all seven deposited taxa.

## What was measured (all numbers in the deliverable + receipt)

- **Independent parse vs acquisition prior**: 14 wrap objects = 9 WrapCylinder /
  3 WrapSphere / 2 WrapEllipsoid (inventory.json had `type: null`). DIVERGENCE from
  the mission-brief phrasing: the metatarsal and hallux cylinders exist on foot_r but
  NO muscle references them; FDL II-IV + FHL route over `R_Ankle_Cylinder`, FDL V over
  the distal-tibia ellipsoid, quads (+RF's second wrap) over the femoral condyle/neck
  cylinders. `rProxTibiaCylinder` (R_LG) and `rDistalAnkle_SphereforFDL` are
  `active=false`.
- **Knee extension** (R_RF/VI/VL/VMed over the SI-recorded ranges): arms
  +17.64..+25.05 mm, condyle cylinder engaged 2001/2001 samples on all four.
  The pulley IS the patella-substitute mechanism whose absence caused the 0.00 ratio.
- **MTP flexion** (R_FDL II-V, R_FHL over +-30 deg): arms -15.73..-0.21 mm; ankle
  cylinder engaged 2001/2001 on FDL II-IV; FHL's and FDL V's wraps are topologically
  zero-contribution for the mtp arm (their wrapped segments are ankle-rigid during an
  mtp scan; FHL crosses hallux_r, slaved 1:1 to mtp).
- **Determinism**: two full derivations byte-identical
  (`2a99cd2b...f76d5`). 17/17 lane tests green.
- **Signs**: extensors positive / flexors negative on every compared muscle, matching
  SI 2 under `r = -dL/dq`.

## The unit verdict and the standing divergence

The pre-registered unit membrane: SI 2 states no units; joint-range columns are
degrees (certain - they match the model's radian ranges); arm columns to be resolved
between mm and cm. Measured outcome:

- **mm hypothesis: FIRED** (every muscle off by a uniform factor 8.21-8.36).
- **cm hypothesis: HELD** inside the pre-registered band max(0.25 mm, 25 % |SI|) on
  all 9 muscles, both endpoints - the unique surviving raw reading.
- **Exact structure**: SI 2 macaque arm = deposited-geometry arm x **0.119754**
  (least-squares over the MTP class, spread 0.119728-0.119768 - four-decimal
  constancy on pure point geometry, i.e. a uniform model-scale residual). The same
  derivation on the Gorilla deposit gives k = 0.03290 and on Gibbon k = 0.10845:
  per-taxon constants, differing between taxa, undocumented in the deposit. Deposit
  segment lengths are taxon-sized (gorilla shank 405 mm, macaque 165 mm), so the
  deposits are NOT size-normalized templates; the divergence is in the SI-vs-deposit
  pair and is NOT resolvable from the deposit. Operator follow-up: authors'
  subject-specific scaling.

## What this unblocks

The 2026-09-18 bar ("knee extension and mtp flexion MUST NOT be used for force claims
until via-pulley paths are derived") is lifted at MECHANISM level: both directions now
have real, engaged pulleys and deterministic, sign-correct, non-zero arms whose
per-muscle shape the authors' independent pipeline reproduces (MTP class exact to four
decimal places after the scalar fit; knee class within 0.09 mm). The gait torque laws
may use the arm-vs-angle curves and relative magnitudes from the Wiseman geometry.
Absolute torque scales carry the k = 0.11975 caveat until the per-taxon scale is
resolved; absolute force claims additionally need the Guimaraes architecture numbers
admitted onto the Wiseman paths (separate admission).

## Replay

```bash
python -B tools/science_funnel/validation/pulley_rederivation_20260920/derive_pulley_arms.py
python -B -m unittest tools.science_funnel.validation.pulley_rederivation_20260920.test_pulley_rederivation
```
