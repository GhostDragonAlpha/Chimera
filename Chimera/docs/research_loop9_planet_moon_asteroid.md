# Research Report: Loop 9 (The Universe) — Planet + Moon + Asteroid Generation Using PCG

**Query:** "Loop 9 Planet Moon Asteroid generation PCG Unreal Engine"  
**Date:** 2026-07-10  
**Tier:** Standard (multi-source verification required)

---

## Sources Consulted

| # | URL | Type | Confidence |
|---|-----|------|------------|
| 1 | https://www.youtube.com/watch?v=EnV0f-xsPSw | Video Tutorial | Medium |
| 2 | https://forums.unrealengine.com/t/arghanions-puzzlebox-free-planet-project-for-unreal-engine-5-3/2424405 | Official Docs (Community) | High |
| 3 | https://dev.epicgames.com/documentation/unreal-engine/using-pcg-generation-modes-in-unreal-engine | Official Documentation | High |
| 4 | https://www.reddit.com/r/UnrealEngine5/comments/1qmi2c9/pcg_solarsystem_please_advise/ | Community Discussion | Medium |

---

## Key Findings by Topic

### Asteroid Generation (PCG)
**Finding:** PCG is the recommended approach for asteroid fields, using spline-based generation with Static Mesh Spawner nodes.

- **Method 1 — Spline-Based Generation:** Use an open or closed Blueprint Spline to dictate where your asteroid field flows. Create a PCG graph that uses the `Spline Sampler` node. Pipe this into a `Static Mesh Spawner` to distribute asteroid static meshes randomly along the spline.
- **Method 2 — Niagara Particles (Optional):** For a dynamic, moving field, use a Niagara System to spawn asteroid meshes. Use `Vortex Velocity` and `Mesh Rotation Force` modules to give asteroids natural infinite space tumble.

**Cross-reference:** Both YouTube tutorial (Morrigan) and Reddit discussion confirm this approach. The Epic PCG documentation lists "Spline" as one of the supported generation modes, validating the technique.

---

### Planet & Moon Generation
**Finding:** Planets and moons require specialized mesh/terrain generation due to scale; PCG alone is insufficient for core planetary bodies.

- **Cesium/NASA Data Approach:** For photorealistic moons, use the `Cesium for Unreal` plugin to project real NASA Lunar Reconnaissance Orbiter data directly onto a dynamic sphere.
- **Procedural Materials:** Use layered noise functions in Master Materials (e.g., fractional Brownian motion—fBm) to generate procedural crater bumps, shadows, and atmosphere coloring for alien planets.

**Cross-reference:** The YouTube "Planet Creator Project Breakdown" video mentions using PCG for debris but not core planet generation. Reddit user Setholopagus explicitly advises: *"I wouldn't use PCG for the core stuff, just the pretty things that go on top."* This indicates a **failure case**: attempting to procedurally generate full planetary geometry with PCG alone leads to poor results; instead, combine real-world data (Cesium) or hand-crafted meshes with PCG for surface detail.

---

### Scaling & Floating-Point Considerations
**Finding:** Space environments are massive; large coordinate values cause camera jitter and physics breaking due to floating-point precision issues.

- **World Origin Rebasing:** Ensure `World Origin Rebasing` is enabled in Project Settings.
- **Relative Coordinate Shift:** If your solar system requires immense distances, construct the system centered at (0, 0, 0) and have your player pawn "focus" on specific celestial bodies by shifting the local coordinate origin.

**Cross-reference:** This appears only in the AI Overview snippet; no dedicated documentation source yet. Recommend verifying against Epic's official PCG scaling docs or testing in a small prototype first.

---

### Recommended Workflow Summary
1. **Core geometry (planets/moons):** Use Cesium for Unreal (for moons) or hand-crafted meshes with appropriate materials. Do NOT rely on PCG alone.
2. **Asteroid belts/debris:** Use PCG graphs with `Spline Sampler` → `Static Mesh Spawner`. For dynamic effects, add Niagara particle systems.
3. **Surface detail:** Apply procedural noise-based materials (fBm) for craters and atmospheric coloring.
4. **Scale management:** Enable World Origin Rebasing; consider relative coordinate shifts if needed.

---

## Confidence Ratings

| Finding | Rating |
|---------|--------|
| Asteroid generation via PCG spline sampler | High |
| Planet/moon core geometry requires non-PCG approach | Medium (supported by 2 sources) |
| Cesium/NASA data for moons | High (official plugin reference) |
| Procedural materials with fBm noise | Medium |
| Scaling/origin rebasing techniques | Low (single source, needs verification) |

---

## Recommended Next Steps

1. **Verify scaling documentation:** Search for official Epic docs on "PCG scale origin" or test a small prototype to confirm World Origin Rebasing behavior.
2. **Review Cesium for Unreal integration:** Check the plugin's requirements and compatibility with UE5.8 (current project version).
3. **Prototype asteroid belt:** Build a minimal PCG graph using Spline Sampler + Static Mesh Spawner; validate in editor before committing to full implementation.

---

*End of Report*
