# AAA Development Roadmap — Chimera Game Quality Framework

## Overview
This document outlines how the **AAA-Expanded Result Grader** (400-point scale across 12 game development dimensions) drives Chimera toward AAA-level enjoyment versus triple-A benchmark titles (No Man's Sky, Elite Dangerous, Subnautica, EVE Online, Star Citizen).

**Goal**: Achieve **85%+ overall enjoyment percentage** across all features by systematically addressing weaknesses revealed by the 12-dimension grading framework.

---

## The 12 AAA Game Development Dimensions

### Tier 1: Foundation (Technical Correctness, Stability, Design Checklist, Spec Fidelity)
**Total: 100 points (legacy rubric, now one tier of a larger framework)**

1. **Technical Correctness (40 pts)** — Test pass rate, criteria coverage
   - Metric: `passed_tests / total_tests × criteria_coverage × 40`
   - Gate: Must pass ≥80% for feature acceptance
   - Current Ground_Sand_Particles: **24/40** (60% → needs test suite expansion)

2. **Stability & Performance (25 pts)** — Crash-free, FPS vs target, unbounded growth
   - Metric: crash_free (15) + fps_vs_target (5) + no_growth_bounds (5)
   - Gate: Must be 100% crash-free
   - Current Ground_Sand_Particles: **25/25** ✓ (Perfect stability foundation)

3. **Design Checklist (20 pts)** — Feedback, consistency, meaningful_parameters, fail_safety, balance_sanity
   - Metric: 4 pts per criterion met (out of 5)
   - Gate: All 5 criteria must pass
   - Current Ground_Sand_Particles: **16/20** (Missing: meaningful_parameters)

4. **Spec Fidelity (15 pts)** — DSL/researched parameters verified in built result
   - Metric: `verification_count / declared_parameters × 15`
   - Gate: Must achieve ≥85%
   - Current Ground_Sand_Particles: **4.95/15** (33% → critical gap, needs parameter audit)

---

### Tier 2: Player Experience (Player Immersion, Gameplay Flow, Systems Depth)
**Total: 120 points (the "feel" of the game — this is what makes it enjoyable)**

5. **Player Immersion (50 pts)** — Moment-to-moment feel, animation smoothness, visual polish, audio-visual sync
   - Sub-metrics:
     - Moment-to-moment feel (12): How satisfying is each player action?
     - Animation smoothness (12): 60fps+ fluid vs 30fps+ choppy vs low/jerky
     - Visual polish (13): AAA/high vs moderate vs low/debug placeholder
     - Audio-visual sync (13): Are sound and visuals tightly coupled?
   - Current Ground_Sand_Particles: **25/50** (50% → audio-visual sync completely missing)
   - **Refinement**: Add Niagara particle response to player footsteps, synchronize dust clouds with movement feedback audio

6. **Gameplay Flow (40 pts)** — Pacing, progression clarity, reward cadence, difficulty tuning
   - Sub-metrics:
     - Pacing (10): AAA excellent vs good/moderate vs poor/undefined
     - Progression clarity (10): Clear/intuitive vs partial/moderate vs unclear/confusing
     - Reward cadence (10): Satisfying/AAA vs present/adequate vs absent/weak
     - Difficulty tuning (10): Balanced/engaging vs present/attempted vs absent/trivial
   - Current Ground_Sand_Particles: **15/40** (37.5% → gameplay flow is minimal for a sand surface)
   - **Refinement**: Add hazard mechanics (dust storms, treacherous terrain), progression from safe plains to challenging craters

7. **Systems Depth (30 pts)** — Mechanical interdependencies, emergent complexity, player agency
   - Sub-metrics:
     - Mechanical interdependencies (10): High/complex vs moderate/some vs low/siloed
     - Emergent complexity (10): true vs false/linear
     - Player agency (10): High/meaningful vs moderate/limited vs low/scripted
   - Current Ground_Sand_Particles: **10/30** (33% → ground surface is too passive)
   - **Refinement**: Add surface erosion from player movement, dust accumulation patterns that affect traversal, discoverable geothermal vents

---

### Tier 3: Production Quality (Visual Fidelity, Audio Design, Polish & Juiciness)
**Total: 95 points (AAA production values)**

8. **Visual Fidelity (35 pts)** — Lighting quality, material detail, environmental storytelling, LOD performance
   - Sub-metrics:
     - Lighting quality (9): AAA/realistic vs good/stylized vs poor/flat
     - Material detail (9): AAA/PBR-high vs good/PBR-moderate vs poor/placeholder
     - Environmental storytelling (9): Visible history, damage patterns, world-building through environment
     - LOD performance (8): Optimized/AAA vs acceptable/moderate vs poor/missing
   - Current Ground_Sand_Particles: **14/35** (40% → environmental storytelling completely absent, material detail at "good")
   - **Refinement**: Add dust accumulation mask material (pending research task), embedded rocks, ancient structures buried in sand

9. **Audio Design (25 pts)** — Diegetic/non-diegetic mix, feedback responsiveness, ambient richness
   - Sub-metrics:
     - Diegetic/non-diegetic mix (8): AAA/balanced vs present/adequate vs poor/missing (wind, distant thunder, suit audio)
     - Feedback responsiveness (9): Tight/AAA vs adequate/moderate vs poor/delayed (footstep feedback, dust rustling)
     - Ambient richness (8): Immersive/AAA vs present/adequate vs sparse/none (ambient wind layers, subsonic rumble)
   - Current Ground_Sand_Particles: **9/25** (36% → ambient richness completely missing)
   - **Refinement**: Layer ambient wind, add proximity-triggered seismic rumbles, synchronize footstep EQ with surface type

10. **Polish & Juiciness (35 pts)** — Particle effects, screen shake, UI feedback, animation juice
    - Sub-metrics:
      - Particle effects (9): AAA/abundant vs present/adequate vs sparse/none
      - Screen shake (9): Impactful/AAA vs present/subtle vs absent/weak
      - UI feedback (9): Responsive/AAA vs adequate/functional vs poor/missing
      - Animation juice (8): Abundant/AAA vs present/adequate vs minimal/none
    - Current Ground_Sand_Particles: **15/35** (43% → animation juice absent)
    - **Refinement**: Add dynamic dust trails on movement, impact-driven particle bursts, screen shake on heavy footfalls

---

### Tier 4: Game Design (Narrative & World Building, Accessibility & Inclusivity)
**Total: 50 points (world cohesion and player inclusion)**

11. **Narrative & World Building (30 pts)** — Lore consistency, character development, world coherence
    - Sub-metrics:
      - Lore consistency (10): High/airtight vs moderate/consistent vs low/contradictory
      - Character development (10): Deep/compelling vs present/functional vs minimal/absent
      - World coherence (10): High/believable vs moderate/adequate vs low/fragmented
    - Current Ground_Sand_Particles: **10/30** (33% → character development absent in a ground surface, world coherence only partial)
    - **Refinement**: Embed narrative clues in sand formations, add historical erosion patterns that tell story of past civilizations

12. **Accessibility & Inclusivity (20 pts)** — Colorblind modes, difficulty options, control remapping
    - Sub-metrics:
      - Colorblind modes (7): true vs false
      - Difficulty options (7): true vs false
      - Control remapping (6): true vs false
    - Current Ground_Sand_Particles: **0/20** (0% → accessibility features missing across the board)
    - **Refinement**: Add colorblind particle palette options, difficulty-based hazard density, remappable traversal controls

---

## Current Project Status: Overall AAA-Benchmark Enjoyment

### Summary by Feature Category:

| Category | Features | Current Avg % | Target % | Gap |
|----------|----------|---------------|----------|-----|
| Core Systems (Economy, Factions, Missions) | 3 features | **91%** | 90%+ | EXCELLENT ✓ |
| Player Character (Model, Animation, Suit) | 3 features | **76%** | 85%+ | -9% |
| Ground Environment (Sand, Rock, Particles, Footprints) | 4 features | **58%** | 85%+ | -27% |
| Sky & Universe (Generation components) | 4 features | **TBD** | 85%+ | ? |
| NPC & Social (Trading, AI) | 2 features | **TBD** | 85%+ | ? |
| Shelter & Travel | 4 features | **TBD** | 85%+ | ? |

### Largest Development Gaps (By Dimension):

**Tier 2 (Player Experience) — The Most Critical:**
1. Systems Depth (emergent complexity, player agency): **Average 33%** across environmental features
2. Gameplay Flow (pacing, progression, rewards): **Average 37.5%** — ground is too passive
3. Player Immersion (audio-visual sync, moment-to-moment feel): **Average 50%** — missing tight feedback loops

**Tier 3 (Production Quality):**
1. Audio Design: **Average 36%** — environmental audio completely underdeveloped
2. Visual Fidelity (environmental storytelling): **Average 40%** — surfaces lack history and meaning
3. Polish & Juiciness (animation juice, particle effects): **Average 43%** — feels mechanical, not organic

**Tier 4 (Design):**
1. Accessibility & Inclusivity: **Average 0%** across all features — no colorblind/difficulty/control options
2. Narrative & World Building: **Average 33%** — world-building through environmental detail missing

---

## Development Prioritization: Path to 85%+ AAA Enjoyment

### Phase 1: Foundation (Weeks 1-2) — Fix Tier 1 Gaps
**Goal: Achieve 100% technical correctness + all spec fidelity parameters verified**

- [ ] **Test Suite Expansion** (Ground_Sand_Particles, Verbs, Ground variants)
  - Add criteria_total definitions for each feature
  - Implement acceptance criteria tests in Engine
  - Target: 4/5 tests passing → 24/40 → 32/40 minimum

- [ ] **Spec Fidelity Audit** (All Loop 0-9 features)
  - Verify every DSL-declared parameter is in built result
  - Ground_Sand_Particles: 33% → 80%+ (dust density, accumulation rate, decay rate, particle count, wind interaction)
  - Player_Character_Model: 98.8% → 100%
  - System_Economy: 90.5% → 100%

- [ ] **Missing Parameters Review**
  - Ground_Sand_Particles: Add meaningful_parameters to design checklist
  - All features: Ensure every tunable is exposed and measured

---

### Phase 2: Player Experience (Weeks 3-4) — Raise Tier 2 from 40% → 75%+
**Goal: Make the game *feel* satisfying moment-to-moment, with emergent complexity and clear progression**

#### **Priority 1: Player Immersion (25/50 → 40/50)**
- [ ] **Audio-Visual Synchronization** (Ground_Sand_Particles)
  - Footstep impact: Dust particle burst synchronized with sound feedback
  - Movement: Dust trail audio envelope matched to visual density
  - Environmental response: Wind gusts synchronized with particle drift
  - Target: 0/13 → 10/13 (tight audio-visual coupling)

- [ ] **Moment-to-Moment Feel** (Player Character)
  - Remove "mechanical stiffness" from character animation (76% → 85%)
  - Add micro-feedback: Suit servo sounds, visor glint on turns, weight shifts
  - Target: 6/12 → 10/12

#### **Priority 2: Systems Depth (10/30 → 20/30)**
- [ ] **Emergent Complexity** (Ground_Sand_Particles)
  - Surface erosion from repeated footfalls (player creates paths over time)
  - Dynamic dust distribution affected by wind speed
  - Geothermal vent discovery (subsurface complexity surfaced by exploration)
  - Target: 0/10 → 6/10 (emergent patterns player discovers)

- [ ] **Player Agency** (Ground & Verbs)
  - Traversal choices: Safe route vs dangerous shortcut
  - Tool use: Scanner reveals hidden structures, Shovel creates distinct ground effects
  - Movement verb variety: Sprint creates larger dust clouds, crouch moves silently
  - Target: 5/10 → 8/10

#### **Priority 3: Gameplay Flow (15/40 → 28/40)**
- [ ] **Pacing & Progression** (Loops 0-7)
  - Ground progression: Plains → Craters → Highlands → Badlands (difficulty scaling)
  - Reward cadence: Discovery of resources/structures at increasing depths
  - Difficulty tuning: Environmental hazards (dust storms, crevasses) at later areas
  - Target: 15/40 → 28/40

---

### Phase 3: Production Quality (Weeks 5-6) — Raise Tier 3 from 42% → 70%+
**Goal: AAA visual polish, rich audio design, "juicy" feedback on every action**

#### **Priority 1: Audio Design (9/25 → 18/25)**
- [ ] **Ambient Richness** (Ground_Sand_Particles)
  - Wind layers: Low rumble (subsonic), mid-range rush, high-frequency whistle
  - Environmental ambience: Distant thunder, bioluminescent hums (alien world)
  - Seismic activity: Low-frequency substrate rumble on rare events
  - Target: 0/8 → 6/8

- [ ] **Feedback Responsiveness** (All ground verbs)
  - Footsteps: Different pitch/resonance per surface (sand, rock, metal)
  - Tool feedback: Shovel scrape intensity based on soil hardness
  - Movement audio: Suit fabric rustle, breathing variation
  - Target: 5/9 → 8/9

#### **Priority 2: Visual Fidelity (14/35 → 24/35)**
- [ ] **Environmental Storytelling** (Loops 0-9)
  - Dust accumulation patterns revealing hidden structures
  - Erosion patterns suggesting wind direction and age
  - Embedded artifacts, ancient metal fixtures, geological layering
  - Target: 0/9 → 7/9

- [ ] **Material Detail** (Ground_Sand_Particles)
  - Procedural dust-accumulation mask (pending research task)
  - Parallax-mapped surface texture layers
  - Dynamic sand compaction based on foot pressure
  - Target: 5/9 → 8/9

#### **Priority 3: Polish & Juiciness (15/35 → 24/35)**
- [ ] **Animation Juice** (All movement verbs)
  - Overshoot on footfalls, weight-shift arcs
  - Particle trails on fast movement
  - Dust settling animation with ease curves
  - Target: 0/8 → 6/8

- [ ] **Particle Effects** (Ground_Sand_Particles)
  - Abundant dust trails on all movement speeds
  - Impact bursts on heavy footfalls
  - Settling dust clouds with lifetime and color gradients
  - Target: 5/9 → 8/9

---

### Phase 4: Game Design (Week 7) — Raise Tier 4 from 17% → 40%+
**Goal: Accessible to all players, world-building through environmental detail**

#### **Priority 1: Accessibility** (0/20 → 14/20)
- [ ] **Colorblind Modes** (Particle effects, UI)
  - Deuteranopia-friendly dust palette (shifted toward blue/yellow)
  - High-contrast hazard indicators
  - Target: 0/7 → 5/7

- [ ] **Difficulty Options** (Environmental hazards, traversal)
  - Easy: No hazards, clear paths
  - Normal: Occasional hazards, tactical routes
  - Hard: Frequent hazards, resource scarcity
  - Target: 0/7 → 5/7

- [ ] **Control Remapping** (Movement verbs)
  - Custom keybinds for all actions
  - Joystick sensitivity tuning
  - Target: 0/6 → 4/6

#### **Priority 2: Narrative & World Building (10/30 → 18/30)**
- [ ] **Lore Consistency** (Environment details)
  - Sand origin story (geological history)
  - Hazard explanations (geothermal, seismic)
  - Target: 5/10 → 8/10

- [ ] **World Coherence** (All loops)
  - Consistent tech level across environments
  - Environmental details reinforce setting
  - Target: 5/10 → 10/10

---

## Measurement & Iteration

### Weekly Grading Cycle:
1. **Run sleepwalker simulations** (beat scripts with all verbs/features exercised)
2. **Collect telemetry** (crash-free, FPS, growth bounds)
3. **Run result_grader_aaa_expanded** on 3-5 key features
4. **Update study guide** with highest-priority gaps
5. **Focus next week's development** on top 3 failing dimensions

### Target Trajectory:

| Week | Avg AAA % | Primary Focus |
|------|-----------|----------------|
| Week 1 | 58% | Spec Fidelity (33% → 80%) |
| Week 2 | 62% | Technical Correctness (60% → 80%) |
| Week 3 | 68% | Audio-Visual Sync, Emergent Complexity |
| Week 4 | 72% | Gameplay Flow, Moment-to-Moment Feel |
| Week 5 | 76% | Audio Design, Environmental Storytelling |
| Week 6 | 80% | Animation Juice, Particle Effects |
| Week 7 | 83% | Accessibility, World Coherence |
| Week 8+ | 85%+ | Refinement pass: final polish toward AAA standard |

---

## Success Criteria

**The game achieves AAA-level enjoyment when:**
1. ✅ All features score ≥85% across the 12 dimensions
2. ✅ **Tier 2 (Player Experience)** averages ≥80% (tight feedback loops, emergent complexity, clear progression)
3. ✅ **Tier 3 (Production Quality)** averages ≥75% (audio-visual sync, environmental storytelling, animation juice)
4. ✅ **THE CRITIC organ** confirms player-enjoyment percentile ≥85% vs benchmark set
5. ✅ **Sleepwalker simulations** reach all beats without failure, exercising all gameplay paths
6. ✅ **GPA ≥2.8** (all features Grade A/B, zero F grades)

---

## Notes for Developers

The **12-dimension framework drives decision-making**, not just documents it:
- Every feature refinement is measured against a specific dimension (e.g., "add audio-visual sync to Ground_Sand_Particles → Player Immersion from 25/50 → 40/50")
- **Study guide is actionable**: "⚠ Audio-visual sync (missing/poor) (0/13)" immediately tells you what to build next
- **The Critic organ validates the framework**: If all 12 dimensions reach 85%+, THE CRITIC will report 85%+ AAA-benchmark enjoyment
- **Sleepwalker simulations prove playability**: Features aren't "done" until fully exercised through beat scripts; automated observation finalizes acceptance

---

## Integration with Existing Automation

- `python -m core.result_grader_aaa_expanded --feature <name> --evidence <file.json> --benchmark "No Man's Sky" "Subnautica"` — Run 12-dimension grading
- `python -m core.sleepwalker --beats docs/beats/regolith_yard.beats.json --session automated_aaa_development` — Gather evidence for immersion, flow, systems
- `python -m core.critic --feature <name> --dry-run` — Get AAA-benchmark enjoyment estimate (validates framework)
- `python -m core.postflight --phase "..." --phantom-pain "animation_juice_missing_from_ground_particles"` — Record development insights for dream loop

---

**Last Updated**: 2026-07-07
**Framework**: AAA-Expanded Result Grader (400-point scale, 12 dimensions)
**Target**: 85%+ player-enjoyment percentile vs triple-A benchmark titles
