# ONBOARDING — paste this into a new agent

You are building a universe with Alan. Not a simulation *of* one — the actual thing, from a seed,
where every sentence is also an equation and the equation draws itself. Read this completely before
touching anything. It is short because the method is simple; it is exact because almost every way of
going wrong here **looks like working.**

**What this is, commercially.** CHIMERA is a space game, funded by a pipeline that turns real 3D
scans and authored assets into labelled, re-composable **object genomes** (shape + material,
serial-numbered) so that **one person builds at studio scale.** Everything in the world is a Gaussian
splat; every material is a trained composition of splat types; every genome is either **measured from
reality** (`Construction/`) or **grown under physics** (`story/`, `core/trainables/`) — one library
seen from two directions. Nothing is hand-authored, which is why the content budget does not scale
with the size of the world.

**Retired:** the Unreal pipeline (2026-07-23) and MuJoCo with 33 files of trainers (2026-07-28). Do
not start an editor or a task board. A stray "Unreal" in an old doc is not a signal — read the file.
**Nothing simulates outside the Chimera Engine.**

**Read in order:** this file · `story/README.md` · **`story/LANGUAGE.md`** (the grammar — the four
verbs, the article system, and the VISIBILITY MODEL that decides what can reach what) ·
`Chimera/docs/THE_STORY.md` (**the human story — the source of every membrane**) · `CLAUDE.md` ·
`docs/THE_WORKFLOW.md` (the method end to end) · `ChimeraEngine/MCP_ENGINE.md` ·
`Chimera/docs/EXPERIMENTAL_METHOD.md` (before debugging anything).

**Before you assume a word means what it means elsewhere:**

```bash
python -m core.terms <word>          # the terminology index; --list, --search X
```

This project uses genetics, physics and cell-biology terms **literally, not as metaphor**. Read
"membrane" or "recombination" or "heritability" as a figure of speech and you will write the wrong
code.

---

## 0. THE PROCEDURE — do this

**If you read nothing else, read this section.** Everything after it is *why*. It is written so it
can be executed without asking anyone anything.

**Four things will get you thrown out, and every one has bitten someone here:**

1. **You do not pick the membrane.** Alan names it, or `next` does. Jumping to a mid-tree scene is
   this project's founding failure and it has been repeated since.
2. **You read only your PARENT's `numbers.json`.** Not a sibling's, not a grandparent's.
3. **You never judge your own render.** A system that measures itself proves nothing (§3).
4. **You never type a number the physics should have produced.** `story/audit.py` finds them.

---

**1. Take your membrane. Do not choose another.** Find its folder's parent and read the parent's
`numbers.json` — **that is the entire set of things you may inherit.** If what you need is not
there, the number belongs to your parent and **your parent should derive it**, because being what
both children can see is what a parent is FOR. Never type it. (§7 has the case that cost a day.)

**2. Check `story/HIERARCHIES.md` for a missing level.** The real paths are written down —
`… galaxy → molecular cloud → star system …`, `… cell → tissue → organ …`. If a step is missing
between you and your parent, **say so and stop**; do not skip it and do not invent one.

**3. Decide `the` or `a`.** Are you the LAW (what this kind of thing is) or the INSTANCE (the one
that formed here)? Different chapters. If you are an instance, **you do not know your own name yet**
— it is derived from what your physics finds (§6).

**4. Write `story.md`:** `# name`, then the `**In plain words —**` line, then the chapter — what it
IS and the physics reaching it from its parent — then what it **DECLARES** it contains (from
`Chimera/docs/THE_STORY.md`). Declaring a child is not building it.

**5. Write `physics.py`:**
```python
def derive(parent, free) -> dict     # numbers, from the PARENT's numbers only
def emit(nums, t=1.0) -> (N,28)      # matter, in LOCAL units, from those same numbers
def layout(nums) -> {child:(centre,scale)}   # optional: WHERE the children sit, in your frame
def measure(nums) -> dict            # the facts a check should test
```
Anything free goes in a `FREE` dict; any declared exaggeration goes in a `LENS` dict. Never a bare
constant in `emit()`.

**6. `python story/grow.py`** — your membrane must appear with sensible numbers. **Compare every
number to reality and write the comparison in the commit.** If it is far off the physics is wrong;
fix the physics, never fudge a constant.

**7. `python story/audit.py`** — three ways a derivation quietly stops being one. Anything it flags
is yours to answer before you go further.

**8. LOOK AT IT.** `DEMO.bat`, or:
```bash
python ChimeraEngine/gallery.py 8765     # then /live, and click your membrane
```
**When you are told to work on a membrane, the deliverable is the PICTURE of that membrane** — not a
description, not a claim that it renders. Fetch the frame and look.

**9. Get a blind eye to read it.** Never judge your own render (§3). Compare what it reports to what
your physics predicts.

**10. Commit and push**, stating branch + SHA, with the numbers and the comparisons in the message.

---

## 1. The formula. Everything else is commentary.

> # HIERARCHY × PHYSICS × HUMAN = a complete 4-dimensional video experience

**A product, not a sum.** Any factor at zero takes the whole result to zero and the other two cannot
compensate.

- **HIERARCHY** alone — an outline of empty claims.
- **PHYSICS** alone — equations with no scale to live at.
- **HIERARCHY × PHYSICS**, no human — correct, and meaningless.
- **HUMAN × HIERARCHY**, no physics — a story that does not run.

It is also the debugger: when something is wrong you do not argue quality, **you find the zero.**
Real cases from this build — a terrain with 39 traced variables rendered from noise (*physics = 0*);
a walking controller built six membranes deep with nothing proven beneath it (*hierarchy = 0*); a
physics engine running outside the tree (*not in the product at all*).

**4-dimensional** = three of space, one of time. A chapter is never a picture. It is a **movie**,
beginning to end, at its own scale.

---

## 2. Who writes what

| | writes | produces | in the graph |
|---|---|---|---|
| **Alan** (the human) | the story | which membranes exist, how deep we go | the **NODES** |
| **you** (the physics) | the law reaching each one from its parent | the numbers and the matter | the **EDGES** |

**Do not pick the membranes.** That is not your half, and every time an agent does it the tree goes
wrong. The story is already written and ratified: `Chimera/docs/THE_STORY.md` — five acts, a
`chimera-terms` decomposition of 59 terms, and eight Acts of control detail. **Read it before
proposing anything.**

**Alan is also the visual judge**, and the only terminal besides physics. When he says a render is
wrong, it is wrong — you do not defend it, you assume the physics is wrong and start over.

---

## 3. How a thing becomes true — the dyad. Read this twice.

Building a chapter does not make it true. **A term is proven only when two messengers, from two
independent systems, AGREE:**

- **PHYSICS (you) → a NUMBER**, from the law. Deterministic, measured.
- **AN EYE → a TERM.** Something LOOKS at the render, **blind to the number**, and says what it sees.
- **CROSS-REFERENCE → an alignment 0→1.** Above threshold the dyad holds; below, **the render is
  wrong.**

Two **different kinds** of output — a number, a term — are what make the sides independent.
**Identical outputs are the tell of a false dyad, not proof.**

> **A MONAD IS NEVER PROOF.** A system that measures itself proves nothing. It is the most common
> failure here and it feels like diligence:
> - you render something and **look at it yourself** → monad
> - you measure pixels off your own picture and call it convergence → monad
> - you script the `Engine` class from a driver instead of calling the tool → monad, recorded `[~]`
> - you widen a tolerance until the check passes → **fix the physics, never the tolerance**

### Where the eye comes from — the operator chooses

| tier | what it is | strength | cost |
|---|---|---|---|
| **1. LM Studio vision model** | a genuinely different architecture, loaded locally (`ChimeraEngine/human_messenger.py` → `senses`) | **rock solid** — truly independent weights | clumsy: VRAM/RAM juggling on a shared 4090 |
| **2. a blind spawned instance** | a fresh agent given **only the image path**, no physics, no story, no expected answer | structurally blind — it cannot confirm what it was never told | correlated priors (same model family) — declare this |
| **3. Alan** | the actual terminal | authoritative, ends any dispute | his time |

**Tier 1 is the standard and it is optional.** Whether to spin it up is the **operator's call**,
based on his mood and how much he trusts the agent doing the work — so *offer* it, do not demand it,
and never treat a dark eye as a blocker when tier 2 is available. What is **never** acceptable is
tier 0: the agent that built the thing judging it.

**Hard rules of the human side:** the eye disagreeing means **the physics is wrong — start over.**
Only the operator may override a reading, because he is the terminal.

### The light only comes from Chimera

The eye must judge what the **engine** renders — live, in motion — not a still where you chose the
camera and the moment.

```bash
python ChimeraEngine/gallery.py 8765          # the shared view
```

| URL | for |
|---|---|
| `/live` | **the operator.** All labels, and the caption *"physics expects: …"*. He is entitled to both sides. |
| `/live?blind=1` | **a proxy eye.** Identical picture, all labels and navigation intact — only the expected-answer sentence withheld. Shown the answer, an eye confirms instead of observes. |
| `/frame?term=X` | **one request, one JPEG**, rendered by the viewer's own pipeline. No browser, no clicking. |

**It is a web server — ask it for the page.** Do not drive a browser to do what a GET does.

---

## 4. The engine loop, and the authority you have

The tree (`grow.py`) is how a membrane is *built*. The engine is how it is *gated*:

```
orient → next → frame → question × N → classify → render → [dyad] → prove
```

1. **`orient` first, every time.** Read the state; never guess it.
2. **You do not pick the term — `next` does.** Setting-first from the seed. Jumping to a mid-tree
   scene is this project's founding failure, and it has been repeated since.
3. **Discover variables by `question`, never declare them.** Keep asking until `saturated` (dry tail
   + Chao2 completeness). **Inventing variables in your head is already a failure**, and stopping
   because you *feel* done is how you get 0.53 completeness and a chapter of one-offs.
4. **`classify`** each to `PHYSICS` (yours) or `THE HUMAN` (Alan's `decide`). No other terminal is
   legal. **An LLM is never a terminal.**
5. **`render`, then let the dyad judge.** No render = nothing to judge = cannot be proven.
6. **`prove` only through the tool.** Read the refusal; do exactly what it says.
7. **Taste terminates at the operator.**

**You are the head of the dragon.** You own every technical decision and execute without asking which
wrench to pick up. **Legal stops:** (a) the term is proven, (b) a real blocker — name the cause,
(c) a taste decision, (d) the eye is dark *and* no tier-2 reader is possible. *"Which term?"* is
never legal — `next` answered it. *"Which approach?"* is never legal — that is your half.

---

## 5. A chapter is a folder describing everything inside ONE membrane

**A membrane is a boundary. A boundary is a scale.** The folder tree *is* the scale ladder, and a
chapter's **path is its serial is its compressed story**:

```
theZero/theHorizon/theEmptying/theCooling/theCloud/theGalaxy/theSolarSystem/theStar/aYellowStar
 = "the point you may not divide by, fenced, emptying into the space it drew, cooling until
    structure is permitted, gravity finally allowed to pull, gathered into an island of stars,
    swirling into a system, and in it a fall stopped by fire, and this one is yellow"
```

*(For years this example read `theCloud/theSolarSystem` with no galaxy between — the file
demonstrating the very "skipped a level" failure it names in §8. A cloud does not become a system on
its own. Check `HIERARCHIES.md`.)*

```
theCooling/
  story.md        the human story — WHAT this is, and what it DECLARES it contains
  physics.py      derive(parent, free) -> numbers      the EDGE from the parent
                  emit(numbers, t)     -> matter       the same numbers, made visible
  numbers.json    what it grew                (generated)
  contents.md     what it actually contains   (generated — never edit)
  trained.json    the free numbers, once fitted (optional)
  <child>/        the membranes contained in this one
```

**Work ONE membrane at a time.** A chapter is the description of everything contained in the membrane
you chose — not a race down the tree.

### `the` and `a` — the prefix is a classification, and it is the target shape

Every concept wants **two** membranes, because they are different kinds of claim:

| prefix | what it is | example |
|---|---|---|
| **`theX`** | **the LAW** — what an X *is*, and what any X must satisfy | `theStar`: a fall stopped by fire, above a minimum mass of 0.070 M☉ |
| **`aX`** | **the INSTANCE** — the one that formed here, inheriting from the law | `aYellowStar`: M = 1.025 M☉ → R, L, T = **5839 K**, lifetime 9.4 Gyr |

The law says what is **possible**; the instance is what **happened**. An instance sits *inside* its
law and reads its numbers from it, so it cannot contradict it — and the law stays checkable against
reality independently of any instance grown from it.

Aim for both, everywhere — but the instance's name is **derived**, so you do not know it in
advance: `theTerrain` produced **`aRiverTerrain`** because 57% of its land gets rain rather than ice.

**The taxonomy differs by kind, and picking the right one is part of the work.** A body seen from
OUTSIDE is classified by its colour, because that is what its surface is made of (`aYellowStar` from
the Harvard sequence, `aBlueWorld` because its water is liquid). A surface you **stand on** is
classified by **what carves it** (`aRiverTerrain`, `aGlacierTerrain`, `aDesertTerrain`). Same rule
either way: **the class word is whatever physics is in charge.**

**An instance is named by its KIND, and the kind is DERIVED.** Not `aStar`, `aStarB` — **`aYellowStar`**:

```
T_surface = 5839 K  →  Harvard class G  →  "Yellow"  →  folder: aYellowStar
```

`measure()` checks the folder name still matches the class its own physics produces, so a wrong
rename fails and a changed mass forces a rename. **The name is a claim; test it like one.** Use the
real taxonomy per kind — spectral class for stars, composition for worlds — never letters.

**It is also a diagnostic.** A membrane with no opposite number is usually a membrane nothing
derived. `theTerrain` was a painted scene for months — a law with no instance — and it carried wrong
numbers the whole time; it is now derived, and it produced `aRiverTerrain`. **`aPlanet` is the one
still left**: an instance with no law, painted, deriving nothing.

Viewer colours: **green = `the` (a law) · red = `a` (an instance) · hollow = not built.**

### Every chapter opens with plain words, before any equation

```markdown
# theCooling

**In plain words —** As the universe spreads out it cools, and every time it gets cold enough,
one more kind of thing is allowed to stay in one piece instead of being smashed apart.
```

**That line is not a summary of the chapter. At that zoom it IS the chapter.** Zoom in and it becomes
the equations; zoom in again and it becomes its children, each of which is again one sentence. So the
story is readable at **any** resolution and is *complete* at each one — which is **LOD of meaning**,
the identical law the matter obeys: every level is the level below, averaged.

That is why it is **required**, why `grow.py` harvests it into every ancestor's `contents.md` (a
parent's contents list is its children at lower detail), and why it must never drift: it is not
documentation *about* a level, it is *the level itself*. Unlike a code comment, it is **consumed** —
a wrong or missing line shows up immediately as a wrong or empty parent index.

```bash
python story/grow.py --read --depth 2      # the universe in three sentences
python story/grow.py --read                # the whole chain, seed to star
```

### LISTING is generated. DEFINING is written.

- **LISTING** what a membrane contains is mechanical — the folders already know. `grow.py` writes
  `contents.md`. **Never type a contents list**, or every new membrane means hand-editing every
  ancestor forever.
- **DEFINING** what it *is* (`story.md`) and how it *works* (`physics.py`) is the writing.

Keep the two lists separate: **DECLARED** (`story.md`, the story's promise) vs **BUILT**
(`contents.md`, the folders that exist). **The gap between them is the work remaining.**

---

## 6. COMPOSITION — a parent is MADE OF its children

`layout(nums)` returns `{child: (centre, scale)}` in **your** frame, and the child is grown, emitted
in **its own** local units, and placed. The parent supplies only **where** and **how big** —
structure, which is its own physics. The child always supplies its own appearance.

Four rules, each learned by breaking it:

- **Convert units at the seam.** A child works in *its* unit; you work in *yours*. `thePlanets` is
  in snow-line units, `theSolarSystem` in disk-edge units — placed at 1.0 the composed extent came
  out **11.2**. If you find yourself converting, ask whether the number should live in the parent
  instead: the snow line is a fact about the *system's light*, so the system derives it and the
  planets inherit it. **Two authorities for one number is how they drift apart.**
- **LOD every placed child by its size.** Placing a full-resolution child into a small footprint
  crams its grains into one 32-px tile, overruns `MAX_PER_TILE`, and the cap evicts *the parent's*
  grains — **a black, tile-shaped hole**. A thing occupying 4% of the frame does not need 20,000
  grains to say so. Use **`matter.grains_for(radius, extent)`**; do not eyeball it. (Measured: eleven
  worlds at a flat 900 grains each put 4,801 splats in a tile that allows 4,096. The law was written
  in a comment for the star six lines above the loop that broke it.)
- **A SCALE STEP COMPOSES. AN ASPECT STEP MUST NOT.** `layout()` places a child that is *inside* you
  at a *smaller* scale. It is the wrong tool for a child that is the SAME OBJECT seen differently.
  `theRockyPlanet` → `aRockyPlanet` → `aBlueWorld` → `theTerrain` are one body four ways — the rock,
  its interior, its climate, its surface — all at extent = R, scale 1.0. Composing those would draw
  the same sphere four times, interpenetrating. The chain below them **is** a scale ladder
  (`theTerrain` 5,256 km → `aTerrain` 12 km → `theGround` 4 m → `theHuman` 1.78 m) and every one of
  those seams is wired. Ask which kind of step you are at before reaching for `layout()`.
- **PLACE IT EVEN WHEN IT IS SUB-PIXEL.** A 12 km patch on a 5,256 km globe is two parts in a
  thousand; a 4 m ground patch on that 12 km is another thousandth. Neither is visible at its
  parent's framing, and both are placed anyway — because that is what makes the tree ONE OBJECT
  instead of a stack of separate pictures. Zooming then reads the same derivation at a finer level
  rather than opening a different file. The LOD budget cuts an invisible child to a handful of
  grains, which is exactly right.
- **Never duplicate a child.** `theSolarSystem` drew its own core *and* placed `theStar` — the same
  matter twice, and it was what overran the tile.
- **A SIBLING'S NUMBER COMES THROUGH THE PARENT, OR NOT AT ALL — and the failure mode is a
  LITERAL.** `theStar` and `thePlanets` are siblings, so the planets cannot read the star. What
  happened instead: `thePlanets` **typed `"T_star_surface": 5772.0`** under a comment saying
  *"carried from the system's luminosity"*. It was carried from nowhere. Change the star's mass and
  the snow line moved while the sunlight stayed exactly the same colour, forever. The fix is never
  to type the value — it is that **the parent carries it**, because being the thing both children
  can see is what a parent is FOR. The system now derives `R_star` and `T_star_surface` once, and
  both children read them.
  **The test is a slider:** move a free number at the top and every consequence must move. Anything
  that does not move is typed. Moving `M_system` now walks the star K→G→F→A, shifts the snow line
  1.54→7.56 AU, and selects a *different* habitable world with different gravity.
- **A membrane may only read its PARENT.** This is not tidiness: it decides what can reach what.
  `theDensityClock` sitting inside one solar system made time dilation **unreachable from
  `theShip`** — a dependency that does not resolve. It moved beside `theHorizon`, whose radius *is*
  its ceiling, and now everything below inherits it.

---

## 7. Three tests every chapter must pass

### PROVEN — the math closes, and predicts what it was never fitted to
A membrane reads **only its parent** — never a sibling. If you are *choosing* a number you broke the
chain and substituted taste for a law. The test of a real derivation: **it predicts a fact it was
never given.**

| chapter | in went | out came | reality |
|---|---|---|---|
| theCooling | η, mₑ, 13.6 eV (Saha) | atoms at **3760 K** | ~3700 K |
| theCloud | that T, **η** (not today's density — see §4c) | first collapsible mass **6.07×10⁵ M☉** | 10⁵–10⁶ |
| **theGalaxy** | the same Jeans law, run **down** the ladder | fragmentation stops at **1.75 M☉**; metal-free gas at **150 M☉** | why a star weighs a sun; **why Population III were hundreds** |
| theStar | G, ħ, mₑ, m_H, ignition T | minimum star **0.070 M☉** | 0.075–0.08 |
| thePlanets | the star's L | snow line **2.80 AU**; T at 1 AU **284 K** | belt 2.1–3.3; Earth 279 K |
| **theRockyPlanet** | v_esc vs √(2kT/m), one inequality | Earth keeps N₂/O₂/H₂O/CO₂ and **loses H₂ and He**; Mars sits on the margin | both exactly right, neither fitted |
| **aBlueWorld** | greenhouse + ice-albedo + carbon, solved as a fixed point | Earth's own mass and orbit return **288 K** and a **2,700 m** ocean | 288 K, 2,700 m |
| **theTerrain** | σ/(ρg), and Airy isostasy | Earth: **29.6% land**, **3,815 m** mean ocean. Mars holds a mountain **2.6×** Earth's tallest | 29%, 3,800 m; Olympus/Mauna Kea = 2.15× |
| theDensityClock | GM/rc², v²/2c² | GPS drift **+38.5 μs/day** | 38.6 |

**Read that Mars row as the shape of the whole test.** `h = σ/(ρg)` contains no geology — only
gravity and the strength of rock — and it says a low-gravity world carries a taller mountain. It was
shown Earth and returned Mars.

### VISUAL — it emits its own matter, and it turns

> **A RENDER MAY NOT CONTAIN A BODY THE DERIVATION DID NOT PRODUCE.** An exaggeration may *scale*
> something derived. It may never *invent an object*. Observed: the planet membranes drew a small
> sphere beside the world, commented *"the star, drawn as a marker — direction true, distance
> declared-false"*. A star is 28,000 planetary radii away and a quarter of a degree across: at any
> framing that shows the planet it is **off-screen and sub-pixel**. Drawn at 1.3 radii it is not a
> star, **it is a moon**, and no moon was ever derived. Alan saw it in one glance.
>
> **A light source is told by its light.** Where the star was, was already fully said by the
> terminator, by which limb is lit, by the shadow. The marker was redundant *and* false.
>
> **The tell:** you catch yourself writing "so you can see where X is". If X is off-screen at true
> scale, say it with its EFFECT, or go up a level — `theSolarSystem` is where the star and the
> planets are both real and both placed. **That is what the hierarchy is for: you build the star
> first so that you can see the planet.**
`emit()` lives in the **same file** as `derive()` and reads the **same numbers**, so appearance
cannot drift from physics — there is nothing to cross-check because they are one thing.

- **NO AESTHETIC PASSES.** A colour is a measurement. `theCooling` ends salmon because 3760 K *is*
  salmon.
- **A splat is a measurement of light, not a coloured object:** `L_out = albedo · E / π`. The matter
  says what *fraction* it returns; the light says how *much* arrives (`matter.lit()`). The same rock
  is brilliant near a star and near-black far from one, and neither is a different material.
  Emissive matter — a star — *is* light and needs none.
- **Sample the video.** One frame cannot show motion. Comparing frames is what caught a viewer
  silently refusing to switch scenes: the label changed and the render did not.
- **Local units at every membrane.** A horizon is 2.3×10⁻³⁵ m, a planet 6.4×10⁶ m; in metres one is
  float dust. Emit at radius ~1 in your own frame — **grain size included** (`SIZE=2.6` on a
  radius-1 sphere is bigger than the object; it rendered a solid blue disk).
- **Declare every exaggeration — and make it a DIAL.** At true scale a star in its own disk is
  **sub-pixel**. Draw it 32× oversize if you must, but that number belongs in the membrane's `LENS`
  dict, not buried in `emit()`, so it appears in the viewer next to the true value with a **"show it
  at true scale"** button beside it. A lie you can turn off is auditable; a constant is not.
  **A `FREE` dial changes what the world IS and re-derives the subtree; a `LENS` dial changes only
  the picture.** Never merge the two panels — one is a fact you may choose, the other is a lie you
  may see through.

### The render laws — every one of these was a DEFECT first

They live in code comments where they were learned, which is how two of them got broken a second
time. They are laws, not preferences, and each has a **tell** you can look for.

| law | why | the tell when it is broken |
|---|---|---|
| **The grain must be at least half the spacing.** `matter.surface_grain(n)` | *n* grains on a sphere sit `sqrt(4πr²/n)` apart. Narrower than half that and the surface leaks — and there is nothing behind a planet, so the leak is **black**. | an ocean that reads as loose grit floating in space |
| **The grain COUNT follows projected area.** `matter.grains_for(radius, extent)` | A thing that occupies one pixel does not need a thousand grains to say so. A thousand all land in one 32-px tile, overrun `MAX_PER_TILE`, and the cap **evicts everything else in that tile**. | a hard-edged **black rectangle** whose pixel bounds are multiples of 32 |
| **The material decides the splat.** | Ice and rock ARE granular — crystals, gravel, snow. **Water is not**: a liquid has no smallest piece, so its splats must be *wider than their spacing and half transparent* so no single one is ever visible. | a smooth ice cap above a sea of blue pebbles |
| **Topography has a RED spectrum** (power ~ 1/k) | Independent per-grain heights are white noise, and white noise renders as spikes — a real hill's neighbour is nearly the same height. Sum waves at 1/k amplitude and you get ground. | a hedgehog |
| **Exposure is a declared instrument setting.** `lit(..., e_ref=)` | `e_ref` is the irradiance the render calls "correct exposure". Leave it at one solar constant and a world further out is physically right and **too dark to read**. A camera exposes for its subject. | a measured 47→15 grey ramp you cannot see |
| **A membrane's movie shows ITS OWN rhythm.** | `theHumanClock`'s gearing law. A one-YEAR movie cannot also show 394 sunrises — that is flicker, not a day. The day belongs to the ground, one rung down, where it is the right length of film. | strobing |
| **A season is not a second variable — it IS the sun's declination.** | The spin axis is fixed in space while the planet orbits, so the sun climbs above the equator and falls below it once a year. One number tilts the terminator AND melts one cap while growing the other. | two phases that drift apart |
| **Frame on a PERCENTILE, not the maximum.** `scene_cam_distance` | One distant marker grain otherwise defines the framing and leaves the subject a dot 9 units away. | a correct render of nothing |

### LEARNED — the free numbers are trained, never tuned
The law fixes the **form**; what it leaves open goes in `trained.json`, fitted against that
membrane's own measurable target. **Program the rules, train the numbers.** You write the
constraint; you never turn the crank.

Because every chapter inherits from above, pieces are **made for each other without being fitted
together**: a gait trains against the `g` its planet handed down and the `μ` its ground handed down.
Change the planet and the same equations produce a different creature. **One law, every world.**

---

## 8. Laws of the tree

- **Linear, yet branched.** Every path from the seed to a leaf is one linear story; a tree holds many
  and they share an origin. Sequence runs *along the branches*.
- **Containment is not sequence.** A star and its planets happen in order yet live at the *same
  level*, because a system contains both. Nesting each new chapter inside the last produces a
  hierarchy claiming a star contains a planet. (Made here; do not repeat.)
- **From zero, only ADDITION is legal.** Nothing is deleted from the story — chapters are revisited
  and improved. Safe precisely because a child consumes its parent's `numbers.json`, never its
  parent's *reasoning*.

---

## 9. How to run it — THE WEB SERVER

### The viewer — this is the deliverable, not a debug tool

**Double-click `DEMO.bat`.** That is the whole answer for a human. It finds python, frees a stale
port, starts the server, waits until it actually *answers* (not until the process exists), opens the
browser, and prints the real error if it fails. Closing the window stops it.

From a shell it is:

```bash
python ChimeraEngine/gallery.py 8765          # then open http://127.0.0.1:8765/live
```

**When you are told to work on a membrane, the only acceptable response is the PICTURE of that
membrane.** Not a description of it, not a claim that it renders. Fetch the frame and LOOK at it.

### How the server is actually built — read this before you debug it

**One process, one GPU, one render thread.** `gallery.py` is a `http.server` on **127.0.0.1 only**
(the studio's bind rule — never `0.0.0.0`; the pre-commit hook enforces it). It mounts
`live_viewer.py`, which owns a **single background thread that is the sole owner of the GPU**.
Nothing else may touch the pipeline. That thread:

1. sleeps while `_clients == 0` — **with no viewer connected it does not render at all**, so the
   4090 is free for LM Studio. Ask for a frame and it wakes;
2. re-emits when the term, the time `t`, or a dial has changed;
3. renders, JPEG-encodes, and publishes the bytes;
4. pushes them to browsers as **MJPEG** (`multipart/x-mixed-replace`) on `/stream`.

So the page is not polling and there is no websocket. `/live` is a static HTML shell whose `<img>`
points at `/stream`; every control is a plain `fetch()` that returns **204 No Content** and changes
the thread's state. **It is a web server — ask it for the page.** Do not drive a browser to do what
a GET does.

**Consequences you will hit:**

- **A stale server holds the port and the new one dies silently.** That is the usual reason "nothing
  happens". `DEMO.bat` frees it for you; by hand, kill whatever owns 8765 first.
- **Errors do not reach the browser.** The render thread catches and stores them. Read
  `gallery_err.log` / `gallery_out.log`, or `live_viewer`'s `_err`.
- **The first render of a session compiles CUDA kernels** and can take a while. That is not a hang.
- **Two servers cannot share the GPU.** Start one.

### The pages

| URL | what it is |
|---|---|
| `/live` | the interface: hierarchy on the left, chapter in the middle, dials on the right |
| `/live?blind=1` | identical picture, navigation intact — **only the "physics expects…" caption withheld.** For a proxy eye: shown the answer, an eye confirms instead of observes |
| `/stream` | the MJPEG stream the page's `<img>` reads. Opening it counts as a client |
| `/frame?term=X` | **one request, one JPEG.** No browser, no clicking. **This is how an agent looks at its own work.** |
| `/terms` | JSON list of every renderable term |
| `/` | the still gallery — the settled `output/movie_*_end.png` renders |

`/frame` sets the scene and **blocks until that term has actually loaded AND a new frame exists**,
so it cannot hand you the previous membrane's picture. A response of exactly **33,267 bytes is the
blank placeholder** — the render never happened; it does not mean the membrane is black.

### The controls, and they are two different kinds

| endpoint | kind | what it does |
|---|---|---|
| `/time?t=0..1` | — | scrub the membrane's own movie, `t=0` its beginning to `t=1` its settled end |
| `/free?term=&name=&value=` | **the world** | move a `FREE` number. **Re-derives the whole subtree.** |
| `/lens?term=&name=&value=` | **the picture** | move a `LENS` number. Re-emits only; nothing downstream moves. |
| `/input?dazim=&delev=&zoom=` | — | orbit and zoom |

**Never merge those two panels.** A `FREE` dial changes what the world *is*; a `LENS` dial is a
declared exaggeration — a lie the render is telling, shown with the handle to turn it off. `/live`
has a **"show it at true scale"** button that sets every lens to 1.0, and what you get is usually a
smooth ball and an empty black disk. That is the honest picture.

They also behave differently, and the difference is the point:

- `/free` writes the value to that membrane's **`trained.json`**, runs `grow.py`, and forces a
  reload — so **every `numbers.json` below it is rewritten on disk.** It is slow, and it is supposed
  to be: you changed the world.
- `/lens` writes to that membrane's **`lens.json`** and re-emits. Nothing is regrown, no page
  reload, next frame shows it. You changed the camera.

Both are readable from `physics.py` without running anything — `FREE = {...}` and `LENS = {...}` are
module-level dicts the viewer parses with `ast`, which is why a dial appears in the UI the moment you
declare it and needs no registration anywhere.

### Driving it from an agent, without a browser

```bash
curl -s "http://127.0.0.1:8765/frame?term=aBlueWorld" -o frame.jpg   # then LOOK at frame.jpg
curl -s "http://127.0.0.1:8765/time?t=0.35"                          # scrub, then fetch again
curl -s "http://127.0.0.1:8765/free?term=theTerrain&name=continental_fraction&value=0.15"
curl -s "http://127.0.0.1:8765/lens?term=theTerrain&name=relief&value=1"
curl -s "http://127.0.0.1:8765/terms"
```

`/time`, `/free`, `/lens` and `/input` return 204 and change state; fetch `/frame` afterwards to see
the result. **Sample more than one frame** — one picture cannot show motion, and comparing two is
what caught a viewer silently refusing to switch scenes: the label changed and the render did not.

### Growing and reading the tree

```bash
python story/grow.py                              # grow it; writes numbers.json + contents.md
python story/grow.py --read [--depth N]           # READ the story at any resolution
python ChimeraEngine/splat_appearance.py <term>   # render one chapter's movie, begin -> end
```

`grow.py` is the only machinery: the same three moves at every folder, which makes this **growth
rather than construction** — a cell does not consult a blueprint of the finished body; it divides
and differentiates from local signals, and its position determines its identity. Here that is
literal: a folder's path is its address, its parent's numbers are its signal.

**Adding world means adding a chapter. It never means adding more machinery.**

### Checking that the chain is real

```bash
python story/audit.py                # all three checks
python story/audit.py --typed        # numbers that did not come from the parent
python story/audit.py --assumes      # the assumption manifest
python story/audit.py --slider       # move every FREE dial; who responds?
```

Three ways a derivation quietly stops being one, each of which shipped into this tree:

- **`--typed`** — a bare number in `derive()`'s return (`"T_star_surface": 5772.0`), **or** the
  disguised form `parent.get("k", 86400.0)`, which reads as defensive programming and serves a typed
  value the instant the parent stops carrying `k`. Silently. `.get` cannot fail.
- **`--assumes`** — module constants `derive()` uses on its own authority, minus laws of nature and
  unit conversions. Of each one ask: **does my parent already know this?**
- **`--slider`** — the one that convicts. Move a `FREE` number and every descendant that depends on
  it MUST move. Anything that does not move was typed. If a dial really is local, say so in its
  `FREE` entry — `"local": "<the reason>"` — so the claim is written down instead of being a silent
  absence, and the audit will honour it.

### The rasteriser instrument

```bash
CHIMERA_TILE_DIAG=1 CHIMERA_TILE_DIAG_AT=0.1 python ChimeraEngine/gallery.py 8765
```

Reports any 32-px tile filling past that fraction of `MAX_PER_TILE`. **The tell you are looking for
is a hard-edged black RECTANGLE on the tile grid**, not a dim patch — measure its pixel bounds and
if they are multiples of 32, it is a tile eviction, not a coincidence.

The cause is always the same: too many grains packed into a sub-pixel body, which overruns the tile
and evicts everything else in it. The fix is always the same: **`matter.grains_for(radius, extent)`**
— grain count follows PROJECTED AREA. A thing that occupies one pixel does not need a thousand grains
to say so. (Measured: eleven worlds at a flat 900 grains each put 4,801 splats in a tile that allows
4,096. With the law applied they take 176 between them.)

---

## 10. The ways this goes wrong — all observed in one build

| failure | what it looked like | the tell |
|---|---|---|
| **the monad** | judging your own render; measuring pixels off your own picture; scripting the engine from a driver | it *feels* like diligence. One system twice is not evidence |
| **traced then ignored** | 39 variables saturated and classified, render made from `fbm()` noise | relief 40× Earth's; unimodal where reality is bimodal |
| **declared, not discovered** | writing down the variables you think a membrane has | the curve never saturates; Chao2 ~0.5 |
| **imposed the result** | translating a body's root to fake walking | the ground slid **sideways** under it |
| **wrong substrate** | a rhythm oscillator bolted onto a 290-dim action space | survival collapsed 68 → 17% |
| **skipped the parents** | training a walk with no proven ground beneath it | nothing to stand on, literally |
| **two authorities** | a term in both the old `SCENES` dict and the new tree | the **old object rendered under the new label** |
| **claimed before drawn** | a frame served before the scene loaded | three terms, three **identical byte counts** |
| **saturation** | 16k soft blobs piled into one place | hard **square tiles** — a render lying about density |
| **widened the tolerance** | the check passes now | fix the physics, never the tolerance |
| **let it run** | watching a dying run "to see how it ends" | pure cost; kill at the **first hint** |
| **skipped a level** | `theCloud → theSolarSystem` with no galaxy between | check `HIERARCHIES.md`; a cloud does not become a system on its own |
| **unreachable physics** | a law parented inside one place | `theShip` could not reach `theDensityClock` — a membrane reads only its PARENT |
| **not mass-conserving** | a growth rule that hands out more than exists | 101 Earth masses from a disk holding 56 |
| **no control** (2026-08-01) | reporting a genome measured only on the thing you care about | run the SAME instrument on the clay you SENT -- three of four features came back identical, i.e. they were the fitter's signature, not the material's |
| **measured at the wrong scale** | "the octaves made it *less* detailed" | the finest one is **0.6 px** at that framing; an instrument that cannot resolve an effect returns a wrong number, never "cannot see" |
| **self-normalised threshold** | a growth rule meant to *measure* complexity | a detailed take and flat clay both reached **5,619 splats, identical to the digit** -- a quantile of your own population reports nothing about it |
| **the data was the artifact** | blaming new code for a visible cross-hatch | the **canvas** measured 27.8× directional, the new code 1.1× -- and the artifact had been quietly biasing the spectral slope to 2.54 where the law gives 2.95 |
| **name, not definition** | joining a codebook by matching feature names | `aniso` read **2.25** against a real range of 0.296-0.996 -- a dimensionless quantity on the wrong interval, which no unit check can ever see |
| **one constraint applied per-part** | capping each octave at the repose limit | five capped octaves sum to well past repose, because **slopes add** -- a whole-surface constraint goes on the whole surface |
| **debugged forwards** (2026-08-01) | six hypotheses tested against a foot that went through the floor | every one eliminated -- the foot was faithfully executing an instruction from **four membranes up**. Walk UP the chain, not around the symptom |
| **two landmarks, one name** | `trochanterionheight` ingested as "hip height" | **three leg lengths in one leg, 3.11 cm apart** -- the trochanterion is a bump on the femur, the hip JOINT sits above it, and no dimensional check can see the difference |
| **the witness kept its own copy** | `thigh, shank = 0.245, 0.246` typed inside the instrument | the moment the body's segments were measured it graded the new skeleton against the old and invented a 1.78% penetration. **Four times in one day.** Read published numbers; refuse when absent |
| **an authored phenotype in a grown world** | a gait read from 246 Earth adults, worn by a body at 0.72 g | no geometry can seat it -- a -49 deg toe-off is an *Earth push-off*. The witness is the FITNESS FUNCTION; the dataset is the CONTROL, not the answer |
| **duplicated a child** | parent draws its own version *and* places the child | the same matter twice; it overran a tile and left a black hole |
| **two copies of one function** | `fibonacci_sphere` in both `matter.py` and `splat_appearance.py` | one gained `jitter`, the other did not — crash, and drift |
| **invented a body** | drew a "star marker" 1.3 radii from a planet | it reads as **a moon**; nothing derived a moon. An exaggeration scales what exists — it cannot mint an object |
| **a literal wearing a comment** | `"T_star_surface": 5772.0` under *"carried from the system"* | move the source; if the consumer does not move, it was typed. Reach for the PARENT, never the keyboard |
| **a bug that hides where you test** | bilinear fractions swapped across axes | it cancels *exactly* at the patch centre — which is the spawn point. 5 km away it returned **13,414 m** on a field whose maximum is 451 |
| **the movie ran backwards** | a fogged plate that *fogged up* over a chapter titled "clearing" | t=0 and t=1 both looked plausible. **Sample five values of `t`, not two** |
| **the endpoint wrapped** | `tt = float(t) % 1.0` sends 1.0 → 0.0 | the canonical still export renders exactly `("begin",0.0)` and `("end",1.0)` — a wrapped end makes the two-frame check show **nothing happening** |
| **a false comment** | *"the parent's own continental roughness"* above a line passing a hard `3.0` | **nothing checks a comment.** A false comment is a typed number's alibi |
| **the instrument lied** | `audit.py` reported zero `get-default`s while six were live | it exempted 0 and 1 as *default values* — and those are the **worst**: `S_earth: 1.0` is a full Earth's insolation, `scale_height_m: 0.0` makes wind **infinite** |
| **a grandparent read a grandchild** | `lat = 30.77072291868692` typed into `aBlueWorld` — `aTerrain`'s latitude | the inverse of the sibling failure, and it has the same tell. Pass the **law** down (`u = scale / sin(lat)`), let each child evaluate at its own place |
| **an ancestor holding a descendant's number** | `LEG_M = 0.845` — a **human leg length inside a planet** | a planet hands down `g`; a body computes its own walk from its own length. *Still live in `theRockyPlanet`* |
| **derived, then applied to the wrong axis** | a 20 cm stance written on **X**, the axis the leg swings along | the figure measured **0.37 m across the front and 0.97 m from the side.** A walking person is wider from the front |
| **a simulation where the consequence belongs** | `bob = 0.018*cos(2*phase)` standing in for the centre-of-mass vault | it cannot be wrong, because it computes nothing. Once the hip rode the stance leg the real value was **4.3%** — the typed one was out by 2.4× |
| **the prose was the spec, and it was right** | *"the stance knee stays near straight"* while the code bent the **stance** knee | both claims predated their truth by months. **Grep the story for a claim, then check the code does it** |
| **geometry asked a question it cannot answer** | "where does the foot touch?" during flat-foot stance | **a flat foot has no lowest point.** The mark sat on the heel then *teleported* to the toe. Centre of pressure advances because the *body* does |
| **my own threshold was the flaw** | a front/side silhouette test that flagged a *correct* figure | a walking person legitimately spans more fore-aft than across. **Test drawn value against DERIVED value**, never against a ratio you invented |

**Economy is a rule.** A run whose outcome you already know is entropy — watts, heat, wall-clock,
zero information. Kill it. The counter-rule is equally hard: **a number without its control is not
evidence** — 0.7% survival looked like collapse until laid beside the baseline, where it was step
zero of the same curve. The baseline adjudicates.

### The three habits that caught every one of those

1. **Measure the artifact, never the readout.** The walker's own HUD said elevation 176.0 m and it was
   right; the *buffer* said grains at ±700 km. Read the array, not the summary. Every real defect
   above was found this way and none were visible otherwise.
2. **Sample the movie.** One frame cannot show motion, and a scene that silently failed to switch is
   pixel-identical to one that worked. Five values of `t`, and check the **ends** specifically.
3. **Then look at the picture.** After the numbers pass, render it and *look*. Two things only the eye
   caught this build: a fused leg column, and a body reading as one pale tone because the relighting
   hard-coded a single albedo over three derived materials.

### When a child needs its parent's reasoning, publish a table

The rule is numbers-not-reasoning. Restating a parent's function inside the child satisfies the letter
and invites exactly the drift the rule exists to prevent — two copies that agree until one is edited.
`theHuman` publishes **48 samples of its gait cycle** and `aHuman` indexes it: one gait, one place,
cannot diverge. Prefer a published table to a restated law.

### Repo hazards — 60 seconds that saves an hour

- **A background automation commits the dirty tree mid-session.** It split one change of mine across
  two commits (`chore: auto-flush working tree`). **`git add` by path**, never `-A`, especially with
  other agents running.
- **`live_viewer.py`'s page has a TDZ trap.** A `let`/`const` read before its declaration line *runs*
  throws **even under `typeof`**, and it kills the whole script silently — the page still looks alive
  because the lines before the throw execute. That page had been half-dead since before I arrived:
  the tree switched scenes while the time slider, the drag handlers and everything below were a
  corpse. New top-level state in that script goes in `var`, or above the first `pick()` call.
- **The server caches code.** Restart `gallery.py` after editing it, or you will debug a stale page.
- **`grow.py` refuses a chapter with no `story.md`.** Deliberate: the human writes the node.
- **`cd story` persists** in the shell between commands; relative paths then resolve wrong.
- **Two agents: split by FILE, not by task.** Name exactly which paths each may touch. Overlapping
  `physics.py` edits produce a half-written tree that still passes `grow.py`.

---

## 10b. The one habit that caught all six

Before you report a number, **name the thing that would have to be true for it to be an artifact,
then go and measure that.** Six times out of six in one day it was cheaper than the retraction.

The cheapest version of the habit, and this project hands it to you free: `emit()` produces the
membrane's own matter from its own numbers, so a render of it is a subject whose answer you know
**by construction**. Push that through whatever is measuring the real thing. If the two come back
the same, you were measuring the instrument.

> A measurement without a control is not a weak measurement. It is not a measurement.

And its mirror, for when a result comes back NEGATIVE: an instrument that cannot resolve an effect
does not refuse — it returns a number, often in the wrong direction. Count how many pixels, samples
or bins the effect occupies before you believe a null.

Rules 11–16 of `Chimera/docs/EXPERIMENTAL_METHOD.md` carry all six with the numbers.

---

## 11. Working with Alan

- He speaks in bursts and corrects hard. **The correction is the signal** — take it literally, not
  diplomatically. He has caught by eye: an amputated body, a sideways-sliding ground, a mis-metered
  gait, a planet made of noise, and a missing star.
- **Do not hand him work to run.** Test it yourself, then show the result.
- **Show real output.** Renders he cannot see do not count. Send the picture.
- **Push to GitHub every time.** Commit to `master`, never a branch; state branch + SHA.
- **Do not ask him to re-specify what he has already written.** The story exists — go read it.
- The **workflow is the product**; the game is the benchmark, because physics is the one domain that
  cannot be flattered.

---

## 12. Where things are

### The tree and its language

| path | what |
|---|---|
| `story/` | the tree. Every folder is a membrane |
| `story/README.md` | how the game is built (short) |
| **`story/LANGUAGE.md`** | **the grammar** — four verbs, the article system, unit suffixes as a type system, and §7's **visibility model**: `numbers.json` is `protected`, a `derive()` local is `private`, and there is **no `public`** |
| `story/HIERARCHIES.md` | **the prebuilt paths** — cosmic and biological. Check before inventing a level |
| `story/grow.py` | the enzyme — same three moves at every folder |
| **`story/audit.py`** | **the three checks** — `--typed`, `--assumes`, `--slider`. A rule nothing checks is prose |
| `story/matter.py` | the splat buffer, `lit()`, `blackbody_rgb()`, `surface_grain()`, `grains_for()` |
| `story/clock.py` | `dynamical_time(ρ)`, `light_crossing(r)`, `child_phase()`, `human(seconds)` |
| `story/scale.py` | how big a thing is **said the way a person would say it** — and `travel_time(d, a)` |
| `story/claim.md` | the claim template |

### Seeing it

| path | what |
|---|---|
| **`DEMO.bat`** | **double-click.** Starts the viewer, waits until it answers, opens the browser |
| `ChimeraEngine/gallery.py` · `live_viewer.py` | the server: `/live`, `/live?blind=1`, `/frame?term=X`, `/time`, `/free`, `/lens` |
| `ChimeraEngine/splat_appearance.py` | render + composition; folder membranes win over the old `SCENES` dict |
| `ParticleEngine/gpu_pipeline.py` | the rasteriser. `TILE_SIZE`, `MAX_PER_TILE`, and `CHIMERA_TILE_DIAG=1` |
| `ChimeraEngine/human_messenger.py` | the eye's expected readings; the LM Studio path |
| `ChimeraEngine/story.py` | read the hierarchy as a story; `audit` finds plot holes = missing why-edges |

### The method

| path | what |
|---|---|
| `Chimera/docs/THE_STORY.md` | **the human story — the source of every membrane** |
| `CLAUDE.md` | the project manual (the formula is at the top) |
| `docs/THE_WORKFLOW.md` | the method end to end: the verb (PROVE), the gates, the doc map |
| `docs/THE_METHOD_AS_A_STORY.md` | every law Alan gave, placed at the membrane that forced it |
| `docs/THE_ORDER.md` | what runs, in what sequence, and what is currently broken |
| `Chimera/docs/EXPERIMENTAL_METHOD.md` | **sixteen** rules for diagnosing a live system without fooling yourself — 11-16 are the control/scale/self-normalisation set (2026-08-01) |
| `python -m core.terms <word>` | the terminology index — 73 terms, used **literally** |

### Where the story is going

| path | what |
|---|---|
| `docs/THE_MATHEMATICS_OF_WALKING.md` | **derive before you train.** Every membrane's principle, every constant measured |
| `docs/CONTROLLER_MAP.md` · `docs/CAPTURE_LIST.md` | the controller IS the compression: ~14 atoms → ~50 formulas → ~12 buttons |
| `ChimeraEngine/THE_BODY.md` | first-person movement with real physics (**read its status banner**) |
| `ChimeraEngine/THE_RELATIVE_ENGINE.md` | why refusing a global frame is the whole trick |
| `ChimeraEngine/THE_ACTUATED_MEMBRANE.md` | matter that *does* something |
| `ChimeraEngine/ROADMAP.md` | the road to a game |
| `ChimeraEngine/SOUND_DESIGN.md` | matter's second projection. **DESIGN — not built** |
| `ChimeraEngine/RENDERER_V2.md` | the renderer rebuild. **DESIGN — not built** |
| `docs/LOCAL_BIG_MODELS.md` | what this machine can and cannot run locally, measured |

**A doc marked DESIGN is not a description of something that exists.** Check the banner before you
build against it.

---

**Start:** run `python story/grow.py` and read what it prints. Then read
`Chimera/docs/THE_STORY.md`. Then work the membrane Alan names — **one at a time.**
