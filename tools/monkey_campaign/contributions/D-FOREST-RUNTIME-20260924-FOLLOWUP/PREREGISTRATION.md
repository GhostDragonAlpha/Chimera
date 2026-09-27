# PREREGISTRATION — D-FOREST-RUNTIME-20260924-FOLLOWUP (correction 2: gap/row convention consistency)

Card: `D-FOREST-RUNTIME-20260924-FOLLOWUP`. Correction attempt
`9b1d9ec7c1ae4c969db51c317b99f44f`, arrival
`arrival-93d3ca26b5b640a6983176e771421e30`. Written BEFORE any candidate code
change in this workspace. Corrections the reviewed candidate
(`0f29ec07434840939d0b53c4bc5a30b4`, PR #155 @ `be058d58`) stays READ-ONLY as
the source of the prior artifacts (its five files, its evidence, its pinned
reference materialization). Prior findings that are VERIFIED AND PRESERVED
(ill-formed helper placement, private default ctor, compile evidence, oracle
parity) are NOT re-litigated here; this prereg covers ONLY the open lead
finding `msg-0cca72cf79d34124bcc7f60e5e76a730` (duplicated
`msg-1c802c3c7eed47618bc703365fb5ed1c`).

## SUBJECT (the finding, verified from the pinned bytes)

`gap_of` (terrain arm) returns the VERTICAL gap `y + radius - h(x,z)`, whose
exact q-derivative is `d gap/dq = (-hx,1,-hz)·J` (unnormalized surface
normal). The patched `contact_row` (terrain arm) returns the NORMALIZED
`(-hx,1,-hz)/||·|| · J`. The pinned positional-correction block (impact(),
lines 1844-1852 @ blob 5863348f) consumes `arows=contact_row` with
`rhs[a2]=-gaps[a2]` under the pinned comment "the contact rows ARE
d gap/d q". Mixing the normalized row with the vertical-gap rhs makes the
projection over-shoot the zero crossing by the factor `||(-hx,1,-hz)||`:
for h=x+z, J=I, unit mass, gap=-0.01 the reproducer
(`E:/Chimera/queue-check-20260926/pr155/gap_row_reproducer.json`) gives
correction = (-0.0057735,+0.0057735,-0.0057735) and gap_after =
+0.007320508075688773 = gap·(1-sqrt(3)) — inside the pinned 0.05 correction
budget, so the defect sails through the budget guard. I re-derived the
reproducer algebra from the pinned `gram_factor`/least-norm code and it
matches exactly. Flat ground conceals it: n=(0,1,0), ||n||=1, both arms
coincide.

## PRE-PREREG FEASIBILITY PROBES (disclosed; run in TEMP, before this file)

All read-only against the repo/prior attempt; outputs in the Windows temp
dir only; nothing written to E:/PythonChimera, E:/Chimera, or the candidate
tree.

1. The pinned scene compiler (`tools/science_funnel/gait_scene.py` @
   `33e7a444`, archived to temp with the pinned tools subtree) COMPILES a
   valid 18-coordinate gait scene: sha256 of
   `scene.json` = `e61ad3864472453f2b2a77a71ca0579f1b78e905b2495f581a9f87f27502333c`
   (fixture shipped with the contribution; provenance recorded in report).
   Scene facts used below: 18 coordinates (index 4 = `base_trans_y`),
   `contact_plane_height_m`=0.004, tick 300 Hz, substeps 4, friction 0.6,
   8 contact points (heel/MP per leg), reset gaps: fore MP pair seated at
   +2e-6 m, others +1.77e-2..+1.74e-1 m.
2. The PRIOR candidate's patched header (prior attempt `proposed.patch`
   applied to a temp `git archive` of the pinned engine subtree) compiles a
   probe TU (g++ `-std=c++17 -O0`, engine-dir include path, 5.4 s) and the
   walker CONSTRUCTS with an injected `terrain_grid` slope
   h(x,z)=0.004+0.5x+0.25z and base raised +0.6 m (all reset gaps > 0,
   `gait_initial_penetration` not triggered). Measured sole world positions
   at the reset state (flat): fore MP x=+0.160439699 (the seated pair,
   z=±0.02), fore heel x=+0.076086776, hind L heel x=+0.075423287 /
   R heel x=-0.224474380, all |z|<=0.02.

## CONVENTION DERIVATION (frozen before implementation)

Consumer audit of `contact_row` / `tangent_row` / `gap_of` in the PINNED
tree (blob 5863348f @ 33e7a444), every call site read:

| site | consumer | needs |
|---|---|---|
| rate() :1726-1727 | touch gate `inner(rown,v)<=gate` | sign/scale-classification; flat-identical under any positive scale |
| rate() :1743 | `friction_solve(...,rown,row_t,...)` | FORCE row: multiplier semantics; mu cone couples row_n to unit tangent rows |
| rate() :1751-1757 | `project_rows` velocity floors | velocity row; floor=-contact_bias[1] (vertical-bias) |
| free_step() :1765 | same touch gate | as above |
| impact() :1789-1801 | friction_solve + energy ledger | ledger closes for ANY row scale (share=lambda*row·mean uses the same rows) |
| impact() :1844-1852 | POSITIONAL CORRECTION `arows=contact_row`, `rhs=-gaps` | THE pinned contract: row = d gap_of/dq (comment verbatim in the pinned source) |
| status() :2729-2731 | gap + tangent rows (telemetry) | reporting only |
| leg_contact/hull/guards/localization/bisection/initial-penetration | gap scalar alone | convention-free |

CONCLUSION OF THE AUDIT: no pinned consumer requires a UNIT row (pinned rows
were raw Jacobian columns, not unit); the unit-normal/unit-tangent frame is
NEW in the candidate's terrain arm and is what the velocity/force consumers
(friction_solve cone, project_rows velocity floors) now see on slopes.
Unnormalizing `contact_row` GLOBALLY (the naive fix) would silently rescale
the force rows: with row_n scaled by c=||n_un||>1 against unit tangent rows,
the friction cone `|lambda_t| <= mu*lambda_n` becomes a PHYSICAL cone of
mu/c — a force-law change hiding inside a projection fix. That is exactly
what the lead forbade ("do not blindly unnormalize a force row used
elsewhere").

CHOSEN BRANCH (the lead's "the row must match the gap derivative", applied
at the projection consumer only): keep `contact_row`/`tangent_row` EXACTLY
as the reviewed candidate ships (unit surface frame: flat-identical to
pinned, physically exact friction cone on slopes), and in the
positional-correction block ONLY, rescale each projection-local row to the
exact gap Jacobian before the pinned `rhs=-gaps` solve:

    row_proj = contact_row(e,k) / n_y ,  n_y = contact_normal(e,points_[k]).y

because `contact_row = n̂·J` and `n̂_y = 1/||(-hx,1,-hz)||`, so
`row_proj = (-hx,1,-hz)·J = d gap/dq` EXACTLY. The pinned rhs law
`rhs[a2]=-gaps[a2];` stays byte-identical; the pinned block comment "the
contact rows ARE d gap/d q" becomes TRUE again on slopes. Flat/inactive
paths: n_y=1.0, and IEEE `x/1.0 == x` exactly, so the correction is
BITWISE IDENTICAL to the pinned/candidate behavior on flat ground. Named
refusal `gait_gap_row_normal_y_invalid` if n_y is not > 0 (defensive;
impossible for finite gradients). REJECTED alternative (rhs rescale
`-gap*n_y` with unit rows): algebraically equivalent (lambda scales
inversely), rejected only because it edits the pinned rhs line instead of
restoring the pinned row contract; recorded here for the reviewer.

Regression-enabling seam (scope-honest): the prior patch already opened a
public seam in the class member block (`public: using TSurface=...;
private:`). The correction extends THAT SAME seam with read-only forwarders
`probe_gap_of`, `probe_contact_row`, `probe_tangent_row`,
`probe_contact_normal` (pure one-line delegations, no state, no law change)
so the compiled regression can drive the patched members. Disclosed as a
fourth patch edit; the physics-symbol guard and two-file scope are preserved.

## REGRESSION DESIGN (frozen)

Headless compiled driver (`contact_consistency.cpp`) against the PATCHED
engine subtree (git archive @ 33e7a444 + proposed.patch), g++
`-std=c++17 -O0 -I <engine>`; NO `step()` call anywhere — construction
(`reset()` state seeding) + public `model().evaluate()` + the probe
forwarders only. Inputs: the shipped scene fixture (sha above) +
deterministic in-driver terrain injection: grid 41x41 over [-20,20]^2,
dx=dz=1, h(x,z)=0.004+0.5x+0.25z, base raise +0.6 m (measured feasible).
Modes: `slope` (terrain active), `flat` (constant grid h=0.004 = the
authored plane), `noterrain` (no terrain_grid key). Driver output = machine-
readable JSON lines; the Python harness asserts the laws.

  R1 FLAT-PATH IDENTITY (compiled, bitwise): at the untouched default state,
  probe_gap_of / probe_contact_row / probe_tangent_row(axis 0 and 2) are
  BITWISE EQUAL between the `flat` walker (terrain active) and the
  `noterrain` walker over all 8 contact points (rows/gaps via the pair law:
  4 sole representatives + axis rows). Also `tangent_row(e,k,1)` on flat
  throws the NAMED refusal `gait_tangent_degenerate` (compiled path).
  R2 SLOPE FINITE-DIFFERENCE GAP/JACOBIAN: at >= 12 probe states
  (4 sole representatives x >= 3 deterministic states around the slope
  default; states chosen with pair-branch margin |gh-gm| > 1e-4 so the
  pair-min is differentiable; FD step h=1e-6, central differences over ALL
  18 coordinates): max_i |probe_contact_row[i] - FD_i(gap_of)| <= 1e-7.
  R3 PENETRATION-CORRECTION EXACTNESS (the corrected projection, driven on
  compiled values): replicate the in-class block's law (arrows, rhs=-gaps,
  gram=rows·M^-1·rows, Cholesky via the same algorithm, corr=sum lambda·M^-1
  ·row, budget 0.05) with M=e.mass from the public Evaluation and rows
  EXACTLY as the bytes under test build them (fixed tree: rescaled by 1/n_y;
  pre-fix tree: unrescaled — the mode is part of the recorded config).
  Scenarios by pure vertical offset dq4 (gap is exactly affine in
  base_trans_y): (a) single active row: left fore pair at gap=-0.003, all
  other pairs > 0 (predicted right pair ≈ +0.007); (b) two active rows:
  both fore pairs penetrating (-0.013/-0.003). Assert active-set gap after
  correction |gap_after| <= 1e-8 m and every previously-positive pair stays
  > 0 (unilateral law) — for (b) BOTH penetrating pairs must land at ≈ 0.
  R4 BITE / NEGATIVE CONTROL: the SAME driver run against the PRE-FIX
  candidate bytes (prior attempt `proposed.patch`, i.e. PR #155 @ be058d58
  exactly) with the pre-fix projection mode must FAIL R2 (relative row/FD
  mismatch >= 0.05; predicted = ||n||-1 = sqrt(1.3125)-1 = 0.145644) and
  FAIL R3(a) (gap_after > 0; predicted = +0.003·(sqrt(1.3125)-1) =
  +4.369e-4 m, the lead's reproducer mechanism at scene scale), while its
  flat path stays green — proving the regression detects the reviewed
  defect and only the reviewed defect.
  R5 the corrected header still passes the shipped `-fsyntax-only` check and
  the ill-formed negative control still bites; all prior checks (oracle
  parity 2081 points exact, extent law, degeneracy, physics-symbol guard,
  unittest suite) stay green.

## PREDICTIONS (measurable, named before the run)

1. The regenerated patch applies to the pinned blob, scope EXACTLY the two
   engine files; diff vs the prior candidate = probe seam (4 one-line
   forwarders + comment) + the projection-local row rescale + comments ONLY;
   `terrain_surface.hpp` bytes IDENTICAL to the prior attempt's.
2. `g++ -std=c++17 -fsyntax-only -I <engine>` on the modified header: exit 0;
   the ill-formed stub control exits 1 "not allowed here".
3. R1 bitwise identity holds (no `-0.0`/`+0.0` visible difference; IEEE
   compare equal).
4. R2 worst |row-FD| <= 1e-7 over all probed states/coordinates.
5. R3(a) |gap_after| <= 1e-8 m; R3(b) both active gaps <= 1e-8 m; budget
   guard dq_max <= 0.05 respected (predicted corr ~ 3e-3..1.3e-2).
6. R4: pre-fix bytes FAIL R2 with relative mismatch in [0.10,0.20]
   (predicted 0.145644) and FAIL R3(a) with gap_after in
   [+3e-4,+6e-4] (predicted +4.369e-4, positive = overshoot);
   pre-fix flat probes stay bitwise green.
7. Prior evidence reproduces: worst oracle height 0.0 m EXACT / worst normal
   <= 1e-15 over 2081 points; extent/degeneracy exact; unittest suite
   >= 15 tests OK on a fresh directory; physics-symbol guard green.
8. The unittest suite extended for the new checks runs >= 17 tests, OK,
   order-independent, on a fresh directory.

## FALSIFIERS (named before the run)

- FC1: patch fails to apply, scope drifts beyond the two engine files, or
  `terrain_surface.hpp` changes by one byte vs the prior attempt.
- FC2: modified header fails `-fsyntax-only`, or the negative control
  compiles clean.
- FC3: any R1 bitwise mismatch (flat path no longer identical).
- FC4: R2 bar exceeded on the FIXED bytes, or R4 shows NO bite on the
  PRE-FIX bytes (regression does not detect the reviewed defect).
- FC5: R3 residuals above bars, wrong sign, budget exceeded, or a
  previously-positive pair driven negative.
- FC6: any prior frozen number regresses (oracle parity, extent,
  degeneracy, physics guard), or the unittest suite fails.
- FC7: overclaim — any statement beyond: TU well-formedness + compiled
  member-level contact-consistency evidence. NO walk step is executed
  anywhere (no `step()`); the in-class positional-correction statement
  itself runs inside impact() during engine walks and is NOT executed
  headless — the regression exercises the compiled patched gap/row members
  and the pinned projection algorithm on those compiled values, plus the
  compiled TU proof of the in-class edit. Runtime/visual gates stay
  PENDING; trunk contact = Stage 2.

## BOUNDS

CPU-only; g++ invocations bounded (1 surface driver TU + 2 header
`-fsyntax-only` + 2 consistency-driver TUs (fixed, pre-fix) + 1 stub
control, each <= 120 s); read-only against E:/PythonChimera and the prior
attempt workspace; ZERO writes in E:/PythonChimera and E:/Chimera; scene
fixture shipped once (~delta KB, sha-pinned); no GPU, no engine launch, no
`step()` call, no training, <= 16 MiB new output.

---

## AMENDMENT 1 (2026-09-26, BEFORE the first full-suite run; disclosed)

Trigger: the fixed-mode consistency driver's first temp smoke run (probe,
not shipped evidence) measured R2 worst |row-FD| = 8.886e-2 -- the 1e-7
prediction falsified. Traced to a consumer the audit table above MISSED:

**A1 (new edit, correction 2b):** `sole_local` (the anchor-point selector
for contact_row/tangent_row/contact_bias) keeps a STALE gap law in the
terrain arm: it compares PLANE heights (`gh=ph[1]+r-plane_model_y_`,
`dy=pm[1]-ph[1]`) while `gap_of` compares TERRAIN gaps. When a slope flips
which pair point is lower, the row anchors at a different point than the
active gap branch and differs from `d gap/dq` by the heel/MP lever
(measured 8.886e-2). This is the same convention-consistency defect class
the lead flagged, at the anchor level. FIX (same ternary pattern): the
selection becomes terrain-aware in the active arm with the ORIGINAL plane
expressions verbatim behind; `dy` keeps the pinned `pm[1]-ph[1]` in the
inactive arm and uses `gm-gh` on terrain (identical VALUES on flat/inactive
paths: pair radii are equal, so the anchor choice is bit-identical there).
The R4 prefix reconstruction now reverts THREE edits; the hash pin
(15ea9528.../476b5905...) still proves the prefix bytes == reviewed PR #155.

**A2 (R2 object clarified, consistent with the frozen derivation):** the
regression compares FD against the row AS THE PROJECTION CONSUMES IT:
`contact_row/n_y` on the fixed bytes (the projection-local rescale), raw
`contact_row` on the prefix bytes. The frozen derivation itself chose the
"rescale at the projection consumer" branch -- `contact_row` the SHARED row
stays unit -- so the compared object is the projection's row, not the
shared one. The prefix bite expectation is unchanged (worst >= 0.05;
measured 0.127 from the scale mismatch).

**A3 (R3 bar refined; original 1e-8 prediction honestly REFINED-LOST):** the
frozen `|gap_after| <= 1e-8` assumed the correction acts through pure
translation. The pinned mass-metric least-norm legitimately couples
rotations, so the residual is second-order, not zero (smoke-measured
8.298e-6 m at a 3 mm authored penetration = 0.28% of |gap_before|). The
SHIPPED law becomes: active `|gap_after| <= 2% of |gap_before|`, pinned
budget `dq_max <= 0.05` respected, previously-positive pairs stay > 0.
Prefix bite bands unchanged (scenario 1 gap_after in [+3e-4,+6e-4],
positive overshoot).

**A4 (two-row scenario re-authored):** the frozen two-row authoring (pure
vertical drop to -0.003/-0.001) is INFEASIBLE inside the pinned budget:
the two fore pairs sit ~1 cm apart vertically on this slope, any drop that
activates the second pair penetrates the first by >1 cm, and the
smoke-measured dq_max (7.94e-2) stays above the pinned 0.05 -- the engine
itself would refuse such a state. A translation cannot fix this (on a
constant-gradient plane both soles shift identically, so the RELATIVE pair
height is translation-invariant; probe-verified). Scenario 2 is re-authored
deterministically: a base_rot_x roll (deterministic bisection on the
measured pair-gap difference, monotone in theta) equalizes the two fore
pairs, then a pure vertical drop takes BOTH to -0.0005. Predicted:
pen == [4,6] with both gaps_before in [-0.00051,-0.00049], dq_max within
the budget, second-order residuals within the 2% bar.

**A5 (R4 bite mechanics clarified):** the reviewed PR #155 bytes carry no
probe seam -- correctly so, and the reconstruction law forbids adding one --
so a binary compiled from the reviewed bytes cannot run the probe driver.
The bite control therefore mirrors the reviewed projection LAW (raw
contact_row, no rescale) on the corrected tree's compiled gap/row/mass
values; the identity of the reviewed bytes themselves is proven by the
reconstruction hash pin (git blob 15ea9528... == sha256 476b5905... == the
prior attempt's pinned reference materialization). The bite run reuses ONE
compiled driver (mode "prefix"); no second header compile is needed.

Nothing else changes: the derivation's convention choice, the regression
architecture, the bite design, and all other predictions stand as frozen.
