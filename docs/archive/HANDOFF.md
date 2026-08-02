# Foundry Capability & Handoff Document

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

The Gaussian Foundry autonomous development system has completed its design
and construction phase. This document describes what was built, what the
foundry can and cannot do, and what needs human intervention.

## What Was Built

### Educational Canyon Demo
- 30 educational texts in UE5 level (geology, meteorology, astronomy)
- Volumetric clouds with slow drift animation
- 18 TriggerBox volumes for zone-based education
- Wind ambient actor (needs sound assigned)
- Star sphere with night sky educational content
- Day/night orchestrator in Python (not wired to UE5 lighting)

### Pipeline
- game_code_generator.py fixed: 20+ C++ errors resolved
- All AErisaidActor timer/function declarations corrected
- SetTimer signatures updated for UE5.8 API
- Pipeline compiles (can't link with editor open)

### Python Modules
- core/geology.py — rock type classification, strata, educational descriptions
- core/env_education.py — educational prompts for all 3 sciences
- core/cloud_education.py, cloud_weather.py — meteorology system
- core/celestial_rotation.py, env_temperature.py — day/night simulation
- core/day_night_orchestrator.py — full environmental tick system
- core/feature_graph.py — feature graph management (2028+ questions)

### Tools
- worker_bridge/mcp_builder.py — MCP client with session management
- worker_bridge/respawn_demo.py — one-command demo rebuild
- worker_bridge/worker_client.py — bridge SDK

### Steam Page Assets
- docs/steam_capsule.png (616x353)
- docs/demo_images/ (10 screenshots)
- docs/STEAM_PAGE.md (description, features, price: $19.99 EA)
- docs/DEMO_WALKTHROUGH.html (interactive slideshow)

## Foundry Capabilities

### Can Do
- Ask questions until feature design is saturated
- Write Python modules for game logic
- Spawn UE5 actors via MCP (TextRenderActor, TriggerBox, etc.)
- Set component properties (text, color, size, rotation, etc.)
- Create Blueprint assets (empty — no logic wiring)
- Take viewport screenshots
- Verify actor existence via MCP inspect
- Build HTML documentation from screenshots
- Fix C++ compilation errors in generated code

### Cannot Do
- Wire Blueprint logic (events, graphs, node connections)
- Create UMG/HUD widgets
- Edit Sequencer camera paths
- Author audio content or assign sounds
- Save the level file (.umap)
- Package standalone builds
- Create or manage Steam store pages
- Playtest the game (requires human perception)

## Handoff Instructions

To complete and ship the demo, a human needs to:

1. **Save the level:** Open UE5 editor, press Ctrl+S. This persists all
   30 educational texts, trigger boxes, cloud settings, and star sphere
   into the .umap file.

2. **Package the build:** Close the editor (so DLLs unlock), run the
   pipeline, then use UE5's File → Package Project to create a standalone
   .exe. The pipeline now compiles without errors.

3. **Create the Steam page:** Use the assets in docs/ to create a Coming
   Soon page. docs/STEAM_PAGE.md has the description. docs/steam_capsule.png
   is the capsule image. docs/demo_images/ has the screenshots.

4. **Build the scanner tool (optional):** Educational_Scanner feature is
   fully designed (43 questions answered). Python scanner module exists.
   Needs a human to create the UE5 Blueprint UI and wire the scanning
   interaction.

5. **Add audio (optional):** Wind_Ambient actor exists in the level but
   has no sound assigned. A wind audio file or MetaSound would make the
   canyon feel alive.

## Next Feature Cycles (Designed, Ready to Build)

When development resumes on the full game, these features are fully
designed in the graph and ready for implementation:

- Travel_Systems (41 questions) — orbital mechanics education
- NPC_Basic (41 questions) — social science education
- Shelter_Habitat (41 questions) — survival science education
- Tool_Systems (41 questions) — tool crafting and durability
