# THE SIX GAP QUERIES — outputs on the seeded graph (2026-09-15)

Machine-readable twin: `acceptance_results.json` (`six_queries` key). Store: 1482 objects / 130 relations (110 authored + reference join). All six shapes ran on the SAME store.

## Q1 — limb compartments lacking a closed, physically supported boundary

- **inst.band.feet** (verified): physically bounded — walls: memb.septum.feet_shins[simulated supported], memb.septum.feet_shins[simulated supported]
- **inst.band.shins** (verified): physically bounded — walls: memb.septum.feet_shins[simulated supported], memb.septum.feet_shins[simulated supported], memb.septum.shins_thighs[geometry_built supported], memb.septum.shins_thighs[geometry_built supported]
- **inst.band.thighs** (verified): physically bounded — walls: memb.septum.shins_thighs[geometry_built supported], memb.septum.shins_thighs[geometry_built supported], memb.septum.thighs_torso[geometry_built supported], memb.septum.thighs_torso[geometry_built supported]
- **inst.band.torso** (verified): physically bounded — walls: memb.septum.thighs_torso[geometry_built supported], memb.septum.thighs_torso[geometry_built supported]
- **inst.comp.thigh_l** (specified): boundary pending build — walls: memb.septum.thigh_l_shin_l[specified NOT-supported], memb.septum.thigh_l_shin_l[specified NOT-supported]
- **inst.comp.shin_l** (specified): boundary pending build — walls: memb.septum.thigh_l_shin_l[specified NOT-supported], memb.septum.thigh_l_shin_l[specified NOT-supported], memb.septum.shin_l_foot_l[specified NOT-supported], memb.septum.shin_l_foot_l[specified NOT-supported]
- **inst.comp.foot_l** (specified): boundary pending build — walls: memb.septum.shin_l_foot_l[specified NOT-supported], memb.septum.shin_l_foot_l[specified NOT-supported]

The four verified bands are bounded by built shared septa + skin; the per-bone compartments have SPECIFIED septa only — intended, not physical. A visual cap alone would not count.

## Q2 — structures that exist only as placeholders

- inst.comp.foot_l (volume, specified)
- inst.comp.shin_l (volume, specified)
- inst.comp.thigh_l (volume, specified)
- memb.septum.shin_l_foot_l (surface, specified)
- memb.septum.thigh_l_shin_l (surface, specified)
- region.leg_l (region, specified)
- region.seg.foot_l (region, specified)
- region.seg.shin_l (region, specified)
- region.seg.thigh_l (region, specified)

## Q3 — active parameters lacking units/source/applicability

- param.breath_period = 13.38 s — gaps: not validated against an independent reference (virtual-simulator provenance does not count)
- param.contact_spring_k = 13562000.0 N/m — gaps: not validated against an independent reference (virtual-simulator provenance does not count)
- param.kappa = 4.6e-10 Pa^-1 — gaps: source partly unknown; not validated against an independent reference (virtual-simulator provenance does not count)
- param.mass_inventory = 13824.5 kg — gaps: not validated against an independent reference (virtual-simulator provenance does not count)
- param.sigma_skin = 4000.0 N/m — gaps: source partly unknown; not validated against an independent reference (virtual-simulator provenance does not count)
- param.tau_recovery = 0.5 s — gaps: not validated against an independent reference (virtual-simulator provenance does not count)

All six carry units + source; the honest residual gaps are applicability conditions (temperature/strain-rate) and independent validation — a virtual-simulator provenance does not independently validate the simulator's material model.

## Q4 — what unfinished prerequisite blocks local withdrawal

- Ready now (prerequisites available): work.partition_leg_l, work.septa_leg_l, work.causal_demo_leg_l
- Blocked, by what:
  - memb.septum.shin_l_foot_l (surface, specified) ← blocked by work.septa_leg_l
  - memb.septum.thigh_l_shin_l (surface, specified) ← blocked by work.septa_leg_l
  - inst.comp.foot_l (volume, specified) ← blocked by work.partition_leg_l, work.septa_leg_l
  - inst.comp.shin_l (volume, specified) ← blocked by work.partition_leg_l, work.septa_leg_l
  - inst.comp.thigh_l (volume, specified) ← blocked by work.partition_leg_l, work.septa_leg_l
  - req.every_bone_sealed (requirement, specified) ← blocked by inst.comp.foot_l, inst.comp.shin_l, inst.comp.thigh_l

## Q5 — evidence that would go stale if a septum/material changed

- If `memb.septum.feet_shins` changed: ['ev.band_seal_conservation'] (directly measured against it)
- If `material.water` changed: ['ev.band_seal_conservation']

## Q6 — next ready task by explicit authored priority

- **work.partition_leg_l** (authored priority 1): Partition the left leg into per-bone volumetric regions
- Enables: experience.local_withdrawal, experience.press_and_response
- Acceptance: Acceptance = req.every_bone_sealed verification on the leg: count matches, cells conserve, press answers in the right bone's cell.
- Evidence it would add: {"falsifier_statement": "Derive segments from skeleton connectivity in the reference configuration", "acceptance_test": "Acceptance = req.every_bone_sealed verification on the leg: count matches, cells conserve, press answers in the right bone's cell.", "would_attach_to": ["experience.local_withdrawal", "experience.press_and_response", "inst.comp.foot_l", "inst.comp.shin_l", "inst.comp.thigh_l"]}

Ranking uses the AUTHORED `authored_priority` field only — no centrality, no imported-fact tasking (tasks follow req.every_bone_sealed / req.press_answer_chain).
