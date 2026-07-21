> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# The Creative Research Cycle — How to Sculpt the David

## Overview

This is not a phase. This is a continuous loop that runs before, during, and after every other phase. It connects reference gathering to emotional understanding to technical implementation. It turns the AI from a code generator into an artist with a reference library.

---

## PRINCIPLE 1: RESEARCH BEFORE CREATION

Every object, every material, every light, every sound begins with looking. Not at other games. At reality.

### The Question Chain

For every creative task, ask:
1. What is this thing in the real world?
2. What makes it feel the way it feels?
3. What details would someone who's never seen one miss?
4. What happens to it over time?
5. What does it sound like? What does it feel like?
6. How would it exist in space — zero-G, vacuum, radiation?

### Research Methods

**Direct Observation:**
- NASA image archives for real spacecraft, planets, nebulae
- ISS interior photos for lived-in space environments
- Military naval vessels for functional, hardened design language
- Oil rigs and industrial complexes for utilitarian structure
- Abandoned buildings for decay patterns
- Junkyards for debris composition

**Artistic Interpretation:**
- ArtStation, DeviantArt, concept art books
- Film production design: 2001, Alien, Interstellar, The Expanse, Star Wars
- How did Syd Mead design for Blade Runner? How does that translate to space?
- What makes Ron Cobb's designs feel functional rather than fantastical?

**Scientific Understanding:**
- How does metal fatigue in vacuum?
- How does light scatter through nebulae?
- How does ice form in zero-G?
- What frequencies travel through a ship's hull?
- How do human eyes adapt to extreme contrast in space?

**Emotional Research:**
- Find photographs that evoke "lonely"
- Find paintings that evoke "cold"
- Find music that evokes "abandoned"
- Find poetry about isolation, hope, the sublime terror of infinity
- What do these have in common? What patterns emerge?

---

## PRINCIPLE 2: PATTERN EXTRACTION

Research produces raw material. Pattern extraction finds the rules.

For each subject, extract:

### Shape Language
What geometries communicate what emotions?
- Sharp angles = danger/military
- Curves = organic/alien
- Straight lines = human/functional

### Color Language
What palettes evoke what moods?
- Cold blues and greys = isolation
- Warm ambers = habitation
- Deep blacks = void
- Bright whites = sterile/clean

### Texture Language
What surfaces communicate what history?
- Smooth = new/maintained
- Pitted = old/damaged
- Layered = repaired
- Scorched = conflict

### Light Language
What lighting patterns evoke what feelings?
- Single source = loneliness
- Multiple sources = community
- Flickering = danger/damage
- Steady = safety

### Scale Language
How do we communicate size?
- Windows, doors, handrails
- Familiar objects next to unfamiliar ones
- The human figure is the universal scale reference

### Sound Language
What sounds evoke what states?
- Low hum = power/presence
- High whine = stress/danger
- Silence = void/death
- Rhythmic = mechanical/functioning
- Irregular = damaged/failing

### Pattern Library in Graphify

Each pattern is a node. "Lonely lighting" connects to "single point light", "cold color temperature", "high contrast shadows", "large negative space". When the Ether extracts "lonely" from a description, Graphify returns the full pattern.

---

## PRINCIPLE 3: CREATIVE SYNTHESIS

Research provides the pieces. Synthesis combines them into something new.

### The Synthesis Process

1. **Deconstruction:** Take a reference image. List every element: light sources, materials, colors, composition, scale cues, emotional impact.
2. **Abstraction:** What principles does this image demonstrate? Not "there's a red light on the left" but "asymmetric warm element in cold scene creates tension."
3. **Recombination:** Apply the principle to our context. Not copying the red light. Understanding why it worked and using that understanding.
4. **Iteration:** Generate. Evaluate against reference. Adjust. Generate again. Each pass refines.

### Example: Designing Orbital_Hub_7

**Research:**
- ISS exterior photos → modular construction, solar panels, docking ports
- Naval ships → functional layout, exposed systems, painted markings
- Oil rigs → industrial scale, safety equipment, harsh environment adaptation
- Abandoned factories → decay patterns, broken windows, rust

**Pattern Extraction:**
- Function over form: everything serves a purpose
- Layered history: repairs visible, upgrades apparent
- Human scale: windows, handrails, markings
- Wear concentrated at touch points

**Synthesis:**
1. Start with maximum detail — every panel, every rivet, every warning label
2. Apply emotional filter: "neutral trading hub, functional, slightly worn, not hostile"
3. Subtract what contradicts: remove military hardening, remove luxury, remove neglect
4. Keep: modular construction, visible repairs, warm docking lights, clean but not sterile

The result isn't a copy of the ISS or an oil rig. It's a new thing that FEELS like both, because it's built from the same principles.

---

## PRINCIPLE 4: EMOTIONAL ANCHORING

Every creative decision ties back to a specific emotion. Nothing is arbitrary.

### The Emotion → Implementation Chain

| Emotion | Light | Material | Color | Sound | Shape | Space |
|---------|-------|----------|-------|-------|-------|-------|
| Lonely | Single source, high contrast, cold | Bare, worn, functional | Desaturated, cool | Silence, distant hum | Isolated, exposed | Large negative space |
| Safe | Multiple sources, warm, steady | Clean, maintained, soft | Warm, saturated near light | Steady rhythm, familiar | Enclosed, protected | Contained, human-scale |
| Danger | Flickering, red, harsh shadows | Scorched, damaged, sharp | Red accents, high contrast | Irregular, loud, sudden | Jagged, aggressive | Tight, claustrophobic |
| Awe | Dramatic, volumetric, colored | Rich, detailed, vast | Deep blues, vibrant accents | Low rumble, harmonic | Massive, overwhelming | Infinite, grand |
| Mystery | Dim, indirect, colored shadows | Obscured, reflective, dark | Deep purples, faint glow | Whispered, occasional | Hidden, suggesting | Partially revealed |
| Hope | Single warm light in cold scene | Worn but cared for | Warm accent against cool | Rising tone, clear | Small against vast | A point in the void |

Every object, every room, every station gets assigned an emotional anchor. The anchor determines which patterns apply. Two stations with different anchors feel different even if they share the same mesh.

---

## PRINCIPLE 5: DETAIL HIERARCHY

Not everything gets equal detail. Detail follows attention. Attention follows emotion.

### Three Levels of Detail

**Level 1: Focal Points (where the player looks)**
- The docking bay entrance
- The market interface
- The ship cockpit
- Extreme detail. Every rivet. Every scratch. Every light.

**Level 2: Context (what surrounds the focal point)**
- Station exterior from 100 meters
- Debris field in the midground
- Planet in the background
- Moderate detail. Shapes read clearly. Textures are visible. Individual rivets are not.

**Level 3: Atmosphere (what creates the feeling)**
- Distant stars
- Far-off nebula
- Background ships
- Minimal detail. Color, shape, and light only. Impressions, not objects.

The research cycle determines what goes where. A docking bay is Level 1 because that's where the player interacts. The far side of the station is Level 2 because it's background. The nebula is Level 3 because it's atmosphere.

---

## PRINCIPLE 6: ITERATIVE REFINEMENT

No creation is final. Everything can be improved by another research pass.

### The Refinement Loop

1. Create based on current research
2. View the result (screenshot, playtest)
3. Compare against reference: what's missing?
4. Research the specific gap: "why doesn't this feel cold enough?"
5. Find references that nail "cold"
6. Extract what they do differently
7. Apply those principles
8. Repeat until the feeling is right

### The David Principle

Michelangelo didn't carve David in one pass. He rough-cut the form, then refined, then detailed, then polished. Each pass removed less material but made more difference. The final passes — the pupils of the eyes, the curve of the lips — are what make David feel alive.

The research cycle is the same. Early passes establish the broad shape. Later passes find the details that create the feeling. The difference between "a space station" and "a space station that feels like hope" is a thousand small observations from a thousand references, synthesized through a thousand iterations.

---

## PRINCIPLE 7: CROSS-POLLINATION

Ideas from one domain inform another. The sound of rain inspires a particle effect. A painting's color palette inspires a lighting setup. A poem's rhythm inspires a docking sequence.

### Cross-Domain Research

- How does architecture create sacred space? → Apply to station interiors
- How does music build tension? → Apply to pirate encounter pacing
- How does poetry use white space? → Apply to the void between stations
- How does sculpture use negative space? → Apply to debris field composition
- How does theater use lighting? → Apply to docking bay atmosphere
- How does dance use weight? → Apply to ship movement

### The Ether's Role

When the Ether extracts "lonely" from a description, it doesn't just query the "lonely lighting" pattern. It queries across domains: lonely in painting, lonely in music, lonely in architecture, lonely in poetry. The synthesis of all domains creates something richer than any single domain could.

---

## INTEGRATION WITH THE MASTER WORKFLOW

The research cycle runs continuously. It's not a phase. It's the thread that connects all phases.

**Before Phase 2 (Create Assets):**
- Research reference for every asset
- Extract patterns
- Build mood boards
- Define emotional anchors

**During Phase 2:**
- Compare each creation against reference
- Adjust based on extracted principles
- Document what works and what doesn't

**During Phase 7 (Visual Polish):**
- Research the specific gaps: "why doesn't this feel cold enough?"
- Find targeted references
- Apply micro-adjustments

**During Phase 9 (Playtest):**
- Observe emotional response
- Research what's missing from the feeling
- Queue refinements for next cycle

**After Phase 10:**
- The research cycle never stops
- Every observation feeds back into the pattern library
- Every iteration enriches the knowledge graph
- The AI gets better at understanding "lonely" with every cycle

---

## THE CREATIVE RESEARCH CYCLE IN ONE DIAGRAM

```
TEXT DESCRIPTION ("lonely cold station")
              ↓
         THE ETHER (extracts emotion, sensory, temporal, cultural context)
              ↓
    ┌─── RESEARCH CYCLE ───────────────────────────────┐
    │                                                    │
    │  1. SEARCH REFERENCES                              │
    │     - NASA photos of real stations                  │
    │     - ArtStation concept art of "lonely space"      │
    │     - Film stills from Interstellar, Alien          │
    │     - Music that evokes isolation                   │
    │     - Poetry about the sublime                      │
    │                                                    │
    │  2. EXTRACT PATTERNS                               │
    │     - Shape language: isolated, exposed             │
    │     - Color language: desaturated, cool             │
    │     - Light language: single source, high contrast  │
    │     - Sound language: silence, distant hum          │
    │     - Texture language: bare, worn, functional      │
    │                                                    │
    │  3. SYNTHESIZE                                     │
    │     - Combine patterns into design principles       │
    │     - Create emotional anchors                      │
    │     - Define detail hierarchy                       │
    │                                                    │
    │  4. CREATE                                          │
    │     - Apply principles to assets                    │
    │     - Generate materials, lights, sounds            │
    │     - Spawn and configure via MCP                   │
    │                                                    │
    │  5. EVALUATE                                        │
    │     - Screenshot vs reference                       │
    │     - Does it evoke the target emotion?             │
    │     - What's missing?                               │
    │                                                    │
    │  6. REFINE ←───────────────────────────┐           │
    │     - Research the gaps                 │           │
    │     - Find targeted references          │           │
    │     - Apply micro-adjustments           │           │
    │     - Repeat until feeling is right ────┘           │
    │                                                    │
    └────────────────────────────────────────────────────┘
              ↓
         GRAPHIFY (records every pattern, every iteration, every result)
              ↓
         THE DAVID EMERGES
```

---

## Summary

This is how the AI becomes an artist. Not by generating randomly. Not by copying patterns. By studying the world with the same intensity Michelangelo brought to the morgue, understanding the principles beneath the surface, and then creating something new from that understanding. The research cycle is the apprenticeship. Every reference is a master class. Every pattern is a lesson. Every iteration is a sketch. The David is the accumulation of a thousand hours of looking, understanding, and making.

---