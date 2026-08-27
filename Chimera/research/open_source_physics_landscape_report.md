# Open-Source Real-Time Deformable-Body Physics Landscape
## Research report for the Chimera project

**Date:** 2026-08-26  
**Research question:** Which open-source real-time/near-real-time physics methods compete with, or could augment, Chimera’s CA-style local-rule triangle-mesh soft-tissue stack?  
**Classification asked:** COMPETITOR (does what Chimera does), COMPONENT (could be adopted), REFERENCE (published numbers to derive from).

---

## Executive summary

Chimera’s architecture — local-rule dynamics on a triangle carrier, symplectic integration, bone-rig-driven ROM extremes with learned in-betweens, and a custom C++/Vulkan renderer — sits at the intersection of three well-explored literatures:

1. **Position/constraint-based dynamics (PBD/XPBD/Projective Dynamics)** on triangle/shell meshes.
2. **Data-driven deformation and neural skinning** (pose-space deformation, learned correctives, delta mush).
3. **GPU-accelerated robotics simulators** that now bundle FEM, MPM, PBD, and IPC under one scene (Genesis, Newton, MuJoCo Warp).

The genuinely novel Chimera combination is not any single solver, but the **triangle-mesh cellular-automata-style local rules + trained pose-space interpolation from sparse ROM extremes + custom Vulkan render loop**. Many individual pieces have open-source implementations that are mature enough to study, port constraints from, or use as validation baselines. None of them simultaneously (a) run at game frame rate, (b) guarantee visual tissue detail competitive with a hand-tuned CA/triangle stack, and (c) are licensed under a stack compatible with Chimera’s AGPL stance without careful LGPL isolation.

**Bottom line:** the field is converging on exactly the kind of unified, GPU-resident, learned-corrective soft-body pipeline Chimera is building. The main open-source threats/components are **PositionBasedDynamics/Strain Based Dynamics**, **NVIDIA Warp/MuJoCo Warp/Newton**, **Genesis**, **DiffPD/DiffXPBD**, and the established **FEM reference codes (VegaFEM, SOFA, AMD FEMFX).**

---

## 1. Position / constraint-based family

### 1.1 PositionBasedDynamics library (Jan Bender et al., RWTH Aachen)
* **What:** mature C++ library implementing PBD, XPBD, strain-based dynamics, shape matching, FEM-based PBD, rods, fluids, rigid bodies, SDF collision.
* **License:** MIT ([GitHub](https://github.com/InteractiveComputerGraphics/PositionBasedDynamics)).
* **Maturity:** high; ~10 years of development, Python bindings (`pyPBD`), many published papers integrated, graph-color parallelized unified solver.
* **Performance:** CPU multi-threaded; not GPU by default. Designed for interactive, not necessarily high-end-game frame rate on dense meshes.
* **Visual quality ceiling:** cloth/soft-body “visually plausible” quality; Bender’s own docs note PBD is “generally not as accurate as force-based methods but still provide visual plausibility” ([repo README](https://github.com/InteractiveComputerGraphics/PositionBasedDynamics)).
* **Role for Chimera:** **COMPONENT + COMPETITOR**. The closest open-source analog to Chimera’s local-rule triangle dynamics. MIT license means constraints, strain-based dynamics, and shape-matching implementations can be read, ported, or compared directly.

### 1.2 XPBD (Macklin, Müller, Chentanez, Kim 2016)
* **What:** extension of PBD that adds compliance and Lagrange multipliers, making stiffness independent of iteration count and time step.
* **License:** algorithm is public; implementations vary (MIT in PositionBasedDynamics).
* **Maturity:** industry standard (used in NVIDIA Flex, many game cloth solvers, Style3D, etc.).
* **Performance:** GPU-friendly Jacobi variants run cloth/soft body at 60 Hz for moderate meshes.
* **Visual quality ceiling:** game-quality cloth and volumetric soft bodies; artifacts at low iteration counts (stretching, damping).
* **Role:** **REFERENCE + COMPONENT**. The compliance formulation is the canonical way to make local-rule dynamics stable; Chimera should derive its stiffness/compliance mapping from this literature.

### 1.3 Strain Based Dynamics (SBD, Müller & Chentanez 2014)
* **What:** directly constrains Green strain per triangle/tet instead of springs; converges faster than distance constraints.
* **License:** algorithm public; implemented in PositionBasedDynamics.
* **Performance:** faster than basic PBD for similar visual results.
* **Role:** **COMPONENT**. A triangle-mesh strain measure is exactly the language Chimera uses (per-triangle area strain); SBD gives a published way to regularize it.

### 1.4 Projective Dynamics (Bouaziz et al. 2014)
* **What:** fuses constraint projections into a fast local/global solver; equivalent to a quasi-Newton implicit integration.
* **License:** algorithm public; reference code historically from the authors, plus many forks:
  * [Pies](https://github.com/nithinp7/Pies) — constraint/particle-based soft body built on Projective Dynamics.
  * [pratyai/projective-dynamics-2022](https://github.com/pratyai/projective-dynamics-2022) — Python cloth PD.
* **Maturity:** high in research; fewer production game integrations than PBD because it needs a global linear solve.
* **Performance:** real-time for moderate meshes on CPU; GPU versions exist (see §3 GPU-IPC/PD below).
* **Role:** **REFERENCE + COMPONENT**. A more accurate implicit baseline against which to validate Chimera’s explicit/local-rule results.

### 1.5 Shape Matching (Müller et al. 2005)
* **What:** clusters particles, fits a rigid transform to each cluster, pulls particles toward the transformed rest shape.
* **License:** public algorithm; implemented in PositionBasedDynamics.
* **Performance:** very fast, GPU-friendly; recent “parallelized graph-based shape matching on GPU” achieves real-time soft-body dissection ([ScienceDirect 2024](https://www.sciencedirect.com/science/article/pii/S0169260724001676)).
* **Visual quality ceiling:** good for blobby/jiggly bodies, less precise for thin tissue details.
* **Role:** **COMPONENT**. Could augment Chimera’s triangle carrier as a cheap “bulk stiffness” or jiggle layer.

### 1.6 XPBI — PBD with Smoothing Kernels for Continuum Inelasticity (Yu et al., SIGGRAPH Asia 2024)
* **What:** updated-Lagrangian enhancement to XPBD using SPH-style smoothing kernels; handles mud, sand, snow, fracture, plasticity.
* **License:** research code not confirmed; paper is public ([arXiv:2405.11694](https://arxiv.org/html/2405.11694v2)).
* **Performance:** real-time on Apple Vision Pro for 20K particles at 30 fps; millions of particles in offline-quality demos.
* **Visual quality ceiling:** high for elastoplastic and granular materials.
* **Role:** **REFERENCE**. Shows how far local-rule dynamics can be pushed into continuum mechanics without switching to FEM.

---

## 2. FEM family

### 2.1 VegaFEM
* **What:** C/C++ middleware for corotational linear FEM, invertible nonlinear FEM, Saint-Venant Kirchhoff, Neo-Hookean, Mooney-Rivlin on tetrahedral or cubic meshes.
* **License:** 3-clause BSD ([GitHub](https://github.com/starseeker/VegaFEM)).
* **Maturity:** very high; ~50 kLOC, used in many research projects.
* **Performance:** multi-core CPU only; not GPU.
* **Visual quality ceiling:** accurate continuum mechanics, large deformations, stable implicit integration.
* **Role:** **REFERENCE**. Ideal source for material-model equations, tangent-stiffness formulas, and implicit-time-stepping benchmarks. Not a runtime competitor because it lacks GPU.

### 2.2 AMD FEMFX
* **What:** multithreaded CPU library for tetrahedral FEM with plasticity and fracture.
* **License:** MIT ([GPUOpen](https://gpuopen.com/archived/femfx/), [GitHub](https://github.com/GPUOpen-Effects/FEMFX)).
* **Maturity:** v0.1.0, released 2019; sample Houdini/UE4 plugins, but limited ongoing updates.
* **Performance:** CPU-parallel; intended to complement GPU rendering on many-core desktops.
* **Visual quality ceiling:** game-quality deformable wood, metal, gel; not tuned for soft tissue.
* **Role:** **REFERENCE + partial COMPONENT**. The FEM discretization and material models are derivable; the codebase is game-oriented but not actively maintained.

### 2.3 SOFA (Simulation Open Framework Architecture)
* **What:** real-time multi-physics framework with heavy medical/soft-tissue emphasis; FEM, CUDA plugins, haptic coupling.
* **License:** LGPL-2.1 ([GitHub](https://github.com/sofa-framework/sofa), [SOFA site](https://www.sofa-framework.org/)).
* **Maturity:** very high; 16+ years, large research community.
* **Performance:** interactive real-time for surgical scenes (~50 Hz reported); GPU plugins exist.
* **Visual quality ceiling:** clinically oriented soft-tissue accuracy.
* **Role:** **REFERENCE + COMPONENT (with care)**. LGPL requires dynamic linking/isolation; not as clean as MIT/Apache for a tightly integrated engine. Use for published soft-tissue validation numbers and material-law references.

### 2.4 GPU corotational / nonlinear FEM
* **Published interactive GPU FEM exists:**
  * Joldes et al., “Real-Time Nonlinear Finite Element Computations on GPU” ([PMC 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3003932/)) — early CUDA nonlinear soft-tissue brain surgery.
  * Comas et al., “Efficient Nonlinear FEM for Soft Tissue Modelling and Its GPU Implementation within SOFA” ([Springer 2008](https://link.springer.com/chapter/10.1007/978-3-540-70521-5_4)).
  * Trinity College dissertation on co-rotational FEM GPU implementation ([TCD 2015](https://scss.tcd.ie/publications/theses/diss/2015/TCD-SCSS-DISSERTATION-2015-047.pdf)).
* **Role:** **REFERENCE**. Proves real-time nonlinear FEM on CUDA is possible; Chimera can compare its triangle-rule results against these published timings.

---

## 3. Incremental Potential Contact (IPC) and successors

### 3.1 IPC reference implementation (Li et al., SIGGRAPH 2020)
* **What:** penetration-free, inversion-free large-deformation dynamics with a barrier formulation and conservative CCD.
* **License:** main repo open-source reference; reusable **IPC Toolkit** is MIT ([ipctk.xyz license](https://ipctk.xyz/about/license.html)).
* **Maturity:** research gold standard for contact robustness.
* **Performance:** CPU, implicit Newton with CHOLMOD; default time step 0.025 s. Not real-time for complex scenes, but guarantees no tunneling.
* **Visual quality ceiling:** very high for contact-rich elastodynamics.
* **Role:** **REFERENCE**. Defines the accuracy/contact ceiling. Chimera’s local collision response should be sanity-checked against IPC ground truth.

### 3.2 GPU IPC + Projective Dynamics
* **What:** [GrahamZen/Soft-Body-Simulation-CUDA](https://github.com/GrahamZen/Soft-Body-Simulation-CUDA) implements IPC and Projective Dynamics on CUDA.
* **License:** not verified in fetched data; treat as research code until license is confirmed.
* **Performance:** GPU-resident; real-time or near-real-time for modest scenes.
* **Role:** **REFERENCE + possible COMPONENT**. A working GPU IPC/PD baseline to compare against Chimera’s triangle carrier.

### 3.3 Penetration-free Projective Dynamics on the GPU (Lan et al. 2022)
* **What:** interior-point-like contact constraints inside PD; simulates solids and shells on GPU at interactive/real-time rates ([UCLA PDF](https://www.math.ucla.edu/multiples/publication/lan2022pdipc.pdf)).
* **Role:** **REFERENCE**. Shows how to get IPC-like contact guarantees inside a real-time GPU PD solver.

### 3.4 uIPC in Genesis
* Genesis lists a built-in `uipc` solver (unified IPC) among its physics backends ([Genesis World README](https://github.com/Genesis-Embodied-AI/genesis-world)).
* **Role:** **COMPETITOR**. A packaged real-time IPC variant in an open robotics simulator.

---

## 4. Robotics sim engines usable open-source

### 4.1 MuJoCo
* **What:** high-fidelity rigid-body/contact simulator; DeepMind open-sourced under Apache 2.0 in 2022. Added **Flex** deformable-body support (tetrahedral meshes, cloth) — currently experimental.
* **License:** Apache 2.0 ([GitHub](https://github.com/google-deepmind/mujoco)).
* **Maturity:** extremely high for rigid/contact; Flex deformable is newer and less optimized.
* **Performance:** CPU-first; ~1,000 parallel envs with MJX on GPU.
* **Visual quality ceiling:** excellent contact; basic rasterizer (OpenGL) by default.
* **Role:** **COMPONENT**. Best-in-class contact solver and tendon/actuator models; Chimera could use MuJoCo for rigid skeleton/contact validation.

### 4.2 MuJoCo Warp (MJWarp)
* **What:** GPU-accelerated MuJoCo by DeepMind + NVIDIA; part of the Newton project.
* **License:** Apache 2.0 ([GitHub](https://github.com/google-deepmind/mujoco_warp)).
* **Performance:** >70× speedup for humanoids, >100× for in-hand manipulation; batch ray-tracing renderer at millions of FPS for camera passes.
* **Deformable:** Flex rendering supported, solver features still experimental.
* **Role:** **COMPONENT + COMPETITOR**. Strong candidate for batched training/validation of Chimera policies or learned in-betweens.

### 4.3 NVIDIA Warp
* **What:** Python framework that JIT-compiles kernels to CUDA/CPU; includes FEM, MPM, SPH, geometry, differentiable examples.
* **License:** Apache 2.0 ([GitHub](https://github.com/nvidia/warp), [NVIDIA blog](https://developer.nvidia.com/blog/build-accelerated-differentiable-computational-physics-code-for-ai-with-nvidia-warp/)).
* **Maturity:** rapidly maturing; heavily used by Newton/MJWarp.
* **Performance:** CUDA-native; 1M particles in 20 lines of code demo.
* **Role:** **COMPONENT**. Could become the authoring layer for Chimera’s material kernels if the project wants Python-based differentiable prototyping.

### 4.4 Newton (Disney Research / Google DeepMind / NVIDIA, Linux Foundation)
* **What:** GPU-accelerated, extensible, differentiable physics engine built on NVIDIA Warp and MuJoCo Warp, OpenUSD-based.
* **License:** Apache 2.0 ([NVIDIA Developer blog](https://developer.nvidia.com/blog/announcing-newton-an-open-source-physics-engine-for-robotics-simulation/), [Linux Foundation press](https://www.linuxfoundation.org/press/linux-foundation-announces-contribution-of-newton-by-disney-research-google-deepmind-and-nvidia-to-accelerate-open-robot-learning)).
* **Maturity:** beta as of 2025; active development.
* **Performance:** targets large-scale RL and real-time soft-body interaction.
* **Role:** **COMPETITOR + COMPONENT**. The closest industry-backed open-source analog to a unified GPU deformable simulator. Study for architecture and solver-coupling patterns.

### 4.5 Genesis / Genesis World
* **What:** unified multi-physics engine (Rigid, FEM, MPM, Particle/PBD/SPH, uIPC, SAP), photo-realistic Nyx renderer, Quadrants compiler to CUDA/ROCm/Metal/Vulkan.
* **License:** Apache 2.0 ([GitHub](https://github.com/Genesis-Embodied-AI/genesis-world), [PyPI](https://pypi.org/project/genesis-world/0.1.1/)).
* **Maturity:** academic since Dec 2024; now supported by Genesis AI; very high star count, very active.
* **Performance:** 43 M FPS on RTX 4090 for simple rigid scenes (robot learning benchmarks); deformable speeds depend on solver choice.
* **Visual quality ceiling:** Nyx renderer targets photo-realism; physics solvers span the full continuum from PBD to IPC.
* **Role:** **COMPETITOR**. Directly overlaps Chimera’s target of high-fidelity GPU soft-body simulation. The existence of a Vulkan backend path in Quadrants is particularly relevant.

### 4.6 Brax
* **What:** JAX-based differentiable rigid-body simulator from Google.
* **License:** Apache 2.0 ([GitHub](https://github.com/google/brax), [arXiv 2021](https://arxiv.org/abs/2106.13281)).
* **Performance:** massive GPU batching for RL.
* **Deformable:** no meaningful soft-tissue support.
* **Role:** **REFERENCE (for batching/RL)**, not a tissue competitor.

### 4.7 Drake
* **What:** model-based design, control, and verification toolbox (TRI); includes deformable-body FEM and convex MPM/rigid coupling.
* **License:** BSD-3-Clause ([Stack Overflow note by Russ Tedrake](https://stackoverflow.com/questions/75929355/simulate-deformable-objects-with-drake), [arXiv convex MPM coupling](https://arxiv.org/html/2503.05046v2)).
* **Performance:** research-oriented; not game frame rate.
* **Role:** **REFERENCE** for contact/MPC and deformable-body math; not a runtime component.

### 4.8 Bullet / PyBullet
* **What:** mature open-source rigid/soft/cloth physics; zlib license.
* **License:** zlib ([fxguide](https://www.fxguide.com/fxfeatured/bullet_open_source_physics_engine/)).
* **Performance:** CPU, partial GPU cloth abstraction historically planned.
* **Visual quality ceiling:** good for games/VR, but soft-body solver is older than PBD/PD/FEM options above.
* **Role:** **REFERENCE**. A baseline everyone knows; not state-of-the-art for tissue.

### 4.9 NVIDIA PhysX 5
* **What:** open-source CPU physics (BSD-3) with GPU binaries; includes FEM deformable bodies, cloth, fluids. GPU source code released April 2025.
* **License:** CPU source BSD-3; GPU code now open ([NVIDIA blog 2022](https://developer.nvidia.com/blog/open-source-simulation-expands-with-nvidia-physx-5-release/), [Phoronix 2025](https://www.phoronix.com/news/NVIDIA-OSS-PhysX-Flow-GPU)).
* **Role:** **COMPONENT (caution)**. License is compatible, but it is NVIDIA-controlled middleware with a long EULA history. Useful as a feature checklist, less so as a dependency for an independent AGPL engine.

---

## 5. Differentiable physics

### 5.1 DiffPD (MIT CSAIL)
* **What:** differentiable Projective Dynamics with implicit integration and contact.
* **License:** open-source code exists ([mit-gfx/diff_pd](https://github.com/mit-gfx/diff_pd)); associated sim2real fork at [srl-ethz/diffPD_sim2real](https://github.com/srl-ethz/diffPD_sim2real).
* **Performance:** faster adjoint than naive autodiff for soft-body control.
* **Role:** **COMPONENT**. Could train or fine-tune Chimera’s “in-between” deformation network from physics objectives.

### 5.2 DiffXPBD (Stuyck & Chen, Meta Reality Labs Research, 2023)
* **What:** analytically differentiable XPBD; computes gradients w.r.t. parameters for shape, forces, material estimation.
* **License:** research code status unclear; paper public ([arXiv:2301.01396](https://arxiv.org/html/2301.01396v3), [Papers with Code](https://paperswithcode.com/paper/diffxpbd-differentiable-position-based)).
* **Role:** **REFERENCE**. If Chimera wants to learn local-rule parameters from observed motion, this is the canonical formulation.

### 5.3 Does anyone ship game-quality visuals from differentiable physics?
* **Answer:** not as a primary render path. Differentiable simulators are used for:
  * policy/control training (Brax, MJWarp, Newton),
  * material/parameter estimation (DiffPD, DiffXPBD),
  * inverse design (Warp examples).
* Game-quality visuals still come from rasterized/ray-traced meshes, often with learned correctives. Differentiable physics is a **training/validation tool**, not yet a renderer.

---

## 6. Cellular automata / particle methods for elasticity

### 6.1 Cellular Potts Models (CPM)
* **Tools:** CompuCell3D, Morpheus, Tissue Simulation Toolkit (TST), Artistoo ([NIH paper 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8143789/)).
* **License:** varies; TST open source.
* **Performance:** lattice-based, not real-time 3D graphics.
* **Accuracy:** validated for tissue growth, tumor, cell sorting.
* **Role:** **REFERENCE**. Chimera’s “cellular automata-like local rules” are more like PBD/CA hybrids than true CPM, but CPM gives published morphogenetic behaviors to compare against.

### 6.2 SPH-based solids
* **SPlisHSPlasH:** open-source SPH framework; supports corotated elastic SPH solids, deformable solids, rigid-fluid coupling, GPU neighborhood search ([features page](https://splishsplash.physics-simulation.org/features/)).
* **GPUSPH:** CUDA-only open-source SPH.
* **Role:** **REFERENCE + COMPONENT**. Elastic SPH is a meshless alternative to triangle-mesh rules; useful for validating large-deformation behavior and for fluids coupled to tissue.

### 6.3 Peridynamics
* **Tools:** Peridigm (Trilinos-based, open source), PeriDyno (“泛动引擎”, award-winning Chinese open-source project), projective peridynamics for elastoplastic materials (He et al. 2018).
* **Role:** **REFERENCE**. Peridynamics handles fracture and long-range nonlocal elasticity; Chimera could borrow nonlocal interaction ideas for tearing/damage.

### 6.4 Lattice spring models
* **State:** used in biomechanics and haptics; less common in modern graphics.
* **Role:** **REFERENCE**. Published accuracy for soft-tissue haptics exists ([JCGT GPU haptic tissue paper](https://jcgt.org/published/0002/02/03/paper.pdf)).

### 6.5 Material Point Method (MPM)
* **Taichi MLS-MPM:** original SIGGRAPH 2018 code, MIT license ([yuanming-hu/taichi_mpm](https://github.com/yuanming-hu/taichi_mpm)).
* **CRESSim-MPM:** GPU MPM for surgical soft-body with cutting/suturing ([arXiv 2025](https://arxiv.org/html/2502.18437v1)).
* **Warp/Genesis MPM:** built into Newton/Genesis.
* **Role:** **REFERENCE + COMPONENT**. MPM is the state-of-the-art for snow, sand, and large-deformation soft bodies. Not a direct triangle-mesh competitor, but could augment Chimera for environmental/interaction materials.

---

## 7. Skinning / deformation beyond LBS

### 7.1 Dual Quaternion Skinning (DQS)
* **What:** avoids candy-wrapper twisting of LBS, better volume preservation.
* **License:** public algorithm; many open implementations.
* **Role:** **COMPONENT/REFERENCE**. Drop-in replacement for LBS in the bone-rig layer.

### 7.2 Delta Mush / Direct Delta Mush
* **What:** post-skinning smoothing that preserves volume and removes artifacts.
* **Open implementations:** [MeshDeformUnity](https://github.com/PacosLelouch/MeshDeformUnity) (Unity), [Direct Delta Mush paper](https://history.siggraph.org/learning/direct-delta-mush-skinning-and-variants-by-le-and-lewis/).
* **Role:** **COMPONENT**. Could be a cheap runtime corrective on Chimera’s triangle mesh before physics is applied.

### 7.3 Physics-based secondary motion
* **Velocity Skinning** ([hal.science PDF](https://polytechnique.hal.science/hal-03195315/file/velocity_skinning.pdf)) — adds stylized inertia to skinned motion in real time.
* **Spring Decomposed Skinning** ([Wiley CGF 2025](https://onlinelibrary.wiley.com/doi/10.1111/cgf.70209)) — integrates springs into skinning for secondary motion.
* **Role:** **COMPONENT**. Chimera already has physics, but these methods show how to add cheap “life” on top of a bone rig.

### 7.4 Neural skinning / learned deformation correctives
* **NeuroSkinning** (Liu et al., SIGGRAPH 2019): automatic skin binding with graph networks; code on [GitHub](https://github.com/FuxiCV/NeuroSkinning).
* **Neural Blend Shapes** (Li et al., SIGGRAPH 2021): end-to-end rigging, skinning, and blend-shape generation; code on [GitHub](https://github.com/PeizhuoLi/neural-blend-shapes).
* **DeepDeformation / Fast and Deep Deformation Approximations** (Bailey et al. 2018): neural corrective on top of cheap skinning; early implementation on [GitHub](https://github.com/PeterZhouSZ/DeepDeformation).
* **Dem Bones** (EA): extracts LBS from example poses; code on [GitHub](https://github.com/electronicarts/dem-bones).
* **Role:** **COMPONENT + COMPETITOR**. Chimera’s “trained in-betweens from ROM extremes” is exactly this idea applied to a physics carrier. These repos provide architectures, training pipelines, and evaluation metrics to study.

---

## 8. Muscle simulation open source

### 8.1 OpenSim
* **What:** musculoskeletal simulation with Hill-type muscles, Simbody dynamics.
* **License:** Apache 2.0 API; free for research/teaching ([OpenSim Capabilities](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53087561/OpenSim%27s+Capabilities)).
* **Maturity:** very high; clinical/biomechanics standard.
* **Performance:** real-time for inverse kinematics; forward muscle-driven simulations slower than game frame rate.
* **Role:** **REFERENCE**. Source for Hill-type muscle-tendon parameters, muscle paths, and validation data.

### 8.2 MyoSim
* **What:** models mechanical properties of striated muscles (force, shortening, power).
* **License:** open source ([awesome-biomechanics list](https://github.com/modenaxe/awesome-biomechanics)).
* **Role:** **REFERENCE** for sarcomere-level muscle mechanics.

### 8.3 Graphics-oriented volumetric muscle methods
* **Finite Volume Methods for Skeletal Muscle** (Teran et al., SCA 2003) — classic; code not widely available but paper public ([Stanford](https://graphics.stanford.edu/papers/fvm_sig03/)).
* **Physically-based Muscles and Fibers Modeling** (Turchet et al., EG 2017) — volumetric muscle primitives + fiber fields for animation ([Eurographics PDF](https://diglib.eg.org/bitstream/handle/10.2312/egsh20171008/033-036.pdf)).
* **GPU real-time muscle simulation** (Navarro-Hinojosa et al., 2020) — meshfree muscle model on GPU ([MDPI](https://www.mdpi.com/2076-3417/10/6/2099)).
* **Role:** **REFERENCE**. Show the art of embedding muscle fibers in a volumetric mesh and driving them with activation; Chimera could derive fiber-field rules for its triangle carrier.

---

## 9. Candid novelty assessment: where is Chimera new?

| Aspect | How original is it? | Why |
|--------|---------------------|-----|
| **Triangle-mesh local-rule soft-body dynamics** | Incremental, not revolutionary | PBD, XPBD, SBD, and shape matching already do local per-triangle/per-particle updates on triangle meshes. PositionBasedDynamics is a direct open-source analog. |
| **Per-triangle area strain + shared-edge springs** | Implementation choice | These are standard discrete shell/solid mechanics ingredients. |
| **Symplectic integration + Barnes-Hut gravity + bond/wall forces** | Engineering synthesis | Well-known methods combined in a custom engine. |
| **Bone-rig-driven ROM extremes** | Common in animation | Motion-capture driven pose-space deformation is standard. |
| **Trained in-betweens from sparse ROM extremes** | Genuinely novel combination | This is the Chimera signature: using a learned pose-space map to interpolate between physically/kinematically sampled extremes on a triangle carrier. Closest analogs are neural skinning, neural blend shapes, and Fast & Deep Deformation Approximations, but those are not tied to a CA local-rule physics loop. |
| **Custom C++/Vulkan renderer for splat/mesh shells** | Engineering differentiator | Many engines use Vulkan; few combine it with a hand-tuned tissue solver. |
| **“Publishedology” / no parameter sweeps** | Methodological differentiator | Strong alignment with the project’s stated doctrine, but not a technical novelty per se. |

**Conclusion:** Chimera is not reinventing the physics literature, but it is building a **unique integration** of (a) lightweight local-rule triangle dynamics, (b) learned pose-space interpolation, and (c) a custom Vulkan render loop. The open-source field is converging on similar unified stacks, so speed of execution and visual tuning will determine competitiveness more than the underlying equations.

---

## 10. Top 5 techniques / codebases to study first

| Rank | Item | Why first? | URLs |
|------|------|------------|------|
| 1 | **PositionBasedDynamics library + Strain Based Dynamics** | Closest open-source analog to Chimera’s triangle-mesh local-rule stack; MIT license; read constraints, SBD, shape matching, collision handling. | [GitHub](https://github.com/InteractiveComputerGraphics/PositionBasedDynamics), [README fetched](https://github.com/InteractiveComputerGraphics/PositionBasedDynamics) |
| 2 | **NVIDIA Warp + MuJoCo Warp + Newton** | The industry-backed GPU+differentiable pipeline most similar to where Chimera is heading; Apache 2.0; study solver coupling, batching, and material kernels. | [Warp GitHub](https://github.com/nvidia/warp), [MJWarp GitHub](https://github.com/google-deepmind/mujoco_warp), [Newton announcement](https://developer.nvidia.com/blog/announcing-newton-an-open-source-physics-engine-for-robotics-simulation/) |
| 3 | **Genesis / Genesis World** | Direct competitor with unified physics (FEM/MPM/PBD/IPC), Vulkan-capable compiler, and a photo-realistic renderer. Study its solver architecture and performance claims. | [GitHub](https://github.com/Genesis-Embodied-AI/genesis-world), [PyPI](https://pypi.org/project/genesis-world/0.1.1/) |
| 4 | **DiffPD / DiffXPBD** | Differentiable position/projective dynamics are the right mathematical framework to *train* Chimera’s in-betweens and local-rule parameters from objectives and data. | [DiffPD arXiv](https://arxiv.org/abs/2101.05917), [DiffXPBD arXiv](https://arxiv.org/html/2301.01396v3), [DiffXPBD Papers with Code](https://paperswithcode.com/paper/diffxpbd-differentiable-position-based) |
| 5 | **VegaFEM + SOFA + AMD FEMFX** | Published, validated FEM baselines for material laws and soft-tissue accuracy. Use these to derive constants and to sanity-check the triangle-rule physics. | [VegaFEM GitHub](https://github.com/starseeker/VegaFEM), [SOFA](https://www.sofa-framework.org/), [AMD FEMFX](https://gpuopen.com/archived/femfx/) |

---

## Quick-reference classification table

| Name | License | Maturity | Game FPS? | Tissue detail? | Role |
|------|---------|----------|-----------|----------------|------|
| PositionBasedDynamics | MIT | High | Moderate | Good | COMPONENT/COMPETITOR |
| XPBD / SBD | public | High | Yes | Good | REFERENCE/COMPONENT |
| Projective Dynamics | public | High | Near | Very good | REFERENCE/COMPONENT |
| Shape Matching | public | High | Yes | Moderate | COMPONENT |
| VegaFEM | BSD-3 | Very high | No | Very good | REFERENCE |
| AMD FEMFX | MIT | Medium | CPU only | Good | REFERENCE |
| SOFA | LGPL-2.1 | Very high | Interactive | Clinical | REFERENCE/COMPONENT* |
| IPC Toolkit | MIT | High | No | Excellent | REFERENCE |
| GPU IPC/PD (GrahamZen) | unverified | Research | Near-real-time | Very good | REFERENCE |
| MuJoCo | Apache 2.0 | Very high | Yes (rigid) | Basic (Flex) | COMPONENT |
| MuJoCo Warp | Apache 2.0 | High | Yes | Basic (Flex) | COMPONENT/COMPETITOR |
| NVIDIA Warp | Apache 2.0 | High | Yes | Good | COMPONENT |
| Newton | Apache 2.0 | Beta | Targets yes | Good | COMPETITOR/COMPONENT |
| Genesis | Apache 2.0 | Active | Yes | Good | COMPETITOR |
| Brax | Apache 2.0 | High | Yes | None | REFERENCE (batching) |
| Drake | BSD-3 | High | No | Research | REFERENCE |
| Bullet | zlib | High | Yes | Moderate | REFERENCE |
| PhysX 5 | BSD-3 (+GPU src) | Very high | Yes | Good | COMPONENT (caution) |
| DiffPD | MIT-ish | Research | No | Good | COMPONENT |
| DiffXPBD | research code | Research | No | Good | REFERENCE |
| SPlisHSPlasH | open | High | Yes (fluids/solids) | Moderate | REFERENCE/COMPONENT |
| Taichi MLS-MPM | MIT | High | Yes | Good | REFERENCE/COMPONENT |
| OpenSim | Apache 2.0 API | Very high | No | Clinical | REFERENCE |
| Neural Blend Shapes | open code | Medium | Yes (inference) | High | COMPONENT |
| Delta Mush / DQS | public | High | Yes | Good | COMPONENT |

*SOFA LGPL requires dynamic linking/isolation for an AGPL project.

---

## License compatibility note for Chimera

Chimera’s target stack is **AGPL-compatible**. The safest dependencies are **MIT, BSD-3/2, Apache 2.0, and public-domain/algorithms**. **LGPL** (SOFA) can be used via dynamic linking or separate processes but taints the linking boundary. **GPL** code should be avoided inside the engine. **PhysX** is BSD-3 for CPU and now open GPU source, but it is a large NVIDIA-controlled body of code; adopting it as a core dependency conflicts with Chimera’s stated goal of avoiding closed/proprietary engines and keeping the stack independently verifiable.

---

*End of report.*
