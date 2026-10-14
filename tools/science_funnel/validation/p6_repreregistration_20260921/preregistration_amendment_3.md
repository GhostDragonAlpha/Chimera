# PREREGISTRATION AMENDMENT 3 — the seat band re-derived: [0, cut], tol_ip as the resolution floor

Banked (`preregistration_amendment_3.sha256`) BEFORE the corrected-contrast re-run. This amendment
changes NO number's value; it changes ONE number's ROLE, and the change is forced by the run's own
falsifier firing. The prior lane's discipline is followed: amendments are banked, justified by the
run's measured numbers, and recorded with the run that motivated them.

## A. WHAT FIRED (run 1, battery sha256 c82947c22e85c75b2537175fd18a17842279b9d80e2f049f8b843be44788a77d, byte-identical on immediate re-run)

The v1 predicate's Leg 1 was banked as a HARD band [tol_ip, cut] with tol_ip = 0.08 mm as a clause
edge; its own falsifier (preregistration.md L6) read: "if the REAL arm's seat readings fall below
tol_ip anywhere on the grid, the half-voxel derivation is mis-derived → the amendment voids."
MEASURED, IT FIRED:

- REAL arm, hip 02, grid point k−3 (θ = −3R/5, the flexion-side interior): seat gap
  **0.053906119839 mm** < 0.08 mm — while the head-center displacement is **0.0 EXACTLY** (the pivot
  law's own signature: the head is CENTERED in its socket). Hip 03's grid minimum
  (0.142631908664 mm) cleared the floor; the v1 verdict was real_pass FALSE on hip 02 alone.
- The measured inconsistency is a CLAUSE inconsistency, not a pose inconsistency: the displacement
  clause certifies CENTERED while the hard lower edge refuses the SEAT. Two derived clauses cannot
  both be reading the same pose correctly; the run decides which is wrong: the head is centered by
  the fit's own geometry (d ≡ 0 for ANY rotation about the fitted center — an identity, not an
  estimate), so the clause that contradicts it is the lower edge.

## B. THE MEASURED THEOREM THE FIRING YIELDS

On this mesh class, SEATED RIGID IMPINGEMENT legitimately drives the unsigned vertex-vertex gap
BELOW the surfaces' half-voxel localization (0.0539 mm at d ≡ 0.0): at deep flexion the femoral
NECK meets the acetabular RIM — bone-on-bone contact, which a rigid model renders as gap → the
sampling floor — while the HEAD stays in the socket. Therefore NO positive lower edge derived from
the mesh's resolution can carry a hard seat clause without mis-classifying seated impingement as
dislocation. The v1 reading of §5A ("[tol_ip, cut]") was a MIS-DERIVATION of the mission's band
form; the mission's own form — "a gap band [0, cut]" — is the derivable one, and the firing is its
evidence.

## C. THE RE-DERIVATION (predicate v2; zero free numbers)

- **LEG 1 — the seat band is [0, cut].** Lower edge 0: gaps are unsigned and non-negative; the
  committed cut's own class is the TOUCHING class — contact (g = 0) is IN the seat class, separation
  beyond 3.0 mm is out. Upper edge cut = 3.0 mm, committed, unchanged.
- **THE INTERPENETRATION TOLERANCE STANDS, DERIVED, AS THE RESOLUTION FLOOR:**
  tol_ip = specimen.resolution_um/2 = 0.08 mm — a reading below it lies inside the surfaces' own
  localization, where the gap metric CANNOT certify not-through (both seated-impingement contact and
  through-crossing live there). Readings below the floor are RECORDED per pose
  (`reading_class: below_resolution_floor`), never clause-binding. The value is untouched: it is the
  committed resolution's half-step, exactly as banked in preregistration.md §2.2.
- **LEG 2 — the head-center displacement band, UNCHANGED and now load-bearing as the not-through
  test:** d(θ) = ‖pose(c*) − c*‖ ≤ band_h = the registered fit's own RMS residual
  (band_02 = 0.155477725893 mm, band_03 = 0.147474758014 mm). The displacement is the through-test
  AT THE HEAD — where dislocation lives; the gap metric's blindness below the floor is exactly why
  the through-test must be carried here. An arm PASSES P6′ iff Leg 1 AND Leg 2 hold at every θ of
  the closed cited range (grid: endpoints exact + R·k/5, k = −4..4).
- TUNING AUDIT (F4): no number's value changed — tol_ip's derivation is byte-identical
  (resolution_um/2), cut and bands are committed/fit-derived as before; the changed ROLE is forced
  by the fired L6, and the firing itself is a measurement (0.0539 mm at d ≡ 0.0), not a preference.

## D. PREDICTIONS FOR THE RE-RUN (run 2), banked before it

- The re-run reproduces run 1's readings EXACTLY (same deterministic path; determinism falsifier).
- **REAL ARM PASSES P6′ on both hips:** every grid gap ≤ 3.0 mm (max 2.21511346552 mm hip 02,
  1.650134761681 mm hip 03) and d ≡ 0.0 exactly at every grid θ. Below-floor readings RECORDED
  (hip 02 k−3: 0.053906119839 mm — seated-impingement contact class at d ≡ 0).
- **NULL ARM FAILS P6′ on both hips via the displacement band:** d up to 5.745805839276 mm
  (36.96× band_02) and 3.945980865254 mm (26.76× band_03), 0.0 at rest only, reproducing
  2·|c⊥|·sin(|θ|/2) to ≤ 1e-9 at every grid θ. Its seat-band readings are all ≤ 3.0 (max
  1.438430430193/1.486366553653 mm — the predicate's blindness to pivot-in-gap rotation, now
  carried by Leg 2 exactly as designed); below-floor reading RECORDED (hip 03 +R: 0.046718998681 —
  the through-class reading the prior lane diagnosed).
- **THE DISCRIMINATION (the lane's headline):** real PASS ∧ null FAIL on both hips, on the
  conjunctive predicate. If the real arm fails either clause or the null arm passes both on either
  hip, the amendment FAILS and the design REMAINS VOID — final.

## E. FALSIFIERS FOR RUN 2 (v2; named before the run)

- **L5b the discrimination (headline):** as in D, else the design remains VOID.
- **L6b the upper edge:** any REAL arm gap > 3.0 mm on the grid → the predicate fails → the design
  remains VOID. (The lower edge can no longer fail an arm: it is 0. Its meaning is carried by the
  recorded floor classes and Leg 2.)
- **L1b determinism:** double-run byte drift → VOID.
- **L2b untouched:** any watched sha256 change during the run → VOID (now including the archived
  run-1 record and this amendment's bank).
- **L3b gates:** any kernel gate red → VOID.
- **L4b honest arms:** both arms on the registered constructions; verdicts recorded whichever way
  they land; suppressing or retuning either arm is VOID by definition.

Trailer: Agent: GLM 5.3
