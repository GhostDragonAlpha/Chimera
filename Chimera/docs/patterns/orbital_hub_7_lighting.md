# Pattern: orbital_hub_7_lighting

## Subject
Orbital_Hub_7 neutral trading hub interior lighting — functional, worn but maintained

## Source
Creative Research Phase 0 — Orbital_Hub_7 lighting patterns extracted from ISS references via LM Studio image analysis.

## Reference Images Analyzed by LM Studio

### Ref 1: NASA JSC Lighting (nasa_lighting.png)
- Mixed environments with pink/magenta grow lights in Harmony Node 2
- Blue accent lighting in other areas
- Neutral white lab lighting on equipment panels
- Bright white backgrounds from screens/panels

### Ref 2: Guardian ISS Gallery - Cupola View (guardian_iss_gallery.png)
- Primary light: Natural sunlight through large windows (cool daylight, bright white/blueish)
- Secondary: Computer monitors at bottom (green/blue data screens)
- No active overhead artificial lights visible in this shot
- Cool/neutral color temperature overall
- Interior walls are cool blue-grey

### Ref 3: Space.com LED Article - SSLA Fixture (space_com_iss_led.png)
- One primary rectangular LED fixture mounted horizontally on module wall/ceiling
- Neutral to cool white light, high intensity
- Bright illumination of surrounding white padded surfaces
- No colored accent lights visible in this specific image

## Extracted Parameters

### Primary Overhead Lights (Functional Areas)
| Parameter | Value | Reference |
|-----------|-------|-----------|
| Light type | PointLight / RectAreaLight | ISS SSLA ceiling fixtures |
| Color temperature | 4500K neutral white | Space.com LED article analysis |
| RGB color | [0.92, 0.93, 0.95] (R=234, G=237, B=242) | Neutral cool white from LM Studio |
| Intensity | 800 lumens / UE intensity 5000 | Functional visibility threshold |
| Placement | Ceiling-mounted, horizontal orientation | ISS SSLA fixture pattern |
| Shadow quality | Soft via LightMass | Diffused station lighting |

### Colored Accent Lights (Specific Zones)
| Zone | Color | RGB | Intensity | Reference |
|------|-------|-----|-----------|-----------|
| Grow room / Veg production | Pink/Magenta | [1.0, 0.39, 0.78] (R=255, G=100, B=200) | 400 | NASA Harmony Node 2 SSLA |
| Corridor accent | Blue | [0.196, 0.392, 1.0] (R=50, G=100, B=255) | 300 | NASA middle photo blue light source |

### Lighting Distribution Pattern
- Primary overhead lights spaced every ~5m along module length
- Wall-mounted accent lights at 4 positions around each module circumference
- Even distribution for functional visibility in work areas
- Dimmer colored accents in specific zones (grow rooms, corridors)

## Files Modified
- `Source/Chimera/ProceduralGenerated/Stations/StationActor.h` — StationActor class definition
- `Source/Chimera/ProceduralGenerated/Stations/StationActor.cpp` — Implementation with lighting installation
- `Source/Chimera/ProceduralGenerated/GameMode/DeepSpaceTraderGameMode.cpp` — Updated spawn calls

## DNA Graph Records
- Mutation: station_mutation (AStationActor class creation)
- Template: orbital_hub_7_station_design
- Pattern: orbital_hub_7_lighting (this entry)
- Pattern: orbital_hub_7_hull_material
- Pattern: orbital_hub_7_structure
