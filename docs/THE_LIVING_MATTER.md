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

> Drafted 2026-08-03. Status: **THEORY, UNRUN.** Nothing in this file has been executed.
> The instrument it needs (per-pass energy readout) does not exist yet — that is Phase 1,
> and building the instrument before the run is the method, not a delay.

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

**Phase 1 — THE INSTRUMENT.** The shaker has no energy readout; you cannot measure a
relaxation you cannot see. Add to `Chimera/core/matter_gpu.py`:
- per-pass Hamiltonian evaluation on-device (interface energy + area term), folded
  into the existing pass structure — zero CPU↔GPU syncs inside the sweep loop, one
  readback of the energy TRACE at the end (the readback discipline is already the
  code's own rule, `matter_gpu.py:128-138, 184-185`);
- a persistent lattice: `open_lattice(...) → handle`, `step(handle, n_passes) →
  energy_trace`, `close(handle) → grid`. The kernels are already per-color-pass; this
  is a host-wrapper change, not a rewrite.
- Falsifier for the phase itself: energy trace of the rung-1 control is non-monotone
  or does not plateau — then the Hamiltonian we think we are running is not the one
  in the kernel.

**Phase 2 — THE CONTROL.** Research the tissue surface tensions; derive the 5×5 J for
bone/muscle/skin/tendon/medium through the mapping above; run the rung-1 scramble;
read τ_sort and the anatomy off the trace. F1, F2, F3 all live here. This is the run
the theory can lose.

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
