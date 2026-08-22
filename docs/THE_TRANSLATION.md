# THE TRANSLATION — triangles are authoring, the field is the truth

*2026-08-22. Named BEFORE the build, per the law. Rule 0 applies: statement,
prediction, falsifier — or it does not get built.*

## STATEMENT (someone could disagree)

Any triangle mesh can be translated into the kernel's point set by **sampling**,
with mass conserved exactly: each packet's mass is the material density times its
share of the surface (or volume), so the sampled body has the same total mass and
the same moments of inertia as the analytic body. The mesh is an authoring format;
the packet field is the only physical truth. Light and physics are both readers of
that one field (per THE_TWO_FORCES). No engine feature may treat the mesh as the
truth after translation.

**This is the universal importer.** CAD parts, scanned objects, downloaded meshes,
spacecraft — all enter the same field by the same law, and thereafter obey the same
two forces (DRAW and RESISTANCE, THE_KERNEL.md) on the same tree. Barnes–Hut gives
the translated body every resolution at once: deep nodes carry detail, shallow
nodes carry coarse mass — the gait solver, the fur solver, and the orbit solver
read the SAME body at the depth each can afford.

## THE LAW

1. **Conservation is the contract.** Sum of packet masses == density × analytic
   measure (surface area for shells, volume for solids), to a named tolerance.
   Moments of inertia match to the same tolerance. A sampler that fails this is
   wrong — fix the sampler, never the tolerance.
2. **Sampling density is derived, not picked.** Packets per unit area come from
   the thinnest feature that must carry force (a knit shirt needs enough packets
   across its 2 mm to bend; a hull needs enough to be stiff). The resolution dial
   is set by the physics the part must perform, stated before sampling.
3. **Appearance is not physics.** Color, texture, and sheen ride packets as
   reader attributes for the light pass. Translation carries them; the force
   laws never read them.
4. **Rigidity is a material property, not a mode.** Stiff parts are bonded stiff
   (RESISTANCE wall/bond from the materials table); truly rigid parts may lock
   their packets to one frame the solver integrates as a single body. The choice
   is per-material, from composition — never per-convenience.

## PREDICTION (to be measured on the CAD bear)

- Sampling `models/cad_bear/cad_bear.glb` at the derived density yields packet
  mass within **1%** of the analytic mass (geometry × materials-table density)
  for every one of the 19 parts, and total moment of inertia within **2%**.
- The packet bear, rendered by the field's light reader, is recognizably the
  CAD bear to a blind judge at first frame (the dyad gates this, not me).

## FALSIFIER (any one ends this build)

- Mass or inertia mismatch beyond tolerance on ANY part → the sampler is wrong;
  the law stands, the implementation is judged.
- A part that cannot carry the force it must (shirt tears at rest, hull flows)
  at its derived sampling density → the shell-law clause (2) failed; the
  successor is an explicit membrane law for thin parts, named here in advance.
- Any code path that edits the mesh after translation to fix a physics
  discrepancy → the doctrine is violated; the build stops.

## WHAT THIS KILLS

Every future "which format?" argument. .splat, .ply, .glb, .fbx, CAD, scans:
all are authoring inputs. None is required. The field is the game.

## RUN RECORD (append-only)

**Run 1 (2026-08-22): FALSIFIER FIRED — implementation judged, law stands.**
mass_err 0% everywhere (conserved by construction), inertia FAIL 17/19. Three
bugs, all mine, all in the implementation:
  a) mesh volume summed per-triangle-abs — not translation-invariant, inflated
     off-origin parts up to 4.6x. Fix: signed divergence sum, abs of the SUM.
  b) capsule analytic inertia used cylinder-only formulas — caps are 32% of arm
     mass at +-L/2, undercounting I_tr ~70%. Fix: exact solid-capsule inertia
     (cylinder + 2 hemispheres, parallel-axis).
  c) N = 1/tol^2 put MC noise at exactly the tolerance (eyes: 28 packets).
     Fix derived: N >= 4/tol^2 for noise <= tol/2.
Also found by this run: cad_mesh.capsule duplicated its equator ring, building
a spurious interior cone that ate ~25% of capsule volume while rendering fine
(the mesh looked right in UE — numbers caught what eyes missed. The dyad
working as designed). Fix: continuous row order, no seam rings.

**Run 2 (2026-08-22): FALSIFIER FIRED — margin derivation corrected.**
Capsule fix verified (arms 82-176% -> 1.9-3.3%). Remaining fails all in
2.0-4.1% = pure MC noise at the boundary; mirror parts differed by luck
(ear_L 2.07% vs ear_R 1.65%). The N>=4/tol^2 derivation stands as stated;
mesh resolution raised (SEG 28->48, RING 20->32) so faceting << tol/4.

**Run 3 (2026-08-22): ALL PASS.** 190,000 packets, total mass 2.5057 kg,
mass_err 0.000% all parts, iner_err max 1.921% (sleeve_R) vs tol 2%.
Output: models/cad_bear/bear_packets.npz (pos, mass, part, packet_size).
Numbers gate: GREEN. Eyes gate: pending operator verdict.
