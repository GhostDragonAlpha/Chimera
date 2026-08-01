# HOW THIS GAME IS BUILT

> # HIERARCHY × PHYSICS × HUMAN = a complete 4-dimensional video experience
>
> **A product, not a sum.** Any factor at zero takes the whole result to zero, and no amount of the
> other two makes up for it.
>
> * **HIERARCHY** alone — an outline of empty claims.
> * **PHYSICS** alone — equations with no scale to live at.
> * **HIERARCHY × PHYSICS**, no human — correct, and meaningless.
> * **HUMAN × HIERARCHY**, no physics — a story that does not run.
>
> Every failure in building this has been one factor going to zero:
> a terrain with 39 traced variables rendered from *noise* (**physics = 0**);
> a walking controller built six membranes deep with nothing proven beneath it (**hierarchy = 0**);
> a physics engine outside the tree entirely (not in the product at all).
>
> **4-dimensional**: three of space and one of time — so a chapter is never a picture, it is a
> movie, from its beginning to its end, at its own scale.

**You write chapters. Each chapter must be PROVEN, VISUAL, and LEARNED. That is the whole method.**

There is no asset pipeline, no level editor, and no content budget. The world is a story told in
order from a seed, where every sentence is also an equation, and the equation also draws itself.

---

## The two authors

| | writes | produces | in the graph |
|---|---|---|---|
| **the human** | `story.md` — what this membrane IS | the concepts, and how deep we go | the **NODES** |
| **the physics** | `physics.py` — the law reaching it from its parent | the numbers and the matter | the **EDGES** |

The human story *defines* the membranes; the physics story *connects* them. Neither writes itself,
and neither one alone is the game.

## A chapter is a folder

## `the` and `a` — the prefix is a classification

**Every concept wants two membranes, and they are different kinds of claim:**

| prefix | what it is | example |
|---|---|---|
| **`theX`** | **the LAW** — what an X *is*, and the constraints any X must satisfy | `theStar`: a fall stopped by fire, and the least mass at which fire can light (0.070 M☉) |
| **`aX`** | **the INSTANCE** — the one that actually formed here, inheriting from the law | `aStar`: this system's star. M = 1.000 M☉ → R, L, T = 5772 K, lifetime 10 Gyr |

The law says what is *possible*; the instance is what *happened*. An instance always sits **inside**
its law and reads its numbers from it, so it can never contradict it — and the law can be checked
against reality independently of any instance that grew from it.

**This is the target shape for every concept**, all the way down: `theTerrain` / `aTerrain`,
`theGround` / `aGround`, `theOcean` / `anOcean`, `theHuman` / `aHuman`.

### An instance is named by its KIND, and the kind is derived

Not `aStar`, `aStarB`, `aStarC` — **`aYellowStar`**. The descriptive word is the thing's
**classification**, taken from the established taxonomy, and it is *computed*, never assigned:

```
T_surface = 5772 K   →  Harvard class G  →  "Yellow"  →  the folder is aYellowStar
```

`measure()` then checks the **folder name still matches the class its own physics produces**. Rename
it wrongly and the check fails; change the star's mass enough to move it out of G and the name has
to change with it. **The name is a claim, so it is tested like one.**

Use the real taxonomy for each kind — spectral class for stars (O B A F G K M), composition for
worlds (rocky / ice giant / gas giant), and so on. Two of a kind in one place get their own
descriptors, not letters.

**It also diagnoses the two orphans.** `aPlanet` and `theTerrain` are the only painted scenes left,
and each is missing its other half — `aPlanet` is an instance with no law above it, `theTerrain` a
law with no instance below it. That is precisely why nothing derives them and why both held wrong
numbers for so long (relief 40× too tall, aridity peaking at the poles).

In the viewer: **green = `the`, a law · red = `a`, an instance · hollow = not built yet.**

---

**Every chapter opens with a plain-words line, before any equation:**

```markdown
# theCooling

**In plain words —** As the universe spreads out it cools, and every time it gets cold enough,
one more kind of thing is allowed to stay in one piece instead of being smashed apart.
```

That is the **label that comes before the thing** — a reader knows what they are about to look at
before a single symbol appears. It is also the chapter's own **low-LOD version of itself**, which is
why `grow.py` harvests it into every ancestor's index: a parent's contents list is literally its
children described at lower detail. **One line, two jobs** — and it is not optional, because a
membrane nobody can read is a membrane nobody can judge.

```
theCooling/
  story.md        one paragraph. the human story. what this is.
  physics.py      derive(parent, free) -> numbers      the EDGE from the parent
                  emit(numbers, t)     -> matter       the same numbers, made visible
  numbers.json    what it grew (written by grow.py)
  trained.json    the free numbers, once fitted        (optional)
  <child>/        the concepts contained in this one
```

**A folder is a membrane. A membrane is a boundary. A boundary is a scale.** So the folder tree is
the scale ladder, and a chapter's **path is its serial is its compressed story**:

```
theZero/theHorizon/theEmptying/theCooling
  = "the point you may not divide by, fenced, emptying into the space it drew, cooling until
     structure is permitted"
```

**Linear, yet branched.** The story is a line, but a tree holds many lines — every path from the
seed to a leaf is one linear story, and they all share an origin. That is why chapters work: they
keep the order, and they can be **revisited and improved** without disturbing their neighbours,
because a child consumes its parent's `numbers.json`, never its parent's reasoning.

## The three tests a chapter must pass

### 1. PROVEN — the math closes, and predicts what it was not fitted to
The law derives this membrane's numbers from its parent's. It is not a parameter you pick; if you
are choosing a number, you have broken the chain and substituted taste for a law. The test that a
derivation is real and not a story: **it predicts a fact it was never given.**

> ¶4 put in η, mₑ and 13.6 eV and got **3760 K** for the temperature the universe went transparent.
> Literature: ~3700 K. Nothing was fitted.
> ¶2 put in nothing but G, c, ħ and got the crossing where a black hole and an electron are the
> **same size**, and with it the first length and the first tick of time.

### 2. VISUAL — it emits its own matter, and it turns
`emit()` lives in the *same file* as `derive()` and reads the *same numbers*, so the appearance
cannot drift from the physics — there is nothing to cross-check because they are one thing.
**No aesthetic passes.** A colour is a measurement: `theCooling` is salmon at the end because
3760 K *is* salmon. Then look at it in the engine — it renders as splats and turns in the live
viewer (`ChimeraEngine/gallery.py`, http://127.0.0.1:8765/live).

**One frame cannot show motion.** Sample the video — comparing frames is what catches a scene that
silently did not switch.

**Every membrane works in its own local units.** A horizon is 2.3e-35 m and a planet is 6.4e6 m; in
metres one of them is float-precision dust. A boundary supplies its own unit, so a law emits at
radius ~1 in its own frame — grain size included — and the parent scales its children when it
composes them. Precision stops being a problem the moment the membrane is the unit.

### 3. LEARNED — the free numbers are trained, never tuned
The law fixes the FORM; whatever it leaves open goes in `trained.json`, fitted against that
membrane's own measurable target. **Program the rules, train the numbers.** An LLM writes the
constraint and never turns the crank.

Because every chapter inherits from the one above, the pieces are **made for each other without
ever being fitted together**: a body's gait is trained against the `g` the planet handed down and
the `μ` the ground handed down. Change the planet and the same equations produce a different
creature. That is the content budget: **one law, every world.**

---

## Two rules that cost a day each

**A render may not contain a body the derivation did not produce.** An exaggeration scales something
derived; it cannot invent an object. A "star marker" drawn beside a planet is a moon, and no moon was
derived. A light source is told by its light — the terminator already says where the star is. If a
thing is off-screen at true scale, go up a level; that is what the hierarchy is *for*.

**A sibling's number comes through the parent, or not at all.** `theStar` and `thePlanets` cannot
read each other. When the planets needed the star's colour they typed `5772.0` under a comment
claiming it was inherited — so changing the star moved the snow line and left the sunlight identical.
The parent carries it. **The test is a slider:** move a free number at the top, and anything that
fails to move downstream is typed, not derived.

## Composition — a parent is made of its children

A law may define `layout(nums) -> {child: (centre, scale)}`. Each named child is grown, emitted in
**its own** local units, and placed in the parent's frame. The parent supplies only **where** and
**how big** (structure — an orbital radius is derived, not decorated); the child supplies its own
appearance, always.

So looking at `theSolarSystem` shows you the star and the worlds inside it, and zooming in is just
reading the same tree at a finer level. **That is LOD of meaning applied to matter: every level is
the level below, placed.**

Four rules, each learned by breaking it: convert units at the seam (or better — move the number to
the parent that owns it); **LOD every placed child by its size**; never duplicate a child; and
**a membrane may only read its PARENT**, because that is what decides which physics is reachable
from where.

## Don't invent levels

`HIERARCHIES.md` holds the established paths — `galaxy → molecular cloud → star system`,
`cell → tissue → organ → organism`. If a step feels missing between a membrane and its parent, it
probably *is* one. Check there first; skipping a level is a bug, not a shortcut.

## The enzyme

`grow.py` walks the tree and does the same three moves at every folder — read the concept, derive
from the parent, emit the matter. **Same code at every level**, which is what makes this growth
rather than construction: a cell doesn't consult a blueprint of the finished body, it divides and
differentiates from local signals, and its position determines its identity. Here that is literal —
the folder's path is its address, its parent's numbers are its signal.

```bash
python story/grow.py                              # grow the whole tree, print what each chapter made
python ChimeraEngine/splat_appearance.py <term>    # render one chapter's movie (begin -> end)
python ChimeraEngine/gallery.py 8765               # then open /live and watch it turn
```

**Adding world means adding a chapter. It never means adding more machinery.**

## The one rule about the tree

From zero, only **addition** is legal. Nothing is deleted from the story — chapters are revisited
and improved, never subtracted.

---

## The chapters so far

| # | chapter | proven by | visual |
|---|---|---|---|
| 1 | `theZero` | r=0; the one forbidden operation. Black hole ≡ electron: three numbers, and Kerr–Newman with an electron's values gives g=2 exactly | everything arrives at a point with no size |
| 2 | `theHorizon` | `r_s = 2GM/c²` vs `λ_C = ħ/mc` cross at `M=√(ħc/2G)` → `l_P`, `t_P`. Zero is *fenced*, not approachable | the fence at radius 1, the point at its centre |
| 3 | `theEmptying` | `S = kA/4l_P²` — the information is on the *boundary*. `T = ħc³/8πGMk`, lifetime ∝ M³ → a runaway, not a leak | the surface empties into the space it drew |
| 4 | `theCooling` | Saha: atoms permitted at **3760 K** (lit. ~3700 K), lateness **42×** derived | opaque blue-white → transparent, salmon at 3760 K |

Next: gravity has no threshold and never switches off, and it has just been handed matter that is
neutral and one part in 100,000 uneven.

---

## AND EVERY NUMBER DECLARES ITS UNIT (2026-07-31)

A chapter is PROVEN, VISUAL and LEARNED — and now also **BINDABLE**. Every number a membrane
publishes states its unit, either in the key name (`extent_m`, `duration_s`, `foot_pressure_kPa`)
or in `story/data/units.json`. A number nothing can read the unit of is a number nothing can safely
connect to, and that is exactly how 294.19 **Kelvin** ended up in a **Celsius** table and rendered
a temperate world as hot desert, poles included.

    python story/folding.py audit     # before you call a chapter done

It needs no setup and no signatures: it reads the unit off the key and asks what that unit
*forbids*. Full method — folds, bonds, regimes, and why protein folding is the right metaphor
rather than a decorative one — in `docs/THE_FOLDING.md`.

---

## AND EVERY CLAIM CARRIES A CONTROL (2026-08-01)

A chapter is PROVEN, VISUAL, LEARNED and BINDABLE — and none of those survive an instrument that is
reading itself. **PROVEN has a fourth requirement, and it is the cheapest one on the list:
before reporting a number, run the identical instrument on something whose answer you already
know.** Not a held-out sample. A thing you MADE.

This chapter's own machinery hands you the perfect control for free. `emit()` produces the
membrane's matter from its own numbers, so a render of it is a subject whose answer is known **by
construction**. Push that through whatever is measuring the real thing and see what comes back.

It reversed three already-written conclusions in one day:

| what was believed | what the control said |
|---|---|
| a generated take's splat statistics land inside the range real scans occupy | **the clay we sent it** returns the same numbers to 6.9% — three of four features were the FITTER, only colour was material |
| adding octaves raised `aTerrain`'s surface detail 1.118 → 0.963 | under a denoise the gain *evaporated* (1.116× → 0.895×) — it was render grain |
| the cross-hatch came from the new octave code | the **canvas** measured 27.8× directional, the new code 1.1× — innocent |

Three corollaries, each of which cost its own hour:

- **Measure at the scale the thing lives at.** An instrument that cannot resolve an effect does not
  say "cannot see" — it returns a number, often in the wrong direction. `aTerrain`'s finest drawn
  octave is 0.6 px at whole-patch framing. This is LOD applied to measurement: a membrane is judged
  at its own scale, by an instrument that resolves it, exactly as it is *rendered* at its own scale.
- **Never threshold on a quantile of what you are measuring.** A top-12% growth rule grew a detailed
  take and flat clay to *5,619 splats, identical to the digit*. Every normalisation buys robustness
  by discarding a degree of freedom — check it is not the one you came for.
- **A shared name is not a shared definition.** `folding.py` reads units off published numbers; it
  cannot see a formula in code computing something else under the same name. Four features were
  written from the name alone and one of them, `aniso`, read 2.25 against a real range of
  0.296–0.996 — a spectacular finding that was a quantity on the wrong interval.

> A measurement without a control is not a weak measurement. It is not a measurement.

The sixteen rules in full, with every number: `Chimera/docs/EXPERIMENTAL_METHOD.md`.

---

## AND EVERY CHAPTER KNOWS WHEN IT IS (2026-08-01)

A chapter's folder path says what **contains** it. The story is told in **time**, and those two
part company the moment the tree branches: `theStar` and `thePlanets` are siblings in the folder
tree and are not simultaneous. Nothing written anywhere said which came first.

    A HIERARCHY SAYS WHAT CONTAINS WHAT. A TIMELINE SAYS WHAT FOLLOWS WHAT.

So the serial is now **derived from time**, not from the tree. Every chapter already publishes
`duration_s` — its own span, and those are real, `theCooling`'s 1.199e13 s *is* the 380,000 years
to recombination. Summing down the path from the seed gives the seed's own seconds at which each
chapter's process completes, and it is monotonic down every branch by construction, because a child
cannot finish before the parent it lives inside.

    python story/timeline.py            # the story, in the order it happens
    python story/timeline.py --write    # publish timeline_serial + t_since_seed_s

**AND THE STORY CARRIES THE SAME NUMBER.** Every `story.md` is stamped with its chapter, its epoch
and its span. If only the numbers knew the order, there would be two orderings — and the one a
human reads would be the one that quietly went wrong.

**It found what was out of order the first time it ran**, which is the whole reason to have it:

- `theHumanClock` lands at **3 seconds after the seed**, sorting before recombination. Humans do
  not exist three seconds after the Big Bang. It is the first chapter whose containment and
  chronology genuinely disagree — it sits under `theClock` because it *is* a clock, while what it
  describes happens thirteen billion years later.
- **Nine hand-written chapter numbers disagreed with the derived order, and two pairs collided** —
  `theSolarSystem` and `theStar` both claimed chapter 6. They were paragraph counts written as the
  story was composed, drifting each time a chapter was inserted between two others, with nothing to
  notice, **because a number in prose has no consumer.**

Honest limit: this sums process spans, not the waiting between them, so the epoch is exact as an
ORDERING and approximate as an absolute time. When a chapter publishes the interval it waits before
starting, the same sum becomes a real clock without changing shape.

---

## FAL.AI — how we "scan" things that do not exist

This project sources APPEARANCE from measurement, and cannot measure what has never existed: this
world's rock, a suit nobody sewed, a creature nobody caught. fal.ai runs a video model that
textures **our own geometry**, which turns it into a synthetic capture rig.

    a chapter's emit()  ->  clay_export  ->  fal.ai (Seedance)  ->  harvest / splat_genome
                                                                          |
                                                back into the chapter's own numbers

**IT IS NOT ALLOWED TO INVENT THE SCENE.** We supply geometry and camera; it supplies appearance
only — and appearance is already the one thing sourced from measurement rather than derived, so
nothing is conceded. It is also checkable: reconstruct from the generated views and compare against
the chapter's own emit. Two independent messengers, which is a dyad.

**WHAT IT GIVES, MEASURED:** colour (ΔRGB −0.22…−0.25 on a suit, −0.45…−0.51 on terrain),
`surface_complexity` 1.71×, `splat_demand` 1.398×.

**WHAT IT CANNOT, AND WHY THAT IS FINE:** geometry comes back wrong (hull IoU 0.45, a body 25% less
voluminous) — and **a material genome contains no positions.** Every feature is a distribution. We
already have the geometry; deriving it is the whole project.

**REFUTED — DO NOT RE-ATTEMPT:** `log_size`, `aniso`, `opacity` from a generated take match *the
clay we sent it* to within 6–7%. They are the fitter's signature, not the material's. Adaptive
densification was built and did not rescue them.

**MONEY AND THE TRAPS, each one paid for:** nothing spends without `--yes`; `FAL_KEY` lives in the
environment, never in a file. Discover for FREE first — `fal.ai/api/models?keywords=…` and
`openapi/queue/openapi.json?endpoint_id=…` — because seven paid calls were burned probing an
endpoint with invented field names. **fal ignores unknown fields rather than rejecting them**, so a
misspelling returns 200 and a charge. **A 422 is not proof an endpoint is live:** one validated
inputs and then returned a canned example (seed 0, 0.6 s) for any prompt, so check the returned
seed and duration against what you asked for.

**CAPTURE SETTINGS, every one measured against a control:** 480p beats 720p for frame-to-frame
consistency (2.62% vs 4.30% drift, clay floor 2.51%) — more resolution bought less agreement. Black
floor, ambient only, no shadows, because our renderer programs its own light and a baked one is
permanent. Keep the floor contact visible; it is information.

**AND THE CLAY IS THE FREE CONTROL.** We rendered it, so we know its answer by construction. Run
every measurement on the take AND on what we sent. Three conclusions were reversed by that in one
day. Full account: `docs/FAL_AI.md`.
