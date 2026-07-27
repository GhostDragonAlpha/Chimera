# -*- coding: utf-8 -*-
"""env_education.py - Environmental education system.

Generates context-aware educational prompts based on terrain geology,
weather conditions, celestial positions, and time of day.

Teaches: Geology, meteorology, astronomy through environmental observation.
"""

import random
from typing import Optional, Dict

from . import cloud_education
from . import cloud_weather

# --- Geology prompts ---

GEOLOGY_PROMPTS = {
    "regolith_breccia": [
        "Wind-blown debris covers the surface. Nothing stays buried here long.",
        "This regolith is young - no soil formation yet. Constant wind erosion.",
    ],
    "sedimentary_sandstone": [
        "Cross-bedding in the sandstone - ancient dune fields, now stone.",
        "The sandstone layers tilt at different angles. The wind direction shifted over centuries.",
        "Ripple marks preserved in the stone. Ancient shoreline.",
    ],
    "sedimentary_limestone": [
        "Fossil fragments in the limestone. This was once a shallow sea.",
        "Limestone dissolves in rainwater. These caves are still growing.",
        "Calcium carbonate precipitate - the remains of tiny marine organisms.",
    ],
    "metamorphic_schist": [
        "The foliation bands in this schist run vertical. Intense pressure from tectonic activity.",
        "Schist at this depth means the crust was compressed and heated. Ancient mountain building.",
    ],
    "igneous_granite": [
        "Large crystal grains in the granite. Slow cooling deep underground.",
        "This granite was once magma, cooling over millions of years. Erosion exposed it.",
        "Granite weathers into rounded shapes. Spheroidal weathering - water seeps along joints.",
    ],
    "igneous_basalt": [
        "Columnar jointing in the basalt. Rapid cooling of a lava flow.",
        "Basalt means volcanic activity. This region was built by eruptions.",
    ],
}

# --- Cloud type education sub-feature ---

def cloud_observation(cloud_type_id: str) -> str:
    """Educational observation about a specific cloud type.
    
    Sub-feature of Demo_Volumetric_Clouds: Teaches real meteorology
    through interactive cloud type identification.
    
    Cloud types: cumulus (fair weather), stratus (overcast),
    cirrus (changing), nimbostratus (rain), cumulonimbus (storm).
    """
    return cloud_education.cloud_type_observation(cloud_type_id)


def weather_prediction_from_cloud(cloud_type_id: str) -> str:
    """Predict weather 5-10 minutes ahead from cloud type.
    
    Education: Players learn to predict storms, plan flights,
    and seek shelter before bad weather arrives.
    """
    weather = cloud_weather.WeatherStateMachine()
    weather.set_cloud_type(cloud_type_id)
    weather.tick(1.0)
    return weather.get_prediction_text()


def shadow_educational_note(shadow_type: str) -> str:
    """Educational note about cloud shadow meaning.
    
    Education: moving cloud shadows = wind,
    sudden darkening = thick cloud overhead,
    shadow softness = cloud altitude.
    """
    return cloud_education.shadow_observation(shadow_type)


# --- Weather prompts ---

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

# --- Astronomy prompts ---

ASTRONOMY_PROMPTS = {
    "constellation": [
        "That pattern of stars is a constellation - same stars, every night.",
        "The stars change position through the night as the planet rotates.",
        "If you recognize this constellation, you know which hemisphere you are on.",
    ],
    "moon": [
        "The moon is {phase} tonight. In {days} days it will be full.",
        "The moon phase affects the tides and the shoreline access.",
    ],
    "sunset": [
        "The sun is red at this angle. More atmosphere = more red.",
        "Green flash at sunset means exceptionally clear air. Rare.",
    ],
    "night_sky": [
        "Light from those stars left them years ago. You are looking back in time.",
        "The Milky Way is brighter here than on Earth. No light pollution.",
    ],
}

ASTRONOMY_CONSTELLATIONS = {
    "orion": "Three stars in a row - Orion's belt. Visible from most of the planet.",
    "ursa_major": "The Big Dipper. Points to the North Star.",
    "crux": "The Southern Cross. Only visible in the southern hemisphere.",
    "scorpius": "Scorpius - shaped like its namesake. Visible in summer months.",
}

# --- Time prompts ---

TIME_PROMPTS = {
    "dawn": "First light. The temperature rises fast without an atmosphere.",
    "day": "The sun is high. Heat shimmer on the horizon.",
    "dusk": "Long shadows. The day's heat radiating back into space.",
    "night": "Surface cooling rapidly. Stars sharp without atmospheric distortion.",
}


def geology_prompt(rock_type: str, terrain_feature: str = "canyon") -> str:
    """Educational observation about the current terrain."""
    prompts = GEOLOGY_PROMPTS.get(rock_type, [])
    if not prompts:
        return f"[Geology] The {rock_type} here tells a story of this planet's formation."
    return f"[Geology] {random.choice(prompts)}"


def deep_geology_observation(rock_type: str) -> str:
    """Deeper geology observation for close examination."""
    extras = {
        "sedimentary_sandstone": [
            "The sandstone has cross-bedding at 30 degrees. Wind direction was consistent for centuries.",
        ],
        "igneous_granite": [
            "Feldspar crystals in this granite are 5mm. Cooling took approximately 10,000 years.",
        ],
        "igneous_basalt": [
            "The basalt columns are hexagonal. Typical of slow, uniform cooling.",
        ],
    }
    obs = extras.get(rock_type, [])
    if obs and random.random() < 0.3:
        return f"[Geology Detail] {random.choice(obs)}"
    return geology_prompt(rock_type)


def weather_prompt(weather_state: str) -> str:
    """Educational observation about current weather."""
    prompts = WEATHER_PROMPTS.get(weather_state, [])
    if not prompts:
        return "[Weather] The weather is unremarkable."
    return f"[Weather] {random.choice(prompts)}"


def astronomy_prompt(sky_feature: str, context: Optional[Dict] = None) -> str:
    """Educational observation about the sky."""
    if sky_feature == "moon" and context:
        phase = context.get("moon_phase", "waxing")
        days = context.get("days_to_full", 7)
        return f"[Astronomy] The moon is {phase} tonight. In {days} days it will be full."
    prompts = ASTRONOMY_PROMPTS.get(sky_feature, [])
    if prompts:
        return f"[Astronomy] {random.choice(prompts)}"
    return "[Astronomy] The sky is clear. Good for navigation."


def constellation_observation(constellation: str = None) -> str:
    """Observation about a specific constellation."""
    if constellation and constellation in ASTRONOMY_CONSTELLATIONS:
        return f"[Astronomy] {ASTRONOMY_CONSTELLATIONS[constellation]}"
    return f"[Astronomy] {random.choice(ASTRONOMY_PROMPTS['constellation'])}"


def time_prompt(time_of_day: str) -> str:
    """Observation based on time of day."""
    prompt = TIME_PROMPTS.get(time_of_day, f"It is {time_of_day}.")
    return f"[Environment] {prompt}"


def random_observation(geology_type: str, weather_state: str, time_of_day: str) -> str:
    """Random environmental observation weighted by context."""
    roll = random.random()
    if roll < 0.35:
        return geology_prompt(geology_type)
    elif roll < 0.60:
        return weather_prompt(weather_state)
    elif roll < 0.80:
        return constellation_observation()
    else:
        return time_prompt(time_of_day)


def environment_report(geology_type: str, weather_state: str,
                       time_of_day: str, sky_feature: str = "clear") -> str:
    """Full environmental status report."""
    lines = [
        "=== ENVIRONMENTAL SCAN ===",
        f"Time: {time_of_day.upper()}",
        f"Weather: {weather_state.upper()}",
        f"Terrain: {geology_type}",
        "",
        random_observation(geology_type, weather_state, time_of_day),
    ]
    return "\n".join(lines)
