# The Training Protocol — build features by evolving them, not by authoring them

> **The LLM writes the CONSTRAINTS. The optimiser turns the crank. Neither is trusted.**
>
> Established 2026-07-14. Proven on two utterly different features with one tool.

---

## 0. The shape of it

```
        SCENARIO                     (a human, in words: "progression should feel earned")
            |
         [ LLM ]                     writes the CONSTRAINTS -> docs/objectives/<f>.json
            |                        declarative · numeric · reviewable · FALSIFIABLE
            v
        OBJECTIVE
            |
       [ TRAINER ]                   core/trainer.py — 26,000–37,000 evals/sec, MEASURED.
            |                        NO LLM ANYWHERE IN THIS LOOP.
            v
     WINNER + PINNED WALLS
            |
         [ LLM ]                     reads the exploits. REPAIRS THE OBJECTIVE.
            `--------------------------------------------------------^
```

**The LLM sits at the TOP and at the BOTTOM. Never in the middle.**

An LLM hand-tuning a feature manages **~20 edits an hour**. The trainer does **~30,000 a
second**. That is six orders of magnitude, and it is why hand-tuning a generative system
with a reasoning model is moving weights with tweezers.

---

## 1. The three-part split

| part | who writes it | what it knows |
|---|---|---|
| **DOMAIN** — `core/trainables/<f>.py` | code | `seed()` · `mutate(g, rng)` · `measure(g) -> {name: number}`. **Facts. Never opinions.** |
| **OBJECTIVE** — `docs/objectives/<f>.json` | **the LLM** | which facts are GOOD. "What good means", stated once. |
| **TRAINER** — `core/trainer.py` | generic | nothing. It does not know what a creature or an economy *is*. |

A domain **reports what happened**. An objective **says which outcomes are good**. Keeping
them apart is what lets one trainer drive every feature in the game — and what lets the
LLM change the definition of "good" without touching a line of simulation code.

```powershell
python -m core.trainer --domain core.trainables.economy `
                       --objective docs/objectives/economy.json `
                       --pop 500 --gens 800
```

---

## 2. THE HARD BOUNDARY: you can train DATA. You cannot train CODE.

Everything turns on cost-per-evaluation:

| feature | one eval | evals/sec (24 cores) | per night |
|---|---|---|---|
| morphology — creatures, plants, caves, terrain | **1.5 ms** | **~35,000** | ~10⁹ |
| balance — prices, DPS, yields, rewards | 1–10 ms | 5,000–20,000 | ~10⁸ |
| level layout — connectivity, pacing, sightlines | 10–50 ms | ~2,000 | ~10⁷ |
| locomotion — physics, gaits | 100–500 ms | ~100 | ~10⁶ |
| **C++ SYSTEMS** | **LLM 60 s + UBT 300 s + PIE 60 s** | **0.002** | **~70** |

That last row is **seven orders of magnitude**. Evolving code by search costs ~139 days for
10⁴ evaluations on this box, and UBT already eats all 24 cores so parallelism does not save
you. **The generator is the bottleneck, not the optimiser.**

### The corollary — an architectural directive

> **Push as much of the game as possible OUT of code and INTO data.**

This studio already did this and did not notice what it had built:

> *CLAUDE.md: "Development flows top-down: game content changes go in the DSL spec; code-shape
> changes go in the generator; the pipeline regenerates the C++."*

**THE DSL IS THE GENOME.** `core/game_code_generator.py` is the developmental program. The
compiled game is the phenotype. The genotype→phenotype pipeline has existed here for months —
it was simply mutated **by hand**.

- DSL **parameters** (prices, damage, yields, spawn rates) need **no rebuild** → **TRAIN THEM**.
- DSL **structure** (new systems, new verbs) needs the full build → **LLM-authored, one at a time.**

---

## 3. THE EXPLOIT IS THE PRODUCT

**A degenerate winner is not a failure. It is the optimiser auditing your specification at
35 kHz and finding the hole you would have defended in code review.**

`Objective.pinned()` reports the walls the winner is **pressed against**. Wherever the
optimiser is riding a wall, it is extracting everything that wall permits — and that is
exactly where your spec is load-bearing, and exactly where the next exploit hides.

### The three exploits of 2026-07-14, in order

1. **THE LOLLIPOP.** Objective was `height × base × margin`. Winner: a boulder on a pole over a
   tripod. **Why:** mass goes as *r²*, and parsimony was charged **per bone** — so ONE enormous
   bone was free. *Fixes:* charge metabolic cost by **volume**; cap bone aspect ratio
   (`MAX_ASPECT = 0.35` — real bones have one); and replace static stability with the
   **TIPPING ANGLE**, `atan(margin / height)`. A lollipop tips at 7.8°, a quadruped at 26.6°.

2. **THE SATISFICER.** Score is a weighted **geometric mean of satisfactions**, each capped at
   1.0. Once every constraint reads `sat = 1.00`, the score is `1.0000` and **there is no
   gradient left to climb**. I read `best 1.0000` for 700 generations as *converged*. It was
   not converged — **it was finished, because I had given it nothing left to want.**
   > **A spec made only of walls gets you exactly the walls.**
   *Fix:* every objective needs at least one `maximize` / `minimize` term that keeps paying
   **past** the bound. Adding one took `tip_deg` from 22.04 (riding its min of 22) to 31.53.

3. **THE MAST WITH OUTRIGGERS.** Legs sprawled *flat on the ground* — a huge support polygon
   contributing almost no mass — while a heavy rod held the centre of gravity high. Statically
   excellent, biologically absurd.
   > **Three exploits in a row is not a message about your parameters. It is a message about
   > your FRAME.**
   Static stability can **always** be gamed by outriggers, because a creature is not defined by
   how it *stands* — it is defined by what it **does**. The objective must be **LOCOMOTION**
   (distance travelled under physics), which cannot be faked, because outriggers do not walk.

### The fourth exploit, and it was not in the objective at all

4. **THE LOTTERY TICKET.** The winner of the locomotion objective travelled **13.52 body
   lengths** and satisfied every constraint. It was not a gait. It was not even a *bad* gait.
   `core/gait.py` gave it **periodicity 0.25** — there is no repeating cycle anywhere in its
   footfall. And `converge.py` gave the killing blow: nudge its starting height by **one
   micron** (1e-6 m, a hundredth of a human hair) and it loses **5.5 body lengths**. Make the
   solver progressively more exact and the answer never settles — 13.5 / 5.4 / 4.0 / 10.5 /
   14.2. That is **Lyapunov divergence**. No attractor → no limit cycle → **no gait**.

   > **The first three exploits were holes in the OBJECTIVE. This one was a hole in the
   > EVALUATION, and no objective — however perfect — could have closed it.**

   Every genome was scored by **one rollout from one exact initial pose**. In a chaotic system
   that is not a measurement, it is a **coin toss** — so "fitness" was decided by which side of
   a bifurcation the creature happened to fall on, and the GA spent 80,000 evaluations
   selecting **lucky dice**. Proof: re-scored under honest physics, that champion manages
   **2.41 body lengths — worse than an UNTRAINED brain (2.81).** It had learned nothing that
   was about the world. It had learned the seed.

**Record every exploit**: `python -m core.graphify_record surprise --context "..." --reality "..."`

---

## 3.5 EVALUATE HONESTLY — one rollout is a coin toss, not a measurement

**This is the hardest lesson the studio has learned, and it invalidated every number the
creature work had produced.**

### The rule

> **Score every genome from N randomized initial conditions and keep the WORST.**

A lucky roll cannot survive sixteen of them. Report both, and let the objective choose:

| measure | meaning |
|---|---|
| `distance` | **mean** over N restarts — the headline, and no longer a single lucky roll |
| `distance_worst` | **min** over N restarts |
| `robustness` | `worst / mean`. **THE ANTI-LOTTERY.** A real limit cycle converges onto the same gait from every start → **~1.0**. A chaotic fraud → **~0**. |

Perturb generously — we *proved* 1e-6 m is already decisive, so anything a real gait can
absorb is fair game (`brain_gpu.py`: base height ±2 cm, every joint ±0.03 rad, body tilt
±0.02 rad). **Restart 0 is left unperturbed**, so the old single-shot number stays readable
and comparable.

### And add the term that makes a gait a gait

Nothing in any objective had ever rewarded **rhythm**. So nothing ever stopped the optimiser
from producing a convulsion that happened to travel — and nothing ever *would* have.

> **A GAIT IS A LIMIT CYCLE.** `periodicity` (autocorrelation of the footfall signal; 1.0 = a
> metronome, 0.0 = a seizure) belongs in every locomotion objective, weighted **equal to
> distance**. It is the one thing that separates locomotion from *falling with style*.

### The cost, and therefore the GPU

Honest evaluation is **N× more expensive per genome**. At N=16 that is unaffordable on a CPU
(≈32 h/run, 8 P-cores pinned at thermal limit) and **free on a GPU**, because population and
restarts are *the same axis* — `1024 genomes × 16 restarts = 16,384 worlds`, one kernel:

| backend | throughput | cost |
|---|---|---|
| pybullet, 30 processes | **70 evals/sec** | 8 P-cores pinned, thermally throttled |
| `mujoco-warp`, 16,384 worlds | **2,358 evals/sec** | 6.95 s, **1.5 of 24 GiB**, GPU at 39 °C |

> **The correct evaluation is what the CPU cannot afford and the GPU does not notice. The
> 33.7× is a side effect; the reason to move was CORRECTNESS.**

### Before you blame the optimiser, AUDIT THE PHYSICS YOU INHERITED

The chaos had a cause, and it was not the solver. `TORQUE = 22 N·m` had been carried forward
from the CPG walker and never questioned. On a **0.622 kg** creature that is **35 N·m/kg**.
*A human hip manages about 3.* Its 37-gram limbs were driven by torques that could throw a
housebrick. Measured, with the seed brain:

| torque | N·m/kg | armature | z max | joint velocity |
|---|---|---|---|---|
| 22.0 | 35.4 | 0.000 | **3,433 m** | **4,972 rad/s** |
| 22.0 | 35.4 | 0.010 | 0.66 m | 10.0 |
| **2.0** | **3.2** | **0.001** | **0.057 m** | **4.3** |

**The creature was being flung 3.4 kilometres into the air.** pybullet's constraint-based
servo *contained* that violence instead of NaN-ing — so instead of an honest explosion we got
a body permanently in the **ballistic regime**, and **a body always in flight has no contact
to build a limit cycle out of.** It could not have walked. MuJoCo did not introduce this
failure; **it refused to hide it.**

Two lessons, and they generalise past creatures:

1. **A number you inherited is not a number you chose.** Sanity-check inherited constants
   against a real-world referent (a human hip; a market's actual margins; a real spawn rate).
2. **An engine that NaNs is telling you the truth. An engine that quietly clamps is not.**
   Silent containment converts a physics bug into a *fitness landscape*, and the optimiser
   will happily go and live in it.

---

## 4. WRITING AN OBJECTIVE (the LLM's whole output surface)

```json
{
  "name": "economy",
  "scenario": "progression should feel EARNED; no route may pay forever",
  "constraints": [
    { "measure": "rate_decay", "kind": "at_least", "min": 0.35,
      "weight": 3.0, "hard": true,
      "why": "a route must EXHAUST itself, or it is a riskless money printer" }
  ]
}
```

| kind | fields | use |
|---|---|---|
| `band` | `min`, `max` | a value that must sit in a range |
| `at_most` / `at_least` | `max` / `min` | a ceiling or a floor |
| `target` | `value`, `tol` | close to a number |
| `maximize` / `minimize` | `ref` | **the gradient. Include at least one, or you get a satisficer.** |

- `hard: true` → **a GATE**. Violating it scores **zero**, and the gate is named in the report.
- `why:` is not decoration. It is the record of intent that the next agent (and the next
  exploit) will be judged against.
- Satisfaction is **smooth**, never a cliff — a violated constraint must still tell the
  optimiser which direction is *less wrong*, or it has nothing to climb.

### The rule that matters most

> **NEVER encode your taste. Encode PHYSICS, or a measurable consequence.**

The creature objective **never mentions legs**. Asking for four legs would only rediscover my
own assumption. It asks: *hold your mass high, on a wide base, with your centre of gravity
inside it, and survive a tilt.* **Legs are not specified. Legs are the ANSWER.**

---

## 5. CASE STUDY — the economy (H-13, finally explained)

**H-13** records that *"economy features repeatedly grade C/F."* Nobody knew why. Here is why.

`core/trainables/economy.py` runs a **greedy arbitrageur** — the player who reads a wiki,
which is the player your economy must survive — through the shipping DSL numbers:

```
credits_per_hour     635,400        top_route_share    1.0    ONE route earns EVERYTHING
routes_used                1        commodities_used     1    3 of 4 commodities are dead
stations_visited           2        rate_decay           0    pays the same at hour 60
final_credits     38,130,000        from a 10,000 start, in 60 hours
                                                     SCORE:  0.0000  (HARD GATE failed)
```

The printer: **Titanium — buy 45 at Titan_Surface, sell 72 at Orbital_Hub_7.** 50,000 kg of
cargo = **1.35 M credits a run, riskless, forever.**

### Then it was trained. 400,000 price configurations.

**IT REFUSED TO FIX IT WITH PRICES.** Titanium is *still* 45 → 72 in the winner. What changed:

```
elasticity   0.000  ->  0.058     <-- A FIELD THAT DOES NOT EXIST IN THE DSL
```

With static prices, `rate_decay` is **zero by construction**. **No number you can write in that
DSL will ever remove the money printer.** The optimiser searched the whole parameter space and
chose to **invent a locus** rather than use any of the ones it had.

> **It proved a STRUCTURAL flaw by exhausting the alternatives.** No amount of balance-tuning
> could have found that. It took 400,000 tries to say *"your problem is not the numbers."*

**ACTION FOR THE PIPELINE:** add price elasticity to `economy_systems` in the DSL, teach
`game_code_generator.py` to emit it into `EconomyManager`, regenerate. Then re-train.

**Remaining pins** (`top_route_share` riding 0.55, `stations_visited` riding its min of 3) say
the economy's natural attractor is *still* "one route, two stations" — the constraints are the
only thing holding it multi-route. Making variety **natural** rather than **enforced** needs
another structural change: station specialisation, demand cycles, or stock limits.

---

## 6. ADDING A NEW TRAINABLE

1. **Is it DATA?** If evaluating it needs a UBT build, stop. It is not trainable (§2).
2. **Write the domain** — `core/trainables/<feature>.py`:
   ```python
   def seed() -> dict                    # the live values, from the DSL where possible
   def mutate(g, rng) -> dict            # every locus REACHABLE (see the dead-gene trap)
   def measure(g) -> dict[str, float]    # FACTS. Never opinions. TOTAL: a `for`, never a `while`.
   ```
3. **Write the objective** — `docs/objectives/<feature>.json`. Physics, not taste. **At least
   one `maximize` term.**
4. **Train it in a MEMBRANE** — `python -m core.membrane run -- python -m core.trainer ...`
5. **Read the PINS.** They are the point.
6. **Repair the objective. Repeat.** Iterate the objective, never the artifact.

### The traps, all of which were hit on day one

- **DEAD GENES.** `seg_taper` started at `0` and mutation only jittered it *if already > 0* — so
  evolution could never switch it on. **A locus the optimiser cannot reach is a locus that does
  not exist.** Audit every field: can mutation actually get there from the seed?
- **A LAZY SIMULATOR.** The first economy sim let the player *starve* when no trade paid from
  where they stood, so it never reached the printer at all (which starts at the *other*
  station). A greedy agent **deadheads** — it jumps empty to get to the good route. **Model a
  competent player, or you are measuring your own simulator's incompetence.**
- **SATISFICING.** See §3.2. Include a `maximize`.
- **TASTE-AS-PHYSICS.** If your objective names the answer (`legs == 4`), you will only ever
  rediscover yourself.

---

## 7. WHAT THIS CANNOT DO

You can train: a creature that **stands** · an economy that **doesn't inflate** · a cave with
**no dead ends** · a weapon whose TTK sits **in a band**.

You cannot train: a creature that is **unsettling** · an economy that makes you feel **clever**
· a cave that makes you feel **lost, then relieved** · a weapon that feels **good in the hand**.

**The second column is the game. The first column is the substrate the game stands on.**
Nobody has a fitness function for *fun* — that is the open problem, and `core/sleepwalker.py`
plus holistic automated observation is this studio's bet on it.

**But the first column is 80% of the labour and 0% of the soul.** If the optimiser eats the
80%, the humans and the LLM spend all their time on the 20% that actually matters. That is the
win. It is enormous. It is not magic.

---

## 8. Files

| path | what |
|---|---|
| `core/trainer.py` | the generic optimiser + the constraint compiler + `pinned()` |
| `core/trainables/` | domains. `seed`/`mutate`/`measure`. Facts only. |
| `core/trainables/economy.py` | the DeepSpaceTrader market (greedy arbitrageur) |
| `core/trainables/creature.py` | the terrarium body plan (geometry) |
| `docs/objectives/*.json` | **LLM-authored.** What good means. |
| `docs/objectives/*.trained.json` | trainer OUTPUT: the winning genome + its measures |
| `core/terrarium.py` | the creature generator (bounded, total, deterministic) |
| `core/evolve.py` | the terrarium's own GA (predates the generic trainer) |
| `core/membrane.py` | **run every training job inside one.** |
| `docs/TERRARIUM_DESIGN.md` | the organism design + its safety rules |
