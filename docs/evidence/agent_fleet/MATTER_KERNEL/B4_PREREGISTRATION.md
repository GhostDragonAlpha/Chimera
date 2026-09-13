# B4 PREREGISTRATION — the tension-only drape reference model

Rule 0: statement, prediction, falsifier — BEFORE implementation. No
measured actuals appear here; every number below is a PREDICTION derived
from cited constants (spec law: membranes are tension-only; battery B4).

## STATEMENT

A membrane carries load in TENSION ONLY — it cannot push. A cloth
dropped on a frictionless horizontal rail therefore drapes if and only
if it can reach the rail's two vertical tangent lines (the equators):
past that, a free membrane segment hangs EXACTLY vertical. So the
threshold is exact: drape requires cloth width >= half-circumference
(pi x R). The excess beyond the contact arc hangs at the lift-off
lines; no tension anywhere goes negative; material is conserved
exactly; the rail carries the whole cloth weight. Excess never
"stretches in" and the cloth never floats and never passes through.

## DERIVATION (from cited constants only)

- Rail radius R; cloth width W_c along the wrap; areal density
  sigma; gravity g REQUIRED (a known force, never defaulted — operator
  law; tests use standard gravity 9.80665 m/s^2, SI/BIPM defined).
- Symmetric equilibrium on a frictionless rail: the free segments must
  hang vertical (a membrane with no bending stiffness cannot curve
  without a normal force, and no horizontal restraint exists), so
  lift-off sits exactly at the equator, theta = pi/2, on BOTH sides.
- Contact arc = pi x R. Draping exists iff W_c >= pi x R; below that
  the cloth slides off: NO static drape — a named outcome, not a
  number.
- Excess = W_c - pi x R hangs at the two lift-off lines, excess/2 per
  side (zero-bending limit: folds pile at the tangent lines).
- Tension at each lift-off line, per unit rail length (2D membrane):
  T_e = sigma x g x excess / 2 — exactly linear in excess.
- Vertical force balance (exact): contact-arc weight sigma g pi R +
  two lift-off pulls sigma g excess = sigma g W_c. The rail carries
  the whole cloth.
- Constants: woven cotton sheeting sigma ~ 0.2 kg/m^2 typical
  (ENGINEERING_TOOLBOX textiles typical range 0.15-0.3); R and W_c are
  prescribed test geometry.

## OPEN (named, with its test)

Discrete fold PITCH (how many wrinkles the excess makes) needs bending
stiffness, D = E h^3 / (12 (1 - nu^2)) — a SHELL constant the membrane
law does not contain. The membrane model reports the excess exactly and
the fold count as OPEN. Test when shells land: measure pitch vs excess;
expected scaling pitch ~ (D / (sigma g))^(1/4) (stiffness-gravity
length). Until then no fold count is claimed.

## PREDICTIONS (test bars; R = 0.05 m, sigma = 0.2 kg/m^2, g = 9.80665)

P1. No-drape: W_c = 0.9 x pi x R -> named cannot_drape refusal; the
    model never returns a drape below the threshold.
P2. Exact threshold: W_c = pi x R -> drapes with contact arc exactly
    pi x R, excess exactly 0, lift-off tensions exactly 0.
P3. Drapes: W_c = pi x R + 0.02 -> contact arc exactly pi x R,
    lift-off exactly pi/2 both sides, excess exactly 0.02 m, every
    reported tension >= 0.
P4. Conservation: contact + excess = W_c exactly (floating-point
    exact), no stretch, no loss.
P5. Load path: rail reaction breakdown sums to sigma g W_c exactly;
    arc weight and lift-off pulls each match their derived values.
P6. Linearity: doubling the excess exactly doubles T_e
    (T_e = sigma g excess / 2).
P7. Named refusals: missing gravity -> gravity_required; zero/negative
    width, radius, or density -> invalid_* refusals. Nothing defaults.

## MUTATION PROBE

- "slide mutant" (drapes below threshold, holds the cloth with
  negative tension): P1 refuses; P3 asserts min tension >= 0.
- "stretch mutant" (consumes the excess by stretching the contact
  arc): P4 pins contact + excess = W_c at exact equality.

## FALSIFIER

Any bar fails, OR the model ever reports a drape below pi x R, OR a
negative tension, OR contact + excess != W_c, OR the rail's support
sum deviates from sigma g W_c. On failure the successor hypothesis is
named: bending stiffness matters at the tested scale (the cloth is a
shell, not a membrane) — then fold pitch becomes derivable via
D = E h^3 / (12 (1 - nu^2)) and the OPEN block closes.
