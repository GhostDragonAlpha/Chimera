# WALKING MECHANICS — the cited numbers behind the gait reward

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
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> The real biomechanics that replace a hand-tuned speed knob. Each is a **reward term trained against
> reality's numbers**, not my taste. The canoe analogy (momentum preserved by resistance, balance kept
> between strokes, paddle placed deliberately) maps exactly onto these three named, quantified
> mechanisms. Foundation first (quasi-static walk), then layer these in for a natural, gravity-adaptive
> stride.

## 1. Pendular energy recovery (Cavagna) — the "momentum-preservation %"

Walking is an **inverted pendulum**: the body vaults *over* the planted foot, trading kinetic (KE,
forward speed) and gravitational potential (PE, CoM height) energy **out of phase** — as the CoM rises
it slows, as it falls it speeds up. Recovery peaks at **~65%** at intermediate speed (**~4 km/h ≈
1.1–1.3 m/s**), which is also the metabolic-cost minimum. Below that, vertical work Wv > forward work
Wf; above, Wf > Wv; either way cost/km rises.

- Recovery = (|Wv| + |Wf| − Wext) / (|Wv| + |Wf|).
- **Reward term:** reward the **anti-phase KE↔PE exchange** over each step (PE up while KE down and
  vice-versa) — the pendular signature. This rewards *carrying* momentum, not brute-forcing speed.

## 2. Capture point / extrapolated CoM (Hof) — foot placement, and the Moon

To not fall, plant the next foot relative to where momentum is carrying you. The **extrapolated CoM**
(a.k.a. **capture point**):

> **XcoM = x + v / ω₀,   where   ω₀ = √(g / L)**   (x = CoM position, v = CoM velocity, L ≈ leg length)

Rule (Hof): at foot contact the center of pressure (the foot) sits a fixed distance **behind and
outward** of the XcoM. A velocity disturbance Δv is caught by shifting the foot **Δv / ω₀** in the same
direction — deliberate placement, your "place the paddle to avoid debris."

- **Gravity-scaled, for free:** ω₀ = √(g/L). On the Moon g is 1/6, so ω₀ is ~2.4× smaller → the foot
  plants **~2.4× further ahead** and the pendulum swings slower → the long, floaty Moon stride *emerges
  from the equation*. One formula, every world.
- **Reward term:** reward foot placement near the XcoM (slightly behind + outward). Gravity is an input
  (`ω₀ ∝ √g`), so the same term walks on any planet.

## 3. Ground reaction force profile — the resistance that directs momentum

The paddle-in-water. The planted foot's **GRF**:

- **Vertical:** a **double-hump**, peaks **~120% body weight** (just after contact, and before push-off),
  dipping to **~80% BW** at mid-stance as the body vaults over the foot.
- **Anterior–posterior:** **braking then propulsion**, peaks **~20% BW**; **braking impulse ≈ propulsion
  impulse** at constant speed (net A-P impulse ≈ 0 = momentum conserved).
- **Friction cone:** horizontal GRF < μ × vertical GRF or the foot slips — the "resistance keeps the
  canoe from going sideways." **We already have this** (`planner.py`, tan θ < μ).
- **Reward term:** reward a realistic GRF shape (double-hump vertical, balanced braking/propulsion
  impulse) and keep every contact inside the friction cone.

## Integration plan

1. **Quasi-static walk (training now)** — slow, always-balanced steps; the foundation.
2. **+ capture-point foot placement** (term 2) — the single highest-value add: it makes the gait
   *catch itself* AND makes it gravity-adaptive (Moon/Mars/Earth) in one term.
3. **+ pendular exchange** (term 1) — turns a shuffle into an efficient stride that *carries* momentum.
4. **+ GRF shaping** (term 3) — a natural heel-strike-to-push-off contact profile.

Each is cited, measurable, and trained — no hand-tuned coefficients where a real number exists.

## Sources
- Cavagna et al., pendular energy recovery (~65%): [The sources of external work in level walking and running](https://pubmed.ncbi.nlm.nih.gov/1011078/) · [Pendular energy transduction within the step](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0186963) · reduced-gravity walking energetics: [Walking in simulated reduced gravity](https://journals.physiology.org/doi/full/10.1152/jappl.1999.86.1.383)
- Hof, extrapolated CoM / capture point (XcoM = x + v/ω₀): [The 'extrapolated center of mass' concept](https://pubmed.ncbi.nlm.nih.gov/17935808/)
- Ground reaction force profiles (double-hump ~120% BW, A-P ~20% BW): [GRF in normal gait](https://pmc.ncbi.nlm.nih.gov/articles/PMC4311602/)
