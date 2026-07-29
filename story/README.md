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
