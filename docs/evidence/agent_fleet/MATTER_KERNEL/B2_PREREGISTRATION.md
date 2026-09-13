# B2 PREREGISTRATION — the glue reference model

Rule 0: statement, prediction, falsifier — BEFORE implementation. No
measured actuals appear here; every number below is a PREDICTION derived
from cited constants (spec law: bonds are materials; battery B2).

## STATEMENT

A bond is a THIRD MATERIAL between two membranes: the glue, with its own
cure strength, independent of the members it joins. Under a pull, every
load path carries capacity = strength x its own load-bearing area, and
the line with the SMALLEST capacity fails first. Two steel membranes
bonded with weak glue therefore fail AT THE GLUE LINE, at
F_fail = cure_strength x A_glue — never in the steel, and never holding
past the glue's capacity.

## DERIVATION (from cited constants only)

- Mild steel yield 250 MPa (constants.py: ENGINEERING_TOOLBOX steels;
  MATWEB AISI 1020).
- Bond cure strength is per-bond data (KERNEL_SPEC.md 2: cure_strength);
  the spec's worked example: cured PVA-style glue, 3.5e7 Pa (35 MPa).
  The constants table's PVA row (yield 30 MPa, ASHBY polymers) brackets
  the same order — the bond definition value is authoritative per bond.
- Capacity = strength x area. Two steel plates, 10 cm x 10 cm =
  0.01 m^2 each: steel capacity = 250e6 x 0.01 = 2.5e6 N.
- Glue line at the same 0.01 m^2 overlap, cure 3.5e7 Pa:
  glue capacity = 3.5e7 x 0.01 = 3.5e5 N — 7.14x weaker than the steel.
- Therefore: F_fail = 3.5e5 N, site = glue line, and the steel sits at
  35/250 = 14% of its own yield when the glue line lets go. Pulling
  anywhere below 3.5e5 N holds with safety factor F_fail / F.

## PREDICTIONS (test bars; steel = mat.steel_mild, cure = 3.5e7 Pa)

P1. Holds below cure: pull 3.0e5 N -> holds, safety factor 7/6.
P2. Breaks AT the glue line: pull 4.0e5 N -> failure, site "glue_line",
    failure force exactly 3.5e5 N = cure x A_glue; steel unfailed.
    The joint cannot hold past 2x cure capacity (7.0e5 N): the recorded
    failure force is the capacity, so "holds past 2x" is impossible.
P3. Linearity in glue area: halve A_glue -> failure force exactly
    halves (1.75e5 N), site unchanged, steel still unfailed.
P4. Anti-always-glue control: bond with cure 3.0e8 Pa (> steel 250 MPa)
    -> the joint fails IN THE STEEL at 2.5e6 N, site "mat.steel_mild".
    The model reads capacities; it never blames the glue by name.
P5. Named refusals: omitted force -> force_required; zero/negative
    force -> invalid_force; non-positive glue area -> invalid_area;
    missing cure -> invalid_cure; unknown material -> refused by the
    sourced-constants lookup.
P6. Exact boundary: F exactly at capacity fails; any F strictly below
    holds. No fudge margin, no rounding shelter.

## MUTATION PROBE

If the glue-line capacity wrongly used the MEMBER's yield (250e6 Pa)
instead of cure_strength, P2's failure force would read 2.5e6 N — the
bar detects the 7.14x divergence by asserting the failure force equals
cure x A_glue AND is strictly below every member capacity. The P4
control proves the reverse mutation (always pinning at the glue) is
also caught.

## FALSIFIER

Any bar fails, OR the model ever fails the steel while the glue line
has strictly lower capacity, OR failure force deviates from
cure x A_glue, OR the strong-glue control blames the glue. On failure
the successor hypothesis is named: a joint-efficiency factor (adhesive
vs cohesive failure) calibrated per bond geometry by measurement.
