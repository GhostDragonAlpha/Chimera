# THE MUSCLE ATLAS — measured muscle parameters from published open models

> **STATEMENT (a theory, 2026-08-09):** every muscle the skeleton needs for
> the standing chain (ankle / knee / hip) plus the fetched arm subset can be
> parametrized from *published, license-clean, machine-readable* models —
> not from memory, not from a textbook table. The standing chain is fully
> covered by the canonical Rajagopal2016 model (80 MTUs); the full 3-D
> upper-extremity set is an **explicit gap** (registration-gated at
> simtk.org), not an estimate. The Arm26 planar model (6 elbow muscles)
> covers the elbow subset; everything beyond is named UNKNOWN.
>
> **PREDICTION (not yet measured):** the 80 Rajagopal2016 standing-chain
> muscles in `muscle_parameters.json` reproduce the earlier
> `rajagopal_extract.json` extraction (from Rajagopal2015.osim) field for
> field — because both are the same published parameter set.
>
> **FALSIFIER (named before the run):** any field in the 80 shared muscles
> differs from the Rajagopal2015 extraction by more than floating-point
> noise (> 1e-6). The cross-check ran on 2026-08-09: **80 tested, 0 field
> mismatches.** Prediction confirmed. The extraction is a faithful reading
> of the published model, twice independently.

---

## 0. THE SOURCES (all Apache-2.0, opensim-org/opensim-models, no registration)

| model | file | muscles | role | citation |
|---|---|---|---|---|
| **Rajagopal2016** | external/anatomy/Rajagopal2016.osim | 80 Millard2012EquilibriumMuscle | **primary** (standing chain) | Rajagopal, Dembia, DeMers, Delp, Hicks, Delp (2016). Full-Body Musculoskeletal Model for Muscle-Driven Simulation of Human Gait. IEEE TBME 63(10), 2068-2079. doi:10.1109/TBME.2016.2586891. Parameters from 21 cadaver specimens + 24 MRI subjects. |
| **gait2392** | external/anatomy/gait2392.osim | 92 Thelen2003Muscle | fallback | Delp et al. (1990) gait2392 lower-limb model; Thelen (2003) musculotendon dynamics. |
| **Arm26** | external/anatomy/Arm26.osim | 6 muscles (TRIlong/TRIlat/TRImed/BIClong/BICshort/BRA) | arm subset | OpenSim planar 2-DoF arm model. |

Fetched 2026-08-09 from raw.githubusercontent.com (opensim-org/opensim-models
master branch); sha256 checksums and the fetch procedure are in
`external/anatomy/FETCH_LOG.md`. The Rajagopal2016.osim copy is byte-identical
to the canonical GitHub raw file (3f5c5f23…).

### The gap, stated honestly

The Rajagopal2016 model's arm is **not** musculated: the torso is driven by
ideal torque actuators, and the upper limb carries no muscle-tendon units.
The canonical 3-D upper-extremity muscle models — **MoBL-ARMS** (Saul et al.
2015, 50 muscles per arm) and **Holzbaur 2005** (32 per arm) — are
registration-gated downloads at simtk.org. Per the falsifier, they are
listed as a gap with published citations, NOT substituted with estimates.
Arm coverage in this atlas is therefore exactly the Arm26 elbow subset (6
muscles) plus the Rajagopal2016 shoulder/elbow/wrist **joints** (which ARE
present, in the joint extract).

---

## 1. THE EXTRACTION (re-runnable, line-provenant)

`tools/extract_muscle_atlas.py` reads the three `.osim` files and writes:

- `external/anatomy/muscle_parameters.json` — 178 muscle records
  (Rajagopal2016 80 + gait2392 92 + Arm26 6), keyed `"<Model>:<name>"`.
- `external/anatomy/joint_definitions.json` — 37 joints across the three
  models + the kernel cross-check.

The extractor is a SAX parse (not regex) with an exact 1-based line number
per element, so **every extracted value carries a `line` pointer to the raw
file**. 178/178 muscle elements and 712/712 parameter fields carry a line.
Verification: read back `psoas_r` `max_isometric_force` line 8177 =
`<max_isometric_force>1426.79016393443</max_isometric_force>`.

The gait2392 and Arm26 `_fetch_*.osim` files are promoted to canonical names
idempotently by the script.

### Schema — muscle_parameters.json

Per-muscle record:

```jsonc
{
  "source_model": "Rajagopal2016",
  "name": "addbrev_r",
  "group": "hip_adductor",              // functional role, modeler's label
  "crosses_joints": ["hip_r"],          // derived from the body subtree
  "origin":   {"segment": "pelvis", "location_m": [-0.0191,-0.094,0.0154],
               "normalized": {"t": 0.077965, "p_offset_m": 0.05796, "length_m": 0.12368}},
  "insertion":{ "segment": "femur_r", "location_m": [-0.002,-0.118,0.0249],
               "normalized": {"t": 0.117846, "p_offset_m": 0.025697, "length_m": 0.408049}},
  "max_isometric_force_N":  {"value": 625.819672131148, "line": 5319},
  "optimal_fiber_length_m": {"value": 0.1031,          "line": 5321},
  "tendon_slack_length_m":  {"value": 0.035450291324676,"line": 5323},
  "pennation_angle_rad":    {"value": 0.11478092,      "line": 5325},
  "muscle_element_line": 5277
}
```

`normalized` origin/insertion: `t` = fraction along the body's measured
proximal→distal axis (0 = proximal end), `p_offset_m` = perpendicular
offset from that axis, `length_m` = the measured body axis length. This is
the skeleton-scalable form: a link's own frame length scales the attachment
without re-reading the source model.

### Schema — joint_definitions.json

Per-joint record: `name`, `atlas_class` (revolute / universal / spherical /
free, derived from the OpenSim joint element: 1 coordinate → revolute, 2 →
universal, 3 → spherical, ≥6 → free; CustomJoint by coordinate count,
PinJoint → revolute, UniversalJoint → universal), `parent`/`child` bodies
(offset-frame sockets resolved to their owning body), joint/child `location`
and `orientation`, the coordinate list (name, range, locked), and measured
`dof`. Plus `crosscheck_vs_lightengine` — see §3.

---

## 2. COVERAGE (counted from the JSON, not claimed)

| functional group | muscles |
|---|---|
| hip flexors | 20 |
| hip extensors | 28 |
| hip abductors | 24 |
| hip adductors | 28 |
| hip rotators | 8 |
| knee extensors | 12 |
| ankle plantarflexors | 32 |
| ankle dorsiflexors | 14 |
| torso extensors / flexors | 2 / 4 |
| elbow flexors / extensors | 3 / 3 |
| **total** | **178** |

All 178 classified (0 unclassified). Standing-chain DoF coverage: hip
(3-DoF spherical, both sides), knee (revolute), patellofemoral (revolute),
ankle + subtalar (revolute each), mtp (revolute) — all present in the
Rajagopal2016 extract with coordinates and ranges.

---

## 3. KERNEL CROSS-CHECK (atlas vs LightEngine skeleton spec)

`joint_definitions.json#crosscheck_vs_lightengine` is produced by reading
the kernel's own `build_spec()` topology and joint classes — not a hand
table. 18 standing-chain joints compared; 16 match; 2 genuine differences:

| joint | kernel | measured (Rajagopal2016) | verdict |
|---|---|---|---|
| hip_L / hip_R | spherical 3 | spherical 3 | MATCH |
| ankle_L / ankle_R | revolute 1 | revolute 1 (talocrural) | MATCH |
| mtp_L / mtp_R | revolute 1 | revolute 1 | MATCH |
| shoulder / elbow / wrist (both sides) | spherical 3 / revolute 1 / universal 2 | acromial spherical 3 / elbow revolute 1 / radius_hand universal 2 | MATCH |
| tibia_L / fibula_L / tibia_R / fibula_R | revolute 1 | walker_knee revolute 1 | MATCH |
| **patella_L / patella_R** | **saddle (universal) 2** | **patellofemoral revolute 1** | **DIFF** — the kernel models the patella as a 2-DoF saddle; the measured model as a 1-DoF revolute. Structural difference, recorded. |

Spine / ribs / sternum / ilium-posterior kernel-only joints have no
Rajagopal2016 counterpart at that granularity (the model lumps the spine
into a single `back` spherical 3-DoF joint) — marked N/A with the granularity
reason, not counted as mismatches.

---

## 4. VERDICTS ALREADY LANDED (why this lane exists)

The joint cross-check and this parameter file feed the existing
`docs/JOINT_ATLAS.md` kernel-diff verdicts. Key standing facts this lane
confirms or extends:

- **VERDICT 1/2 (2026-08-08):** the kernel's default mass distribution was a
  design-load scaffold, not anthropometry; the anatomic body (`mass_model=
  "deleva"`) is the measured one. Muscle parameters were NOT part of that
  scaffold — they come from the published Rajagopal model. This lane now
  makes those parameters provenance-tracked and re-runnable.
- **JOINT CLASSES MATCH (already stated in JOINT_ATLAS.md):** ball-cup =
  hip 3-DoF, hinge = knee/ankle/elbow, saddle = wrist. The measured extract
  confirms 1:1 (16/18; patella is the 2-DoF exception).
- **New, this lane:** the Rajagopal2016 muscle force/fiber/tendon/pennation
  parameters reproduce the Rajagopal2015 extraction field-for-field (the
  falsifier), and every value carries a line pointer to the Apache-2.0 raw
  file. A consumer of `muscle_parameters.json` can prove where any number
  came from without trusting this document.

## 5. NEXT STEPS (open, recorded)

1. Wire `muscle_parameters.json` as the `mass_model="deleva"` standing-chain
   muscle table (the ANATOMIC-MASS membrane's muscle half), replacing any
   in-kernel table with the provenant source.
2. Gap: MoBL-ARMS / Holzbaur upper-extremity muscle sets require simtk.org
   registration. If the operator supplies credentials or an approved mirror,
   extend the same extractor (both are OpenSim `.osim` format).
3. The patella 2-DoF (kernel) vs 1-DoF (measured) difference: verdict for
   THE HUMAN — which is the model the skeleton should carry?
