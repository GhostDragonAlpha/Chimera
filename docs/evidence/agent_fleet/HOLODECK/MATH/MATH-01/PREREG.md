# PREREG — holodeck-math-01 (gen 1)

- Agent: subagent-worker-11. Slot 15, worktree E:\ChimeraWork\slot-15, branch
  astra/tasks/holodeck-math-01, base 62b8e35757c71e31d621c26b32a7c52558905b02
  (= remote tip at claim, rev 890; provision verified HEAD==base, clean; the
  provisioner confirmed 6050-file index). Scope (the ONLY writable path):
  docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01.
- Admitted from my own draft DRAFT-holodeck-math-01 (PR #67 batch; catalogue
  card MATH-01, digest b9d32319b43a, content_sha256 d7fb68e14b18e300, raw read
  retained at docs/evidence/agent_fleet/CATALOGUE_PACKET_BATCH/raw/catalogue_read/MATH-01.json).
  Dependency holodeck-gov-01 INTEGRATED (PR #77) — its evidence is the pattern
  this lane follows.
- SOURCE-ONLY lane: the deployed/repo contract state is measured from source
  text at base 62b8e357 (file line counts + sha256 recorded in RESULT.md). The
  live service at 127.0.0.1:8099 is NEVER contacted. CPU only; no GPU/model/
  engine process; no controller resources; no code outside this evidence
  directory is created or modified.
- DYAD: NOT_APPLICABLE — reference-only/source-only scope records no executed
  visible-behavior change; reason recorded here and in RESULT.md per the
  card's DYAD policy.
- This commit contains the prereg ONLY. No reference model, no controls, no
  results.

## CARD MEMBRANE (quoted verbatim from the card)

- CARD STATEMENT: Typed quantity/frame contract and reversible coordinate
  transforms
- CARD PREDICTION: Unit and frame changes preserve dimensionless predictions
- CARD FALSIFIER (named BEFORE the run, binding on both the reference model
  and the source trace): **A metre-newton comparison or undeclared
  world-unit conversion is admitted**
- CARD MATHEMATICS: SI dimensions; nondimensionalization; Buckingham Pi
- CARD THRESHOLD POLICY: derive the fixture-specific bound before
  implementation tests (done below, per row); preserve existing frozen gates
  (this lane writes no code, so no gate is touched); a catalogue prediction
  is not a preregistered numeric certificate (all numeric certificates below
  are preregistered HERE, first).

## REFERENCE MODEL CONTRACT (fixed before implementation)

A self-contained STDLIB-ONLY python module (`reference/math01_reference_model.py`
inside this evidence scope) implementing the card's INTENDED contract:

1. `Dimension`: exact SI base-dimension exponent vector over (m, kg, s) with
   `fractions.Fraction` exponents (L, M, T suffice for every control below;
   the vector is length-3 and extensible). Named derived dimensions used in
   the controls: Pa = kg·m⁻¹·s⁻², N = kg·m·s⁻², N/m = kg·s⁻², N/m² = Pa.
2. `Quantity`: immutable (value: float, dimension: Dimension). Multiplication
   and division compose values and dimensions exactly; addition, subtraction,
   equality and ordering REQUIRE equal dimensions and refuse otherwise with
   the named refusal `dimension_mismatch` (this is the metre-newton tripwire:
   `1 m == 1 N` must refuse, `1 m + 1 N` must refuse). `is_dimensionless()`.
   Nonfinite values refuse at construction (`nonfinite_quantity`).
3. `UnitRegistry`: conversions are ONLY explicit declarations (source unit,
   target unit, exact scale factor); `convert(q, target)` refuses
   `undeclared_conversion` when no declaration exists, refuses
   `conversion_dimension_mismatch` when a declaration's dimension does not
   match, refuses `contradictory_conversion` when a second declaration gives
   a different scale for the same pair. Declaring `world-unit = 1 m` makes
   metre/world-unit conversion LEGAL (the falsifier's "undeclared" is the
   refusal condition, not the conversion itself).
4. `Frame`/`Transform`: a frame is a name + declared length unit (Quantity of
   dimension m, or a declared world unit); a rigid `Transform` is an
   orthonormal 3x3 rotation R and translation t; `apply(point)`,
   `compose`, `inverse()` (= Rᵀ, −Rᵀt); transforming BETWEEN frames with
   different declared length units requires the unit conversion to be
   DECLARED, else `undeclared_frame_scale`.
5. `nondimensionalize` / Buckingham Pi: given n Quantities, build the exact
   rational dimension matrix, compute its rank k over Q and the (n−k)-
   dimensional nullspace; the Pi-group exponents are the exact rational
   nullspace basis (normalized: first nonzero exponent = 1).

## PREREGISTERED NUMBERS / THRESHOLDS (stated before ANY implementation test)

Verdict rule: each R row must reach its full N/N; any miss = the card
falsifier (or the row's named prediction) FIRED for that row, and the miss
is REPORTED, not patched around. For the reference model a fired falsifier
means the MODEL (or my reading of the contract) is wrong: the model gets
fixed and the correction is disclosed in RESULT.md with the fired run
retained; the DEPLOYED-source findings are never edited.

- R1 positive controls (model must ACCEPT): N=6/6 —
  (a) 3 m + 2 m = 5 m (dimension-equal addition);
  (b) E3d [Pa] * h [m] reduces to exactly the dimension N/m = kg·s⁻²
      (the deployed E₂=E₃d·h reduction reproduced dimensionally);
  (c) declared conversion 1 MPa = 1e6 Pa converts 2.5 MPa to 2.5e6 Pa;
  (d) declaring world-unit = 1 m, then converting 3 m to world units yields 3;
  (e) rigid round-trip: point p through T then T.inverse() returns p with
      max abs deviation <= 1e-12;
  (f) nondimensionalize(3 m, 2 m) -> both reduce to dimensionless with exact
      ratio 1.5 preserved.
- R2 metre-newton negatives (card falsifier clause 1 — model must REJECT):
  N=6/6 named `dimension_mismatch` refusals — (a) 1 m + 1 N; (b) 1 m == 1 N;
  (c) 1 m < 1 N; (d) 1 m + 1 s; (e) 1 Pa + 1 N/m (kg·m⁻¹·s⁻² vs kg·s⁻²);
  (f) 1.0 (dimensionless) + 1 m. Post-state assertions in every case: both
  operands unchanged (immutability), refusal named.
- R3 undeclared-conversion negatives (card falsifier clause 2 — model must
  REJECT): N=5/5 — (a) convert 1 m to undeclared unit "wu" refuses
  `undeclared_conversion`; (b) m -> s refuses `undeclared_conversion`
  (no declaration); (c) a declaration m->ft with wrong target dimension
  refuses `conversion_dimension_mismatch`; (d) second contradicting
  declaration m->ft (different scale) refuses `contradictory_conversion`;
  (e) MIRROR: after the correct declaration, the same conversion succeeds
  (proves the refusal is about declaration, not the unit).
- R4 reversibility of coordinate transforms (card statement): N=5/5 with
  round-trip bound <= 1e-12 max abs (DERIVED BOUND: 3 chained float64
  orthogonal products; Higham gamma for n=9 multiplications is
  9·2⁻⁵²/(1−9·2⁻⁵²) ≈ 2.0e-15, so 1e-12 carries ~500x headroom) —
  (a) pure rotation round-trip; (b) rotation+translation round-trip;
  (c) rigid chain A->B->C then C->B->A returns the original point;
  (d) inverse(inverse(T)) == T exactly (Rᵀᵀ=R elementwise exact);
  (e) NEGATIVE tie-in: transforming a point from a metre frame to a
  world-unit frame with NO declared scale refuses `undeclared_frame_scale`,
  and after declaring world-unit = 1 m the same transform succeeds.
- R5 dimensionless-prediction preservation (card prediction): N=3/3 —
  (a) aspect ratio h/L computed in metres vs in millimetres (declared
  1 mm = 1e-3 m) agrees to <= 1e-15 relative (exact power-of-ten scales:
  derivation — scale factors 1e3/1e-3 are powers of two times powers of
  five; float64 division error <= 2 eps per op, so 1e-15 carries >100x
  headroom); (b) point-pair distance invariant under a rigid frame change
  to <= 1e-12 relative (same derived bound as R4); (c) Buckingham Pi group
  COUNT invariant under re-declaring the unit system: pendulum set
  {T [T], L [L], g [L T⁻²]} -> exactly 1 Pi group with normalized exponents
  {T:+2, L:-1, g:+1} EXACT (rational nullspace, zero tolerance);
  re-running with L declared in mm gives the same exponents exactly.
- R6 deployed-source trace (card prediction judged against the DEPLOYED text
  at 62b8e357; measurement, never edited): threshold 6/6 rows each carrying
  either quoted file:line PRESENCE or measured ABSENCE (grep count 0) —
  (i)   units EXPLICIT at one boundary: tools/elastic_foundation/
        units_contract.py:5-9 (E3d [Pa], h [m] -> E2 [N/m] docstring),
        317-324 (admit_volumetric_v1 "reducing exactly once"), 357+365
        (input_modulus_unit="Pa", representation labels);
  (ii)  NAMED refusals at that boundary: UnitsReason (lines 36-54, incl.
        OUTPUT_DIMENSION_MISMATCH at 53) + UnitsRefusal (57-61);
  (iii) provenance mandatory: SourceReference/provenance classes (76-107),
        STRUCTURED_PROVENANCE_REQUIRED (51);
  (iv)  ABSENCE of typed quantity algebra: no Dimension/Quantity/dimension-
        comparison machinery anywhere under tools/ (grep count 0) — unit
        safety is carried by one boundary's labels + ad-hoc checks, so a
        metre-newton comparison cannot even be EXPRESSED there (it is
        neither admitted nor refused — it is unrepresentable, which is a
        WEAKER guarantee than the card's typed refusal);
  (v)   ABSENCE of frame/coordinate-transform machinery with a reversibility
        contract in the units layer (grep count 0 under tools/elastic_foundation);
  (vi)  ABSENCE of nondimensionalization/Buckingham-Pi machinery (grep count
        0); the deployed E2=E3d·h is a FIXED dimensional reduction, not a Pi
        engine (R1(b) of this prereg reproduces its dimension exactly).
- R7 recorded-regression cross-check: the live claim path's owner_instance
  drop (lead's known regression, fix in PR #80 review) — expected N/A: this
  card touches no claim path; recorded in RESULT.md with the reason.

## METHOD (binding on the run)

- Sequencing: THIS commit (prereg only) -> model + controls written -> runs
  executed ONCE with outputs retained verbatim under checks/*.txt -> RESULT.md
  scoreboard + limitations + integration handoff -> evidence commit -> push
  no-force -> PR -> submit_review at exact HEAD.
- All artifacts live INSIDE docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/
  (reference/, controls/, checks/); stdlib only; no network; no live service.
- Falsifier disposition rule: see Verdict rule above. The card falsifier is
  ALSO the acceptance gate for the model: if any R2/R3 refusal is missing,
  the model admitted a metre-newton comparison or undeclared world-unit
  conversion — falsifier FIRED, reported, never patched around silently.

Acceptance: NOT CLAIMED. Trailer on every commit: Agent: subagent-worker-11
