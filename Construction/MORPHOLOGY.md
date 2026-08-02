# Morphology — the template knowledge base

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> The concepts the AI **draws on** to author a template (see the "Morphology informs
> the template" section of `REFERENCE_TO_NOUN.md`). A **told** knowledge base, not
> code: the AI recognizes the subject, picks the concepts, and authors the
> per-subject template generator from them. **Grow this catalog; never grow the
> engine.** Every entry is source-cited — ground the choice in it, never in taste.
> Researched & verified 2026-07-22.
>
> **Told here, measured there — same morphology.** In the sibling scan→DNA pipeline
> (`SPLAT_DNA_WORKFLOW.md`) these shape concepts are *computed* per element by
> `morphology_signatures.py` (taper / radial symmetry / fractal dimension / aspect =
> the measured shape-DNA). This catalog is the concepts a template is authored *from*;
> that code is the concepts a real scan is measured *against*.

A morphology concept does one of **four jobs** for a template. When authoring, name
the job you need, then reach for the concept:

1. **Topology prior** — WHERE the parts go, and how to generate the UNSEEN half.
2. **Surface-pattern / material** — how markings and materials are distributed.
3. **Deform-a-mean-to-the-photo** — fit a canonical template to the image.
4. **Thickness & proportion** — infer radii and part sizes, including the unseen.

## Job 1 — Topology prior (where parts go + complete the unseen half)

| concept | rule | markers / complete | source |
|---|---|---|---|
| **Symmetry class** (spherical / radial / biradial / bilateral) | body plans fall into symmetry groups; each is a different *completion operator* | place markers only in the fundamental domain (a wedge for radial, a half for bilateral); the group replicates them → the unseen side. **Detect the group FIRST** — mis-mirroring a radial subject (starfish, flower) as bilateral is the classic error | Manuel 2009, *C R Biologies* 332:184 |
| **Hallé–Oldeman–Tomlinson architectural models** | a tree's whole form is one of ~23 inherited growth programs (4 binary choices: mono/sympodial, ortho/plagiotropic, rhythmic/continuous, terminal/lateral flowers) | pick the model → it places every branch; the unseen crown completes as the model's rhythmic/mirrored tiers (table below) | Hallé, Oldeman & Tomlinson 1978, *Tropical Trees and Forests*; Barthélémy & Caraglio 2007, *Ann Bot* 99:375 |
| **Reiteration** (Oldeman) | a tree is its architectural unit repeated at many scales — a fractal of the same program | tile the crown with scaled copies of the visible unit; fill an occluded region with a scaled copy | Ishii 2007, *Tree Physiol* 27:455 |
| **Bauplan / phylotypic stage** (developmental hourglass) | a phylum shares a conserved mid-development body plan; the Bauplan is the invariant scaffold | anchor on phylum invariants (axis count, segments, appendage positions); **assert the plan** (spine, paired limbs) even when the photo can't show it, then deform | von Baer 1828; Domazet-Lošo & Tautz 2010, *Nature* 468:815 |
| **Morphogenetic fields** | development is discrete self-regulating spatial fields (limb field, eye field); each forms a whole | partition the template into fields; a partly-visible field completes to its canonical whole, and fields say which regions complete independently | Gilbert, Opitz & Raff 1996, *Dev Biol* 173:357 |
| **L-systems** (Lindenmayer) | development as parallel string-rewriting — the formal engine under the above | encode the growth laws as productions; run the grammar to EMIT the full 3D marker set; the unseen half is just more derivation of the same rules | Prusinkiewicz & Lindenmayer 1990, *The Algorithmic Beauty of Plants* |

## Job 2 — Surface-pattern & material distribution

| concept | rule | markers / complete | source |
|---|---|---|---|
| **Positional information** (Wolpert, "French-flag") | cells read position from a morphogen gradient and differentiate by threshold | lay a coordinate field over the template; place pattern/material markers by *thresholding* it (not enumerating); extend the gradient into occluded regions to fill what belongs there — the continuous cousin of your Hox cascade | Wolpert 1969, *J Theor Biol* 25:1 |
| **Turing reaction–diffusion** (activator–inhibitor) | short-range activator + long-range inhibitor break symmetry into spots/stripes at an intrinsic wavelength | parameterize the RD field over the surface — it *generates* the markings from a few constants; run the same process across the unseen side for seamless, statistically-matching pattern | Turing 1952, *Phil Trans R Soc B* 237:37; Kondo & Miura 2010, *Science* 329:1616 |
| **Differential adhesion** (Steinberg) | tissues sort like immiscible fluids — most-adhesive interior, least enveloping (minimizes surface energy) | assign each material an adhesion value; radial layering (bone core → muscle → skin shell) is *predicted*, not hand-placed; the unseen cross-section nests in tension order. **We already run this** (Cellular Potts, `core/matter.py`) | Steinberg 1963, *Science* 141:401 |

## Job 3 — Deform a canonical template to the photo (the fit machinery)

| concept | rule | markers / complete | source |
|---|---|---|---|
| **Theory of transformations** (D'Arcy Thompson) | related forms connect by smooth coordinate warps of a reference grid | fit the warp on the VISIBLE part, apply the SAME warp to the unseen part → completion by homologous deformation, not invention | Thompson 1917, *On Growth and Form* |
| **Geometric morphometrics** (Procrustes + thin-plate spline) | shape = landmark config after removing translation/rotation/scale; differences = TPS warps (Thompson's grids, computed) | landmarks ARE markers; Procrustes-align template landmarks to the photo's, solve the TPS, push the whole 3D template (unseen included) through the warp | Bookstein 1991; Adams et al. 2013 (geomorph), *Methods Ecol Evol* 4:393 |
| **3D Morphable Model** (Blanz & Vetter) | a PCA space over registered exemplars; instance = mean + linear basis (shape+texture); fit = solve coefficients from visible pixels | dense correspondence fixes the marker layout; the mean is the canonical template; fitting *visible* pixels yields the COMPLETE 3D (unseen filled by the most-probable shape) | Blanz & Vetter 1999, SIGGRAPH |
| **Mean-template + blendshapes + LBS** (SMPL / SMPL-X / STAR / FLAME) | one canonical mesh deformed by learned identity blendshapes + pose skinning + expression; shape disentangled from pose | fixed topology = marker layout; blendshapes = licensed deformations; one photo constrains the whole; unseen back/limbs generated in the inferred pose. SMPL=bodies, FLAME=heads | Loper et al. 2015 (SMPL); Li et al. 2017 (FLAME) |
| **Category-specific mesh / Common3D** | learn a category MEAN mesh + per-instance deformation + camera + texture from image collections / videos, no 3D ground truth | the learned mean = the marker canvas; a net predicts the deformation and mirrors texture/features to the hidden side; **Common3D generalizes zero-shot to arbitrary categories — our animal/artifact endgame** | Kanazawa et al. 2018 (CMR), ECCV; Common3D, CVPR 2025, arXiv:2504.21749 (authors unverified) |

## Job 4 — Thickness & proportion (complete radii and sizes)

| concept | rule | markers / complete | source |
|---|---|---|---|
| **Pipe model** (Shinozaki) | a tree is a bundle of unit pipes; woody cross-section = leaf mass borne above (the mechanistic parent of Murray/Leonardo — ties diameter to *leaf area supported*) | set each axis radius from the count of distal leaf-markers; infer hidden trunk/branch THICKNESS from visible canopy, and unseen foliage from a measured base diameter | Shinozaki et al. 1964, *Jpn J Ecol* 14:97 |
| **Corner's rules** | (1) stouter axes carry larger appendages; (2) more branching → smaller branches/appendages | scale each appendage marker to its axis diameter and shrink along branching order; predict unseen leaf/organ SIZE from a visible twig's diameter | Corner 1949, *Ann Bot* 13:367 ("The Durian Theory") |
| **Medial axis transform** (Blum) | a shape = its skeleton (centers of maximal inscribed balls) + a radius per point; sweeping reconstructs the solid | markers on the medial axis carry thickness — **our "axis + radial tissue" limb encoding** (`core/limb.py`); extend the axis into occluded regions + sweep the radius → watertight unseen volume | Blum 1967/1973, *J Theor Biol* 38:205 |
| **Allometric / metabolic scaling** (Kleiber; West–Brown–Enquist) | quantities scale as power laws of size via space-filling fractal transport networks (¾-power metabolism) | set network calibers by the space-filling rule; predict an unseen internal network's size from overall size (or the whole from a visible part) via the exponent | West, Brown & Enquist 1997, *Science* 276:122 |
| **Phytomer / metamer** (the plant module) | the plant is one repeated unit — node + internode + leaf + axillary bud; branching = activating a bud | the phytomer IS the marker unit; tile an occluded stem with identical phytomers at the known internode spacing | White 1979, *Annu Rev Ecol Syst* 10:109 |

## Tree architectural models — expand the tree exemplars (Job 1, applied)

Pick the model the photo shows; it is a ready-made branch grammar **and** a
completion rule. (These extend the excurrent/decurrent split in the recipe.)

| model | growth program | reads as | recipe row |
|---|---|---|---|
| **Rauh** | monopodial, orthotropic, rhythmic tiers, lateral flowers | whorled tiers on a straight leader (oak, many conifers) | excurrent |
| **Massart** | monopodial orthotropic trunk + plagiotropic tiered branches | symmetric pagoda | — |
| **Roux** | continuous monopodial trunk + plagiotropic branches | diffuse, non-tiered | — |
| **Attims** | Rauh but continuous (no rhythm) | leader + branches, no tiers | — |
| **Troll** | all axes plagiotropic, then secondarily erect | most dicot trees | decurrent |
| **Leeuwenberg** | 3-D sympodium; each module orthotropic, determinate, ends in a flower | forking shrub | — |
| **Scarrone** | sympodial, orthotropic, rhythmic, terminal flowers | mango-like | — |
| **Champagnat** | orthotropic axes bending under their own weight | arching / weeping | weeping |
| **Corner (model)** | unbranched single axis, lateral flowers | palm, tree-fern | rosette |

## Already realized in our code (draw on it, don't rebuild)

- **Differential adhesion** → `core/matter.py` (Cellular Potts self-sorting layers).
- **Medial axis / axis + radial** → `core/limb.py` (skeleton = axis, adhesion = radial tissue).
- **L-systems** → `core/terrarium.py` (bounded parametric L-system; "a creature is a cascade").
- **Phyllotaxis / Murray** → `WorldModel/physics_tree.py` + the golden-angle lift.

The rest — Hallé models, pipe model, positional information, Turing, the morphable
models (3DMM / SMPL / CMR / Common3D), geometric morphometrics — are **available to
add**. Start with the tree architectural models above (we already do trees), and
reach for CMR/Common3D when generalizing to animals and artifacts.
