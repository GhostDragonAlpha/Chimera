# MATH-01 contract audit

**Task:** `math-contract-audit-01` (preparatory audit; this does not accept the
catalogue card or change its dependencies).

## Preregistration

**Statement:** The repository's existing unit and coordinate conventions provide
enough explicit, testable material for a typed quantity/frame contract, while
remaining gaps can be named without introducing new physical defaults.

**Prediction:** Existing code will show several local conventions (SI metres in
the material and membrane paths, glTF metres with an importer frame conversion,
and a global/local precision helper), but no single enforcement boundary that
proves reversibility and dimensional consistency for all callers.

**Falsifier:** A read-only inventory finds a single authoritative typed quantity
and frame API used at every inspected physics, mesh, and renderer boundary,
with executable tests proving round-trip transforms and rejecting undeclared
unit/frame conversions. If that is observed, the predicted gap is falsified.

## Scope and method

Inspect only existing source, tests, and documentation for units, dimensions,
coordinate frames, and conversion boundaries. Run only bounded CPU tests or
small pure-Python probes already implied by those contracts. Record source
identity, commands, observed results, and limitations under
`docs/evidence/master_completion/MATH01/`. No engine, GPU, DYAD, catalogue, or
Master List operation is in scope.

## Acceptance boundary

This document reports an audit and concrete follow-on envelope. It does not
claim MATH-01 acceptance, derive new constants, or replace the catalogue card's
required independent reference/benchmark, negative controls, reproduction
commands, source identity, preserved evidence, limitations, and integration
contract.

