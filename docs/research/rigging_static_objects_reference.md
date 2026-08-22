# Rigging a Static Object — Established Practice (research reference, 2026-08-18)

Researched to answer: *how do people rig static objects* — before Chimera builds the
deformation layer for the sectioned 3DGS teddy. Starting point: symmetric stick skeleton
already fitted by measuring the cloud, parts rigidly assigned by nearest-bone (segment
Voronoi), splats carry position + rotation + scale + opacity + color.

## 1. Skinning methods (canonical)

- **LBS (Linear Blend Skinning).** `p' = Σ wᵢ · Bᵢ · p`, weights non-negative, Σw = 1.
  Cheap, universal (glTF skins cap at **4 influences/vertex** — one vec4). Artifacts:
  joint collapse / volume loss at bends, candy-wrapper collapse on twists — blended
  matrices need not be rigid even when every bone is.
  Sources: http://graphics.cs.cmu.edu/courses/15-466-f17/notes/skinning.html ·
  https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_020_Skins.html ·
  https://cseweb.ucsd.edu/~tzli/cse167/fa2023/lectures/23_rigging_skinning_blendshapes.pdf
- **DQS (Dual Quaternion Skinning).** Blend dual quaternions (8 floats), normalize → a
  rigid transform. Kills candy-wrapper + volume loss. Rigid transforms only (scale/shear
  need a separate pass — Disney's two-phase production variant).
  Sources: https://users.cs.utah.edu/~ladislav/kavan08geometric/kavan08geometric.pdf ·
  https://media.disneyanimation.com/uploads/production/publication_asset/98/asset/dualQ.pdf
- **Others:** Spherical Blend Skinning (Kavan & Žára 2005); Delta Mush (Le & Lewis 2019
  direct form); Pose-Space Deformation / corrective blendshapes (Lewis 2000; neural
  variant Li et al. 2021, https://arxiv.org/abs/2105.02451).

## 2. Rigid binding vs smooth weights

- Hard-surface/mechanical: **pure rigid** — each vertex w=1.0 on one bone. Standard for
  props/robots (Game-Ace: https://game-ace.com/blog/game-character-skinning/).
- Plush/organic (the teddy's class): **smooth skinning with a narrow transition band** —
  abrupt seams read wrong on a stuffed toy (Roblox character guide: "plenty of falloff on
  each joint and overlap between them" —
  https://github.com/Roblox/creator-docs/blob/main/content/en-us/resources/beyond-the-dark/custom-characters.md).
- Band width heuristic: ~**5–15% of limb length** (plush → wider end, stiff toy →
  tighter); falloff = exponential or inverse-distance kernel, Σw = 1, ≤4 influences.

## 3. Automatic rigging of static meshes/scans

- **Pinocchio** (Baran & Popović 2007): medial-surface skeleton embedding + heat-diffusion
  weights. Canonical auto-rigger.
  https://www.cs.toronto.edu/~jacobson/seminar/baran-and-popovic-2007.pdf
- **Mixamo**: closed production auto-rigger (marker-guided humanoid).
- **RigNet** (SIGGRAPH 2020): GNN joints + hierarchy + geodesic weights, template-free.
  https://arxiv.org/pdf/2005.00559
- **Geometric weight solvers:** Bounded Biharmonic Weights (Jacobson 2011,
  https://igl.ethz.ch/projects/bbw/); Geodesic Voxel Binding (Dionne & de Lasa 2013 —
  shipped in Maya, https://diglib.eg.org/items/3d3458d9-bdf2-41c7-8b84-5da16b5cd637).
- Newer: SkinningNet 2022 (https://arxiv.org/pdf/2203.04746), SkinCells 2025
  (https://arxiv.org/html/2506.14714v1), MagicArticulate 2025
  (https://arxiv.org/html/2502.12135v2), **Make-It-Animatable (CVPR 2025) — takes 3DGS
  directly** (https://arxiv.org/html/2411.18197v3).

## 4. Rigging 3D Gaussian splats specifically

- Consensus: **LBS on Gaussian means**, canonical→posed. Survey:
  https://research.moverse.ai/articles/skinned-gaussian-avatars/skinned-gaussian-avatars.html
- **Mean**: LBS. **Rotation/covariance**: rotate by the bone rotation — blending rotation
  matrices is not a valid rotation, so use weighted quaternion averaging (Moverse) or the
  rotation part of the blended transform; re-orthonormalize covariance if needed.
- **Scale and opacity: untouched** by bone transforms (rotation-invariant; scale travels
  with the mean in the Gaussian's local frame).
- **SH color**: zeroth-order (baked color like ours) needs nothing; first-order SH would
  rotate with the blended rotation.
- Representative pipelines: 3DGS-Avatar (Qian 2024,
  https://www.cvlibs.net/publications/Qian2024CVPR.pdf), RigGS 2025
  (https://arxiv.org/html/2503.16822v1), Instant Skinned Gaussian Avatars 2025 (bind each
  splat to nearest mesh vertex + relative transform —
  https://arxiv.org/html/2510.13978v1), SuGaR (extract mesh, skin the mesh, splats follow
  — https://imagine.enpc.fr/~guedona/sugar/), Gaussian Garments (mesh-mediated cloth).

## 5. Recommended method for the Chimera teddy

1. **Keep the rigid nearest-bone partition as the w=1.0 baseline** — it is exactly rigid
   skinning, the correct floor and our already-passing gate.
2. **Add a smooth LBS band at each joint**: within ~5–15% of limb length of a joint,
   blend between the two adjacent bones with an exp(−d/τ) falloff; ≤4 influences; Σw=1.
3. **Transform per Gaussian:** mean by LBS; rotation by weighted quaternion average of the
   influencing bone quaternions; scale/opacity/color untouched.
4. **Escalation only if measured artifacts appear:** DQS for the band if volume collapses;
   pose-dependent offset net only if fur compression reads wrong; SuGaR mesh-mediation as
   the heavy fallback.
5. **Validation (fits our movie workflow):** render posed orbits; seams → widen band;
   volume loss → DQS; wrong-looking features → check rotation transport, not just means.

Bottom line: our nearest-bone cut is not a dead end — it is the standard rigid baseline,
and the established next step is a narrow smooth LBS band at the joints with proper
quaternion transport of Gaussian rotations.
