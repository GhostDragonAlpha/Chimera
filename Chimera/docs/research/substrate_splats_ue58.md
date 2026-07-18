# Substrate + splats in UE 5.8 — live research cache (tb-0170, fable-5, 2026-07-18)

## Substrate status (LIVE lookups, load-bearing)

- **Production-ready since UE 5.7; enabled BY DEFAULT for new projects.** Upgraded
  projects (this one: upgraded to 5.8) must enable it manually.
  Source: [UE 5.7 release notes](https://www.unrealengine.com/news/unreal-engine-5-7-is-now-available) ·
  [Substrate overview, UE 5.8 docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine) ·
  [Substrate materials, UE 5.8 docs](https://dev.epicgames.com/documentation/unreal-engine/substrate-materials-in-unreal-engine)
- **Enable**: `DefaultEngine.ini` → `[/Script/Engine.RendererSettings]`:
  `r.Substrate=1` and `r.Substrate.GBufferFormat=1`
  (GBufferFormat 1 = **Adaptive**: full material complexity, quality-first;
   0 = **Blendable**: fixed memory, 60Hz parity with the legacy path).
  This project chooses **Adaptive** — the thesis is quality-first on a 4090 dev box;
  the 60fps wall is Malcolm's to enforce later, with Blendable as the named fallback.
- **Legacy conversion**: with Substrate on, existing material graphs are auto-converted
  to Substrate slabs internally — meaning the glTF importer's generated materials become
  Substrate slabs without re-authoring. (Docs above; verified empirically in-engine
  below once screenshots land.)
- Epic ships production Substrate material packs on Fab
  ([280 automotive materials, free](https://www.unrealengine.com/news/get-over-280-production-ready-automotive-substrate-materials-for-ue-5-7-free-on-fab)) —
  candidate slab references for the matter library's built-materials family.

## The splat→engine route chosen for this rung (and why)

- **Quad-per-splat static mesh via GLB (trimesh COLOR_0 vertex colors)**, imported over
  the PROVEN `bake_to_ue5.py` MCP pathway (`manage_asset import` → `spawn_actor` →
  `BugItGo` → viewport screenshot). Chosen over:
  - **Niagara per-particle**: bridge Niagara AUTHORING is a documented dead end
    (SUCCESSOR_RUNBOOK trap: create/add/set all return success and do nothing;
    "spawn stock templates; author nothing").
  - **Third-party splat plugins**: unlit-radiance viewers (model knowledge, unverified
    live) — the whole point here is ENGINE lighting on matter, not baked radiance.
- Per-splat albedo (the mottle — the library's "average, not a surface") rides COLOR_0;
  whether UE's glTF importer wires vertex color into the generated material is verified
  EMPIRICALLY by screenshot (if flat: fallback is a hand-authored VertexColor→slab
  material, one asset, reused by every splat import).
- Dithered/stochastic opacity for soft splat edges: DEFERRED to a later rung — v1 quads
  are opaque; coverage softness is a refinement after the lighting proof stands.

## Model-knowledge items deliberately NOT asserted as fact
- Exact behavior of the 5.8 glTF importer wrt COLOR_0→material wiring (verified by
  looking at the in-engine result instead).
- Third-party splat plugin GBuffer behavior (not used; not re-verified).
