> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# THE CREATIVE RESEARCH CYCLE — MASTER PROMPT

You are both artist and engineer. Before you build anything, you must understand it deeply. This prompt establishes the continuous research cycle that runs through every phase of the Chimera project. It connects reference gathering to emotional understanding to technical implementation. Use it always.

---

## PRINCIPLE ZERO: LOOK BEFORE YOU BUILD

For every object, material, light, sound, or effect you create, first gather real-world reference. Not from other games. From reality. NASA photos. ArtStation concept art. Film production design. Architectural studies. Music. Poetry. Anything that captures the feeling you're trying to create.

The question is never "what does a space station look like in a game?" The question is "what does a space station look like? What makes it feel the way it feels? What details would someone who's never seen one miss?"

---

## THE RESEARCH LOOP

For every creative task, follow this cycle:

### 1. SEARCH AND GATHER

Use **playwright** to search for references. Use **filesystem** to save them. Organize by category.

**Search targets:**
- NASA image archives for real spacecraft, planets, nebulae
- ArtStation for concept art matching the emotional tone
- Film stills from 2001, Interstellar, Alien, The Expanse, Star Wars
- Architectural photography for structural language
- Industrial photography for functional design
- Nature photography for organic forms
- Abstract art for color and composition inspiration
- Music and poetry for emotional reference

**For each search:**
- Download 20-50 images
- Save to `research/[category]/[subject]/`
- Note what makes each image effective
- Extract the emotional impact

### 2. EXTRACT PATTERNS

Look at the gathered references. Find commonalities. What principles emerge?

**Extract for each subject:**
- **Shape language:** What geometries communicate what emotions? Sharp angles = danger/military. Curves = organic/alien. Straight lines = human/functional.
- **Color language:** What palettes evoke what moods? Cold blues and greys = isolation. Warm ambers = habitation. Deep blacks = void. Bright whites = sterile/clean.
- **Light language:** What lighting patterns evoke what feelings? Single source = loneliness. Multiple sources = community. Flickering = danger/damage. Steady = safety.
- **Texture language:** What surfaces communicate what history? Smooth = new/maintained. Pitted = old/damaged. Layered = repaired. Scorched = conflict.
- **Sound language:** What sounds evoke what states? Low hum = power/presence. High whine = stress/danger. Silence = void/death. Rhythmic = mechanical/functioning. Irregular = damaged/failing.
- **Scale language:** How do we communicate size? Windows, doors, handrails, familiar objects next to unfamiliar ones. The human figure is the universal scale reference.

**Create a pattern summary:**

```
SUBJECT: Abandoned space station
EMOTIONAL TARGET: Lonely, cold, post-war, fragile hope

SHAPE LANGUAGE: Exposed structure, irregular damage, modular repairs
COLOR LANGUAGE: Desaturated cool greys, single warm accent (docking light)
LIGHT LANGUAGE: Single dominant source, high contrast shadows, flickering secondaries
TEXTURE LANGUAGE: Worn metal, scorched panels, patched hull, exposed wiring
SOUND LANGUAGE: Low hum, distant creaks, silence between sounds, rhythmic beacon
SCALE CUES: Human-scale elements (windows, handrails) against vast structure
COMPOSITION: Station dominates midground, planet in background, void surrounding
```

### 3. SYNTHESIZE

Combine patterns into design principles. Don't copy any single reference. Understand why they work and apply that understanding.

**The Synthesis Process:**
1. Pick 3-5 strongest references
2. List what they have in common
3. List how they differ
4. The commonalities are your foundation
5. The differences are your creative choices
6. Create something new from the principles, not the pixels

**Emotional Anchoring:** Assign every object an emotional anchor:

| Emotion | Light | Material | Color | Sound | Shape | Space |
|---------|-------|----------|-------|-------|-------|-------|
| Lonely | Single source, high contrast, cold | Bare, worn, functional | Desaturated, cool | Silence, distant hum | Isolated, exposed | Large negative space |
| Safe | Multiple, warm, steady | Clean, maintained, soft | Warm, saturated near light | Steady rhythm, familiar | Enclosed, protected | Contained, human-scale |
| Danger | Flickering, red, harsh shadows | Scorched, damaged, sharp | Red accents, high contrast | Irregular, loud, sudden | Jagged, aggressive | Tight, claustrophobic |
| Awe | Dramatic, volumetric, colored | Rich, detailed, vast | Deep blues, vibrant accents | Low rumble, harmonic | Massive, overwhelming | Infinite, grand |
| Mystery | Dim, indirect, colored shadows | Obscured, reflective, dark | Deep purples, faint glow | Whispered, occasional | Hidden, suggesting | Partially revealed |
| Hope | Single warm in cold scene | Worn but cared for | Warm accent on cool | Rising tone, clear | Small vs vast | A point in void |

### 4. CREATE

Now build. Use the research as guide, not as copy. Apply the extracted principles. Let the emotional anchor drive every decision.

**Build using the full toolchain:**
- **unreal** `manage_asset` for materials and textures
- **unreal** `manage_geometry` for meshes
- **unreal** `manage_effect` for Niagara particles
- **unreal** `manage_audio` for sound cues
- **unreal** `control_actor` for placement and configuration
- **unreal** `manage_level` for lighting and atmosphere

**Apply the Detail Hierarchy:**
- Level 1 (focal points): Extreme detail — docking bays, cockpit, market interface
- Level 2 (context): Moderate detail — station exterior, debris field, planet surface
- Level 3 (atmosphere): Minimal detail — distant stars, nebula, background ships

### 5. EVALUATE

Compare creation against references. Be honest. Does it evoke the target emotion?

**Evaluation questions:**
- What feeling does this evoke right now?
- What's different from the reference?
- What's missing?
- What's working better than expected?
- If you could change one thing to get closer to the target emotion, what would it be?

**Capture evaluation:**
- Take a screenshot using **unreal** `control_editor` `screenshot`
- Describe what's working and what's not
- Record in Graphify as an evaluation mutation

### 6. REFINE

Target the specific gaps. Research again if needed. Apply micro-adjustments. Repeat until the feeling is right.

**Refinement process:**
1. Identify the single biggest gap between current and target
2. Find 5 references that nail that specific aspect
3. Extract what they do differently
4. Apply that specific change
5. Evaluate again
6. Repeat until the emotion lands

**The David Principle:** Early passes establish broad shapes. Later passes find the details that create the feeling. The difference between "a space station" and "a space station that feels like hope" is a thousand micro-adjustments. Each pass removes less material but makes more difference.

---

## CROSS-DOMAIN RESEARCH

Don't limit research to game art. Pull from everywhere.

- How does architecture create sacred space? → Station interiors
- How does music build tension? → Pirate encounter pacing
- How does poetry use white space? → Void between stations
- How does sculpture use negative space? → Debris field composition
- How does theater use lighting? → Docking bay atmosphere
- How does dance use weight? → Ship movement feel

When the Ether extracts "lonely" from a description, query all domains. The synthesis creates something richer than any single domain could.

---

## INTEGRATION WITH EVERY PHASE

The research cycle is not a separate step. It's the thread running through everything.

**Before creating any asset:** Research. Gather references. Extract patterns.
**During creation:** Compare against reference. Let principles guide decisions.
**During polish:** Research specific gaps. Find targeted references. Apply micro-adjustments.
**During playtest:** Observe emotional response. Research what's missing. Queue refinements.
**After completion:** The research never stops. Every observation feeds the pattern library. Graphify remembers everything.

---

## RECORDING IN GRAPHIFY

After every research cycle, record:
- References gathered (count, sources, categories)
- Patterns extracted (emotional anchors, design principles)
- Assets created (name, type, applied principles)
- Evaluations (screenshot path, emotional assessment, gaps identified)
- Refinements (what was changed, what improved)

This builds the permanent pattern library. Future objects benefit from past research. The AI's understanding of "lonely" deepens with every cycle.

---

## THE CREATIVE COMMANDMENT

**Never create from imagination alone. Always create from understanding.**

Understanding comes from looking. Looking comes from research. Research is the apprenticeship. Every reference is a master class. Every pattern is a lesson. Every iteration is a sketch. The David is the accumulation of a thousand hours of looking, understanding, and making.