# The Construction Layer

> 2D authoring · deterministic 3D · **direct** control · difference-as-dimension
>
> Status: DESIGN + walking-skeleton demo (a tree in the wind). 2026-07-22.
> Home: `E:\PythonChimera\Construction\` — a pure-Python integrating layer over
> `WorldModel/` (generators, VAE) and `ParticleEngine/` (GPU splat renderer).
> This is **not** part of the Unreal manual; it has no UE dependency.

---

## 0. The one sentence

The AI authors in a **legible low dimension**; a **deterministic construction
program** lifts that to 3D with **direct** (not emergent) control; the
**difference between two anchor states IS a controllable dimension**, and the
**fill** between them is a walk along a bounded manifold.

## 1. Why this exists (the problem it solves)

Three commitments, each a verbatim design constraint from the operator:

- **"You can't have control [over] the emergent. It has to be direct."**
  A simulation left to find its own attractor is not steerable per-frame. The
  granular sandpile and the N-body accretion *select for* emergence — that is
  their job, and it is a different job. The construction layer **places**. It is
  an algorithm keyed on game state, whose output is a pure function of its input.

- **"If we don't have to think about [the] third [dimension] then the AI can
  focus on its own third dimension, which is what I want."**
  The AI's native plane is *meaning*, not geometry. Author in 2D (a plane the
  model reads and edits fluently); spend the model's capacity on intelligence,
  and let a deterministic program own the lift to 3D.

- **Construction, not extraction.** We are *not* reconstructing 3D from
  photographs (photogrammetry / NeRF / Gaussian-splat *fitting*). Those go
  `pixels → guess the geometry that produced them`. We go the other way:
  `2D spec → known design principle → exact geometry`. The 2D is a **spec we
  wrote**, not an observation we are inverting. That is why the lift can be
  deterministic and the control direct.

## 2. The three actors (never conflated)

| Actor | Owns | In this system |
|---|---|---|
| **The human** | the *references* and the *taste* | authors the anchor states; picks among valid fills |
| **The AI** | *targeting* and *filling* | measures distance to an anchor; walks the manifold between anchors |
| **The machine** | the *lift* and the *gate* | constructs 3D deterministically; gates validity with physics |

The AI sits at the **top** (choose/target) and the **bottom** (fill/measure),
never in the middle turning the crank — the same split as the trainer.

## 3. The core mechanism: difference = dimension

This is the keystone. It is worth stating precisely because everything else is a
consequence of it.

- Two **anchors** that differ define an **axis**. The *difference vector between
  them* is a coordinate. You do not describe the axis; you exhibit its two ends.
- A **dial** is a scalar `t` (canonically `[0,1]`, extrapolation allowed) that
  walks the axis.
- **Fill** = interpolation between the anchors, in two flavors:
  - **direct-parameter lerp** — when the parameter space is already convex-valid
    (every blend of two valid points is valid). This is what the tree demo uses.
  - **manifold traversal** — when a straight lerp would leave the valid set, walk
    the **VAE latent** (`WorldModel/model.py`) instead, so every intermediate is
    *valid by construction*. This is the upgrade path, not yet wired.
- **Compose axes → a control space.** N dials span an N-dimensional design space;
  the anchors are its corners (a grid). Two dials give you a plane you can feel.

> "We're just measuring the distance between two points. That's all that any
> intelligent system does." — the operator.
> Made literal here: the AI's *utility/loss* is a distance to a reference, and
> the *fill* is a path between references. Targeting = shrink a distance.
> Filling = traverse one.

## 4. Dimensions, as differences

Every added dimension is "the difference between two of the thing below it":

| Dimension | Difference of… | Deterministic lift |
|---|---|---|
| 3rd — depth / Z | two viewpoints (stereo), **or** a top-down map + a heightmap | ground-plane inverse perspective `Z = f·H/(y − yₕ)`, or `map+height → world xyz` |
| 4th — time / motion | two moments | the delta *is* velocity / flow; pose = state·f(t) |
| season, age, weather… | any two states | anchor-pair + fill |

**View-independence.** The authoring surface that scales is not a single
photograph (whose depth cue depends on where the camera stood) but a **top-down
map + heightmap**: placement is world-X/Y, elevation is world-Z, and the lift
needs no inference. The single-photo perspective lift is available for quick
sketches; the map/height pair is the load-bearing authoring format.

## 5. Direct, not emergent (the discipline)

- The construction is an **algorithm**: `pose = construct(state, dials)`. Same
  `(state, dials)` → byte-identical geometry, forever. This is the determinism /
  fractal property the operator requires ("same seed, same world, forever").
- It does **not** relax to an attractor, integrate a chaotic ODE, or depend on a
  random seed at *runtime*. Randomness is allowed only at *authoring* time (to
  grow an anchor), never in the per-frame fill.
- **Do not conflate the two regimes.** Selecting-for-emergence (sandpile,
  accretion) and placing-directly (construction) are different rungs. Mixing them
  — asking a placement layer to also discover dynamics — is the named
  "rung conflation" failure mode. The construction layer is deliberately dumb and
  exact so the intelligence can live where the operator wants it: in the choice
  of anchors.

## 6. Two backends, one model

```
                     ┌───────────────────────┐
                     │      SCENE MODEL       │   renderer-agnostic
                     │  placed objects +      │   (Construction/scene)
                     │  generator ids + params│
                     │  + per-object state    │
                     └───────────┬───────────┘
                                 │  fill(axis, dial)
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
        ┌─────────────────┐             ┌──────────────────┐
        │ DOM / HTML       │            │ PC / 3D           │
        │ dev backend      │            │ ParticleEngine    │
        │ canvas, legible, │            │ Gaussian splats,  │
        │ instant iterate  │            │ GPU, the real one │
        └─────────────────┘             └──────────────────┘
```

- The **scene model** is the single source of truth. Both backends are
  *projections* of it — they cannot disagree about *what* is in the scene, only
  about *how* it is drawn.
- **DOM/HTML** is the development surface: an AI can emit it, render it, read it
  back, and adjust in one fast loop. It is where authoring happens.
- **PC/3D** is the product surface: `physics_tree` → Gaussian splats →
  `ParticleEngine` on the GPU.
- **Drift guard.** The one thing that can silently diverge is the *fill math*
  duplicated in JS (HTML) and Python (3D). Until the fill is shared (compiled
  from one source, or the HTML consumes a Python-precomputed pose sequence), the
  two implementations must be tested against each other at the anchors: at `t=0`
  and `t=1` both backends must reproduce the anchors exactly.

## 7. The reference / taste tie-in (closes today's loop)

The anchors *are* references, so the preference machinery built earlier plugs
straight in:

- **Physics** gates *validity* — only feasible fills are eligible (the hard
  wall). Same role it plays in the trainer.
- **Taste** (`docs/objectives/taste.json`, the Will) *selects among valid fills*
  — the soft, human-authored post-filter. `core/preference_select.py` already
  ranks a trainer's `top_k`; here it ranks candidate fills / candidate anchors.
- **The human authors the anchors.** That is the one thing neither physics nor
  taste can do: supply the reference. No reference, no verdict.

## 8. Worked example — a tree in the wind (the walking skeleton)

The thinnest slice that exercises every idea above at once:

- **Object:** `WorldModel/physics_tree.py` — a physics-informed oak skeleton
  (gravitropism, phototropism, Murray's law, beam mechanics), Z-up.
- **Axis:** `WIND`, from anchor **CALM** to anchor **GALE** — a difference in
  four scalars: downwind `lean`, gust `sway` amplitude, leaf `flutter`, and
  `sky` greying.
- **Dial:** one slider, `t ∈ [0,1]`.
- **Backends:** the HTML dial (interactive, drag CALM↔GALE) and `ParticleEngine`
  stills rendered at `t = 0, 0.5, 1.0` — the *same* scene model and the *same*
  anchor definitions driving both.

What it proves, line by line: difference-as-dimension (§3), a deterministic
state→pose fill (§5), one model / two backends (§6), and an object whose validity
is physical (§7). It is deliberately parameter-lerp, not manifold — §9 widens it.

## 9. Roadmap (what widens the skeleton)

Condensed from the full task list. `[FIX]`/`[BUILD]`/`[WIRE]`, rough size.

**A · Foundation** — `[FIX](S)` restore `ParticleEngine/splat.py` *(done)* ·
`[FIX](S)` cap the `physics_tree` trunk-radius blowup at the construction layer ·
`[DECIDE](S)` `physics_tree` (Z-up) is the one canonical tree generator; retire
`oak_demo`.

**B · 2D authoring surface** — `[BUILD](M)` top-down **map** (world X/Y) ·
`[BUILD](M)` **heightmap** channel (world Z) · `[BUILD](S)` **anchor** format.

**C · Construction spine** — `[BUILD](L)` the **lift** (map+height → world xyz) ·
`[BUILD](M)` the **scene model** *(first pass done for the tree)* ·
`[BUILD](M)` per-object **construction operators** (tree = skeleton+thickening).

**D · Anchor / axis / dial** — `[BUILD](S)` axis = anchor-pair + rule ·
`[BUILD](S)` fill `(axis,t) → state` · `[BUILD](S)` dial bound to game state ·
`[DONE→GENERALIZE](S)` the wind axis.

**E · Two backends** — `[BUILD](M)` HTML dev renderer of the scene model ·
`[WIRE](M)` 3D renderer of the *same* model · `[BUILD](S)` shared camera ·
`[BUILD](S)` anchor drift-guard test.

**F · Manifold fill** — `[BUILD](L)` traverse the VAE latent for non-convex
axes · `[WIRE](M)` encode each anchor → a latent point · `[WIRE](M)` physics as
the validity gate on the manifold.

**G · Control & runtime** — `[BUILD](M)` compose axes (prove 2 dials → a plane) ·
`[BUILD](M)` bind dials to game state · `[BUILD](M)` the runtime loop.

**H · Reference & taste** — `[WIRE](M)` anchors as references (loss = distance) ·
`[WIRE](S)` taste selects among valid fills.

## 10. Honest status & limits

- The fill is **parameter-lerp**, not manifold traversal. Valid for wind (the
  parameter space is convex); *not* valid in general. The VAE path (§F) is
  designed, not built.
- HTML and 3D **duplicate the fill math** (JS vs Python). Guarded only at the
  anchors for now (§6). One shared source is the real fix.
- The `physics_tree` **trunk-radius blowup** (beam mechanics inflates the trunk
  to ~100 after growth) is **capped at the construction layer**, not fixed at the
  source. The source behavior is arguably a real physics bug (a 300-tall tree
  should not need a 100-radius trunk); left untouched because `physics_tree` is
  shared and the cap is sufficient for rendering.
- The general **2D→3D lift** (§C) is designed; the tree demo uses **direct
  placement** (a world coordinate), which is the map-lift's `t=identity` case.
- "Direct not emergent" is a *discipline*, not something the code enforces yet —
  nothing stops a future operator from wiring a chaotic sim into a dial. The
  discipline is documented here so that when it is violated, it is violated
  knowingly.
