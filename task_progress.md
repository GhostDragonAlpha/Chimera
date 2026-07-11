# Session 2026-07-11 — Ground_Sand_Sound: audio subsystem for ground sand particles, wind layers, footstep feedback, ambient richness

**Scope:** game development (\"make the game\"). Additive, non-invasive.

**What exists:** Ground_Sand_Particles has visual dust trails and drift but no sound system at all — no wind ambience, no footstep impact audio, no particle response to movement or environmental events. The study guide flags this as \"audio-visual sync completely missing\" (Tier 2 Player Immersion) and \"ambient richness completely missing\" (Tier 3 Audio Design).

**Plan:** Implement a layered sound system:
1. Wind layers: low rumble, mid-range rush, high-frequency whistle — all spatialized to the ground surface, wind speed-driven volume/pitch.
2. Footstep feedback: impact burst synchronized with dust particle burst on each footfall, pitch/resonance varying by surface type (sand vs rock vs metal).
3. Ambient richness: distant thunder, bioluminescent hums, subsonic seismic rumble — all diegetic to the environment.
4. Accessibility: colorblind-friendly particle palettes for visual feedback when audio is muted, difficulty-based hazard density tied to sound intensity.

**References:** AAA_DEVELOPMENT_ROADMAP.md §9 Audio Design (wind layers, footstep feedback, ambient richness), PENDING_HEURISTICS.md #10 polish & juiciness (particle effects, animation juice).

## NEXT
1. Ground_Sand_Sound - CODE COMPLETE (pending build + PIE verify):
   - Footstep audio now auto-loads CC0 Fantozzi assets from /Game/Audio/Footsteps when the
     Sand/Rock/Metal/Ground/WaterFootstepSound properties are unset (bAutoLoadDefaultFootsteps=true).
   - Wind layer system implemented in USandSoundComponent: StartWind/StopWind/SetWindIntensity,
     speed-driven volume/pitch/low-pass, auto-starts in BeginPlay when WindLoopSound is set.
     No wind loop asset exists yet - drop one on WindLoopSound to activate (system is ready).
   - Footstep impact is already coupled to the dust burst in the same tick (audio-visual sync);
     servo actuator sounds + telemetry accessors already present.
   - Remaining: (a) build the module, (b) PIE playtest to confirm sync telemetry, (c) optional
     ambient loop asset for "ambient richness".
2. After build verifies green, run `python -m core.rehearsal --decide` for the next Loop candidate.
