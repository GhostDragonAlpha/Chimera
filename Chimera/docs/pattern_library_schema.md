# Pattern Library Schema — Graphify Integration

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

## Overview

This document defines the schema for recording creative patterns, emotional anchors, and design principles in the Graphify knowledge graph. Every pattern extracted from research should follow this structure so that future objects benefit from past understanding.

---

## PATTERN NODE STRUCTURE

### 1. Pattern Node (Core Abstraction)

Represents an extracted principle from research references.

```json
{
  "label": "Pattern:lonely_lighting",
  "type": "pattern",
  "properties": {
    "name": "Lonely Lighting",
    "category": "light_language",
    "emotional_anchor": "lonely",
    "domain": "visual",
    "confidence": 0.85,
    "description": "Single light source in cold scene creates tension through isolation and negative space",
    "source_references": [
      "NASA ISS interior photos - single illuminated panel",
      "Interstellar docking bay scene - single warm light against void",
      "ArtStation concept art 'lonely station' by [artist]"
    ],
    "sub_patterns": ["single_point_light", "cold_color_temperature", "high_contrast_shadows", "large_negative_space"]
  }
}
```

### 2. Pattern Node (Shape Language)

```json
{
  "label": "Pattern:exposed_structure",
  "type": "pattern",
  "properties": {
    "name": "Exposed Structure",
    "category": "shape_language",
    "emotional_anchor": "fragile",
    "domain": "visual",
    "confidence": 0.78,
    "description": "Structural elements visible through outer shell communicate vulnerability and functional honesty",
    "source_references": [
      "Oil rig photography - exposed support beams",
      "Abandoned factory photos - torn cladding revealing framework"
    ],
    "sub_patterns": ["visible_framework", "torn_cladding", "structural_honesty"]
  }
}
```

### 3. Pattern Node (Color Language)

```json
{
  "label": "Pattern:desaturated_cool_greys",
  "type": "pattern",
  "properties": {
    "name": "Desaturated Cool Greys",
    "category": "color_language",
    "emotional_anchor": "cold",
    "domain": "visual",
    "confidence": 0.92,
    "description": "Low saturation cool grey palette evokes isolation and temperature without direct representation",
    "source_references": [
      "NASA lunar surface photos - desaturated greys under harsh light",
      "Interstellar space scenes - cool desaturation in void"
    ],
    "sub_patterns": ["low_saturation", "cool_temperature", "grey_dominance"]
  }
}
```

### 4. Pattern Node (Texture Language)

```json
{
  "label": "Pattern:worn_functional",
  "type": "pattern",
  "properties": {
    "name": "Worn Functional",
    "category": "texture_language",
    "emotional_anchor": "lived_in",
    "domain": "visual",
    "confidence": 0.81,
    "description": "Functional wear patterns concentrated at touch points communicate habitation without neglect",
    "source_references": [
      "ISS exterior photos - scuff marks at handrail points",
      "Naval vessel photography - worn paint at high-traffic areas"
    ],
    "sub_patterns": ["touch_point_wear", "functional_scarring", "maintained_but_used"]
  }
}
```

### 5. Pattern Node (Sound Language)

```json
{
  "label": "Pattern:silence_distant_hum",
  "type": "pattern",
  "properties": {
    "name": "Silence with Distant Hum",
    "category": "sound_language",
    "emotional_anchor": "lonely",
    "domain": "audio",
    "confidence": 0.88,
    "description": "Near-silence punctuated by low mechanical hum creates isolation while maintaining presence",
    "source_references": [
      "Space station ambient recordings - HVAC hum in empty corridors",
      "NASA audio archives - silence between mechanical cycles"
    ],
    "sub_patterns": ["near_silence", "low_frequency_hum", "mechanical_presence"]
  }
}
```

---

## EMOTIONAL ANCHOR NODES

Each emotion gets a dedicated node that connects to all applicable patterns.

### Emotion: Lonely

```json
{
  "label": "Emotion:lonely",
  "type": "emotion_anchor",
  "properties": {
    "name": "Lonely",
    "description": "Isolation, exposure, vast negative space with single point of warmth or hope",
    "applies_to": ["lighting", "material", "color", "sound", "shape", "space"],
    "pattern_connections": [
      "Pattern:lonely_lighting",
      "Pattern:bare_worn_functional",
      "Pattern:desaturated_cool_greys",
      "Pattern:silence_distant_hum",
      "Pattern:isolated_exposed",
      "Pattern:large_negative_space"
    ],
    "implementation_rules": {
      "light": "Single source, high contrast, cold color temperature",
      "material": "Bare, worn, functional - no ornamentation",
      "color": "Desaturated cool greys, single warm accent",
      "sound": "Silence with distant mechanical hum",
      "shape": "Isolated structure, exposed framework",
      "space": "Large negative space surrounding subject"
    }
  }
}
```

### Emotion: Hope

```json
{
  "label": "Emotion:hope",
  "type": "emotion_anchor",
  "properties": {
    "name": "Hope",
    "description": "Small point of warmth against vast cold - the feeling that someone is coming home",
    "applies_to": ["lighting", "material", "color", "sound", "shape", "space"],
    "pattern_connections": [
      "Pattern:single_warm_light_in_cold",
      "Pattern:worn_but_cared_for",
      "Pattern:warm_accent_on_cool",
      "Pattern:rising_tone_clear",
      "Pattern:small_vs_vast",
      "Pattern:point_in_void"
    ],
    "implementation_rules": {
      "light": "Single warm light source in otherwise cold scene",
      "material": "Worn but cared for - maintained despite harsh conditions",
      "color": "Warm accent against cool background palette",
      "sound": "Rising tonal quality, clear and definite",
      "shape": "Small structure against vast environment",
      "space": "A single point of warmth in overwhelming void"
    }
  }
}
```

### Emotion: Danger

```json
{
  "label": "Emotion:danger",
  "type": "emotion_anchor",
  "properties": {
    "name": "Danger",
    "description": "Immediate threat communicated through flickering light, red accents, and claustrophobic space",
    "applies_to": ["lighting", "material", "color", "sound", "shape", "space"],
    "pattern_connections": [
      "Pattern:flickering_red_lighting",
      "Pattern:scorched_damaged",
      "Pattern:red_accent_high_contrast",
      "Pattern:irregular_loud_sound",
      "Pattern:jagged_aggressive_shape",
      "Pattern:tight_claustrophobic_space"
    ],
    "implementation_rules": {
      "light": "Flickering red sources, harsh shadows",
      "material": "Scorched, damaged, sharp edges",
      "color": "Red accents against high contrast background",
      "sound": "Irregular patterns, loud sudden sounds",
      "shape": "Jagged, aggressive geometries",
      "space": "Tight, claustrophobic environments"
    }
  }
}
```

### Emotion: Awe

```json
{
  "label": "Emotion:awe",
  "type": "emotion_anchor",
  "properties": {
    "name": "Awe",
    "description": "Overwhelming scale and richness that dwarfs the viewer - the feeling of standing before something ancient and vast",
    "applies_to": ["lighting", "material", "color", "sound", "shape", "space"],
    "pattern_connections": [
      "Pattern:dramatic_volumetric_lighting",
      "Pattern:rich_detailed_vast",
      "Pattern:deep_blues_vibrant_accents",
      "Pattern:low_rumble_harmonic",
      "Pattern:massive_overwhelming_shape",
      "Pattern:infinite_grand_space"
    ],
    "implementation_rules": {
      "light": "Dramatic volumetric lighting with colored sources",
      "material": "Rich, detailed, vast scale surfaces",
      "color": "Deep blues with vibrant accent colors",
      "sound": "Low rumble with harmonic overtones",
      "shape": "Massive, overwhelming geometries",
      "space": "Infinite, grand environments"
    }
  }
}
```

### Emotion: Mystery

```json
{
  "label": "Emotion:mystery",
  "type": "emotion_anchor",
  "properties": {
    "name": "Mystery",
    "description": "Partially revealed - what's hidden suggests more than what's shown, inviting investigation",
    "applies_to": ["lighting", "material", "color", "sound", "shape", "space"],
    "pattern_connections": [
      "Pattern:dim_indirect_colored_lighting",
      "Pattern:obscured_reflective_dark",
      "Pattern:deep_purples_faint_glow",
      "Pattern:whispered_occasional_sound",
      "Pattern:hidden_suggestive_shape",
      "Pattern:partially_revealed_space"
    ],
    "implementation_rules": {
      "light": "Dim, indirect lighting with colored shadows",
      "material": "Obscured, reflective, dark surfaces",
      "color": "Deep purples with faint glow accents",
      "sound": "Whispered tones, occasional sounds",
      "shape": "Hidden forms that suggest rather than reveal",
      "space": "Partially revealed environments"
    }
  }
}
```

### Emotion: Safe

```json
{
  "label": "Emotion:safe",
  "type": "emotion_anchor",
  "properties": {
    "name": "Safe",
    "description": "Enclosed, protected, human-scale environment with warm steady presence and familiar rhythms",
    "applies_to": ["lighting", "material", "color", "sound", "shape", "space"],
    "pattern_connections": [
      "Pattern:multiple_warm_steady_lighting",
      "Pattern:clean_maintained_soft",
      "Pattern:warm_saturated_near_light",
      "Pattern:steady_rhythm_familiar_sound",
      "Pattern:enclosed_protected_shape",
      "Pattern:contained_human_scale_space"
    ],
    "implementation_rules": {
      "light": "Multiple warm sources, steady and consistent",
      "material": "Clean, maintained, soft surfaces",
      "color": "Warm saturated colors near light sources",
      "sound": "Steady rhythm, familiar mechanical sounds",
      "shape": "Enclosed, protected geometries",
      "space": "Contained, human-scale environments"
    }
  }
}
```

---

## EVALUATION NODES

Record the results of creative evaluation against references.

```json
{
  "label": "Evaluation:orbital_hub_7_pass1",
  "type": "evaluation",
  "properties": {
    "subject": "Station_Orbital_Hub_7",
    "pass_number": 1,
    "target_emotion": ["lonely", "functional"],
    "screenshot_path": "Chimera/Screenshots/orbital_hub_pass1.png",
    "emotional_assessment": {
      "evokes": ["isolation", "cold"],
      "missing": ["warm accent light", "human-scale details"],
      "working_better_than_expected": ["modular construction reads clearly"]
    },
    "identified_gaps": [
      "Needs single warm docking light to suggest hope",
      "Missing handrails and window frames for human scale",
      "Surface too uniform - needs touch-point wear patterns"
    ],
    "next_refinement_focus": "warm_accent_lighting",
    "confidence": 0.65
  }
}
```

---

## REFINEMENT NODES

Record what was changed and what improved between passes.

```json
{
  "label": "Refinement:orbital_hub_7_pass1_to_pass2",
  "type": "refinement",
  "properties": {
    "subject": "Station_Orbital_Hub_7",
    "from_pass": 1,
    "to_pass": 2,
    "focus_area": "warm_accent_lighting",
    "changes_applied": [
      "Added single warm amber docking bay light at forward port",
      "Added window frames with interior illumination at 3 locations",
      "Applied touch-point wear pattern along primary approach corridor"
    ],
    "improvements_observed": {
      "evokes_more": ["hope", "habitation"],
      "still_missing": ["interior detail for Level 1 focal points"]
    },
    "confidence_delta": 0.15,
    "new_confidence": 0.80
  }
}
```

---

## PATTERN LIBRARY QUERY API

### Query by Emotion

Find all patterns that apply to a specific emotion:

```
GET /patterns?emotion=lonely
Returns: Pattern:lonely_lighting, Pattern:bare_worn_functional, Pattern:desaturated_cool_greys, etc.
```

### Query by Domain

Find all patterns in a specific sensory domain:

```
GET /patterns?domain=audio
Returns: Pattern:silence_distant_hum, Pattern:low_frequency_hum, etc.
```

### Query by Category

Find all patterns of a specific language type:

```
GET /patterns?category=light_language
Returns: All lighting-related patterns with their emotional anchors
```

### Find Sub-Patterns

Given a pattern, find its connected sub-patterns:

```
GET /patterns/sub_patterns?label=Pattern:lonely_lighting
Returns: single_point_light, cold_color_temperature, high_contrast_shadows, large_negative_space
```

---

## RECORDING WORKFLOW

After every research cycle, follow this recording process:

1. **Create Pattern Nodes** for each extracted principle (use Graphify `write_to_file` or knowledge graph mutation)
2. **Create Emotion Anchor Nodes** if new emotions are discovered
3. **Record Evaluation Nodes** after each creative pass
4. **Record Refinement Nodes** documenting what changed and why
5. **Update Confidence Scores** as patterns are validated across multiple projects

---

## PATTERN CATEGORIES REFERENCE

| Category | Domain | Examples |
|----------|--------|----------|
| shape_language | visual | exposed_structure, modular_construction, irregular_damage |
| color_language | visual | desaturated_cool_greys, warm_accent_on_cool, deep_purples |
| light_language | visual | single_point_light, flickering_red, volumetric_colored |
| texture_language | visual | worn_functional, scorched_damaged, smooth_new |
| sound_language | audio | silence_distant_hum, irregular_loud, steady_rhythm |
| scale_language | spatial | human_scale_cues, massive_overwhelming, infinite_grand |
| composition_language | visual | station_midground_void_surrounding, partial_reveal |

---

## SUMMARY

This schema ensures every pattern extracted from research is permanently recorded in the knowledge graph. Future creative tasks can query these patterns by emotion, domain, or category. The AI's understanding of "lonely" deepens with every cycle because each new evaluation and refinement enriches the existing pattern library rather than starting fresh.
