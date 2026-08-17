# THE GROWTH — what CHIMERA is, and the rules that make it build itself

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
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Solidified 2026-07-31 from the operator's rulings, so they never have to be re-explained
> to any agent again. This file is the SECOND read after `ChimeraEngine/ONBOARDING.md`
> (the method loop) and before touching anything. It owns the *what and why*; the
> onboarding owns the *how*; the corpus (below) owns the *knowledge*.

---

## WHAT THE GAME IS

CHIMERA is a **grown simulation**, not a coded game. A Star-Citizen-natured space game —
a realistic human walking a real planet — whose detail standard is set by one north star:

> **"When we get done, people should be able to use this game to go to medical school.
> You can be a surgeon, use advanced scanners, see organs — and if we want to do something
> gory, then we really have to have the guts."** (the operator, 2026-07-31)

Everything in it is **light and physics** — nothing else exists. Rendering is light
transport from measured optical constants; simulation is physics from official scientific
sources. The engine is a physics engine custom to light: **from the electron to the black
hole, and everything in between** (`research_references/PHYSICS_OF_EVERYTHING.md` is that
scope, sourced, minus the forbidden branches).

Vocabulary (the operator): the artifacts are **membranes, recipes, genomes** — not "code"
and "assets". A law (`theX`) is a recipe; an instance (`aX`) is a grown child of it.

---

## THE FIVE RULINGS OF 2026-07-31

1. **Everything is a sample that you train.** The game is made FROM real 3DGS scans:
   extract the shape+texture elements (one joint codebook over the collection —
   `Construction/material_elements.py` → `story/data/material_genomes.json`), and train
   them all together. 2D-texture pipelines are superseded. No surface may have less
   fidelity than a measured scan of its class provides.
2. **Research connects the physics to the training data.** Effort is spent on a subject
   ONCE, then reused infinitely and morphed onto other things. Acquisition is the first
   move of any subject: download the measured data, then derive.
   (`research_references/human/ACQUISITION_PLAN.md` is the pattern.)
3. **The physics is the code.** No library call terminates a law; a membrane's
   `physics.py` derives from first principles + measured inputs. Physics is proven by
   **deriving it yourself** or from **official scientific sources** — peer-reviewed
   papers, standards, textbooks. *The college papers are the gold: what humanity believes
   counts as a direct source.*
4. **The natural world is a combination of ALL of the known.** Each membrane is an
   intersection of every law whose variables it touches — never one branch.
   (`research_references/MEMBRANE_PHYSICS_MAP.md` enumerates which rows apply to each
   membrane, and why; a membrane ignoring a governing row is incomplete by construction.)
5. **The standard of definition is measured capture.** Detail tiers:
   **D0** proven function (membranes) · **D1** macro anatomy ~1 mm (ANSUR, Visible
   Human) · **D2** surgical anatomy ~0.3 mm (cryosection/micro-CT capture) · **D3**
   histology ~µm (the honest capture boundary) · **D4** molecular (out of scope).
   The ceiling is the measurement, never the renderer: 3DGS reproduces whatever the
   source resolves. The true frontier is **deformation** — static capture is a download;
   tissue that cuts and bleeds by law (fracture mechanics, hemodynamics — already rows in
   the physics tree) is prove-work.

---

## CHILDREN — the recipe doctrine (mutation, variation, seeds)

> The operator: *"make one version we like, then make other versions — mixing a little of
> this and a little of that, or the same variables with a different seed, so it looks
> different but still has the same characteristics."*

A child is legal in exactly two ways, and one gate makes both honest:

- **RE-SEED.** Same recipe, different seed. The story's grow is deterministic per seed
  (`Chimera/core/grow.py`), and the genomes carry measured distributions (mean/std/p10/p90 from
  real scans), so a re-seeded child *looks different with the same characteristics* while
  every sampled value stays inside measured reality. This is already the law/instance
  mechanism: `theX` is the recipe, `aX` is one grown child.
- **MIX.** Recombine measured genomes or recipe parameters — a little of this genome, a
  little of that. Legal **inside** the measured envelope (interpolation between measured
  elements is still bounded by measurement). Extrapolation beyond measured bounds is an
  invention: allowed only as a declared experiment that must then prove itself.
- **THE GATE — what "simulated data in the smart way" means.** Synthetic data is legal
  when it is **sampled from measured distributions and then proven through the boundary**
  (the physics number + the human dyad ≥ 0.6). Synthetic that trains itself without proof
  is a monad — excluded from the codebook by standing rule (gen_tree/warp_gen/molds are
  excluded from extraction for exactly this reason). The loop is
  **measure → sample → prove**, never *generate → trust*.
- **Inheritance.** A child keeps its parent's proven physics; only what changed re-proves.
  Effort per subject stays paid-once.

---

## THE CORPUS — where the knowledge lives (read these instead of asking)

| file | what it owns |
|---|---|
| `research_references/PHYSICS_OF_EVERYTHING.md` | humanity's complete physics tree, ~110 sourced rows, minus the forbidden branches |
| `research_references/PHYSICS_SOFTWARE_MATH.md` | the simulator's-eye view: the math every engine encompasses (math isn't copyrightable; code is) |
| `research_references/MEMBRANE_PHYSICS_MAP.md` | for each membrane: which physics rows apply and why (prose; the machine-checkable version is below) |
| **`docs/THE_FOLDING.md`** | **a serial that says what it can CONNECT to.** The catalog rows as an index (`story/data/physics_catalog.json`, 158 rows), every number's unit (`story/data/units.json`, 86%), and the fold/bond/regime checks that make ruling 4 a test instead of a sentence. `python story/folding.py audit` |
| `research_references/human/ACQUISITION_PLAN.md` | the measured-data side: what to download once per subject, tiers and licenses |
| `research_references/human/PHYSICS_OF_THE_HUMAN.md` | the human's 45 physics rows with sources and proof status |
| `research_references/human/MUSCLE_INVENTORY.md` | every muscle that moves the body: what it does, why it exists |

The rule these six files enforce: **any membrane in any game asking "what does humanity
know about X?" gets a sourced row, never a guess** — and any agent joining the project
inherits the whole answer by reading, without a single token of re-explanation.

---


## THE RULING OF 2026-08-01 — the control

**Nothing above is true until an instrument that can be fooled has been checked against one that
cannot.** Add to the creed, ahead of everything else in it:

- **Before reporting a number, push a KNOWN subject through the whole instrument.** Not a held-out
  sample -- a thing you MADE, whose answer you know by construction. `emit()` gives you one for
  free: the membrane's own matter, rendered. Three already-written conclusions were reversed by this
  in a single day (a material genome that was the fitter's signature; a detail gain that was render
  grain; a cross-hatch blamed on new code that came from the twenty-one-plane-wave canvas).
- **Measure at the scale the thing lives at.** An instrument that cannot resolve an effect returns a
  number in the wrong direction, not a refusal. Count the pixels the effect occupies first.
- **Never threshold on a quantile of the thing you are measuring** -- a rule defined in terms of its
  own population reports nothing about that population. Use an outside reference.
- **A shared name is not a shared definition.** `folding.py` binds published *units*; it cannot see a
  formula computing a different quantity under the same name. Their file is the authority.
- **Derive the shape, let physics set the level** -- and when the two disagree, publish the
  disagreement. `aTerrain`'s spectrum wanted 20x more sub-grid relief than the friction angle allows,
  and that gap IS the threshold-hillslope result.

Full account, with every number and every reversal: `Chimera/docs/EXPERIMENTAL_METHOD.md` rules 12-17.

## THE BUILDER'S CREED (2026-07-31, in the operator's direction)

- Download once, train once, prove once — reuse infinitely, morph onto everything.
- **Every number declares its unit** — in its key name, or in `story/data/units.json`. A number
  nothing can read the unit of is a number nothing can safely bind, and that is how a Kelvin
  ended up in a Celsius table and rendered a planet as desert.
- Appearance comes from scans; law comes from papers; taste comes from the operator.
- A child is a recipe re-seeded or measured genomes mixed — and nothing counts until
  `prove` crosses the boundary.
- The detail limit is the measurement; the scope is the electron to the black hole;
  the standard is that a surgeon could learn here.
- This is how the game builds itself and gets smarter at building games: every proven
  row, every measured genome, every sourced membrane is inherited by everything that
  comes after. **We are shooting for everything in between.**
