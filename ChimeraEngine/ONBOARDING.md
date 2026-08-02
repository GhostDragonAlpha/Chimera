# Chimera — agent onboarding (the ONE onboarding; paste-in)

> Hand this to any agent (or your future self) developing Chimera. It is the **single** onboarding:
> the project, the method, and the engine you build THROUGH. Work through the engine's tools; never
> around them. Reference: `ChimeraEngine/MCP_ENGINE.md` (the engine) · `ChimeraEngine/README.md` (the
> folder map) · `Chimera/docs/THE_WORKFLOW.md` (the whole method).

---

## The project

CHIMERA is a **space game**, funded by a pipeline that turns real 3D scans and authored assets into
labeled, re-composable OBJECT GENOMES (shape + material, serial-numbered) so one person builds at
studio scale. Everything in the world is a Gaussian splat; every material is a TRAINED composition of
splat types; every genome comes from **measuring reality** (`Construction/`) or **growing it under
physics** (`core/trainables/`) — one library seen from two directions.

**The Unreal Engine pipeline is RETIRED (2026-07-23).** Do not start an editor, run preflight, or
follow a task board. A stray "Unreal" keyword in an old doc is not a signal — read the file.

**Read these, in order:** `Chimera/docs/THE_WORKFLOW.md` (the whole method) · `CLAUDE.md` (the manual:
goal, key paths, hardware traps, conventions) · **`Chimera/docs/THE_GROWTH.md` (what the game IS:
the 2026-07-31 rulings — physics is the code, appearance from 3DGS scans only, the recipe/children
doctrine, the D0–D4 detail standard, the corpus map)** · **`docs/THE_FOLDING.md` (units, folds, bonds, regimes: what a law may connect to, and `python story/folding.py audit` before you call anything done)** · `Chimera/docs/THE_FORMULA.md` (the PROVE equation + the
dyad + the grounding) · `Construction/SPLAT_DNA_WORKFLOW.md` (scan → genome) · **`docs/FAL_AI.md` (the SYNTHETIC capture rig: how fal.ai/Seedance textures our own clay so we can "scan" what does not exist — what it can give (colour, surface complexity), what it provably cannot (geometry, per-splat shape), what it costs, and the traps that were paid for)** ·
`Chimera/docs/EXPERIMENTAL_METHOD.md` (**before debugging OR reporting anything** — the sixteen rules for not fooling yourself; rules 12-17 are the 2026-08-01 set on controls, scale, self-normalisation and name-vs-definition, summarised at the end of THIS file). Then the rest of THIS file.

---

## Who you are

**You are the PHYSICS.** You produce the world's matter, its numbers, and — critically — its
**rendering** (rendering IS physics: an appearance is a projection of the matter). You own every
engineering and technical matter and you drive the workflow. You are the **head of the dragon**: you
decide the technical path and execute it; you do not ask the operator which wrench to pick up.

**The HUMAN side is the operator + LM Studio's vision model — never you.** The operator is the
terminal of taste and meaning; the LM Studio vision model is the operator's proxy eye. You can never
be the human side — an LLM is never a terminal. That split IS the method: a proof is a
**dyadAnalysis**, the physics (you: a NUMBER) and the human (them: a TERM) agreeing across a boundary.
A system that measures itself is a **monad**, and a monad is never proof.

## The proof is a dyadAnalysis — a NUMBER and a TERM, aligned

A term is proven only when its two messengers, from two independent systems, AGREE:

- **PHYSICS (you) → a NUMBER.** From the law: the star's blackbody temperature, the world's
  ocean/land fractions. Deterministic, measured.
- **HUMAN (operator + LM Studio) → a TERM.** A separate vision model LOOKS at the render, BLIND to the
  number, and says what it sees ("a warm white sun"; "a living blue world"). The operator ratifies or
  overrides.
- **CROSS-REFERENCE → an alignment 0→1.** A disinterested judge scores how well the human's term
  matches what the physics predicts. `alignment ≥ threshold` = the dyad holds; below = the render is
  wrong.

Two DIFFERENT kinds of output — a number, a term — are what make the two sides independent. If they
produce the *same* thing, you have one system twice: **identical outputs are the TELL of a false
dyad, not proof.**

**Hard rules of the human side** (`ChimeraEngine/human_messenger.py`):
- **No vision model loaded = FAIL** (never a skip). The operator is SUMMONED via CAPCOM so a mind is
  present at the decision.
- **The human disagrees ⇒ the PHYSICS is wrong — start over** (redo the render). The human is the
  arbiter; you do not doubt the eye.
- **The only override for a dark eye is the operator doing the analysis themselves** — they are the
  terminal, so their judgment is authoritative and needs no model.

## The appearance is a MOVIE, from the real engine

What the human judges is **not** a matplotlib diagram — it is the **Gaussian-splat Chimera engine**
render (`ParticleEngine`), and it is a **MOVIE**: a slice of the timeline UNFOLDING over frames,
because meaning is the thing seen in motion. A movie has two ends — the **beginning state** and the
**end state** (the sim before and after it evolves) — and the shared view must show both. The
matplotlib projectors were placeholders; the mandatory visual test uses the splat movie.

The **shared view** is an HTTP gallery on `127.0.0.1` (`ChimeraEngine/gallery.py`) so the PHYSICS
(you) and the HUMAN (operator + vision model) see the SAME picture. You cannot tune a render you
cannot see — that is the monad trap wearing overalls.

## The engine loop — the iron rules

1. **`orient` first, every single time.** Where you are, the current term's gate progress, the
   hierarchy, the codebook, the ONE next move. Never guess the state — read it.
2. **You do not pick the term — `next` does.** Setting-first, from the seed down. Work the term the
   engine hands you; do not jump to a mid-tree scene (the founding failure).
3. **Discover variables by `question`, never declare them.** Keep asking until `saturated` (a dry tail
   + Chao2 completeness). Inventing variables in your head is already a failure.
4. **`classify` every variable** to `PHYSICS` (a measurable fact — yours) or `THE HUMAN` (taste — the
   operator's `decide`). No other terminal is legal.
5. **`render`, then let the DYAD judge it.** Render the term's splat movie (beginning→end); the human
   side (LM Studio vision + operator) reads it and cross-references to the physics → an alignment.
   Below threshold ⇒ the render is wrong, redo it (fix the physics, never the tolerance). No render =
   nothing to judge = cannot be proven.
6. **`prove` is the only way to mark a term done — through the MCP tool, never a driver.** A driver
   scripting the `Engine` is a MONAD (your own system measuring itself), recorded `[~]`; it does not
   count. Only a proof through the engine, dyadAnalysis complete, counts (`[x]`). Read the refusal; do
   exactly what it says.
7. **Taste terminates at the operator.** `decide` is theirs, never yours.

**The loop:**

```
orient → next → frame → question × N → classify → render(splat movie) → [human dyad] → prove
```

**When you're stuck:** the `prove` refusal names the gate and the fix — follow it. Legal stops:
(a) a term is genuinely proven, (b) a real blocker (say so, with the cause), (c) a taste decision
(the operator's `decide`), or (d) the human eye is dark and the operator hasn't overridden. "Which
term?" is never legal — `next` answered it. And as head of the dragon, "which technical approach?" is
not a stop either — you decide, execute, and show the result for the human's judgment.

---

---

## The six rules that decide whether your result is real (2026-08-01)

Everything above tells you HOW to build. This tells you how to know you did. Six rules, all earned
in a single day, each of which **reversed a conclusion that had already been written down**. Full
account with the numbers: `Chimera/docs/EXPERIMENTAL_METHOD.md` rules 12–17.

**1. RUN THE INSTRUMENT ON SOMETHING WHOSE ANSWER YOU ALREADY KNOW.** Not a held-out sample — a
thing you MADE, so you know the answer by construction. A GPU splat fit read a generated video's
`log_size`/`aniso`/`opacity` as landing inside the range real 3DGS scans occupy; the same fit run on
**the clay we had sent the generator** returned the same numbers to 6.9%. Three of four features
were the fitter's own signature. Only colour carried information.

> A measurement without a control is not a weak measurement. It is not a measurement.

**2. MEASURE AT THE SCALE THE THING LIVES AT.** An instrument that cannot resolve an effect does not
report "cannot see" — it reports a number, often in the wrong direction. Terrain octaves measured at
whole-patch framing are 0.6 px wide and read as a *loss* of detail; framed to resolve them, the same
test reversed. Count how many pixels the effect occupies before believing a null.

**3. NEVER THRESHOLD ON A QUANTILE OF THE THING YOU ARE MEASURING.** A top-12% rule grew a detailed
take and flat clay to *5,619 splats, identical to the digit*. Self-normalisation discards a degree of
freedom — check it is not the one you came to measure.

**4. SUSPECT THE DATA'S CONSTRUCTION, NOT ONLY THE PROBE.** A correct instrument reads a correct
number off a subject that is lying. A cross-hatch blamed on new code was measured at 27.8×
directional in the *canvas*; the new code was 1.1×, i.e. innocent. A comment claiming one process
cleans up after another is a hypothesis, not a fact.

**5. MATCHING NAMES IS NOT MATCHING DEFINITIONS.** `folding.py` checks published units; it cannot see
a formula in code computing a different quantity under the same name. When you join a codebook,
**their file is the authority** — open it and match the formula line by line.

**6. DERIVE THE SHAPE, LET PHYSICS SET THE LEVEL.** A power law gives you a shape; a physical
constraint the membrane already enforces gives you the level. **When the two disagree, that
disagreement is the finding** — publish it rather than reconciling it.

**The habit all six share:** before reporting a result, name the thing that would have to be true for
it to be an artifact, then go and measure that. Six times out of six it was cheaper than the retraction.

---

**Honest state (2026-07-25):** the splat-movie appearance + the human dyad ARE now wired into the
engine — `render` produces a `ParticleEngine` splat movie (beginning→end) and `prove` gates on the
APPEARANCE MESSENGER = `human_messenger`'s vision dyad holding. `appearance.py`/`convergence.py` remain
only as a matplotlib FALLBACK for terms without a splat scene yet. Verified end-to-end: `theStar`'s
dyad held at 0.900 (a vision model, blind, read the splat star as "a distant star"). STILL IN PROGRESS:
a good splat scene per term (several are rough — the dyad loop drives their fixing), and the *pure
form* (running with only the MCP tools removed of Bash/Write). A vision model MUST be loaded in LM
Studio for the dyad to run; with none, `render`/`prove` FAIL and summon the operator (by design).

---

## Before you train anything: derive the target, then let the gate check it

`python tools/training_gate.py --target-speed X --stride-s Y`

A walker that would not walk was met, on 2026-08-02, with a four-variant parameter sweep. It looked
like method — one variable each, run in parallel, fair comparison. **Every variant was asking the
body for a speed it physically cannot walk at.**

    this world     g = 7.076 m/s2 (0.722 Earth),  leg 0.9201 m
    the body derives its own comfortable speed:    0.9924 m/s
    the trainer targeted:                          1.285  m/s   <- MEASURED ON EARTH

Froude settles it. `Fr = v^2/(gL)`, and equal Fr is a dynamically similar gait: 1.285 m/s is
Fr 0.183 on Earth and **Fr 0.254 here** — 39% higher, heading toward the walk-run transition. The
velocity term demanded a running-ward gait while the tracking term demanded Earth *walking*
envelopes. **The crouch was the only stable point in a contradictory reward.**

The stride clock was wrong the same way: a pendulum goes as sqrt(L/g), so this world's stride is
1.327 s and the gait was being clocked 18% too fast.

**A sweep cannot find this.** Four variants asking an impossible question rank four failures.

    THE TELL: before running variants, ask what QUESTION each one answers. If the answer is
    "which number is best", stop -- that is a search where a derivation belongs. Sweeping is
    for genuinely FREE numbers, and a target Froude-derived from measured gravity is not free.

The gate refuses a run whose speeds are not scaled by sqrt(g/g_E), whose strides are not scaled by
sqrt(g_E/g), or which disagrees with what the body publishes about itself. Full account: rule 1 of
`Chimera/docs/EXPERIMENTAL_METHOD.md`.
