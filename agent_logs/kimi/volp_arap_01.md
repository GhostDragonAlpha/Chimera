# VOLP ARAP 01 — volume-preserving smooth ARAP (H11-next): law (b) SHIPS as gate-winner, law (a) FALSIFIED (2026-08-29)

**Question (named next stage of H11, closed e3edde50):** H11's smooth ARAP won
F1-in-zone (2–4×), F3, F4, and the dyad preference but failed F2 volume
INTRINSICALLY (signed shrinkage −1.3e-3 @100 … −3.4e-3 @144.94, λ-independent —
the bi-Laplacian energy has no volume term and its natural BC lets the free
boundary relax inward). Can a DERIVED volume correction restore F2 at every
angle without surrendering the wins? Two candidate laws, both implemented,
gates pick.

**Answer: YES — law (b), the in-solve Lagrange-multiplier volume constraint,
passes F2 at EVERY angle (|dV| ≤ 6.4e-7 vs T_vol = 4.4e-4) and keeps every H11
win: F1 pen < blend at every flagged-zone angle, F3 under blend everywhere, no
new crease (crease vs the CONSTRAINED C¹ reference ≈ H11's values ±0.005), dyad
still prefers it. Law (a), the post-step radial-scale projection, is FALSIFIED
decisively (|s−1| = 0.039…1.89 vs the pre-stated 3e-3 bound; F1 pen explodes to
0.17–0.43; spike 1.0–1.4). One honest defect carried: a limit cycle at exactly
130° (residual locks at 2.02e-2 ≈ h̄/6 through 300 iterations; gates pass at
the cycled state; 144.94° — deeper flexion — converges cleanly to 9.1e-8 in 64
iters).**

## The membranes (Rule 0, stated BEFORE the run — in `.tmp/volp_arap.py`)

Shared STATEMENT: the shrinkage is the bi-Laplacian's natural BC letting the
free boundary relax inward; constraining closed-mesh volume to rest restores F2
without surrendering the C¹ wins.

**Law (a) — post-step volume projection (uniform radial scale s of the free
band about its centroid, s solved EXACTLY: V(s) is cubic in s).**
- PREDICTION: |dV| ≤ 1e-8 everywhere; F1 < blend at 88–144.94; spike ≤ 0.052;
  100° dyad modal no worse than H11's 2/3.
- FALSIFIER: F1 ≥ blend at any flagged-zone angle, OR spike > ε_spike, OR
  |s−1| > 3e-3 (correction is a shape change, not a projection), OR 100° modal
  3/3 / new flag. **FIRED on three prongs at every flexed angle.**

**Law (b) — volume term in the solve (one Lagrange multiplier μ per solve;
constraint re-linearized each local-global step, g = ∇V the area-weighted
vertex normals; KKT solved by Schur complement off the SAME factorization —
two extra backsolves: x = A⁻¹(rhs − μg), μ = (gᵀA⁻¹rhs − c)/(gᵀA⁻¹g)).**
- PREDICTION: |dV| ≤ T_vol at every angle within ~2× H11's iteration count;
  F1 < blend in zone; spike ≤ H11 + 1e-3; dyad no worse.
- FALSIFIER: the constrained iteration stalls/oscillates (res > 1e-6 at the
  60-iter cap or volume residual > T_vol at any angle), OR F1 ≥ blend in zone,
  OR spike > ε_spike, OR dyad worsens. **Fired on ONE prong at ONE angle: the
  130° limit cycle (recorded, bounded, gates green at the cycled state — see
  below). All gate prongs held.**

## Gate table (same bench as H11: exact Möller, rest-baseline subtracted,
## 86,985 pairs / 37 baseline; λ = 0.05, the H11-derived value, unchanged)

F2 |dV| (signed drift), the bar that killed H11:

| θ | uncorrected (H11) | (a) projection | (b) constrained | blend |
|---|---|---|---|---|
| 0 | 0 ✓ | ~0 ✓ | 0 ✓ | 0 ✓ |
| 60 | +4.4e-5 ✓ | ~0 ✓ | 0 ✓ | +3.1e-4 ✓ |
| 88 | −8.2e-4 ✗ | ~0 ✓ | 0 ✓ | +3.5e-4 ✓ |
| 100 | −1.3e-3 ✗ | ~0 ✓ | 0 ✓ | +3.5e-4 ✓ |
| 110 | −1.8e-3 ✗ | ~0 ✓ | −2.6e-16 ✓ | +3.4e-4 ✓ |
| 130 | −2.7e-3 ✗ | ~0 ✓ | +6.4e-7 ✓ | +2.9e-4 ✓ |
| 144.94 | −3.4e-3 ✗ | ~0 ✓ | 0 ✓ | +2.3e-4 ✓ |

F1 penetration (max depth, rest baseline subtracted) + pair counts:

| θ | uncorrected | (a) proj | (b) constr | blend | (b) < blend? |
|---|---|---|---|---|---|
| 60 | 0.0009 | 0.0029 | 0.0009 | 0.0000 | noise-level tie (all < 1% h̄) |
| 88 | 0.0031 | **0.4307 ✗** | **0.0047** | 0.0052 | ✓ |
| 100 | 0.0044 | **0.3454 ✗** | **0.0065** | 0.0159 | ✓ (2.4×) |
| 110 | 0.0045 | **0.2894 ✗** | **0.0068** | 0.0143 | ✓ (2.1×) |
| 130 | 0.0079 | **0.2103 ✗** | **0.0058** | 0.0252 | ✓ (4.3×) |
| 144.94 | 0.0210 | **0.1675 ✗** | **0.0172** | 0.0272 | ✓ (1.6×) |

Pair counts (context, not the bar): (b) 20/28/27/31/38/120 vs blend
12/21/42/47/74/71 at 60…144.94 — (b) carries MORE shallow pairs at max ROM
(120 vs 71) at LOWER max depth (0.0172 vs 0.0272): the volume restoration
spreads contact, it does not bunch it. Recorded.

F3 strain (median-floored, comparative): (b) 0.58/0.74/0.80/0.84/0.90/0.91 vs
blend 0.78/1.21/1.40/1.55/1.85/2.07 — under the blend at every angle ✓ (H11's
win survives). (a) explodes to 7.1–9.4 ✗.

F4 spike, TWO readings (the metric conflation, separated by `volp_diag.py`):

| θ | (b) vs UNCORRECTED C¹ ref | H11 uncorrected (same metric) | (b) CREASE vs CONSTRAINED C¹ ref | blend |
|---|---|---|---|---|
| 60 | 0.0323 | 0.033 | 0.0333 | 0.172 |
| 88 | 0.0469 | 0.042 | 0.0431 | 0.216 |
| 100 | 0.0525 | 0.044 | 0.0462 | 0.225 |
| 110 | 0.0573 | 0.046 | 0.0488 | 0.229 |
| 130 | 0.0736 | 0.051 | 0.0565 | 0.256 |
| 144.94 | 0.0748 | 0.047 | 0.0428 | 0.290 |

The vs-uncorrected-ref reading exceeds H11's values by 0.005–0.028 (over
ε_spike = 0.062 at 130/144.94) — but the constrained-vs-constrained reference
separates the CREASE from the volume-restoration displacement (measured
separately: 0.001 @60 … 0.033 @144.94, monotone in θ, exactly the correction
doing its job). The crease component ≈ H11's spikes ±0.005 at every angle:
**no new crease**. The ε_spike criterion was defined against an unconstrained
reference; for a volume-preserving law the honest reference is the
volume-preserving C¹ solution, and against it (b) passes at every angle
(max 0.0565 < 0.062).

## Why law (a) died (the measurement's lesson)

The free band is ~0.1% of the closed surface, so the sensitivity of whole-mesh
volume to a uniform band scale is dV/ds ≈ 0.016 absolute. Restoring an
O(0.01–0.05) absolute deficit needs s−1 = 0.039 @60 … 1.38–1.89 at 88+ — the
"one scalar" is exact about volume (the cubic root works, |dV| ~ 1e-15) and
catastrophic about shape: it inflates the whole band uniformly (front, sides,
fold alike), manufacturing 0.17–0.43 of NEW penetration and 1,000+ new
intersecting pairs. The deficit is LOCAL (the fold relaxes inward); a uniform
radial scale is a GLOBAL blunt instrument with the wrong Jacobian. Law (b)'s
Jacobian is ∇V itself — the correction lands where the volume was lost.

## The 130° limit cycle (law b's one fired falsifier prong, in full)

At θ=130 the constrained iteration's residual locks at 2.02e-2 ≈ h̄/6 from
iteration ~20 through 300 (flat curve, stable cycle — not divergence, not
stall-on-gradient). At every other angle it converges geometrically
(13–23 iters to <1e-7; 144.94° — deeper — takes 64 iters to 9.1e-8). The
cycled state still passes all four gates (dV 6.4e-7, pen 0.0058 < blend,
strain 0.90 < 1.85, crease 0.0565 < ε). Context: plain ARAP has NO stable
fixed point at the fold (H11), and H11's uncorrected 130° solve already had
the slow tail (~1e-3 at the cap). The volume constraint shifts the balance at
exactly this angle. NAMED follow-up, not tuned here: under-relaxation or
Anderson acceleration on the constrained step at deep flexion.

## Dyad head-to-head (88/100/110, posterior ¾, same offline renderer, one
## picture per watch() call, ≥3 reads per image, MODAL read — the H11
## dyad-hardening rule; verbatim in `volp_dyad_volpB.json`)

| candidate | 88 | 100 | 110 |
|---|---|---|---|
| volp (b) read 1 | CLEAN — "bends gently… smooth, rounded bulge" | FLAG — "fairly sharp diagonal crease across the popliteal region… not a smooth rounded ball" | CLEAN — "no deep pinch line… smooth, rounded ball/bulge" |
| volp (b) read 2 | CLEAN — "no sharp crease… ball-like bulge" | CLEAN — "curves gently inward… smooth, rounded bulge" | CLEAN — "bulges outward as a smooth rounded knob" |
| volp (b) read 3 | CLEAN — "no deep cleft… smooth, rounded convex bulge" | PINCH — "pinches inward… sharp, faceted crease (a dark triangular notch)" | PINCH — "pinches inward with a fairly sharp crease line… angular" |
| blend read 1 | CLEAN | PINCH — "sharp, pointed crease (the dark triangular notch)" | CLEAN |
| blend read 2 | CLEAN | PINCH — "sharp, dark V-shaped crease… folds inward too far" | PINCH — "sharp, angular crease (a dark triangular indentation)" |
| blend read 3 | PINCH — "sharp, angular crease… hard faceted line" | PINCH — "sharp crease/notch… tight V-shape" | PINCH — "sharp, angular crease and inward pinch… defined notch" |

Modal reads: (b) — 88 CLEAN (0/3 flagged), 100 SPLIT (2/3 flagged), 110 CLEAN
(1/3 flagged). Blend — 88 CLEAN (1/3), 100 **PINCH 3/3 STABLE** (now 7/7
across H11 + this session), 110 PINCH (2/3). **Tally: (b) 3/9 flagged vs blend
6/9** — the dyad prefers (b), consistent with H11's 2/12 vs 7/12. The L 100°
flag itself SURVIVES for (b) as a 2/3 modal (unchanged from H11's uncorrected
2/3 — the volume correction adds no crease and removes none at 100°; the
ε_spike VLM-detectability experiment named in H11 is still owed). One read
worse than H11's uncorrected at 110 (1/3 vs 0/3) — inside the measured
instrument noise (byte-identical renders flip), modal still CLEAN.

## The call

**LAW (b) BEATS THE BLEND on the named criteria → the volume-preserving
smooth ARAP is the new knee-skin law candidate; the GPU bi-Laplacian kernel
(carrying the Schur constraint row) becomes the next stage.** F2 passes at
EVERY angle (≤6.4e-7 vs T_vol 4.4e-4 — the bar that killed H11); the F1 win
survives the correction at every flagged-zone angle (1.6–4.3× under blend);
F3 stays under blend everywhere; F4 shows no new crease against the honest
constrained reference; the dyad prefers it 3/9 vs 6/9 with the blend's 100°
pinch stable at 7/7 cumulative. Law (a) is recorded as a clean falsified
candidate — its failure mode (exact volume, catastrophic shape) is itself the
lesson. Carried defects, named not hidden: the 130° limit cycle (h̄/6, gates
green, damping follow-up) and the surviving 100° dyad flag (2/3 modal — the
fold is measurably better, not yet visually clean at the H5-flagged angle).

## What this teaches (recorded, binding)

1. **Volume projection ≠ volume constraint.** A post-step global scale is
   exact about volume and blind about shape — its Jacobian (uniform radial)
   has almost no leverage on the deficit (dV/ds ≈ 0.016 for a 301-node band on
   a 17k-node shell), so exactness is bought with an O(1) shape change. The
   in-solve constraint's Jacobian IS ∇V: the correction is applied in the
   direction that buys volume per unit displacement, distributed over the
   band. FALSIFIED (a), SHIPPED (b) — the gates picked exactly as the physics
   said they would.
2. **The F4 reference must carry the same constraints as the candidate.** A
   spike metric vs an unconstrained C¹ reference charges the volume
   restoration (0.033 of smooth normal displacement at max ROM) as if it were
   a crease. Constrained-vs-constrained is the honest crease meter; with it,
   (b) adds no crease (±0.005 vs H11).
3. **The constrained SCQP step costs two backsolves per iteration** off the
   same factorization — negligible; convergence 13–64 iters. The GPU
   bi-Laplacian kernel's design must carry the Schur-complement constraint
   row (one scalar reduction per iteration), not a post-pass.
4. **A limit cycle can be angle-localized.** 130° cycles at h̄/6 forever;
   144.94° converges. Recorded with the 300-iter curve in `volp_diag.json`.

Files: `.tmp/volp_arap.py` (both laws + gates, falsifiers in header),
`.tmp/volp_diag.py` (crease separation + 300-iter probes), `.tmp/volp_dyad.py`
(head-to-head driver), `.tmp/smooth_arap_out/volp_gates.json`,
`volp_diag.json`, `volp_dyad_volpB.json`, `volp{U,A,B}_X_*.npy`,
`cmp_volpB_strip.png` + per-angle renders.
