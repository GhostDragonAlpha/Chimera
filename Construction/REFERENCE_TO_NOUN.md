# Photo → Textured 3D Tree — THE WORKFLOW (a recipe, follow it exactly)

> Turn a real photograph into a complete, orbitable 3D tree that wears the photo's
> own bark and foliage. Discovered end-to-end 2026-07-22 (the Baginton-oak run).
> **This is a RECIPE. The judgment is already in the code. Run the steps in order,
> verify by eye, do not improvise the design.** (Successor-runbook rule.)
>
> **Sibling pipeline — don't confuse them:** this recipe builds a stylized object *from a
> 2D photo*. To instead decompose a *real 3D Gaussian-splat scan* into material genomes
> (DNA), see **`Construction/SPLAT_DNA_WORKFLOW.md`**. Same DNA/patch vocabulary, different
> input.

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

## The two engines — AI and training — and how they interlock

The workflow runs on two different engines, and keeping each in its lane is the
whole reason it works. The studio's core rule: **the AI writes the constraints; it
never turns the crank.**

**The AI engine — judgment (the top and the bottom, never the middle).**
- LOOKS at the photo (vision) and recognizes the pattern-groups: what bark is,
  what foliage is, the tree's morphology.
- AUTHORS the template: using its knowledge of how a tree is built, it decides the
  3D distribution of markers and **completes the membrane** — the crown-top and the
  back the photo never shows. No optimizer can do this from one clipped photo; it
  needs a prior about what a whole tree *is*. This is the AI's real contribution.
- JUDGES the result by eye and ITERATES THE OBJECTIVE when it is wrong.
The AI chooses and sees. It does NOT place ten thousand splats by hand — it manages
~20 edits an hour; that is not its job.

**The training engine — the crank (turned by the machine).**
- TRAINS the template's parameters against the photo's descriptors: ~7,000
  evaluations/second, no taste, no rendering in the loop (statistics space). It
  discovers the parameter values the AI cannot eyeball.
- FITS per-splat Gaussians to the actual pixels by gradient descent
  (`gsplat_fit`) — the finer recognition.
Training turns fast. It has no idea what a tree is; it only reduces a distance.

**How they interlock — the MARKERS are the handoff.** The AI authors WHERE patterns
go (the marker distribution) and completes the form; training optimizes the numbers
that shape that distribution to the photo; then the CROSS matches each marker to a
recognized photo patch and stamps it. AI at the top (author + complete), training in
the middle (optimize to the photo), AI at the bottom (judge + iterate). Put the AI
in the middle — hand-tuning splats — and you get the confetti tree we threw away.
Put training at the top — inventing the unseen crown from one photo — and you get a
billboard. Each in its lane, and it works.

## The template — what it is FOR, and why its detail sets the ceiling

The template is the **complete 3D scaffold**: a marker for every place a patch of
the tree should go, arranged into a whole form (crown dome + trunk cylinder). It
exists to solve the two things a photo alone cannot:
- **Completeness (the membrane).** A photo is clipped and single-view — no crown-
  top, no back, no interior. The template supplies them, so the tree is whole and
  survives rotation. The photo colours the markers it can see; markers beyond the
  frame wear the nearest photo pattern.
- **Distribution.** The template says WHERE each pattern belongs in 3D; the photo
  says WHAT each looks like. The CROSS multiplies the two.

**Level of detail is the primary quality dial (`--lod`).** Each marker places ONE
patch, so the marker count is the resolution of the result:
- too few → sparse, blobby, confetti at the edges;
- more → denser coverage, finer texture, sharper bark and leaf detail;
- you cannot show detail finer than your markers are dense — the template's LOD is
  a hard ceiling on how much of the photograph can land.
So "make the tree better" mostly means **raise the template's level of detail** —
more markers, `--lod 1.5`, `--lod 2.0` (trading render time for detail). Structural
detail matters too: the closer the marker distribution matches the real crown and
limb layout, the more believable the 3D shape — and that comes from **iterating the
training objective** so the template's proportions match the photo. The AI shapes
the template; training sharpens it; LOD scales it.

## Morphology informs the template — name the form BEFORE you place a marker

The template is not a fixed shape you reuse; it is the subject's **morphology**,
authored fresh each time. This is a CONCEPT the agent is **told, never programmed**:
you cannot hardcode a template for every species and object, but an agent that
knows morphological principles can look at the photo, recognize the category, and
author the right marker distribution from the rules. **Before you place a marker,
name the subject's morphology and distribute the template by its growth / structural
rules.**

This is also what lets the template **complete the membrane honestly**: the
crown-top and the back the photo never shows are not guessed — they *follow the
morphology* (symmetry + growth rules). Morphology is the prior that completes what a
single photo cannot see. (This is the AI-authored analog of ML "3D morphable models
/ learned template + deformation field": the AI authors the category template, then
training deforms its parameters.)

Told, not programmed — but paired with **exemplars**, so a weaker agent *matches a
pattern* instead of guessing. And the concept produces code: from the morphology you
author a per-subject template generator (as `tree_appearance` is authored for the
oak). The concept is the reusable part; the generator is its instantiation.

### Exemplar catalog — match the subject to a morphological pattern

Trees first (real, named science — ground the choice in it, never in taste):

| If the photo shows… | morphology (the rule) | distribute markers as… | complete the unseen by… |
|---|---|---|---|
| broad spreading crown, stout low fork (oak, maple) | **decurrent** — apical dominance lost, repeated forking; Leonardo's/Murray's rule (branch cross-section conserved through a fork); beam-mechanics taper | a wide, slightly flat dome of clumps over a short stout trunk cylinder | radial symmetry of the dome; forks continue around the back |
| tall narrow column (poplar, cypress) | **excurrent** — strong apical dominance, one dominant leader | a slim vertical spindle of clumps hugging a tall straight trunk | axial symmetry about the leader |
| cone, tiered whorls (spruce, fir) | excurrent + whorled branching in phyllotactic tiers | stacked rings of clumps narrowing to a point | rotational symmetry of each whorl |
| bare stalk topped by a rosette (palm, tree-fern) | monopodial column + apical crown of fronds | a bare trunk cylinder + a radial fan of frond-markers at the top ONLY | radial fan completes around the crown |
| weeping form (willow) | decurrent + strong droop (raise `droop`) | a dome whose outer markers hang below the branch line | symmetry + gravity |

Beyond trees (same principle, different rule set — hooks for later):
- **Animals** — bilateral symmetry + a Hox/segmentation cascade (a body is a staged
  program with positional identity; see `Chimera` `docs/TERRARIUM_DESIGN.md`, "a
  creature is a cascade"). Distribute markers by body plan; complete the far side by
  mirror.
- **Artifacts / architecture** — structural symmetry and load paths. Distribute by
  the object's construction logic; complete by its symmetry group.

The tree table is the worked catalog; the two hooks mark where the concept extends.
When a subject fits none of these, that is the signal to **research** its morphology
(Hallé's architectural models for plants; Bauplan / body-plan references for
animals) and **add a row** — grow the catalog, never the engine.

**The full concept catalog is [`Construction/MORPHOLOGY.md`](MORPHOLOGY.md)** — 19
source-cited concepts organized by the **four jobs** a morphology concept does for a
template: (1) *topology prior* (where parts go + complete the unseen half — symmetry
class, Hallé models, Bauplan, reiteration, L-systems), (2) *surface-pattern /
material* (positional information, Turing reaction-diffusion, differential adhesion),
(3) *deform-a-mean-to-the-photo* (D'Arcy Thompson transformations, geometric
morphometrics / TPS, 3DMM, SMPL/FLAME, CMR/Common3D), (4) *thickness & proportion*
(pipe model, Corner's rules, medial axis, allometric scaling). Reach into it by
**naming the job you need**, then pick the concept.

## Stage 0 — get the reference photo

### Choosing the reference — the methodology (matters as much as the code)

The template is built FROM the photo's silhouette (Stage 3), so **a clean subject
IS a clean template**. Choose the reference by these rules, in order:

- **Search `"<subject> on white background"`.** This returns the subject
  pre-isolated on white (stock sites, cutouts). The white background is trivially
  masked — the pipeline drops it — so there is **no sky and no clutter** to pollute
  the mask or the patch library. This one trick fixes most reference problems.
- **Whole subject in frame** — crown AND trunk, **not clipped**. A clipped crown
  makes a clipped template (the gnarled oak that started this project was clipped
  and cluttered, and it fought us for days — the anti-example).
- **Highest resolution the source offers.** More pixels → more and finer patches →
  more detail.
- **A canonical form** for the morphology you want (round-crowned for a round tree;
  name it via `MORPHOLOGY.md`).
- **ALWAYS Read (look at) the download before using it.** Reject clipped, cluttered,
  tiny, or wrong-subject images on sight — never run the pipeline on a bad photo.
- **Watermarks / licensing:** a faint stock watermark is tolerable for a DEV test
  (the patch library edge-rejects most of it). For anything shipped, use a
  freely-licensed or your own photo — stock previews are copyrighted; keep them local.

### Fetching it

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
Builds the template's 3D markers **from the photo's own silhouette** (foliage fills
the crown mask, the trunk fills the trunk mask, each lifted into 3D), colours each
from **its own source pixel**, matches each to the nearest photo patch, and stamps
it. **The template is MADE FROM the photo, not reused** — a marker only exists where
the tree is, so sky/white can't enter and a trunk marker is bark by construction.
The trained genome is now **optional** (it lightly scales crown depth). Front view ≈
the photo's texture; angle view = a complete, rotatable 3D tree. **Read both PNGs and judge by eye** (ground the verdict in what
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
| `Construction/MORPHOLOGY.md` | author | the cited concept catalog (author the template from it) |
| `web/index.html` + `Construction/web_export.py` | dev | **run it in the BROWSER over HTTP** — the DOM dev backend |

### Run it in the browser (the DOM dev backend, HTTP)

The canvas renderer runs natively in a browser — the "develop in the DOM" surface.
```bash
python -m Construction.web_export        # markers + photo colours -> web/tree.json
# then start the server + open the pane (do NOT use Bash to run servers):
#   preview_start  name="construction-web"   ->  http://localhost:8017  (canvas orbit)
```
Iterate like web dev: edit `web/index.html` (or re-run `web_export` after retraining)
and **reload** the tab. Verify without a screenshot when the pane isn't displayed:
`read_page` (the HUD shows "&lt;N&gt; markers") and `read_console_messages` (errors).
This renders the photo-*coloured* markers; the photo-*textured* patch pass and the
GPU splat renderer are Python (stream their PNGs to a page, or port the patch
composite to canvas, as the next step).

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
