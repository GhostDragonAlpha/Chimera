# THE ROADMAP — the whole future, as far as it can be thought

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done.
<!-- CHIMERA-LAW -->

> Commissioned by the operator, 2026-08-26: *"Shape the entire roadmap for this project and think
> out the entire future as far as you can, with monetization as the goal. We can never take the
> easiest route, otherwise we will never compete."*
>
> Grounded in three research streams executed the same day:
> `Chimera/research/open_source_physics_landscape_report.md` (physics methods),
> the splat/render survey (gsplat · vk_gaussian_splatting · SplattingAvatar · Filament · FlashGS),
> and the monetization survey (BeamNG · Teardown · Noita · Shapez.io · Mindustry precedents).
> Slot #0 remains `docs/THE_WOLFRAM_FRAME.md`; where older prose conflicts, it wins.
>
> **This file POINTS at live state; it does not copy it.** The dated snapshot in §1 is a snapshot —
> `python tools/orient.py` and `docs/THE_MASTER_LIST.md` are the live reads.

---

## 0 · THE PRODUCT THEORY

**STATEMENT.** Chimera is a space game that is a *film of a computation you can enter*: one kernel
of simple local rules, run — not authored — over a triangle carrier, read by light, judged by a
human. The thing nobody else ships is the weld: physics, rendering, and control are ONE system
read three ways, and every visible detail is a physical consequence, never a decoration.

**The sentence this roadmap exists to earn:** *"How did he make something so beautiful with just
triangles alone?"* — where beauty means **perfect in the reality of light to which the concept
belongs**. A bear's fur-lit softness, a hull's cold specular, a knee's honest arrest at its stop:
each concept rendered in its own physics, no aesthetic passes, no borrowed realism.

**PREDICTION.** A physics-first clip of the bear — standing, walking, deforming under its own
tissue, lit honestly — posted cold, outperforms any authored-art teaser the same channel could
produce, measured in raw views/engagement. (Tested the day the bear walks; the monetization
survey's viral-clip evidence — Teardown, Instruments of Destruction — is why this is a prediction
and not a hope.)

**FALSIFIER.** If the honest-physics renders, judged by the operator's eye at each feature
boundary (Wolfram §8), do not produce a visibly *better* image than a conventional PBD/PBR stack
at equal effort, the moat is imaginary and Phase 2+ must be re-planned around adopting
`PositionBasedDynamics` instead of the CA carrier. The dyad is the judge; a monad is never proof.

**Why the hard route is the route.** The research verdict: Chimera invents no new equations —
XPBD, FEM, IPC, PBD all exist open-source, and Genesis/Newton (Apache-2.0, NVIDIA/Disney/DeepMind)
are coming for the same GPU-resident deformable space. What does not exist anywhere is the
*integration*: CA local rules on a triangle carrier + ROM extremes declared and the in-between
*trained* + dirty-set economy (V62: a settled world costs ~nothing to hold) + physics/render/
control in one buffer. Anyone can adopt an easy component; nobody can cheaply copy a weld. **The
easiest route is the one route guaranteed to be commoditized.** That is the whole strategy.

---

## 1 · WHERE WE STAND (dated snapshot, 2026-08-26 — re-read live, never trust this copy)

Live reads: `python tools/orient.py` · `python tools/verdict.py status` · `docs/THE_MASTER_LIST.md`.

- **Term ladder:** `theStory`, `theSeed` proven (dyad 0.85). Current term `theDeterminism`:
  S0–S3 done; S4 bit-identical-trajectory experiment specified in `docs/THE_DETERMINISM_S4.md`,
  not yet run. Engine state and the S4 doc disagree about APPEARANCE MESSENGER — reconcile first.
- **The launch metric: 3.10 s** (seconds held at forward=0.5; target: minutes). The walk lane is
  the front line: F4 fired (travel 16% of derived speed, upright 2.98/6.0 s).
- **The carrier works:** bear CA run PASS — RUN A rel err 2.5e-9, energy gate PASS, max strain
  2.19%, band held. Bone rig drives the real teddy mesh (30,768 verts, LBS) — commit `a4b5ff31`.
  P6/P7/P8 (tissue interfaces, rig, in-between harness) PASS. Octree build byte-identical at
  12× per-tick (B1); 24-core parallelism falsified twice and still open.
- **T4 fired:** 1M points at full walk cost = 0.7 fps. The million budget survives as
  *reallocation doctrine* (LOD toward the player's light), not fixed-cost-full-walk.
- **Known rot:** Wolfram §5's failure list is stale (JOINT_LIMIT/SWING/UPRIGHT/RHYTHM_DRIVE/
  END_STOP now PASS); LAND is conflicted between docs; `matter_library.json` absent (3/21 ports
  error on missing data); 19 publishedology minting groups; 3 allometry audit findings
  (human-norm torques on a teddy bear — F-1 400 N·m HIGH).
- **Assets:** cad_bear (57,312 CA tris, 19 watertight shells, UV atlas), teddy native genomes +
  T-pose rig, fur sheet selected (seed 3, wrap 0.92). All provenance intact.
- **Engine:** C++/Vulkan renders splats, meshes (depth-correct), skinned splats; movie + dyad
  judgment pipeline live (LM Studio vision eye). Splat lane deferred per Wolfram §12.

---

## 2 · THE MOAT MAP (what the research found, and what we do about it)

| Finding | Classification for us | Doctrine response |
|---|---|---|
| **Genesis World, Newton (Warp+MuJoCo)** — unified GPU deformable sims, Apache-2.0 | COMPETITOR | They are platforms; we are a *world*. Study their compiler/render architecture; never adopt their solver as our truth. |
| **PositionBasedDynamics (RWTH, MIT)** — XPBD/SBD/shape-matching on tri/tet meshes | COMPONENT-GRADE BASELINE | The instrument-control: run our carrier against it on a known answer (EM-12). If it beats us honestly, see §0 FALSIFIER. |
| **DiffPD / DiffXPBD** — differentiable position dynamics | REFERENCE | The math for training the in-between from physics objectives instead of sweeps. First literature scan of Phase 1. |
| **VegaFEM / SOFA / AMD FEMFX** | REFERENCE | Published accuracy + material-law anchors for publishedology docking. |
| **INRIA license dominates 3DGS academia** (3DGS, 2DGS, SuGaR, Mip, GOF, GaussianAvatars…) | TRAP | Reference only. Runtime frosting builds on permissive code: **gsplat (Apache), FlashGS (MIT), vk_gaussian_splatting (Apache)**. |
| **SplattingAvatar** — splats bound barycentrically to an *animated primary mesh*, 300 fps | THE ARCHITECTURE (CC-BY-NC — study, never ship) | Clean-room the binding math (barycentric + displacement + pose-dependent deltas) on permissive kernels. This *is* the frosting seam. |
| **Filament (Apache)** — canonical honest PBR/HDR/tone-map | REFERENCE | The light model for Phase 3. Khronos PBR Neutral tone mapper. |
| **Monetization:** physics hook sells millions (BeamNG ~$130M, Teardown ~$55M, Noita ~$26M) **when paired with a game loop**; middleware licensing is dead as a first revenue (Havok acquired, PhysX free) | STRATEGY | Sell the GAME on Steam; AGPL engine + commercially-licensed assets (Mindustry/Shapez model); middleware only post-proof. |

**The uniqueness ledger (what we keep because no one else has it):** the weld (derive/emit same
file, one buffer) · ROM-extremes + trained in-between · dirty-set economy · allometry as law
· publishedology as gate · the dyad itself. **The rule: every roadmap item must strengthen at
least one of these, or it is the easiest route wearing a plan.**

---

## 3 · THE PHASES

Every phase ends at **the human visual checkpoint** (Wolfram §8): a movie through the real engine,
judged by the operator's eye. No phase gate is self-reported.

### PHASE 0 — CLOSE THE CURRENT FRONT *(weeks; no new ambition until honest)*
The repo cannot compound on contradictions.
1. Reconcile engine state vs `THE_DETERMINISM_S4.md`; run the **S4 bit-identical trajectory
   experiment** (extend `tools/ci_determinism.py`; falsifier 1e-15, verdict-flip).
2. Doc-rot sweep: refresh Wolfram §5's stale failure list, resolve LAND's conflicted status,
   fix THE_COMPILER's stale primitive table, apply the `matter` twin-merge or repopulate
   `matter_library.json` (3/21 ports are missing-data errors, not physics failures).
3. Allometry F-1/F-2/F-3: derive test loads from the body's own actuators (the audit's proposed
   fix), killing the last human-norm torques.
- **FALSIFIER for the phase:** any of the "fixed" ports re-fails under body-derived load — then
  the load, not the port, was the defect, and the walk lane re-opens there.

### PHASE 1 — THE BEAR WALKS *(the launch metric: minutes, not 3.10 s)*
Train the in-between (Wolfram §5): structure AND physics across the ROM, both tracks together.
1. Literature scan first (Rule: derivation starts from print): DiffPD/DiffXPBD for objective-from-
   physics training; capture-point + contact-entrained oscillator literature for gait.
2. The named needs: moving-base stand term · swing-terminating stop condition · passive tissue
   for subtalar/MTP/hip rotation stops (universal passive-tissue port per THE_COMPILER).
3. Statics P-A/P-B for the levers (`story/theStance/numbers.json` exists — the "blocked" note is
   stale); levers wired into the kernel DSL universal layer.
4. **THE MOMENT:** the teddy walks across the frame with deforming tissue, honest arrest at every
   stop, lit plainly. Operator eye judges. This is the first clip the outside world ever sees.
- **PREDICTION:** seconds-held at forward=0.5 goes 3.10 s → ≥60 s; periodicity 0.13 → ≥0.8.
- **FALSIFIER:** training improves the number but the operator's eye says "that's not walking" —
  the objective is wrong, not the search; iterate the objective, never the artifact.

### PHASE 2 — THE TRIANGLE WORLD *(the kernel becomes a place)*
1. **LOD reallocation** (T4's successor): the million-point budget as conservation law — points
   reallocate toward the player's light; near rich, far aggregated. V62 already proved the hold
   costs ~nothing; this spends the saving on *change near the eye*.
2. **Passive tissue universal:** grass, rock, tree, wall, hull through the same ports
   (THE_COMPILER's doctrine) — the world is made of stuff because everything runs the same rules.
3. **The 24-core/GPU question, round 3:** B2-A falsified (0.93×), candidate B retired. Next
   membrane: profile-first — the persistent-pool floor is ~101 ms on T4-1M; the honest question
   is whether the *walk* (GPU) or the *build* (CPU) gates the frame at world scale.
4. **Determinism ladder → levers+seed replication** (the multiplayer/lockstep foundation; the
   checksum falsifier from the retired door lane still applies: drift = the box is a participant).
- **FALSIFIER:** reallocated LOD produces visible popping/swimming the operator's eye rejects —
  the aggregation law, not the budget, is wrong.

### PHASE 3 — LIGHT *(the sentence gets earned)*
Beauty = perfect in the reality of light to which the concept belongs.
1. **Honest PBR in the Vulkan engine**, Filament as reference: linear HDR, split-sum IBL,
   inverse-square punctuals, Khronos PBR Neutral tone map. Deformed normals recomputed from the
   CA state — lighting responds to strain, or the weld is decorative.
2. **Aliveness:** wrap/SSS approximation for skin and plush (GPU Gems 3 ch.16 — a published
   anchor, not a taste knob); dynamic occlusion; mesh-shader/GPU-driven path if draw calls gate.
3. **THE FROSTING RETURNS** — splats bound to the deforming mesh: barycentric + displacement +
   pose-dependent deltas (SplattingAvatar's math, clean-roomed; gsplat/FlashGS kernels; the
   vk_gaussian_splatting depth-interop pattern: mesh G-buffer → sorted splats depth-tested
   against it). The kept provenance: `ChimeraEngine/core/splat_mesh.py`, the fur sheet, the UV
   chain (bit-exact to link 5).
4. **The dyad on material truth:** the eye reads the same concept bare (triangles) and frosted
   (splats); the frosting must add richness *without contradicting* the physics term — e.g.
   strained fabric reads strained in both.
- **PREDICTION:** frosted render scores higher dyad alignment on material terms ("plush", "fur",
  "worn hull") than the bare render at equal physics.
- **FALSIFIER:** the frosting hides or contradicts a physical state (strain, contact, motion) the
  bare mesh showed — then splats are an aesthetic pass, the exact defect Phase 3 exists to kill.

### PHASE 4 — THE GAME *(the hook gets a room)*
The monetization survey's core warning: physics is the door, not the room. Instruments of
Destruction ate a 16% refund rate on a thin campaign under a great trailer.
1. **The loop, operator-decided (taste terminal, listed in §5):** candidate spine — *"the space
   game where things are actually made of stuff"*: ships crumple, cargo shifts, creatures bruise,
   salvage means separating bonded matter. Space supplies scale and isolation; the physics
   supplies the tactile payoff. Six directions from the anchor budget what gets built.
2. **Levers as the control scheme** (THE_LEVERS): intents ∈ [0..1], behavior on inputs never
   state — already the doctrine; the game speaks levers end-to-end.
3. **UGC/creation:** CAD-authored bodies enter the same pipeline the bear did (scan → genome →
   matter). Players building things that *behave* is the BeamNG/Besiege long-tail engine.
- **FALSIFIER:** playtesters (operator first) engage the physics sandbox and bounce off the loop —
  no amount of Phase 3 beauty patches a missing game; return here before more rendering.

### PHASE 5 — MONEY *(monetization is the goal; here is the ladder)*
Ranked by the research; the full report is the source.
1. **Sell the game on Steam (primary), itch (secondary).** AGPL engine as trust/values signal +
   commercially-licensed art/audio/writing (the Mindustry ~$9.7M / Shapez.io ~$1M model, both
   open code + paid Steam). Anchor: 50–100k units at $20–30 = $1–3M gross.
2. **Tech-demo-led funnel, starting NOW, not at launch:** the 3.10 s → 60 s walk, the first
   honest-light bear, the frosting reveal — each is a 15–30 s clip. Precedent: Instruments of
   Destruction turned a trailer into 25k wishlists in 3 weeks; physics clips are the one format
   that markets itself. Steam page live early; Next Fest demo 3–6 months pre-launch; influencer
   keys to physics-game YouTubers.
3. **Early Access + DLC/live content** once the loop holds (Besiege/Trailmakers long-tail model).
4. **Middleware/consulting — post-proof only.** Havok got acquired; NaturalMotion exited; PhysX
   is free. Nobody buys physics from a studio with no shipped title. After a hit, the weld
   becomes licensable — and AGPL makes *dual-licensing* the natural instrument (AGPL gratis,
   commercial license for closed use). Decision deferred; recorded here so it is never a
   first-revenue fantasy.
- **AGPL×Steam mechanics:** keep Steamworks SDK integration in a thin separate wrapper or avoid
  deep integration (Valve's open-source distribution rule); assets under a separate commercial
  license from day one — retrofitting is the expensive path.

---

## 4 · THE ANTI-ROADMAP — routes we refuse, and why refusal is the strategy

- **No closed engines, ever.** UE was excised; Genesis/Newton are study-objects, not organs.
- **No adopting a solver as our truth.** PBD/XPBD is the control instrument, not the physics.
- **No INRIA-licensed code in the product.** The frosting is reimplemented on permissive kernels.
- **No aesthetic passes.** A colour is a measurement; beauty is the light of the concept's own
  physics. The instant a look needs a fudge, the physics is wrong.
- **No middleware-first monetization.** The game proves the tech; then the tech is for sale.
- **No parameter sweeps, no minted constants.** Publishedology and allometry are gates, not
  vibes — 19 minting groups are already flagged; zero is the target.

## 5 · OPERATOR DECISION POINTS (taste terminals — yours, never mine)

1. **The game loop** (Phase 4.1) — the one decision no physics can make.
2. **Art direction of the first public clip** — which reality of light the bear debuts in.
3. **Pricing/EA timing** — after Next Fest data exists, not before.
4. **Dual-licensing posture** — whether commercial licensing of the weld is even on the table
   (doctrine question, not business question).
5. **ENOUGH** — depth calls at every saturation point, as always.

## 6 · THE IMMEDIATE QUEUE (next turns, in order)

1. Reconcile `theDeterminism` engine-state vs S4 doc; run the S4 bit-identical experiment. *(Phase 0.1)*
2. Doc-rot sweep: Wolfram §5 staleness, LAND conflict, matter twin-merge / `matter_library.json`. *(Phase 0.2)*
3. Allometry F-1: body-derived test loads. *(Phase 0.3)*
4. DiffPD/DiffXPBD literature scan → the in-between training objective, derived not swept. *(Phase 1.1)*
5. First public-clip candidate: the bear standing in honest light, operator's eye the gate.

---

## THE HONEST BOUNDS

- **Genesis/Newton may eat the platform space while we build the world.** The bet of this
  roadmap is that a *welded world* outlives a *general solver* the way BeamNG outlived generic
  soft-body middleware. It is a bet. §0's falsifier exists to call it.
- **T4's falsifier stands:** nobody has proven the million at frame rate. Phase 2's LOD doctrine
  is a theory with a named test, not a result.
- **The monetization numbers are third-party estimates** (review-count inference), cited as
  directional in the research report, not audited.
- **An LLM wrote this roadmap; an LLM is never a terminal.** The phases are theories with named
  falsifiers; the operator's eye decides every boundary. The plan can lose. That is what makes
  it a plan instead of a description.
