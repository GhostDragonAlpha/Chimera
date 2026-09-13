# FEET PREREGISTRATION — membranes authored first, before training

Rule 0: statement, prediction, falsifier — BEFORE implementation. Every
number below is MEASURED from the live engine state (GET /joints,
2026-09-13 ~04:15 local) or derived from those measurements. This is the
body-completion rung the KERNEL_SPEC build order names: "bodies authored
as membranes (feet first — the monkey's missing piece), then training,
which stays forbidden until the body is complete."

## THE MEASURED DEFECT

The rendered creature shows skin-shaped feet, but ankle is the LAST
computed joint (GET /joints: n_joints=28, ends at ankle_L/ankle_R).
The foot skin does not travel with a computed body: it is decoration.
A creature that cannot compute its feet cannot stand on computed force,
and walk training remains forbidden (operator veto, standing law).

## MEASURED STATE (live, engine units)

- ankle_L J = (+0.4609, 0.3378, 0.0678); ankle_R J = (-0.4609, 0.3378, 0.0678)
- knee_L  J = (+0.4833, 1.9033, -0.0155)  -> shank length ~1.57
- hip_L/R J = (+/-0.1734, 3.4153, 0.1155) -> thigh ~1.52
- ground plane y = 0; ankle height above ground = 0.3378
- stance: feet at +/-0.461 in x (stance width 0.922)

## DERIVED FOOT GEOMETRY (anthropometric ratios, from the shank)

- foot length = 0.5 x shank = 0.78  (heel behind ankle, toes ahead)
- foot width  = 0.5 x foot length = 0.39
- ankle sits 30% of length from the heel: heel extends 0.234 behind the
  ankle x-offset, toes 0.546 ahead (toes = -z, the creature's facing)
- sole plane: y = 0 (flat contact, no float, no sink)
- the ankle hinge (axis = x) drives flex: the membrane binds at the
  ankle pin and deforms forward to the toe line

## STATEMENT

A foot is a MEMBRANE authored as data — a triangle set with programmed
material constants — hinged at the measured ankle pin, sole resting on
the ground plane. It is not a recorded mesh patch and not a sculpted
decoration: loads through the foot distribute through the bond network
at the ankle, and the sole's contact is computed, not scripted. The
current skin-shaped feet are decoration; these membranes replace them
as the computed truth surface.

## PREDICTIONS (test bars)

P1. Visible: after load, both feet appear in /frame and /glass at the
    ankle positions, symmetric in x about 0, toes -z. Pictures land in
    CHIMERA_PROOF (pictures or it did not happen).
P2. Grounded: sole plane sits at y = 0 within the engine's numeric
    epsilon; the feet neither float nor sink (measured from the
    membrane buffer, not eyeballed).
P3. Material truth: the foot material carries a SOURCED constants row
    (skin: young_modulus ~0.1-0.2 MPa range, cited) added to the
    constants table with a source string — the validator refuses
    uncited constants, and this row closes the gap (OPEN until
    committed with its citation).
P4. Travel: posed at the ankle (flex), the foot membrane MOVES with the
    ankle pin — the skin-travel law measured on the rest of the body
    applies to the feet (before/after pictures at two flex angles).
P5. Load path: a press intent on the sole computes contact through the
    membrane (the scratch/press law chain), not a scripted stop.

## FALSIFIER

Any bar fails, OR the feet render asymmetric, OR the sole plane is not
y=0, OR the foot does not travel with the ankle pin when posed. On
failure the successor is named: the rig binding for the foot membrane
is the defect (recomputed bindings, Python-side data — never an excuse)
and the rebind is measured before any other work resumes.

## OPEN (named, with its test)

- Engine scene composition: feet enter the loaded membrane scene through
  the same buffer pipeline as the body (cpp_bridge 14-float splat layout
  vs 7-float vertex layout — resolved at implementation, measured by P1).
- Press intent (P5) lands when the named engine press appliance exists;
  until then P1-P4 gate the geometry and binding work.
