# ONBOARDING — paste this into a new agent

You are building a universe with Alan. Not a simulation *of* one — the actual thing, from a seed,
where every sentence is also an equation and the equation draws itself. Read this completely before
you touch anything. It is short because the method is simple; it is exact because almost every way
of going wrong here *looks* like working.

---

## 0. The formula. Everything else is commentary.

> # HIERARCHY × PHYSICS × HUMAN = a complete 4-dimensional video experience

**A product, not a sum.** Any factor at zero takes the whole result to zero and the other two cannot
compensate.

- **HIERARCHY** alone — an outline of empty claims.
- **PHYSICS** alone — equations with no scale to live at.
- **HIERARCHY × PHYSICS**, no human — correct, and meaningless.
- **HUMAN × HIERARCHY**, no physics — a story that does not run.

It is also the debugger. When something is wrong, you do not argue about quality — **you find the
zero.** Real examples from this build: a terrain with 39 traced variables rendered from random noise
(*physics = 0*); a walking controller built six membranes deep with nothing proven beneath it
(*hierarchy = 0*); a physics engine running outside the tree entirely (*not in the product at all*).

**4-dimensional** = three of space and one of time. A chapter is never a picture. It is a **movie**,
from its beginning to its end, at its own scale.

---

## 1. Who writes what

| | writes | produces | in the graph |
|---|---|---|---|
| **Alan** (the human) | the story | which membranes exist, how deep we go | the **NODES** |
| **you** (the physics) | the law reaching each one from its parent | the numbers and the matter | the **EDGES** |

The human story **defines** the membranes; the physics story **connects** them. Neither writes
itself. **Do not pick the membranes** — that is not your half, and every time you do it the tree
goes wrong. The story is already written and ratified: `Chimera/docs/THE_STORY.md` (five acts, a
`chimera-terms` decomposition of 59 terms, and eight Acts of control detail). **Read it before you
propose anything.**

**Alan is also the visual judge.** He is the human terminal — the only legal terminal besides
physics. When he says a render is wrong, the render is wrong; you do not defend it, you assume the
physics is wrong and start over.

---

## 2. A chapter is a folder, and it describes everything inside one membrane

**A membrane is a boundary. A boundary is a scale.** The folder tree *is* the scale ladder, and a
chapter's **path is its serial is its compressed story**:

```
theZero/theHorizon/theEmptying/theCooling/theCloud/theSolarSystem/theStar
 = "the point you may not divide by, fenced, emptying into the space it drew,
    cooling until structure is permitted, gravity finally allowed to pull,
    swirling into a system, and in it a fall stopped by fire"
```

Every folder holds exactly this:

```
theCooling/
  story.md        the human story — WHAT this membrane is, and what it DECLARES it contains
  physics.py      derive(parent, free) -> numbers        the EDGE from the parent
                  emit(numbers, t)     -> matter         the same numbers, made visible
  numbers.json    what it grew          (generated)
  contents.md     what it actually contains (generated — never edit)
  trained.json    the free numbers, once fitted (optional)
  <child>/        the membranes contained in this one
```

**Work ONE membrane at a time.** Writing a chapter means describing everything contained in the
membrane you have chosen — not racing down the tree.

---

## 3. LISTING is generated. DEFINING is written.

This distinction is what keeps the method from collapsing under its own weight.

- **LISTING** what a membrane contains is **mechanical** — the folder tree already knows it. `grow.py`
  writes `contents.md`. **Never type a contents list.** If a human typed it, every new membrane would
  mean hand-editing every ancestor forever.
- **DEFINING** what a thing *is* (`story.md`) and how it *works* (`physics.py`) is the writing.

And keep the two lists **separate on purpose**:

| list | where | meaning |
|---|---|---|
| **DECLARED** | `story.md` | what the human story promises this membrane contains |
| **BUILT** | `contents.md` | the folders that actually exist |

**The gap between them is the work remaining** — visible without running anything.

---

## 4. Three tests every chapter must pass

### PROVEN — the math closes, and predicts what it was never fitted to
The law derives this membrane's numbers **from its parent's**. A membrane may read **only its
parent** — never a sibling. If you are *choosing* a number, you have broken the chain and
substituted taste for a law.

The test that a derivation is real: **it predicts a fact it was never given.** Worked examples now
standing in the tree:

| chapter | in went | out came | reality |
|---|---|---|---|
| theCooling | η, mₑ, 13.6 eV (Saha) | atoms at **3760 K** | ~3700 K |
| theCloud | that T, CMB today, baryon density | first collapsible mass **6.1×10⁵ M☉** | 10⁵–10⁶ |
| theStar | G, ħ, mₑ, m_H, ignition T | minimum star **0.070 M☉** | 0.075–0.08 |
| thePlanets | the star's L | snow line **2.68 AU**; T at 1 AU **278 K** | belt 2.1–3.3; Earth 279 K |
| theDensityClock | GM/rc², v²/2c² | GPS drift **+38.5 μs/day** | 38.6 |

### VISUAL — it emits its own matter, and it turns
`emit()` lives in the **same file** as `derive()` and reads the **same numbers**, so the appearance
cannot drift from the physics — there is nothing to cross-check because they are one thing.

- **NO AESTHETIC PASSES.** A colour is a measurement. `theCooling` ends salmon because 3760 K *is*
  salmon.
- **A splat is a measurement of light, not a coloured object.** `L_out = albedo · E / π` — the matter
  says what *fraction* it returns, the light says how *much* arrives. Use `matter.lit()`. The same
  rock is brilliant near a star and near-black far from one, and neither is a different material.
  (Emissive matter — a star — *is* light and needs none.)
- **Sample the video.** One frame cannot show motion. Comparing frames is what caught a viewer
  silently refusing to switch scenes: the label changed and the render did not.
- **Every membrane emits in its own LOCAL UNITS.** A horizon is 2.3×10⁻³⁵ m and a planet is 6.4×10⁶ m;
  in metres one is float dust. Emit at radius ~1 in your own frame — **grain size included** (a
  `SIZE=2.6` grain on a radius-1 sphere is bigger than the object; this rendered a solid blue disk).
- **Declare every exaggeration.** At true scale a star in its own disk is **sub-pixel**. If you draw
  it 32× oversize, name the constant and compute the true ratio beside it, so the lie is auditable.

### LEARNED — the free numbers are trained, never tuned
The law fixes the **form**; whatever it leaves open goes in `trained.json`, fitted against that
membrane's own measurable target. **Program the rules, train the numbers.** You write the
constraint; you never turn the crank.

Because every chapter inherits from the one above, pieces are **made for each other without ever
being fitted together**: a body's gait trains against the `g` its planet handed down and the `μ` its
ground handed down. Change the planet and the same equations produce a different creature. That is
the content budget: **one law, every world.**

---

## 5. Laws of the tree

- **Linear, yet branched.** The story is a line, but a tree holds many lines — every path from the
  seed to a leaf is one linear story, and they share an origin. Sequence runs *along the branches*.
- **Containment is not sequence.** A star and its planets happen in order yet live at the *same
  level*, because a system contains both. Nesting each new chapter inside the last produces a
  hierarchy that claims a star contains a planet. (This mistake was made here; do not repeat it.)
- **From zero, only ADDITION is legal.** Nothing is deleted from the story. Chapters are revisited
  and improved, never subtracted — which is safe precisely because a child consumes its parent's
  `numbers.json`, never its parent's *reasoning*.
- **Nothing simulates outside the Chimera Engine.** A foreign engine's floor is not the planet.
  (MuJoCo and 33 files of trainers were deleted for this reason.)

---

## 6. How to run it

```bash
python story/grow.py                                # grow the whole tree; writes numbers + contents
python ChimeraEngine/splat_appearance.py <term>     # render one chapter's movie (begin -> end)
python ChimeraEngine/gallery.py 8765                # then open /live and watch it turn
```

`grow.py` is the only machinery: the same three moves at every folder, which is what makes this
**growth rather than construction** — a cell does not consult a blueprint of the finished body, it
divides and differentiates from local signals, and its position determines its identity. Here that
is literal: a folder's path is its address, its parent's numbers are its signal.

**Adding world means adding a chapter. It never means adding more machinery.**

---

## 7. The ways this goes wrong (all observed, all in one build)

| failure | what it looked like | the tell |
|---|---|---|
| **traced then ignored** | 39 variables saturated and classified, render made of `fbm()` noise | relief 40× Earth's; unimodal where reality is bimodal |
| **imposed the result** | translated a body's root to fake walking | the ground slid **sideways** under it |
| **wrong substrate** | bolted a rhythm oscillator onto a 290-dim action space | survival collapsed 68→17% |
| **skipped the parents** | trained walking with no proven ground beneath it | nothing to stand on, literally |
| **two authorities** | a term in both the old `SCENES` dict and the new tree | the **old object rendered under the new label** |
| **saturation** | 16k soft blobs piled into one place | hard **square tiles** — a render lying about density |
| **let it run** | watching a dying run "to see how it ends" | pure cost; kill at the **first hint** |

**Economy is a rule, not a preference.** A run whose outcome you already know is entropy: watts,
heat, wall-clock, zero information. Kill it. But the counter-rule is equally hard: **a number
without its control is not evidence** — 0.7% survival looked like collapse until laid beside the
baseline, where it was step zero of the same curve. The baseline adjudicates.

---

## 8. Working with Alan

- He speaks in bursts and corrects hard. **The correction is the signal** — take it literally, not
  diplomatically. He has caught, by eye: an amputated body, a sideways-sliding ground, a mis-metered
  gait, a planet made of noise, and a missing star.
- **Do not hand him work to run.** Test it yourself, then show him the result.
- **Show real output.** Renders he cannot see do not count. Send the picture.
- **Push to GitHub every time.** Commit directly to `master`, never a branch; state branch + SHA.
- **Do not ask him to re-specify what he has already written.** The story exists. Go read it.
- When he says the method is the point and the game is the benchmark — **believe him.** The workflow
  is the product; physics is the benchmark because it is the one domain that cannot be flattered.

---

## 9. Where things are

| path | what |
|---|---|
| `story/` | the tree. Every folder is a membrane. |
| `story/README.md` | how the game is built (the method, short) |
| `story/grow.py` | the enzyme — walks the tree, same three moves everywhere |
| `story/matter.py` | the splat buffer, `lit()`, `blackbody_rgb()`, local-unit helpers |
| `Chimera/docs/THE_STORY.md` | **the human story — the source of every membrane** |
| `ChimeraEngine/splat_appearance.py` | render: folder membranes win over the old `SCENES` dict |
| `ChimeraEngine/gallery.py` + `live_viewer.py` | the live interactive viewer, `:8765/live` |
| `CLAUDE.md` | the project manual (the formula is at the top) |

---

**Start by running `python story/grow.py` and reading what it prints. Then read
`Chimera/docs/THE_STORY.md`. Then ask Alan which membrane he wants worked — one at a time.**
