# Emotional Anchor Reference — Creative Decision Table

## Overview

This is the standalone lookup table for assigning and implementing emotional anchors on every object, room, station, ship, and environment in the Chimera project. Every creative decision ties back to a specific emotion. Nothing is arbitrary.

---

## THE EMOTIONAL ANCHOR TABLE

| Emotion | Light | Material | Color | Sound | Shape | Space |
|---------|-------|----------|-------|-------|-------|-------|
| **Lonely** | Single source, high contrast, cold color temperature | Bare, worn, functional — no ornamentation | Desaturated cool greys, single warm accent | Silence with distant mechanical hum | Isolated structure, exposed framework | Large negative space surrounding subject |
| **Hope** | Single warm light in otherwise cold scene | Worn but cared for — maintained despite harsh conditions | Warm accent against cool background palette | Rising tonal quality, clear and definite | Small structure against vast environment | A single point of warmth in overwhelming void |
| **Safe** | Multiple warm sources, steady and consistent | Clean, maintained, soft surfaces | Warm saturated colors near light sources | Steady rhythm, familiar mechanical sounds | Enclosed, protected geometries | Contained, human-scale environments |
| **Danger** | Flickering red sources, harsh shadows | Scorched, damaged, sharp edges | Red accents against high contrast background | Irregular patterns, loud sudden sounds | Jagged, aggressive geometries | Tight, claustrophobic environments |
| **Awe** | Dramatic volumetric lighting with colored sources | Rich, detailed, vast scale surfaces | Deep blues with vibrant accent colors | Low rumble with harmonic overtones | Massive, overwhelming geometries | Infinite, grand environments |
| **Mystery** | Dim, indirect lighting with colored shadows | Obscured, reflective, dark surfaces | Deep purples with faint glow accents | Whispered tones, occasional sounds | Hidden forms that suggest rather than reveal | Partially revealed environments |

---

## DETAILED IMPLEMENTATION GUIDES

### EMOTION: LONELY

**Description:** Isolation, exposure, vast negative space with single point of warmth or hope.

**When to use:** Abandoned stations, empty corridors, deep-space approach sequences, solo ship interiors at night.

#### Lighting Implementation
- **Primary source:** One light only — a docking bay entrance, a single window, a beacon
- **Color temperature:** 4000K or cooler (blue-white)
- **Contrast ratio:** High — deep shadows, bright isolated highlights
- **Secondary sources:** None, or one flickering emergency light at low intensity

```python
# Example: Lonely lighting setup in UE5
light = DirectionalLight()
light.color = Color(0.7, 0.75, 0.8)  # Cool blue-white
light.intensity = 2.0
light.shadows = True
light.shadow_cast_mode = ShadowCastMode.SHADOWS_ONLY

secondary = PointLight()
secondary.color = Color(1.0, 0.4, 0.1)  # Warm amber — the hope accent
secondary.intensity = 0.3
secondary.range = 500
```

#### Material Implementation
- **Base surfaces:** Bare metal, unpainted hull plating, scuffed floors
- **Wear patterns:** Concentrated at touch points (handrails, door frames, floor paths)
- **No ornamentation:** Every surface serves a function; nothing is decorative
- **Repair patches:** Visible weld seams, bolted plates over original hull

#### Color Implementation
- **Dominant palette:** Desaturated greys (#6B7278, #8B95A1, #4A5058)
- **Accent color:** Single warm element — amber docking light (#FF8C42), red emergency beacon
- **Saturation:** Low across board (0.15-0.30 range)

#### Sound Implementation
- **Ambient layer:** Near-silence (volume -40dB or lower)
- **Mechanical presence:** Low frequency hum at 60Hz, barely audible
- **Intermittent sounds:** Distant creaks every 8-15 seconds, rhythmic beacon pulse
- **No music:** Or if used, a single sustained note with long decay

#### Shape Implementation
- **Composition:** Subject isolated in frame, surrounded by void
- **Structure:** Exposed framework visible through outer shell
- **Silhouette:** Irregular, asymmetrical — repairs and additions break the form

#### Space Implementation
- **Negative space:** 60%+ of frame is empty void or dark background
- **Scale cues:** Small human-scale elements (windows, handrails) against massive structure
- **Depth layers:** Foreground debris → midground station → background planet/stars

---

### EMOTION: HOPE

**Description:** Small point of warmth against vast cold — the feeling that someone is coming home.

**When to use:** Approaching a trading hub after long voyage, docking bay entrance lights, inhabited station exteriors at dawn.

#### Lighting Implementation
- **Primary source:** Warm light from docking bay or habitation module
- **Color temperature:** 2700K-3200K (warm amber)
- **Placement:** Off-center, asymmetric — creates tension with cold surroundings
- **Secondary sources:** None — the warmth is singular and precious

```python
# Example: Hope lighting setup in UE5
primary = PointLight()
primary.color = Color(1.0, 0.65, 0.3)  # Warm amber
primary.intensity = 3.0
primary.range = 800

environment = RectLight()
environment.color = Color(0.4, 0.45, 0.55)  # Cool ambient fill
environment.intensity = 0.5
```

#### Material Implementation
- **Condition:** Worn but cared for — cleaned where people walk, maintained despite harsh conditions
- **Markings:** Painted identification numbers, safety warnings, crew names
- **Interior surfaces:** Warmer tones than exterior — habitation warmth bleeds through

#### Color Implementation
- **Dominant palette:** Cool greys and blues (the environment)
- **Accent color:** Warm amber/orange at docking ports and windows (#FF8C42, #E8713A)
- **Contrast:** The warmth reads clearly against the cold background

#### Sound Implementation
- **Tonal quality:** Rising — a note that ascends rather than descends
- **Clarity:** Clear and definite, not muffled or distant
- **Rhythm:** Steady, predictable — someone is home and keeping time

#### Shape Implementation
- **Scale relationship:** Small structure against vast environment — but the small thing matters
- **Framing:** Warm light element framed by cold darkness
- **Composition:** The warm point draws the eye; it's the center of gravity

#### Space Implementation
- **Feeling:** A single point of warmth in overwhelming void
- **Distance:** Close enough to reach, far enough to be uncertain
- **Direction:** Implied movement toward the light — you're going home

---

### EMOTION: SAFE

**Description:** Enclosed, protected, human-scale environment with warm steady presence and familiar rhythms.

**When to use:** Market interiors, crew quarters, docking bay interiors, station common areas, habitation modules.

#### Lighting Implementation
- **Number of sources:** Multiple — no single point dominates
- **Color temperature:** 2700K-3500K (warm)
- **Steadiness:** Consistent, unchanging — no flickering, no sudden shifts
- **Coverage:** Even illumination with soft shadows

```python
# Example: Safe lighting setup in UE5
for position in warm_positions:
    light = PointLight()
    light.color = Color(1.0, 0.72, 0.45)  # Warm amber
    light.intensity = 1.5
    light.range = 600

# Soft fill to eliminate harsh shadows
fill = RectLight()
fill.color = Color(0.9, 0.85, 0.75)  # Warm white
fill.intensity = 0.8
```

#### Material Implementation
- **Condition:** Clean and maintained — regularly cleaned surfaces
- **Texture:** Soft edges, rounded corners, padded surfaces where possible
- **Markings:** Safety signs, route indicators, crew information boards

#### Color Implementation
- **Dominant palette:** Warm tones — amber, soft white, muted browns
- **Saturation:** Moderate to high near light sources, lower in shadow areas
- **Consistency:** Colors don't shift dramatically between zones

#### Sound Implementation
- **Rhythm:** Steady and familiar — the sounds of a place that works
- **Content:** Mechanical hum, distant conversation, routine activity
- **Volume:** Moderate — not silent, not loud. The sound of life.

#### Shape Implementation
- **Enclosure:** Walls, ceiling, floor — clearly defined boundaries
- **Proportion:** Human-scale ceilings (3-4 meters), wide corridors
- **Flow:** Clear sight lines, intuitive navigation

#### Space Implementation
- **Feeling:** Contained but not cramped — human scale with room to move
- **Boundaries:** Visible walls and structures that define the space clearly
- **Familiarity:** Layout feels logical, not labyrinthine

---

### EMOTION: DANGER

**Description:** Immediate threat communicated through flickering light, red accents, and claustrophobic space.

**When to use:** Pirate encounters, damaged station sequences, emergency scenarios, hostile territory approaches.

#### Lighting Implementation
- **Primary source:** Flickering red or orange — emergency lighting in crisis mode
- **Color temperature:** 1800K-2500K (deep red-orange)
- **Pattern:** Irregular flickering — not rhythmic, unpredictable
- **Shadows:** Harsh, deep, covering more area than light

```python
# Example: Danger lighting setup in UE5
primary = PointLight()
primary.color = Color(1.0, 0.2, 0.1)  # Deep red
primary.intensity = 2.0
primary.range = 700

# Flicker pattern
import random
def flicker_light(light, t):
    base_intensity = light.intensity
    flicker = base_intensity * (0.3 + 0.7 * random.uniform(0, 1))
    return max(0.1, flicker)
```

#### Material Implementation
- **Condition:** Scorched, damaged, sharp edges exposed
- **Surface:** Scorch marks, torn panels, broken conduits
- **Warning signs:** Emergency markings, hazard stripes, warning lights

#### Color Implementation
- **Dominant palette:** Red and orange accents against dark background
- **Contrast:** High — red elements pop sharply against darkness
- **Saturation:** High on reds, low everywhere else

#### Sound Implementation
- **Pattern:** Irregular — sudden loud sounds followed by silence
- **Content:** Alarms, hissing steam, cracking metal, warning klaxons
- **Volume:** Dynamic — sudden peaks, deep valleys

#### Shape Implementation
- **Geometry:** Jagged, aggressive — broken structures, exposed framework
- **Edges:** Sharp, dangerous-looking — torn metal, shattered panels
- **Composition:** Tight framing, elements pressing in from edges

#### Space Implementation
- **Feeling:** Claustrophobic — walls feel like they're closing in
- **Navigation:** Confusing, disorienting — wrong turns, blocked paths
- **Escape routes:** Visible but uncertain — is there a way out?

---

### EMOTION: AWE

**Description:** Overwhelming scale and richness that dwarfs the viewer — the feeling of standing before something ancient and vast.

**When to use:** Ancient alien structures, massive station complexes, nebula approaches, planet views from orbit, discovery sequences.

#### Lighting Implementation
- **Primary source:** Volumetric — light that fills space with atmosphere
- **Color temperature:** Variable — deep blues in shadow, vibrant accents where light hits
- **Scale:** Massive light sources — entire surfaces glow
- **Effect:** Light rays visible through atmosphere, colored volumetric fog

```python
# Example: Awe lighting setup in UE5
primary = DirectionalLight()
primary.color = Color(0.15, 0.2, 0.6)  # Deep blue
primary.intensity = 4.0

# Volumetric fog for light rays
fog = VolumeMaterial()
fog.color = Color(0.3, 0.35, 0.8)  # Blue-tinted atmosphere
fog.density = 0.02

# Accent lights — vibrant and saturated
accent = PointLight()
accent.color = Color(0.1, 0.6, 0.9)  # Vibrant cyan
accent.intensity = 5.0
```

#### Material Implementation
- **Detail:** Rich and detailed at every scale — ancient carvings, vast surfaces with texture
- **Scale:** Massive elements that dwarf human presence
- **Finish:** Impeccable or anciently weathered — either pristine or beautifully eroded

#### Color Implementation
- **Dominant palette:** Deep blues and purples as base
- **Accents:** Vibrant colors where light hits — cyan, gold, emerald
- **Contrast:** Deep shadows with brilliant highlights

#### Sound Implementation
- **Foundation:** Low rumble that you feel more than hear
- **Harmonics:** Harmonic overtones — musical, not mechanical
- **Space:** Reverberation that suggests vastness

#### Shape Implementation
- **Scale:** Massive, overwhelming geometries that dwarf the viewer
- **Complexity:** Rich detail at every scale — layers of form within form
- **Presence:** The structure dominates the frame completely

#### Space Implementation
- **Feeling:** Infinite and grand — no sense of boundaries
- **Perspective:** Multiple depth layers stretching to infinity
- **Immersion:** You're inside the experience, not looking at it

---

### EMOTION: MYSTERY

**Description:** Partially revealed — what's hidden suggests more than what's shown, inviting investigation.

**When to use:** Unexplored stations, ancient ruins, obscured facilities, signals of unknown origin, abandoned research outposts.

#### Lighting Implementation
- **Primary source:** Dim and indirect — light that reveals only part of the scene
- **Color temperature:** Variable — often colored (purple, blue-green, deep red)
- **Technique:** Light from behind objects, casting shadows that suggest hidden forms
- **Effect:** Colored shadows, obscured areas, hints of what's beyond

```python
# Example: Mystery lighting setup in UE5
primary = SpotLight()
primary.color = Color(0.4, 0.2, 0.6)  # Deep purple
primary.intensity = 1.0
primary.cone_inner = 0.7
primary.cone_outer = 1.2

# Fill from behind — reveals silhouette but hides detail
fill = PointLight()
fill.color = Color(0.2, 0.3, 0.5)  # Cool blue
fill.intensity = 0.6
```

#### Material Implementation
- **Condition:** Obscured by dust, darkness, or intentional concealment
- **Surface:** Reflective elements that catch partial light, dark matte surfaces that absorb it
- **Revelation:** Only parts of the surface visible — the rest hidden

#### Color Implementation
- **Dominant palette:** Deep purples and blues as base
- **Accents:** Faint glow — barely visible colored highlights
- **Contrast:** Low overall — most elements in shadow, few bright spots

#### Sound Implementation
- **Volume:** Whispered tones — quiet, intermittent
- **Content:** Occasional sounds that suggest activity but don't explain it
- **Direction:** Sounds come from hidden locations — you can't see the source

#### Shape Implementation
- **Revelation:** Hidden forms that suggest rather than reveal complete structure
- **Silhouette:** Partially obscured — you catch edges and hints
- **Complexity:** Layers of form where each visible layer hides what's behind it

#### Space Implementation
- **Feeling:** Partially revealed — the space tells you there's more beyond
- **Navigation:** You can see a path but not the destination
- **Invitation:** The space suggests investigation without guaranteeing reward

---

### EMOTION: SAFE (WARM HABITATION)

**Description:** Enclosed, protected, human-scale environment with warm steady presence and familiar rhythms. This is the emotional counterpoint to the void of space — a place where life persists.

**When to use:** Market interiors, crew quarters, docking bay common areas, station mess halls, habitation module corridors.

#### Lighting Implementation
- **Number of sources:** Multiple overlapping sources create even illumination
- **Color temperature:** 2700K-3500K — warm amber and soft white
- **Steadiness:** Consistent, unchanging — the sound of a place that works reliably
- **Coverage:** Even with soft shadows — no harsh contrasts

```python
# Example: Warm habitation lighting in UE5
warm_positions = [
    (0, 0, 200), (300, 0, 200), (-300, 0, 200), (0, 300, 200), (0, -300, 200)
]

for pos in warm_positions:
    light = PointLight()
    light.location = pos
    light.color = Color(1.0, 0.72, 0.45)  # Warm amber
    light.intensity = 1.5
    light.range = 600

# Soft ceiling fill to eliminate harsh shadows
ceiling_fill = RectLight()
ceiling_fill.color = Color(0.9, 0.85, 0.75)  # Warm white
ceiling_fill.intensity = 0.8
```

#### Material Implementation
- **Condition:** Clean and regularly maintained — this place is lived in
- **Texture:** Soft edges where possible, rounded corners, padded surfaces at hand height
- **Markings:** Safety signs, route indicators, crew information boards, personal touches

#### Color Implementation
- **Dominant palette:** Warm tones — amber (#D4A056), soft white (#F5E6D3), muted browns (#8B7355)
- **Saturation:** Moderate to high near light sources, lower in shadow areas
- **Consistency:** Colors don't shift dramatically between zones — this is a stable environment

#### Sound Implementation
- **Rhythm:** Steady and familiar — the sounds of a place that works reliably
- **Content:** Mechanical hum (60Hz), distant conversation through comms, routine activity
- **Volume:** Moderate — not silent, not loud. The sound of life going about its business.

#### Shape Implementation
- **Enclosure:** Walls, ceiling, floor — clearly defined boundaries that protect
- **Proportion:** Human-scale ceilings (3-4 meters), wide corridors (2+ meters)
- **Flow:** Clear sight lines, intuitive navigation — you know where to go

#### Space Implementation
- **Feeling:** Contained but not cramped — human scale with room to move comfortably
- **Boundaries:** Visible walls and structures that define the space clearly
- **Familiarity:** Layout feels logical, not labyrinthine — this is a place you could live

---

## CROSS-DOMAIN TRANSFER TABLE

| Domain Principle | Application to Game Art | Example |
|------------------|------------------------|---------|
| Architecture: sacred space through proportion | Station interior proportions that feel reverent | High ceilings, centered sight lines, focal point at far end |
| Music: tension through dissonance | Visual dissonance — conflicting geometries, unexpected colors | Sharp angles against smooth surfaces, warm element in cold scene |
| Poetry: white space as meaning | Empty void as emotional weight | Large areas of darkness surrounding small light sources |
| Sculpture: negative space defines form | What's absent shapes what's present | Station silhouette defined by missing sections, dark corridors defining lit rooms |
| Theater: lighting directs attention | Light placement guides player eye | Single warm light draws to docking bay; flickering red marks danger zone |
| Dance: weight and momentum in movement | Ship movement feels like physical mass | Acceleration feels heavy; turning feels gradual; stopping feels impossible |

---

## QUICK REFERENCE CARD

**When the Ether extracts an emotion, look up these implementation rules:**

| Emotion | Key Light | Key Material | Key Color | Key Sound |
|---------|-----------|--------------|-----------|-----------|
| Lonely | Single source, cold | Bare, worn | Desaturated cool | Silence + distant hum |
| Hope | Single warm in cold | Worn but cared for | Warm accent on cool | Rising tone, clear |
| Safe | Multiple, warm, steady | Clean, maintained | Warm saturated | Steady rhythm, familiar |
| Danger | Flickering red, harsh | Scorched, damaged | Red accents | Irregular, loud |
| Awe | Volumetric, colored | Rich, detailed, vast | Deep blues + vibrant | Low rumble, harmonic |
| Mystery | Dim, indirect, colored | Obscured, reflective | Deep purples, faint glow | Whispered, occasional |

---

## SUMMARY

Every object, every room, every station gets assigned an emotional anchor. The anchor determines which patterns apply. Two stations with different anchors feel different even if they share the same mesh. This reference table is your quick lookup — when you know the target emotion, you know exactly what lighting, material, color, sound, shape, and space should look like.