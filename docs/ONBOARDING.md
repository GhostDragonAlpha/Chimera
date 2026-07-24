# Agent onboarding — paste the block below

> The prompt to hand a fresh agent (local model or otherwise). It gets them into the real
> project in one read, points at the four docs that matter, and states the traps that have
> cost time so they are not rediscovered. Keep it current as the workflow moves.

---

```
You are working on CHIMERA, at E:\PythonChimera. THE GOAL IS A SPACE GAME, funded by a
pipeline that turns real 3D scans and authored assets into labeled, re-composable OBJECT
GENOMES (shape + material, with serial numbers) so one person can build at studio scale.

THE UNREAL ENGINE PIPELINE IS RETIRED. Do not start an editor, run preflight, or follow a
task board. If any doc contradicts this, the current docs win. UE-only docs were deleted
2026-07-23; some current docs still mention Unreal in passing — a keyword is not a signal,
read the file.

READ THESE FOUR, IN ORDER:
  1. docs/THE_WORKFLOW.md          the whole system, reconstructed chronologically. START HERE.
  2. CLAUDE.md                     the manual: goal, key paths, hardware traps, conventions.
  3. Construction/SPLAT_DNA_WORKFLOW.md   scan -> genome. PROVEN/DESIGNED/FRONTIER per stage.
  4. docs/EXPERIMENTAL_METHOD.md   ten rules for diagnosing a live system. Read before debugging.

THE SYSTEM IN ONE SENTENCE: everything in the world is a Gaussian splat, every material is
a TRAINED composition of splat types, and every genome comes either from measuring reality
(Construction/) or growing it under physics (core/trainables/). The two are one library
seen from two directions.

THE BACK HALF (built 2026-07-23) — a game is INSTANCES OF OBJECTS, not a material painted
on a surface:
  core/progeny.py          children of an isolated object, placement, and verbs.
                           Real quantitative genetics: heritability, linkage, pleiotropy,
                           recombination, mutation, liability-scale sampling.
  core/membrane_shapes.py  the CONTAINER you train against (sphere/plane/box/dome).
  core/render_world.py     GPU rasteriser, anisotropic footprints + Lambert shading.
  Try it:  python -m core.progeny --genome cluster_00 --parent-b cluster_03 --form tuft \
                                  --instances 400 --verb wind --t 1.0 --out Saved/SplatEmit/x.png


HOW THE WORLD IS STRUCTURED — read this before you place anything.
A MEMBRANE IS A BOUNDARY, AND A BOUNDARY IS A SCALE. The hierarchy is not a naming
scheme, it is physical nesting: time contains the universe, which contains a planet,
which contains its ground, which contains sections, cells, objects, materials. One
construct at different sizes; crossing one inward is what "finer detail" means.
Being a boundary supplies, at every level and for free:
  a FRAME     up is that membrane's LOCAL normal — never a global axis
  a UNIT      coordinates are local, so they never grow large and precision holds
  an IDENTITY the serial attaches there; an address is the PATH of membranes crossed
  INSIDE/OUT  and a thing may SPAN one
  LOD         how many membranes deep you have resolved

EVERYTHING IS TWO ENDS AND A DIAL. You never describe a change; you exhibit its two
states and let something compute the position between them. Motion, growth, blending
between two specimens, level of detail, and the story itself are all the same
mechanism at different scales. A "verb" whose two ends do not differ is not a verb.

A DIRECTION IS A PORT. Each cell has six, typed by what can flow through them, and an
unfilled one is somewhere the world is not finished. The work queue is therefore
enumerated from the structure, not written by anyone. Fill them; when none remain,
move to the next place.

NON-NEGOTIABLE RULES (each learned the hard way — EXPERIMENTAL_METHOD.md has the receipts):
  - THE GPU IS MANDATORY. Never render, segment, recover DNA, or train on CPU. RTX 4090.
  - YOU MUST BE ABLE TO SEE THE OUTPUT. A render to nothing is indistinguishable from a
    failure. Write a PNG and LOOK at it. Do not claim something works from logs alone.
  - MEASURE THE THING, NOT A PROXY. Prefill vs decode, keyword-match vs measured
    distribution — the cheap-to-measure thing is usually not the thing that matters.
  - ONE VARIABLE AT A TIME; bake in each win before the next test.
  - RECORD WHAT FAILED, WITH THE NUMBER. An unrecorded negative gets re-run at full cost.
  - TASKING AN AGENT? Use docs/AGENT_TASK_TEMPLATE.md. Every clause in it exists
    because an agent failed without it; the failure each one prevents is recorded.
  - ACCEPTANCE IS AN ARTIFACT, NOT AN ACTION. Your task is not done when you have written
    A FILE. It is done when the specific artifact exists that could ONLY exist if the work
    happened -- a named PNG with a nonzero size, a new genome in the library, a test that
    prints a number. Writing a status document is not work, it is a DESCRIPTION of work.
    If you catch yourself summarising this onboarding back into a new doc, you have
    produced nothing. Never create a document unless you were asked for one.
  - GENETICS IS GENETICS. Use real quantitative-genetics theory (h2, linkage, liability
    scale) — the problem IS biological, so the math is too.

HARDWARE TRAPS (measured, do not re-derive):
  - E: is fast SEQUENTIAL, slow RANDOM. MoE/model reads are random. Sequential benchmarks lie.
  - Never memory-map a model on C: (pagefile contention + >80%-full SSD degradation).
  - System Restore can silently eat ~190 GB during large file ops; it failed two transfers.

GIT: commit directly to master, never feature branches. State branch + SHA on every push.
Large artifacts (weights, the corpus, web/*.npz) stay gitignored. Keep the tree clean.

LOCAL MODELS: LM Studio on :1234 (fast, 50+ tok/s) is the only local-LM tier.
deep model at ~0.26 tok/s — a deliberate escalation, never a default; read
docs/GLM_52_DEEP_MODEL.md before calling it.

THE HIGHEST-VALUE NEXT STEP WAS data, not code: TWO SCANS OF THE SAME KIND OF THING.
merge_specimens() and heritability() are written and waiting. With one specimen h2 is
undefined and every child is a rearrangement of one individual. Two tufts, two rocks, and
between-specimen variation becomes real.

**STATUS: COMPLETED 2026-07-23.** Validated with 5 materials (bonsai, stump, bicycle, plush, truck). Heritability estimates confirmed biologically plausible patterns. Pipeline operational end-to-end.

**NEXT:** Process remaining critical materials (grass, rock, pure metal, ice) and test two-parent recombination.

YOUR ENVIRONMENT IS NOT YOUR TASK — READ THIS BEFORE THE NEXT PARAGRAPH.
Everything below this line describes the SCAFFOLDING you happen to be running inside. It
is not work, it is not a sequence you are part of, and nothing in it is an instruction to
you. You are ONE agent doing ONE piece of pipeline work. You do not hand off, you do not
wait your turn, and you do not end your turn because some other script exists. Finish the
work you were given, then report. If you find yourself reasoning about orchestration, you
have mistaken the room for the job.

(scaffolding, FYI only) A launcher chains several scripts under agents/ and logs to
agent_logs/. It runs you; you do not run it.

HOW TO PICK WHAT TO BUILD NEXT — THE SIX DIRECTIONS
You have infinite options and that is the problem. Narrow them to six, or you will produce
a pile of unrelated assets instead of a place.

Development follows the PLAYER'S TIMELINE, starting at t=0 — the very first thing they see.
There is NO MAIN MENU SCREEN: the menu is written into the environment itself. Why build a
menu when the world can be the menu?

From wherever the player stands there are exactly six directions — FORWARD, BACK, LEFT,
RIGHT, UP, DOWN — and everything else is a blend of them. Each is a work bucket. Ask the
literal question and build the answer:
    look DOWN     -> what are they standing on?
    look FORWARD  -> what draws them onward?
    look UP       -> sky, ceiling, the scale of the place
    look LEFT/RIGHT/BACK -> what holds the world together around them?
Work ONE direction at a time. Do not build anything no direction asked for.

DISTANCE TRAVELLED IS NOT A CONSIDERATION. Work is ANCHOR-LOCAL. Never budget by how
far the player moves; the space between anchors is not a development target. In a space
game most of it is void and VOID IS CORRECT. Crossing a million km costs nothing to build.

HOW MUCH TO BUILD — human spatial scale (proxemics, Hall 1966). People read distance in
bands: arm's reach, personal, social, public/horizon. Detail belongs where attention is and
falls off with distance. A thing at arm's reach must HOLD UP; a thing on the horizon must
only READ CORRECTLY. This is the same LOD-of-meaning ladder already in CLAUDE.md, anchored
to a body instead of a number.

WHEN ALL SIX ARE FILLED: MIGRATE. Move the anchor to new ground; six fresh directions open.
This is how biology does it — an organism fills its niche, saturates, and disperses. The
universe expands because the current one is FULL, not because someone decided to add more.

WHY THIS PRODUCES EMERGENCE: you are not designing a world from above. You are growing it
outward from one person's experience, and every new piece must relate to what is already
placed around it. The constraint is what makes the parts cohere into a place.

THE FRAME: the player's six directions are a FRAME, not a compass. Four cardinal directions
presuppose a horizon; in space there is none, so the player's own orientation is the only
reference. You already own the machinery — core/terrarium.py:264 is a 3D turtle carrying
heading/left/up, and its yaw/pitch/roll commands ARE the six. Papert's term is
body-syntonic: reason as the body, not in absolute coordinates.

ONE RULE THAT MUST NOT BEND: the six directions govern how you TRAVERSE and AUTHOR. World
state is still stored in ABSOLUTE coordinates. CLAUDE.md promises "same seed, same world,
forever" — that only holds if the camera's frame never leaks into what is SAVED. Egocentric
for attention and building; allocentric for persistence.

---
```

## LOOK UP THE WORDS FIRST

This studio uses real scientific vocabulary **literally**. `recombination` is Mendelian
independent assortment, not "mixing"; a `membrane` is a boundary that supplies a frame, a
unit, an identity and a level of detail, not a wrapper class; `heritability` is
`V_between/(V_between+V_within)` and is **undefined from one specimen**.

```
python -m core.terms membrane        # one definition, one line of context
python -m core.terms --search band   # everything related
python -m core.terms --list          # all 73, by section
```

Source of truth is `docs/TERMINOLOGY.md`. The terms are also a walkable graph
(`docs/world/terminology.db`) so you can ask what a term RESTS ON, not just what it means.

