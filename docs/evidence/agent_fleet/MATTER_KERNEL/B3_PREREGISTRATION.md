# B3 PREREGISTRATION — the tensile chain reference model

Rule 0: statement, prediction, falsifier — BEFORE implementation. No
measured actuals appear here; every number below is a PREDICTION derived
from cited constants (spec law: the tensile web; battery B3).

## STATEMENT

A chain of members and bonds in series under one pull carries the SAME
force in every link — that is what "in series" means. Each link has
capacity = strength x its own load-bearing area (members: yield x area;
bonds: cure x area). The chain fails the moment the pull reaches the
SMALLEST capacity, and the failure lands on exactly that link: the
weakest link fails first, at its own capacity. Stronger links survive
because the force never reaches their capacity.

## DERIVATION (from cited constants only)

- Member yields (constants.py): steel_mild 250 MPa (ENGINEERING_TOOLBOX;
  MATWEB AISI 1020), aluminum 95 MPa (6061-T6), oak 45 MPa (ASHBY).
- Bond cure: 3.5e7 Pa per-bond data (spec worked example, as in B2).
- One chain, four links in series, all 0.01 m^2:
  steel plate 2.5e6 N | glue bond 3.5e5 N | aluminum plate 9.5e5 N |
  oak plate 4.5e5 N.
- Weakest = glue (3.5e5 N); second = oak (4.5e5 N). F_fail = 3.5e5 N.
- Remove the glue and the minimum moves to oak: F_fail = 4.5e5 N. The
  failure follows the MINIMUM, not a position in the chain.

## PREDICTIONS (test bars)

P1. Pull 3.0e5 N on the four-link chain -> holds, safety factor 7/6.
P2. Pull 4.0e5 N -> fails at the GLUE bond at exactly 3.5e5 N; oak
    (second weakest) and both metals survive.
P3. Order proof: same chain without the glue -> pull 5.0e5 N fails at
    the OAK at exactly 4.5e5 N; aluminum (9.5e5) and steel (2.5e6)
    survive. The failing link moved with the minimum.
P4. Survivor check: at failure, every surviving link's capacity is
    strictly greater than the failure force, and its carried stress
    (failure force / area) is strictly below its own strength.
P5. Linearity: halving the weakest link's area halves F_fail exactly
    (3.5e5 -> 1.75e5 N), site unchanged.
P6. Named refusals: omitted force -> force_required; zero/negative
    force -> invalid_force; empty chain -> empty_chain; non-positive
    area -> invalid_area; bond without cure -> invalid_cure; unknown
    material -> refused by the sourced-constants lookup.
P7. Exact boundary: F exactly at F_fail fails; F_fail - epsilon holds.
    No fudge margin.

## MUTATION PROBE

Two mutations must be caught:
- "max instead of min": the model would fail the steel (2.5e6 N) while
  the glue survives — P2 pins the failure force at the minimum and
  asserts every other capacity is strictly larger.
- "positional failure" (always the first link): P3 moves the failing
  link from the glue to the oak by changing the chain, so a positional
  rule breaks the bar.

## FALSIFIER

Any bar fails, OR a stronger link ever fails while a weaker one
survives, OR the failure force deviates from the weakest link's
capacity, OR the failing link follows position instead of capacity.
On failure the successor hypothesis is named: parallel load paths —
after the first failure the load REDISTRIBUTES through the surviving
network, which needs a web solver (per-link force shares), not a chain
minimum. That solver is the step from chain to web, and it keeps the
same law: computed failure, never scripted.
