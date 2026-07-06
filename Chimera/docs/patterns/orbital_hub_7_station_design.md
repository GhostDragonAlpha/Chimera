# Pattern: orbital_hub_7_station_design

## Subject
Station_Orbital_Hub_7 — Neutral Trading Hub at location (0, 0, 0)

## Source
Creative Research Phase 0 — Orbital_Hub_7 lighting and material patterns extracted from ISS/space station references.

## Parameters

### Structure
| Parameter | Value | Reference |
|-----------|-------|-----------|
| Module count | 6 | ISS modular construction |
| Module radius | 2.25m (4.5m diameter) | ISS standard module size |
| Module length | 3.5m per segment | ISS module proportions |
| Arrangement | Linear truss | ISS US Orbital Segment |

### Appearance
| Parameter | Value | Reference |
|-----------|-------|-----------|
| Hull color (RGB) | [0.72, 0.73, 0.75] | ISS module exterior — neutral silver-grey |
| Roughness | 0.45 | Worn but maintained |
| Metallic | 0.65 | Aluminum alloy appearance |

### Lighting
| Parameter | Value | Reference |
|-----------|-------|-----------|
| Light type | PointLight | ISS interior panels |
| Color temperature | 4500K (neutral white) | ISS functional lighting standard |
| RGB color | [0.92, 0.93, 0.95] | Neutral white equivalent |
| Intensity | 800 lumens per light | Functional visibility threshold |
| Placement | Ceiling center + 4 wall positions per module | ISS panel distribution pattern |
| Shadow quality | Soft via LightMass | Diffused station lighting |

### Wear Details
- Panel seam lines along module boundaries
- Handrail placements along corridor walls
- Cable conduit runs at module interfaces
- Worn grip tape on floor paths between modules
- Faded panel labels and identification markings

## Per-Station Variations

| Station | Modules | Radius | Color Temp | Intensity | Hull Tone | Roughness | Metallic |
|---------|---------|--------|-----------|-----------|-----------|-----------|----------|
| Orbital_Hub_7 | 6 | 2.25m | 4500K (neutral) | 800 | Silver-grey [0.72, 0.73, 0.75] | 0.45 | 0.65 |
| Ares_Market_Central | 8 | 2.5m | 3500K (warm) | 1000 | Warm grey [0.78, 0.75, 0.70] | 0.35 | 0.55 |
| Shadow_Reef | 4 | 1.8m | 2700K (orange emergency) | 300 | Dark weathered [0.35, 0.36, 0.38] | 0.75 | 0.40 |

## Files
- `Source/Chimera/ProceduralGenerated/Stations/StationActor.h` — StationActor class definition
- `Source/Chimera/ProceduralGenerated/Stations/StationActor.cpp` — Implementation with procedural hull, lighting, materials
- `Source/Chimera/ProceduralGenerated/GameMode/DeepSpaceTraderGameMode.cpp` — Updated spawn calls with station-specific parameters

## DNA Graph Records
- Mutation: mutation_3450aa99 (StationActor class creation)
- Template: template_194712c7 (orbital_hub_7_station_design)
- Pattern: pattern_3e53261a (orbital_hub_7_lighting)
- Pattern: pattern_e2e7d3fd (orbital_hub_7_hull_material)
- Pattern: pattern_d3e03a8f (orbital_hub_7_structure)
