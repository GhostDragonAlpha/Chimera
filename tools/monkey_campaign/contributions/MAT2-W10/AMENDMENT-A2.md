# AMENDMENT A2 — MAT2-W10 preregistration (declared-geometry pin addition)

Disclosed BEFORE any implementation commit and BEFORE any experiment.
PREREGISTRATION.md and AMENDMENT-A1.md are untouched. This amendment adds
ONE sealed-lane pin that supplies declared skeleton geometry for the
visualization pose law.

## What changed

Section 1 (Input pins) gains one lane pin, verified at freeze:

- `tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json`
  `013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173`

## Why

The pose law (prereg section 6) renders the declared gait-walker skeleton and
refuses any geometric constant absent from pinned bytes
(`asset_geometry_absent`). At implementation time the per-segment lengths
were located in the derivation lane's own pinned derived-numbers record:
`leg_pendulum` (the declared leg pendulum of the SAME 10.037998 kg body
derivation), and the segment table `thigh.length_m = 0.163`,
`shank.length_m = 0.182` (with masses and COM fractions). These are declared
constants of the certified body's own derivation — read from pinned bytes,
never invented. The foot contact offsets (heel [-0.012, 0, 0], mp head
[+0.074, 0, 0], radius 0.004) and the joint tables/zero map come from the
already-pinned `model.dynamics.gait_walker` contract (amendment A1's program
bytes). Pinning this file closes the last geometry input before anything
runs; a run that needed an unpinned constant would violate the prereg's own
refusal law.

## Receipt binding

Every W10 receipt records `preregistration_sha256`, `amendment_a1_sha256`
AND `amendment_a2_sha256` (the live bytes of each file) and refuses any
document whose recorded values do not match.
