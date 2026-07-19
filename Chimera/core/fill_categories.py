#!/usr/bin/env python3
"""Replace generic save_load and physics questions with feature-specific ones across all feature JSONs."""

import json, os, copy

FEATURES_DIR = "docs/features"

FEATURE_QUESTIONS = {
    "Camera_Cinematic_Sequence": {
        "save_load": {
            "question": "Does the camera path keyframe data (position, rotation, FOV at each waypoint) need to persist between sessions, or is it authored at build time?",
            "answer": "Path keyframes are authored at build time in Sequencer. No runtime save/load needed. Only camera FOV preference and starting position may optionally persist."
        },
        "physics": {
            "question": "Does the camera flythrough obey any physical constraints (acceleration limits, momentum, collision) or is it purely cinematic spline interpolation?",
            "answer": "Purely cinematic. The camera follows an authored spline with no physics. No collision response, no momentum, no acceleration curves beyond Sequencer easing."
        }
    },
    "Camera_Educational_Showcase": {
        "save_load": {
            "question": "Which educational observations the player has already seen during the flythrough need to persist to avoid repeating the same label on replay?",
            "answer": "Yes. A 'seen_observations' bitmask per camera segment must persist. If the player re-watches the flythrough, already-shown labels should skip or summarize."
        },
        "physics": {
            "question": "Does the camera need collision-aware positioning to frame geological features, or is it always on the authored spline?",
            "answer": "Authored spline only. No physics needed. The camera path is hand-placed to frame each point-of-interest at its optimal angle."
        }
    },
    "Camera_Lighting_Transitions": {
        "save_load": {
            "question": "Does the lighting transition timing (start time-of-day, transition duration, target time-of-day) need to persist per save slot?",
            "answer": "The transition timing parameters are authored in Sequencer. No runtime save/load needed. Lighting state is part of the authored sequence."
        },
        "physics": {
            "question": "Does the lighting transition model physically correct light color temperature shifts (warm sunset to cool night) or is it artistic?",
            "answer": "Artistic with educational anchoring. Light color temperature shifts follow real physics directionally (warm at low angle, cool at zenith) but values are authored for visual impact rather than spectroradiometric accuracy."
        }
    },
    "Canyon_Resource_Indicators": {
        "save_load": {
            "question": "Does the player's discovered resource locations and status (mined, depleted, pending) need to persist across sessions?",
            "answer": "Yes. Resource node states (mined/unmined, depleted/active) are persistent game state. Each node has a unique ID and its extraction status must save. Frequent writes: every time the player extracts a resource."
        },
        "physics": {
            "question": "What geological principles determine resource distribution — does the system model hydrothermal vein deposition, sedimentary stratification, or magmatic concentration?",
            "answer": "Sedimentary stratification and hydrothermal deposition. Ore veins follow real geological rules: heavier minerals settle in lower strata, quartz veins fill fracture lines, fossil deposits occur in sedimentary layers. This teaches economic geology."
        }
    },
    "Canyon_Strata_Visuals": {
        "save_load": {
            "question": "Are stratum layer parameters (color, thickness, order) authored at build time or can they be modified at runtime and need to persist?",
            "answer": "Authored at build time. Strata layers are part of the terrain material and are deterministic from the seed. No save/load needed for strata visuals themselves."
        },
        "physics": {
            "question": "Does strata formation simulate real sedimentary processes (grain size sorting, cross-bedding, unconformities) or is it aesthetic layering informed by geology?",
            "answer": "Aesthetic layering for visual readability, informed by real geology. Layer order follows actual deposition principles (older below, younger above) but individual layers do not simulate grain sorting or cross-bedding physics."
        }
    },
    "Canyon_Terrain_Generation": {
        "save_load": {
            "question": "Does the terrain generation seed and any player-driven terrain modifications (digging, building) need to persist between sessions?",
            "answer": "The generation seed must persist (one integer). Terrain itself is regenerated deterministically from the seed. If the player modifies terrain (digging, building), those deltas must save. Write frequency: seed once at world creation, deltas on player edit."
        },
        "physics": {
            "question": "Does terrain erosion simulation use physically based hydraulic erosion (rainfall, runoff, sediment transport) or statistical noise that looks like erosion?",
            "answer": "Statistical noise that approximates erosion. A full hydraulic erosion simulation (Navier-Stokes, sediment transport) is computationally prohibitive at runtime. The noise model produces visually plausible canyon shapes with V-shaped valleys, alluvial fans, and meander patterns."
        }
    },
    "Celestial_Light_Rotation": {
        "save_load": {
            "question": "Does the current time-of-day (sun angle, star sphere rotation) need to persist and resume on load, or does the cycle always restart from dawn?",
            "answer": "Yes, time-of-day must persist. If the player saves at sunset and loads the save, the sun should still be at sunset position. One float value: accumulated rotation angle. Written only on manual save or checkpoint."
        },
        "physics": {
            "question": "Does the sun arc model real orbital mechanics (axial tilt, latitude-dependent arc, seasonal variation) or is it a fixed equatorial rotation?",
            "answer": "Fixed equatorial rotation in v1. Axial tilt and seasonal variation are identified as future enhancement. The rotation rate is constant and the arc is symmetric about the zenith with no seasonal change."
        }
    },
    "Cloud_Shadow_Rendering": {
        "save_load": {
            "question": "Are cloud shadow parameters (shadow density, softness, coverage) authored at build time or runtime-modifiable and in need of persistence?",
            "answer": "Authored at build time. Cloud shadow parameters are part of the volumetric cloud configuration. No runtime save/load needed for shadow properties."
        },
        "physics": {
            "question": "Do cloud shadows model the physical relationship between cloud optical depth and shadow darkness, or is shadow density a fixed aesthetic value?",
            "answer": "Fixed aesthetic value in v1. A physically accurate model would tie shadow darkness to cloud water content and optical depth, but v1 uses authored density for performance and visual consistency."
        }
    },
    "Cloud_Types_Educational": {
        "save_load": {
            "question": "Does the player's cloud-type identification progress (which clouds they have scanned, learned about, identified correctly) need to persist?",
            "answer": "Yes. The player's cloud identification journal records which cloud types they have scanned. This is player progression state and must save. Written when the player scans a new cloud type (infrequent, once per type)."
        },
        "physics": {
            "question": "Does the cloud classification system teach real cloud physics (cumulus convection, stratus stratification, cirrus ice crystal formation) or just visual identification?",
            "answer": "Both. Visual identification (shape, color, altitude) is the primary interaction, but each scan also explains the meteorological physics: warm air rising for cumulus, stable layers for stratus, high-altitude ice for cirrus."
        }
    },
    "Cloud_Weather_Connection": {
        "save_load": {
            "question": "Do weather state parameters (current weather pattern, storm progression, cloud-to-weather mapping) need to persist and resume on load?",
            "answer": "Yes. Weather state (current pattern, intensity, remaining duration) must save. Multiple float/integer values representing the weather system state machine. Written on manual save or weather transition."
        },
        "physics": {
            "question": "Does the weather system model real atmospheric physics (pressure gradients, humidity, adiabatic cooling, condensation) or is it a state machine with visual states?",
            "answer": "State machine with visual states, informed by real meteorology. The system cycles through weather patterns (clear, building clouds, storm, clearing) in a physically plausible order, but does not simulate air pressure or humidity numerically."
        }
    },
    "Demo_Camera_Path": {
        "save_load": {
            "question": "Is the camera path authored in Sequencer and baked into the level, or are keyframes saved separately and loaded at runtime?",
            "answer": "Authored and baked into the level via Sequencer. No separate save/load of path data. The camera path is part of the packaged level asset."
        },
        "physics": {
            "question": "Does the camera flythrough use any physics-based camera damping or collision, or is it entirely spline-interpolated?",
            "answer": "Entirely spline-interpolated. No physics applied to the camera. The camera follows the authored spline with no collision detection or momentum."
        }
    },
    "Demo_Canyon_Terrain": {
        "save_load": {
            "question": "Is the canyon terrain baked into the packaged level or regenerated from seed on each load, requiring seed persistence?",
            "answer": "Regenerated from seed at level load for the demo. The seed (one integer) must persist. The demo always generates the same canyon from the demo seed value."
        },
        "physics": {
            "question": "Is the demo canyon terrain shaped by procedural noise that mimics geological processes, or is it hand-sculpted?",
            "answer": "Procedural noise approximating geological processes. The demo showcases the procedural generation pipeline rather than hand-sculpted terrain, demonstrating the seed-based approach."
        }
    },
    "Demo_Day_Night_Cycle": {
        "save_load": {
            "question": "Does the demo's day/night phase need to persist on save so the player returns to the same time-of-day?",
            "answer": "Yes. Time-of-day must persist for save/load consistency. One float: accumulated cycle time. Written on manual save."
        },
        "physics": {
            "question": "Does the demo's day/night cycle follow a physically accurate sun trajectory or is it a simplified gameplay cycle?",
            "answer": "Simplified gameplay cycle. The sun rotates at a constant speed (compressed to ~5 minutes real-time) along a fixed equatorial arc. No axial tilt, no seasonal variation."
        }
    },
    "Demo_Educational_Triggers": {
        "save_load": {
            "question": "Do the trigger states (fired/not-fired, last-triggered-time, times-triggered) need to persist so the player does not see the same educational text on reload?",
            "answer": "Yes. Each trigger's 'last_triggered_time' and 'times_triggered' count must persist. This prevents spam and allows cooldown tracking. Written on each trigger fire (frequent during exploration)."
        },
        "physics": {
            "question": "Are trigger zones positioned with real-world physics considerations (line-of-sight, occlusion, distance-based falloff) or are they simple sphere volumes?",
            "answer": "Simple sphere/capsule volumes with distance fade. No physics occlusion. Triggers fire when the player enters the volume, regardless of visual line-of-sight."
        }
    },
    "Demo_Volumetric_Clouds": {
        "save_load": {
            "question": "Are cloud configuration parameters (density, coverage, type) authored at build time or do they need runtime persistence across sessions?",
            "answer": "Authored at build time. Cloud configuration is part of the volumetric cloud asset. No runtime save/load for cloud parameters in the demo."
        },
        "physics": {
            "question": "Do the volumetric clouds simulate real atmospheric light scattering (Mie scattering, Rayleigh scattering, phase functions) or use simplified shading?",
            "answer": "Simplified shading using UE5's volumetric cloud system, which approximates multiple scattering but does not model Mie/Rayleigh phase functions with physical accuracy. The visual result is convincing without being physically precise."
        }
    },
    "Educational_Scanner": {
        "save_load": {
            "question": "Does the scanner's calibration state, unlocked categories, and scan history (journal of scanned objects) need to persist across sessions?",
            "answer": "Yes. The scanner is a persistent tool with progression state: unlocked categories, calibration level, and scan history journal. This is core player state. Written on progression unlock or manual save."
        },
        "physics": {
            "question": "What physical sensing principle does the scanner simulate (spectroscopy, LIDAR, ground-penetrating radar, mass spectrometry) and how does accuracy degrade with distance?",
            "answer": "Multi-principle simulation. The scanner uses 'spectral analysis' for mineral identification (simulated reflectance spectroscopy), 'GPR mode' for subsurface features, and 'atmospheric sampling' for air composition. Accuracy degrades with distance quadratically and is reduced by weather interference."
        }
    },
    "Environmental_Demo": {
        "save_load": {
            "question": "What specific elements of the environmental demo need to persist: camera progress, educational triggers fired, time of day, or is it a fresh-start experience each time?",
            "answer": "Fresh-start experience. The demo is a walkthrough meant to be experienced in one sitting. No save/load needed. Everything resets on launch."
        },
        "physics": {
            "question": "Does the demo environment need any physics simulation (wind effects, particle systems, dynamic lighting) or is it primarily static geometry?",
            "answer": "Primarily static geometry with dynamic lighting (day/night) and wind-driven cloud movement. No destructible physics or rigid body simulation. The physics needs are limited to the day/night cycle and cloud drift."
        }
    },
    "Flight_Orbital_Mechanics": {
        "save_load": {
            "question": "Does the ship's orbital state (position, velocity vector, current reference body, orbital parameters) need to persist and resume accurately on load?",
            "answer": "Yes. Orbital state is the most critical save data for this feature: position (x,y,z), velocity vector (vx,vy,vz), current reference body, and time since insertion. This is ~7 floats. Written on manual save or checkpoint. Frequent auto-saves recommended during orbital maneuvers."
        },
        "physics": {
            "question": "Does the flight model use real N-body orbital mechanics (Newtonian gravitation, Keplerian orbits, Lagrange points) or simplified patched-conic approximation?",
            "answer": "Simplified two-body patched-conic approximation in v1. Each body's sphere of influence is modeled separately with Newtonian gravity (F = GMm/r\u00b2). N-body interactions are deferred. This is sufficient for teaching orbital insertion, transfer burns, and gravity well traversal."
        }
    },
    "Fuel_Consumption_System": {
        "save_load": {
            "question": "Does the fuel state per tank/resource type need to persist, and are consumption rates deterministic so fuel level is identical on reload at the same state?",
            "answer": "Yes. Fuel levels per tank and fuel type are persistent state. Consumption must be deterministic (based on delta-v expended, not real time) so reloading at the same orbital position gives the same fuel level. Written on burn completion or manual save."
        },
        "physics": {
            "question": "Does fuel consumption model the Tsiolkovsky rocket equation with real specific impulse values for different fuel types, teaching the exponential cost of delta-v?",
            "answer": "Yes. The rocket equation is the core mechanic. Different fuel types have different Isp values (chemical: ~350s, nuclear-thermal: ~900s, ion: ~3000s). The player must budget delta-v against the rocket equation, learning that higher Isp means less fuel for the same delta-v but potentially lower thrust."
        }
    },
    "HUD_Notification_System": {
        "save_load": {
            "question": "Does the notification history (which messages the player has seen/dismissed) and queue state need to persist across sessions?",
            "answer": "Yes. Dismissed notification IDs should persist to avoid re-showing dismissed messages. Queue state (pending notifications) should also persist. Written on notification dismiss."
        },
        "physics": {
            "question": "Does the HUD notification system have any physics-based animation (spring dynamics for pop-in, velocity-based scrolling)?",
            "answer": "No physics simulation. Animations are authored keyframes in UMG. Pop-in uses simple scale/fade curves. No spring dynamics or physics-driven layout."
        }
    },
    "NPC_AI_Behavior": {
        "save_load": {
            "question": "Does each NPC's current state (location, activity, faction reputation, task queue, schedule position) need to persist and resume on load?",
            "answer": "Yes. NPC AI state is complex and must persist: current location (vector3), current activity (enum), task queue (array of task IDs), schedule position (time of day), faction standing (float per faction). Heavy save data. Written on manual save or zone unload."
        },
        "physics": {
            "question": "Does NPC movement use physics-based locomotion (momentum, acceleration curves, ground friction) or animation-driven root motion?",
            "answer": "Animation-driven root motion with navigation mesh pathfinding. No physics simulation for NPC bodies. Collision is handled by UE5's character movement component with standard capsule collision."
        }
    },
    "NPC_Basic": {
        "save_load": {
            "question": "Does the basic NPC's spawn state, location, and conversation flags (greeted, quest items received) need to persist?",
            "answer": "Yes. NPC location, spawn state (alive/disabled), and interaction flags must persist. These are core world state. Written on manual save."
        },
        "physics": {
            "question": "Does the NPC character use physics-based ragdoll on death, or standard animation state transitions?",
            "answer": "Standard animation state transitions. Ragdoll physics is not planned for v1. NPC death triggers a canned animation, not a physics simulation."
        }
    },
    "NPC_Dialogue_System": {
        "save_load": {
            "question": "Does the dialogue state (active branch, completed topics, reputation-gated unlocks, conversation history) need to persist?",
            "answer": "Yes. Dialogue state is complex: completed topics (bitmask or set of IDs), current reputation thresholds met, active quest dialogue branches. Written on conversation end or manual save."
        },
        "physics": {
            "question": "What physical principles apply to a dialogue system — is there any physics consideration (acoustic propagation, lip-sync physics, spatial audio)?",
            "answer": "No physics relevance for the dialogue logic itself. Spatial audio and lip-sync are handled by UE5's audio and animation systems, not by the dialogue state machine."
        }
    },
    "NPC_Trade_Mechanics": {
        "save_load": {
            "question": "Do trade inventories, prices, supply/demand modifiers, and player reputation per NPC need to persist?",
            "answer": "Yes. Each NPC trader has inventory (item IDs + quantities), price modifiers, and dynamically adjusted supply/demand based on recent trades. Written on trade completion or manual save. Write frequency: every trade transaction."
        },
        "physics": {
            "question": "Does the trade system model any physical constraints (cargo mass, storage volume, fuel cost of transporting goods) or is it purely economic?",
            "answer": "Not in v1. Trade is purely economic (currency-for-goods) with no physical cargo simulation. Cargo mass/volume and transport costs are identified as a future enhancement for the economic system."
        }
    },
    "Night_Visibility_Gameplay": {
        "save_load": {
            "question": "Does the player's night-vision equipment state (active, charge level, upgrade level) and visibility settings need to persist?",
            "answer": "Yes. Night vision equipment state (on/off, battery charge, upgrade tier) must persist. Also the player's brightness/contrast preferences for accessibility. Written on manual save or equipment change."
        },
        "physics": {
            "question": "Does night visibility simulate real scotopic/photopic vision (rod/cone adaptation, pupil dilation over time) or is it a simple brightness curve?",
            "answer": "Simple brightness curve in v1. Eye adaptation (darkness exposure time affecting visibility) is approximated but does not model real rod/cone photochemistry. Full adaptation takes ~2 seconds game-time, not the real-world 20-30 minutes."
        }
    },
    "Prompt_Selection_Logic": {
        "save_load": {
            "question": "Does the prompt history (which educational prompts have been shown, priority scores, debounce timers) need to persist?",
            "answer": "Yes. Prompt selection state requires persistence: every prompt ID has a 'last_shown_time' and 'display_count'. Priority scores are recalculated from state. Written on each prompt display."
        },
        "physics": {
            "question": "What physical principles apply to a prompt selection system?",
            "answer": "No physics relevance. Prompt selection is a priority-scored decision engine with debouncing. No physical simulation."
        }
    },
    "Scanner_Audio_Feedback": {
        "save_load": {
            "question": "Does the audio settings (volume, mute state) specific to scanner sounds need to persist?",
            "answer": "Yes. Scanner audio channel volume and mute state must persist as part of the global audio settings. Written when player changes audio settings."
        },
        "physics": {
            "question": "Does the scanner audio simulate real acoustic phenomena (Doppler shift, attenuation over distance, material-dependent reflection) or is it stylized feedback?",
            "answer": "No. Scanner audio is stylized feedback (activation chirp, scanning hum, result chime). It does not simulate real acoustic physics. Each scan category has a distinct audio signature for gameplay clarity."
        }
    },
    "Scanner_Progression_System": {
        "save_load": {
            "question": "Does every scanner upgrade state (unlocked tiers, current calibration level, XP/progress toward next unlock) need to persist?",
            "answer": "Yes. This is inherently a progression system: unlocked upgrade tiers (array of IDs), current calibration level (integer), scan count per category (integer per category). This IS the persistent state. Written on upgrade unlock or manual save."
        },
        "physics": {
            "question": "Does scanner progression model real instrument physics (signal-to-noise ratio improving with calibration, resolution increasing with aperture) for educational value?",
            "answer": "Abstracted progression. Upgrades improve numerical parameters (range +25%, scan speed -30%, new category unlock) rather than simulating real instrument physics. The educational connection is explained in flavor text but not simulated."
        }
    },
    "Scanner_Tool_Implementation": {
        "save_load": {
            "question": "Does the scanner's active state, current mode selection, and target lock need to persist between sessions?",
            "answer": "Partially. Active state (equipped/not) is transient. Mode selection (geology vs atmosphere vs biology) should persist once unlocked. Target lock is transient. Written on mode change (infrequent)."
        },
        "physics": {
            "question": "What physical principles govern the scanner's interaction with materials: does it use simulated reflectivity, density, or composition data, or a lookup table?",
            "answer": "Lookup table driven by the graph knowledge base. When the scanner targets a canyon wall, it queries the feature graph for the geological data at that location. No simulated physics interaction with the material itself."
        }
    },
    "Scanner_UI_Display": {
        "save_load": {
            "question": "Does the scanner UI layout customization (element positions, visible panels, transparency, scale) need to persist?",
            "answer": "Yes. UI layout preferences (element positions, visible panels, scale, opacity) should persist. Written when player customizes the HUD layout."
        },
        "physics": {
            "question": "What physical principles apply to a scanner UI display system?",
            "answer": "No physics relevance. UI display is 2D screen-space rendering with no physics simulation."
        }
    },
    "Shelter_Habitat": {
        "save_load": {
            "question": "Does every shelter's structural state (module list, positions, connections, damage, resource inventory) need to persist?",
            "answer": "Yes. Shelters have complex persistent state: list of placed modules with positions/rotations, module health/damage per module, stored resources, occupant count. This is heavy save data. Written on manual save or module change."
        },
        "physics": {
            "question": "What structural physics apply to shelters — load-bearing, stress distribution, collapse mechanics under weight or storm stress?",
            "answer": "Simplified structural integrity model. Each module has a structural load capacity. Exceeding it (too many stacked modules, storm damage reducing capacity) causes progressive deformation then collapse. Collapse uses basic rigid body physics for debris."
        }
    },
    "Shelter_Material_Properties": {
        "save_load": {
            "question": "Are material property definitions (insulation values, durability, weight) authored as data tables (constant) or can players develop improved materials that need persistence?",
            "answer": "Material base properties are authored data tables (constant). Player-crafted improved materials (e.g., reinforced composite) have modified properties that must persist. Written on material crafting or discovery."
        },
        "physics": {
            "question": "Do material properties model real thermodynamics (thermal conductivity, R-value, specific heat capacity) for the temperature system?",
            "answer": "Abstracted thermodynamics. Each material has insulation (0-100), durability (HP), and weight (kg). These are not derived from real R-values or specific heat but are authored for gameplay balance while being directionally accurate (stone insulates better than fabric)."
        }
    },
    "Shelter_Module_System": {
        "save_load": {
            "question": "Does the module blueprint definition, placement state, and connections to other modules need to persist?",
            "answer": "Yes. Module placement is the core persistent data: module type ID, world transform (location + rotation), connected module IDs (array), current health. Written on module placement, destruction, or manual save."
        },
        "physics": {
            "question": "Do module connections use physics constraints (snap-point alignment, joint strength, shear force limits) or simple positional snapping?",
            "answer": "Simple positional snapping with snap-point alignment. Connection integrity is tracked as a health value, not simulated via physics joints. Modules interlock via authored snap points similar to Valheim or Satisfactory."
        }
    },
    "Shelter_Weather_Interaction": {
        "save_load": {
            "question": "Does the accumulated weather damage per shelter module need to persist so damage is consistent across reloads?",
            "answer": "Yes. Each module stores accumulated weather damage (float), current damage state (undamaged/damaged/critical/destroyed), and repair progress. Written on damage tick or repair action. Write frequency: every weather tick that changes state."
        },
        "physics": {
            "question": "What atmospheric physics govern weather effects on shelters — wind load (force based on exposed surface area), thermal cycling, or precipitation erosion?",
            "answer": "Simplified wind load model. Damage rate scales with wind speed (exposed face takes more damage) and precipitation intensity. Thermal cycling (expansion/contraction from day/night temperature swings) is modeled as gradual fatigue damage. No fluid dynamics for water erosion."
        }
    },
    "Star_System_Navigation": {
        "save_load": {
            "question": "Does the player's discovered star chart data, plotted routes, and visited systems need to persist?",
            "answer": "Yes. Star chart state is persistent exploration progress: discovered star positions (x,y,z in galaxy), visited system IDs (set), plotted routes (source-destination pairs), navigation waypoints. Heavy save data. Written on discovery or route plot."
        },
        "physics": {
            "question": "Does the star navigation system use real stellar physics (proper motion, parallax, spectral classification, Hertzsprung-Russell diagram) or is it abstracted?",
            "answer": "Abstracted with real references. Star positions are world-aligned and fixed (no proper motion simulation). Spectral classification (OBAFGKM) is used for star color and temperature display. The HR diagram is shown in educational annotations but does not drive the simulation."
        }
    },
    "Temperature_Time_System": {
        "save_load": {
            "question": "Does the current ambient temperature and daily temperature curve parameters need to persist so the player returns to the same thermal environment?",
            "answer": "Yes. Current temperature (float) and time-of-day phase (float) must persist. The temperature curve is deterministic from time-of-day and weather state, so only the time reference needs to save. Written on manual save."
        },
        "physics": {
            "question": "Does the temperature system model real thermodynamic processes (solar irradiance, albedo, greenhouse effect, thermal mass, convection cooling by wind)?",
            "answer": "Simplified thermodynamic model. Temperature is computed from a base value modulated by: solar angle (irradiance proxy), cloud cover (albedo/shading), and wind speed (convection cooling). No greenhouse gas model or ground thermal mass simulation. The curve is physically plausible but not precise."
        }
    },
    "Tool_Crafting_System": {
        "save_load": {
            "question": "Does every crafted item, recipe state, available blueprints, and crafting station inventory need to persist?",
            "answer": "Yes. Crafting is a persistence-heavy system: known recipes (set of IDs), crafting station inventories (item stacks per station), player inventory of crafted items. Written on craft completion or manual save."
        },
        "physics": {
            "question": "Does the crafting system model any physical fabrication process (heat treatment, alloy formation, forging pressure) or is it recipe-driven assembly?",
            "answer": "Recipe-driven assembly. The player combines ingredients at a crafting station and receives the output. No physical fabrication simulation. Educational flavor text describes the real process (e.g., 'smelting iron ore at 1538\u00b0C separates metal from gangue') but no physics drives it."
        }
    },
    "Tool_Durability_Maintenance": {
        "save_load": {
            "question": "Does each tool's current durability, quality modifiers, and repair history need to persist?",
            "answer": "Yes. Each tool item stores: current durability (float 0-100), max durability (float, affected by material quality), repair count (integer, each repair slightly reduces max durability), and quality modifiers. Written on tool use or repair. Frequent writes during gameplay."
        },
        "physics": {
            "question": "Does tool wear model real material fatigue (stress cycles, work hardening, crack propagation) or is it a linear degradation curve?",
            "answer": "Linear degradation per use with a quality multiplier. No material fatigue simulation. Higher-quality tools degrade slower (lower linear rate) and can be repaired more times. The educational connection is explained textually rather than simulated."
        }
    },
    "Tool_Systems": {
        "save_load": {
            "question": "Does the player's tool belt contents, equipped tool, and tool-specific auxiliary state (fuel, charge, ammo) need to persist?",
            "answer": "Yes. Tool inventory state: equipped tool ID, tool belt contents (array of item IDs), per-tool auxiliary resources (fuel/charge/ammo). Written on tool switch, use, or manual save."
        },
        "physics": {
            "question": "What physical principles govern each tool's operation — for example, does the mining tool simulate impact force versus material hardness, or is it a DPS abstraction?",
            "answer": "Damage-per-second abstraction for combat tools. Mining tools use a material hardness multiplier (softer materials mine faster) but do not simulate impact force or fracture mechanics. Scanner tools are data-driven with no physical emission simulation."
        }
    },
    "Travel_Systems": {
        "save_load": {
            "question": "Does the entire travel state (current system, current body, orbital parameters, fuel, plotted route) need to persist?",
            "answer": "Yes. Travel state is the most complex persistent data: current star system ID, current orbital body, orbital position/velocity, fuel levels per tank, plotted route waypoints, navigation history. This is the heart of the game's persistent state. Written on manual save or significant travel event."
        },
        "physics": {
            "question": "Does interstellar travel model real astrophysics (relativistic time dilation, light-speed lag, gravitational lensing) or use gameplay-friendly warp mechanics?",
            "answer": "Gameplay-friendly warp mechanics. Interstellar travel uses 'warp drive' (skip to destination after a loading screen with travel time calculation). No relativistic effects. In-system travel uses the orbital mechanics model (real physics). This split keeps interstellar travel accessible while teaching real orbital physics in-system."
        }
    },
    "Trigger_Placement_Strategy": {
        "save_load": {
            "question": "Are trigger volume positions and configurations authored in the level (constant) or can they be modified at runtime, requiring persistence?",
            "answer": "Authored at build time. Trigger volumes are placed during level design and baked into the level. No runtime modification of trigger placement needed. Therefore no persistence needed."
        },
        "physics": {
            "question": "Do trigger volumes use any physics-based detection (line-of-sight raytracing, occlusion queries, physics channels) or simple overlap tests?",
            "answer": "Simple overlap tests via UE5 trigger volumes (BoxComponent/CapsuleComponent with OnComponentBeginOverlap). No raytracing or occlusion queries. A trigger fires when the player's collision capsule enters the volume regardless of intervening geometry."
        }
    }
}

def fill_features():
    files = sorted(os.listdir(FEATURES_DIR))
    updated_count = 0
    
    for fname in files:
        path = os.path.join(FEATURES_DIR, fname)
        if not fname.endswith(".json"):
            continue
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if "questions" not in data:
            print(f"SKIP (no questions): {fname}")
            continue
        
        name = data.get("name", "")
        if name not in FEATURE_QUESTIONS:
            print(f"SKIP (no mapping): {name}")
            continue
        
        qs = data["questions"]
        qdata = FEATURE_QUESTIONS[name]
        modified = False
        
        # Find and replace save_load and physics questions
        for q in qs:
            if q["category"] == "save_load":
                old_question = q["question"][:60]
                q["question"] = qdata["save_load"]["question"]
                q["answer"] = qdata["save_load"]["answer"]
                modified = True
                print(f"  save_load: {name} -- was '{old_question}...' -> replaced")
            elif q["category"] == "physics":
                old_question = q["question"][:60]
                q["question"] = qdata["physics"]["question"]
                q["answer"] = qdata["physics"]["answer"]
                modified = True
                print(f"  physics:   {name} -- was '{old_question}...' -> replaced")
        
        if modified:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            updated_count += 1
    
    print(f"\nDone. Updated {updated_count} feature files.")

if __name__ == "__main__":
    fill_features()
