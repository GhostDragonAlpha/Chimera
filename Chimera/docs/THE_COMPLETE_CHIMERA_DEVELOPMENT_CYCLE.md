# The Complete Chimera Development Cycle

## Overview

The Chimera Development Cycle is a structured, iterative workflow for building video games in Unreal Engine through research-driven design and systematic verification. It combines education (learning from real-world references), creative research (extracting parameters from those references), application (building test scenes in UE5), and verification (comparing against references via AI vision models).

The cycle follows a spiral growth pattern: each loop builds on the previous one, refining materials, geometry, lighting, and mechanics until they match their real-world references. The process is governed by contracts — pre-flight checks before building, post-flight records after verifying.

---

## The 13 Schools (Education Phase)

Before any building begins, all 13 schools must be attended. Each school teaches principles that will later be linked to specific features in the Feature Ledger.

### School 1: Game Development
- Subjects: Camera systems, lighting design, material workflows, animation states, input handling
- Principles: Third-person camera distance (1.5–2.5m behind player), FOV (60–90°), pitch angle (-15 to -20° for gameplay, 0 to +5° for realism)

### School 2: Art School
- Subjects: Color theory, PBR workflows, material layering, texture tiling, normal mapping
- Principles: BaseColor hex codes, Roughness (0.0–1.0), Metallic (0.0–1.0), clearcoat layers, anisotropic direction

### School 3: Film School
- Subjects: Three-point lighting, camera angles, framing, color grading, visual storytelling
- Principles: Key light intensity (2x fill), fill light softness, rim light separation, HDRI environment captures for reflections

### School 4: Architecture School
- Subjects: Spatial reasoning, scale, proportion, material transitions, environmental storytelling
- Principles: Ground plane scale matching real-world dimensions, rock patch placement following natural patterns, metal surfaces near station areas

### School 5: Engineering School
- Subjects: Physics simulation, collision detection, performance optimization, LOD management
- Principles: Collision bounds for player character, mesh simplification at distance, draw call batching for materials

### School 6: Unreal Engine Craft
- Subjects: Blueprint workflows, material graphs, particle systems, Niagara effects, PCG volumes
- Principles: Material instance creation, parameter-driven variation, procedural mesh generation, volume-based effect triggers

### School 7: Spatial Reasoning
- Subjects: Environmental layout, sight lines, navigation flow, player orientation, landmark placement
- Principles: Camera sight lines avoiding clipping, landmarks for player orientation, navigation mesh coverage

### School 8: Iteration and Refinement
- Subjects: Version control, regression testing, snapshot comparison, parameter tuning, visual verification
- Principles: Screenshot-based comparison against references, iterative refinement until LM Studio confirms match, DNA graph recording of each iteration

### School 9: Emotion-to-Parameter Mapping
- Subjects: Mood boards, emotional tone translation, atmospheric lighting, color psychology
- Principles: Translating "isolation" to desaturated colors and high contrast, "wonder" to wide FOV and dramatic lighting

### School 10: Reference Management
- Subjects: Image organization, parameter extraction, PBR measurement, material sampling, documentation
- Principles: Extracting exact hex codes from reference images, measuring roughness via specular highlight spread, documenting source URLs for each parameter

### School 11: Creativity and Problem Solving
- Subjects: Constraint-based design, procedural generation, emergent behavior, player agency
- Principles: Working within available tools (MCP pathways), adapting when references don't match exactly, finding creative workarounds

### School 12: Collaboration and Communication
- Subjects: Documentation standards, version control etiquette, code review practices, team coordination
- Principles: Clear commit messages linking changes to Feature Ledger entries, structured documentation for agent handoff

### School 13: The Complete Cycle (Meta-School)
- Subjects: Workflow orchestration, phase management, spiral growth tracking, quality gates
- Principles: Education before research, research before application, application before verification, verification before next loop

---

## Six Phases of the Development Cycle

### Phase 0: Foundation
1. Verify editor is running and accessible via MCP
2. Confirm DNA graph exists at `docs/chimera_dna_graph.json`
3. Check LM Studio model availability (`qwen3.6-35b-a3b-mtp@iq2_m`)
4. Query Graphify for existing pathways — if none exist, run pathway discovery

### Phase 1: Creative Research (Spiral Loops)
For each spiral loop (0 through N):
1. Identify features to research from the Feature Ledger
2. Extract exact parameters from real-world references (NASA photos, Apollo imagery, astronaut footage)
3. Record findings as Reference nodes in DNA graph with source URLs and extracted values
4. Link education principles from relevant schools to each feature

### Phase 2: Apply & Verify
For each verified research loop:
1. Build test scenes using MCP pathways (query Graphify before each call)
2. Apply materials, lighting, camera settings per extracted parameters
3. Take screenshots and send to LM Studio for visual comparison against references
4. Iterate until LM Studio confirms match — record each iteration in DNA graph

### Phase 3: Integration
1. Merge verified test scenes into the main level
2. Connect gameplay systems (movement, interaction, UI)
3. Run automated tests if available
4. Update Feature Ledger with integration status

### Phase 4: Polish
1. Apply final material refinements based on LM Studio feedback
2. Optimize performance (LODs, draw calls, memory usage)
3. Add visual effects and polish details
4. Final verification against all references

### Phase 5: Release
1. Package the build for target platform
2. Generate release notes documenting verified features
3. Archive DNA graph state as milestone snapshot
4. Update Feature Ledger with final statuses

---

## Spiral Growth Pattern

The development follows a spiral pattern where each loop builds on previous work:

```
Loop 0 (Player) → Loop 1 (Ground) → Loop 2 (Verbs) → Loop 3 (Sky) → ... → Loop N (Universe)
     │                │               │              │                  │
     └─── Verified ───┴───────────────┴──────────────┴──────────────────┘
```

Rules:
- Complete all features in Loop N before starting Loop N+1
- Each loop's verified output becomes the foundation for the next loop
- The spiral grows outward from the player character to the entire universe

---

## Feature Ledger Structure

The Feature Ledger tracks every feature across all loops:

```json
{
  "feature_name": "Player_Character_Suit",
  "loop": "Loop_0_Player",
  "status": "verified | needs_refinement | not_started",
  "parameters": "Exact PBR values extracted from research",
  "research_references": ["NASA Apollo EVA suit photos", "EMU documentation"],
  "education_principles": ["School 2 Art School: PBR workflows", "School 3 Film School: material rendering"],
  "verification_history": [
    {"iteration": 1, "lm_studio_feedback": "...", "change_applied": "..."},
    {"iteration": 2, "lm_studio_feedback": "...", "change_applied": "..."}
  ],
  "verified_at": "ISO timestamp"
}
```

Status values:
- `not_started`: Feature has not been researched or built
- `in_progress`: Research complete, building in progress
- `needs_refinement`: Built but LM Studio feedback indicates changes needed
- `verified`: LM Studio confirms match with reference

---

## The Ralph Loop

The Ralph Loop is the iterative verification process within Phase 2:

1. **Build**: Create test scene using MCP pathways (query Graphify first)
2. **Screenshot**: Capture viewport screenshot
3. **Compare**: Send to LM Studio alongside reference images
4. **Record**: Save LM Studio's assessment in DNA graph
5. **Refine**: Apply the ONE change LM Studio suggests
6. **Repeat**: Go back to step 2 until verification passes

The loop continues until all features in a loop are verified before advancing to the next loop.

---

## The Contract (Pre-Flight / Post-Flight)

### Pre-Flight Checklist (Before Every MCP Call)
1. Query Graphify: `g.query("pathway", "what_you_want_to_do")`
2. If pathway exists: follow it exactly — do not experiment
3. If pathway does NOT exist:
   - Report: "No pathway found for [task]"
   - Test the simplest possible approach
   - If it works: record the pathway in Graphify for future use
   - If it fails: record the failure, try next approach

### Post-Flight Checklist (After Every MCP Call)
1. Record result in DNA graph: mutation node with pathway name, success/failure, error message
2. Update Feature Ledger if the call changed a feature's status
3. Take screenshot if verification was involved — save to `Saved/Screenshots/`

---

## MCP Pathway Query Rule (MANDATORY)

### Before ANY MCP Call:

1. **Query Graphify**: `g.query("pathway", "what_you_want_to_do")`
   - Examples: `g.query("pathway", "create_material")`, `g.query("pathway", "spawn_point_light")`
   
2. **If pathway exists**: Follow it exactly. Do not deviate. Do not experiment.

3. **If pathway does NOT exist**:
   - Report: "No pathway found for [task]"
   - Use `manage_tools` → `list_tools` to find tools that might work
   - Test the simplest possible approach
   - If it works: record the pathway in Graphify for future use
   - If it fails: record the failure, try next approach

4. **After ANY MCP call**: Record result in DNA graph as a mutation node with pathway name, success/failure status, and error message if any.

This rule prevents random tool testing when a proven pathway exists, repeating failed approaches across sessions, and agents wasting time reading documentation for tools they don't need. The pathways accumulate — every successful MCP interaction becomes a pathway; every failure becomes a warning. The graph grows smarter with every call.

---

## File Paths (Canonical Project)

All paths are relative to `E:\PythonChimera\Chimera\`:

| Component | Path |
|-----------|------|
| DNA Graph | `docs/chimera_dna_graph.json` |
| Knowledge Graph | `docs/chimera_knowledge_graph.json` |
| MCP Pathways | `docs/MCP_PATHWAYS.md`, `docs/MCP_PATHWAYS.json` |
| Screenshots | `Saved/Screenshots/` |
| DNA Dashboard | `dna_dashboard.py` |
| Graphify Interface | `core/graphify_interface.py` |
| Build Pipeline | `run_deep_space_trader_pipeline.py` |

---

## Current Project State

- **DNA Nodes**: 459 (growing with each iteration)
- **MCP Pathways**: 11 working, 1 failed
- **Feature Ledger Entries**: 56 features across 10 spiral loops (Loop 0–9)
- **Current Phase**: Phase 2 — Apply & Verify (Loops 0–2 in progress)
- **Verified Features**: Player_Character_Lighting, Ground_Sand_Surface, Verb_Look
