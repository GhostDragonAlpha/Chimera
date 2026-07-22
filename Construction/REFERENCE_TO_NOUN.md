# Photo → Textured 3D Tree — THE WORKFLOW (a recipe, follow it exactly)

> Turn a real photograph into a complete, orbitable 3D tree that wears the photo's
> own bark and foliage. Discovered end-to-end 2026-07-22 (the Baginton-oak run).
> **This is a RECIPE. The judgment is already in the code. Run the steps in order,
> verify by eye, do not improvise the design.** (Successor-runbook rule.)

## TL;DR — one command

You fetch the reference photo yourself (below), then:

```bash
python Construction/photo_to_tree.py --photo <ABSOLUTE path to the photo> --name oak
# -> Construction/renders/oak_tree_0.png (front)  +  _1.png (angle).  Read them.
```

That is the whole thing. It runs the three stages below in the one correct order.
`--lod 1.5` raises template detail (more markers → finer). If you only want to
re-render (template already trained), skip to stage 3.

## The idea in one paragraph (so you don't fight the recipe)

A photo is a **clipped, single-view billboard** — fitting splats to its pixels
just re-draws the photo, flat, with no back and a cut-off crown. A hand-built
parametric tree is a **complete 3D shape but generically coloured**. Neither is
the answer. The answer is to **CROSS** them: the template distributes **markers**
in complete 3D (crown dome + trunk cylinder, no clipping, holds up when rotated);
each marker, coloured by the photo, says *"put the photo pattern of this colour
HERE"*; and a **pattern library of real textured patches cut from the photo** is
matched to each marker and stamped in its vicinity. Markers = WHERE (distribution).
Photo patches = WHAT (the recognized sub-patterns). Cross them and you get a
complete 3D tree wearing the photo's real texture. Refinement dial = template
**level of detail** (marker density).

## Stage 0 — get the reference photo

Screenshots need the Browser pane displayed; **downloading + Read does not**, so
prefer this. Find an image URL in the Browser pane, then download WITH browser
headers (Wikimedia and most hosts block bare `curl`):

```bash
# in the Browser pane, list candidate images on a page:
#   javascript_tool: JSON.stringify(Array.from(document.querySelectorAll('img'))
#     .map(i=>({src:i.src,w:i.naturalWidth,h:i.naturalHeight}))
#     .filter(o=>o.w>=200).sort((a,b)=>b.w*b.h-a.w*a.h).slice(0,6))
curl -sL \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36" \
  -H "Referer: https://en.wikipedia.org/" \
  -o Construction/renders/reference_oak.jpg "<image-url>"
file Construction/renders/reference_oak.jpg     # MUST say "JPEG image data", not HTML
```
Then **Read** the file to actually look at it. A clean single tree, trunk + crown,
works best. (`Construction/renders/` is gitignored — photos and PNGs stay local.)

## The three stages (what the one command runs)

### 1. EXTRACT — the photo's descriptors  (statistics the template trains toward)
```bash
cd Chimera && PYTHONPATH=. python -m core.trainables.tree_appearance extract \
    --photo <ABSOLUTE path>            # writes docs/tree_references/<name>.json
```
Silhouette (aspect/fill/cy/cover/trunk_w/fork) + foliage colour moments
(lum/lstd/grn) + a small foliage & bark palette. Committed, so training is
reproducible without the photo.

### 2. TRAIN — the template's parameters, against the photo  (never renders; ~7000 evals/sec)
```bash
cd Chimera && PYTHONPATH=. CHIMERA_TREE_REF=<name> python -m core.trainer \
    --domain core.trainables.tree_appearance \
    --objective docs/objectives/tree_appearance.json \
    --pop 200 --gens 60 --out docs/objectives/tree_appearance.trained.json
```
The genome is the template's render parameters (crown rx/rz/zc, droop, density,
trunk hf/base_w, the shade curve, colour gain). The measure is **Julesz-descriptor
distance to the photo** — no rendering in the loop, no taste. **Iterate the
OBJECTIVE, never the artifact** (`docs/objectives/tree_appearance.json`): if the
result is wrong, a descriptor is wrong. Confirm `fidelity` climbs and `nothing
pinned`.

### 3. CROSS — markers × photo patches → the textured 3D tree  (the step that made it work)
```bash
python -m Construction.cross --photo <ABSOLUTE path> \
    --genome Chimera/docs/objectives/tree_appearance.trained.json \
    --out Construction/renders/oak_tree --lod 1.0
```
Builds the template's 3D markers from the trained genome, colours each by sampling
the photo at its front projection, matches each to the nearest-colour real photo
patch, and stamps it. Front view ≈ the photo's texture; angle view = a complete,
rotatable 3D tree. **Read both PNGs and judge by eye** (ground the verdict in what
you see, never in taste).

## The pieces (file map)

| file | stage | role |
|---|---|---|
| `Construction/photo_to_tree.py` | all | the one-command orchestrator (runs 1→2→3) |
| `Chimera/core/trainables/tree_appearance.py` | 1,2 | the trainable template: `descriptors_from_photo`, `seed/mutate/measure`, `render_tree` witness |
| `Chimera/docs/objectives/tree_appearance.json` | 2 | the objective — match the photo's descriptors (edit THIS to iterate) |
| `Chimera/docs/tree_references/<name>.json` | 1 | the committed descriptors + palette (the reference) |
| `Construction/cross.py` | 3 | THE SYNTHESIS: template markers × photo patches → textured 3D tree |
| `Construction/gsplat_fit.py` | (refine) | differentiable per-splat fit to the pixels — finer pattern recognition, feeds future cross |
| `Construction/DESIGN.md` | — | the architecture and why |

## Refinement — the dials, in order of value

1. **Template level of detail** (`--lod`): more markers → finer texture. The main
   quality dial now.
2. **Trim edge halos**: the outer canopy patches float as light cotton-puffs. In
   `cross.pattern_library`, reject patches whose mean is sky-bright; in `render`,
   drop markers whose sampled colour is background.
3. **Iterate the objective** (stage 2): the trained crown is only as good as the
   descriptors — the green mask catches background trees, so it trains tall. Tighten
   the silhouette descriptor (exclude background) to fix proportion.
4. **Finer recognition**: match markers to `gsplat_fit` splats (oriented, per-pixel)
   instead of raw colour-nearest patches — sharper bark fissures.

## Honest state (2026-07-22)

Works: complete 3D tree, real photographic bark and foliage texture, holds up from
multiple angles, a believable offspring of the specific tree. Not yet photoreal:
fuzzy/haloed canopy edges, silhouette a touch soft, proportion driven by a crude
mask. The mechanism is proven; the remaining distance is LOD + the refinements above.

## Worked example — the Baginton oak (2026-07-22)

`reference_oak.jpg` (Wikimedia). The journey, so you learn the dead ends:
- Parametric-only construct → generic "ultra-stylized" tree (right shape, wrong,
  invented appearance).
- Nine-descriptor trainer → matched colour, still looked nothing like the photo
  (you cannot rebuild a photo from nine numbers).
- Per-splat 2D fit → reproduced the photo exactly = a flat billboard, and the clip
  and empty back returned. "That's just the photo."
- **CROSS (this recipe)** → template markers (complete 3D) × photo patches (real
  texture) → a textured 3D oak that holds up rotated. This is the one that worked.
