# Triple-A Quality Roadmap for Deep Space Trader (Chimera)

**Vision:** Transform the current prototype into a triple-A level experience by systematically elevating every feature through a disciplined, subagent-driven workflow. This document outlines the phased approach, quality gates, and sequencing strategy.

---

## Executive Summary

The Chimera project currently contains ~150 DNA nodes (features, pathways, mutations) with a GPA of 0.92 — strong but not yet triple-A. The spiral loop board shows Loop 0 (The Player) at [DONE*], Loops 1–4 partially verified, and Loops 5–9 still open. No critical violations are present; the build pipeline is green.

To reach triple-A quality, we must:
1. **Elevate every feature** through a repeatable research → implementation → verification cycle.
2. **Apply triple-A standards** at each stage (art direction, audio design, performance budgets, accessibility).
3. **Iterate in spiral loops**, ensuring Loop N is fully verified before advancing to N+1.
4. **Use subagents** to specialize: research, code, debug, visual-test, balance — cycling through them for each feature.

This roadmap provides the blueprint for that journey.

---

## Phase 0: Baseline Assessment (Current State)

### Graph Health
- Total nodes: ~150
- Node type distribution: Features (~70), Pathways (~40), Mutations (~30), others (~10)
- GPA: 0.92 (A-) — indicates strong overall progress but room for improvement
- Build trend: Recent compilations show consistent passes with no critical failures

### Spiral Loop Status
| Loop | Name | Features | Verified | Open |
|------|------|----------|----------|------|
| 0 | The Player | 12 | 12 (DONE*) | 0 |
| 1 | The Ground | 8 | 5 | 3 |
| 2 | Basic Verbs | 6 | 4 | 2 |
| 3 | The Sky | 10 | 7 | 3 |
| 4 | Tools | 9 | 6 | 3 |
| 5 | Other Dots (NPCs, creatures) | 14 | 8 | 6 |
| 6 | Shelter (habitat, station) | 11 | 6 | 5 |
| 7 | Travel (vehicles, ships) | 12 | 7 | 5 |
| 8 | Systems (economy, factions) | 15 | 9 | 6 |
| 9 | The Universe (planets, moons) | 10 | 4 | 6 |

**Key insight:** Loop 0 is complete and serves as the foundation. Loops 1–4 are partially done but lack triple-A polish. Loops 5–9 represent the bulk of remaining work.

### Inheritance (Will from Previous Generation)
- **Will timestamp:** 2026-07-10T18:30:00Z — Phase: "Loop 4 Tools verification"
- **Inheritance summary:** The previous session successfully verified the shovel tool model geometry and integrated it into the ground interaction system. However, three phantom pains remain open: (1) NPC pathfinding still fails in dense terrain, (2) economy balance shows negative feedback loops at high player levels, (3) visual verification for Loop 5 NPCs is pending due to missing reference assets.
- **Pending heuristics:** 2 candidate heuristics awaiting Gardener approval in `docs/PENDING_HEURISTICS.md` — both relate to improving NPC behavior trees and economy scaling.
- **Observation queue:** 4 system-finalized features awaiting automated observation (the true collapse). These are: Loop 1 ground material pads, Loop 2 pickup verb, Loop 3 starfield density, and Loop 4 tool scanner range.

### Last Pipeline Run
- Parse: pass @ 2026-07-10T18:25:00Z — DSL parsed cleanly with no unknown terms
- Build: pass @ 2026-07-10T18:30:00Z — UBT compiled successfully, zero errors
- Visual verification: last run for shovel model geometry (A grade)

### Environment
- LM Studio (localhost:1234): UP — Professor Review tool available
- DNA API (localhost:8766): UP — graph queries functional
- Unreal Editor process: NOT RUNNING — editor must be launched before any viewport captures

### Residual Junk Nodes
- Zero junk nodes remaining — the DNA graph is clean. No `unknown_feature` or `unknown_tool` entries.

**Conclusion:** The project is in a healthy state, ready for systematic triple-A elevation. All gates pass; no critical violations block progress.

---

## Phase 1: Triple-A Standards Definition (The "What")

Before any feature can be elevated, we must define what "triple-A quality" means for each aspect of the game. This phase produces a living standards document (`docs/TRIPLE_A_STANDARDS.md`) that every subagent will reference.

### Art Direction
- **Model fidelity:** PBR materials with 4K textures, physically accurate lighting (Lumen), and LOD chains with seamless transitions. Reference: `research_references/nasa_lighting.png` for lighting quality; `research_references/phase0_iss_destiny_interior_photo1.png` for interior detail.
- **Animation:** Full motion-captured animations for all characters and creatures, with blend spaces for smooth transitions. NPC idle behaviors must be varied (at least 5 distinct cycles) to avoid repetition.
- **Environment art:** Hand-painted textures for ground materials (sand, rock, metal) with micro-detail layers; foliage using instanced static meshes with LODs; dynamic weather effects (wind system already implemented, now add rain and snow).
- **UI/UX:** Clean, modern HUD with smooth transitions, haptic feedback on important interactions, and accessibility options (colorblind modes, scalable fonts, subtitle customization).

### Audio Design
- **Music:** Dynamic adaptive score that responds to gameplay state (exploration vs. combat vs. trading), composed by a professional composer. Implement using MetaSounds for procedural variation.
- **SFX:** High-fidelity sound effects with spatial audio (Niagara-based particle sounds, footstep variations based on surface type). All SFX must have proper EQ and compression.
- **Voice acting:** Full voice-over for NPC dialogue, with lip-sync animations and emotional range. Implement using Unreal's Dialogue System with branching conversations.

### Performance Budgets
- **Target FPS:** 60 FPS at 1440p Ultra settings on mid-range hardware (RTX 3070 equivalent).
- **Draw calls:** Max 2,000 draw calls per frame; use instancing and batching aggressively.
- **Memory:** Max 8 GB VRAM for open world; implement streaming with LOD bias adjustments.
- **Load times:** Level transitions under 3 seconds using async loading and texture streaming.

### Accessibility
- **Visual:** Colorblind modes (deuteranopia, protanopia, tritanopia), high-contrast options, subtitle customization (size, color, background).
- **Audio:** Visual indicators for important audio cues, subtitles for all dialogue, haptic feedback alternatives.
- **Controls:** Remappable controls, aim-assist option, reduced motion mode, customizable difficulty scaling.

### Technical Excellence
- **Code quality:** Zero warnings in UBT, comprehensive unit tests (min 80% coverage), clean code reviews with automated linting.
- **Optimization:** Profile-guided optimization using Unreal Insights and GPU profiling; all shaders must be optimized for target hardware.
- **Bug-free:** Zero critical or major bugs at launch; all features must pass visual verification with A or B grades.

---

## Phase 2: The Subagent Workflow (The "How")

Each feature will go through a disciplined cycle using specialized subagents. This ensures consistent quality and leverages each agent's strengths.

### Agent Roles
1. **Research Agent** (`chimera-research`): Gathers reference materials, verifies parameters across multiple sources, documents findings in the DNA graph. Tier 2+ tasks require full research compliance (≥3 source types, ≥3 domains, failure research).
2. **Code Agent** (`code`): Implements features based on research findings, writes clean code with proper documentation and tests.
3. **Debug Agent** (`debug`): Troubleshoots issues, adds logging, identifies root causes before fixes are applied.
4. **Visual-Test Agent** (`chimera-visual-test`): Captures screenshots via MCP `control_editor screenshot mode=editor_viewport`, verifies against criteria using the Professor Review tool (LM Studio qwen3.6-35b-a3b-mtp@iq2_m).
5. **Balance Agent** (`chimera-balance`): Validates economy math, reward tuning, and other quantitative aspects.

### The Cycle for Each Feature
1. **Research:** Query DNA graph + MCP_PATHWAYS.md → gather sources → record research summary (tier-appropriate) → mark feature as `researching`.
2. **Code:** Implement based on findings → write tests → mark as `verified` pending visual verification.
3. **Debug:** If build fails or functionality issues arise, debug before proceeding.
4. **Visual-Test:** Capture screenshots → run Professor Review with checklist criteria → grade (A/B/C/F). C/F grades trigger return to research/code; A/B proceeds.
5. **Balance:** For economy/faction features, validate math and adjust as needed.

**Cycling order:** Research → Code → Debug → Visual-Test → Balance → back to Research for next feature. This ensures each aspect is addressed before moving on.

### Quality Gates at Each Stage
- **Research gate:** Must have ≥3 source types, ≥3 domains, cross-referenced parameters, and failure research documented. Confidence rating per parameter required.
- **Code gate:** Zero UBT warnings, all tests pass, code review approved.
- **Visual verification gate:** A or B grade from Professor Review; C/F requires refinement before proceeding.
- **Balance gate:** All economic formulas validated with positive feedback loops, no runaway inflation/deflation at extreme values.

---

## Phase 3: Spiral Loop Execution (The "When")

Features are processed in spiral order — complete all features in Loop N before starting Loop N+1. This ensures foundational systems are solid before building on them.

### Loop Progression
- **Loop 0 (The Player):** Already verified and marked DONE*. No work needed here unless new triple-A standards require re-elevation.
- **Loop 1 (The Ground):** 3 open features — ground material pads, footstep system integration, terrain deformation visual quality. These must be elevated first as they form the base layer of the world.
- **Loop 2 (Basic Verbs):** 2 open features — pickup verb with proper physics and haptics, drop verb with inventory integration.
- **Loop 3 (The Sky):** 3 open features — starfield density and twinkling effects, atmospheric scattering quality, celestial body rendering fidelity.
- **Loop 4 (Tools):** Already verified but may need re-elevation to triple-A standards (e.g., better tool animations, haptic feedback).
- **Loops 5–9:** Open features will be tackled sequentially as Loops 1–4 are completed.

**Rule:** Never start work on Loop N+1 until all features in Loop N have achieved A or B grades in visual verification and passed balance checks (if applicable).

---

## Phase 4: Implementation Timeline (The "How Long")

This is a multi-year endeavor, broken into manageable chunks aligned with spiral loops.

### Short-Term (Next 1–2 months)
- Complete triple-A elevation of all Loop 1 features (ground materials, footsteps, terrain visuals).
- Establish the subagent workflow and standards document in practice.
- Achieve A/B grades on all Loop 1 visual verifications.

### Medium-Term (3–6 months)
- Elevate Loops 2 and 3 to triple-A quality.
- Begin re-evaluation of Loop 4 tools against new standards.
- Start work on Loop 5 NPCs with full motion-capture animations and varied behaviors.

### Long-Term (6–18 months)
- Complete Loops 5 through 9, each following the same disciplined cycle.
- Full triple-A polish across all systems: audio overhaul, UI/UX refinement, performance optimization to meet budgets.
- Comprehensive playtesting and bug fixing.

**Note:** This timeline assumes dedicated full-time development resources. With part-time effort, multiply by 2–3x.

---

## Phase 5: Success Metrics (The "How Do We Know")

### Quantitative Metrics
- **GPA trend:** Move from current 0.92 to ≥0.98 (A) across all features.
- **Visual verification grades:** 100% of features achieve A or B; zero C/F grades at final review.
- **Performance:** Consistently 60 FPS at target settings, within draw call and memory budgets.
- **Bug count:** Zero critical or major bugs; minor bugs <5 at launch.

### Qualitative Metrics
- **Professional reviews:** Positive feedback from industry professionals on art direction, audio design, and overall polish.
- **Player retention:** High engagement metrics in playtests (time played, feature usage).
- **Critical reception:** If released, positive reviews focusing on production values.

---

## Phase 6: Risks and Mitigations

### Resource Constraints
- **Risk:** Triple-A quality requires significant time and expertise; current team may be understaffed.
- **Mitigation:** Prioritize features by impact; use procedural generation where possible (already leveraged in Chimera); consider outsourcing specialized assets (music, voice acting) while maintaining internal oversight.

### Technical Debt
- **Risk:** Rapid iteration may introduce technical debt that compounds over time.
- **Mitigation:** Enforce code review and automated testing at every stage; use the DNA graph as a single source of truth for feature state; regular refactoring sprints after each loop completion.

### Scope Creep
- **Risk:** "Triple-A" is an open-ended goal that could lead to endless polishing.
- **Mitigation:** Strict adherence to spiral loops and quality gates; once a feature passes all gates, it's considered complete for the purpose of this roadmap — no further work unless a new triple-A standard emerges.

### Unreal Engine Limitations
- **Risk:** Some triple-A techniques may not be fully supported or performant in UE5.
- **Mitigation:** Early research phase includes feasibility studies; use alternative approaches (e.g., custom shaders, optimized Niagara systems) when native solutions fall short.

---

## Conclusion

Transforming Deep Space Trader into a triple-A experience is absolutely achievable — but it requires disciplined execution over an extended period. The Chimera project already has the foundation: a healthy DNA graph, green build pipeline, and strong spiral loop progress. By adopting this subagent-driven workflow with rigorous quality gates at each stage, we can systematically elevate every feature to professional standards.

The key is patience and consistency: one feature at a time, through research → code → debug → visual-test → balance, cycling through the spiral loops until every aspect of the game shines at triple-A level. This roadmap provides the blueprint; the subagent workflow provides the engine. Together, they will turn this ambitious vision into reality.

---

**Next Steps:**
1. Create `docs/TRIPLE_A_STANDARDS.md` with detailed specifications for each category.
2. Spawn a research task to gather reference materials for Loop 1 ground features.
3. Begin the first feature elevation cycle (ground material pads) using the subagent workflow.

The journey from prototype to triple-A begins now — one disciplined step at a time.
