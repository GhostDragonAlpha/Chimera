# Elastic domain audit

This CPU diagnostic audits the already implemented isotropic STVK membrane; it
does not alter the law, material records, fixtures, or tolerances.

**STATEMENT:** The declared law is objective under proper 3D rigid motions, but
its admissible material domain and near-collapse boundary must be explicit:
`E > 0`, `-1 < nu < 1/2`, `h > 0`, finite nondegenerate triangles, and energy
reported per reference area.

**HISTORICAL INITIAL PREREGISTRATION (superseded):** A proper rotation preserves energy and force norms; a reflected
pose is reported with its inverted-face flag rather than silently certified as
a proper rotation; collapsed geometry and invalid material inputs receive named
refusals.

**FALSIFIER:** A proper rotation changes the energy beyond floating-point
roundoff, a collapsed triangle is accepted, invalid material is certified, or
thickness is silently multiplied into the per-reference-area law.

The derivation and units are sourced from
`docs/evidence/elastic_foundation/DERIVATION.md` §§2–3, 6, and 12 and
`GPU_HANDOFF.md` §§3–4. The diagnostic records these as provenance; it does not
claim unrestricted finite-strain or volumetric compression validity.

Run with `python tools/elastic_foundation/domain_audit.py --json`.

## Correction record

The first audit used a rest pose and arbitrary synthetic material, so its
rotation result was vacuous. The corrected runner uses the committed
`trisingle_stretch.npz` current pose and a proper cyclic coordinate rotation,
then compares the full force vector after rotation. It also runs the existing
`eulerian_frame` mutation as a known negative control; the observed covariance
break is retained rather than converted into a tolerance.

The current numeric gate uses full-vector covariance and independent frozen
energy/force oracles. The source API accepts `E` in Pa and `h` in metres, while `lambda_bar` and
`mu_bar` omit `h` and the law computes the per-reference-area energy with an
implicit unit thickness. Equal-pose runs at `h` and `2h` therefore produce the
same energy. This is recorded as
`CONTRACT_CONFLICT_NOT_CERTIFIED`, and no law change is made here.
