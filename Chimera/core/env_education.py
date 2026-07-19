"""env_education.py — Environmental education system.

Generates context-aware educational prompts based on terrain geology,
weather conditions, celestial positions, and time of day. No UE5
dependency — pure Python, works with existing Chimera systems.

The player encounters these as environmental observations:
- "The canyon walls show sedimentary limestone over igneous granite —
  this planet had an ocean millions of years ago."
- "Flat-bottom clouds mean stable air. You have good flying weather."
- "That constellation is Orion. You're in the northern hemisphere."

Teaches: Geology, meteorology, astronomy through environmental observation.
"""

from typing import Optional, Dict
import random

# ─── Geology prompts ───────────────────────────────────────────────────────

GEOLOGY_PROMPTS = {
    "regolith_breccia": [
        "Wind-blown debris covers the surface. Nothing stays buried here long.",
        "This regolith is young — no soil formation yet. Constant wind erosion.",
    ],
    "sedimentary_sandstone": [
        "Cross-bedding in the sandstone — ancient dune fields, now stone.",
        "Sandstone layers tilt at different angles. The wind direction changed over millennia.",
    ],
    "sedimentary_limestone": [
        "Fossil fragments in the limestone. This was once a shallow sea.",
        "Limestone dissolves in rainwater. These caves are still growing.",
        "Calcium carbonate precipitate — the remains of countless tiny marine organisms.",
    ],
    "metamorphic_schist": [
        "The foliation bands in this schist run vertical. Intense pressure from tectonic activity.",
        "Schist at this depth means the crust was compressed and heated. Ancient mountain building.",
    ],
    "igneous_granite": [
        "Large crystal grains in the granite. Slow cooling deep underground.",
        "This granite was once magma, cooling over millions of years. Erosion exposed it.",
    ],
    "igneous_basalt": [
        "Columnar jointing in the basalt. Rapid cooling of a lava flow.",
        "Basalt means volcanic activity. This entire region was built by eruptions.",
    ],
}

# ─── Weather prompts ───────────────────────────────────────────────────────

WEATHER_PROMPTS = {
    "clear": [
        "High pressure dominates. Stable air. Good for flying.",
        "No clouds at altitude. The stars will be visible tonight.",
    ],
    "windy": [
        "Wind from the east. A weather system is moving in.",
        "Gusting stronger now. Low pressure approaching.",
        "The wind carries dust from the dry basin to the west.",
    ],
    "storm": [
        "Pressure dropping fast. A storm is building.",
        "Cumulonimbus towers on the horizon. Seek shelter.",
        "Lightning in the distance. The storm will arrive within the hour.",
        "Surface visibility dropping. The dust storm is almost here.",
    ],
    "calm": [
        "Dead calm. The air is heavy. Rain coming within a day.",
        "Not a breath of wind. High humidity. Morning fog likely.",
    ],
}

# ─── Astronomy prompts ─────────────────────────────────────────────────────

ASTRONOMY_PROMPTS = {
    "constellation": [
        "That pattern of stars is a constellation — different stars, same story, every night.",
        "The stars change position through the night as the planet rotates.",
        "If you recognize this constellation, you know which hemisphere you're on.",
    ],
    "moon": [
        "The moon is [PHASE] tonight. In [N] days it will be full.",
        "The moon's phase affects the tides — and the tide affects the shoreline access.",
    ],
    "sunset": [
        "The sun is [COLOR] at this angle. More atmosphere = more red. Dust in the air shifts it further.",
        "Green flash at sunset means exceptionally clear air. Rare.",
    ],
    "night_sky": [
        "Light from those stars left them [YEARS] years ago. You're looking back in time.",
        "The Milky Way is brighter here than on Earth. No light pollution for a thousand light-years.",
    ],
}

# ─── Time-of-day context ──────────────────────────────────────────────────

TIME_PROMPTS = {
    "dawn": "First light. The temperature is rising fast without an atmosphere to trap heat.",
    "day": "The sun is high. Heat shimmer on the horizon. Minimal cloud cover.",
    "dusk": "Long shadows. The day's heat radiating back into space. Temperature dropping.",
    "night": "The surface is cooling rapidly. Stars sharp and numerous without atmospheric distortion.",
}


def geology_prompt(rock_type: str, terrain_feature: str = "canyon") -> str:
    """Generate an educational observation about the current terrain."""
    prompts = GEOLOGY_PROMPTS.get(rock_type, [f"The {rock_type} here tells a story of this planet's formation."])
    return f"[Geology] {random.choice(prompts)}"


def weather_prompt(weather_state: str) -> str:
    """Generate an educational observation about the current weather."""
    prompts = WEATHER_PROMPTS.get(weather_state, ["The weather is unremarkable. No educational signal."])
    return f"[Weather] {random.choice(prompts)}"


def astronomy_prompt(sky_feature: str, context: Optional[Dict] = None) -> str:
    """Generate an educational observation about the sky."""
    if sky_feature == "moon" and context:
        phase = context.get("moon_phase", "waxing")
        days_to_full = context.get("days_to_full", 7)
        prompt = f"The moon is {phase} tonight. In {days_to_full} days it will be full."
        return f"[Astronomy] {prompt}"
    
    prompts = ASTRONOMY_PROMPTS.get(sky_feature, ["The sky is clear. Good for navigation."])
    return f"[Astronomy] {random.choice(prompts)}"


def time_prompt(time_of_day: str) -> str:
    """Generate an observation based on time of day."""
    prompt = TIME_PROMPTS.get(time_of_day, f"It is {time_of_day}.")
    return f"[Environment] {prompt}"


def random_observation(geology_type: str, weather_state: str, time_of_day: str) -> str:
    """Generate a random environmental observation weighted by context.
    
    The player sees these periodically as they explore.
    """
    roll = random.random()
    if roll < 0.35:
        return geology_prompt(geology_type)
    elif roll < 0.60:
        return weather_prompt(weather_state)
    elif roll < 0.80:
        return astronomy_prompt("constellation")
    else:
        return time_prompt(time_of_day)


def environment_report(geology_type: str, weather_state: str, 
                       time_of_day: str, sky_feature: str = "clear") -> str:
    """Full environmental status report — like a survival scanner readout."""
    lines = []
    lines.append("=== ENVIRONMENTAL SCAN ===")
    lines.append(f"Time: {time_of_day.upper()}")
    lines.append(f"Weather: {weather_state.upper()}")
    lines.append(f"Terrain: {geology_type}")
    lines.append("")
    lines.append(random_observation(geology_type, weather_state, time_of_day))
    return "\n".join(lines)
