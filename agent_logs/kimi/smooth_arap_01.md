# SMOOTH ARAP 01 — bi-Laplacian knee skin (H11): F2 volume FALSIFIED, blend stays the law (2026-08-29)

**Question (physics packet Q4.2, master list H11):** does smooth ARAP
(E = (1−λ)E_ARAP + λE_smooth, global step = bi-Laplacian, Oehri et al. 2025,
arXiv:2501.10335) beat the production blend at the H5-flagged angles —
L 100° pinch flag gone, F1 pen < blend at every angle, volume ≤ T_vol,
dyad prefers it?

**Answer: NO on the named success criteria — F2 (volume) fails INTRINSICALLY
and the L 100° dyad flag survives at the derived λ. Not shipped; the blend
stays the law.** It wins three of the four measured gates (F1-in-zone, F3,
F4) and the dyad prefers it 1-flag-vs-3 — recorded in full below.

## The membrane (Rule 0, stated before the run — in `.tmp/smooth_arap.py`)

- STATEMENT: the blend's fold bunching is the C⁰ tangent discontinuity at the
  constraint ring; the bi-Laplacian's C¹ across the ring kills it.
- PREDICTION: F1 pen < blend at every gate angle; volume ≤ T_vol = 4.4e-4;
  L 100° pinch flag gone, no new flags.
- FALSIFIER: F1 ≥ blend at any angle, OR volume > T_vol, OR dyad still flags
  pinch/new defect → membrane fails, blend stays. **Fired: F2 and the dyad.**

## Implementation (Q4.2 as specced, welded graph)

Solver `.tmp/smooth_arap.py`: welded node graph (17,204 nodes — twins are ONE
node, seams cannot tear by construction, the wadj law). Bi-Laplacian system
(λL M⁻¹L + (1−λ)L)p′ = λL r + (1−λ)b, r_i = R_i ℓ0_i, rotation fitting
EDGE-ONLY (SVD per node), ring (rotating set, posed rigidly about the
corrected inter-knee axis) + w==0 far field as Dirichlet by substitution,
band R_FALL = R_JOINT·θ_max = 0.759 (the arc derivation — stands), 301 free
nodes, sparse-direct factorization per (λ, θ), local-global to |Δx| < 1e-7.

**Two implementation findings that CONTRADICT a naive read of Q4.2:**

1. **Cotan weights are unusable here.** 18,932 negative cotan weights on this
   recon ⇒ L indefinite ⇒ the local-global fixed point OSCILLATES for
   λ ≲ 0.2 (measured limit cycles: residual 4.25 at λ=0, 0.42 at λ=0.05,
   0.37 at λ=0.1; converges at λ=0.3). This is the Alexa & Wardetzky 2011
   trade the repo already ratified for water (physics_packet_02: KEEP
   positivity, SURRENDER linear-exactness). The R4 conductance law
   k_ij = g·A_pipe/l_ij with A_pipe = |e_ij|·H gives k_ij = const on the
   primal graph — the UNIFORM Laplacian (what arap_skin used). With it,
   λ ≥ 0.05 converges in ~20 iterations; θ=0 reproduces rest to 3e-14.
   Scheme = "r4" (uniform), recorded in the file header.
2. **Rotation fitting with negative cotan covariance returns R ≠ I at rest**
   (θ=0 drifted 0.174 before the fix). Covariance weights clamped to
   w ≥ 0 ⇒ S_i PSD ⇒ rest is an exact fixed point. Eq 3's weights cannot be
   read literally on a non-Delaunay mesh.

Also: λ=0 (plain ARAP) does not converge even with the uniform operator — it
settles into a limit cycle of amplitude ~6e-2 ≈ h̄/2 at the fold. Plain ARAP
has NO stable fixed point at the crease; the smooth term is also the
regularizer. (Consistent with arap_skin_01's 6-iteration cap hiding this.)

## The λ derivation (never 0.95-by-citation)

ε_spike = 0.5·h̄, h̄ = median band edge length = 0.12383 ⇒ **ε_spike = 0.06192**.
Derivation of ε_spike: a surface deviation under half the local sampling
length is below what the mesh can represent as a feature — the surface cannot
carry a spike finer than its own sampling. **CHOSEN-UNVERIFIED**: the
verification experiment is the dyad itself (if the VLM flags a crease at the
λ this ε selects, ε was too loose — and it DID, see below; the h̄/2
coefficient needs a human/VLM detectability study, named, not run).

spike(λ) = max deviation from the λ_ref = 0.999 (near-C¹) solution over the
29 ring-adjacent free nodes, at the two worst angles (100 = dyad flag,
130 = F1 peak):

| λ | spike @100 | spike @130 | < ε_spike? |
|---|---|---|---|
| 0 (plain ARAP) | 0.307 (limit cycle) | 0.254 (limit cycle) | NO — 4–5× over |
| 0.01 | 0.142 | 0.135 | no |
| 0.02 | 0.094 | 0.101 | no |
| 0.03 | 0.069 | 0.078 | no |
| 0.04 | 0.054 | 0.0620 | 100: yes / 130: NO (0.1% over) |
| **0.05** | **0.044** | **0.051** | **YES — smallest passing** |
| 0.1 | 0.022 | 0.026 | yes |
| 0.3 | 0.0060 | 0.0072 | yes |
| 0.7 | 0.0011 | 0.0013 | yes |
| 0.95 | 0.00014 | 0.00016 | yes |
| 0.999 (ref) | 0 | 0 | — |

**λ = 0.05, derived** (smallest λ passing ε_spike at both angles). The paper's
empirical 0.95 is ~2 orders of magnitude more smoothing than this tolerance
requires. Residual curves: ~20 iters to 1e-7 at θ=100; θ=130 plateaus at
~1e-3 after 60 iters (slow tail at deep flexion, recorded; 1e-3 ≈ 1.6% of h̄).
The absolute-Laplacian diagnostic κ = ‖ℓ‖/h̄ is FLAT across λ (~764–794) —
rest curvature dominates it; the λ-dependence lives entirely in the
deviation-from-C¹-reference metric. Reported, not used.

## Gate table (F1/F2/F3/F4 vs the blend; exact Möller, rest-baseline
subtracted, same zone/pair machinery as fold_validate — 86,985 candidate
pairs, 37 rest-baseline)

λ = 0.05 (the derived candidate):

| θ | F1 pen sarap / blend | F2 \|dV\| sarap / blend | F3 strain sarap / blend | F4 spike sarap / blend |
|---|---|---|---|---|
| 0 | 0.0000 / 0.0000 | 0 / 0 | 0.00 / 0.00 | 0.0000 / 0.0000 |
| 60 | **0.0009 / 0.0000** | 4.4e-5 ✓ / 3.1e-4 ✓ | 0.58 / 0.78 | 0.033 / 0.172 |
| 88 | 0.0031 / 0.0052 ✓ | **8.1e-4 ✗** / 3.5e-4 ✓ | 0.74 / 1.21 | 0.042 / 0.216 |
| 100 | 0.0044 / 0.0159 ✓ | **1.3e-3 ✗** / 3.5e-4 ✓ | 0.78 / 1.40 | 0.044 / 0.225 |
| 110 | 0.0045 / 0.0143 ✓ | **1.8e-3 ✗** / 3.3e-4 ✓ | 0.82 / 1.55 | 0.046 / 0.229 |
| 130 | 0.0079 / 0.0252 ✓ | **2.7e-3 ✗** / 2.8e-4 ✓ | 0.87 / 1.85 | 0.051 / 0.256 |
| 144.94 | 0.0210 / 0.0272 ✓ | **3.4e-3 ✗** / 2.3e-4 ✓ | 0.88 / 2.07 | 0.047 / 0.290 |

λ = 0.95 (diagnostic — "is the F2 failure a λ artifact?"):

| θ | F1 pen sarap / blend | F2 \|dV\| sarap |
|---|---|---|
| 60 | 0.0007 / 0.0000 | 1.5e-4 ✓ |
| 88 | 0.0033 / 0.0052 | 6.4e-4 ✗ |
| 100 | 0.0044 / 0.0159 | 1.1e-3 ✗ |
| 110 | 0.0043 / 0.0143 | 1.6e-3 ✗ |
| 130 | 0.0075 / 0.0252 | 2.6e-3 ✗ |
| 144.94 | **0.0339 / 0.0272 ✗ (worse!)** | 3.3e-3 ✗ |

Gate reads:

- **F1: PASS in the flagged zone** — pen < blend at 88/100/110/130 (2–4×
  lower) at both λ. At 60° sarap is marginally above blend (0.0009 vs ~0 —
  both noise-level, <1% of h̄). At max ROM λ decides: 0.05 wins (0.0210 <
  0.0272), 0.95 loses (0.0339 > 0.0272).
- **F2: FAIL — intrinsic.** The solve SHRINKS volume (signed drift
  −1.3e-3 @100, −3.4e-3 @144.94; the blend GAINS +2–3e-4 and passes).
  Roughly λ-independent (same order at 0.05 and 0.95) ⇒ not a λ artifact;
  the bi-Laplacian energy simply is not volume-conserving under fold
  compression — the packet's Q4.5.1 falsifier ("ARAP must be near-lossless")
  fires on smooth ARAP exactly as it would on plain ARAP.
- **F3: PASS (comparative)** — median-floored max strain below the blend at
  every angle (0.58–0.88 vs 0.78–2.07). fold_validate's max≤2×median form
  fails BOTH methods at every flexed angle (it failed the blend in H5 too) —
  it is a spread diagnostic, not a discriminator; recorded.
- **F4: PASS** — ring spike 3–7× below the blend's at every angle (0.033–0.051
  vs 0.17–0.29 at λ=0.05; ~0.0002 at λ=0.95 by construction).

## Dyad head-to-head (88/100/110, posterior 3/4, SAME offline matplotlib
renderer for both candidates — operator decree: not the live engine; one
picture per watch() call, the L-100° question)

FOUR judgings were collected (the first two "λ=0.95" attempts silently
re-judged the λ=0.05 renders — a variable collision with the exec'd solver
wiped the --lam flag; the accident became a repeated-read noise probe on
BYTE-IDENTICAL images, verified by md5):

| candidate | 88 | 100 | 110 |
|---|---|---|---|
| sarap λ=0.05, read 1 | CLEAN — "bends gently without a hard line… smooth, rounded bulge" | PINCH — "pinches inward and forms a sharp crease… angular, pinched V" | CLEAN — "smooth, rounded bulge… no deformation artifacts" |
| sarap λ=0.05, read 2 | CLEAN | CLEAN | CLEAN |
| sarap λ=0.05, read 3 | CLEAN | PINCH — "sharp, angular crease" | CLEAN |
| sarap λ=0.95, read 1 | CLEAN | CLEAN — "transitions smoothly without a deep fold line" | CLEAN |
| blend, read 1 | FLAG — "fairly sharp, faceted inward crease" | PINCH — "sharp, angular triangular crease… hard-edged notch" | PINCH — "deep, angular notch… sharp V-shaped crease" |
| blend, read 2 | PINCH | PINCH | PINCH |
| blend, read 3 | CLEAN | PINCH — "sharp, pointed crease" | PINCH |
| blend, read 4 | CLEAN | PINCH | CLEAN |

Tally: sarap λ=0.05 flags 2/9 reads (both at 100°); sarap λ=0.95 flags 0/3;
blend flags 7/12. **At L 100° specifically: the blend is PINCH 4/4 reads —
the H5 flag reproduces perfectly and stably; sarap λ=0.05 flags 2/3;
sarap λ=0.95 clean 1/1 (single read).** Verbatim reports in
`dyad_cmp.json` (λ=0.05 read 1), `dyad_cmp_lam0.05_rerun.json`,
`dyad_cmp_lam0.05_rerun2.json`, `dyad_cmp_lam0.95.json`.

Dyad verdict: **smooth ARAP is preferred at both λ** (2/12 vs 7/12 flagged
overall; the blend's 100° pinch is a STABLE instrument reading, sarap's is
not). At λ=0.95 the 100° read is clean — but one read is not a clearance.

## The call

**LOSS on the named criteria → not shipped, production blend untouched.**
Smooth ARAP as specced in Q4.2 wins F1-in-zone, F3, F4, and the dyad
preference — but **fails F2 volume intrinsically** (the energy is not
volume-conserving; λ cannot fix it: same-order drift at 0.05 and 0.95), and
at the derived λ=0.05 the L 100° dyad flag survives (2/3 reads). The blend
remains the shipping law (H5's close stands).

What this teaches (recorded, binding):

1. **C¹ continuity ≠ volume conservation.** The bi-Laplacian kills the
   tangent spike (F4, 3–7×) and cuts the bunching 2–4× (F1) but pays volume —
   the packet's own T_vol falsifier, derived from ν=0.49 tissue
   incompressibility, is exactly the gate that fires. A fold law needs BOTH.
2. **The next membrane is named: volume-preserving smooth ARAP** — either a
   volume-restoration post-projection onto the |dV| ≤ T_vol manifold
   (H5's push-out was falsified for INTERSECTION projection; a VOLUME
   projection is a different, global, well-posed constraint — one scalar
   per solve), or a volume term in the energy. The GPU bi-Laplacian kernel
   is NOT the next stage — there is no point porting an F2-failing law.
3. **ε_spike = h̄/2 is FALSIFIED as a dyad-detectability tolerance.**
   λ=0.05 passes it (spike 0.044 < 0.062) yet the dyad still flags the 100°
   crease 2/3 of the time; the sub-sampling argument bounds what the MESH
   can represent, not what the VLM can see. The named experiment: VLM flag
   rate vs spike height in units of h̄, repeated reads (the instrument noise
   is now measured — below).
4. **The dyad instrument at 100° is noise-dominated for near-clean
   candidates but STABLE on the blend's pinch.** Byte-identical λ=0.05
   renders flipped PINCH↔CLEAN across reads (1/3, then 0/3, then 2/3
   cumulative); the blend's 100° pinch read PINCH 4/4. Any future "flag
   gone" criterion needs ≥3 reads per image or a sharper render (the fold
   is a small fraction of the frame at the arap_compare framing).
5. **Cotan is dead on this recon for iterative solves** (18,932 negative
   weights → indefinite L → limit cycles at λ ≲ 0.2). The R4/uniform
   operator with clamped-PSD covariance is the recorded working choice;
   θ=0 fixed point exact to 3e-14. Also: plain ARAP (λ=0) has no stable
   fixed point at the fold (limit cycle ~h̄/2) — arap_skin_01's 6-iteration
   cap had hidden this.
6. **exec()-shim scripts share ONE namespace** — a `CLI` variable in the
   exec'd solver silently wiped the dyad driver's `--lam` flag, and two
   full dyad runs judged the wrong λ before the md5 check caught it.
   Namespace-prefix everything in exec'd harnesses (recorded as a bench
   hygiene rule).

Files: `.tmp/smooth_arap.py` (solver + λ sweep), `.tmp/smooth_arap_gates.py`
(F1–F4), `.tmp/smooth_arap_dyad.py` (head-to-head), `.tmp/smooth_arap_out/`
(lambda_curve.json, lambda_refine.json, gates.json [= λ0.95], lam0.05/
[gates.json + solutions], gates_lam0.95.json, dyad_cmp.json,
dyad_cmp_lam0.95.json, cmp strips, renders).
