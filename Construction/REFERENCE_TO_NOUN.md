# Reference → Noun → Verb — the workflow

> How to turn **any reference photo** into a controllable 3D **noun**, by
> CONSTRUCTION (not extraction), and give it a **verb**. A recipe, not a theory.
> Companion to DESIGN.md. First recorded 2026-07-22 (the Baginton-oak run).

## The principle (why this works)

The AI does **not** decode the photo into geometry (that is extraction — inverting
pixels, brittle, and not what we want). The photo is a **reference**. The AI
**authors a clean, decodable 2D seed that resembles it**, and a deterministic
constructor lifts that seed into valid 3D. Construction, guided by a reference.

The two hard jobs are split so each goes to whoever is good at it:
- **Validity** (is it a well-formed 3D noun?) — *guaranteed by the constructor*.
  You cannot author an impossible tree; the decode only makes valid ones.
- **Resemblance** (does it look like the photo?) — *the AI's job*: look at a
  reference, emit a structured spec. The AI never has to be right about the
  photo's true geometry — only author a seed that decodes to something that reads
  like it. The gap is measurable by eye against the reference.

## The loop (do this)

### 1. Get a reference photo
Find an image URL in the browser, then download WITH browser headers (Wikimedia
and most hosts block bare `curl`):
```bash
# in the Browser pane, list candidate images on a page:
#   javascript_tool: JSON.stringify(Array.from(document.querySelectorAll('img'))
#     .map(i=>({src:i.src,w:i.naturalWidth,h:i.naturalHeight}))
#     .filter(o=>o.w>=200).sort((a,b)=>b.w*b.h-a.w*a.h).slice(0,6))
curl -sL \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36" \
  -H "Referer: https://en.wikipedia.org/" \
  -o Construction/renders/reference.jpg "<image-url>"
file Construction/renders/reference.jpg   # confirm "JPEG image data", not HTML
```
Then **Read** the file to actually LOOK at it. (Screenshots need the Browser pane
displayed; downloading + Read does not.)

### 2. Author the seed — LOOK, then map to knobs
Read the photo and set `Construction/noun.construct(...)` arguments:

| The photo shows… | knob |
|---|---|
| thick / stout trunk | `trunk_radius` ↑ (sapling ~12, old oak ~30) |
| tall tree / high fork | `trunk_height` ↑ |
| dense, full canopy | `max_depth` ↑ (5–6; 4 is sparse) |
| deep rounded **dome** crown | `droop` ↑ (0 = flat umbrella, ~1.2 = oak dome) |
| wide spreading crown | `spread` ↑ (0.3–0.6) |
| leaning tree | the wind **verb** `lean` (not a noun knob) |
| silhouette off in a way no knob fixes | change `seed` (new branch pattern) |

`rule=golden_rule` is the default — it won the construction bake-off because
137.5° phyllotaxis packs the canopy most evenly (physics, not taste).

### 3. Construct the noun, give it a verb, render
```python
import sys; sys.path.insert(0, r"E:\PythonChimera")
import math
from Construction import noun as N, tree as T, backend_3d as B3
from PIL import Image

noun = N.construct(seed=42, trunk_height=330, trunk_radius=30,
                   max_depth=6, droop=1.2, spread=0.55)      # author -> 3D noun
CALM = {"flutter": 0.0, "sky": 0.0}
# verb (optional): blown = T.pose(noun, wind_state, time, T.max_depth_of(noun))
img = B3.render([(noun, (0,0,0))], CALM, width=520, height=680,
                orbit_az=-math.pi/2, elev=0.04)             # front-on, eye-level
Image.fromarray(img).save(r"Construction\renders\match.png")
```
Then **Read** `match.png`.

### 4. Compare by EYE, then refine
Look at the render next to the photo and name the gap in physical terms
(proportion, crown shape, density) — **ground the verdict in what the constructor
can/can't express, never in taste** (the operator only trusts a science-grounded
pick). Adjust the knobs and re-run. Stop when it reads right, OR when the knobs
converge and it still doesn't — that convergence IS the constructor's ceiling,
and it is the signal to widen the vocabulary or move to the learned map (below).

### 5. Record
Append the run to the worked-examples list at the bottom of this file: the
reference, the final knobs, what each refine fixed, and where the ceiling showed.

## The pieces (file map)

| file | role |
|---|---|
| `Construction/noun.py` — `construct()` | author knobs → 3D noun (the whole decode) |
| `Construction/tree.py` — `build_skeleton`, `pose` | the tree generator wrapper + the wind **verb** |
| `Construction/lift.py` — `flatten`, `lift`, `shape_crown` | 2D picture, golden 3D lift, crown vocabulary |
| `Construction/backend_3d.py` — `render` | noun → Gaussian splats → ParticleEngine (GPU) |
| `Construction/viewer_nv.py` | interactive orbit + verb dial (dev surface) |

## Honest limits (know these before you judge)

- **The renderer is additive/emissive** (ParticleEngine splats add light over the
  background), so it needs a **dark sky** and produces soft glowing blobs with no
  solid bark. A daylight photo will never match its palette — that is a renderer
  choice, not a shape error. For a solid, daylight look use the opaque canvas
  backend (`viewer_nv` / `backend_html`), not this one.
- **The parametric constructor has a ceiling.** It makes one *family* of trees.
  Widening the vocabulary (this run added `droop`/`spread`) moves the ceiling but
  never removes it — a sprawling live oak, a palm, or a photoreal wall of leaves
  is out of range. When refinement converges short of the photo, that is the cue
  for the endgame: a **learned / holographic map** trained on real shapes, where
  any crown is representable (DESIGN §F; the "generalize the noun" fork).

## Worked examples

- **Baginton oak** (2026-07-22, `reference_oak.jpg`, Wikimedia). Read as: stout
  thick trunk, low fork, broad dense upright crown. Progression:
  - v1 `trunk_radius 26, max_depth 5, droop 0` → thin stalk + **flat pancake** crown. Trunk too thin/long; canopy categorically flat (no vocabulary for depth).
  - v2 `trunk_radius 42, trunk_height 190` → stout trunk fixed, crown still a flat disc → **exposed physics_tree's ceiling** (flat-umbrella canopy only).
  - **Added the crown knobs** (`droop`, `spread` in `lift.shape_crown`).
  - v3 `droop 1.2` → crown gained vertical depth, edges droop down (a dome, not a disc). Trunk over-corrected to a blob.
  - v4a `trunk_radius 30, trunk_height 330, max_depth 6, droop 1.2, spread 0.55, seed 42` → **best parametric match**: broad drooping crown, thick tapering trunk. Residual gap is now renderer realism (additive soft blobs, dusk palette) + the parametric ceiling → next is the daylight backend and the learned map.
