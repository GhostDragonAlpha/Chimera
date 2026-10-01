# ONE LIMB — PREREGISTRATION (physics half, agent AN2)

Written BEFORE the partition/patch code was written. Rule 0: statement,
prediction, falsifier — all three, stated first. The brief's central
falsifier is adopted here verbatim as this lane's own:

> **If the graph says a structure exists and works, we must be able to
> select it, inspect its physical connections, intervene on it, and
> observe the predicted change.**

This file covers the PHYSICS half: the limb partition (membranes, septa,
volumes, mass) and the local-sensing/intervention machinery. The graph
lane owns its own mirror of the falsifier.

---

## MEMBRANE M1 — the partition is connectivity, not bands

**STATEMENT.** The left leg's sealed compartments can be derived from the
measured skeleton's CONNECTIVITY alone — the pin chain hip_L→knee_L→ankle_L
read off mesh adjacency of pin-dominant skin — and sealed with oblique
plane walls through the joint pins, without horizontal world bands and
without nearest-pin Euclidean labels deciding any boundary.

**PREDICTION (unmeasured).**
P1. The pin adjacency graph over the 28 measured pins, computed from mesh
    edge connectivity of dominant-pin vertex labels, contains the chain
    hip_L—knee_L—ankle_L as a connected path, and no leg pin is adjacent
    to a contralateral pin.
P2. Cutting the merged left-leg cell with the plane through knee_L, normal
    along (knee_L − hip_L), yields a thigh daughter and a shin+foot
    daughter whose seed labels (hip_L-dominant verts vs ankle_L-dominant
    verts) agree with the wall sides for > 90% of the leg's vertices.
P3. The same cut at ankle_L (normal along (ankle_L − knee_L)) yields shin
    and foot daughters with the same > 90% seed agreement.

**FALSIFIER (named before the run).** If the derived pin graph does NOT
contain the chain (P1), or the seed-vs-wall agreement lands <= 90% (P2,
P3), the connectivity claim is FALSE for this creature: the partition code
refuses by name and the finding is recorded as a falsification, not
patched around. A silent fallback to band cuts or Euclidean nearest-pin
labels is forbidden.

Scope honesty: one limb (left leg) is in scope. The right leg, arms, tail
keep their current band compartments; their repartition is backlog.

## MEMBRANE M2 — the walls are physics, the septum is one wall

**STATEMENT.** After the partition, every compartment is a closed oriented
surface in the existing cut-and-weld machinery: each new wall is ONE
physical septum (the welded cross-section, shared slots, opposite winding
in each neighbor's volume sum), and the pre-existing hip wall remains the
ONE septum between thigh_L and the torso cell.

**PREDICTION.**
P4. Sum of all cell rest volumes after partition equals the whole-creature
    divergence volume to |conserve| < 0.01% (the current tree measures
    −0.000117%); per-cell masses sum to 13,824.5 kg within the same
    relative tolerance (rho = 1000 kg/m^3 water, the inventory's only
    material).
P5. Every cell passes the closed-manifold test (each undirected edge of
    its piece set used exactly twice) and divergence v0 > 0.
P6. Total genus is preserved: the sum over cells of (2 − Euler
    characteristic) is unchanged by the repartition.
P7. Under knee_L poses inside the tested range (0, ±10, ±20 deg), every
    new cell's live volume stays positive, no degenerate flag sets, and
    conserve_pct stays under 0.01% in magnitude — the welded blends ride
    the posed surface (the existing growth law) and no reclassification
    happens (piece lists are immutable after the build; ownership is
    fixed at build).

**FALSIFIER.** Any failed closure test, any negative or degenerate
daughter, any conservation residual >= 0.01%, any genus change, or any
degenerate flag under the pose sweep falsifies M2 as built. The 0.5%
degenerate guard stays ARMED: a legitimate-segment refusal (a real
compartment rejected by the guard) is a FINDING with re-derived
arithmetic — never a silent loosening of the threshold.

Nested regions: the current inventory has NONE (each cell is a disjoint
closed surface; fluid-only mass model — structural bone material is not
in the inventory, so fluid vs structural double-count cannot arise in the
present engine; if bones are added later, their enclosed volume must be
subtracted from the enclosing cell's fluid — recorded as the named
precondition). The partition preserves disjointness; P4 is the divergence
witness (an internal double wall or a gap would break it).

Geometric closing face vs load-bearing septum: the walls built here are
BOTH (the weld is the pressure boundary the kappa law reads through each
cell's volume). What is NOT claimed: independent structural strength of a
septum (there is no separate strut material — the wall is membrane
geometry carrying pressure, not a tendon or a bone). Any later claim that
a septum bears bending load needs its own membrane.

## MEMBRANE M3 — local sensing has location, delay, and a cut that is real

**STATEMENT.** Scalar cell pressure cannot locate a touch inside a cell.
The honest sensor is a PATCH: a finite receptor region of skin, with its
own filtered, saturated signal, carried to the controller over a path
with a FINITE transport delay, disconnectable as a real state (a cut
path delivers nothing and remembers being cut).

Receptor law (each constant named before the run; none tuned after):
- raw(v) = press_off_[v], the skin's own local indentation field — the
  same field the surface renders and the volume law reads. The patch raw
  = max over its vertices. The controller sees NO touch point, NO force,
  NO object identity — only this field over the patch's own vertices.
- filter: 1st-order low-pass, tau_f = 10 ms = 3 ticks at the 300 Hz tick
  (integrates >= 3 samples: the shortest honest passband at this
  sampling).
- saturation: out_pre = sat * tanh(filt / sat), sat = press_r0_ = 0.03 m
  (the reduced press model's own spatial reach: beyond r0 the Gaussian
  field is dead; the receptor's full scale is the model's full scale).
- transport delay: delay_s = |centroid − spine_lower pin| / 70 m/s. 70 m/s
  is the A-beta afferent conduction velocity (Kandel, Principles of
  Neural Science — a reference assertion, source recorded); spine_lower
  is the named central terminus (the lumbosacral analogue — leg reflex
  arcs are spinal). The line carries (time, filtered) pairs; delivery
  pops front(t <= now − delay_s). Reported latency = delay_s + up to one
  tick of sampling.
- trigger: rising edge of the DELIVERED signal across thresh = 1e-3 m
  (10x the repo's named 0.1 mm press-cutoff scale: one decade above the
  field's resolution floor).

**PREDICTION.**
P8. A press applied within the shin_L patch fires the shin path after the
    predicted delay ± 1 tick; the same press produces NO event on the
    other segments' patches (locality).
P9. Cutting the shin_L path (POST /tick_patch {"path":"shin_L",
    "connected":false}) makes the identical press produce NO delivered
    event and NO flinch, while the passive mechanical response is
    UNCHANGED: the owning cell's pressure trace and the surface dimple
    match the connected case (same press law). The cut is reported with
    its tick and engine timestamp, and the path reports cut=true.
P10. Reconnection restores the contribution without synthesizing a stale
     spike (the line drains on cut; edges detect only on newly delivered
     samples).

**FALSIFIER.** If the patch fires for a press outside its region (P8), or
a cut path still triggers a response (P9), or the passive pressure trace
DIFFERS between connected and cut cases beyond sampling noise, or a
reconnection synthesizes an edge with no new stimulus (P10) — M3 is
falsified as built. A "sensor" that reads anything the controller could
not physically know (touch force, press coordinates) is a falsification
of the honesty clause, not a feature.

## MEMBRANE M4 — the smallest supported intervention is causal

**STATEMENT.** The demonstration intervenes on the SENSORY PATH (the
brief's disconnect case): one named path, cut and restored, with
consistent IDs (patch id → owning cell id → response pin id) and the
engine's own timestamps (ts_us/ts_ms/ticks) across the pressure trace,
the sensor event, and the actuator response.

**PREDICTION.**
P11. With reflexes armed and patches armed: connected case — touch inside
     shin_L → delivered event at t_touch + delay (±1 tick) → flinch env_l
     rises the same tick the event delivers → strut pin L (resolved:
     pin 17) pose moves next tick. Cut case — identical touch → env_l
     stays 0, pin 17 stays at bearing, cell pressure and dimple match
     the connected case.
P12. The actuator is a SERVO (a position write to joint_deg_, rate/ROM
     capped, exact flex-0 return). It is labeled a servo everywhere, is
     reused for this demo, and is NEVER called contractile tissue. There
     is NO force/torque computation in the actuator path (finding F-2,
     see STALE.md) — therefore "obstruct an actuator and report the
     reaction load" is NOT demonstrated: no torque channel exists to cap
     or to react. The honest statement: obstruction of a pose servo
     reduces to pin ownership (the existing gait/stance/reflex ownership
     law), and reaction-load evidence requires the force-state actuator
     that does not exist yet. That gap is NAMED, not papered over.

**FALSIFIER.** If the connected and cut cases differ in anything BUT the
active contribution (pressure, dimple), or if IDs/timestamps fail to
line up across the three traces, the causal claim is falsified. If
anyone reports this demo as "tendon cut" or the servo as "muscle", the
labeling clause is falsified — the demo's own JSON must carry the servo
name.

## MEMBRANE M5 — the gaps exposed (named now, before the run)

G-1. **Open-wound fluid transfer does NOT exist.** Each sealed cell
     integrates its own P = -(V−V0)/(kappa·V0) independently; no term
     moves fluid between cells; a puncture cannot be represented. The
     demo therefore shows isolation by CONTROLLED BOUNDARY LOADING (a
     press is a boundary load; the neighbors' pressure responds only
     through geometry/mechanics, not exchange). Two auto-sealed daughters
     are never called leakage. Puncture (a real hole with transfer and
     total-system mass accounting) is the named next task.
G-2. **Actuator force state does NOT exist** (see M4/P12, F-2).
G-3. **Reference-data import (Uberon/OpenSim/BodyParts3D) is NOT in this
     lane's slice** — the graph lane owns ingestion; the physics side
     consumes the measured pins (.tmp/joints28.json, already in the
     engine) and records which quantities are measured vs asserted.

## What this prereg does NOT claim

- Not whole-body per-bone compartments (one limb only).
- Not contractile muscle, not gas respiration, not organ-level anatomy.
- Not a claim that the knee/ankle walls sit at the anatomical joint space
  midline — they sit at the MEASURED pin positions, the skeleton being
  the placement authority; the seed agreement (P2/P3) is the honesty
  metric of that choice, not a biology claim.
- The press model delta = F/(4*pi*sigma) and tau = 0.5 s recovery remain
  QUALIFIED REDUCED MODELS (recorded as such since the fleet's early
  windows); the patch senses the field they produce, it does not
  validate them.

---

## ADDENDUM 2026-09-15 — P2/P3 FALSIFIED BY THE OFFLINE MEASUREMENT (before any build)

The derivation table (`derivation_table.json`, from `derive_limb.py` over the
engine's own snapshot blobs) ran BEFORE the build window, exactly so a wrong
prediction would lose here and not in front of a compiled binary.

**P1 — PASS.** The pin graph derives the chain exactly: hip_L—knee_L 112
crossing mesh edges, knee_L—ankle_L 100, hip_L—ankle_L **0**, with the 1%
floor rule; the strongest-neighbor walk from hip lands on knee then ankle
(pin ids 13→15→17). The connectivity claim is TRUE for this creature.

**P2/P3 — FALSIFIED.** The pre-registered "> 90% seed-vs-wall agreement" is
FALSE: measured 82.9% overall. Per population: hip-dominant seeds 243/243
= 100% on the thigh side; ankle-dominant 1287/1477 = 87% on the foot side;
knee-dominant only 108/256 = 42% on the shin side. The guess that binding
labels would track a plane through the joint to 90% was WRONG — the binding
is a smooth IDW blend and near a joint it is a gradient, not a partition;
the knee-dominant population straddles the knee plane 148/108. That is the
saddle the plane must cut; no plane can match a smooth blend there.

**What survives, honestly:** the partition's physical claim (M1's
connectivity clause, upheld by P1) and M2's invariant bars (closure,
orientation, positive volumes, coverage, mass, genus) are untouched. What
dies: the use of binding-seed agreement as a PASS BAR for wall placement.
The wall placement authority was always the measured skeleton (the brief's
own rule); the seeds "seed but do not seal". Accordingly: the engine
REPORTS seed agreement as data (per-population, in the partition report)
and the pass/fail decision rests on M2's physical invariants + P1's chain
check. The 90% bar is not quietly lowered — it is recorded here as a lost
prediction, with the losing numbers, per Rule 0.

**Amended wall claim (dated, falsifiable):** each wall passes through the
measured joint pin, is normal to the proximal bone axis, and sits on the
derived chain (P1). The falsifier for THIS claim: a wall whose plane does
not contain its pin (measurable), or a chain that does not derive (P1).
