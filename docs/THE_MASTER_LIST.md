# THE MASTER LIST — everything this is for, one page

*Rewritten 2026-08-27 by operator decree ("change the master list to fit my
vision"). The 32-continuation history is compressed, not erased: every claim
below names its run record or commit. When docs fight, run records beat prose;
`python tools/orient.py` prints live state.*

## 1 · THE ONE CLAIM (what this is for)

**A holographic engine: the triangle is BOTH the structure of reality AND the
mirror.** One database row per triangle — it occludes, collides, carries mass,
runs in the CA — and it answers light *from the perspective of the viewer*,
the only perspective that matters. Cellular automata give the matter life and
movement; a trained per-triangle light field gives it frost. The product is
**the game** — art so perfect in the reality of its light that people ask
*"how did he make something so beautiful with just triangles alone?"*

**The economics (operator doctrine):** the engine is open-sourced for
humanity — AI unlocks all doors, so there is no durable money in *how* a
thing is done; the machine will be absorbed into the membrane of ML within a
year or two. The only value is the art that comes out of it, and that value
is the artist's taste, amplified. Taste is the one input no absorption can
copy, which is why the human is a terminal of this system, not a user of it.

## 2 · THE ARCHITECTURE (operator decrees — settled, do not reopen)

- **THE RUNTIME LAW (2026-08-28): the runtime loop is GPU / CA-field only.
  Python is never inside a per-frame path.** Python's two legal roles: the
  derivation bench (measuring static constants — sets, axes, weights) and
  one-shot setup (posting them, then exiting). Runtime state lives in GPU
  buffers; runtime math is compute shaders. Reference: `hinge.comp`.
- **Triangles ARE the CA substrate.** The cubes are invisible Cartesian
  address scaffolding; **each cube is its own Gaussian space**. The cubes
  give every triangle an address; the triangles are what we want.
- **A triangle IS a Gaussian.** Covariance identity verified numerically
  (max err 0.0016 vs Monte Carlo). 10 of the 14 splat parameters are DERIVED
  from the geometry (address, frame, extent); 4 are free — the material
  state, the only numbers a model ever learns per triangle.
- **Consume-to-recreate.** Eat a mesh, decompose it into the triangle
  database, regrow it CA-friendly with a bone axis. **Openings stay open**
  (sockets, mouth) — closing a true opening is the defect.
- **The bone axis.** Voxels are only scaffolding to grow the stick figure;
  triangles are addressed relative to bones. Determinism = ROM extremities +
  CA-filled interior, harnessed by the bone rig.
- **Hinge arrays.** A joint is not an object; it is a region where the
  substrate's law changes. Flexion axes DERIVED from bone geometry; muscles
  are CA contraction signals; gait is a standing wave, not a keyframed clip.
- **Water.** The cube columns hold height + flow; a CA exchange rule moves
  it; mass conservation is the falsifier. Creatures interact for free —
  occupied columns exclude water; the wading monkey is the same rows meeting.
- **The frost is distilled ray tracing — 2D splats only (operator decree:
  "we're only going to be working on the 2D version").** Not volumetric 3DGS:
  each splat is a 2D Gaussian living ON its triangle's plane — a surfel whose
  angle IS the triangle's angle, which is exactly what makes reflection
  simulation derivable (the mirror's tilt is known, never fitted). Train the
  light answer offline (path tracer or photographs), run it at lookup cost.
  "Ray tracing without ray tracing cores." Held-out LIGHT directions are the
  door, not held-out views — novel views alone make a texture, not a NeRF.
- **The dyad.** Silicon builds; a separate vision eye (LM Studio's resident
  model via `core/lm_gateway`) judges blind orbit movies; disagreements get
  measured; taste bottoms out in the operator and nowhere else.
- **Rule 0.** Statement / prediction / falsifier BEFORE the build. Derived,
  never chosen. Honest about the unmeasured. Docs append-only (this page's
  rewrite is by decree).

## 3 · THE LINES (every thread, state, next gate)

| # | Line | State | Next action | Home |
|---|------|-------|-------------|------|
| L1 | **The corpus** — 5 license-verified monkeys as watertight per-part contract GLBs | DONE (gate 5/5, `d7a8655e`, `d142f207`) | consumed by L3 | `docs/THE_ARTISTS_SOLID.md` |
| L2 | **The substrate view** — one-mask skin+bone, engine 1px wireframe + overlay slot | DONE — dyad **NO COMPLAINTS 0.95** (`34938671`) | reference pipeline for every later visual | `docs/THE_ARTISTS_SOLID.md` |
| L3 | **THE REGISTRY** (Phase 4a) — triangle centers = Cartesian addresses; cube edge DERIVED from max edge-adjacent center distance; dual graph; cube index must reproduce the neighborhood 100% | **DONE — PASS 100%/100% agreement+reachability on all 5 contract GLBs** (`994bb4e0`, report `.tmp/monkey_assets/recon/tri_ca_report.json`); derived cube edges span four decades across the corpus (0.0068–0.39 per part) from geometry alone; falsifier never fired | consumed by L5/L6/L7 — the substrate exists | `docs/THE_ARTISTS_SOLID.md` |
| L4 | **THE BIRTH RULE** (Phase 4b) — triangle-native wound repair, no voxel rasterization; 8955's 41 boundary loops close, sockets measured OPEN | **DONE — literal wording FALSIFIED, occupant-veto derivative PASS** (`994bb4e0`): no separating voting range exists (first socket closes at 0.0074, all wounds need 0.0523; 4/6 sockets die); veto scale = loop's own median edge, measured separation 0.35 vs 3.3; born 2,454, sockets open by vertex-edge identity, ray-parity 0.965/0.955 body + 1.0/1.0 eyes, gate green; dyad 3 rounds NO COMPLAINTS 0.95/0.96 | the repaired bone-addressed mesh now feeds L6; divergence recorded: the far-side vote needed a range the asset says doesn't exist — veto by identity is the derived substitute | same |
| L5 | **THE FROST** (BET-F2) — distilled relighting on the substrate | specced (`8b36e2b6`); falsifier SPECCED by Big Pickle packet, AMENDED by hy3 audit (`agent_logs/hy3/frost_audit_01.md`): 8-D latent/triangle + 3×64 MLP; bar = MEASURED baseline (not a literature floor); ≥32–64 equal-area stratified held-out lights, PSNR reported per AO/polar band; referee SPP ≥8k (else the gate measures Monte-Carlo noise); weight int-quantization for bit-exactness UNVERIFIED | needs L3+L4 (or runs scratch-only on one corpus part); held-out LIGHT is the door; per-triangle field cannot see self-shadowing — AO stratification makes the limit measurable | same |
| L6 | **HINGE ARRAYS** (BET-J1) — CA-state joints, derived flexion axes | specced (`8b36e2b6`); physics dyad CLOSED (hy3 packet 02 + Big Pickle confirmation audit `physics_audit_02.md`): ring-as-Dirichlet + smooth-ARAP skin CONFIRMED; ν=0.49 openly CHOSEN; per-pair phase bands + hysteresis gait transition CONFIRMED; **T_vol rides to construction as a MEASUREMENT — claimed O(ε²)≈4.8e-4, honest bound 3ε_max≈6.6e-2, decided by measured C_iso over one ROM ARAP solve**. **CONSTRUCTION IN FLIGHT (quinn-3.8): Stage A PASS — rigid rotation exact, edge drift 2.11e-14 (944-tris lower-leg set, full ROM); Stage B fixed (probe17 leg-column shell: 474 ring tris, 1 comp, 0 bone-adjacent); **TORN-LEG FIX LANDED 2026-08-28 (main agent direct, `agent_logs/kimi/leg_fix_01.md`, `.tmp/tri_hinge2.py`): the torn right leg was a set-classification bug — two defects measured: (1) the naive spatial window caught a 179-triangle thigh slab reaching hip height (rigidly rotating it = the ribbon); (2) unwelded coincident seam weld group 5080 (two vertex indices at the exact same rest position, inner knee) tore 1.17e-2 under rotation — invisible to the index-boundary-scoped R2 scan because the seam shares no index edge. Fix: geodesic-on-dual-graph Voronoi sets from rod-endpoint seeds (the chimera packet's folded-limb guard law) + R2 weld scan widened to ALL weld groups. Both knees green: L 3097 tris (symmetric diff 0 vs the repaired reference set), R 3113; above-hip 0/0; boundary loops at knee height; split weld groups 0 after R2. TORN-SHEET (new earned check) PASS both legs every ROM step: free skin 5/5 welded comps, 0 broken weld groups, max dihedral 90.0° < rest-derived bound 131.8°; F2 drift ≤1.4e-3, inside the honest 6.6e-2 bound. HONEST NEGATIVES: the earlier recorded F1=0 was a PLACEBO (trimesh 4.4.7 has no Trimesh.collisions — the hasattr guard silently returned []); the soup carries 1,461 pre-existing REST self-intersections (124/131 in the hinge regions); the deformation-induced F1 delta (L +199 / R +47) is the rigid+frozen model's fold artifact — F1=0 stays OPEN until the ARAP skin lands (still stubbed in tri_hinge.py). Renders verified by main-agent read: `.tmp/leg_fix/right_leg_strip.png` + classification panels — clean single-axis hinge, no ribbon**. **AXIS CORRECTION + LIVE MARCH 2026-08-28 (operator close-read cycle): the probe14 per-side axes (L [0.859,−0.066,0.508], R [0.664,−0.077,0.744]) spend 0.51/0.74 of their unit length LATERAL — the shank swung out sideways ("hacky sack", operator's words); cause: ill-conditioned measurement (tibia ∥ femur at rest). CORRECTED LAW: knee axis = the INTER-KNEE LINE n = normalize(J_R−J_L) = [0.9997,−0.0244,0] (well-conditioned, measured from the derived joint centers); sign from "flexion moves the foot POSTERIOR" with anterior measured from the eye-socket part centroid (z=+0.958; tail at z=−4.288) ⇒ +θ both knees; ROM magnitudes kept from probe14, re-sweep about the corrected axis OPEN (CHOSEN-UNVERIFIED). RETRACTED: the geodesic-blend visual skin (hop weights on the index graph can't cross the welded sole-junction seams — foot disconnected, operator rejected; ARAP skin stays the open membrane path). KEPT per operator: the rigid R2-welded wrap — "the way the knees wrapped around was correct, only the angle was wrong." LIVE DEMO in the engine window: both knees marching full ROM, sagittal fold, no tint (control sets invisible per decree), operator orbit/zoom/pan live during animation (engine `/mesh_bin` cam_radius≤0 = keep-camera patch). **OPERATOR CLOSE-READ CYCLE 2 (2026-08-28): "both knees bend correctly now" — the rigid wrap + corrected axis is the APPROVED state, kept verbatim; the two visible spike ("control") triangles per knee = a boundary-straddling strip at the inner knee (measured edge stretch 28.5×/27.1× L, 23.6×/22.9× R at 85% ROM; triangles with 1–2 of 3 vertices in the rotating set) — HIDDEN FROM THE RENDER per operator decree (dropped from the posted index buffer; they sit in the knee crease so the fold covers the gap). RETRACTED experiments: spike-strip absorption into the rotating set (made the knee a rigid block — "messed up the look") and the welded-graph blend (drawer item alongside the ARAP skin membrane). Input starvation FIXED: the main loop pumped ONE Windows message per frame — at the driver's 12 fps repost rate orbit/zoom starved (worked idle at 1000 FPS); queue now drained per frame**. **SKIN-MOVING BLEND + MAPPED-BUFFER STREAMING (2026-08-28, operator decrees): "when I bend my knee a ball forms, it's round — use MANY triangles to make the radius" and "show all of them" (hiding = holes, rejected): every vertex near the joint rotates by θ·w_i about the measured J — w = clip(1 − d_to_set/0.3, 0, 1), R_FALL = 0.3 = the recorded ring-band slab half-width (the joint's own measured extent; the earlier 42-hop falloff swallowed the torso and was retracted; weights diffuse across welded seams so the foot can't disconnect). All triangles drawn. Front of knee operator-approved; back of knee "deforms in a little too far" — full-ROM scan + dyad analysis (extremes-first) running. ROTATION ROOT CAUSE found and killed: the driver's per-frame full re-upload forced vkDeviceWaitIdle 12×/s — the main thread blocked on the GPU queue and input starved (the queue-drain alone couldn't fix that). Engine now keeps the mesh vertex buffer HOST_VISIBLE + persistently mapped; `/mesh_bin` slotmode ≥100 = memcpy-only update (no GPU idle, no camera). Synthetic-drag test mid-march: 6.6% view change — ROTATION LIVE; engine free-runs ~1800 FPS while streaming at 120 fps driver rate**. **DENSE DYAD SCAN (2026-08-28, operator: "not just extremes — every range in between"): 68 back-of-knee frames at 4° steps, one picture per dyad call, one report per frame (resume-safe incremental report `.tmp/rom_scan_dense/dyad_report.json`). Verdict: the fold reads CLEAN across the whole ROM except a localized pinch band — L knee ~92–108°: "pinches and folds inward too far, sharp concave crease" at 92°/96°/104° in the posterior-3/4 re-check (the pure-posterior camera occludes the fold past ~90° — one earlier flag at 100° was that artifact; framing limitation recorded). R knee clean everywhere its fold stayed in frame. Cause named, no knob patched: the per-vertex arc rotation drags POSTERIOR skin inward at mid-flexion — the fold side needs area redistribution (the open ARAP-skin membrane item) or instant-center migration (real knees are four-bar linkages; the instant center moves posteriorly with flexion — derivable from the bone rods, future membrane work). The pinch is CONFIRMED, BAND-LOCALIZED, cause-named; fix deferred to the membrane, not another midnight knob**. Engine B1+B3 FIXED same commit: B1 = WM_SIZE never handled + OUT_OF_DATE/SUBOPTIMAL swallowed (window froze at last present while FPS logged) — now WM_SIZE → pending-resize consumed in frame(), OUT_OF_DATE rebuilds the swapchain immediately, present result checked, suboptimal rebuilds at frame end (falsifier PASS: window captures advance through two camera moves AND a window resize, ~1050 FPS); B3 = 0-byte upload NULL-buffer crash on empty POST (killed the engine on every overlay clear) — empty upload now CLEARS the slot (verified: empty overlay POST → HTTP 200, engine alive, window still advancing)** | needs the repaired bone-addressed mesh (`.tmp/monkey_assets/recon/8955fb5..._birth.glb`, SALLY_body_0 34,538 tris); monkey knee 0→140° (L measured −2.50…+144.94, R −3.62…+114.82), zero self-intersection; δ integer-quantized for bit-exactness | same |
| L7 | **WATER** (BET-W1) — river on the cube scaffolding | specced (`8b36e2b6`); physics dyad CLOSED; **all three named measurements LANDED on the real 37 corpus parts** (`agent_logs/hy3/water_measure_01.md`, data `.tmp/hy3_water/`): C_sw MEASURED per part ∈ [0.047, 0.493], median 0.18 — audit's 0.56 eigenvalue correction confirmed, but 0.56 AND 0.76 both died to data (irregularity, not just slivers, drives it down; per-part values mandatory); slivers real (lmin/med down to 0.022, 4 parts throttle 15–45×) ⇒ BUILD SUBCYCLING with per-part C_local; integer quantum Q=A_min·L_part, corrected leapfrog verified on a 2-triangle dual (drift 3.3e-15, clamp load-bearing, bit-constant ΣV) | needs L3's cubes (exists); **construction-ready AND decision-free** — membrane written (`agent_logs/hy3/water_packet_03.md`, ACCEPTED): test case SALLY_body_0 with its measured C_sw=0.07121/Q=5.1e-9, mass drift falsified bit-exact, level tolerance traced to Q, metamorphic downhill-on-rotate, canonical edge order for bit-identity; CHOSEN-UNVERIFIED (α, ΔT, g, H, S, C_AW) each name their experiment; queued behind L6 per attack order | same |
| L8 | **THE FIRST CHIMERA** — teddy-bear / monkey 50-50 split down the midline | pipeline proven at dyad 0.65 with a procedural stand-in (P9, `41893558`); **CHIMERA PACKET 01 ACCEPTED 2026-08-28** (`agent_logs/bigpickle/chimera_packet_01.md`): seam = dual-graph edge-cut on DERIVED sagittal planes (teddy x=0.0358, NOT x=0 — P9 cut the shoulder; monkey δ = first experiment); identity = discrete per-triangle scalar (Stovold Model B), blend in perception weights only; occupant-veto classifies the fused seam as OPENING (genomes can't birth into each other); mass-balance may DERIVE split ratio x* over the 50-50 decree. **TEDDY CANDIDATE FOUND (freeagent2, 2026-08-28):** Sketchfab UID `33ef76f2cd5d43aa9fea7779ea8041ce`, CC0, 94k tris, plush silhouette — CANDIDATE ONLY, must pass the same 6-view + hole + topology qualification the monkeys passed before it enters the corpus | the creature the whole stack points at; **hy3 AUDIT LANDED (`agent_logs/hy3/chimera_audit_01.md`), ALL ADOPTED — 1 FATAL: C2/C4 blend bands contradict (1-hop α vs 2-hop tanh; MeshNCA citation decorative); X1 teddy normal asserted not derived + no folded-limb guard (crouch defeats genome-by-x-sign); X2 seam-as-opening unverified (vacuous if truly fused; tol=0.005 CHOSEN); X4 x* needs unmeasured ρ, 5% trigger CHOSEN; X5 bleed falsifier needs L5+L6 — static graft buildable now, closure waits; "QUOINED" tag fixed. Revision (packet 02) issued → **CHIMERA PACKET 02 DELIVERED (`agent_logs/bigpickle/chimera_packet_02.md`, 466 lines); hy3 CONFIRMATION AUDIT (`chimera_audit_02.md`): X3 RESOLVED (Band A perception vs Band B render — one residual D-WEXP: Band B must blend the CA-EVOLVED s_i, not source latents, or the render hides a sick seam), Y3–Y6 CONFIRMED (fused-with-boundary + derived tol, 50/50 declared decree, staged falsifiers), 1 new trivial FATAL: R2a cross-product sign ((−1,0,0), not (1,0,0)) → micro-revision applied + VERIFIED; **CHIMERA DYAD CLOSED 2026-08-28 — all items resolved/confirmed; the one survivor rides to construction as a named measurement: the render MUST decode the CA-evolved s_i, never source latents (pretty-seam-hides-sick is now a testable requirement)**; honest gaps: monkey δ, kernel R (needs L6), latent blend compatibility | `docs/THE_MASTER_LIST.md` §heritage |
| L9 | **THE GAME** | the artifact of value | arrives when L1–L8 produce a world | — |

## 4 · LANDED FOUNDATIONS (verified — do not redo)

- **T2 triangle carrier LANDED:** the triangle is a SOLID element — area
  rigidity `k = 0.75·K_BOND/A0` (derived, zero free numbers) + R7c bending.
  RUN A rel err 2.5e-9; 1000 ticks finite; energy drift 0.5% ≤ 1% net of
  radiation; max strain 2.19% honesty line; curvature-exterior
  domain-restricted, BOTH meshes pass (`models/cad_bear/ca_run.json`).
- **Octree lane:** B1 njit build byte-identical to the referee, 44.5→3.5 ms;
  persistent pool landed (`3ee05fb`); the live CA walk uses it (~12×). The
  visible pinned core the operator kept killing runs for is GONE.
- **Bone rig PASS 12/12 (P7):** ROM + CA interior slaved to a rig; mesh
  follows LBS exactly — J1's direct ancestor. **Tissue systems PASS (P6):**
  skin/muscle/bone as separate triangle systems with interface continuity.
  **In-between harness 27/27 (P8).**
- **Physics body lane CLOSED (Phase 0, 2026-08-27):** ports 19/19+2 REFUSED,
  primitives 7/7, actions 9/10 + RHYTHM_DRIVE's earned FALSIFIED (the test
  left failing, mechanism proven, no tolerance widened); S4 determinism
  52,472 stepped states bit-identical; theDeterminism PROVEN via MCP.
  Doctrine that carries forward into J1: allometry (no human-table number on
  another body), hard stops own the boundary, ligaments arrest the approach.
- **The dyad machinery:** LM Studio resident vision judge (adopt-never-pin),
  settle-capture fix (movies are real movies), `senses.watch` orbit protocol.
  **The operator's web viewer (2026-08-28, `.tmp/webviewer/`):** three.js
  orbit viewer + live `/engine_frame` pane on http://localhost:8088/
  (server: `.venv-hy3d/Scripts/python.exe .tmp/webviewer/server.py`;
  vendored three.js r170, offline-capable; self-tested screenshot shows
  the repaired monkey, 36,630 tris). The native Vulkan window is no
  longer the development viewport.
- **THE MACHINE, probed 2026-08-28 (`agent_logs/freeagent/env_probe_01.md`):**
  RTX 4090 24 GB (driver 610.47, Vulkan 1.4.341); **all three frost-relevant
  extensions PRESENT — VK_NV_cooperative_vector (2–4× decode path), DP4a
  (deterministic fallback), VK_EXT_mesh_shader**; torch 2.5.1+cu124 CUDA-ON
  in `.venv-hy3d`; mitsuba 3.9.1+drjit installs clean (dry-run PASS);
  mujoco 3.10 on system python; LM Studio ALIVE serving qwen3.8 27B;
  32 cores, 1.3 TB free. CONTENTION NOTE: the resident 27B model holds
  ~21.5 GB VRAM (llama-server) + ~1.15 GB engine — training jobs schedule
  around it or shrink. Ground truth
  no longer needs the llvm-CPU fallback: CUDA/OptiX is the fast referee.
  **Probe 02 (`agent_logs/freeagent/env_probe_02.md`):** cooperative-vector
  rev 4, subgroup 32, nvdiffrast ABSENT, torch CUDA confirmed;
  **Blender MISSING** (winget candidates: Blender 5.2.1 / LTS 4.2.16 /
  MS Store — install is an operator decision, the R10 artist door is not
  on this box); **probe-02's VRAM table and workgroup counts REJECTED as
  misparse** (42 GB process entry on a 24.6 GB card; count=3 absurd —
  re-measure issued).
  **Probe 03 (`agent_logs/freeagent/env_probe_03.md`), the remediation —
  ACCEPTED:** compute limits real (workGroupCount [2³¹−1, 65535, 65535],
  size [1024, 1024, 64], invocations 1024, shared 48 KB); **Vulkan SDK
  1.4.328.1 PRESENT** (glslangValidator + glslc); VRAM instruments
  disagree HONESTLY — nvidia-smi physical: 0.66 GB free; torch: 23.3 GB
  free of a 25.8 GB "total" (> physical ⇒ CUDA-on-WDDM counts shared
  memory in its pool). **Operational law: nvidia-smi PHYSICAL is the
  number; while the 27B eye is resident the trainer gets ~0.7 GB —
  training runs either with the model paged out, paged (slow), or
  shrunk.**
- **LICENSE LEDGER (freeagent2 probe, 2026-08-28,
  `agent_logs/freeagent2/teddy_license_01.md` + follow-up
  `license_followup_01.md`):** 5 corpus monkeys CC-BY-4.0
  and OpenIllumination CC BY 4.0 (credit line: `liu2024openillumination`)
  — commercial OK but **attribution REQUIRED:
  the game must ship an attribution file** (release requirement, recorded);
  MatSynth per-material via `metadata.license` (CC0+CC-BY mix; CC0 subset
  is frost-training-safe); **Hunyuan3D RESOLVED: commercial YES but
  TERRITORY-EXCLUDES EU/UK/South Korea + >1M MAU triggers a Tencent
  license; Tencent claims no rights in outputs (§6b) ⇒ doctrine:
  hy3-generated creatures are RESEARCH/STRESS-TEST ONLY — the shipped
  chimera builds from license-clean consumed assets (CC0 teddy, CC-BY
  monkeys)**; cellular-automata-as-mechanic: no IP issue.
  **Teddy page-confirmed CC0, 94.3k tris / 40.9k verts, author Gabriel
  Ryan / New Horizon Homes Inc — download needs the operator's Sketchfab
  login, then qualification (6-view + holes) through the real viewer.**

## 5 · HONEST NEGATIVES (recorded, never papered)

- **Real primate mocap does not exist publicly** (free-agent probe
  2026-08-28): every open "monkey/gorilla" clip (CMU subjects 28/80/120)
  is a HUMAN actor pantomiming. The CPG-derived gait was already the
  doctrinal route — it is now the ONLY route, and the dyad + the gait
  packet's phase/energy falsifiers are the only gait judges we will
  ever have. No mocap reference will bail us out.
- **T13 SFC octree FALSIFIED** — structurally valid, 24× less accurate than
  the adaptive referee and slower; not a drop-in (`gate_octree_sfc.json`).
- **B2-A prange octree FALSIFIED 0.93×** — threads engaged, still no win;
  the 24-core build question stays OPEN.
- **RHYTHM_DRIVE (action) FALSIFIED as stated** — the drive CAN move the
  frequency in this regime; successor theory (cadence + the ligament wall)
  parked for the physics lane.
- **BET-T2 literal birth-rule wording FALSIFIED by its own predicted
  falsifier** (`tri_birth_literal.json`): no separating voting range
  exists on the raw 8955 soup — closing all 35 wounds (r=0.0523) seals
  4 of 6 eye sockets (first closes at r=0.0074). Wounds-vs-features is
  not a distance question, exactly as the research annex predicted; the
  occupant-veto derivative (identity, not distance) earned the PASS.
- **Substrate-view bugs that were mine, not geometry's:** two-centroid
  overlay misalignment; contaminated dyad reference frame. Both recorded in
  `THE_ARTISTS_SOLID.md` with the lesson: when instrument and eye disagree,
  suspect the display transform first.
- **Engine presentation bugs QUEUED for the construction crew:** frozen
  window with the render loop alive at ~800 FPS (present/swapchain stall,
  not a dead sim — operator closed it, relaunched clean); teardown leaks
  a VkPipelineLayout + debug messenger on every exit (validation layer
  fires on each rebuild); **B3 zero-allocation CRASH (2026-08-28):
  vkAllocateMemory with allocationSize=0 on an empty upload (zero-triangle
  mesh or overlay) cascades invalid-memory errors and kills the process —
  guard: reject/guard empty uploads before allocation.**

## 6 · RETIRED / PARKED

- **UE pipeline EXCISED** (doctrine: nothing closed-source; ~1000 files,
  history retains all).
- **P-A stand lane PARKED** — blocked structurally (story ledgers hollow in
  this checkout); not dead, not gating anything above.
- **"Seconds held at forward = 0.5" RETIRED as THE metric** — that was the
  walk-first era. Every membrane now carries its own falsifier as the gate;
  the project's north star is the operator's sentence in §1.

## 7 · THE ATTACK ORDER

1. ~~L3+L4 — Phase 4~~ **DONE (`994bb4e0`)** — the substrate stands;
   everything below now builds on it.
2. **L6 — hinge arrays** — the monkey bends both knees, live in the
   operator's window, operator-approved ("both knees bend correctly now";
   the fold is a skin-moving ball, all triangles drawn). Remaining before
   close: the ARAP skin for the pinch band (in flight), ROM re-sweep about
   the corrected axis (open measurement).
3. **L5 — the frost** (the mirror answers light; beauty begins).
4. **L7 — water** (the world gets a river).
5. **L8 — the chimera** (the first creature, dyad-judged).
6. **L9 — the game.**

### THE BACKLOG (maintained — every open item, its owner, its state)

| # | Item | Owner | State |
|---|------|-------|-------|
| B1 | **ARAP skin for the L-knee pinch band (92–108°)** — fold-side area redistribution | main agent | **FALSIFIED 2026-08-28** (`agent_logs/kimi/arap_skin_01.md`): plain ARAP (welded-node graph, uniform Laplacian, batched-SVD local-global, derived arc-length band 0.759) flags PINCH at **all 7** band angles in the head-to-head dyad; the blend flags 3, cleans 3, borderlines 1. Plain ARAP's energy minimum IS a crease — the blend stays the shipping law. 0 broken welds every step (welded-graph structure holds). Residual blend flags narrow to ~88°/108–112° (±8° dyad noise). Next candidates if revisited: smooth ARAP bi-Laplacian (the membrane's actual spec), cotan weights, fold-side weight shaping |
| B2 | **ROM re-sweep about the corrected inter-knee axis** — current limits were swept about the old tilted axes (CHOSEN-UNVERIFIED) | `.tmp/_hinge_probe15.py` | **CLOSED 2026-08-29, moved to H6** — corrected-axis limits L [−1.56°,+145.39°], R [−2.33°,+140.75°] recorded in `docs/THE_ARTISTS_SOLID.md:619` |
| B3 | **Instant-center migration (four-bar linkage knee)** — the lawful deeper fix if ARAP redistribution is insufficient; derivable from the bone rods | unassigned | OPEN — future membrane |
| B4 | **Engine B2 teardown leaks** — validation fires at shutdown (VkPipelineLayout + debug messenger) | main agent | **CLOSED 2026-08-28** — messenger stored + destroyed before the instance, graphics `pipeline_layout_` destroyed at shutdown |
| B5 | **Engine idle spin** — no mesh loaded ⇒ busy loop at ~6M FPS burns a core | main agent | **CLOSED 2026-08-28** — `engine.idle()` + paced loop; idle now ~118 FPS |
| B6 | **Dyad scanner framing at high flexion** — pure-posterior camera occludes the fold past ~90° | main agent | **CLOSED 2026-08-28** — scanner default is the posterior-3/4 view (8.0, 0.7, 0.18) |
| B7 | **L7 water reference solver** — CPU numpy, decision-free per `agent_logs/hy3/water_packet_03.md` | kimi subagent (agent-32) | **CLOSED 2026-08-28 — ALL 6 FALSIFIERS PASS**: mass drift 0 bit-exact, non-negativity (both unclamped placebos fired — check proven failable), bowl level 5.39e-6 ≤ T_level 0.01463 (derived), metamorphic ρ=0.99979, two-seed bit-identity, cube veto; solver `.tmp/tri_water.py`, report `agent_logs/kimi/water_ref_01.md`; honest negatives: render/dyad stubbed, occupancy synthetic, CHOSEN constants named |
| B8 | **Ling fur audit** — F1 fur×frost interface question | Ling | NON-DELIVERY recorded; the interface answer stands in fur packet U3 (frost lives on the outermost shell; one latent shared across shells) — formal audit deferred to fur construction |
| B9 | **Teddy download + Blender decision** — Sketchfab login (operator action), Blender install verdict | operator | Blender CLOSED as UNNEEDED — frost packet 02 E1 converts GLB→PLY with trimesh, no Blender in the pipeline; teddy download remains the one true operator action |
| B13 | **Frame stutter / glitch diagnostics** — GPU contention + driver discipline | main agent | **CLOSED 2026-08-28** — measured: llama-server at 65% GPU (23.7/24.6GB VRAM) = the contention; glitching was duplicate drivers (drivers now DIE when the engine is unreachable); HTTP accept-loop death fixed (one transient accept error used to kill the listener forever); engine frame-cap + 1ms timer + frame-time histogram in the FPS line; driver at 1ms timer, steady ~81 posts/s |

### THE NEXT HARD QUEUE (2026-08-28 — ordered; each row has its spec, its reference, and its falsifiers)

| # | Hard thing | Spec / reference | Done when |
|---|-----------|------------------|-----------|
| H1 | **Frost AO pass** — per-triangle ambient occlusion, R=1024 rays (derived: 0.5/√R ≤ 0.016), ε = 1e-4·D; bands exposed/mid/occluded at 1/3, 2/3 | frost packet 02 E2 | **CLOSED 2026-08-29** — `.tmp/frost_gt/ao.npy` (36,630 tris, mitsuba CUDA ray scene, seed 7 deterministic): AO mean 0.690, bands exposed 26,769 / mid 2,132 / **occluded 7,729 (21%)**; MAXT 2.0·D vs 4.0·D two-point check = **0.0 mean abs diff** (the one CHOSEN control validated); 206 degenerate normals counted, not hidden |
| H2 | **Frost B0 baseline** — 8-D latent/triangle + 3×64 MLP, fp32, N=1 frame pinned to the true normal, L1-in-log, on the GT batch; the bar = MEASURED B0_occl (never a literature floor) | frost packet 02 E3 | **CLOSED 2026-08-29 — B0 = 39.62 dB, B0_occl = 39.32 dB** (200k steps, batch 16k, cosine; `.tmp/frost_b0.py`, `b0_report.json`, `b0_model.npz`). The pre-registered [29,35] dB expectation is FALSIFIED upward: the local per-triangle field sits AT the SPP-8192 GT noise ceiling (~39 dB) even in the occluded band — occl 39.32 ≈ global 39.62, mid band 47.7. Dataset: 7,524 visible (view,tri) pairs × 192 lights from the 1,536-render GT (id maps via the sensor's own `sample_ray` — pixel-perfect registration, no guessed ortho scale). PSNR pixel-count weighted per-triangle means, choice recorded |
| H3 | **Frost falsifier dispatch** — frosted_occl ≥ bar−1 → engine integration; miss ≤3 dB → dual-graph neighborhood latents (tri_ca 100% neighbor); miss >3 dB → per-triangle 8-D premise FALSIFIED | frost packet 02 E6 | **CLOSED 2026-08-29 — PASS → ENGINE INTEGRATION.** E4.2 ablation (`.tmp/frost_e42.py`, `e42_report.json`; int4 latents per-channel affine over trained rows, int8 weights per-output-row symmetric): occluded-band W0 39.32 / WL 39.41 / WL+WI 38.73 → **C = 0.60 dB ≤ X = 1.0 → ship int weights** (bit-exact DP4a decode viable); frosted_occl 38.73 ≥ bar−X 38.32 → **F1 PASS**. Honest notes: int4 latent cost concentrates in the exposed band (−3.0 dB), occluded band moves < 0.1 from latent quantization (WL slightly ABOVE W0 — quant jitter vs noisy GT); weight int8 costs only ~0.7 dB more |
| H4 | **Water runtime + the visible river** — macro steps on the engine's clock (CA-field), wetness tint kernel, W4 surface displacement render | runtime packet 02 V4 + water packet 03 W4 | **CLOSED 2026-08-29 — BIT-EXACT AT RUNTIME RATE + VISIBLE POOLING.** (1) `water_record_macro_step()` extracted from `water_run()` (batch `/water_step` path re-verified bit-exact, all 21 states); the clock runs on the render thread inside `frame()` (`POST /water_clock {on,steps,dt,inj_target,inj_count}`, constant source — no HTTP per step, states slot 0 = latest V, `water_clock_steps_total_` for bookkeeping). **Clock gate: 136 macro steps at 590 steps/s, full V array bit-identical to the golden CPU run with the same constant injection, ΣV = 6800 = 50×136 exact, min 0.** (2) W4 surface render `water_vis.comp`: cell t == whole-mesh face 2092+t (PROVEN by `.tmp/water_align_check.py` — all 34,538 faces index-exact vs the hinge driver's `/mesh_bin` upload); wet tris displaced d=V·Q/A along the geometric normal into an atomically-compacted vertex buffer, drawn `vkCmdDrawIndirect` after the mesh draw; mesh-buffer lifetime via `water_vis_desc_dirty_` lazy rebind; `/water_vis_state` readback probe kept. Fixed water blue (0.15,0.35,0.75) per W4 — the "wetness tint kernel" is a reserved push constant, appearance belongs to the frost packet. (3) Visual: 1,429+ wet cells pooling on the crown/back and spreading (`.tmp/water_vis/v3_*.png`), tracking the POSED mesh while it marches. **FPS 291–292 with clock (2 steps/frame) + vis on, ft avg 0.80 ms, zero frames >16.7 ms** — no collapse vs the ~240–270 hinge baseline |
| H5 | **The fold residual** — smooth ARAP with the bi-Laplacian term (the L6 membrane's actual spec, never built) OR fold-side weight shaping inside the blend; dyad re-scan 88°/108–112° | physics packet Q4 + B1 falsification record | **CLOSED 2026-08-29 as MEASURED-BOUNDED, shaping FALSIFIED.** The measurement chain (`.tmp/fold_bench2.py`/`fold_diag.py`/`fold_project.py`/`fold_validate.py`, JSONs beside them): (1) **F2 volume PASS everywhere** — max drift 3.5e-4 ≤ T_vol 4.4e-4 across both knees' full ROM. (2) F1 penetration (exact Möller, rest-baseline subtracted): L max **0.0278 units @130°** (peaks BELOW max ROM), R 0.0092 @114.82 — all intersecting pairs are fold-skin-vs-fold-skin (`mov 11` — the blend's arcs bunch the band against itself behind the knee; no moving-into-stationary collisions in the zone). (3) **The derived push-out shaping is FALSIFIED** (`.tmp/fold_validate.json`): separation-projection field, canonical pair order, per-vertex quadratic fit — the projection never converges (60-iter cap hit at every non-trivial angle), corrects the WRONG verts (5/1639 L, 1/1641 R), leaves penetration identical at every angle, fit residual 0.0375 ≈ the correction scale. Not shipped; the blend stays the law. (4) **Dyad dense scan (68 frames, 4° step, back-of-knee view, one report per frame): 67/68 CLEAN; single pinch flag at L 100°** ("folds in a bit too tightly, fairly sharp crease") — the one residual the operator saw. (5) Gate lesson recorded: per-edge relative strain needs a floor vs MEDIAN edge length — near-degenerate rest edges (welded twins) explode the naive metric (L read 7.6e7 with zero visual defect). Residual fix is named: **H11 smooth ARAP** |
| H11 | **Smooth ARAP (bi-Laplacian) knee skin** — the L6 membrane's actual spec (physics packet Q4.2, arXiv:2501.10335): C¹ across the hinge ring kills the fold bunching the blend leaves (H5 record). λ derived from tolerated spike height ε_spike, never 0.95-by-citation. First gate: CPU head-to-head vs the blend at the H5-flagged angles (88°/100°/108–112°) with the same dyad protocol; then the GPU bi-Laplacian solve as a CA-field kernel | physics packet Q4.2 + H5 falsification record | **CPU GATE RUN 2026-08-29 — F2 volume FALSIFIED intrinsically, NOT SHIPPED, blend stays the law** (`agent_logs/kimi/smooth_arap_01.md`, `.tmp/smooth_arap{,_gates,_dyad}.py`). λ DERIVED = 0.05 (ε_spike = h̄/2 = 0.062 from the sub-sampling argument, CHOSEN-UNVERIFIED; smallest λ with ring spike < ε at 100°+130°; paper's 0.95 is 100× more smoothing than the tolerance needs). Wins: F1 pen 2–4× under the blend at 88/100/110/130 (0.0044 vs 0.0159 @100), F3 strain under at every angle, F4 ring spike 3–7× under, dyad prefers it (2/12 vs 7/12 flagged reads; blend's 100° pinch is a STABLE 4/4 instrument reading). **Fires the F2 falsifier: the solve SHRINKS volume −1.3e-3 @100 … −3.4e-3 @144.94 vs T_vol 4.4e-4, same order at λ 0.05 AND 0.95 — the bi-Laplacian energy is not volume-conserving and λ cannot fix it.** Also recorded: ε_spike = h̄/2 FALSIFIED as a detectability tolerance (λ=0.05 passes it yet the dyad flags 100° 2/3 reads); cotan is dead on this recon for iterative solves (18,932 negative weights → limit cycles λ≲0.2; R4/uniform operator + clamped-PSD covariance is the working choice, θ=0 exact to 3e-14); plain ARAP has no stable fixed point at the fold (limit cycle ~h̄/2); the dyad at 100° is noise on near-clean candidates (byte-identical renders flip PINCH↔CLEAN) → future "flag gone" criteria need ≥3 reads. Next stage is NOT the GPU kernel — it is **volume-preserving smooth ARAP** (volume-projection post-step or a volume term; H5's push-out was intersection projection, a different constraint) with the VLM-detectability experiment for ε_spike named. **STAGE 2 (volume-preserving) RUN 2026-08-29 — law (b) WINS, BEATS the blend; law (a) FALSIFIED** (`agent_logs/kimi/volp_arap_01.md`, `.tmp/volp_arap.py`/`volp_diag.py`/`volp_dyad.py`). Two derived laws, falsifiers stated pre-run: (a) post-step uniform radial scale of the band about its centroid restoring V=V_rest exactly (cubic root) — FALSIFIED on all prongs (the band is ~0.1% of the closed surface so dV/ds≈0.016; exact volume costs |s−1| = 0.039…1.89, F1 pen explodes to 0.17–0.43, spike 1.0–1.4 — a global blunt Jacobian for a local deficit); (b) volume term IN the solve — one Lagrange multiplier μ per solve on ΣV=V_rest, re-linearized each local-global step, KKT by Schur complement off the same factorization (two extra backsolves) — **PASSES F2 at EVERY angle (|dV| ≤ 6.4e-7 ≤ T_vol) and keeps every H11 win**: F1 pen < blend at every flagged-zone angle (0.0065 vs 0.0159 @100; 0.0172 vs 0.0272 @144.94), F3 under blend everywhere, no new crease (the honest F4 reference is the CONSTRAINED C¹ solution: crease 0.043–0.057 ≈ H11 ±0.005; the vs-unconstrained-ref reading charges the smooth volume-restoration displacement, ≤0.033, as if it were a crease — metric lesson recorded), dyad prefers it (3/9 vs 6/9 flagged reads; blend's 100° pinch still stable 3/3 — 7/7 cumulative — (b)'s 100° modal split 2/3 flagged as H11). One defect carried, named not tuned: a stable limit cycle at exactly 130° (res locks at 2.02e-2 ≈ h̄/6 through 300 iters; gates green at the cycled state; 144.94° converges 9.1e-8 @64 iters) — follow-up is under-relaxation/Anderson on the constrained step. **Volume-preserving smooth ARAP (law b) is the new knee-skin law candidate; the GPU bi-Laplacian kernel becomes the next stage and MUST carry the Schur constraint row (one scalar reduction per iteration), not a post-pass** |
| H12 | **Frost GT view coverage** — the 8 GT views trained only 2,756/36,630 triangles (7.5%); untrained latents decode muted-but-wrong on unseen regions (H9 honest gap). Extend the GT sweep to a Fibonacci view sphere (same SPP 8192, same 128+64 lights, same E2.3 report), retrain B0, re-run E4.2 + the fixed-point budget | frost packet 02 E1 + H9 coverage note | **CLOSED 2026-08-29 — v3 TRAINED + INTEGRATED, coverage 80.7%.** Root cause: mitsuba's ortho sensor maps the film to a ~2-unit window with a rigid `look_at` — every prior GT render was CROPPED to a central slab (idmap v0: tris y 4.5–6.79 of 0–10); fix derived `to_world = look_at @ scale(extent×1.05)`, verified whole-body. All renders re-done: **32 views (26 whole-body = 8 azimuthal + 18 Fibonacci, + 6 head-zoom)**. Coverage **29,543/36,630 unique trained triangles (80.7%)**; residual = dense-head sub-pixel + crouch-cavity interior (recorded). **v3 numbers (`b0_report_v3.json`, `e42_report_v3.json`, `b0_model_v3.npz`): B0 = 31.51 dB global / B0_occl = 33.56 dB** (the packet's [29,35] band holds; the cropped v1 39.62 was the easy slab); E4.2 v3 occluded W0 33.556 / WL 33.553 / WL+WI 33.494 → **C = 0.062 dB ≤ X → ship int weights, E6 PASS**. **Engine integration (H9 pipeline re-run on v3, hot `/frost_bin` re-upload, no restart): fixed-point budget C_total = 0.137 dB ≤ 1.0** (fixed occl 33.419 vs bar 33.556; Q-formats re-checked against v3 ranges — ACT_HI=64 vs measured 41.25, all int32 ACC bounds hold, no format moved); **bit-exactness 0 mismatches / 219,780 core + 180,210 front-end evals**; 299 FPS at the cap with the v3 decode live (ft avg 0.29 ms); captures `.tmp/frost_v3_lightA/B.png` — shading tracks light. Recorded protocol muddle (not blocking, eval is self-consistent): v3's 8 azimuth views feed view=+fwd (sign-flipped vs the physical surface→camera the 24 Fibonacci views use) — the engine feeds the physical convention (`eye − target`), matching the 24-view majority |
| H6 | **ROM re-sweep about the corrected inter-knee axis** — probe15 capsule-contact method; corrected axis n=[0.9997,−0.0244,0]; L [−1.56°,+145.39°], R [−2.33°,+140.75°]; old tilted-axis CHOSEN-UNVERIFIED resolved | `.tmp/_hinge_probe15.py` + `docs/THE_ARTISTS_SOLID.md` membrane | **CLOSED 2026-08-29** — new limits recorded at :619; R flexion +25.93° vs old because old R axis was laterally tilted; `leg_move_v2.py` ROM updated and engine constants re-posted. **CAVEAT (G3, `fae174a0`): the EXTENSION stops inherit a probe15 artifact** — the "forelimb" contact partners are the foot's own distal toes inside the z<0.39 rotating-set cut (100% of nearby skin is in the leg's own rot_set); extension limits flagged for re-measure. **Flexion stops confirmed real** (shank↔thigh skin contact, gap 0.031 @145.39°) |
| H13b | **Frost black-speckle triangles (KNOWN ISSUE, deferred per operator 2026-08-29)** — scattered single triangles decode full-black amid lit neighbors (hand back, arms), viewport+light dependent. Candidates ranked: (1) sliver/near-degenerate triangles whose posed frame (largest-axis basis from the cross product, `frost_decode.comp:87-134`) is unstable vs the rest-pose frame at train time — 206 degenerate normals measured in the AO pass; (2) the azimuth-8 view-direction sign muddle (H12 integration note — train fed +fwd for equator views, engine feeds physical); (3) untrained latents (19.3% coverage residual — but speckle ≠ coherent regions, so unlikely the main cause). Named fix path: frame from rest normals rotated by the pose (sliver-stable) + the sign-fix retrain. NOT blocking; the display gamma (1/1.8) is live | frost_decode front-end + H12 row | re-open when shading quality is next on the table |
| H14 | **Sound stage 2 — the GPU mode bank + impact excitation** — stage 1's modes are landed (F1/F2/F3 PASS, `94b32cf4`): port the lowest-N global modes (up to the derived 129 Hz carrier-Debye ceiling) + the Rayleigh damped-sinusoid bank to the runtime, excited by G3's deterministic contact impulses λ (estimator B rows). α/β (damping) measured by the named plush/foam loss-factor experiment; t·ρ CHOSEN flagged | `agent_logs/hy3/sound_packet_02.md` S2-S4 + `agent_logs/kimi/contact_ref_01.md` | footstep impacts audible from the walk's λ rows, bit-identical render from the same state, mode frequencies matching stage 1's table |
| H15 | **THE SKELETON LINE (operator priority 2026-08-29: foundation before polish)** — a COMPLETE humanoid stick figure (the 690-rod bone GLB) fittable into ANY humanoid object, with the knee-proven law repeated for EVERY joint: per joint — derived center, derived axis (bilateral pairs: the inter-joint line; spine/neck: the segment axis), ring set, capsule-contact ROM, and registration into ONE unified volp-ARAP system (the visual membrane manipulated around every joint by the same law). Then the gait CPG drives the full skeleton. This is L6 generalized: the knee was the prototype; the factory is the product | physics packet Q4 + H13 + `.tmp/_hinge_probe*.py` | every skeleton joint articulated in the window by the same volp law (no per-joint special cases); per-joint F1/F2/F3 gates green; the monkey moves its arms/spine/neck, not just knees |
| H16 | **Locomotion intelligence (the robot with biological limits)** — the creature MEASURES its environment through the substrate (contact λ, the cube index, the CA field — its senses are measurements, not scripts) and DECIDES actions: keep moving forward? place the foot HERE or HERE or HERE? Footstep planning over the measured terrain, biological/anatomical constraints (the derived ROM/axis limits are its hard bounds, the CPG its rhythm) | H7/G3/G4 + H15 | the monkey walks a non-flat environment and chooses footsteps from measured contact, not a canned march; metamorphic rotate-world still PASS |
| H13 | **GPU volp-ARAP knee kernel (the blend successor)** — port the SHIP-path law (H11, `9d575b03`: bi-Laplacian smooth ARAP λ=0.05 + in-solve Lagrange volume constraint ΣV=V_rest, Schur row INSIDE the solve — never a post-pass) to a CA-field kernel replacing the blend in the live window. Iterative GPU solve (no splu on GPU): fixed-order Jacobi/CG with the Schur backsolve per iteration, determinism tier named (float solve = Tier-1b per runtime packet 02; the 130° limit-cycle follow-up = under-relaxation/Anderson, measured on CPU first) | `agent_logs/kimi/volp_arap_01.md` + runtime packet 02 | **CLOSED 2026-08-29 — LIVE AS THE DEFAULT KNEE SKIN, all numeric gates green.** The shipped kernel (`ChimeraEngine/engine/shaders/volp.comp`, 393 lines, one 512-thread workgroup): UNIFIED two-knee solve (the bands overlap — one system, one whole-body volume constraint), precomputed dense A_ff⁻¹ (θ-independent — the CG question dissolved: NF=291), Horn quaternion polar via 4×4 Jacobi 5 sweeps (power iteration FALSIFIED on degenerate fold spectra; worst 3e-8 vs SVD over 100k real covariances), M=8 damped outer, **ω=0.5 DERIVED from the measured limit-cycle eigenvalue λ=−1.0000** (pure period-2 flip; ω=1/(1−λ) kills it, res 2e-2→3e-5), warm start across frames with a 2.5° cold-start gate (tracking domain from volp_track.json). f32 Tier-1b: fixed order, no atomics in the value path; NOT bit-exact vs the f64 golden (dev rms ~2.5e-3, boundary named). **In-engine gates** (`.tmp/volp_verify.py`, `volp_engine_gates.json`): **volume exact (dV ~1e-7) at every angle; F1 pen 0.0000 at 88/100/110** (blend: 0.0052/0.0159/0.0143), R-side and (100,100) combined also 0.0000; strain 0.56–0.94 vs blend 0.78–2.07; dev from golden rms 2.5e-3. **FPS 299 at the cap, ft +0.05 ms vs the blend — no collapse.** **The live dyad caught what the offline one missed:** first live scan flagged volp 3/3 with "jagged facets/spikes" — measured cause: the R_i·n0 normals were up to **177° off the geometric normals at the fold** (48 band verts >30°) while positions were clean (pen 0.0000); fixed with geometric normals from incident band tris in the kernel (median 0.03°). Post-fix dyad: modal split at 88/100, CLEAN 3/3 at 110 — the instrument flips on near-clean candidates at this camera (recorded; the numeric gates carry the verdict). Engine: `volp_mode_` defaults to 1 (blend behind `/volp {"mode":"blend"}`), `/volp_bin` (blob), `/volp` (mode/manual/m), `/volp_state` (mesh readback), manual-theta override for verification |
| H7 | **Gait CPG as CA state** — phase per hinge cell, per-pair bands from a reference run's natural lag spread, load feedback from substrate contact, ω-sweep hysteresis | `agent_logs/hy3/gait_packet_01.md` | the march becomes a walk; metamorphic rotate-world PASS — **STAGE 1 (CPU reference) DONE 2026-08-29** (`agent_logs/kimi/gait_ref_01.md`, `.tmp/gait_ref.py`): 8-oscillator reference CPG per the packet (H6 corrected ROM adopted: L 71.915/73.475, R 69.210/71.540; hips + fore "knee"=elbow slots are phase-only placeholders, stated). **G2 bands MEASURED**: all 8 pairs lock on the canonical walk (contralateral ±0.5 cyc, diagonal +0.252 cyc, hip–knee ~0; δ_band = ±2σ_natural = ±0.072…±0.516 rad per pair). **G4 transition FALSIFIED at CPU tier**: ω-sweep [π,4π] ×25 dwells up+down shows zero discontinuity, Δω_h = 0, R ≥ 0.836 everywhere — the stance-depth load surrogate carries no body state; re-run with real substrate λ is mandatory (G3 = next stage's dependency, estimator A-vs-B). Metamorphic **PASS** (same-seed φ series 0 ULP; two-seed lock inside bands; rotate-world exact, by construction at this tier). G5 **PASS** bounded (no pump), W_proxy 579.4°/stride reported, COT anchor engine-side. w-selection criterion found degenerate (monotone in w) — recorded, w=1 adopted. **STAGE 2 (engine port) DONE 2026-08-29** (`agent_logs/kimi/gait_ref_01.md` §stage-2, `shaders/gait.comp`, `.tmp/gait_verify.py`): the CPG runs in-engine on the render thread (gait clock = the water clock's pattern: `/gait_bin` setup, POST `/gait {on,omega,steps}`, GET `/gait`, GET `/gait_state` ring readback) and drives the knees through the existing hinge path (hinge.comp takes θ from the gait; hips/elbows stay placeholder-inert per stage 1). **BIT-EXACTNESS GATE: 0 ULP over 25,000 steps × 8 phases vs the golden CPU run** — the transcendental problem was solved by reversing ucrtbase.dll's sin/cos (np.sin ≡ np.cos's twin ≡ math.sin on this box, measured; the DLL's FMA path transcribed op-for-op into GLSL; Python twin `.tmp/ucrt_trig.py` validated 0/2,000,010 across all code paths; valid |x| < 2e7 rad ≈ 30 days gait, boundary named). Walk VISIBLE: hind knees alternate antiphase (θ_L 2.2…130°, θ_R 0.4…124° over a stride — lateral-sequence, no gallop), one time-stream (the duplicate Python driver killed). **FPS 299–300 at the cap with the gait stepping — no collapse.** **STAGE 3 (G3 contact/load solve) DONE 2026-08-29** (`agent_logs/kimi/contact_ref_01.md`, `.tmp/contact_ref.py`): deterministic Baumgarte contact solve as a pure function of state — **0 ULP double-run on λ AND on the full gait φ/N series with contact in the loop**. The sole rows' load path is the GROUND PLANE (Y_G = −0.0195, birth pose stands on it): the stage brief's toe↔forelimb premise measured FALSE — probe15's extension-stop "partners" are the foot's own toes (100% of nearby skin inside the leg rot_set; the birth pose is standing, arms free at y ≥ 2.49) — **H6 extension stops flagged for re-measure**, flexion stops confirmed real (shank↔thigh at 145.39°). Stride λ: double-peak toe-press windows with liftoff at max extension, duty 0.46/0.47, L/R peak ratio 0.992, half-cycle corr 0.98; ω-insensitive at this drive (Baumgarte `min(depth,slop)/dt` saturates at 5.8× slop press depth — named). Estimator experiment: **B (penetration proxy) ADOPTED** — A (impulse sum) needed the structural effective-mass bound to exist at all (naive hinge-priced λ diverged to 1e11 on compression geometry, measured and fixed). At the surrogate's stall normalization real λ PARKS both hind knees (0.00 Hz — Owaki stall trap, mechanism measured); κ×0.25 restores the walk with bands TIGHTER than the surrogate (Σσ 0.770 vs 1.018, cadence brake 0.9%). **STAGE 4 (real-load gait + G4 RE-RUN) DONE 2026-08-29** (`agent_logs/kimi/gait_load_01.md`, `.tmp/gait_load.py`): **κ derived from the channel's own statistics** — κ* = ω_lo/(σ·M) with M = max_t(N·cosφ) the channel's maximal braking rate (κ*/κ_stall = 0.2405 = sweep placement 0.200 × dynamic range P/M 1.202; the ×0.25 working point EXPLAINED, not adopted; stall boundary predicted at ×0.60 and confirmed marginal, 19% brake, R 0.44). **G2 bands re-measured with real λ at κ***: all 8 pairs lock (min R 0.978, max drift 0.011 rad), **Σσ = 0.736 — TIGHTER than the surrogate (1.018)**; diagonals settled +0.269 cyc (real channel content, inside band); cadence brake 0.8% (was 3.6%). **G4 RE-RUN with real λ: NO TRANSITION — Δω_h = 0** (25 dwells × 2 directions, max lag jump 0.108 rad vs 0.636 threshold, R ≥ 0.900 everywhere, cadence 97–100% of free-run at every ω; the low-end marginality prediction FALSIFIED — stride-averaged braking ~2% governs, the instant peak touching 1.0 cannot trap). **The packet's Owaki form produces no ω-driven transition on this substrate at any gain (walk regime and transition regime do not overlap); the load phenomenon that EXISTS is gain-driven (walk → in-phase park across the load-strength boundary).** Amendments named, none built: velocity-carrying load (unsaturate the channel), load-dependent coupling, swing/stance drive asymmetry. G5: W_proxy 580.30°/stride (0.04% off analytic), E_mech bounded PASS. Engine port gets the load law (estimator B at κ*, normalize on M never peak) + the new acceptance bands — and must NOT promise the transition |
| H8 | **Chimera static graft** — packet 02 Stage-1 falsifiers (buildable now, needs no CA/frost); seam = derived sagittal planes (teddy x=0.0358 law) | `agent_logs/bigpickle/chimera_packet_02.md` | F1.1–F1.4 PASS — BLOCKED on the teddy download (operator's Sketchfab login). **Monkey-side prep DONE 2026-08-29: the monkey's sagittal plane is x = 0.0 EXACTLY** (x-mirror NN distance median 0.0000, mean 0.0011; best-fit plane offset 0.0 over an 81-point scan) — unlike the teddy's x=0.0358. The graft's align step maps teddy x=0.0358 → monkey x=0.0; the seam is NOT "both at x=0" for the donor |
| H9 | **Frost decode in-engine** — the trained MLP as a compute shader (DP4a integer path pinned for determinism; coop-vec for speed on Ada) | frost packet 01 Q1 + runtime packet V5 | **CLOSED 2026-08-29 — BIT-EXACT AT RENDER RATE.** The shipped decode is DEFINED by `.tmp/frost_decode_ref.py` (golden fixed-point reference: PP=15 pos / QN=30 unit / SD=RM=14 dir-coord / SZ=12 hidden / R=24 rescale / QO=16 out, ACT_HI=64 clamp — all sized by `frost_range_probe.py` measurements, int32 MAC bounds PROVEN); `shaders/frost_decode.comp` is its bit-exact port (per-triangle dispatch, atomic-free, int64 rescale, GELU as a 65,537-entry LUT, error ≤ 1.3e-4/act derived). **Fixed-point budget: C_total = 0.563 dB ≤ X = 1.0** (occl 38.76 vs W0 39.32 — 0.034 dB BETTER than e42's own WL+WI fp32 eval; the folding bug found en route: the latent-affine offset must fold with ws·Wq, not fp32 W — worth ~0.5 dB). **Bit-exactness gate (`.tmp/frost_decode_verify.py`): 0 mismatches / 219,780 core decodes + 180,210 front-end evals** across 6 camera/light configs (gate A: engine RGB vs ref core on the engine's own kernel inputs; gate B: ref front-end from rest floats vs engine coords on the 30,035 hinge-unposed tris — the posed-float boundary is Tier-1b, named). `/frost_bin` (model blob) + `/frost {on, light}` + `/frost_debug` (snapshot readback) + frost frag via `gl_PrimitiveID` (per-tri color SSBO — welded verts can't carry flat colors). **299–300 FPS at the cap, ft avg 0.28–0.29 vs 0.31–0.32 ms off — relighting at render rate.** Brief deviations, honest: (1) **DP4a unusable — glslang 1.4.328 has no GLSL integer-dot-product binding; scalar int32 IMAD is the same exactness class** (logged at startup); (2) coop-vec present (rev4) but INACTIVE — scalar path meets rate with headroom, a second exact path doubles the verification surface (V5); (3) two shader bugs found by gate B before ship (std430 ivec3 push-constant packing → ivec4; missing ×2^PP scale in the position quantize). **COVERAGE GAP (v1, RESOLVED by H12 2026-08-29): the "2,756 of 36,630 triangles (7.5%)" gap was NOT a view-count gap — it was the cropped-ortho-film bug H12 root-caused (mitsuba's rigid `look_at` covered a ~2-unit central slab); the whole-body re-render + 32-view retrain (v3) covers 29,543/36,630 (80.7%) and is the live engine model** — see H12. (v1 record: untrained rows decoded muted-but-wrong, mean \|rgb\| 0.027 vs trained 0.012 under the same light, 0 rows past the display clamp; captures `.tmp/frost_lightA/B.png`, `.tmp/frost_underside_lit.png`) |
| H10 | **Sound modes** — K·φ = λM·φ on the dual graph with the corrected D ∝ K_BOND·t³ bending scaling, impact from the gait's contact impulse | `agent_logs/hy3/sound_packet_02.md` | **STAGE 1 (CPU reference) DONE 2026-08-29** (`agent_logs/kimi/sound_modes_01.md`, `.tmp/sound_modes.py`): **F1 PASS** (icosphere ladder = membrane-sphere branch exactly: f₃/f₂ 1.4139 vs √2, f₄/f₂ 1.8236 vs 1.826; Kraus inextensional missed at l=4, reported), **F3 PASS** (sphere rate p = 2.094 ≈ O(h²); SALLY 2× midpoint refinement 20/20 modes monotone +2.4…+4.3%), **F2 Weyl PASS** (19,765 ≤ 34,332 DOF). Carrier-Debye cutoff derived: f_max = 129.19 Hz (replaces air-343 14 kHz). **Packet text contradicted by measurement:** the per-triangle-A0 reading of k = 0.75·K_BOND/A0 is refinement-inconsistent GLOBALLY (p = −1.008, v1 FALSIFIED) — the law only survives as constant k_e = 0.75·K_BOND/A0_eq through the part's S = R_BOND/e_med (packet-02's re-scaling clause made precise). t·ρ, α, β CHOSEN-UNVERIFIED (experiments named). Bending share of low modes ~1e-6 — the ω∝t flexural law is assembled but lives in the patch band, not the global low end. Stage 2 = GPU/runtime bank + impact excitation — **G3 λ EXISTS 2026-08-29** (`agent_logs/kimi/contact_ref_01.md`): deterministic per-row contact impulses on the sole sets (0 ULP bit-identity), double-peak toe-press transients per stride; the impact channel reads the same rows (estimator B adopted; the velocity share of λ is small at this drive — Baumgarte clamp saturates at 5.8× slop press, named) |
| B14 | **The hinge lives in the ENGINE, not Python** — operator decree ("why is it running off of Python") | main agent | **CLOSED 2026-08-28, three stages:** (1) C++ `pose_hinge()` — 238 FPS; (2) **`hinge.comp` — the first CA-field kernel** (weight SSBO + engine clock on GPU, buffers device-local); (3) **optimization pass — 273 FPS, ft avg 0.29ms, max 1.27ms, 0 spikes**: per-slot mapped camera UBOs (the old path did a staging create/destroy + vkQueueWaitIdle EVERY FRAME), true frames-in-flight (slot-cycled fences/cmdbufs/descriptors; two fence bugs found by validation, fixed), cap 300, rotation live |
| B15 | **Water GPU port as CA-field kernels** — per runtime packet 02 against the landed CPU golden reference | main agent | **CLOSED (B15a) 2026-08-28 — BIT-EXACT PASS**: `water_depth/color/occ.comp`, order-consistent Gauss-Seidel coloring (63 colors, schedule proven exact on CPU first), float64 with `precise` (FMA contraction was flipping `delta_count` at rounding boundaries), dispatch overrun guard (rounded groups spilled into the next color's edges), edge-activity mask (the cube veto's transport half), injection table as DATA (numpy's PCG64 is unportable — no RNG in the runtime). **All 21 states bit-identical across 34,538 cells: F1 ΣV exact, F2 min ≥ 0, F3 full arrays identical — "the GPU water IS the CPU water"** |
| B10 | **L5 frost experiment** — `agent_logs/bigpickle/frost_packet_02.md`, decision-free | main agent | **GT PIPELINE LIVE (2026-08-28)**: mitsuba 3.9.1 cuda_ad_rgb installed from the preserved wheel; `.tmp/frost_gt.py` renders the packet's exact spec (SALLY body via trimesh PLY, principled 0.5/0.4/0 control, path+RR, independent seed 0, SPP 8192, 128 train + 64 held-out Fibonacci lights with the 8° gate verified at exactly 8.0°, 8 ortho views); validate PASS, timed 1.7s/render; **full 1536-render batch running (~0.7 h, checkpointed, resume-safe)** — then the AO pass (R=1024) and the B0 baseline (8-D latent + 3×64 MLP fp32) per the packet |
| B11 | **L7 GPU port** — per runtime packet 02 (SSBO ping-pong, subcycle seam SOLVED) | unassigned | READY — after B7 lands |
| B12 | **Chimera packet 02 construction** — static split/graft buildable now (Stage-1 falsifiers need no CA/frost) | unassigned | READY — after teddy qualifies |

**Division of labor (operator decree 2026-08-27, AMENDED 2026-08-28):** Kimi
holds project context and writes elaborate prompts IN CHAT (never in docs)
for transfer to Open Code, where local agents run long construction loops.
~~HARD BOUNDARY: Kimi edits ONLY this file~~ **AMENDED by the operator during
the leg night (2026-08-28): when the local agents stall, the main agent
constructs directly** — it fixed the torn leg, the engine (B1/B3/input/
streaming), and the knee axis itself, by explicit operator instruction
("I want you to do the work"). The master list remains Kimi's exclusive
edit surface among docs; everything else now carries a workflow:
`docs/THE_OPERATING_MANUAL.md` (boundaries, the loop, the task envelope) +
`docs/THE_TRIANGLE_GUIDE.md` (the laws). This file is the guide for BOTH
sides: the prompter writes from it, the builder reads it first and runs
`python tools/orient.py` second. The operator ratifies, steers, and is the
human terminal of every dyad.

**ROSTER (2026-08-28, operator report):** the free model supply was cut;
Big Pickle and hy3 are RETIRED with their service (their packets/audits
stand — the work is independent of the worker). Active: **CatCoder 2.5**
(construction lane) and **Ling 3.0 Flash FIN** (bounded verification lane).
**Addendum (leg night, 2026-08-28):** the local agents stalled on the torn
leg; the main agent closed it directly and now shares the construction lane
per the amended division of labor above. Quinn 3.8's fate unconfirmed.

## 8 · THE RULES OF THIS PAGE

- This list is a MAP, not evidence: when it disagrees with orient or a run
  record, the newer fired falsifier wins and the row rots — amend, don't argue.
- Every thread has a home doc; no second source of truth lives anywhere else.
- Written so any agent, after any compression, can read ONLY this file and
  know what this is for, what is proven, what is unmeasured, and who owns
  the next gate.

## 9 · RESEARCH ANNEX (2026-08-27 — concepts for the next prompts, not yet built)

External art that connects to our lines. Nothing here is measured by us yet;
each entry names what it gives us and what would falsify it for our use.

- **The CA's physics has a rigorous home: Discrete Exterior Calculus.**
  Diffusion, waves, and flow on a triangle mesh are exact discrete operators
  (cotan Laplacian, Hodge star over the circumcentric/barycentric dual) — our
  dual graph IS DEC's dual mesh. The CA rules stop being hand-tuned and
  become discrete PDEs with conservation laws. Water (L7) = the wave/shallow
  equation on this operator; mass conservation is built in, not asserted.
  Falsifier for us: any CA rule we keep that cannot be written as a DEC
  operator is a smell, not a law.
- **CA shallow water is proven to converge with finite-volume solvers**
  ([J. Hydrology 2018](https://www.sciencedirect.com/science/article/pii/S0022169418304438)):
  CA is not a toy for L7 — same equations, same answers, local updates only.
- **MeshNCA ([arXiv:2311.02820](https://arxiv.org/abs/2311.02820))** — neural
  CA living directly on a mesh, real-time, no UV maps, steerable at test
  time. Proof our substrate idea is state of the art — and the
  differentiator: theirs runs per-VERTEX; ours runs per-TRIANGLE (the
  triangle is the substrate, the cell, and the mirror). Their learned rule
  is the frost-texture lane's closest neighbor.
- **The 2D splat's correct ancestor is the surface light field, not NeRF.**
  Radiance as f(surface point, view direction) with geometry carrying
  parallax (Wood et al. 2000; TU Wien/Eurographics surveys). A BTF
  (Dana 1999) adds the light direction: f(point, view, light) — a 6D field,
  exactly "train ray tracing without ray tracing cores." Held-out light
  directions as the door (already in §2). Neural BTF compression (Kautz,
  GPU Gems 2 ch.11) is the lookup-cost runtime. 2DGS
  ([arXiv:2403.17888](https://arxiv.org/abs/2403.17888)) confirms the
  primitive: a planar disk whose normal is its steepest density direction —
  one disk per triangle, normal never fitted.
- **The frost as a differential appearance equation**
  ([Neural Differential Appearance Equations, arXiv:2410.07128](https://arxiv.org/html/2410.07128v2)):
  weathering/corrosion modeled as a neural PDE over a surface's appearance.
  Frost growing on fur is the same math — appearance evolving locally over
  the substrate, seeded by the CA state.
- **Hinge arrays (L6) get their deformation law from ARAP, not LBS.**
  As-rigid-as-possible keeps the skin smooth while a region rotates;
  pseudo-skeleton ARAP (Zollhöfer 2013) decouples edit handles from mesh
  complexity; Mesh Puppetry (Shi et al.) adds joint-limit constraints;
  higher-order ARAP ([arXiv:2501.10335](https://arxiv.org/html/2501.10335v1))
  removes the crease at the hinge boundary. Our hinge array = a designated
  triangle ring carrying a rotation field, the surrounding skin solved ARAP.
  Falsifier unchanged: volume loss or self-intersection inside the ROM.
- **Skeletons can drive simplices directly, no vertex weights**
  (Tsinghua simplex-transform deformation): the bone rig drives triangles,
  not vertices — no skinning weights, no candy-wrapper collapse. Matches
  the decree "triangles are the substrate" for L6's rig binding.
- **Rules must be E(3)-equivariant**
  ([E(n)-equivariant GNCA, arXiv:2301.10497](https://arxiv.org/html/2301.10497v2)):
  a CA rule that behaves differently after rotating the world is not physics.
  Constraint for every learned rule on the substrate: rotate the input, the
  output must rotate with it. Cheap falsifier, high doctrine value.
- **DiffusionNet ([arXiv:2012.00888](https://arxiv.org/abs/2012.00888))** —
  learned heat-diffusion features on meshes, discretization-agnostic. If a
  network ever reads the substrate (frost trainer, chimera parts classifier),
  this is how it sees triangles without depending on tessellation luck.

### Round 2–3 additions (same day)

- **The birth rule's wound/feature problem is industry-wide and the answer
  is classification + curvature.** Scan-repair literature is blunt: no tool
  auto-tells a wound from an intentional opening — the practical pattern is
  *label the openings, constrain fills to labeled regions, and fill
  curvature-guided patches that extrapolate along principal directions
  rather than naive triangulation* (scan-to-CAD surveys; MeshInspector's
  "repair without closing holes"). Our birth rule gets two upgrades: (a) the
  opening classifier is a first-class membrane, not a heuristic; (b) birthed
  triangles must extrapolate the local curvature field, not just span the
  gap. Falsifier unchanged: any true opening closed — now joined by "any
  birthed patch that flattens the curvature it should continue."
- **The chimera (L8) has a grafting cousin already: MeshNCA grafting** —
  two trained NCA models cooperate across a boundary at test time to grow a
  hybrid texture ([meshnca.github.io](https://meshnca.github.io/)). Texture
  grafting across a seam on one mesh = the teddy/monkey 50-50 split's
  appearance layer. For geometry: Muses ([arXiv:2601.03256](https://arxiv.org/html/2601.03256v1),
  training-free creature composition) and PartCrafter (NeurIPS 2025,
  compositional part-level mesh generation) show part composition is hot —
  but none of them run on a CA substrate. Ours would be the first.
- **Training the frost runs on this PC.** nvdiffrast (PyTorch, NVIDIA
  consumer GPUs) is the differentiable rasterizer; Mitsuba 3 (Dr.Jit,
  CUDA + LLVM-CPU backends) is the ground-truth path tracer for the light
  answers. No RTX required for the CPU/LLVM fallback — slower, but the
  falsifier doesn't care how long the run took. OptiX/RTX paths
  ([arXiv:2103.15208](https://arxiv.org/html/2103.15208v3)) are the upgrade
  if the hardware is there.
- **The engine's future architecture has a name: visibility-buffer
  rendering.** Nanite's core trick — one 64-bit (triangle ID + instance)
  value per pixel via atomic depth max, then shade each visible pixel ONCE
  with deferred materials — is *literally our database*: the pixel stores
  the triangle's database row. Picking, CA state, and material lookup all
  become one indirection. Mesh shaders (VK_EXT_mesh_shader) emit
  meshlet clusters; two-pass HiZ occlusion culling kills the rest. The
  "one row per triangle" doctrine and the renderer converge on the same
  integer. (Refs: [Nanite mental model](https://unbiasedgamer.com/the-mental-model-for-unreal-engines-nanite-virtualized-geometry-and-cluster-culling/), [nanite-webgpu](https://github.com/Scthe/nanite-webgpu), [Granite mesh rendering](https://themaister.net/blog/2024/01/17/modernizing-granites-mesh-rendering/).)
- **"Scaled triangles" is a birth rule.** Loop/√3 subdivision = a
  deterministic CA birth rule on triangles (one triangle → four children,
  positions by stencil); view-dependent refinement (Hoppe's progressive
  meshes, [vdrpm](https://hhoppe.com/vdrpm.pdf)) = the rule keyed on
  screen-space footprint. The operator's complaint about blocky voxels maps
  to: voxel scale is scaffolding-only; triangle scale refines where the eye
  looks. The CA doesn't just repair meshes — it *resolves* them.
- **Gait as a standing wave has a 25-year-old name: CPGs.**
  Central pattern generators — coupled oscillators entrained by LOCAL load
  feedback — produce walk/trot/pace/bound and spontaneous gait transitions
  with no central clock (Ijspeert's salamander; Owaki & Ishiguro's
  decentralized entrainment, [Ryu & Kuo 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8222298/)).
  A decentralized CPG IS a cellular automaton: phases are cell states,
  entrainment is the local rule. The hinge arrays' contraction signals
  (§2) get their waveform from biology, not keyframes.
- **Planar mirrors + splats is now published:** TR-Gaussians
  ([arXiv:2511.13009](https://arxiv.org/html/2511.13009v1)) renders planar
  transmission/reflection with splatting; NeRF-casting (SIGGRAPH Asia 2024)
  keeps reflections view-consistent. They fit the mirror's tilt. Ours never
  fits — the triangle's normal IS the mirror tilt. That's the frost's
  unfair advantage, and it is now a race, not a fantasy.

### Round 4 additions (same day)

- **Frost growth itself is a CA rule — literally.** Frost on glass is the
  canonical example of diffusion-limited aggregation (Witten–Sander DLA);
  constrained 3D DLA already grows believable root/branch systems
  ([C&G 2006](https://www.sciencedirect.com/science/article/pii/S0097849306000896));
  lattice-Boltzmann enthalpy models simulate frost-layer growth for
  engineering. So the frost has TWO layers, both ours: a GROWTH rule (DLA
  walking the dual graph — particles diffuse on triangles, stick where they
  land) and a LIGHT answer (the trained field from round 1). Growth is
  physics; sparkle is lookup. Nobody else has the pair.
- **Muscles driving a meshed body is published and it locomotes.**
  Soft Body Locomotion (Tan/Liu/Turk, Georgia Tech 2012): creatures as
  corotational-FEM meshes with muscle force terms produce walking gaits.
  Our "muscles are CA contraction signals" (§2) has a direct ancestor —
  swap their FEM elements for our triangle carrier (T2, already landed:
  area rigidity k = 0.75·K_BOND/A0) and their muscle signal for our CA
  state. XPBD gives the unconditionally-stable real-time solver
  ([morphogenesis-resources](https://github.com/jasonwebb/morphogenesis-resources)
  catalogues the space; GPU XPBD already uses spatial hashing — our cube
  scaffolding doubles as the collision hash for free).
- **Growing NCA = consume-to-recreate, with healing.** GNCA
  (Mordvintsev 2020; Mixtures of NCA 2025, [arXiv:2506.20486](https://arxiv.org/html/2506.20486v1))
  grows an organism from one cell and REGENERATES it after damage. Mapped
  to the substrate: a chimera grown from a seed rule can re-heal wounds
  in-game — damage is not a texture swap, it's the CA re-growing lost
  triangles. The birth rule (L4) is the static version of this membrane.
- **The money dot exists and it is a CA game.** Noita — "every pixel
  simulated," literally a falling-sand cellular automaton — is a
  commercial hit built by a tiny team over ~7 years
  ([80.lv](https://80.lv/articles/noita-a-game-based-on-falling-sand-simulation)).
  The market has already proven it pays for simulation depth as the core
  aesthetic. Noita is 2D pixels. Nobody has shipped the 3D triangle
  holographic successor. That is the gap L9 stands in.

### Rounds 5–10 (research swarm, same day — threats included on purpose)

**R5 — patterns, stability, streaming.**
- **The fur's PATTERN is a CA too.** Turk 1991 ran reaction-diffusion
  directly on surface meshes — leopard rosettes, zebra stripes, no UVs
  ([paper](https://sites.cc.gatech.edu/people/home/turk/my_papers/reaction_diffusion.pdf)).
  Staddon 2023 ([arXiv:2312.00637](https://arxiv.org/abs/2312.00637))
  shows CURVATURE-dependent diffusion orients stripes correctly around
  torsos and legs — local triangle curvature steers the global pattern.
  Coat, frost, and water are all the same class of rule on our substrate.
- **Learned CA stability is a solved recipe, not a hope:** sample pools +
  damage augmentation ([Distill, Growing NCA](https://distill.pub/2020/growing-ca)),
  coarse time sampling beats frame-locked updates (Richardson 2024, PLOS
  CompBio), pool-free diffusion-style training ([arXiv:2410.02651](https://arxiv.org/pdf/2410.02651v1)).
- **Coarse CA → fine appearance:** NCA-from-Cells-to-Pixels
  ([arXiv:2506.22899](https://arxiv.org/html/2506.22899v3)) pairs a coarse
  NCA with a tiny local decoder for high-res appearance — the architecture
  our frost wants: dynamics on triangles, detail at render resolution.
- **Streaming at scale:** Nanite's own course notes
  ([Karis, SIGGRAPH 2021](https://advances.realtimerendering.com/s2021/Karis_Nanite_SIGGRAPH_Advances_2021_final.pdf))
  prove triangles stream to billions — and explicitly REJECT voxels and
  points. Out-of-core mesh compression (Isenburg/Gumhold 2003) and Chunked
  LOD (Ulrich 2002, public domain) are the compatible recipes; both assume
  static topology, which our birth rules violate — streaming a LIVING mesh
  is our open problem. THREAT: geometry images (Hoppe 2002) resample the
  surface into a regular image and would dissolve the triangle cell
  identity. Noted, rejected by doctrine.

**R6 — collision, GPU speed, training tricks.**
- **Collision against deforming triangles is real-time.** Kavan & Žára
  refit a sphere BVH under skeletal deformation (0.36 ms/frame two-model,
  650k-tri crowd at 52.8 ms — [paper](https://users.cs.utah.edu/~ladislav/kavan05fast/kavan05fast.pdf));
  modified GJK returns exact colliding triangle PAIRS and costs nothing
  when triangles are born or die at runtime ([HAL](https://hal.science/hal-00342935v1/document))
  — the birth rule's collision partner. THREAT: learned shallow-SDF
  collision (Epic, [arXiv:2411.06719](https://arxiv.org/html/2411.06719v1))
  answers collision with implicit fields — accurate, shipped, and not
  triangles. Our falsifier if we ever borrow it.
- **GPU budget measured:** dense CUDA Game-of-Life runs 182M cells at
  729 generations/sec on an RTX 3080 ([repo](https://github.com/bryanoliveira/cellular-automata)) —
  the ceiling for our substrate on this class of hardware. OctreeNCA
  ([arXiv:2508.06993](https://arxiv.org/html/2508.06993v1)) fuses a whole
  neural CA step into one CUDA kernel at ~90% less VRAM than a UNet.
- **Two cheap stabilizers with chimera written on them:** noisy-seed
  training makes NCA robust to timestep AND resolution changes
  ([arXiv:2404.06279](https://arxiv.org/html/2404.06279v3)); an "identity
  channel" keeps separate organisms from bleeding into each other where
  they touch ([arXiv:2508.06389](https://arxiv.org/html/2508.06389v2)) —
  the teddy/monkey seam needs exactly this.

**R7 — fur, eyes, subsurface.**
- **Shells-and-fins fur is doctrine-compatible** (Lengyel/Hoppe 2001,
  [project page](https://hhoppe.com/proj/fur/)): concentric surface-bound
  shells + silhouette fins, interactive, controllable — displaced triangle
  layers, not strands. THREATS: hair meshes (SIGGRAPH 2024, patented) and
  NeuralFur are strand geometry — outside the doctrine.
- **Eyes sell realism through corneal refraction** — production leans on
  RT (Animal Logic SIGGRAPH 2024), but image-space caustics (Wyman &
  Davis 2006, [I3D](https://cwyman.org/supplement/InteractiveISCaustics/I3D06.pdf))
  fake refraction with rasterization only. The per-triangle light field
  must reproduce: refraction, caustics, pupil dilation, sclera vascularity
  (Unity HDRP's checklist is the requirement spec).
- **Subsurface fits the light field:** wrap lighting is a free term in
  f(point, view, light); pre-integrated skin shading (Penner/Borshukov)
  is a 2D LUT indexed by N·L AND surface curvature — curvature we already
  compute. Screen-space SSS (Jimenez 2015) is fast but a post-process —
  outside the per-triangle model. Rejected, recorded.

**R8 — rigging, segmentation, materials.**
- **Auto-rigging exists (Pinocchio, RigNet, ASMR 2025) but every one
  outputs LBS skeletons** — a translation layer to hinge arrays is
  required, and the falsifier is mechanical: does the auto-rig deform
  acceptably when LBS is replaced by hinge constraints?
- **LMSeg ([arXiv:2407.04326](https://arxiv.org/abs/2407.04326)) segments
  meshes ON the barycentric dual graph — one node per face.** It thinks in
  our native data structure. Falsifier for use: do its part boundaries
  coincide with mechanical hinges, or only with human-semantic labels?
- **Materials:** MatSynth (4,069 CC0/CC-BY 4K PBR materials,
  [matsynth](https://www.gvecchio.com/matsynth)) is legal training data
  for the frost; DreamMat (SIGGRAPH 2024) explicitly avoids baked-in
  shading — the doctrinally cleanest text-to-material. TRAP RECORDED:
  DiffMat is non-commercial + Substance-dependent — incompatible with a
  commercial game. Never let it into the build.

**R9 — the market (numbers, not vibes).**
- **Noita:** 3 people, ~2.2M copies, ~$26M gross (est).
  **Teardown:** 2→6 people, 1.1M copies by 2022, studio ACQUIRED by
  Embracer — but its identity is ray-traced voxel lighting: Teardown's
  look is the benchmark our no-RT frost must match. **Besiege:** ~3
  people, 1M copies / $7M in five months at $6.99. **Dwarf Fortress:**
  2 devs, 20 years, then 160k Steam copies in 24 HOURS and $7.2M in one
  month — depth monetized retroactively; retention comes from shareable
  emergent stories ("Losing is Fun"), not graphics.
- **The honest threat:** every commercial CA success is pixel, voxel, or
  tile. No shipped game has proven triangle-substrate CA gameplay. That
  is precisely our bet — recorded as unproven, not as fact.

**R10 — the economics and the door out.**
- **Donations don't fund engines:** Blender FY2024 ran at a LOSS on €3.1M
  income ([annual report](https://www.blender.org/news/blender-foundation-annual-report-2024/));
  Godot spends more per month than it takes in. Confirms the doctrine:
  the GAME carries the revenue; the engine is the gift.
- **Creator-economy benchmarks:** Roblox paid creators >$1B in a year;
  UEFN pays 40% of net revenue into an engagement pool ($352M in 2024);
  marketplace splits run 88/12 (Epic Fab) to 70/30 (Unity); Steam's 25%
  paid-mod split is the exploitative floor. IF a Chimera marketplace ever
  exists: 70–88% to creators or don't bother. THREAT: platform economics
  contradict "the game is the artifact" — chase the game, not the platform.
- **The door out is glTF.** Blender→glTF→Godot is production-proven
  ([Project Dogwalk](https://www.khronos.org/blog/project-dogwalk-stress-testing-blender-to-godot-interoperability-with-gltf));
  glTF is an ISO standard with a vendor-extension mechanism — our
  per-triangle light-field params, hinge arrays, and CA rules ride as
  named metadata (e.g. `CHIMERA_lightfield`) inside a standard container.
  Artists keep Blender; we keep the substrate. THREAT: Khronos is
  advancing volumetric/Gaussian-splat extensions — we document selective
  support or silently contradict the 2D-only decree.

### Rounds 11–16 (second swarm — engineering, training, evolution)

**R11 — inside/outside, erosion, vegetation.**
- **Generalized winding numbers** (Jacobson 2013,
  [project](https://igl.ethz.ch/projects/winding-number/); fast tree
  version Barill 2018) answer inside/outside on BROKEN soups — graceful
  degradation near defects instead of failure. This is the volumetric
  prior the birth rule votes against. THREAT: a naive threshold seals
  true openings — the winding field may inform births, never veto the
  opening classifier.
- **Virtual-pipes erosion (Mei 2007) is a CA by another name** — height,
  water, sediment, 4 outflow fluxes per cell, local update passes; 65
  iterations/sec on 2007 GPU hardware (Jákó 2011). The river line's
  direct ancestor. Multi-layer heightmaps (VMV 2024) add overhangs and
  caves but go volumetric — re-derive on the triangle dual graph or stay
  flat; recorded as the open derivation.
- **Shipped vegetation is baked, not grown:** SpeedTree (Academy Award,
  20 years of titles) ships pre-baked meshes/textures; Horizon Zero
  Dawn's GPU placement built a whole wilderness with THREE artists —
  artist rules, GPU scatter, seeded determinism. Pure runtime L-systems:
  not shipped anywhere. Our chance to be first is real; the bar is
  placement quality, not growth novelty.

**R12 — Vulkan reality, GI without RT.**
- **Memory layout is a 12× question:** for coherent 2D neighbor reads,
  storage images/texel buffers beat flat SSBOs (NVIDIA engineer, measured
  on driver forum); subgroup shuffles replace shared-memory atomics and
  cut atomic count 32–64× ([Khronos tutorial](https://www.khronos.org/blog/vulkan-subgroup-tutorial))
  — and fewer atomics = fewer determinism holes. Async compute on
  tile-based GPUs can serialize the whole frame if barriered wrong; an
  AMD transfer-queue WAW crash in the wild ([llama.cpp #25195](https://github.com/ggml-org/llama.cpp/issues/25195))
  says: synchronization gets driver-tested, not just validation-tested.
- **Mesh shaders are fragmented:** AMDVLK disables `taskShader` on
  RDNA2/3 ([AMDVLK #341](https://github.com/GPUOpen-Drivers/AMDVLK/issues/341)),
  Intel Arc is Vulkan-only, NVIDIA needed beta drivers at launch.
  Verdict for us: NOT a load-bearing default. Classic vertex pipeline +
  compute stays; mesh shaders are an optional fast path behind a
  capability probe.
- **No-RT GI is proven by Lumen's software path** — screen-space traces +
  mesh SDF marching, no RT cores, default in UE5. DDGI and EA's GIBS
  (surfels, shipped at 60fps on consoles) both lean on hardware RT —
  contradiction for us, but GIBS proves the SURFEL CACHE is
  production-ready; our variant replaces its ray casts with known
  triangle mirrors. Baked irradiance volumes (Treyarch) are the static
  floor — useless for a living substrate.

**R13 — the light field gets its architecture and its datasets.**
- **Real-Time Neural Appearance Models (Zeltner, TOG 2024,
  [arXiv:2305.02678](https://arxiv.org/abs/2305.02678)):** an 8-channel
  latent + a 3×64 MLP maps (latent, light, view) → BRDF, 10× faster than
  the layered graph it bakes. That is f(point, view, light) with a
  published parameter budget. Falsifier: train it on a corpus part and
  measure PSNR against Mitsuba ground truth — the frost's first number.
- **Directional encoding:** spherical Gaussians carry a lobe in 10–15
  numbers vs 48 SH coefficients (SG-Splatting, [arXiv:2501.00342](https://arxiv.org/abs/2501.00342))
  — borrow the encoding only; the paper is volumetric 3DGS, doctrine
  violation if adopted whole. NVIDIA's NTC proves per-material tiny-MLP
  decoders ship in SDKs (threat: `VK_NV_cooperative_vector` is
  vendor-locked; DP4a fallback exists).
- **Training ground truth exists:** DiLiGenT (96 calibrated lights,
  laser-scanned normals), OpenIllumination (64 objects, 108K images),
  and DiLiGenRT (translucency/roughness — the boundary where a local
  mirror MUST fail; if we fail there, that's the measurement that sends
  subsurface effects to the CA substrate, exactly as the doctrine says).

**R14 — evolution of creatures and rules.**
- **Sims 1994 + Framsticks:** co-evolving body and control produces
  swimmers/walkers/fighters — and evolution is the best BUG-FINDER ever
  built (both projects report creatures exploiting simulator flaws).
  Lesson: our physics must be exploitable-proof before we let anything
  evolve on it, or we'll breed beautiful cheats.
- **CA rules can be DISCOVERED, not just designed:** Crutchfield &
  Mitchell (PNAS 1995) evolved 1D CA rules that coordinate globally via
  particle-like signals from purely local updates. Known trap: rules
  overfit the training distribution — every evolved rule faces held-out
  initial conditions as its falsifier. Lenia + IMGEP ([arXiv:1908.06663](https://arxiv.org/abs/1908.06663))
  auto-discovers diverse self-organizing phenomena — the chimera
  menagerie's search engine.
- **MAP-Elites/POET/NEAT** give the catalog machinery (niches of elites,
  self-generating curricula). Rule 0 friction recorded: pure novelty
  search has no falsifier and can never be a gate — it generates
  candidates, membranes judge them.

**R15 — fracture, sound, cloth.**
- **Fracture modes (Sellan 2021, [arXiv:2111.05249](https://arxiv.org/pdf/2111.05249v2)):**
  eigen-analysis of a shape's natural breaking patterns — derived
  fracture, not Voronoi's telltale convex chunks; precomputed modes cost
  nothing at runtime. Shipped practice (BF3 pre-fracture swaps, R6 Siege
  2D projection) confirms: pre-computed = cheap + deterministic, runtime
  = pretty + spiky. DMM (Force Unleashed) deliberately CAPPED element
  splitting for predictability — the industry's own determinism
  trade-off, documented.
- **Sound-from-mesh is real but volumetric:** modal synthesis is an
  eigenproblem over the VOLUME (threat to surface-only doctrine);
  DeepModal/NeuralSound compress it to <1s inference. No shipped
  middleware does mesh-driven modal audio — honest gap: if we ship it,
  it's a first, and it needs its own membrane.
- **Shipped cloth ceiling is cosmetic:** PBD/XPBD is the standard; AAA
  uses it for capes, hair, flags — not flesh. Our chimera's skin/fur
  falsifiers must aim at what shipping games actually achieve, then
  exceed it via the substrate — not at film-VFX flesh nobody does in
  real time.

**R16 — determinism, verification, and the gradient wall.**
- **Determinism is engineered, never assumed.** NVIDIA CCCL ships
  determinism tiers (`run_to_run`; `gpu_to_gpu` at 20–30% cost);
  CERN ALICE's deterministic mode (no FMA, no fast-math, total-order
  sorts, [arXiv:2511.17018](https://cds.cern.ch/record/2946680/files/2511.17018.pdf))
  costs 1.5–10× and FOUND long-standing bugs blamed on parallelism.
  Gaffer-on-Games scope: bit-exactness claims must name toolchain +
  hardware family. GPU atomics are the enemy — tree reductions or
  prefix scans everywhere the CA accumulates.
- **Metamorphic testing is the right oracle** (NIST, MET 2021): physics
  has no exact oracle, so test RELATIONS — "rotating the cube
  scaffolding must not change total energy", "sealed mesh + N CA steps
  ⇒ triangle-count-minus-openings invariant". Hypothesis-style PBT
  automates the input generation. This is how Rule 0 falsifiers become
  a test SUITE instead of a document.
- **The gradient wall is proven math:** backprop through long chaotic
  rollouts explodes/vanishes exponentially (Metz et al.,
  [arXiv:2111.05803](https://arxiv.org/pdf/2111.05803)); contact
  on/off discontinuities (hinges! collisions!) break gradient quality
  ([arXiv:2603.16478](https://arxiv.org/html/2603.16478v1)). Doctrine
  consequence: CA rules and light fields train SHORT-HORIZON or
  BLACK-BOX (ES/REINFORCE), never naive long BPTT. The maximum usable
  horizon is itself a membrane to be measured, not assumed.

### Rounds 17–22 (third swarm — the operational layer)

**R17 — networking, player editing, saves.**
- **GGPO's sync-test IS our determinism gate pattern** ([ggpo doc](https://github.com/pond3r/ggpo/blob/master/doc/README.md)):
  rollback netcode is viable only after the simulation proves save/restore
  + re-execute to the same checksum. Our stepped-states-bit-identical
  doctrine is exactly the prerequisite — multiplayer costs us nothing NEW,
  it consumes what we already prove. Lockstep sends inputs, not state
  (Fiedler) — CA local rules + deterministic stepping is the lockstep
  dream substrate; cross-machine float determinism is the gate before
  networking is even discussed.
- **Player sculpting has two shipped shapes:** Dreams (SDF + flecks —
  contradicts triangles outright, noted as the thing we must beat) and
  runtime CSG on polygon meshes (the player-facing behavior our
  birth/death rules must reproduce). Teardown networks DESTRUCTION AS
  DETERMINISTIC COMMANDS, not mesh snapshots — edits as inputs fits the
  lockstep substrate perfectly.
- **Save format template:** Noita serializes per-chunk material grids +
  bodies, FastLZ-compressed, chunk-addressed, with a coarse density map
  for cheap queries ([Noita wiki](https://noita.wiki.gg/wiki/Technical:_File_Formats));
  Dwarf Fortress ships custom zlib block binaries. Our world saves the
  same way: per-cube-addressed chunks of triangle-cell state +
  a coarse acceleration map.

**R18 — retargeting, motion matching, UV-free texturing.**
- **Cross-topology retargeting exists neurally (2025, literally tested on
  a monkey skeleton, [arXiv:2508.13139](https://arxiv.org/html/2508.13139v1))**
  — but derive-before-train flags it. The deterministic path: Blender
  constraint-based retargeting (inspectable, no training).
- **Motion matching (For Honor, GDC 2016) is the shipped alternative to
  CPG gait** — database search per frame, no state machine. Learned MM
  (Ubisoft La Forge 2020) compresses it with networks = determinism
  threat. Verdict: CPG stays the derived route; motion matching is the
  fallback if the dyad rejects oscillator gaits. The hard part is mocap
  DATA for a monkey, not code.
- **Triplanar mapping is the doctrine-clean texturing path** — world
  position + normal drive the lookup, no UVs, ships as a built-in in
  engines. Runtime Virtual Texturing/MegaTexture: mutable caches +
  streaming = determinism threats; recorded, not adopted.

**R19 — the CA substrate's frontier, honestly.**
- **Our face-centered cells need their own kernel:** MeshNCA lives on
  VERTICES; our cells live at triangle CENTERS — the perception
  neighborhood must be re-derived face-to-face (the dual graph does this
  naturally; nobody has published face-cell NCA — white space, ours).
- **Conservation can be WRAPPED, not learned:** MaCE ([arXiv:2507.12306](https://arxiv.org/abs/2507.12306))
  attaches exact mass conservation to existing CA rules — the
  derivation-first answer to "the river must not invent water."
  Lenia/Flow-Lenia are continuous-state — beautiful, but contradict the
  discrete bit-identical substrate; recorded as the road not taken.
- **Crowds on meshes:** geodesic distance fields over the dual graph
  (I3D 2010); per-triangle LSCM charts + planar RVO2 = 140,000 agents
  real-time (SIBGRAPI 2015); CA-boids hit 1M on GPU but on grids —
  porting boids to the dual graph is an open derivation, named.

**R20 — eating the real world.**
- **The capture pipeline exists end-to-end:** photos → COLMAP/Meshroom
  (SfM+MVS) → 2DGS → TSDF mesh → OUR substrate. 2DGS mesh export feeds
  the 2D-only doctrine (capture → surfels → triangles is OUR direction).
  Threats catalogued: screened Poisson is watertight-BY-CONSTRUCTION
  (closes true openings — mask it); SuGaR/GOF are volumetric 3DGS
  (rejected); COLMAP's RANSAC/matching must be seed-pinned for
  reproducibility.
- **NKSR ([arXiv:2305.19590](https://arxiv.org/abs/2305.19590))** meshes
  millions of noisy points in seconds, learned — fast front-end,
  determinism risk; use for exploration, gate with measurements.

**R21 — sky, clouds, wind.**
- **The frost's reference illuminant is analytic:** Preetham 1999 /
  Hošek-Wilkie 2012 sky models + O'Neil LUT scattering give a
  deterministic time-of-day lighting rig with zero ray tracing — the
  sun the per-triangle light field trains against.
- **Clouds are the doctrine's hard case:** every shipped solution
  (HZD/Nubis ~2ms on PS4, Frostbite) is volumetric raymarching —
  contradicts 2D-only. Verdict recorded: clouds enter as surfel shells
  or not at all; nobody has done surfel clouds — white space, flagged.
- **Crysis-style vertex-shader wind is triangle-native and stateless**
  ([GPU Gems 3 ch.16](https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-16-vegetation-procedural-animation-and-shading-crysis)) —
  deterministic by construction, drives fur/vegetation/cloth. GPU
  particle gust fields (Ghost of Tsushima) need seed-pinning.

**R22 — where the MLP actually runs.**
- **The frost's runtime SHIPS AS AN SDK:** NVIDIA RTXNTC evaluates a
  small MLP inside pixel shaders today — `VK_NV_cooperative_vector`
  (2–4× on Ada/Blackwell) with a DP4a fallback for any SM6 GPU
  ([RTXNTC](https://github.com/NVIDIA-RTX/RTXNTC)). f(point, view,
  light) in the render pipeline is not speculative; it's an existing
  Vulkan path. Constraint: quantization + vendor math paths threaten
  bit-identical results — spec-defined math only, measured per-GPU.
- **NPUs: rejected as primary.** DirectML/OpenVINO NPU paths are
  Windows-gated, allow-listed, static-shape-only — wrong for per-pixel
  dynamic input. Possible training helper, never the runtime.
- **WebGPU = the demo layer, not the engine:** 4KB demoscene intros run
  3D fluid sims in-browser via WebGPU compute — our marketing demo can
  too. But dispatch overhead is ~24–36µs vs native Vulkan and Firefox
  rate-limits — the C++ Vulkan engine stays primary.

### SATURATION VERDICT (the research curve, honestly measured)

Three swarms, 22 rounds, ~45 searches direct + ~130 by agents. The curve
has flattened: swarm 3 repeated ~30% of prior findings (MeshNCA, Growing
NCA, Cells-to-Pixels recurring across topics), and new items arrived as
operational confirmations (RTXNTC ships the frost runtime; GGPO consumes
our determinism) rather than new directions. **Searching more would be
re-paying for what is already named.** What remains is not search but
READING and MEASURING: the primary sources worth reading cover-to-cover
before their lines start are — Nanite's SIGGRAPH course notes (L-engine),
RTXNTC SDK + Zeltner TOG 2024 (L5 frost), Growing NCA + MeshNCA (L4/L8),
virtual-pipes + MaCE (L7 water), ARAP lineage (L6 hinges), GGPO sync-test
(multiplayer gate). Research annex CLOSED unless the operator opens a
new territory; the falsifiers from here on are numbers we produce, not
papers we find.

### AGENT PACKETS (the prescribed deep-reads, executed)

- **FROST PACKET 01 — Big Pickle, `agent_logs/bigpickle/frost_packet_01.md`
  (audited, ACCEPTED 2026-08-27).** RTXNTC decode architecture + integer
  DP4a as the only determinism-lawful path; Zeltner 8-D latent + 3×64 MLP
  mapped to one latent per triangle row; Mitsuba `llvm` CPU backend viable
  (GLB→PLY via trimesh, no blender add-on needed); OpenIllumination CC BY
  4.0 as the held-out-light validator (DiLiGenT license UNVERIFIED).
  Debunked honestly: the "10×" figure belongs to the 2×32 model; real
  3×64 speedup ~1.6–2.3×. Named target mismatch: BRDF-fit ≠ relightable
  radiance — the falsifier measures the transfer. L5 falsifier: 128
  lights, 16 held-out, ≥30 dB PSNR vs Mitsuba.
  **hy3 CROSS-AUDIT (`agent_logs/hy3/frost_audit_01.md`) — 5 DISPUTES,
  ALL ADOPTED 2026-08-27:** H1 BRDF∫L misses self-shadowing/interreflection
  (fix: AO stratification); H2 the 30 dB bar was mis-sourced from
  per-texel-pyramid territory (fix: measured baseline); H3 16 held-out
  underpowered (fix: ≥32–64 stratified, per-band PSNR); H4 DP4a is
  decode-only, weights stay fp16 (bit-exactness needs weight quantization,
  unshipped, UNVERIFIED); **H5 FATAL: 512–2048 SPP ground truth has a
  ~27–30 dB noise floor = the bar itself — as specced the falsifier
  measured Monte-Carlo error, not the model (fix: SPP ≥8k, integrator
  pinned).** Doctrinal intent CONFIRMED; experiment design amended.
  **FROST PACKET 02 (`agent_logs/bigpickle/frost_packet_02.md`) —
  ACCEPTED 2026-08-27, experiment now decision-free:** SPP=8192 derived
  (10·log₁₀(SPP)≈39 dB ceiling, >10 dB over the expected baseline);
  integrator pinned path+RR, `direct` quarantined; Fibonacci-sphere 128
  train + 64 held-out lights with an 8° separation gate; AO = 1024
  rays/triangle (binomial-std derivation), ε=1e-4·D, pass cursor = the
  OCCLUDED band only; bar = measured baseline B0_occl (prediction
  B0∈[29,35] tagged as prediction); weight-int-quantization cost X=1.0
  dB openly labeled a policy anchor inside the proven 0–3 bound;
  OpenIllumination validated separately, DiLiGenT EXCLUDED on license.
  Dispatch table: PASS ⇒ engine integration; miss ≤3 dB ⇒ dual-graph
  neighborhood-context latents; miss >3 dB ⇒ per-triangle premise
  FALSIFIED. No further audit round — the experiment is the arbiter.
  Awaits a construction slot (needs `pip install mitsuba` into
  `.venv-hy3d`, verified absent). **Stack probe (`agent_logs/freeagent/frost_stack_01.md`,
  2026-08-28): mitsuba pip wheel ships `cuda_ad_rgb` PREBUILT on
  Windows (fast referee = an install, not a build); nvdiffrast =
  source build from GitHub, CUDA 12.8 toolkit present; OpenIllumination
  879 GB total but ungated with a download script — take ONE object's
  OLAT subset (~14 GB); disk fine (~1.4 TB free). **VERIFIED
  (`agent_logs/freeagent/verify_01.md`): `cuda_ad_rgb.cp311-win_amd64.pyd`
  physically in the wheel (zip listing, 45 MB wheel preserved in
  scratch, NOT installed); OI subset fetch = `--light OLAT --obj_id N`,
  OLAT/ separate from lighting_patterns/, no gate; per-object size
  UNVERIFIED (~13.7 GB avg estimate). Frost experiment fully
  de-risked: referee, optimizer, validation, disk, machine — all
  measured green.**
- **PHYSICS PACKET 01 — hy3, `agent_logs/hy3/physics_packet_01.md`
  (audited, ACCEPTED-WITH-AMENDMENTS 2026-08-27).** DEC cotan-Laplacian
  on our dual graph; virtual pipes ported to per-edge signed flux;
  MaCE REJECTED as redundant + float-family; hinge = Dirichlet ring +
  smooth-ARAP skin; Owaki decentralized CPG mapped to hinge cell phases.
  **Big Pickle CROSS-AUDIT (`agent_logs/bigpickle/physics_audit_01.md`) —
  CONFIRMED: mass conservation (valence-independent, manifoldness
  required), barycentric positivity (qualitative), T_vol arithmetic.
  FATALs ADOPTED: (1c) clamp bounds swapped — non-negativity dies, fix
  `clamp(δ,−V_j,+V_i)`; (3) CFL mis-derived — gravity celerity √(gd)
  binds, not |q|/A; global l_min freezes on slivers — needs local/
  subcycled dt; (5) ν≈0.49 is a DESIGN CHOICE laundered into a
  "DERIVED" T_vol — fictional tissue has no Poisson ratio; re-derive
  T_vol as O(ε²)≈4.8e-4. DISPUTED: barycentric dual costs
  linear-exactness (Alexa–Wardetzky impossibility — name it, don't
  understate); ε_phase ill-posed as one global std across non-identical
  joints. Nothing ships tagged DERIVED until hy3's revision lands.**
  **REVISION LANDED — PHYSICS PACKET 02 (`agent_logs/hy3/physics_packet_02.md`),
  all five revisions ADOPTED 2026-08-27:** R1 clamp corrected with P2+F2
  proven together + explicit manifoldness/A_min preconditions; R2 CFL on
  √(gd) with local subcycled dt (0.76·l/c regular-mesh, irregular
  C_sw → measured from dual-graph λ_max) + integer volumes/pinned float
  schedule; R3 ν=0.49 openly CHOSEN, T_vol=O(ε²)≈4.8e-4 via the Jacobian
  argument; R4 Alexa–Wardetzky named, keep positivity / surrender
  linear-exactness with O(h·μ) hydrostatic bias, conductance/mass
  formulas fixed; R5 per-pair phase lag bands + hysteresis-width gait
  transition. Awaits one confirmation audit; the audit loop TERMINATES
  when remaining disputes are experiments, not proofs.
  **PHYSICS DYAD CLOSED — Big Pickle confirmation audit
  (`agent_logs/bigpickle/physics_audit_02.md`), 2026-08-27:** C1 clamp
  CONFIRMED (caveat: δ must be integer-quantized with integer V);
  C4 dual trade + C5 gait falsifiers CONFIRMED (R4 one-liner has a
  units slip, m/s vs m → reference-run verification); C2 CFL prefactor
  CORRECTED 0.76→≈0.56 (honeycomb λ_max=(3+√6)κ/A≈5.45κ/A, not 3κ/A) —
  DISPUTED-WITH-EXPERIMENT, decided by power-iterated λ_max of the
  actual dual; C3 T_vol mechanism right but tr(ε)=O(ε²) was asserted —
  honest bound 3ε_max≈6.6e-2 vs claimed 4.8e-4 —
  DISPUTED-WITH-EXPERIMENT, decided by measured C_iso over one ROM ARAP
  solve. No new proof-level FATAL; the loop closed per its own rule,
  and three named measurements ride into the L6/L7 construction prompts.
- **Cross-audit PROTOCOL:** each packet's author audits the other's work
  adversarially; disagreements get measured, not argued. Frost side:
  5 disputes adopted into L5 (no packet rewrite needed — design params).
  Physics side: packet 01 → audit → packet 02 (above) → confirmation
  audit, then closed.
- **WATER PACKET 03 — hy3, `agent_logs/hy3/water_packet_03.md`
  (ACCEPTED 2026-08-28):** L7 construction membrane, decision-free —
  recorded in row L7.
- **GAIT PACKET 01 — hy3, `agent_logs/hy3/gait_packet_01.md`
  (ACCEPTED 2026-08-28):** the L6-successor membrane. Phase map from
  the MEASURED ROM literals (L θ_mid=71.22°/θ_amp=73.72°; R 55.60°/
  59.22° — arithmetic re-verified against THE_ARTISTS_SOLID.md:619);
  per-pair bands = a reference-run measurement, not a tolerance; load
  = contact impulse from the deterministic Baumgarte solve with the
  estimator family picked by a named experiment; ω-sweep [π,4π] with
  hysteresis + transition-time falsifiers, metamorphic rotate-world,
  ULP-identical two-seed phase series; energy honesty = bounded
  mechanical work per stride, COT anchor CHOSEN-UNVERIFIED. Awaits
  Quinn's hinge to drive; Big Pickle audits next.
- **FROST-GROWTH PACKET 01 — hy3, `agent_logs/hy3/frost_growth_packet_01.md`
  (ACCEPTED 2026-08-28):** the frost's GROWTH half (L5 split: Big Pickle
  owns the light answer, hy3 owns the rule). DLA walkers diffuse on the
  triangle dual graph via the SAME R4 conductance Laplacian as water
  (one Laplacian, not two); stick p=1 (DLA; <1 = DBM — harmonic-measure
  limit honestly stated); seeded xoshiro256** + fixed-point thresholds ⇒
  bit-identical; frost lives in the cube column above each triangle and
  writes {frost_coverage, frost_height, frost_blend} into the triangle
  row — the interface to Big Pickle's light half; integer-exact
  conservation Q_f=A_min·e_cube; falsifiers = D_f literature band,
  cube-veto, non-conservation, part-seam continuity; shedding stretch
  tagged CHOSEN-UNVERIFIED. Big Pickle audits — the D3 handshake is its
  special hunt.
- **RUNTIME PACKET 01 — hy3, `agent_logs/hy3/runtime_packet_01.md`
  (ACCEPTED 2026-08-28):** the substrate's GPU law. SSBO default gated
  by a falsifiable ≥2× microbenchmark (not the forum anecdote);
  canonical order (part → triangle index → edge key),
  subgroup-independent; conserved mass integer (Q/Q_f), floats pinned
  no-FMA fixed-order; all three kernels atomic-free (2-pass water,
  min-id DLA claim, Jacobi ARAP); **the fast/slow subcycle seam SOLVED
  by the integer design itself — antisymmetric δ cancels at any step
  count**; GGPO-style sync-test against the golden CPU reference gates
  rendering; probe table: coop-vec frost path, DP4a fallback, mesh
  shaders OFF by default. Big Pickle audits.
- **SOUND PACKET 01 — hy3, `agent_logs/hy3/sound_packet_01.md`
  (ACCEPTED 2026-08-28):** the substrate hears itself. Modes =
  generalized eigenproblem on the dual graph with the LANDED T2
  stiffness (zero free numbers) + M=A·thickness·ρ (thickness,ρ openly
  CHOSEN); honest surface-vs-volumetric scope (keeps the audible
  flexural/membrane modes, thin-shell Blevins reference); excitation
  reuses the gait packet's contact-impulse channel (one sensor, two
  senses); runtime = precomputed mode bank, sparse LOBPCG to a
  MESH-DERIVED Nyquist (~14 kHz on SALLY_body_0) + component-mode
  synthesis, ~1.2 GB; monopole Rayleigh transfer; falsifiers = pitch
  band, Weyl mode-count bound, and the refinement-chirp (modes must
  converge under 2× refinement — discretization-agnostic or FAIL).
- **BIG PICKLE AUDITS ×3 (2026-08-28, all ADOPTED with one downgrade):**
  **frost-growth audit (`bigpickle/frost_growth_audit_01.md`) — D3
  handshake FATAL ADOPTED:** {coverage,height,blend} starves the light
  half; the lawful fix is DERIVATION, not more fields — normal
  perturbation = ∇(frost_height) on the dual graph, ONE shared frost
  material (snow is optically uniform), cluster IDs from the runtime's
  min-id claim scheme; RNG model disagreement between packets must
  reconcile to the runtime's per-id partitioned stream; D_f band gets
  a honeycomb-baseline validation experiment. **Runtime audit
  (`runtime_audit_01.md`) — 3 DISPUTED ADOPTED:** V4 is
  conserved-but-WRONG at the time-lagged interface (O(Δt_slow) error +
  sub-Q stalling — quantify vs sync interval M); the sync-test has a
  FLOAT blind spot (integer checksums pass sub-ULP ARAP ordering bugs —
  add a float-state tier); the SSBO bench must cover all three kernels
  on aggregate frame time. **Sound audit (`sound_audit_01.md`) — S1
  FATAL ADOPTED** (t-free bending + t-mass ⇒ ω∝t^(−1/2), backwards
  plate physics; re-derive D∝t³); **S5 F3 DOWNGRADED to
  DISPUTED-WITH-EXPERIMENT** — the audit's scaling argument is
  element-level (k∝1/A₀, M∝A); what matters is GLOBAL-mode convergence
  under refinement, which IS the packet's own F3 — the measurement
  arbitrates, not either mind's prose; Nyquist re-derived from the
  lattice Debye/carrier cutoff (air 343 m/s was the wrong speed);
  Weyl storage estimate must quantify the patch share. hy3 revisions
  issued for all three packets.
  **REVISIONS DELIVERED + ACCEPTED 2026-08-28:** frost-growth 02
  (D3 closed — ∇(frost_height) normals via R4 weights, one shared
  CHOSEN roughness, cluster IDs from min-id; RNG reconciled to per-id
  partitioned stream; honeycomb D_f baseline experiment added);
  runtime 02 (V4 honestly renamed "conservative first-order-at-
  interface" with O(Δt_slow) bound + sub-Q stalling quantified, M from
  measured budget; float Tier-1b ULP-exact same-GPU; bench = all
  three kernels, aggregate frame time); sound 02 (S1 closed —
  D∝K_BOND·t³ ⇒ ω∝t; S5 F3 = global-mode convergence measurement
  with expected FEM rate; Nyquist from lattice Debye speed; Weyl
  re-checked with patch share). Confirmation audits queued behind
  Big Pickle's eye packet. **LING CONFIRMATION AUDITS
  (`agent_logs/ling/confirm_audits_01.md`, 2026-08-28): all three
  pairs CONFIRMED, zero FATALs — the frost-growth/runtime/sound
  revision cycles are CLOSED.** Ling's own catch recorded: the sound
  audit's 14 kHz Nyquist cited l_scale_med=0.012259 but the real JSON
  says 0.04835 — the audit was wrong, the revision's Debye approach
  right; a Flash-class model catching a heavyweight's misread
  validates the bounded-verification lane.
- **FUR PACKET 01 — Big Pickle, `agent_logs/bigpickle/fur_packet_01.md`
  (ACCEPTED 2026-08-28):** the chimera's surface. Shells = displaced
  triangle copies bound to the ARAP solve by re-displacement along the
  transformed normal (fur follows the hinge band, never left behind);
  density = curvature-weighted reaction-diffusion CA grown from the
  genome (Turk/Staddon line; dyad falsifier: "teddy reads plush,
  monkey reads monkey"); frost grows on the OUTERMOST shell (cube
  columns seed it there — fur × frost × light field compose); one
  shared latent across shells via packet-02 decode; **falsifier:
  fur that eats the frost's view-dependence (fuzzy lambert) = FAIL —
  the mirror doctrine survives the pelt**; rim fins derived, visual
  effect tagged CHOSEN-UNVERIFIED at our tri sizes; LOD from
  screen-space triangle size; hinge-sweep falsifier: zero shell/skin
  separation at the ring across the full ROM. hy3 audits.
- **KIMI-SUBAGENT DELIVERABLES (2026-08-28 — the operator's "how far can
  your own subagents go" test, 3/3 landed, all ACCEPTED):**
  **TEDDY PACKET 01 (`agent_logs/kimi/teddy_packet_01.md`, 465 lines):**
  candidate 33ef76f2 NOT on disk (web record only; fitted parts
  LEGACY-UNMEASURABLE — best on-disk kin teddy_honey.glb chamfer 0.035);
  **one-mask skeletonization FAILS on plush — falsifier FIRED and
  standing (164 components vs ≥0.95 bound, 310 rods vs ~15, no σ
  plateau — morphological, not parametric); lawful substitute = the
  recorded capsule fit (15 primitives)**; 9 hinge sites measured
  (plush ROM is belly-contact-limited); CHOSEN-FROM-DERIVED-CANDIDATES
  formalized (table hash, row, interval); corrections to the record:
  cad_bear NOT watertight as claimed (pole pinches + exactly 2,400
  degenerate tris — vertex weld, not birth), teddy_honey = wounded
  soup (36% boundary edges); C_sw measured (honey 0.0822, cad_bear
  0.239–0.269); T4 plane rule hardened (recorded head axis = degenerate
  eigenvector, retired; bilateral witnesses win; mirror-minimization
  instrument validated exact on cad_bear).
  **EYE PACKET 01 ×2 — a divergence, recorded:** `agent_logs/kimi/
  eye_packet_01.md` (PRIMARY — measured the actual sockets first:
  lip r=0.240/throat r=0.212 at 0.132 depth, brow clearance 0.004 the
  honest weak point; E1 = registrations of existing triangles; E2 =
  closed-form Snell remap + caustics via flux conservation ∫(C−1)dA=0;
  E4 pupil integer-quantized, bands derived) vs
  `agent_logs/bigpickle/eye_packet_01.md` (ALTERNATE — excludes eyes
  from frost GT as "tiny high-curved blobs"; kimi packet instead:
  cornea analytic GT + Mitsuba scene of the registered stack, frost's
  128/64/SPP-8192 bar inherited). The blind A/B dyad arbitrates the
  contested choices (η=1.376 both).
  **ATTRIBUTION DRAFT (`agent_logs/kimi/attribution_draft_01.md`):**
  all 5 monkeys with authors (muneto_bm, dinesdiabolik, TdoubleU8,
  saranav, gooseman — CC-BY-4.0 each, per-model URLs) + teddy (CC0) +
  OpenIllumination + MatSynth BibTeX — the ship-required file drafted;
  TEDDY BENCH ×3 (hectopod 34.8k CC-BY, sharetextures 14k CC0, Mathias
  199.7k CC-BY) as backups to the single candidate.

## 10 · HERITAGE LEDGER (the 32 continuations, compressed)

Key run records behind §4/§5, newest last: T2 CA pre-registration →
degenerate-nan gate → T2 landed → run-record audit ("pass" prose corrected)
→ Option B derived rest-area → curvature exterior landed both meshes → T13
SFC falsified → octree option-(a): byte-identity, B1 njit 15×, pool, CA-walk
swap → doctrine: Wolfram frame, Earth gravity canonical, UE excised, island
retired → appearance messenger + dyad movie fix → SWING/UPRIGHT/RHYTHM_DRIVE
closed → 10-task swarm (P1–P10) integrated → Phase 0 closed → corpus 5/5 →
THE ARTIST'S SOLID (CAD-first decree) → substrate view dyad-closed 0.95 →
build queue BET-F2/J1/W1 specced → research annex 22 rounds saturated →
frost + physics packets cross-audited to law → **Phase 4 landed
(`994bb4e0`): registry 100/100 on 5 GLBs, birth rule literal FALSIFIED /
occupant-veto PASS, dyad NO COMPLAINTS 0.96** → **L6 torn-leg fix (`90ad2a2e`):
geodesic sets both knees, TORN-SHEET earned, F1 placebo exposed**. Full text:
git history of this file.

## 11 · THE MAIN-AGENT METHOD (2026-08-28 — written after the torn-leg fix, binding on main-agent construction work)

How the "unfixable" right leg was actually closed; the sequence any agent
inherits when the local agents stall. Full version:
`agent_logs/kimi/leg_fix_01.md` §"The method".

1. **Reproduce from evidence, not testimony** — trace which script staged
   which set into the view the operator saw; never debug an unsourced render.
2. **Classify before solving** — colored-set diagnostic at REST (rigid/ring/
   free/pinned) before believing anything about the dynamics.
3. **Measure the root cause, name it with numbers** — a cause you can't point
   at (triangle count, weld-group id, coordinates, spread) isn't a cause.
4. **Fix with the ratified law, not a patch** — geodesic-on-dual-graph, weld
   scan over ALL weld groups; extents derived from the working side, never
   chosen (hop limit H=42 came from the left set, not taste).
5. **Earn new checks from the failure** — TORN-SHEET + global split-weld-group
   count exist because this bug taught us what to measure; they gate now.
6. **Cross-check against known-good** — the new law must reproduce the one
   working case exactly (left set symmetric diff 0) or the law is wrong.
7. **Record the honest negatives with the win** — placebo exposed, rest
   baseline named, model limitation named; verify the render with your own
   read before claiming; commit with the evidence trail.

**Operating layer for all agents (2026-08-28, operator decree):**
`docs/THE_OPERATING_MANUAL.md` is the workflow — ownership boundaries, the
six-step loop (READ → MEMBRANE → BUILD → MEASURE → REPORT → HAND BACK), the
paste-back format, the earned-blocked rule, and the task-envelope template
every legal task arrives in. `docs/THE_TRIANGLE_GUIDE.md` is the domain laws.
Weaker agents operate by those two documents, pointed at from `AGENTS.md`.
