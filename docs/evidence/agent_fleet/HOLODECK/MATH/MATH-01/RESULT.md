# RESULT — holodeck-math-01 (gen 1)

Agent: subagent-worker-11 · slot 15 · worktree E:\ChimeraWork\slot-15 · branch
astra/tasks/holodeck-math-01 · base 62b8e35757c71e31d621c26b32a7c52558905b02
(= remote tip at claim, rev 890; provision verified HEAD==base, clean; no
reconcile needed). CPU only; no GPU/model/engine process; no controller
resources; the live service at 127.0.0.1:8099 was NEVER contacted. No file
outside docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/ was created or
modified (the deployed sources were read in place).

## SOURCE IDENTITY (the deployed contract, read-only reference text at base)

- tools/elastic_foundation/units_contract.py, 628 lines, sha256
  c9384c0952856175dda07eaead01ffe70651baccd6eaf2e28bd78d8113abd4b1
- tools/elastic_foundation/law.py, 219 lines, sha256
  b8e32ececd4f09b1d5a7af74e7ecffe2b00fa262f50a061d2f6f788e49a41b18
- docs/THE_ELASTIC_UNITS_CONTRACT.md, sha256
  3cedb343ea0f76878c5a0cbf66ee526806ce54a9e1a20cacc560b556fbf5c95b
- All read from the working tree at HEAD 62b8e357 (verified).

## DELIVERABLES

- `reference/math01_reference_model.py` — independent STDLIB-ONLY model of the
  card's INTENDED contract: exact rational SI dimensions (L, M, T) with named
  derived dimensions (Pa, N, N/m); immutable typed Quantity whose every
  cross-dimension operation (add, subtract, ==, ordering — including a
  metre-newton comparison) refuses `dimension_mismatch`; declared-only unit
  registry (`undeclared_conversion`, `conversion_dimension_mismatch`,
  `contradictory_conversion`); rigid reversible frames
  (`undeclared_frame_scale` for cross-unit frames without a declared scale;
  inverse = (Rᵀ, −Rᵀt)); exact-rational Buckingham-Pi nullspace with
  primitive-integer normalization.
- `controls/run_controls.py` — executes preregistered R1-R6; every refusal
  recorded verbatim with its named reason; every bound computed and printed.
- `checks/r1_positive.txt` — R1 HOLDS 6/6 (incl. E3d[Pa]·h[m] → exactly
  N/m = kg·s⁻² at 2e9, reproducing the deployed E₂=E₃d·h reduction
  dimensionally; declared MPa→Pa; declared world-unit conversion; rigid
  round-trip 0.0e+00 deviation; exact nondimensionalization ratios).
- `checks/r2.txt` — R2 HOLDS 6/6: every metre-newton comparison path refused
  `dimension_mismatch` verbatim ((a) +, (b) ==, (c) <, (d) m+s, (e) Pa+N/m,
  (f) bare dimensionless literal); operands unchanged after every refusal
  (immutability). CARD FALSIFIER CLAUSE 1: REFUSED everywhere.
- `checks/r3.txt` — R3 HOLDS 5/5: undeclared unit, undeclared 's',
  wrong-dimension declaration, contradicting re-declaration all refused with
  the named reasons; the mirror case (declaration added → conversion
  succeeds) proves the refusal is about DECLARATION, not the unit.
  CARD FALSIFIER CLAUSE 2: an undeclared world-unit conversion is REFUSED.
- `checks/r4.txt` — R4 HOLDS 5/5: round-trips at 0.0e+00 measured deviation
  (bound 1e-12), inverse-of-inverse bit-exact on the pure-rotation fixture,
  chain A→B→C→A exact within bound, and the cross-unit frame refused
  `undeclared_frame_scale` until the scale was declared, then succeeding on
  the SAME transform object.
- `checks/r5.txt` — R5 HOLDS 3/3: aspect ratio invariant m vs mm at
  0.0e+00 relative (bound 1e-15); point-pair distance invariant under a
  rigid frame change at 0.0e+00 relative (bound 1e-12); Buckingham Pi of
  {T, L, g} → exactly 1 group with exponents {T:+2, L:−1, g:+1} EXACT
  (= T²g/L), invariant under unit re-declaration.
- `checks/r6_source_trace.txt` — the deployed-state measurement (below), 6/6.
- `PREREG.md` — committed FIRST (a7028971), untouched since.

## PREDICTION SCOREBOARD (card prediction / prereg rows)

| row | prediction (fixed in PREREG before any run) | verdict |
|-----|---------------------------------------------|---------|
| R1 | model accepts 6/6 legal typed-algebra sequences | HOLDS 6/6 |
| R2 | model refuses every metre-newton comparison path | HOLDS 6/6 |
| R3 | model refuses every undeclared-conversion path; declaration legalizes | HOLDS 5/5 |
| R4 | transforms reversible within the derived 1e-12 bound; cross-unit frames fail closed | HOLDS 5/5 |
| R5 | dimensionless predictions preserved across unit and frame changes | HOLDS 3/3 |
| R6 | deployed-state trace matches the preregistered presence/absence rows | HOLDS 6/6 |
| R7 | owner_instance claim-path regression N/A for this card | N/A (below) |

**CARD FALSIFIER (a metre-newton comparison or undeclared world-unit
conversion is admitted): NOT FIRED** — in the reference model both clauses
are refused with named reasons on every executed path; in the deployed source
neither can even be expressed (no quantity algebra exists there — see (iv)).

## R6 — THE DEPLOYED STATE vs THE CARD (measured, from SOURCE)

What EXISTS at base (quoted file:line in r6_source_trace.txt):
- (i) units are EXPLICIT at exactly one boundary: units_contract.py:5-9
  (E3d [Pa] with h [m] → E2 [N/m] duck-typed kernel view), :317-324
  (admit_volumetric_v1 "reducing exactly once"), :357/:365 (input_modulus_unit
  "Pa", representation labels);
- (ii) a NAMED fail-closed refusal vocabulary exists there: UnitsReason
  (units_contract.py:36-54, incl. OUTPUT_DIMENSION_MISMATCH at :54) +
  UnitsRefusal (:57-61);
- (iii) provenance is mandatory (SourceReference/structured provenance
  :76-107; STRUCTURED_PROVENANCE_REQUIRED at :51).

What does NOT exist (measured absence):
- (iv) NO typed quantity algebra anywhere under tools/: zero
  `class Quantity`/`class Dimension` definitions. The preregistered grep
  pattern produced exactly 1 hit — units_contract.py:54
  `OUTPUT_DIMENSION_MISMATCH = "output_dimension_mismatch"` — which is the
  boundary's own output-shape refusal CONSTANT (cited as PRESENT semantics in
  row (ii)), not typed algebra. Consequence, measured not judged: at the
  deployed boundary a metre-newton comparison is UNREPRESENTABLE rather than
  REFUSED — a weaker guarantee than the card's typed contract, which refuses
  it by construction everywhere (R2).
- (v) NO frame/coordinate-transform machinery with a reversibility contract
  in the units layer (measured count 0 under tools/elastic_foundation).
- (vi) NO nondimensionalization / Buckingham-Pi machinery (measured count 0
  under tools/); the deployed E₂=E₃d·h is a FIXED dimensional reduction, not
  a Pi engine — and R1(b) reproduces its dimension exactly inside the model.

## DISCLOSED DEVIATIONS DURING THE RUN (retained, never patched silently)

1. RUN1 HARNESS CRASHES (not falsifier fires): checks/r2.txt.run1-HARNESS-CRASH-typerror-no-radd.txt
   and checks/r4.txt.run1-HARNESS-CRASH-compose-arg-order.txt. R2(f) exposed a
   missing reflected-operator seam (float + Quantity leaked TypeError instead
   of the named refusal) — fixed in the model by adding `__radd__`/`__rsub__`
   that refuse `dimension_mismatch` (the card-correct behavior; a bare float
   is not a Quantity). R4(c) was a runner-side argument-order slip (compose
   semantics are outer∘inner). Both fixed; the re-runs are the retained R2/R4
   checks; the crashed outputs are retained verbatim.
2. PREREG PATTERN SUBSTRING FALSE POSITIVE, disclosed per the
   run1-CHECKER-BUG precedent: the preregistered row (iv) pattern
   (`class Quantity|class Dimension|dimension_mismatch`) measures 1 hit — the
   boundary's own refusal-name constant (row (ii) PRESENCE). The row's
   discriminating measurement (zero actual class definitions) is printed in
   the same check file; the raw pattern result is retained alongside. The
   prereg text is untouched.
3. MODEL-CONTRACT CLARIFICATION (prereg-internal, disclosed): the contract
   paragraph's parenthetical described Pi normalization as "first nonzero
   exponent = 1", while preregistered row R5(c) fixes the certificate as the
   EXACT primitive-integer exponents {T:+2, L:−1, g:+1}. The binding number
   is R5(c); the model normalizes to primitive integer vectors, under which
   the certificate is exact. Both describe the same one-dimensional group
   space; nothing was measured differently because of the wording.

## R7 — owner_instance CLAIM-PATH REGRESSION: N/A

The lead's known regression (live claim path drops owner_instance; fix in PR
#80 review) touches the controller claim path. This card is "Units and
coordinate algebra": its realization never reads, writes, or models the claim
path — no deviation to record. (The evidence-only scope holds no code.)

## DYAD: NOT_APPLICABLE

Per the card's DYAD policy: "Reference-only or source-only scope records
NOT_APPLICABLE with reason." This lane executed no integrated change to
visible behavior — it produced a reference model and source measurements
only; there is no image or behavior for the image/question workflow to judge.

## LIMITATIONS

- The reference model is a RECORD of the intended contract, not integrated
  product code: float64 values with exact rational DIMENSIONS (value algebra
  is not exact arithmetic); rotation round-trips are bounded (derived Higham
  gamma_9 ≈ 2.0e-15; tests ran at 0.0e+00 measured deviation on the chosen
  fixtures — the 1e-12 bound carries ~500x headroom, not proof of universal
  exactness).
- Dimensions cover (L, M, T): sufficient for every control on this card
  (all quoted deployed quantities are L/M/T); temperature/current/mol/candela
  are the documented extension points (the vector is fixed-length 3 by
  design here — a production typed contract should widen it).
- UnitRegistry converts through declared scales only; there is no unit-string
  PARSING (no "m/s" composition syntax) — units are declared atoms.
- The deployed-state absence measurements are grep-scoped to tools/ (and
  tools/elastic_foundation for row (v)); they do not index docs prose.

## REPRODUCTION COMMANDS (from the repo root of this worktree, Python 3.14)

```
python docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/controls/run_controls.py r1
python docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/controls/run_controls.py r2
python docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/controls/run_controls.py r3
python docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/controls/run_controls.py r4
python docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/controls/run_controls.py r5
python docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/controls/run_controls.py r6
```
Each exits 0 iff its row holds at full N/N. Raw outputs retained under
`checks/` were produced by exactly these commands at HEAD.

## INTEGRATION CONTRACT AND AUTONOMOUS HANDOFF

- This lane's deliverable is the evidence set; the reference model is NOT
  proposed for direct import into tools/ (that would be a scoped engineering
  change requiring its own gates). Acceptance of this lane = the evidence
  records above, NOT_CLAIMED until lead review.
- Handoff to the next lanes (card-family candidates, in dependency order):
  1. A scoped engineering lane could adopt the typed-quantity refusal
     vocabulary at NEW boundaries (the elastic boundary already speaks named
     refusals — UnitsReason — so the vocabulary transfer is small).
  2. A frame-contract lane (world-unit declaration as first-class registry
     state) matches the engine's world-unit practice; the undeclared-scale
     refusal (`undeclared_frame_scale`) is the falsifier-carrying behavior.
  3. A nondimensionalization lane could wrap the elastic derivations
     (DERIVATION.md) with the exact-rational Pi engine for future fixtures.
- Frozen gates preserved: this lane wrote no code; no gate was touched.

Acceptance: NOT CLAIMED. Trailer on every commit: Agent: subagent-worker-11
