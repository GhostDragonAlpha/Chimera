# THE STATE MACHINE PHYSICS FRAMEWORK

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
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **Every game concept is a state machine. Every state machine has measurable physics.**
> The LLM writes the objective. The trainer turns the crank. Physics decides the answer.

## The Theory

Elements and principles — the same concepts from art — apply to game design at every scale:

| | Art | Game Design | Engine Code |
|---|---|---|---|
| **Elements** | Line, shape, color, texture | Matter bricks, Gaussian primitives, state nodes | FVector, UCLASS, UFUNCTION |
| **Principles** | Balance, contrast, rhythm | Physics, constraints, Design Laws | Compile rules, frame budget, memory layout |
| **AI Shaker** | — | Trainer (seed→mutate→measure) | Generator (genome→C++→compile→measure) |

The theory in practice: **every game artifact can be reduced to irreducible elements, governed by measurable principles, and discovered by the trainer rather than authored by hand.**

## Proven at Every Scale

| Domain | Elements | Principles | What Emerged |
|---|---|---|---|
| `granular.py` | Sand cells, cohesion, quenched thresholds | Angle of repose, avalanche dynamics | 40.03° repose angle (matches lunar regolith research) |
| `creature.py` / `walker_gpu.py` | Bones, joints, muscles | Gravity, torque, contact physics | Walking gait with periodicity 0.98, discovered feet it was never told about |
| `bigbang_gpu.py` | Particles, gravity, inelastic mergers | Kepler's laws, angular momentum conservation | Kepler's third law (slope 1.50, r²=1.000), planets from accretion |
| `planet.py` | Star flux, albedo, greenhouse, condensation | Energy balance, Jeans escape | Habitable zone emerged; learned constants converged on research values |
| `memorial.py` | Sacrifice weights, star brightness curve | Design Law 2 (costless = dim) | Discriminable brightness between generous and costless players |
| `economy.py` | Supply, demand, trade routes | Market equilibrium, arbitrage | Price discovery without hand-tuned values |
| `erisaid_mirror.py` | Reflection types, proximity zones, light levels | Proximity governs state, brightness = sacrifice | Steep curve (k=3.46), 54 reflections, 80% dwell in FOCUSED zone |

## The Domain Pattern

Every trainable domain has three functions:

```python
def seed(rng=None) -> dict:
    """Random genome. The genome IS the configuration of elements."""
    return {"param1": rng.uniform(0, 1), "param2": rng.randint(1, 10)}

def mutate(genome: dict, rng=None) -> dict:
    """Perturb the genome. Small changes to continuous, occasional to discrete."""
    g = copy.deepcopy(genome)
    g["param1"] *= math.exp(rng.uniform(-0.2, 0.2))
    return g

def measure(genome: dict) -> dict:
    """Simulate and report FACTS, not opinions. No adjectives, no scores."""
    return {"metric1": 0.5, "metric2": 3.14}
```

**The domain reports FACTS only.** It never says something is "good" or "bad." What GOOD means lives in `docs/objectives/<name>.json`, written from Design Laws as physics statements.

## The Objective Pattern

```json
{
  "maximize": ["information_per_step", "costless_self_visible_fraction"],
  "minimize": ["comprehension_time"],
  "constraints": [
    {"field": "comprehension_time_worst", "max": 80},
    {"field": "dwell_idle", "max": 0.5}
  ],
  "walls": {
    "costless_self_visible_fraction": "Design Law 2: a costless life MUST be visible"
  }
}
```

**Walls are load-bearing.** A degenerate winner is the optimiser auditing your spec at 35kHz. Walls name the boundaries it must stay within.

## The State Machine Pattern

Every game concept can be encoded as a state machine with physics:

```
States: IDLE → APPROACHING → BROWSING → FOCUSED → SELECTED → TRANSITIONING
Transitions: driven by physical proximity, item possession, time
Physics: comprehension_time, information_per_step, navigation_efficiency
```

The state machine IS the genome. The transitions ARE the mutation space. The physics measurement IS the fitness function.

## Training Command

```powershell
cd E:\PythonChimera\Chimera
python -m core.trainer --domain core.trainables.erisaid_mirror --objective docs/objectives/erisaid_mirror.json --pop 100 --gens 100
```

For GPU-accelerated training (domains with `measure_batch`):
```powershell
python -m core.trainer --domain core.trainables.brain_gpu --objective docs/objectives/brain_gpu.json --pop 1024 --gens 300
```

## Creating a New Domain

1. **Catalog elements**: what are the irreducible building blocks? (Reflection types, proximity zones, light levels — not "button" or "slider")
2. **Define principles**: what physics govern combination? (Proximity → state, brightness → importance, bearing → golden angle)
3. **Encode the state machine**: what states exist? What drives transitions? What can the trainer mutate?
4. **Write `measure()`**: simulate the system and report numbers. No opinions. Facts only.
5. **Write the objective**: what does GOOD mean in physics? What walls must not be crossed?
6. **Train**: `python -m core.trainer --domain core.trainables.<name> --objective docs/objectives/<name>.json`
7. **Read the PINNED walls**: the trainer prints what boundaries the winner is riding. Fix the objective, retrain.

## THE RULE

**The LLM writes the CONSTRAINTS. The trainer turns the crank. Physics decides the answer.**

The LLM sits at the TOP (writing objectives) and the BOTTOM (interpreting results), never the middle (authoring artifacts). The trainer does ~30,000 evals/sec — six orders of magnitude faster than the LLM authoring by hand. A degenerate winner is not a failure — it is the optimiser finding the hole in your spec that you would have defended in review.

**Iterate the objective, never the artifact.**
