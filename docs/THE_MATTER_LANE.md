# THE MATTER LANE — passive tissue for everything that is not a person

**2026-08-04.** `docs/THE_COMPILER.md` states that passive tissue is universal —

    ligament : human  ::  cellulose : grass  ::  crystal lattice : rock  ::  rebar : wall

— and then says, in its own words, that the table is a *design*: grass, rock, tree, building,
vehicle, fabric and terrain had **zero validated ports**. This lane is the beginning of paying that
down, plus two ledger debts and one instrument.

Every port lives in `tools/port_tests_matter.py` and runs through the same harness as the human's
twelve (`python tools/port_tests.py`). Every constant is ingested through `tools/matter_data.py`,
which raises rather than default.

---

## THE SEVEN PORTS

| # | port | statement | falsifier's fate |
|---|---|---|---|
| 13 | `grass_blade` | a lamina is a DISTRIBUTED beam, not a lumped root spring | **FIRED at 200%**, not the 5% asked |
| 14 | `rock_fracture` | σ = Eε to σ_t, with E/σ_t/K_IC over-determined | **UNMEETABLE as written** — see below |
| 15 | `tree_trunk` | orthotropic wood: E_L bends it, G_LR shears it | held to <0.01% at three slendernesses |
| 16 | `terrain_footprint` | a stiffness and a strength must land on one millimetre | **FIRED on the live membrane** |
| 17 | `granular_repose` | θ_r = atan(μ) only for a grain that cannot roll | closed form **bracketed, not reached** |
| 18 | `fibre_rope` | F = kx from published strain-at-10%-BS | **F = kx REFUTED for polyester** |
| 19 | `suspension` | F = kx + cv with k and c DERIVED, not ingested | held to 0.02% |

### 13 · The blade — the answer depends on how you load it

`E = 554 MPa` (Vincent 1982, *J. Mater. Sci.* 17:856, *Lolium perenne* — the canonical
measurement). A lumped torsional spring at the blade's base is **EXACT under a pure moment**
(every station of a cantilever under an end couple carries the same moment) and **3× too stiff
under a tip force**. Worse: matching tip *deflection* needs `k = 3EI/L`, matching root *slope*
needs `k = 2EI/L`, and **no single spring does both** — 50% apart.

**A foot on grass is a tip force.** So the lumped spring is wrong for the one thing grass is asked
to do, and the size of the wrongness is derived rather than measured.

*Refused:* blade damping `c`. Vincent publishes a dynamic modulus (44.38 MPa against 554 static)
which *proves* the blade is viscoelastic — but no loss factor is published, and `c` may not be
chosen.

### 14 · The rock — and a falsifier tighter than its own literature

Three studies, never citing each other: `E = 78 ± 19 GPa` (Quaglio 2020, via the world's library),
`σ_t = 14.5 ± 3.3 MPa` and `UCS = 266 ± 98 MPa` (Schultz 1993), `K_IC = 2.4 MPa√m` (Balme 2004).
The triple is **over-determined**, so the Griffith flaw that reconciles them is a prediction:

    a = (K_IC/σ_t)²/π = 8.72 mm

— a **vesicle** scale, not a mineral-grain scale. (The library's 2 mm "grain size" may NOT be
substituted: its own note says it is surface texture.)

And Griffith 1921 predicts `UCS/σ_t = 8` for elliptical flaws. The published pair says **18.3**.
The 2.3× excess *is* the known crack-closure correction — the law loses cleanly and the amount it
loses by is the finding.

> **THE FALSIFIER AS BRIEFED COULD NOT BE MET BY ANY MODEL.** It asked fracture to land within 20%
> of the derived load. σ_t is published as 14.5 ± 3.3 MPa — **the literature's own spread is
> 22.8%**. A model reproducing basalt perfectly would fail that bar one time in three. A tolerance
> can be too *tight* for its data as easily as too loose, and both are the same defect: a number
> with no source.

### 15 · The trunk — and why a tree never fails in shear

White oak, USDA Wood Handbook Tables 5-1 and 5-3b (the ratios and the absolute come from
*different tables*, so multiplying them is the derivation): `E_L = 12.3 GPa`, `G_LR/E_L = 0.086`.
An isotropic solid has `G/E ≈ 0.385` — **wood is 4.47× more shear-compliant relative to its
bending stiffness**, and that is what orthotropy costs.

The shear share is `(3/16)(E_L/G_LR)(d/L)²/κ`, exact at L/d = 5, 10 and 20. Bending stress grows
with L and shear stress does not, so the failure mode switches at

    L/d = 3·MOR/(16·τ_∥) = 1.43

No tree is stubbier than 1.43, so **a trunk always fails in bending** — which is what licenses the
bending model to be the whole model. It could have come back at 20 and forced a shear port.

*Refused:* a trunk diameter. No chapter grows a wood, so the claim is stated in `L/d`, which is
dimensionless and does not care what diameter arrives later.

### 16 · The footprint — the port that convicted a live membrane

Two literatures that never cite each other, fed this world's own published foot pressure:

| route | says |
|---|---|
| Terzaghi's subgrade modulus (a **stiffness**) | 3.84 mm, elastic, recoverable |
| Terzaghi's bearing capacity (a **strength**) | 3.12 mm, plastic, permanent |

A factor of 1.23 apart, measured by different people for different purposes. **That agreement is
the only reason to believe either.**

Then the port read what `theGround` publishes: **`sinkage_m = 8.674e-19`** — 0.87 attometres, a
thousand times smaller than a proton, and 4.4×10¹⁵ times smaller than its own soil's elastic
settlement. Backtraced *up* the chain: a typed `COHESION_PA = 2000.0` under the comment *"damp
soil holds itself together a little"*, where the world's own library publishes **0.5 ± 0.4 kPa**
(Mitchell et al. 1972). Four times the researched mean, and it set the zero-depth capacity to
92 kPa — 3.8× the pressure under a person — so the bisection balanced before it began.

**Nothing in this world could leave a footprint, and nothing said so.** Same species as the
`g = 7.076` defect: a wrong number under a formula that still looks alive. **Fixed — see below.**

*Refused:* a footprint DEPTH as a validated number. Across cohesion's own ±0.4 kPa the print runs
54 mm → **zero**; at the high end nothing dents at all. A gap inside the instrument's grain is not
a small gap. The **elastic** branch carries no cohesion and is resolvable; that is the half the
port validates.

### 17 · The pile — a friction coefficient does not determine a repose angle

At this world's published φ = 35°, rigid grains **bracket** `atan(μ)` rather than reach it:

    spheres  0.0°   <   atan(μ) 35.0°   <   boxes  66.2°

Identical friction, identical grain mass, identical column, identical seed — **shape alone** moves
it 66°. A sphere rolls out of the friction it is standing on and never stops (its heap height is
fixed at one radius while the grains roll outward forever at 0.80 m/s, because nothing in a rigid
sphere contact resists rolling). A box interlocks and holds more than sliding friction allows.

So a rigid-body engine cannot produce a repose angle from a friction coefficient — **which is why
this world grows its regolith from a topple rule**, and why theGround's grown 40.03° (emergent,
never looked up) landing 0.03° from the centre of Mitchell's published 30–50° band means something.

### 18 · The rope — refuted by two numbers from one standard

A rope has no Young's modulus: it is a helix that stiffens as its lay tightens, which is why the
industry publishes *strain at a stated fraction of breaking strength*. Take that as `F = kx`
(`EA = 0.1·F_break/ε@10%`) and extrapolate to the rated Working Load Limit (`F_break/5`):

| fibre | strain at WLL | published break | of the way to failure |
|---|---|---|---|
| nylon | 5.00% | 21.5% | 23% |
| **polyester** | **12.00%** | **12.5%** | **96%** |

A polyester rope at its RATED load would be at 96% of its own published breaking elongation. It
plainly is not — that is what "rated" means — so the real curve **stiffens**, and the secant taken
at 10% BS is its softest part. **No experiment was needed to see it.**

*Refused:* the seam. A splice fails at a published *fraction* of rope strength and no such fraction
is in `matter_data`, so none is invented.

### 19 · The suspension — Rule 1 applied to the obvious temptation

There **is** a published (k, c) pair for the quarter car — 20,000 N/m and 545.5 N·s/m — and
ingesting it would have looked legitimate and been wrong. Together with the published 250 kg they
imply `f_n = 1.424 Hz` (the **sport** band, 1.2–1.5) and `ζ = 0.122` (**below** the whole
passenger-car range, 0.2–0.4). **The "default quarter car" is a sport spring with an under-damped
shock**, and citing it as a comfort car is the right quantity at the wrong interface.

Deriving instead from the dynamic targets — ride 1.10 Hz, ζ 0.30 — gives `k = 11942.2 N/m`,
`c = 1036.7 N·s/m`, and makes the slider real: move the ride frequency and every number moves.

---

## THE FIX — theGround's cohesion, and what it cost downstream

**STATEMENT.** theGround's bearing cohesion is not a free number: the world's own library publishes
it, and the membrane typed it at 4× the researched mean.

**PREDICTION, before the edit.** capacity 110.4 → 41.2 kPa · `ground_holds_it` stays True with
margin 4.56 → 1.70 · `carries_reference_load` stays True · Earth probe sinkage 7.5 mm, still under
20 mm · theHuman's derived print reproduces the port's independent 3.122 mm.

**FALSIFIERS, named before the run.** (1) the person falls through · (2) a standard bearing plate
sinks · (3) the Earth control breaks · (4) chain_witness or the folding audit regress from
42 working/0 broken and 0 impossible values · (5) the two derivations disagree.

**RESULT.** 1, 2, 3 and 5 held — the two independently written derivations agree to four decimals
(3.1220 mm against 3.1220 mm, sharing no code). **Falsifier 4 FIRED**: chain_witness went
42/0 → 41/**1 broken** and the folding audit found **2 impossible values**.

Both were **correct physics surfacing through names that cannot express it** — the audit doing
exactly its job:

- `theLoad.settle_cargo_kg = −40.9` — with the true, weaker soil the suited body alone already
  exceeds the allowable bearing pressure, so the cargo it may add before the ground prints is
  genuinely negative. **A signed headroom published under a name that means a mass.** Now clamped
  at zero, with `settle_exceeded_unloaded` and `settle_over_by_kg` carrying the other side.
- `theThrust.landing_give_required_frac = inf` — no amount of give suffices, which is the honest
  answer to the wrong question. **A fraction lives in 0..1.** Now capped at 1.0 with
  `landing_give_suffices = False` and the shortfall published as
  `landing_softest_overpressure_ratio = 1.712`, a ratio, which has no such bound.

**AND THE PHYSICS IS A GAME FACT.** `landing_ground_holds = False`, `takeoff_ground_holds = False`:
on this world's real regolith **you cannot jump without your feet punching in**, however softly you
land. That is what jumping on dry sand does.

**AND THE PRINT IS SHALLOWER THAN GRAVITY EXPLAINS.** The same body on the same soil leaves
**20.9 mm** at Earth gravity and **3.1 mm** here — 6.7× for a gravity ratio of 1.39×, because
cohesion does not scale with *g* while the load does. A low-gravity world sits nearer the threshold
at which prints stop existing. Nothing was fitted to produce it.

**Final state:** grow 42 membranes · chain_witness 42 working / 0 stubs / 0 broken · folding audit
0 impossible / 0 inconsistent · 19/19 ports · 7/7 primitives · terrain_witness 0.000 mm gap.

**The conviction became a REGRESSION GUARD.** `terrain_footprint` now checks that theGround's
published cohesion matches the library and that theHuman's derived print matches its own — re-type
the constant and the port fires again. A witness that keeps reporting a repaired defect as live is
the stale-copy failure this studio has convicted four times in one day.

---

## THE TWO LEDGER DEBTS

**Phase 7 — metal as frozen structure.** Re-ran `python -m core.matter_derive --frozen-metal`.
**All four falsifiers PASS**, including **B2** (rock 15.1 < ice 23.7 < sand 25.5), which had fired
in the recorded run and whose caveat blamed scheduling noise. The caveat was right. Metal holds
14,246/14,246. **Closed.**

**Phase 8 — deficit-paired swaps.** Ran it. `docs/THE_LIVING_MATTER.md` recorded the debt as
**PAID**; it is not.

| arm | sorted | final H | drift |
|---|---|---|---|
| swap-only | **5/5** | 21.53M … 21.55M (spread **1.00×**) | `[0,0,0]` every seed |
| mixed | **3/5** | 21.53M … 97.12M (spread **4.51×**) | `[0,0,0]` or ±100s |

`_potts_swap_pass` is never passed the area array — a swap is volume-neutral — while
`_potts_color_pass` does an **atomic read-modify-write on the shared per-type area accumulator**,
so every copy thread's ΔH depends on the order other threads' atomics land. **The swap arm is
bit-deterministic and the mixed arm is not.**

**The tell:** every mixed run that *sorts* reports radii, drift and H identical to swap-only. Drift
of exactly zero is structurally the swap channel's signature — **a "passing" mixed run is one in
which the copy channel did nothing.** The recorded 800-sweep PASS did not measure the interleave
working; it measured the interleave being absent. And the cold-monotone gate that earned the swap
kernel its keep was run *swap-only*: the interleaved path was never gated.

**ONE ROLLOUT IS A COIN TOSS applies to the shaker, not only to a gait.** Both the 200-sweep FIRED
and the 800-sweep PASS were single runs of an order-dependent process.
`tools/phase8_repeat.py` reports the rate. **Closure withdrawn; the debt is open at 60%.**

What survives, and it is the valuable half: **tissue-real K by pure Kawasaki exchange is real and
reproducible.**

---

## THE INSTRUMENT — `tools/splat_density.py`

The blind read said *"low detail"*. That is not a number. A blob and a sieve are opposite failures
and both read that way, so one density figure cannot diagnose it. Measurement only; no scene is
touched. Footprint factor **measured** through the real pipeline (2.67× nominal) — the tool
**refuses** rather than fall back to nominal.

| object | splats | dia | overdraw | holes | verdict |
|---|---|---|---|---|---|
| Stone | 640 | 5.56 px | 2.2× | 7.1% | Nyquist PASS; spends **7.6×** what solidity needs |
| Tuft | 143 | 13.67 px | 2.0× | 16.7% | at the Nyquist edge; **under**-spent (needs 368) |
| Pile | 1600 | 23.44 px | 16.0× | 17.1% | **2.67× over Nyquist — no count fixes it** |

Two bounds, neither chosen: **A** Nyquist (splat ≤ feature/2, feature from the object's own
published geometry) and **B** solidity (`n = (silhouette/splat_area)·ln(1/h)`, the random-coverage
result, **checked against the measured holes before it is used**). The Pile's model *under*-reads
its holes — the signature of splats stacked rather than spread — so it is a blob and a sieve at
once.

---

## THE FOUR INSTRUMENT DEFECTS, every one returning a plausible number first

Expect the same shape next time. None of these was a physics error:

1. **MuJoCo applies `xfrc_applied` at a body's CENTRE OF MASS.** A tip load acted half a segment
   short and read as a **3.10% "discretisation"** — right in the range a discretisation would
   occupy, on a test whose entire purpose was catching discretisation. Predicting the load-at-CoM
   chain instead matched to 0.04%, which is what said the ENGINE was right and the INSTRUMENT was
   wrong. Fixed by making the application point explicit (`mj_applyFT`).
2. **One fixed timestep cannot serve grass and basalt.** 0.0005 s was carried over from the human
   ports; a basalt segment's period is 76 µs, so the step was six and a half periods long. The rod
   returned **0.000 µm of stretch with |qvel| exactly 0** — a perfectly rigid rock, reported
   without complaint. The step is derived from the stiffest mode now.
3. **A convergence test watching `z` during an AXIAL pull.** It declared the rock chain converged
   after 800 steps, satisfied by a coordinate the experiment does not act on.
4. **`abs(qvel).max()` on a freejoint compares rad/s against a m/s bound.** For a 20 mm grain
   ω = v/r multiplies by 50, so the gate refused a correct run as "not at rest at 35.7" when
   35.7 rad/s is 0.71 m/s — exactly the speed a 0.36 m collapse delivers.

And one **falsifier** defect, which is the same disease in the judge rather than the instrument:
the granular port's first version **PASSED on a flat scatter**, because "shallower than atan(μ)" is
satisfied perfectly by no pile at all. The height gate now forbids it.

---

## WHERE IT STANDS

**19/19 ports · 7/7 primitives · 8/11 actions (1 REFUSED).** One port per object is a beginning,
not a passive-tissue model: each row of THE_COMPILER's table names several ports and exactly one of
them has a measured falsifier. **Building still has zero and may not be cited.**

```bash
python tools/port_tests.py && python tools/primitive_tests.py && python tools/action_tests.py
python tools/matter_data.py --audit      # the 43 constants and their sources
python tools/splat_density.py            # the density table
python tools/phase8_repeat.py --runs 5   # the mixed arm as a distribution
```
