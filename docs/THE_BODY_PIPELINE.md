# THE BODY PIPELINE — the workflow for slotting a body into the Chimera system

> Written 2026-08-29, operator decree: "a workflow system that uses the elements we
> need — MuJoCo, OpenSim, Isaac Lab, whatever — with repeatable steps, so we always
> know which step to take next."
>
> **THE STANDING RULE:** work the earliest stage whose gate is not green. Never skip
> a red gate forward. Every stage names its falsifier BEFORE it runs (Rule 0); a gate
> that fires is recorded, never moved.

---

## The pipeline at a glance

| Stage | Name | Law / method | Tool | Output artifact | Gate (falsifier) | Monkey status |
|---|---|---|---|---|---|---|
| **B0** | ACQUIRE | source mesh + per-asset license (the corpus law: dataset license ≠ asset license) | Objaverse / Sketchfab | `*_src.glb` + license row | no license, no build | DONE (5 corpus GLBs, teddy pending operator) |
| **B1** | REPAIR | watertight from the triangle level; true openings stay open by identity | chimera `tri_ca` birth rule | `*_birth.glb` | any true opening closed = rule can't tell wounds from features | DONE (sockets open) |
| **B2** | REGISTER | every triangle gets a center; centers hash into derived cubes; dual graph built; cube index ≡ dual neighborhood | chimera `tri_ca` registry | substrate + report | any neighbor missed by the cube ring | DONE (address law 100%) |
| **B3** | SKELETON | rod cage → collinear chains → joints (the skeleton is a graph, not a list of names) | chimera census | `skeleton/census.json` | any articulation with no census home | DONE (236 bones, 40 joints) |
| **B4** | FACTORY | per-joint center, axis (bilateral/central law), capsule-contact ROM | chimera factory | `skeleton/factory_rom.json` | F1 symmetry, F2 no-contact, F4 blind spot — recorded, never patched | DONE (19 joints) |
| **B5** | ANATOMY REFEREE | ligament/muscle ROM limits for the factory's blind spots (extension stops, ball joints); species-sane bands | **OpenSim** (+ Oku macaque) | `anatomy_limits.json` | limits contradicting a measured bone stop = the model's pose is wrong, not the bone | **NEXT** |
| **B6** | DYNAMICS REFEREE | MJCF skeleton from the factory; contact forces vs the substrate's λ; gait algorithm sandbox | **MuJoCo** | `*_mjcf.xml` + referee report | λ mismatch > the derived tolerance = our contact solve is wrong (not MuJoCo) | pending B5 |
| **B7** | ARTICULATE | generalized joints kernel (the SHOW) + volp-ARAP skin per joint | chimera engine (`joints.comp`, volp) | live articulation | any joint's skin tearing/spiking at mid-ROM | SHOW live; volp-generalization pending |
| **B8** | BEHAVE | CPG gait + real load feedback + footstep planning from measured contact (H16) | chimera CPG + substrate λ | the walk, the footstep choices | metamorphic rotate-world; energy no-pump; referee (B6) agreement | CPG walks (knees); full-skeleton + footsteps pending |
| **B9** | APPEAR | frost GT → B0 baseline → quantization → in-engine decode; eyes; water; fur | mitsuba GT + chimera frost | live relighting | bar = measured B0_occl; fixed-point budget ≤ X | DONE for the monkey (re-run per body) |
| **B10** | DYAD & SHIP | the operator's window is the last gate: NO COMPLAINTS on the walk, the joints, the look | dyad (VLM) + operator | the verdicts row | any earned negative unrecorded | rolling |

---

## The referee contract (what external tools may and may not do)

The substrate is the runtime truth. External tools are **referees and teachers** —
they consume our artifacts, answer a named question, and go home. They never own a
runtime clock, a render path, or a conserved state.

- **MuJoCo consumes:** `factory_rom.json` (joint centers, axes, ROM), the bone cage,
  body masses from the substrate's area law. **It answers:** "does this skeleton,
  driven this way, produce these contact forces / does it fall?" **Its verdict
  targets:** our G3 contact solve and our gait algorithms — a disagreement is OUR
  falsifier to earn, not theirs to be right about by default (record both sides;
  the measurement arbitrates).
- **OpenSim consumes:** the census skeleton + species. **It answers:** "where do
  ligaments and muscles stop this joint?" — the measurement our capsule model cannot
  make. Its limits feed the factory as `anatomy_limits.json`; where they conflict
  with a measured bone stop, the bone stop wins (it's measured on THIS mesh).
- **Isaac Lab consumes:** nothing yet. Deferred by doctrine — a learned black-box
  policy is the baseline our derived walk must beat, not a component of it. When the
  derived walk exists (B8 green), ONE Isaac run becomes the comparison bar.

---

## Stage specs (what an agent executes, in order)

### B5 — ANATOMY REFEREE (the next stage)
1. Obtain the Oku et al. macaque musculoskeletal model (Commun Biol 2021, open
   access) + OpenSim. Record the license in the corpus row.
2. Map the census skeleton to the model's joints (name-free: match by relative
   position on the body graph, not by label).
3. Extract per-joint ligament/muscle limits for every joint whose factory row is
   F2 (no bone stop) or F4 (extension blind spot): shoulders, wrists, jaw,
   extension limits everywhere.
4. Emit `anatomy_limits.json` (per joint: [min, max] + source). Where an OpenSim
   limit contradicts a MEASURED bone stop, record both — the bone stop governs the
   mesh, the anatomy explains the gap.
5. **Gate:** every F2/F4 joint has an anatomy limit or an earned "no data" row;
   species-sanity bands checked (a macaque elbow that can't reach 120° flags the
   model mapping, not the monkey).

### B6 — DYNAMICS REFEREE
1. Translate `factory_rom.json` + the bone cage into `<body>_mjcf.xml` (bodies from
   bone chains, joints with the derived axes/limits, capsule colliders from the rods,
   masses from the substrate's area × thickness law).
2. Drive the MJCF with the SAME march/CPG θ(t) series; record MuJoCo's contact
   forces per foot per step.
3. Compare against the substrate's G3 λ (estimator B) on the same series: report
   per-step peak/duty correlation and the mismatch.
4. Use the MJCF as the sandbox for gait/footstep ideas (cheap resets, mature
   contacts); a controller that survives the sandbox gets ported to the CPG as
   derived law (H16).
5. **Gate:** λ correlation ≥ the derived band on a reference march; any systematic
   mismatch is assigned (ours / theirs / model mass error) before B8 proceeds.

### B7b — VOLP GENERALIZATION (before full-skeleton behavior)
1. Every joint gets its ring + free set from the factory (the knee law: set from
   the distal rods, R_J from the local skin radius).
2. ONE unified volp-ARAP system (the H13 law) over the full joint set — iterative
   solve at full-body scale (the dense-inverse trick dies >~1k nodes; the validated
   CG/Schur scheme from volp_cg.py is the law).
3. **Gate:** the H5/H11/H13 gate bench re-run per joint (F1 pen, F2 volume,
   F3 strain); the dyad at each joint's flagged angles.

### B8 — BEHAVE (H16)
1. The CPG's placeholder slots (hips, elbows, spine) receive the factory/anatomy
   ROMs — θ_mid/θ_amp derived per joint.
2. Load feedback from the substrate's real λ (G3, estimator B at κ*) — already
   landed for the knees; extended per limb.
3. **Footstep planning:** the monkey measures (contact λ, cube index, terrain from
   the CA field) and chooses foot placement among candidate cells — keep moving
   forward? place here or here? — under the ROM/axis hard bounds.
4. **Gate:** metamorphic rotate-world PASS; no energy pump; referee (B6) agreement
   on the same drive; the dyad reads a walk, not a march.

---

## How the next body enters (the teddy bear, the chimera, anything)

Run B0→B10 in order. Only B0 (the mesh), B1 (its wounds), B3/B4 (its skeleton),
and B9 (its material GT) are body-specific work; B5–B8 are body-specific *data*
but the same machinery. The standing rule answers "what next" for any body at any
time: the earliest non-green gate.

---

## Monkey status board (2026-08-29)

- B0–B4, B9: **green.**
- B7: knees volp-green (H13); generalized SHOW live; **volp-generalization = B7b, next after B5/B6.**
- B8: knees walk (bit-exact CPG, real λ at κ*, G4 verdict recorded); **full-skeleton + footsteps = H16.**
- **B5 is the next stage.** Then B6, B7b, B8, B10.
