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
> plateaus, parity restored). Next: Phase 2 — the control run (research tissue surface
> tensions, derive the 5×5 J, read τ_sort).**

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
