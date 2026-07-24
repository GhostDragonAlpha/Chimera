# TERMINOLOGY — the words this studio uses, and what they actually mean

> Built 2026-07-23 because the vocabulary is now load-bearing. This project borrows real
> terms from genetics, physics and cell biology and uses them **literally**, not as
> metaphor. An agent that reads "recombination" as a figure of speech will write the wrong
> code; a human reading "membrane" as a synonym for "boundary object" will miss why it is
> the primitive.
>
> **Each entry answers three things:** what the word means HERE, why that word and not
> another, and where the code lives. Terms are grouped by the layer they belong to, and the
> layers are ordered bottom-up — the same order the world is built in.
>
> Machine-readable mirror: `docs/terminology.json` · query it with `python -m core.terms <word>`

---

## HOW TO READ THIS

A term in **bold** is defined in this file. A term in `code font` is a symbol you can grep
for. Where a definition rests on a measurement, the number is given — a definition without
its number is an opinion.

---

## 1. MATTER — what things are made of

**splat** — an anisotropic 3D Gaussian: a position, a covariance (its size and shape and
orientation in one 3×3 matrix), a colour and an opacity. The primitive the whole pipeline
is built on, because it is simultaneously a rendering primitive and a *statistical* one.
A splat is not a triangle and not a voxel: it has no surface and no fixed extent.
→ `core/splat_types.py`

**Gaussian splatting / 3DGS** — representing a scene as millions of splats fitted to
photographs. What a "scan" is in this repo.

**genome** *(object genome)* — the compressed description of one kind of matter. Two
halves: **morphology-DNA** (shape) and **material-DNA** (appearance). Stored as
**distributions**, never single values.
→ `docs/matter/recovered_genomes.json`

**material-DNA** — the *splat configuration*: the joint distribution of size, anisotropy,
angle, colour and opacity across a material's splats. Deliberately a **range, not an
average** — the range is what lets you generate new members of the same kind.

**morphology-DNA** — the shape half: how the pieces are placed. See **arrangement**.

**feature** — one measured axis of a genome (`size`, `aniso`, `R`, `G`, `B`, `opacity`),
each stored as `mean` + `p10..p90`.

**anisotropy** *(`aniso`)* — `1 - min_axis/max_axis` of a splat's covariance. 0 = a
sphere, 1 = a needle. Bounded [0,1] **by construction**, which is why it must be sampled on
the **liability scale**.

**serial number** — the codebook index of a *recognised* genome. Compression made literal:
once a material is in the codebook you store the serial instead of the splats. Position-
derived for places (`S+00384+00896`), genome-derived for matter.
→ `core/sections.py :: section_serial()`

**brick** — a genome expressed as a placeable object: a **membrane** carrying that genome's
measured properties plus a mating **stud**. The LEGO metaphor made precise.
→ `core/bricks.py :: brick()`

**intake method** — how a genome was obtained. Exactly two: **MEASURED** (scan → inverse
rendering → *reality*) and **AUTHORED** (GLB/OBJ PBR maps read directly → *an artist*).
Both feed one codebook, which is why **format calibration** matters.

**format calibration** — making different file formats agree numerically before they enter
the codebook. An uncalibrated container **forks the same material into two serial numbers**.
Proven case: INRIA `.ply` stores colour as an SH DC coefficient
(`rgb = 0.5 + 0.28209479177387814·f_dc`); applying `sigmoid()` instead gave p10 0.143 vs a
true 0.000. → `Construction/calibrate_formats.py`

---

## 2. ARRANGEMENT — how the pieces are placed

**arrangement** — the structural archetype of an object: *where the pieces go*, as opposed
to what a piece looks like. The operator's point: what must be learned is **how the pieces
fit**. Measured by four facts, all scale-free.
→ `core/trainables/arrangement.py`, `Construction/arrangement_dna.py`

**clustering** — mean pairwise distance ÷ nearest-neighbour distance. High = pieces gather
into distinct groups; low = evenly scattered. **The number that exposed the vocabulary
gap**: real truck-scan regions measure 4.679–8.172, while the three hand-written forms
reached only 1.277–1.497. Real matter is 3–5× more clustered than the old vocabulary could
express.

**verticality** — the mean |z| component of piece directions. 0 = everything lying flat,
1 = everything standing up.

**alignment** — how parallel the pieces are to each other (mean resultant length of their
directions). 1 = perfectly combed, 0 = random. Real material sits at **partial** coherence
(0.516–0.576) — neither combed nor random.

**aspect** — horizontal extent ÷ vertical extent of the whole arrangement.

**band** — the measured min..max of a fact across real regions. The training target is a
band, **not a value**, because real material varies from region to region and demanding a
single number would be fitting noise.

**band error** *(`*_off`)* — distance OUTSIDE a band, normalised by that band's own width;
zero anywhere inside. Normalisation is load-bearing: clustering spans 3.49 and alignment
spans 0.06, so a raw sum would weight clustering 58× for no physical reason.

**band margin** — how far a genome sits from the nearest band edge. 1.0 = dead centre of
every band, 0.0 = on an edge. **Why it exists:** the first trained winner satisfied every
constraint with `verticality 0.476` against a `0.476` ceiling — inside by zero, with
nowhere to vary. Adding margin as a maximize raised child survival from **38% → 81%**.
Margin is physics, not taste: *a genome with room on all sides has children that are still
real material.*

**form** — the named arrangement an emitter uses. `tuft`/`clump`/`shard` are hand-written
guesses; **`measured`** is the trained one and is now the default.
→ `core/progeny.py :: build_child(form=)`

---

## 3. GENETICS — used literally, not as metaphor

**genotype** — the stored distribution. **phenotype** — the expressed splat cloud. The
distinction is load-bearing: the DSL *is* the genotype, physics is the decompressor.

**heritability** *(h²)* — `V_between / (V_between + V_within)`: the fraction of variation
that **breeds true**. **Undefined from a single specimen**, which is why two scans of a kind
are the minimum useful sample. → `core/progeny.py :: heritability()`

**linkage group** — traits inherited as a block. `colour` = (R,G,B), `form` = (size, aniso),
`body` = (opacity).

**pleiotropy** — one underlying factor driving several traits. R/G/B are driven largely by
luminance. **Why it matters:** sampling R, G and B independently produced *rainbow confetti*
children; sharing a luminance factor fixed it.

**recombination** — a child draws each linkage group from one of two parents (**independent
assortment**), so siblings differ in whole blocks rather than in noise.
→ `core/progeny.py :: recombine()`

**mutation** — a separate, low-rate perturbation. **Not** the same thing as parental
variance; conflating the two is why one-parent sampling looked like noise.

**liability scale** — modelling a bounded trait on an unbounded scale and transforming back
(**logit** for proportions, **log** for positives). **Why:** a Gaussian drawn directly on a
[0,1] trait with mean 0.95 piles probability on the boundary — children came out saturated
white and sizes drew negative. The inverse transform cannot leave the domain, so no clamping
is ever needed. Fixed 0/10 saturated after.

**plasticity** — one genotype expressed differently by environment. That is the **verb** and
the **membrane**. Not inherited.

**progeny / children** — variations of one isolated object, sampled from its measured
ranges. The operator's correction: you do not paint a material onto a surface (that is
texturing) — you isolate ONE object, generate variations, and **place instances**.

---

## 4. THE MEMBRANE — the primitive

**membrane** — a boundary, and therefore **a scale**. The project's core primitive. It
supplies six things at once: a local frame, a local unit, an identity, an inside/outside
test, a level of detail, and a set of **ports**. Nested membranes *are* the hierarchy.
→ `core/membranes.py`

**why it is the primitive** — a boundary is what makes a cause **attributable**. In biology
the vesicle is what lets a replicator keep what it makes (no inside/outside → no individual
→ nothing for selection to act on). In engineering the same boundary is what lets you
attribute an outcome to a change rather than to the world.

**skin** — the thickness of "on the boundary", in metres (default 1 mm). **Why absolute:**
a relative tolerance of `1e-6 × scale` on a planet-radius membrane made "on the surface"
mean ±6.4 m, so `side()` returned `'on'` for everything.

**port / stud** — a typed interface on a membrane, typed by **what flows** through it:
`structural`, `gravitational`, `energy`, `fluid`, `atmospheric`, `substrate`. Not a
category — a physical claim.

**mate** — attach a brick to a port. After mating the port is no longer open, and the child
records `attached_via`. **Why recorded rather than inferred:** `open_ports()` used to infer
occupancy from geometry and reported "filled 0" with six bricks attached.

**the six directions** — the ports of a cell (±X, ±Y, ±Z). Used as a **development-focus
mechanism**: pick one direction and build it out. Distance travelled is not a consideration;
the mechanism must transcend scales.

**work queue** — the list of unfilled studs. *Where the world is unfinished*, enumerated.
→ `core/membranes.py :: work_queue()`

**saturated** — a membrane with no open ports. Its state becomes `MIGRATE`.

**time as the outermost membrane** — the fourth dimension is a membrane like any other: the
past inside, the future outside, the present its surface. A game with a beginning and an end
is a set of states between 0 and 1.

**cell** — the human-scale unit, **1.83 m (6 ft)**. Earth's surface is 1.52e14 cells.

**section** — a 128 m tile, addressed by position (`S+00384+00896`). Sections never have to
agree with their neighbours about anything, because content is **deterministic by
coordinate**. → `core/sections.py`

**deterministic by coordinate** — content derives from a pure function of position
(`tile_seed(ix,iy)`, `world_height(x,y)`), so the same seed gives the same world forever and
seams match without negotiation. Measured seam continuity: **5.8e-10**.

---

## 5. VERBS AND STATES

**verb** — a range between two states of a noun. To make a verb you need a noun that has two
states and a **dial** between them. THRUST, BALANCE, GROW, CONNECT, SCAN, NAVIGATE_ORBIT.

**two ends and a dial** — the single mechanism underneath verbs, morphs, heritability, LOD,
growth and the story. `Anchor` / `Axis` / `Dial`. → `Construction/scene.py`

**gate** — a dial held until a **measured** condition holds. How game progression is
expressed without scripting it. *(Distinct from the verification gates in §7 — same word,
different layer.)*

---

## 6. TRAINING — how features get built

**train, don't hand-tune** — if a feature is **DATA** (prices, damage, yields, morphology,
layouts), do not tune it by reasoning. An LLM manages ~20 edits/hour; `core/trainer.py` does
~30,000 evals/sec. Six orders of magnitude.

**domain** — `core/trainables/<f>.py`, providing `seed` / `mutate` / `measure`. Reports
**FACTS only, never opinions**. → e.g. `core/trainables/arrangement.py`

**objective** — `docs/objectives/<f>.json`, saying which facts are GOOD. Written by the LLM.
Must contain at least one **maximize** term or you get a **satisficer**.

**the LLM sits at the top and the bottom, never the middle** — it writes the constraints and
reads the walls; it never turns the crank.

**measure** — the domain's report. A fact, not a judgement. `measure(genome) -> dict`.

**pinned** — the walls the winner is **riding**. The trainer names them. A pinned constraint
is where the next exploit lives.

**the exploit is the product** — a degenerate winner is not a failure. It is the optimiser
auditing your spec at 35 kHz and finding the hole you would have defended in review.

**iterate the objective, never the artifact** — when the winner is wrong, the *spec* is
wrong. Worked example in this repo: round 1 of `arrangement` scored 0.9680 and landed inside
all four bands — and was unusable, because nothing had asked for **band margin**.

**satisficer** — an optimiser with no maximize term. It stops as soon as the constraints are
met, which is almost never where you want it.

**robustness** — `worst / mean` across N randomised restarts. A real limit cycle is ~1.0; a
fraud is ~0. **One rollout from one initial condition is not a measurement — it is a coin
toss.** Proven: a celebrated 13.52-body-length walker had `periodicity 0.25` and lost 5.5
body lengths to a **one-micron** nudge; under honest physics it scored *worse than an
untrained brain* after 80,000 evaluations of selecting lucky dice.

**reachability probe** — checking what the domain can actually reach *before* setting a hard
gate. **A gate you cannot reach is not strict, it is blind:** score-zero everywhere means no
gradient, and the trainer degenerates into a random walk while appearing to run at full
speed. Measured case: 0/140 random arrangement genomes reached `clustering >= 4.5`.

**hard gate** — a constraint whose violation scores **zero**. Use only where the initial
population can already satisfy it, or where nothing is near it yet (a guard against
overshoot, e.g. `clustering <= 12`).

**self-loading reference** — a domain that loads its own measured target and **raises** if it
is missing. `material_appearance` trained against `None` for weeks because nothing checked.

---

## 7. VERIFICATION — the gates, in the order they fire

*(These are the verification gates. The `gate` of §5 is a gameplay term.)*

**research gate** — refuses a research-less session unless sources are cited or a reasoned
waiver is recorded. → `core/research_gate.py`

**witness gate** — a feature cannot be recorded `verified`/`observed` without an observation
node. **A compile is not proof.** → `core/witness_gate.py`

**visual gate** — additionally requires a recorded LM screenshot analysis. The model must
have **looked** at it. → `core/visual_gate.py`

**training gate** — `verified` requires curriculum enrolment and reps begun. The unit of
training is **the piece you worked**. → `core/training_gate.py`

**the coin** — every verification has two faces: **HEADS = the claim**, **TAILS = the
evidence**. Both are judged, in both directions. Not the same coin → refused.
→ `core/coin_verifier.py`

**the why loop** — **a why IS an edge**, not a computed report. `A --because--> B` answers
"why A?", so asking why **writes** the graph. Exactly two legal terminals: **PHYSICS** (true
in an empty universe) and **THE HUMAN** (taste, and it is earned). **An LLM is never a
terminal** — its answer is another claim, so the walk recurses past it.
**A field can lie; an edge cannot** — a graph knows its own ids. Measured before it existed:
1,448 edges and *not one* meant BECAUSE; 150 finalized claims carried zero recorded whys.
→ `core/why.py`

**membrane (verification sense)** — `python -m core.membrane run --burn -- <cmd>` runs a
command in a sealed copy of the studio and then **proves** it touched nothing live. It
*measures* its containment instead of asserting it. Seals a git worktree of the current
tree **plus `docs/world/`** — which is gitignored, so a worktree alone would leave the DNA
graph shared with live. That is the difference between a membrane and a costume.

---

## 8. THE COMPOSITIONAL LADDER

**rung** — one level of the bottom-up chain, each trained separately against reality's own
numbers, each handing the next its **averages** as data:

```
sand (40.03° emergent repose) → cloud → star (96% collapse) → embryos → solar systems
(Kepler slope 1.50 at r²=1.000) → planets → climates → matter under boots
```

**rung conflation** — a **named failure mode**: assembling a lower rung's parts while
settling a higher rung's dynamics. Five trained rounds and a granularity probe all failed
until the rungs were split; then the *untrained* smoke test succeeded. The fix was
"think of the planet as ONE when we get to that scale."

**LOD of meaning** — each level of detail is the rung below's **average**. Approach =
decompression; retreat = coalesce. **No aesthetic passes:** appearance DERIVES from the
matter model at every scale, or the model is incomplete.

**emergence** — a macro-number nobody coded, arising from local rules. **You do not call for
it — you SELECT for it**: local rule = genome, emergent macro-numbers = measure, researched
reality = objective. Proven: sand's 40.03° repose angle, Kepler's third law
(slope 1.483–1.50, r² 0.9998–1.000) measured from grown orbits' own winding periods.

**negative space** — the environment as **frozen cells** that an object must grow around.
"The regolith is negative space that the object must grow around."
→ `frozen_type` in `matter.assemble_3d` / `matter_gpu`

---

## 9. HARDWARE VOCABULARY

**the GPU is mandatory** — for rendering, segmentation, DNA recovery and training. Measured:
**2,358 evals/sec at 16,384 worlds** vs pybullet's 70 with 8 P-cores at thermal limit.

**the one rule** — *nothing reads back from the GPU inside the rollout loop.* A previous
attempt did 1,575 CPU↔GPU syncs per batch and ran **300× slower than the CPU**.

**membrane vs Faraday cage** — the membrane does not isolate the network. It is a cell wall.

---

## 10. RULIOLOGY — borrowed vocabulary, and what it corrected here

*(From Wolfram, "Games between Programs: The Ruliology of Competition", 2026-06-04. Adopted
2026-07-23 because three of these named something this studio was already doing without a
word for it, and two of them corrected a mistake.)*

**ruliology** — systematically enumerating **all possible** simple programs of a type and
observing what they do, instead of studying the ones somebody happened to write. The method
this project already uses on genomes; now it has a name.

**the Axelrod error** — drawing conclusions from the programs people happened to submit.
Wolfram's example: the famous 1980 prisoner's-dilemma tournament crowned **tit-for-tat**,
but enumerating all 22 distinct 2-state machines ranks it **far down** — the real winner is
"grim trigger", which nobody submitted. **Our instance of the same error:** `tuft`, `clump`
and `shard` were three arrangements a person authored, and measurement showed them landing
inside **zero** of reality's four bands. Hand-authored vocabularies are not samples of the
possible; they are samples of what somebody thought of.

**computational irreducibility** — there is no shortcut: to know how something turns out you
have to run it. Wolfram's conclusion about competition, and this studio's reason for the
trainer — an LLM cannot reason its way to an answer at ~20 edits/hour that 30,000 evals/sec
finds by running.

**pocket of computational reducibility** — a region where behaviour *is* predictable, which
is where systematic winners come from. **The sharper statement of what "trainable" means:**
this project's DATA-vs-CODE split is a crude proxy for "does this feature have a pocket of
reducibility?" A feature is trainable when a measurable objective has a searchable gradient
into one.

**capacity** — how much a program can express. Wolfram measured it: 2-state machines top out
at 0.151 against each other, 3-state machines reach 0.593 against 2-state ones, and a
10-state machine wins against **every** 2-state machine by holding a specialised sub-machine
for each. **Measured here, and it did NOT transfer cleanly** — see the two entries below.

**capacity is not monotone under sampling** — Wolfram got monotone gains by *exhaustively
enumerating*; we sample. Adding dimensions to a sampled space dilutes it faster than it opens
it. Measured on `arrangement`: lowering one gene's floor raised reachable clustering
**4.736 → 6.588**, but adding two more capacity dimensions *lowered* it to 4.780 and 5.312.
**Consequence for method:** a reachability probe by random sampling measures the PRIOR, not
the reachable. The honest test of a capacity increase is to **train inside it**.

**a pinned gene is not a binding constraint** — recorded because this studio asserted the
opposite and was wrong. `cluster_tight` sat exactly on its 0.02 floor, which was read as
"the vocabulary runs out". Widening the floor to 0.005 and retraining moved the
score from **0.8238 to 0.8240** — nothing. The gene drifted off the floor to 0.0313 and clustering
turned out to have the *largest* margin of any fact (0.722). The real limiter was
`verticality` (margin 0.196, band width 0.176) and `alignment` (0.204, width 0.061) —
narrow because they came from 5 regions of ONE scan. **The lever was more scans, not more
capacity.** `pinned()` reports where a winner rests, which is not the same as where it is
held back.

---

## MAINTAINING THIS FILE

Add a term when it becomes **load-bearing** — when getting it wrong would produce wrong
code, not merely unfamiliar prose. Give the number wherever one exists. If a term's
definition changes because a measurement changed, update the number *and* say what it was,
the same way `docs/EXPERIMENTAL_METHOD.md` §7 requires recording what failed.

Regenerate the machine-readable mirror after editing:

```
python -m core.terms --rebuild
```
