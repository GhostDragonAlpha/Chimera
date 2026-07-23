# Chimera — Project Manual

> **THE GOAL: a space game**, fed by a pipeline that turns real 3D scans and authored
> assets into labeled, re-composable **object genomes** — shape + material, with serial
> numbers — so one person can build at a scale that normally needs a studio.

> The Unreal Engine pipeline is retired. UE-only documentation was deleted 2026-07-23;
> remaining UE references inside current documents were stripped in place.

## NEW AGENT? START HERE

1. `Construction/SPLAT_DNA_WORKFLOW.md` — the live pipeline, with `PROVEN` / `DESIGNED` /
   `FRONTIER` marked honestly on every stage, plus a full file inventory (§7.5).
2. `WorldModel/ML_PIPELINE.md` — the generative half: SplatVAE, the three training paths,
   nanite-style LOD, infinite world, cellular rules, physics universe. **This is the
   implementation of MEMBRANE PROGRAMMING below.**
3. `docs/EXPERIMENTAL_METHOD.md` — ten rules for diagnosing a live system without fooling
   yourself. Read before debugging anything.
4. **The GPU is mandatory.** Never run rendering, segmentation or DNA recovery on CPU.

## Key Paths

| Path | Purpose |
|---|---|
| `Construction/` | The DNA pipeline — extraction from scans and authored assets |
| `WorldModel/` | The generative half — VAE, LOD, infinite world, physics |
| `WorldModel/clay.py` | Procedural ship hulls — `SHIP_PARAMS`, 24 parameters |
| `WorldModel/training_data/downloads/` | The corpus, ~43 GB, gitignored |
| `docs/EXPERIMENTAL_METHOD.md` | How to diagnose a live system |
| `docs/DOC_AUDIT_2026-07-23.md` | Outstanding documentation defects, ranked |
| `pi-servers/` | Local LM server launchers (live copies at `E:\pi-servers\`) |
| `web/view.html` | Interactive 3D orbit viewer — output the operator can see |
| `core/lm_gateway.py` | The single LM Studio endpoint arbitrated across PROCESSES: a fair FIFO file-queue (docs/world/lm_queue/) so concurrent agents wait their turn instead of dogpiling into timeouts. All generation call sites (critic/solver/spiral_forks/ralph_loop/coin_verifier/generator_guard) route through `lm_urlopen`. Serializes by default (kills the timeout); `CHIMERA_LM_CONCURRENCY=N` raises in-flight slots if LM Studio is configured for parallel/batching. **THE MODEL IS ADOPTED, NEVER PINNED AND NEVER LOADED (2026-07-14): `resolve_model()` reads whatever LM Studio currently has resident and retargets the outgoing body at it** — so changing the model for the whole operation is just "load a different model in LM Studio", no config/env/code. **If nothing is loaded it raises `NoModelLoaded` — it does NOT fall back to a default and JIT-load it.** A "fallback" is a pinned model wearing a hat: it means silently pulling a multi-GB model the operator never asked for. The operator decides what runs; the studio only adopts. Never re-pin a model id and never make the request path load or evict: the box shares ONE GPU with other clients (a `pi` agent harness), and two clients each forcing a different model evict each other mid-load and BOTH die with "Engine protocol startup was aborted". Vision-capability is the operator's responsibility — **never gate on LM Studio's `llm`/`vlm` or `capabilities.vision` flags, they are WRONG for these builds** (vision was added after the fact); `Python/lmstudio_client.py` used to reroute screenshots to a different "vision-capable" model on that bad flag — removed. `python -m core.lm_gateway status` prints which model will be used; `evict` manually frees VRAM (never automatic). |
| `core/council.py` | **THE COUNCIL — the Holy Ghost** (2026-07-15, rewritten 2026-07-19). Two genuinely different minds in dialogue: FAST (responsive MoE, ~3.6B active) and DEEP (thorough dense 27B), swapped dynamically through `core.lm_gateway`. Previously used DS4/DeepSeek-V4; the cost of 80GB RAM + 1.6 t/s no longer justified when both models run on the GPU at 50+ t/s. `CHIMERA_FAST_MODEL` and `CHIMERA_DEEP_MODEL` env vars control which models are swapped. If unset, adopts whatever LM Studio has resident. `-m core.council "<topic>" [--rounds N] [--record]` — `--record` posts synthesis to CAPCOM + Surprise node. **SECOND-SYSTEM REVIEW:** `council.review(feature, ...)` asks what evidence would have to exist (deep model) and checks the graph deterministically. Advisory by default (`CHIMERA_COUNCIL_GATE=block` hardens). |
| `docs/GLM_52_DEEP_MODEL.md` + `E:\pi-servers\START GLM-5.2.cmd` | **THE DEEP MODEL — GLM-5.2, 744B MoE int4, 357 GB, fully offline** (documented 2026-07-23). A *third* tier below LM Studio: OpenAI-compatible on **`http://127.0.0.1:8080/v1`, model id `glm-5.2-colibri`**, started explicitly with `E:\pi-servers\START GLM-5.2.cmd` (CPU mode, **0 VRAM**, so LM Studio keeps the GPU). **READ THE SPEED SECTION BEFORE CALLING IT: ~0.26 tok/s** — 64 tokens is 4 minutes, 500 tokens is half an hour, and a 2,900-token prompt costs 6–18 min of *prefill before the first token*. **Cap `max_tokens`, keep the prompt short, and set a client timeout ≥1800 s.** Never put it on a loop, a gate, a nightly job, or any per-file pass — it will not finish. **It is NOT `core.lm_gateway`** (that arbitrates LM Studio and adopts whatever is resident); do not route gateway traffic at it or a 0.26 tok/s model behind a FIFO will stall every waiting agent. **Three faults found and fixed 2026-07-23, all documented with repro:** (1) `Stream ended without finish_reason` = the server's **300 s `--queue-timeout` firing mid-prefill while the engine was still working** (proven: engine reached layer 25/78 *after* the 429) — `--queue-timeout 3600` is in the scripts and is LOAD-BEARING; (2) instant `500 engine_error` = **more than one `coli serve` instance** on :8080, since `openai_server.py:1036` relabels every exception with that one generic message; (3) CPU-vs-GPU is a deliberate trade, not an oversight — GPU measured **0.289 vs 0.26 tok/s for 13–18 GB of VRAM**, and LM Studio does 50+ tok/s on that same VRAM. **Prefill tuning improved ~10× (14→1.38 s/layer) and moved decode almost none** — decode is what you wait on, so don't re-litigate the expert-tier settings expecting tokens/sec. **An LLM is never a why-chain terminal** (`core/why.py`): being big and slow does not make its answer PHYSICS or THE HUMAN. |
| `core/dyad.py` | **THE DYAD — two-mind development partnership** (2026-07-19). The dyad drives development: it reads the brief (docs/BRIEF.md), decides what to build next, hands the instruction to the lead agent, the lead executes, reports back, and the dyad decides the next move. Loop continues until the human stops it manually. Uses the same model-swap mechanism as council: FAST (MoE) proposes, DEEP (dense) pressure-tests, FAST synthesizes into a concrete instruction. `drive()` returns the next instruction; `report()` records the outcome. No task board — organic, piece-by-piece growth. `CHIMERA_FAST_MODEL` and `CHIMERA_DEEP_MODEL` env vars select the two models. |
| `../Construction/REFERENCE_TO_NOUN.md` | **Photo → textured 3D tree** — the RECIPE (run `python Construction/photo_to_tree.py --photo <abs> --name oak`; do NOT improvise the design). Real photo → complete orbitable 3D tree wearing the photo's own bark/foliage, via template **markers** × real photo **patches** (the CROSS). **The template is the subject's MORPHOLOGY — a TOLD concept, not programmed: name the form (decurrent oak vs excurrent poplar vs palm rosette) and distribute markers by its growth rules BEFORE placing any; that is what completes the unseen back/crown. Full cited concept catalog (19 concepts by the FOUR jobs a morphology does for a template): `Construction/MORPHOLOGY.md`.** Template level-of-detail (`--lod`) sets the ceiling on output quality. Pieces: `Construction/cross.py`, `Chimera/core/trainables/tree_appearance.py`, `Construction/gsplat_fit.py`. Discovered 2026-07-22. |
| `../Construction/SPLAT_DNA_WORKFLOW.md` | **Scan → object genome → game** (2026-07-22 — the pivot from photo→tree to **3DGS-scan → DNA**). An object = **morphology-DNA** (shape) + **material-DNA** (the splat CONFIGURATION — joint *distributions* of size/shape/angle/color/opacity, NOT averages, and a RANGE not a value). Recognized genomes get **serial numbers** (a codebook) → compress / identify / regenerate ("compression is intelligence", made literal = vector quantization). **HONEST STATUS marked per stage.** PROVEN this session: `Construction/ksplat_io.py` (.ksplat decoder), `gpu_render_torch.py` (GPU rasterizer on the 4090), SAM2 multi-view lift (`multiview_sam_lift.py`), `morphology_signatures.py` (6/6 synthetic shapes), `material_dna.py` (recovered known oak/copper genomes to ~1% incl. metal 0.04 vs 0.97), `take_dna.py` (bark/moss/ground distinguishable — **wood grain measured as aligned splat long-axes**). **GPU IS MANDATORY — never run render/segment/recover on CPU.** FRONTIER: relighting (joint material↔light is ill-posed; structural DNA is light-clean, colour DNA is baked), completing unseen geometry. `gsplat` kernels won't JIT here → torch rasterization + explicit voting instead. **AMENDED 2026-07-23 — four facts a successor must not re-derive: (1) TWO INTAKE METHODS — a genome does NOT have to come from a scan. MEASURED (scans → inverse rendering → *reality*) vs AUTHORED (GLB/OBJ PBR maps → read directly → *an artist*); authored is EASIER because PBR maps are already light-separated. "Authored" ≠ "stylized" (Quixel is authored AND photoreal); THE STYLIZED METHOD is the sub-case where you harvest across a CURATED set sharing a look — the resulting distribution **IS your art direction as an enforceable genome**, the consistency a solo dev otherwise cannot hold. Both intakes feed ONE codebook. (2) FORMAT CALIBRATION — because both feed one codebook, **an uncalibrated container forks the same material into two serial numbers.** PROVEN: `load_ply` applied `sigmoid()` where INRIA stores colour as the SH DC coefficient (`rgb = 0.5 + 0.28209479177387814·f_dc`) — p10 0.143 vs the true 0.000; fixed, regression test `calibrate_formats.py`, all channels now agree to 4 dp. SAME BUG CLASS IN MESHES: classic `.mtl` is **Blinn-Phong, not PBR** — `Ns` is shininess (`roughness ≈ √(2/(Ns+2))`) and there is **no metalness**. Harvest ranking: GLB/glTF ⭐ > USD > FBX > OBJ+MTL > PLY > STL. STILL OPEN: `.ply`/`.splat` axis conventions differ — rotation-invariant DNA is safe, orientation features are not. (3) THE EMISSIVE GENOME — light is not matter: a laser/engine-glow EMITS, so albedo/roughness/metalness are meaningless. `{colour, intensity, radial falloff, elongation, core gradient, lifetime}`. **A splat IS the right primitive** (anisotropic blob + falloff = a plasma bolt); `flame.splatv`/`sear.splatv` are REAL captured emissive volumes — a laser is a fire genome stretched along one axis and recoloured. (4) SPATIAL VOTING IS REFUTED — 82.5%→82.8%, flat: the bark/ground confusion is genuine material-DNA OVERLAP, not spatial noise; the real lever is grain/orientation coherence (bark 0.53 vs ground 0.39, never in the classifier). CORPUS: 35 GB license-clean — 28 splat scans + 39 INRIA models (13 scenes) + 489 CC objects (20 categories) + 4D FX + **611 camera poses** (bonsai 292, bicycle 194, stump 125), which make **bicycle the first real multi-view material-recovery target**. Nearly every LARGE splat corpus on HuggingFace is `gated:auto` (account required, no ungated mirror); **Objaverse and INRIA are the exceptions and carry the most value per byte.**** |

## Hardware and its traps (measured 2026-07-23)

- **RTX 4090, 24.5 GB VRAM · 128 GB RAM.**
- `C:` PCIe NVMe (OS + pagefile) · `D:` SATA SSD · `E:` spanned QLC NVMe pair · `F:` USB SSD.
- **`E:` is fast sequential (4,782 MB/s) and slow random (352 MB/s at 4 MB).** MoE model
  reads are random — sequential benchmarks mislead here.
- **Never put a memory-mapped model on `C:`** — it competes with `pagefile.sys`, and SSDs
  degrade past ~80% full. Measured 50% slower in place than the benchmark predicted.
- **System Restore was entitled to 15% of `C:` (279 GB)** and silently consumed ~190 GB
  during large transfers, failing two of them. Cap it (admin):
  `vssadmin resize shadowstorage /for=C: /on=C: /maxsize=25GB`

## Conventions

- **Git: commit directly to `master`, never feature branches.** State branch + SHA on every
  push. Git management is delegated — keep the tree clean, push without asking each time,
  surface only destructive actions.
- **Large artifacts stay gitignored** — model weights, the corpus, `web/*.npz`.
- **Show real output.** Renders the operator cannot see do not count.
- **Opinions must be science-grounded** — a judgement is trusted when a physical constraint
  forces it. Render the evidence, look at it, name the physics.
- **Record what failed, with the number** (`docs/EXPERIMENTAL_METHOD.md` §7).

## Session Memory

Stored at: `C:\Users\allen\.claude\projects\E--PythonChimera\memory\`
Indexed in `MEMORY.md` there.

---

---

## MEMBRANE PROGRAMMING AND UNIVERSAL SIMULATION ARCHITECTURE (2026-07-21)

### The New Programming: Training Patterns & Scene Hierarchy Configuration
Setting up the training patterns is the new computer programming. In traditional programming, you write explicit `if/else` statements and loops to tell a computer exactly what to do. In membrane programming, we don't write traditional code—we define the **training patterns**, the **energy principles**, and the **mathematical constraints** that govern how energy and matter flow through the system.

### Multi-Genre Verification Gates (Spectroscopy & USGS/JPL Spectral Libraries)
The pipeline runs two parallel extraction paths:
- **The Visual Path:** Extracts geometric and topological patterns (hexagonal tessellation, sinuous curvature, fractal branching).
- **The Spectral Path:** Extracts reflectance curves and absorption features from USGS/JPL spectral libraries (silicate absorption bands at 1.4µm, 1.9µm, 2.2µm; vegetation "Red Edge" at 700-1300nm; iron oxide red/orange reflection 600-700nm).

When a potential membrane label is identified, it must be **cross-referenced and verified** by both the visual path and the spectral path. If the visual and spectral data align, the membrane is **verified by PHYSICS**, not just human visual interpretation.

### Physics-Based Modular Control Systems ("LEGO Puzzle" Connection Shapes)
The "connection shapes" are physics interfaces—the specific ways energy and matter flow between modules:
- **Gravitational Anchor:** Newtonian gravity, mass attraction — *All modules* snap to the planet's gravity field.
- **Spectral/Energy Port:** Light interception, "Red Edge" spectral signature, PAR distribution — *Biological modules* connect to the Sky/Sun energy source.
- **Hydrodynamic/Hydration Port:** Buoyancy, fluid drag, water hydration absorption bands (1.4µm, 1.9µm) — *Watercraft modules* connect to River/Ocean surfaces; *Root systems* connect to soil moisture.
- **Aerodynamic/Atmospheric Port:** Lift, drag, thrust, airflow patterns (Bernoulli's principle) — *Aircraft modules* connect to the atmosphere/sky layer.
- **Substrate/Geological Port:** Mineral absorption, soil topography, friction coefficients — *Building foundations, Tree roots, Character controllers* connect to the Ground/Surface layer.

### Verb Over Nouns Philosophy
The core of the system is the **verb**, not the noun/item:
- **THRUST:** applying energy to create motion (keyboard/input → thrust vector ports)
- **BALANCE:** adjusting Center of Gravity vs. Center of Thrust to stabilize torque
- **GROW:** following the flow of energy and matter from seed to canopy (phyllotaxis, fractal branching)
- **CONNECT:** snapping physics modules together via compatible connection shapes
- **SCAN:** using hyperspectral sensors to analyze chemical composition (spectral signatures)
- **NAVIGATE_ORBIT:** calculating and adjusting thrust to achieve stable orbit (Keplerian mechanics)
- **GROW_ECOSYSTEM:** planting seeds and watching biological networks grow based on environmental conditions

### Exploration Product / Universal Simulation Architecture
An educational exploration product — a universe simulator built on physics, not pre-scripted game mechanics. Players explore the universe from home by EXPERIENCING the flow of energy and matter through verbs.

**Hierarchy:**
- **Level 1 (Energy Source/Sky):** Solar granulation + Night sky stellar distribution → outputs photons and spectral environment.
- **Level 2 (Matter Source/Ground):** Basalt, Quartz, Sand dunes, Mud cracks → outputs soil minerals, topography, and water availability.
- **Level 3 (Transformation Engine/Biological Growth):** The seed-to-tree procedural growth → takes energy and matter from Levels 1 & 2, applies the training patterns, and outputs a procedurally grown tree structure with canopy.
- **Level 4 (Observer/Camera View):** Director's camera perspective → places the camera by the tree to view the Earth's ground, sky, and moon cohesively.
