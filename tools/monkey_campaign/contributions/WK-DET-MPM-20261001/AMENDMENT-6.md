# AMENDMENT-6 — lane det-mpm (prereg 32e485e0; amendments a7dc1f1a, bb81ce60, 09dd5a8b, 966a44d8, f6149e76)

Status: DRAFT for Lieutenant commit. Submitted by wk-det-mpm, 2026-10-02.
Dispatches the T1/T2 transfer-boundary arms declared in AMENDMENT-5 and the
final report. Contention-free cells first; contention only as the declared
cheap NG add-on (C20). The three named boundaries (B1 consumed-return int32
only; B2 per-thread static record bounds; B3 int32 workspace shape cap)
constrain what T2 can attempt: if the scatter-heavy target hits B2/B3, that
failure IS the result (pre-ruled).

## C17 — T1 specimen `mpm-changing-contact` (evolving contact topology)

Scene: identical blocks and parameters to `mpm-multi-spec` (all provenance
fields of the prereg scene unchanged: same bounds, densities, materials,
jitter RNG, voxel 0.05, 178,669 particles), with ONE declared input change:
the kinematic block's particles carry a constant initial velocity
(0, 0, KIN_VZ=0.5 m/s), imposed by the solver as a moving infinite-mass
boundary condition (validated CPU-side under R2R: kinematic qd z stays 0.5000
across steps; material response visible).

Declared contact behavior (the DECLARED input is the velocity field; the
exact schedule is emergent, not scripted): the block starts at z[0, 0.25]
with no overlap, rises through sand+snow (z 0.5-0.75, contact ~frames 30-60),
breaks contact, continues into mud (z 1.0-1.5, contact from ~frame 90
onward). Contact sets and per-node contact values therefore change across
frames while per-thread scatter counts remain STATICALLY BOUNDABLE per frame
(the integrand structure is frame-invariant; only contact values and the set
of touched nodes evolve — no data-dependent loops are introduced).

Predictions (observations-vs-guarantees):
- P-T1-1 (NG pair, separate processes): expected bit-exact, consistent with
  the clean and contended NG observations; recorded as OBSERVATION either
  way; no guarantee claimed (NG carries none).
- P-T1-2 (R2R pair): expected bit-exact within warp's documented scope
  (supported scatter patterns; changing contact sets alter values and touched
  nodes, not per-thread record structure). FALSIFIER: any whole-run or
  checkpoint divergence between the R2R processes is a recorded finding that
  blocks any T1 transfer claim and demonstrates order-dependence triggered by
  contact evolution on this stack.
- P-T1-3: IC equality across processes (builder + state hashes), as in every
  prior cell; falsified => harness bug, stop and re-prereg.

## C18 — T2 specimen `mpm-scatter-heavy` (maximal statically-boundable scatter)

Scene: the SAME materials and volumes refined to voxel 0.035
(particles_per_cell unchanged): 518,607 particles = 2.90x the prereg scene
(measured, CPU-validated under R2R). Relationship to real MPM patterns,
honestly stated: this is the solver's OWN P2G/strain scatter surface
(identical integrands, identical atomic sites) scaled by resolution
refinement — it maximizes scatter TRAFFIC exactly the way a real
higher-resolution MPM run would, and introduces NO new atomic pattern. It
therefore does not test pathological patterns (dynamic per-thread loops,
consumed returns) — those are already characterized by B1-B3. Per-launch
record arithmetic at T2 scale: ~518,607 particles x 3 scatter sites ~ 1.56M
records/launch (~63 MB at the measured ~40.5 B/record), three orders of
magnitude inside the B2 static bound and the B3 int32 workspace cap that
killed the synthetic kernel; the prereg-scale clean launches (~0.5M records)
already ran R2R bit-exact.

Predictions (observations-vs-guarantees):
- P-T2-1 (NG pair): expected bit-exact observation; no guarantee claimed.
- P-T2-2 (R2R pair): expected bit-exact within the record budget (arithmetic
  above); FALSIFIER: divergence = recorded finding blocking T2 transfer;
  a B2/B3 failure = the pre-ruled result confirming the boundary at 2.90x
  solver-realistic scatter scale (also a recorded finding).

## C19 — Arms, frames, provenance

All arms: separate OS processes (one queue job each), same hash protocol
(prereg section 4), same provenance discipline (receipts record specimen,
voxel, kinematic_vz, contention params, mode readbacks, env identity);
contention-free first.

| id | specimen | mode | frames | note |
|---|---|---|---|---|
| det-mpm-t1-ng-a/b | T1 | NG | 120 | pair |
| det-mpm-t1-r2r-a/b | T1 | R2R | 96 | frame deviation: measured R2R cost 4.17-4.32 s/f => 96f ~400-415 s, inside the 570 s guard; 120f measured 529-558 s is too close to the 600 s queue cap (C4 precedent) |
| det-mpm-t2-ng-a/b | T2 | NG | 120 | pair |
| det-mpm-t2-r2r-a/b | T2 | R2R | 24 | frame deviation: measured per-frame cost scales ~2.90x => ~12.2-12.6 s/f; 24f ~293-302 s, inside the guard |

Contention: R2R contention for T1/T2 is PRE-DECLARED UNSATISFIABLE (B1-B3
standing, amendment-3/4/5 evidence) and will not be attempted. Cheap NG
contention add-ons ARE declared and authorized as a secondary wave, run only
after all eight primaries complete cleanly: det-mpm-t1-ng-cont-a/b and
det-mpm-t2-ng-cont-a/b (v7, NG, same frames as their primary arms, N=13378 —
the measured cal2 NG value; per-launch iters 8192 unchanged). These carry the
declared C5-letter caveat (per-frame share design drains within the last
frame; reported as context, never upgraded). T2 NG contention runs at T2's
own 518k-particle scene — its contended slowdown measurement is scene-specific.

Harness: run_mpm_arm_v7.py
sha256 1d4a99c80d521de2ee0047f5c03c75e28a01ced1fc8f60a211335166246af1eb
(diff vs v6: `--specimen` argument with the three-way table above, per-
specimen voxel, T1 kinematic velocity, receipt fields `scene`/
`kinematic_vz`; DEFAULT specimen = mpm-multi-spec so all prior arm identities
are unaffected; kernel, contention machinery, hash protocol byte-identical).
Both new specimens CPU-validated under RUN_TO_RUN with CUDA hidden (exact
construction, two full steps each, moving BC verified).

## C20 — Validity and report

C5 unchanged for any contention add-on. The final report adds T1/T2 cells to
the cell table and provenance table; observations-vs-guarantees wording is
mandatory in every T1/T2 conclusion (per the Captain's standing correction).
No other prereg term changes.

## Requested commit

Add to tools/monkey_campaign/contributions/WK-DET-MPM-20261001/ as ONE commit:
1. AMENDMENT-6.md (this file as staged)
2. run_mpm_arm_v7.py (as staged)
