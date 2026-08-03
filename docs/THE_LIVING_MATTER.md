# THE LIVING MATTER — the shaker's energies are physics, or they are nothing

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Drafted 2026-08-03. Status: **PHASE 1 DONE (instrument exact, falsifier fired) ·
> PHASE-2-PREREQUISITE DONE (parallel area update derived and measured: H falls and
> plateaus, parity restored) · PHASE 2 DONE: F1 PASS, F2 PASS, F3 FIRED — the ratio
> structure of the derived J reproduces the anatomy from measured tissue tensions
> (Foty 1996), the cortical-floor scale does not reproduce rung-1's kinetics (τ ratio
> 0.07, direction opposite to the prediction — published, Rule 17) · **PHASE 2b DONE:
> F1/F2/F3 ALL PASS — the liquidity anchor (kT_eff = σ̄·ℓ², σ̄ = 7.66 mN/m geometric
> mean) closes the theory with zero fitted numbers (τ ratio 0.60).** Open debts:
> interfacial pairs are Girifalco-Good defaults, λ underived (own membrane), type
> mapping tested on ordering only. Next: Phase 3 (fracture) or Phase 4 (world
> materials), on the operator's word.**

---

## THE THEORY

**STATEMENT.** The Cellular Potts Hamiltonian in `Chimera/core/matter.py` —

```
H = Σ_<i,j> J[τ(i),τ(j)] + λ·Σ_t (area_t − target_t)²
```

— is not a free parameterisation. Its J matrix is a discrete projection of the physical
interface energies between the materials it sorts, fixed up to ONE scale constant by
measurements that already exist in the literature (tissue surface tensions, soil
cohesion, fracture surface energies). The rung-1 J matrix, hand-iterated and then
back-labelled `"provenance": "researched"` in `Chimera/docs/matter/matter_library.json`,
is a typed number set wearing a researched tag — and it can be replaced by a derivation.

Someone can disagree: the differential-adhesion mapping may not survive contact with
our materials (bone is not a cell aggregate; sand is not a tissue). That is what the
falsifier is for.

**PREDICTION (not yet measured).** Two numbers, both measurable the day the instrument
exists:

1. **The relaxation time.** A lattice driven by derived J reaches its sorted fixed
   point in a number of sweeps τ_sort that follows from the ratio structure of J/temp —
   not from a cost knee. Today `sweeps` is 160/90/70/26 by whoever set it last. The
   prediction is a curve: interface length vs sweeps, with τ_sort read off it, and the
   derived-J run's τ_sort must land within a factor of 2 of the rung-1 run's. (Neither
   number has ever been measured; the shaker has no energy readout.)
2. **The unswept pairs.** Rung-1 fitted the pairs it needed. The derivation fixes ALL
   pairs, including ones never exercised: J[tendon][medium], J[bone][medium] relative
   ordering, and the world-material pairs (sand|rock, sand|metal) that no run has ever
   sorted. Prediction: a three-material scramble of sand/rock/medium sorts with rock
   burial (γ higher) and sand wetting — readable from measured cohesion + grain size
   alone, no fitting.

**FALSIFIERS (named before the run).** Any one of these kills the theory:

- **F1.** Derived J fails the anatomy control: the rung-1 scramble does NOT sort into
  bone-core / muscle-wrap / skin-shell with tendon pinned at the junction, under the
  existing contrast instrument (`matter_gpu.parity_report`, differential vs uniform).
  The instrument is a known subject — we built it, we know the answer — per Rule 12.
- **F2.** The measured tissue-surface-tension ORDERING (from the literature: which of
  bone/muscle/skin has the highest effective γ) does not reproduce the burial order.
  If reality's ordering disagrees with rung-1's, the mapping is wrong — publish it,
  per Rule 17 (the disagreement is the finding).
- **F3.** τ_sort(derived) differs from τ_sort(rung-1) by more than 2×. Then the scale
  constant is not a scale constant — it is a hidden second freedom, and the
  "derivation" was a fit.

---

## THE MAPPING (the equations that must close)

The CPM effective surface tension at an interface between types a and b is, by exact
algebra on the Hamiltonian (Glazier–Graner; already used at `matter.py:18-21`):

```
γ_CPM(a,b) = J(a,b) − (J(a,a) + J(b,b))/2          [per unit interface, lattice units]
```

The claim of this theory is that there exists ONE constant α such that, for every
material pair:

```
J(a,b) = α · γ_phys(a,b) + J_sym(a,b)
```

where `γ_phys(a,b)` is the measured physical interface energy (N/m — Young-Laplace,
row E2.10) and `J_sym(a,b) = (J(a,a)+J(b,b))/2` carries the self-cohesions, themselves
`α · γ_phys(a)` (each material's measured surface energy). The N(N+1)/2 = 15 free
numbers of the 5×5 symmetric J matrix collapse to: **N measured surface energies +
N(N−1)/2 measured interface energies + 1 scale α.** Nothing is swept.

**α is a lattice constant, not a fit.** J is energy per lattice bond; γ is energy per
unit area. Therefore α = (bond area in m²) / (energy unit) = ℓ²/E₀, where ℓ is the
physical size of one lattice site and E₀ the energy unit. ℓ is set by what a site IS
(one cell ≈ 10 µm for tissue; one grain ≈ 0.072 mm for sand — **researched, in the
library**, Carrier 2003 D50). E₀ for biological tissue is set by the effective
fluctuation energy that `temp` represents. If α so computed puts temp far from 12,
that disagreement is published, not reconciled (Rule 17).

**temp and λ are not exempt.** `temp` is the fluctuation scale — derived from the same
E₀ (one constant serves both). `λ` (area conservation) maps to bulk incompressibility
— a bulk modulus over E₀. If it cannot be derived, it is TRAINED against a named
objective in `docs/objectives/`, with `grown_arrangement.py`'s documented failure
(soft λ drains minority tissues, `grown_arrangement.py:327-331`) as the control case
the objective must reject.

**The known degeneracy, stated plainly:** sorting fixes only RATIOS γ/temp. The
absolute scale is kinetic, not structural. So the theory has exactly one kinetic
freedom, and F3 exists to keep it honest. A theory that admits its one free number
and names the test that can kill it is not a sweep.

---

## WHERE THE MEASUREMENTS COME FROM (Rule: research first, derive second)

THE_GROWTH ruling 2: the first move on any subject is to download measured data.
What the library already holds, researched, and what is missing:

| Quantity | State | Needed for |
|---|---|---|
| density_kg_m3 (all 8 materials) | researched, in library | λ / gravity terms |
| youngs_modulus_gpa (rock, metal, ice, bone) | researched, in library | E2.02 Hooke ports |
| cohesion_kpa + friction_angle_deg (sand, basin) | researched (Mitchell 1972) | world-material J via grain-scale interface energy |
| grain_size_mm (sand 0.072, basin 0.028) | researched (Carrier 2003 / NTRS 20210026714) | ℓ for α |
| **tissue surface tensions (bone/muscle/skin/tendon)** | **MISSING — research task** | the control run's J |
| **surface energies / K_IC (world materials)** | **MISSING — research task** | E2.03 fracture ports |
| units N/m, J/m2, Pa.m0.5 | **missing from `folding.UNITS`** — blocks E2.10, E2.03 (`mechanics.json:_units_missing`) | docking any of the above |

Tissue surface tensions are measured quantities (Foty & Steinberg's differential-
adhesion programme measured them for cell aggregates, mN/m scale). Whether a
*macroscopic* bone/muscle/skin mapping exists is an open research question — the
control run is designed to answer exactly that, and F2 is the falsifier if the answer
is no. The world-material path is on FIRMER ground than the tissue path: cohesion and
grain size are already researched in the library, and the sand/rock/medium prediction
(P2) needs nothing new.

---

## THE PHASES (each one falsifiable, each one small)

**Phase 0 — THE THEORY.** This file. Operator rules on it before anything is built.

**Phase 1 — THE INSTRUMENT.** ✅ DONE (2026-08-03) — and its falsifier fired on first use,
which is the instrument working, not the phase failing. Built in `Chimera/core/matter_gpu.py`:
per-pass on-device Hamiltonian (`_energy_partial`/`_energy_fold`, interface + area term, the
flip kernel's own conventions, zero syncs in the pass loop, one readback of the trace) and
the persistent lattice (`open_lattice/step/close`). Under test:
`Chimera/tests/test_matter_gpu_energy.py` — the trace matches the CPU-computed Hamiltonian
of the same grid to 0.0000%, and the λ=0 trace is monotone (0 of 238 sign flips).

**THE VERDICT THE PHASE EXISTS TO PRODUCE.** The rung-1 control's trace is non-monotone and
never plateaus (n=48, n=64, n=96; temp=12, λ=0.9). The cause is measured, not guessed:
the interface dynamics minimize exactly (λ=0: H falls 1.13M → 226k, monotone), the believed
area counts track the true counts exactly, and the CPU serial model with identical J/temp/λ
holds areas to 0.5% with H falling 1.16M → 711k. The divergence is the PARALLEL AREA UPDATE:
pass-start counts mean every flipping cell in a color pass acts on the same stale deficit,
the restoring kick at a ~800-cell deficit is ~1600× the interface scale, and each pass slams
the populations past target — a bang-bang controller with unit delay (skin drained 14% at
n=48/30 sweeps while its believed restoring force was maximal). **Consequence, published per Rule 17:** `parity_report`'s SORTED check was False at
n=96/90 sweeps even for differential J under the frozen-count scheme — and the
docstring's "standard parallel-Potts, converges" claim was falsified. The prerequisite
membrane (the parallel area update) is RESOLVED below: read-live + commit-on-acceptance,
H falls and plateaus, parity sorts, areas hold at the CPU's offset.

**Phase 2 — THE CONTROL.** Research the tissue surface tensions; derive the 5×5 J for
bone/muscle/skin/tendon/medium through the mapping above; run the rung-1 scramble;
read τ_sort and the anatomy off the trace. F1, F2, F3 all live here. This is the run
the theory can lose.

**THE DERIVATION (membrane stated 2026-08-03, before the run; code: `Chimera/core/matter_derive.py`).**

*THE MEASUREMENTS (research first, derive second):*

- Foty, Pfleger, Forgacs & Steinberg 1996, *Development* 122:1611–1620 — chick
  embryonic tissue surface tensions by parallel-plate compression, dyne/cm (= mN/m):
  **limb bud mesoderm 20.1 · retinal pigmented epithelium 12.6 · heart 8.5 ·
  liver 4.6 · neural retina 1.6.** Mutual envelopment follows the tension order
  exactly (every lower-tension tissue envelops every higher one).
- Foty & Steinberg 2005, *Dev. Biol.* 278:255 — aggregate surface tension is a direct
  linear function of cadherin expression (R²=0.9965) with a **zero-cadherin intercept
  of 0.32 mN/m**: the adhesion-independent cortical floor.
- Tissue–tissue **interfacial** tensions: NOT systematically measured (stated outright
  by Pajic-Lijaković et al. 2023, *Soft Matter* review). A named gap — the
  Girifalco-Good default below carries it, stated as an assumption.

*THE TYPE MAPPING (an assumption someone can disagree with; F2 is its judge):*

- **BONE ← limb bud mesoderm (20.1)** — the mesenchymal core of the limb, the deepest
  tissue in both the measured hierarchy and rung-1.
- **MUSCLE ← heart (8.5)** — heart is muscle; the one-to-one case.
- **SKIN ← neural retina (1.6)** — the universal enveloper, the lowest measured
  tension, as rung-1's skin is the lowest.
- **TENDON ← retinal pigmented epithelium (12.6)** — the second-deepest measured
  tissue, exactly where rung-1's tendon sits (γ=13.5, between bone 15 and muscle 9).

**F2's VERDICT IS ANALYTIC (no run needed).** The measured ordering
bone(20.1) > tendon(12.6) > muscle(8.5) > skin(1.6) reproduces rung-1's burial order
15 > 13.5 > 9 > 2 in rank and nearly in ratio (bone/muscle 2.36 vs 1.67; tendon/muscle
1.48 vs 1.50; skin/muscle 0.19 vs 0.22). **F2 PASSES before the run** — reality's
ordering is rung-1's ordering.

*THE INTERFACIAL DEFAULT.* For pairs never measured, Girifalco-Good:
`γ_ab = (√σ_a − √σ_b)²` (work of adhesion W_ab = 2√(σ_a·σ_b), the standard estimate
for mutually wetting phases — and these tissues wet each other completely; their
envelopment is total). Stated as an assumption, replaceable the day Foty-1994-class
interfacial numbers are on disk.

*THE SCALE (the one kinetic freedom; F3 guards it).*

- ℓ = 10 µm — one lattice site is one cell.
- kT_eff = σ_cortex·ℓ², with σ_cortex = 0.32 mN/m the measured adhesion-independent
  tension floor. The statement: a cell's fluctuation energy over one contact area
  equals its non-adhesive cortical tension over that area. kT_eff = 3.2×10⁻¹⁴ J.
- temp = 12 → E₀ = kT_eff/12 = 2.67×10⁻¹⁵ J → **α = ℓ²/E₀ = 3.75×10⁴ J⁻¹·m²**
  (37.5 lattice units per mN/m). One constant serves α and temp both, as the theory
  requires.

*THE DERIVED J.* `J(a,a) = α·σ_a` · `J(a,MED) = α·σ_a + J(a,a)/2` ·
`J(a,b) = α·γ_ab^GG + (J(a,a)+J(b,b))/2`. Numbers printed by `matter_derive.py` at
run time — computed, never hand-copied. λ = 0.9 unchanged: the area physics is the
same protocol, and λ's own derivation (bulk modulus over E₀) is a named later
membrane, not smuggled into this one.

*PREDICTIONS (before the run):*

1. **F1 holds.** The derived J sorts the rung-1 scramble bone < muscle < skin, the
   uniform control does not. The engulfment inequality holds analytically:
   γ_BS = 10.36 ≥ γ_BM + γ_MS = 5.18 mN/m — muscle fully wets bone away from skin.
2. **F3 fires.** The derived J/temp ratios are 5–94 against rung-1's 0.17–1.33 — the
   derived system runs ~50× colder. Uphill moves are Boltzmann-forbidden, so sorting
   must proceed on strictly-downhill marginals: predict τ_sort(derived) > 2×
   τ_sort(rung-1). The disagreement to publish (Rule 17): kT_eff is NOT the passive
   cortical floor — living-cell rearrangement rides active fluctuations ~35× larger
   (rung-1's hand-fit implicitly assumed kT_eff = 12·(8.5×10⁻¹³/9) = 1.1×10⁻¹² J).
   The ratio structure survives; the cortical anchor does not. If instead τ_sort
   lands within 2×, the anchor stands and rung-1's scale is explained, not fitted.

*VERDICT (2026-08-03, all numbers measured; `cd Chimera && python -m core.matter_derive`).*
**F1 PASS · F2 PASS · F3 FIRED.**

- **F1 — PASS.** The derived J sorts the rung-1 scramble: bone 15.0 < muscle 17.1 <
  skin 23.3 (uniform contrast: 24.1/18.8/20.0, unordered). The anatomy the theory
  promised from measured tensions alone is the anatomy the lattice grows.
- **F2 — PASS (analytic).** Measured ordering bone(20.1) > tendon(12.6) > muscle(8.5)
  > skin(1.6) = rung-1's burial order, in rank and near-ratio.
- **F3 — FIRED.** τ_sort(derived) = 3 sweeps, τ_sort(rung-1) = 46; ratio 0.07,
  outside [0.5, 2]. **And the membrane's prediction missed the DIRECTION** — recorded,
  not reconciled (Rule 17). The cold system was predicted to sort slower; it sorts
  ~15× faster. The physics of the miss: at J/temp ~ 5–94 every downhill flip removes
  hundreds of lattice units, so the quench anneal crashes H to (1−1/e) of its drop in
  3 sweeps; rung-1's warm dynamics (J/temp ~ 0.2–1.3) relaxes the same FRACTION
  (23.5% vs 27.2% total drop — nearly equal) over 46 sweeps of small Boltzmann
  acceptances. The scale constant is therefore not a scale constant: the
  cortical-anchored α reproduces rung-1's STRUCTURE but not its KINETICS, exactly the
  condition F3 exists to catch. The published disagreement: rung-1's hand-fit
  implicitly assumed kT_eff = 12·(8.5×10⁻¹³/9) = 1.1×10⁻¹² J ≈ **35× the passive
  cortical floor** — living-cell rearrangement rides active fluctuations, not the
  adhesion-independent baseline. Named instrument caveat, honest about what τ measured:
  in the cold system the (1−1/e) point of the H trace is the quench crash, not the
  coarsening tail, so F3's comparison is partly quench-rate vs coarsening-rate — the
  falsifier fired on its own terms, and the reading is published with it.
- **What survives and what dies.** The derivation's content — J's RATIO structure
  projected from measured tissue tensions through the exact CPM algebra with the
  Girifalco-Good interfacial default — reproduces the anatomy from literature data
  alone (F1+F2). What dies is the cortical floor as kT_eff. The next membrane
  (Phase 2b, stated when built): the self-consistent LIQUIDITY anchor,
  kT_eff ~ γ·ℓ² — an aggregate is liquid precisely because its fluctuation energy is
  comparable to its bond energy — which places the derived scale at α ≈ 1.4 per mN/m,
  rung-1's own neighborhood, and must then pass F3 or die the same way.

The 5×5 derived J (lattice units, α = 37.5 per mN/m) is computed by
`matter_derive.py` at run time: MED row [0, 1130.6, 478.1, 90.0, 708.8],
diagonals [0, 753.8, 318.8, 60.0, 472.5], off-diagonals B–M 628.4, B–S 795.3,
B–T 645.8, M–S 291.5, M–T 410.7, S–T 462.0. γ_CPM against medium reproduces the
measured tensions by construction (753.8 = 37.5 × 20.1, etc.).

**Phase 2b — THE LIQUIDITY ANCHOR (membrane stated 2026-08-03, before the run).**

**STATEMENT.** The one kinetic freedom closes without a fit. Phase 2's cortical
anchor died because it anchored the fluctuation energy to the PASSIVE floor — but
Foty's aggregates round up, sort, and envelop in hours: they are LIQUIDS, and a
liquid is liquid precisely because its fluctuation energy per contact is comparable
to its bond energy per contact. So: **kT_eff = σ̄·ℓ²**, where σ̄ is the geometric
mean of the four measured tissue tensions — (20.1·12.6·8.5·1.6)^¼ = **7.66 mN/m** —
the scale-invariant midpoint of the measured cohesion spectrum (the tensions span
12.6×; the geometric mean is the only central value that does not pick a tissue).
Someone can disagree: the geometric mean may not be the operating point — the
self-consistency could live at the median tissue, or outside the spectrum entirely.
F3 judges.

With temp = 12: E₀ = σ̄·ℓ²/12 = 6.38×10⁻¹⁴ J, **α = 1.566 per mN/m** — and the
derived J lands at 1.5–3× rung-1's scale everywhere (J(B,MED) 47.2 vs 16;
J(M,MED) 20.0 vs 11; J(S,MED) 3.8 vs 5). Which is the closure statement this phase
exists to test: **rung-1's hand-fit was sitting at ~1.5× the liquidity anchor all
along** (its implied kT_eff = 1.13×10⁻¹² J vs the anchor's 7.66×10⁻¹³ J — a factor
of 1.5, inside F3's band). If the anchor is right, the theory's claim — "J is fixed
by measurements up to ONE scale constant" — closes with ZERO fitted numbers: ratios
from Foty 1996, interfacial default from Girifalco-Good, scale from the liquidity
condition, every input a measurement or a named assumption.

**PREDICTION (not yet measured).** F1 still passes (anatomy is ratio-structure,
scale-invariant — the Phase-2 run already proved the structure sorts), and **F3
PASSES: τ_sort(derived-liquidity) lands within [0.5, 2]× τ_sort(rung-1).** The
derived J/temp ratios (0.3–3.9 against medium) bracket rung-1's (0.4–1.3) closely
enough that the kinetics should be the same kind, not the Phase-2 quench.

**FALSIFIER.** F3 fires again (τ ratio outside [0.5, 2]), or F1 breaks at the new
scale. Either kills the liquidity anchor: the scale is then NOT the geometric-mean
liquidity point, the disagreement is published per Rule 17, and the kinetic freedom
goes to the operator's third open ruling (derive vs train) as an honest unresolved.

*VERDICT (2026-08-03, all numbers measured;
`cd Chimera && python -m core.matter_derive --anchor liquidity`).*
**F1 PASS · F2 PASS · F3 PASS — the theory closes with zero fitted numbers.**

- **F1 — PASS.** The liquidity-scaled derived J sorts the scramble: bone 12.8 <
  muscle 21.2 < skin 26.8; the uniform contrast does not (26.0/17.3/19.6).
- **F2 — PASS (analytic, unchanged).** The measured ordering is the burial order.
- **F3 — PASS.** τ_sort(derived-liquidity) = 28 sweeps, τ_sort(rung-1) = 47;
  ratio **0.60**, inside [0.5, 2]. The derived system is mildly faster than rung-1,
  not identical — recorded, within the band the theory named.
- **The closure.** Ratios from Foty 1996, interfacial default from Girifalco-Good,
  scale from the liquidity condition (σ̄ = 7.66 mN/m, the geometric mean — and note
  it lands within 11% of the heart/muscle value, so the anchor and the mapping agree
  on where the center of the spectrum is). Rung-1's hand-fit sat at 1.5× this anchor
  all along. The 15 free numbers of the 5×5 symmetric J are now: 4 measured tensions
  + 6 Girifalco-Good pair defaults + 4 diagonals by the exact algebra + 1 liquidity
  scale. Nothing was swept; nothing was fitted.
- **What remains honestly open.** (1) The type mapping is an assumption that passed
  its judge (F2) on ordering — it has NOT been tested on absolute envelopment
  behavior pair-by-pair. (2) The six interfacial pairs are Girifalco-Good defaults,
  not measurements — the day Foty-1994-class numbers are on disk, they replace the
  default and the matrix is recomputed. (3) λ = 0.9 is still underived (bulk modulus
  over E₀ — its own membrane, with `grown_arrangement.py`'s soft-λ tissue drain as
  its control case). (4) temp = 12 is the protocol's; E₀ derives from it, so the
  one constant serves both as required — but the degeneracy the theory named is
  real: γ/temp ratios are what the lattice reads.

The 5×5 derived J at the liquidity scale (lattice units, α = 1.566 per mN/m):
MED row [0, 47.23, 19.97, 3.76, 29.61], diagonals [0, 31.48, 13.31, 2.51, 19.74],
off-diagonals B–M 26.25, B–S 33.22, B–T 26.98, M–S 12.18, M–T 17.16, S–T 19.30.

**Phase 2-prerequisite — THE PARALLEL AREA UPDATE (a membrane, stated before the build).**

**STATEMENT.** The volume constraint's failure is not the constraint, it is the STALENESS:
a color pass evaluates ~N³/8 copy attempts against one frozen count vector, so every
attempt spends a marginal computed for a world the first accepted flip already
invalidated. The CPU model converges because each attempt sees the LIVE count
(`matter.py:440-451`, counts updated only on acceptance, sites visited in rng order).
The GPU can reproduce exactly those semantics — serial marginal, parallel geometry — by
CLAIMING the count atomically at evaluation time and rolling the claim back on
rejection. The frozen-count scheme cannot converge at any parameters where the
restoring kick λ(2D±1) exceeds temp (rung-1: 0.9·2·800 = 1440 ≫ 12): its per-pass
cohort overshoots the deficit whenever the eligible boundary exceeds the deficit —
which is always.

**PREDICTION (not yet measured).** With live-claim counts, at n=96, temp=12, λ=0.9,
90 sweeps: (1) the rung-1 trace is monotone-up-to-noise and plateaus — the same two
criteria the Phase-1 falsifier fired on; (2) the per-tissue area fluctuation at the
plateau is σ_a ≈ √(temp/2λ) = √(12/1.8) ≈ 2.6 cells — equipartition on the quadratic
area well, derived, not fitted — not the ±600–800 of the frozen scheme; (3) parity is
restored: differential sorts (bone < muscle < skin), uniform does not; (4) λ=0 stays
monotone (the instrument's regression check).

**FALSIFIER.** Any of (1)–(3) fails. If (2) lands far from √(temp/2λ) (>10×), the
phantom-claim window — a tentative claim visible to concurrent threads before its
rollback — is not negligible, the scheme is not serial-Metropolis, and the deterministic
alternative replaces it: z-slab sub-passes with a count fold per slab, K derived from
σ_a and the boundary measure.

**VERDICT (2026-08-03, all numbers measured).** Two schemes were built; the first killed
itself on this membrane's own falsifier.

1. **Claim-then-rollback** (atomic claim at evaluation, rollback on reject): exact serial
   marginal in theory, and the phantom-claim window was NOT negligible — tissue *grew*
   +200 cells/sweep where the CPU drains −25 and holds (checked to 90 sweeps), H rose
   9.4M → 16.0M. Rejected in-flight claims polluted every concurrent read. The
   falsifier's fallback clause fired.
2. **Read-live, commit-on-acceptance** (plain racy read, atomic claim only if the flip
   happens): the growth reversed immediately. At n=96/90 sweeps: **H falls
   8.87M → 6.51M, plateaus** (tail drift 1.19% of drop); **parity restored** —
   differential sorts (17.2/18.1/24.1 ordered), uniform does not (21.1/18.6/20.9);
   areas hold with means at the CPU's own small drain offset (−19/+29/−59) and the
   plateau area term is 0.15% of H. Both instrument tests pass (trace exact, λ=0
   monotone).

**Two predictions missed, and both misses are recorded rather than reconciled.**
(2) σ_a measured 100–152 cells vs the derived serial scale 2.58 — 50×: the parallel
pass keeps cohort-correlated wander (every cell in a pass still acts on pass-correlated
information); bounded, unbiased, and 5–8× tighter than the frozen scheme's bang-bang,
but it is NOT serial-Metropolis by that measure. Whether Phase 2 needs the last 50×
(the deterministic z-slab scheme remains the named route to it) is the operator's call
— it is instrument purity, a taste terminal. And the monotonicity bar itself: the
membrane's 1%-of-drop was an underived number, and the system falsified it twice —
first with its thermal scale (0.4–1.5% of the drop), then with the shape of the noise:
Boltzmann acceptance permits uphill excursions and domain coarsening makes them
correlated (measured: +131k at sweep 0→1, +129k at 14→15, recovered in 1–2 sweeps), so
ANY per-sweep rise bar fires on physics. What convicts a wrong kernel is a rise that
does not recover. The check in `__main__` is now sustained-rise only: a 10-sweep moving
average may never rise more than 3σ of the mean (thermal/√10). **FINAL VERDICT
(n=96, 200 sweeps): monotone True (6.1k vs 15.0k allowance), plateau True (1.31%),
SORTED True — PASS.** The check still catches both measured pathologies: the frozen
oscillation (±300k forever) and the claim-scheme growth (+6.6M sustained) are both
sustained.

**NAMED COST (the human's terminal).** Acceptance order becomes hardware scheduling
order instead of seeded rng order: one seed no longer gives bit-identical grids. The
CPU model's order is rng-driven (`matter.py:425`), so this is the same KIND of
nondeterminism without the seed. Every quantity this theory measures — plateau H,
σ_a, radius ordering, τ_sort — is order-independent.

**Phase 3 — FRACTURE AND DEATH (Griffith, E2.03).** Add `J/m2` and `Pa.m0.5` to
`folding.UNITS` (the mechanics.json `_units_missing` entry names exactly these);
declare E2.03 and E2.10 (the file marks them declarable-on-request). Rupture rule:
an interface whose accumulated copy-attempt stress exceeds the K_IC-derived threshold
converts to MEDIUM (a crack) — this is the first birth/death the lattice has ever
had, and it is derived, not scripted.

**Phase 4 — THE WORLD.** Extend the mapping to the library's world families
(mineral_dry, metallic, cryo) using their researched cohesion/grain-size; then the
story terms that do not exist yet (`thePlant`, `theRock`… — named by the operator,
per the iron rule that the agent does not pick the term). Grass bending underfoot is
a passive-port property of a grown lattice, not a scripted sway.

**Explicitly NOT in this theory:** cell division, growth-as-increase (the lattice
cannot represent it — medium is the only reservoir), and any coupling of the story
tree's `numbers.json` into the shaker. Both are later membranes with their own
theories. This one is scoped to lose cleanly.

---

## DEBTS FOUND EN ROUTE (housekeeping, not part of the theory)

- `ChimeraEngine/core/matter.py` is a stale clone of `Chimera/core/matter.py` that
  **raises FileNotFoundError at import** (`matter.py:130` — its library path
  `ChimeraEngine/docs/matter/matter_library.json` does not exist). The live tree is
  `Chimera/`; the clone should be deleted or the path fixed. A module that crashes on
  import is a lie of omission in the folder map.
- `WorldModel/simulation/cave_karst_generation.py` is a syntax error (method body
  dedented to class level, `return` outside any function) and its "3D Cellular
  Automata" header is false — it is a biased random walk plus a closed-form
  dissolution formula. It cannot be imported; nothing can depend on it.
- `splat_level.py:4`'s docstring claims "Ground terrain = Cellular Potts grid". The
  code is a jittered 2D point grid with `rng.choice(['sand','rock','ground'])`
  (`splat_level.py:152-186`). The real grid→splat path is `splat_emit.py`. Fix the
  docstring or wire the claim; a doc that duplicates a fact will drift from it.
- `ChimeraEngine/tests/` has zero matter coverage. Correctness rests on the contrast
  proofs (`parity_report`, `matter.py main()`). Phase 1's energy trace belongs under
  test.

---

## THE OPEN RULINGS (the human's terminals)

1. **ENOUGH on this theory?** Rule on the statement before Phase 1 is built.
2. **The term name.** When Phase 4 arrives, the new world membranes (thePlant? theRock?
   theSoil?) are named by the operator — the engine's rule, not a courtesy.
3. **The kinetic freedom.** The one scale (α through E₀, or equivalently temp) —
   derive-from-physical-temperature and publish the disagreement, or train it against
   a named objective. Both are legal; it is a taste call about which terminal the
   number answers to.
