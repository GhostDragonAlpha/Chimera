> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# UE 5.8 AAA Tech Roadmap — Deep Space Trader (Chimera)

> Research date: 2026-07-11. Supersedes nothing; this maps UE 5.8 engine capabilities and the
> Claude Code / pi agent toolchain onto the existing spiral-loop plan (`chimera_triple_a_roadmap.md`,
> `AAA_DEVELOPMENT_ROADMAP.md`). Everything here is sourced from Epic's 5.8 release material,
> current Star Citizen tech disclosures, and the current pi / Claude Code feature sets.

---

## 1. GDD Assessment — where the current spec falls short of AAA

The de facto GDD is `tests/dsl_grammar/deep_space_trader.chimera` + `docs/STORY_BIBLE.md` +
the loop board. Strengths: testable spec (tests in the DSL itself), a story bible with a
genuinely distinctive design law (cost-authenticated meaning), a grading rubric competitors
don't have. Gaps against the benchmark set (Star Citizen, Elite Dangerous, No Man's Sky):

| # | Gap | Current spec | AAA benchmark | Severity |
|---|-----|--------------|---------------|----------|
| G1 | **World scale** | `world_bounds` ±100,000 UU = a **1 km box**; stations 500 m apart; planets are set-dressing props (`scale = 5.0`) | SC: full star systems, true-scale planets; ED: 1:1 galaxy | CRITICAL |
| G2 | **Quantum travel is a timer** | `travel_time_seconds = 30` teleport | SC: physical traversal through interdictable space at ~0.2c | HIGH |
| G3 | **Planet surfaces** | 2 planets, single biome_config each, flat pads | NMS/SC Genesis: procedural full-surface biomes, orbit-to-ground | HIGH |
| G4 | **Economy is static price tags** | Fixed buy/sell per market, 4 commodities | ED/EVE: supply-demand simulation, price propagation, sinks/sources | HIGH |
| G5 | **NPC density** | Loop 5 partially open; no crowd tech | SC stations: hundreds of ambient NPCs | MEDIUM |
| G6 | **Audio** | 36% rubric average; Ground_Sand_Sound just starting | Full adaptive MetaSounds mix | HIGH (known) |
| G7 | **Accessibility** | 0% across the board | CVAA compliance is table stakes for AAA shipping | MEDIUM (known) |
| G8 | **Ship interiors / EVA** | Ships are single actors with stats | SC: walkable interiors, physicalized components | MEDIUM |
| G9 | **Destruction / damage feel** | `hit_reactions = false`, HP-pool damage | Chaos-driven breakup, per-system physical damage | MEDIUM |
| G10 | **Character fidelity** | Custom suit/visor pipeline, no face tech | MetaHuman-class characters with performance capture | MEDIUM |

Scoping call worth defending, not fixing: **single-player standalone is the correct wedge.**
Star Citizen's hardest problems (server meshing, 500-player shards, dynamic mesh
reconfiguration) exist because it's an MMO. A single-player sim can spend that entire
complexity budget on fidelity and simulation depth — this is the same wedge Squadron 42
occupies. Keep `network_model = "standalone"`, but adopt **Iris-clean patterns** (see §4.8)
so co-op is not architecturally foreclosed.

---

## 2. UE 5.8 context — one strategic fact first

**UE 5.8 is the last planned major UE5 release; Epic is ramping UE6.** Consequences:
- 5.8 APIs are the stable plateau — safe to build deep against, no 5.9 churn coming.
- Every Experimental feature adopted (Mesh Terrain, MCP plugin, Sandboxes, MetaHuman
  Collections) should be wrapped behind a thin project-side interface so a UE6 port swaps
  implementations, not call sites. Add this as a generator convention: generated code calls
  `Chimera*` wrappers, never Experimental engine types directly.

Feature maturity used below: **PR** = Production-Ready, **B** = Beta, **X** = Experimental.

---

## 3. Feature list — UE 5.8 tech mapped to spiral loops, with specs

### Loop 1–2 (Ground, Verbs) — polish pass
| Feature | UE 5.8 tech | Spec / acceptance |
|---|---|---|
| Sand/dust light scattering | **Fog Screen Space Scattering (X)** on Local Fog Volumes | Dust storms and footfall bursts scatter light multiply; verify vs `research_references/` NASA plates; ≤0.3 ms GPU at 1440p |
| Terrain with overhangs, caves, dig sites | **Mesh Terrain (X)** — true 3D mesh, not heightfield; nondestructive modifiers; PCG-interoperable; World Partition + OFPA streaming | Replace flat pads: 4 km² playable outpost region, overhangs + lava tubes; auto-regen on edit; streamed, no blocking loads |
| Terrain deformation (shovel) | Mesh Terrain modifiers + Chaos | Dig persists across save/load; footprints + excavation share one deformation service |
| Surface audio | **MetaSounds** procedural wind (3 layers: rumble/rush/whistle), surface-typed footsteps | Matches task_progress.md plan; wind params driven by existing DSL `environmental.wind_*` values — single source of truth |

### Loop 3 (Sky) — the scale jump
| Feature | UE 5.8 tech | Spec / acceptance |
|---|---|---|
| True-scale positioning | **Large World Coordinates** (double-precision, stable since 5.0) | Raise `world_bounds` from 1 km to ≥10⁷ km; UU stays cm; all generated transforms move to `FVector` doubles — this is a **generator template change**, one place |
| Seamless space→surface | **World Partition** + **Fast Geometry Streaming Plugin (X)** (the Witcher 4 demo tech) + HLOD | Orbit-to-ground with zero load screens; <3 s worst-case streaming hitch budget → 0 visible hitches |
| Quantum travel as traversal | Rewrite `QuantumTravel` generator: real displacement through LWC space, interdiction volumes sample `interdiction_chance` along the path | Travel is interruptible/interdictable mid-flight; existing DSL route schema keeps working |
| Atmospherics | Sky Atmosphere + Volumetric Clouds per `atmosphere_density`; **Lumen Lite** as the GI floor | Titan haze (0.8) vs Ares (0.6) visibly distinct from orbit AND surface |

### Loop 5 (Other Dots — NPCs) — biggest 5.8 windfall
| Feature | UE 5.8 tech | Spec / acceptance |
|---|---|---|
| Station crowds | **MetaHuman Collections (X)** + **Mass** orchestration + Nanite skinned meshes; auto LOD swap between full Actors and Instanced Skinned Meshes by camera distance | 200+ ambient NPCs in Ares_Market_Central at 60 fps; study Epic's **MetaHuman Crowds Sample** (Fab) before implementing |
| Named NPCs from existing art | **Mesh to MetaHuman** — now conforms **bodies**, arbitrary topology | Convert existing suit character to fully rigged MetaHuman in one workflow; keeps your art, gains the rig |
| Animation without a mocap budget | **MetaHuman Animator markerless full-body capture** — face+body from a single webcam, no suits/markers | Directly satisfies the roadmap's "full motion-captured animations" standard at $0; 5 distinct idle cycles per NPC archetype |
| Secondary motion | **Control Rig Physics (B)** for cinematics; **Control Rig Dynamics** particle solver (5× faster) at runtime | Cloth/equipment jiggle on NPCs at runtime cost ≤0.1 ms each |
| NPC behavior at scale | **Mass** (5.8 overhaul) + StateTree for ambient behavior; keep behavior trees only for pirate combat AI | Pathfinding-in-dense-terrain phantom pain: retest under Mass avoidance before more BT surgery |

### Loop 6–7 (Shelter, Travel)
| Feature | UE 5.8 tech | Spec / acceptance |
|---|---|---|
| Station/ship interior lighting | **MegaLights (PR)** — many dynamic shadowed area lights, now with debug/optimization tooling | Fully dynamic interiors, no baked lighting in the pipeline (fits procedural generation); 60 fps target maintained |
| Walkable ship interiors | Ship = World Partition sublevel attached to LWC ship actor; interior collision authored in the ship generator | Player can stand/walk in Heavy_Freighter_Gamma during quantum travel |
| Ship damage | **Dataflow (PR)** + **Chaos Destruction** — nondestructive iteration on fracture assets | Hull breach visuals per hardpoint hit; replace `hit_reactions = false` with per-system physical damage; wire into existing `SystemDamage` generated class |
| Pilot suit / cloth | **Chaos Cloth (PR)** with new Cloth Panel Editor | Suit fabric responds to wind system values |

### Loop 8–9 (Systems, Universe)
| Feature | UE 5.8 tech | Spec / acceptance |
|---|---|---|
| Living economy | Gameplay-side: replace static `market_price` with source/sink simulation ticked at low Hz; DSL grows `production_rate`/`consumption_rate` per station | Prices drift ±30% around DSL baselines from simulated supply; H-13 telemetry rule applies — measure fps foregrounded |
| Planet surface generation | **PCG framework** — manual edits atop procedural output *without breaking proceduralism*; complex attribute types (arrays/structs/maps); embedded subgraphs | Existing `pcg_graph` DSL blocks gain biome subgraphs; art-directable results |
| Vegetation (Ares-Prime, vegetation_density 0.1) | **Procedural Vegetation Editor (X)** — biologically-correct, Nanite-ready growth; trees compete for light, grow around meshes | Industrial-zone scrub flora; Quixel Megaplants from Fab as starters |
| Environmental storytelling | PCG + Mesh Terrain: buried structures, erosion patterns encoding the Five Dead Houses archaeology | Rubric dimension 11 (currently 33%): every biome carries ≥3 legible history marks tied to STORY_BIBLE lore |

### Cross-cutting (every loop)
| Feature | UE 5.8 tech | Spec / acceptance |
|---|---|---|
| Accessibility (0% → shipping) | UMG Common UI; colorblind LUTs; full input remap via Enhanced Input | Rubric dimension 12 to 20/20: 3 colorblind modes, difficulty scaling, remapping — cheapest 20 points on the board |
| Cinematics/trailers | **Movie Render Graph (PR)** + Accumulation DoF | Marketing captures rendered in-engine |
| Performance budgets (updated) | Lumen Lite floor / Lumen HQ ceiling; MegaLights; Nanite everywhere | 60 fps @ 1440p on RTX 3070: keep. Add: 30 fps floor on Steam Deck via Lumen Lite (it hits 60 on Switch 2-class hardware — Deck is the PC analog) |

---

## 4. The agentic pipeline — Claude Code + pi upgrades

The pipeline (DSL → generate → build → sleepwalk → grade) is already ahead of industry
practice. These are the 2026-current upgrades:

### 4.1 Adopt the official UE MCP plugin (5.8, Experimental) alongside McpAutomationBridge
Epic now ships an in-process MCP server exposing Blueprints, assets, levels, materials,
meshes, automation tests — extensible with custom tools. Migration posture:
- **Keep McpAutomationBridge as the contract** (your tools encode hard-won pathways —
  MCP_PATHWAYS.md, H-2 viewport capture, H-7 error-field discipline).
- **Bridge to the official plugin for what it does better**: asset/Blueprint introspection,
  automation-test invocation, material graphs — things you currently reach via custom code.
- Record each adopted official-tool pathway to the DNA graph exactly like existing ones.
- Watch for API churn (Experimental); pin the engine version, wrap tool names.

### 4.2 UE Sandboxes (X) = engine-native spiral_forks
Sandboxes give isolated project environments with selective merge-back. This is
`core/spiral_forks.py` implemented at the engine level — forks can now include **asset and
level changes**, not just briefs. Wire: one sandbox per fork, loser sandboxes discarded
(autopsy recorded), winner merged. Never fork live state — same rule, better enforcement.

### 4.3 Claude Code: hooks as gates, agent teams as loops
- **Hooks**: move gate enforcement into `PreToolUse`/`PostToolUse`/`Stop` hooks —
  `gate_no_stale_trees` as a PreToolUse write-block, UBT + `result_grader` on Stop. Gates
  then bind *every* Claude Code session mechanically, not just pipeline runs. `proof-of-use`
  (currently a pi extension) has a natural Claude Code twin as a PreToolUse hook.
- **Subagent roster** maps 1:1 to the existing roles: research / code / debug / visual-test /
  balance as `.claude/agents/*` definitions with per-agent tool permissions (visual-test gets
  MCP screenshot tools; research gets web + graph query; balance gets read-only + telemetry).
- **Agent teams / dynamic workflows** (2026): a lead session fans out parallel subagents with
  git-based coordination and rubric-graded revision ("performance outcomes" — a grader sends
  work back until it meets a rubric). That grader pattern is *your* result_grader externalized:
  feed `RESULT_GRADING_RUBRIC.md` to the grading agent verbatim. Parallelize **within** a
  loop (features are independent inside Loop N), never across loops — spiral order is law.

### 4.4 pi: the local/cheap tier, hardened
pi's 4-tool minimalism + TypeScript extensions is the right harness for high-volume,
low-stakes work (grading calls, telemetry parsing, beat-script generation) on LM Studio
models — reserving Claude for research, generation, and judgment. Current leverage:
- `proof-of-use.ts` (fails-closed research enforcement) is genuinely novel — keep it the
  canonical implementation and port the pattern to Claude Code hooks (§4.3).
- pi's **RPC/SDK modes** let `run_deep_space_trader_pipeline.py` invoke pi programmatically
  instead of via terminal wrangling — the sleepwalker can drive a pi session headless.
- pi session **trees** (`/tree`) fit fork autopsies: branch, explore, record, abandon.

### 4.5 The 15-minute wrangler cycle is obsolete — retire screenshot-driven orchestration
SendKeys/screenshot supervision (the old Chimera-VR-era protocol) is superseded by:
headless `claude -p` / pi RPC + hooks for gate enforcement + `task_progress.md` handoffs.
Human attention goes to Gardener approvals and taste, not terminal babysitting.

### 4.6 In-editor LLM workflows
5.8 ships "integrated LLM workflows" (BYO model). Treat as UI sugar for humans; the
pipeline's authority stays with the DSL + generators. Do not let in-editor AI mutate
`ProceduralGenerated/` — it bypasses the generator-ownership contract.

### 4.7 Grading vision tier
MetaHuman Crowds Sample + official MCP screenshot tools give richer verification surfaces;
qwen3.6 vision stays tertiary evidence per the rubric. No change to authority ordering.

### 4.8 Iris-clean patterns (co-op insurance, ~free)
Keep replication-friendly shapes in generated code: state in replicated-capable properties,
inputs through the ability system (already GAS), no client-authoritative mutations. Iris in
5.8 got entity-based replication + multi-server improvements; you're not using it, but code
that *could* replicate costs nothing extra when generated from templates.

---

## 5. Phased roadmap

Ordering respects spiral law (finish Loop N first) while front-loading the two changes
that everything else compounds on: **scale (G1)** and **the agent-pipeline upgrades (§4)**,
which multiply all subsequent throughput.

### Phase A — Foundation upgrades (weeks 1–4)
1. **§4.3 hooks-as-gates + subagent roster** — every session gate-bound. *(pipeline)*
2. **§4.1 official MCP plugin bridged**, pathways recorded. *(pipeline)*
3. **G1 LWC scale-up**: generator emits double-precision transforms; world_bounds → 10⁷ km;
   stations/planets repositioned to plausible orbital distances. One template change,
   ~every visual test re-run. *(Loop 3 prerequisite, do it before more Loop 1 polish lands)*
4. Finish **Ground_Sand_Sound** as specced (MetaSounds, wind-param-driven). *(Loop 1 close-out)*
5. **Accessibility sweep** — 20 rubric points, no dependencies. *(cross-cutting)*

### Phase B — The scale jump (months 2–4)
6. Mesh Terrain outpost region (G3 start): 4 km², overhangs, dig persistence. Loop 1 done at AAA.
7. Fast Geometry Streaming + World Partition: seamless orbit-to-ground on Titan. Loop 3.
8. Quantum travel as real traversal with mid-flight interdiction (G2). Loop 3/7 seam.
9. FSSS dust/fog on both planets. Loop 3.

### Phase C — Population (months 4–8)
10. MetaHuman Collections crowds in both stations (G5); Mesh-to-MetaHuman conversion of the
    existing character; markerless mocap pass over all NPC animation (G10). Loop 5.
11. Mass/StateTree ambient AI; pirate BT kept for combat. Loop 5.
12. Ship interiors walkable + MegaLights interiors (G8). Loops 6–7.
13. Chaos/Dataflow ship damage replacing HP pools (G9). Loop 7.

### Phase D — Systems depth (months 8–14)
14. Living economy simulation (G4) — the rubric's Systems Depth fix; balance agent owns it.
15. PCG planet surfaces with embedded biome subgraphs + PVE vegetation; environmental
    storytelling encoding the Five Dead Houses. Loops 8–9.
16. Story Bible systems: Breaks, Wills, the Ledger sky — NG+ stars are literally the save
    file; this is the differentiator no benchmark title has. Loop 9 + narrative.

### Phase E — AAA polish & ship-readiness (months 14–18)
17. Full adaptive MetaSounds score; audio rubric to 85%.
18. Movie Render Graph trailer pipeline; Steam page assets from in-engine captures.
19. Rubric target: ≥85% enjoyment across all features, GPA ≥ 0.98, zero C/F grades.
20. UE6 migration audit: inventory of Experimental-feature wrappers (§2), port plan.

Timeline assumes the multi-agent pipeline at current throughput; the §4 upgrades in Phase A
are what make C–E dates plausible for a solo-wrangler operation.

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| Experimental features (Mesh Terrain, MetaHuman Collections, MCP plugin, Sandboxes, FSSS, PVE) shift under you | Wrapper convention (§2); pin 5.8; record every pathway; fall back: Landscape+virtual heightfield, vanilla Mass crowds |
| LWC scale-up breaks accumulated visual verifications | It will — budget a full re-verification sweep into Phase A item 3; it's cheaper now than after Loops 5–9 build on 1 km assumptions |
| UE6 arrives mid-project | 5.8 is supported for fixes; ship on 5.8, port after content-complete, not during |
| Crowd tech on a trader game's budget | Crowds are ambience, not simulation — Mass LOD keeps per-NPC cost near zero beyond ~20 m |
| Scope creep via "one more 5.8 feature" | Same law as ever: quality gates + spiral order. This doc is the closed feature list; additions require a fork brief and a Gardener-approved heuristic |

---

## 7. Sources

- Epic, "Unreal Engine 5.8 is now available" — https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available
- UE 5.8 release notes — https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- Unreal MCP in Unreal Editor — https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- Mesh Terrain docs — https://dev.epicgames.com/documentation/unreal-engine/mesh-terrain-in-unreal-engine
- MetaHuman Collections / Crowds — https://dev.epicgames.com/documentation/metahuman/metahuman-crowds-in-unreal-engine
- Star Citizen server meshing status 2026 — https://massivelyop.com/2026/02/06/star-citizen-cto-outlines-progress-on-server-meshing-and-crafting-with-alpha-4-7-on-track-for-march/ ; https://starcitizen.tools/Server_meshing
- pi coding agent — https://pi.dev/ ; https://mariozechner.at/posts/2025-11-30-pi-coding-agent/ ; https://github.com/badlogic/pi-mono
- Claude Code 2026 subagents/hooks/agent teams — https://www.developersdigest.tech/blog/claude-code-agent-teams-subagents-2026 ; https://www.totalum.app/blog/claude-code-skills-totalum
