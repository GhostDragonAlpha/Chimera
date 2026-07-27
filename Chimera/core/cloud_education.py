# -*- coding: utf-8 -*-
"""cloud_education.py - Cloud type educational system.

Sub-feature of Demo_Volumetric_Clouds: Teach meteorology through interactive
cloud type identification. Teaches real science through gameplay.

Loaded from data-driven JSON spec for moddability.
"""

import json, os, random
from pathlib import Path
from typing import Optional, Dict

SPEC_PATH = Path(__file__).parents[2] / "worker_bridge" / "specs" / "cloud_types_educational.json"

# --- Load spec ---

_spec_cache = None

def _load_spec() -> dict:
    global _spec_cache
    if _spec_cache is None:
        with open(SPEC_PATH, "r", encoding="utf-8") as f:
            _spec_cache = json.load(f)
    return _spec_cache

def reload_spec():
    """Force reload from disk. Useful for modding support."""
    global _spec_cache
    _spec_cache = None
    return _load_spec()


# --- Cloud type data access ---

def get_all_cloud_types() -> list:
    """Return all cloud type definitions."""
    return _load_spec()["cloud_types"]

def get_cloud_type(type_id: str) -> Optional[dict]:
    """Get a single cloud type by its string id (e.g. 'cumulus', 'nimbostratus')."""
    for ct in _load_spec()["cloud_types"]:
        if ct["id"] == type_id:
            return ct
    return None


# --- Educational observations ---

CLOUD_OBSERVATIONS = {
    "cumulus": [
        "Fluffy white clouds with flat bottoms and rounded tops. Fair weather.",
        "Flat-bottom clouds = stable air. These cumulus won't bring storms — yet.",
        "Cumulus clouds mark thermals. Good soaring conditions for birds and gliders.",
        "If cumulus grow tall and darken, instability is building. Watch for storms.",
    ],
    "stratus": [
        "A uniform gray blanket covers the sky. Featureless and low — this is stratus.",
        "Stratus means stable overcast. Light drizzle possible, but no heavy rain.",
        "The sun is completely diffused through the stratus layer. No shadows visible.",
    ],
    "cirrus": [
        "Wispy, feathery streaks high in the sky. Ice crystals — cirrus clouds.",
        "Cirrus means a weather front is approaching within 24-48 hours. Enjoy the fair weather while it lasts.",
        "High cirrus moving fast = a strong jet stream aloft. Weather change coming.",
    ],
    "nimbostratus": [
        "Thick, dark gray clouds covering everything. Rain curtains visible beneath — nimbostratus.",
        "Nimbostratus means prolonged, steady precipitation. This rain will last for hours.",
        "The cloud layer is thick enough to block all sunlight. Near-darkness at midday.",
    ],
    "cumulonimbus": [
        "Towering thunderhead with a flat anvil top. Cumulonimbus — seek shelter NOW.",
        "The anvil shape means the storm has reached the stratosphere. Severe weather is imminent.",
        "Lightning, hail, and dangerous wind gusts. Do not fly. Do not stay on high ground.",
        "Cumulonimbus development means the atmosphere is violently unstable. Take cover.",
    ],
}

def cloud_type_observation(type_id: str) -> str:
    """Educational observation about a specific cloud type."""
    prompts = CLOUD_OBSERVATIONS.get(type_id, [])
    if not prompts:
        ct = get_cloud_type(type_id)
        if ct:
            return f"[Meteorology] {ct['display_name']}: {ct['educational_fact']}"
        return f"[Meteorology] Unrecognized cloud formation."
    return f"[Meteorology] {random.choice(prompts)}"


def identify_cloud(description: str) -> Optional[str]:
    """Given a player description of what they see, identify the closest cloud type.
    
    Returns the type_id string or None if no match.
    """
    desc_lower = description.lower()
    type_scores = {}
    
    for ct in _load_spec()["cloud_types"]:
        score = 0
        cues = ct.get("visual_cues", "").lower()
        # Check for keyword matches
        keywords = cues.replace(",", "").split()
        for kw in keywords:
            if kw.lower() in desc_lower:
                score += 1
        # Bonus for type name match
        if ct["display_name"].lower() in desc_lower or ct["id"].lower() in desc_lower:
            score += 3
        type_scores[ct["id"]] = score
    
    best = max(type_scores, key=type_scores.get)
    return best if type_scores[best] > 0 else None


# --- Weather state ---

def get_weather_state(state_id: str) -> Optional[dict]:
    """Get weather state definition by id (e.g. 'clear', 'storm')."""
    return _load_spec()["weather_states"].get(state_id)


def get_all_weather_states() -> dict:
    """Return all weather states."""
    return _load_spec()["weather_states"]


def weather_state_observation(state_id: str) -> str:
    """Educational observation about the current weather state."""
    ws = get_weather_state(state_id)
    if ws:
        return f"[Meteorology] {ws['educational_text']}"
    return "[Meteorology] The weather is unremarkable today."


def weather_survival_advice(state_id: str) -> str:
    """Practical survival advice for the current weather state."""
    ws = get_weather_state(state_id)
    if ws:
        return ws["survival_advice"]
    return "Conditions are normal."


# --- Transition prediction ---

def predict_weather_change(current_state: str) -> Optional[dict]:
    """Given current weather, predict the most likely next state.
    
    Returns dict with 'to' state and 'duration_minutes' or None.
    """
    spec = _load_spec()
    for rule in spec.get("weather_transition_rules", []):
        if rule["from"] == current_state:
            # Return the first matching transition
            return {
                "from": rule["from"],
                "to": rule["to"],
                "trigger": rule.get("trigger", "natural progression"),
                "estimated_minutes": rule.get("duration_minutes", 30),
            }
    return None


def weather_trend_description(current_state: str) -> str:
    """Describe the likely weather trend to the player."""
    pred = predict_weather_change(current_state)
    if pred is None:
        ws = get_weather_state(current_state)
        if ws:
            return f"[Meteorology] {ws['display']} conditions are stable for now."
        return "[Meteorology] No clear trend."
    
    target = get_weather_state(pred["to"])
    target_name = target["display"] if target else pred["to"]
    
    return (
        f"[Meteorology] Trend: {pred['from']} -> {pred['to']} "
        f"({pred['trigger']}, ~{pred['estimated_minutes']} min). "
        f"Prepare for {target_name.lower()}."
    )


# --- Cloud-shadow educational observations ---

SHADOW_OBSERVATIONS = {
    "fast_movement": "Cloud shadows moving fast means strong winds aloft. Weather is changing.",
    "sudden_darkening": "A thick cloud bank just passed overhead. Expect precipitation soon.",
    "sharp_edges": "Sharp-edged shadows = low clouds. Storm clouds are close to the ground.",
    "soft_edges": "Soft, blurry shadows = high clouds. Fair weather for now.",
    "no_shadows": "No cloud shadows visible. The sky is uniformly overcast (stratus).",
}

def shadow_observation(shadow_type: str) -> str:
    """Educational observation about cloud shadow behavior."""
    text = SHADOW_OBSERVATIONS.get(shadow_type)
    if text:
        return f"[Meteorology] {text}"
    return "[Meteorology] Cloud shadows are normal."


# --- Full sky report ---

def sky_report(cloud_type_id: Optional[str] = None,
               weather_state: Optional[str] = None,
               include_shadow: bool = False) -> str:
    """Full meteorology sky report combining cloud type, weather, and shadows."""
    spec = _load_spec()
    lines = ["=== SKY REPORT ==="]
    
    if cloud_type_id:
        ct = get_cloud_type(cloud_type_id)
        if ct:
            lines.append(f"Cloud Type: {ct['display_name']} ({ct['altitude']})")
            lines.append(f"  {ct['educational_fact']}")
            lines.append(f"  Action: {ct['player_action']}")
    
    if weather_state:
        ws = get_weather_state(weather_state)
        if ws:
            lines.append(f"Weather: {ws['display']}")
            lines.append(f"  {ws['educational_text']}")
    
    if include_shadow:
        if cloud_type_id:
            ct = get_cloud_type(cloud_type_id)
            if ct:
                lines.append(f"Shadows: {ct['shadow_behavior']}")
    
    return "\n".join(lines)
