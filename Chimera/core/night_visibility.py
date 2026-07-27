# -*- coding: utf-8 -*-
"""night_visibility.py — Night visibility and darkness gameplay (Night_Visibility_Gameplay spec).

GRAPH-SPECIFIED DESIGN (Night_Visibility_Gameplay, 26 Qs):
- Night = directional light below horizon / below brightness threshold.
- Educational observations change at night: stars, condensation, cold-related geology.
- Proximity-triggered observations check time-of-day before showing content.
- Starlight provides ambient silhouette visibility (no player light source in v1).
- Night-specific educational content requires temperature data from Temperature_Time_System.
- Darkness is not a hazard — it is a different classroom.
- UE5 exposure compensation handles visual darkness naturally.
"""

import math
from typing import Optional, Dict, List

# ────────────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────────────

# Visibility levels
VISIBILITY_NONE = 0.0      # pitch black
VISIBILITY_SILHOUETTE = 0.25   # can see large terrain shapes
VISIBILITY_LOW = 0.50      # can see nearby objects but no color
VISIBILITY_MODERATE = 0.75 # can see some detail
VISIBILITY_FULL = 1.0      # full daylight visibility

# Night state thresholds (normalized time)
NIGHT_START_TWILIGHT = 0.78   # civil twilight begins
NIGHT_START = 0.82            # nautical twilight
NIGHT_DARK = 0.85             # full night
NIGHT_DEEP = 0.90             # deepest darkness (pre-dawn)
DAWN_TWILIGHT = 0.22          # dawn civil twilight
DAWN_START = 0.25             # sunrise

# UE5 exposure-related
STARLIGHT_LUX = 0.002        # approximate lux from starlight on clear night
MOONLIGHT_LUX = 0.1          # approximate full moon lux (not implemented in v1)
DAYLIGHT_LUX = 10000.0       # approximate desert noon lux

# ────────────────────────────────────────────────────────────────────────────
# Night State
# ────────────────────────────────────────────────────────────────────────────

class NightState:
    """Determines current night/visibility state from shared celestial data.
    
    Consumes:
    - normalized_time from CelestialClock
    - sun_elevation from CelestialClock
    - temperature from TemperatureCurve (for condensation/thermal observations)
    """
    
    def __init__(self):
        self._last_visibility: float = VISIBILITY_FULL
        self._night_duration: float = 0.0  # accumulated night time (for tracking)
    
    # ── Core queries ────────────────────────────────────────────────────
    
    @staticmethod
    def is_night(sun_elevation: float) -> bool:
        """True when the sun is below the horizon."""
        return sun_elevation < 0.0
    
    @staticmethod
    def visibility_level(normalized_time: float) -> float:
        """Ambient visibility [0.0, 1.0] based on time of day.
        
        0.0 = pitch black (deep night)
        1.0 = full daylight visibility
        
        Models a smooth curve through:
        - Full day: 1.0
        - Twilight: smooth ramp 1.0 → 0.2
        - Night: 0.2 (starlight silhouette visibility)
        - Deep night: 0.0-0.1 (very dark)
        """
        t = normalized_time
        
        # Daytime: full visibility
        if NIGHT_START_TWILIGHT <= t <= 1.0 or t <= DAWN_TWILIGHT:
            # Actually check if we're in the day portion
            if (t >= 0.25 and t <= 0.75):
                return VISIBILITY_FULL
        
        # Dawn transition: 0.2 → 1.0
        if DAWN_TWILIGHT <= t < 0.25:
            progress = (t - DAWN_TWILIGHT) / (0.25 - DAWN_TWILIGHT)
            return 0.2 + 0.8 * (progress ** 2)  # ease-in
        
        # Dusk transition: 1.0 → 0.2
        if NIGHT_START_TWILIGHT <= t < NIGHT_DARK:
            progress = (t - NIGHT_START_TWILIGHT) / (NIGHT_DARK - NIGHT_START_TWILIGHT)
            return 1.0 - 0.8 * (progress ** 2)  # ease-out
        
        # Night: starlight silhouette visibility
        if t > NIGHT_DARK or t < DAWN_TWILIGHT:
            return VISIBILITY_SILHOUETTE
        
        return VISIBILITY_LOW
    
    @staticmethod
    def can_see_detail(normalized_time: float) -> bool:
        """True if visibility is high enough for detail observation."""
        return NightState.visibility_level(normalized_time) >= VISIBILITY_MODERATE
    
    @staticmethod
    def can_distinguish_colors(normalized_time: float) -> bool:
        """True if visibility is high enough for color discrimination."""
        return NightState.visibility_level(normalized_time) >= VISIBILITY_FULL
    
    @staticmethod
    def silhouette_only(normalized_time: float) -> bool:
        """True if only silhouettes are visible (night with starlight)."""
        vis = NightState.visibility_level(normalized_time)
        return VISIBILITY_SILHOUETTE <= vis < VISIBILITY_LOW
    
    # ── Night progression ───────────────────────────────────────────────
    
    @staticmethod
    def night_phase(normalized_time: float) -> str:
        """Descriptive night phase label."""
        t = normalized_time
        if 0.25 <= t <= 0.75:
            return "day"
        if 0.75 < t < 0.78:
            return "sunset"
        if 0.78 <= t < 0.82:
            return "civil_twilight"
        if 0.82 <= t < 0.85:
            return "nautical_twilight"
        if 0.85 <= t < 0.90:
            return "night"
        if t >= 0.90 or t < 0.05:
            return "deep_night"
        if 0.05 <= t < 0.15:
            return "pre_dawn"
        if 0.15 <= t < 0.22:
            return "astronomical_twilight"
        if 0.22 <= t < 0.25:
            return "dawn"
        return "day"
    
    # ── Tracking ────────────────────────────────────────────────────────
    
    def update(self, normalized_time: float, delta_seconds: float):
        """Update night tracking. Call every frame."""
        if self.is_night(self._sun_elevation_from_time(normalized_time)):
            self._night_duration += delta_seconds
        self._last_visibility = self.visibility_level(normalized_time)
    
    @staticmethod
    def _sun_elevation_from_time(normalized_time: float) -> float:
        """Approximate sun elevation from time (mirrors CelestialClock)."""
        sin_val = math.sin(2.0 * math.pi * normalized_time - math.pi / 2.0)
        return -15.0 + 90.0 * (sin_val + 1.0) / 2.0
    
    # ── Serialization ───────────────────────────────────────────────────
    
    def to_dict(self, normalized_time: float) -> dict:
        return {
            "is_night": self.is_night(self._sun_elevation_from_time(normalized_time)),
            "visibility": self.visibility_level(normalized_time),
            "night_phase": self.night_phase(normalized_time),
            "can_see_detail": self.can_see_detail(normalized_time),
            "silhouette_only": self.silhouette_only(normalized_time),
            "night_duration_hours": self._night_duration / 3600.0,
        }


# ────────────────────────────────────────────────────────────────────────────
# Night-Specific Educational Observations
# ────────────────────────────────────────────────────────────────────────────

NIGHT_OBSERVATIONS: Dict[str, List[str]] = {
    "stars": [
        "The stars are brilliant tonight. No light pollution means the Milky Way casts a faint shadow.",
        "Constellations maintain their positions relative to the terrain. The sky is a fixed map.",
        "Star color reveals temperature: blue stars are hotter than our sun, red stars are cooler.",
        "The stars appear to move as the planet rotates. A long exposure would show star trails.",
    ],
    "condensation": [
        "The temperature drop has reached the dew point. Water condenses on every cool surface.",
        "Condensation on the canyon walls — the rock is colder than the air, so moisture collects.",
        "Morning dew will evaporate within an hour of sunrise. The canyon floor will look untouched.",
    ],
    "cold_geology": [
        "The rocks are contracting audibly — a faint creaking as they cool. Thermal stress in reverse.",
        "Cracks in the canyon floor widen at night as the rock contracts. This is freeze-thaw weathering in action.",
        "Without the sun's heat, the canyon is quiet. But the geology is still active — cooling is as dynamic as heating.",
    ],
    "darkness": [
        "Human eyes cannot distinguish colors in starlight. The canyon is a world of silhouettes.",
        "Without artificial light, navigation relies on terrain memory and the stars.",
        "The darkness changes what you can observe but not what is here. The geology does not sleep.",
    ],
    "dawn": [
        "First light reveals frost on every surface. The night's cooling is visible as ice.",
        "As the sun rises, the frost sublimates directly into vapor. The canyon smokes.",
        "Dawn is the coldest moment. The temperature curve has reached its minimum.",
    ],
}


def night_observation(sun_elevation: float, temp_c: float,
                      phase: str, context: Optional[Dict[str, bool]] = None) -> str:
    """Generate an educational observation specific to night conditions.
    
    Args:
        sun_elevation: Sun elevation in degrees (from CelestialClock).
        temp_c: Current temperature in Celsius (from TemperatureCurve).
        phase: Night phase string (from NightState.night_phase).
        context: Dict of boolean context flags.
        
    Returns:
        Educational observation string.
    """
    if context is None:
        context = {}
    
    import random
    
    # Not night: no night observation
    if sun_elevation >= 0.0:
        return ""
    
    # Dawn observations
    if phase in ("dawn", "astronomical_twilight"):
        return f"[Night] {random.choice(NIGHT_OBSERVATIONS['dawn'])}"
    
    # Cold night: low temperature triggers condensation + cold geology
    if temp_c < 5.0:
        bucket = random.choice(["stars", "condensation", "cold_geology", "darkness"])
        return f"[Night] {random.choice(NIGHT_OBSERVATIONS[bucket])}"
    
    # Mild night: primarily stars + darkness
    if phase in ("deep_night", "night", "pre_dawn"):
        bucket = random.choice(["stars", "darkness"])
        return f"[Night] {random.choice(NIGHT_OBSERVATIONS[bucket])}"
    
    # Twilight
    if phase in ("civil_twilight", "nautical_twilight"):
        bucket = random.choice(["stars", "darkness"])
        return f"[Night] {random.choice(NIGHT_OBSERVATIONS[bucket])}"
    
    return "[Night] The night sky is clear. Stars wheel overhead."


def night_visibility_report(visibility: float, phase: str, temp_c: float) -> str:
    """Short night visibility report for HUD or scanner display."""
    vis_label = {
        0.0: "Pitch Black",
        0.25: "Silhouettes Only",
        0.50: "Low Visibility",
        0.75: "Moderate Visibility",
        1.0: "Full Visibility",
    }
    label = "Unknown"
    for threshold, name in sorted(vis_label.items(), key=lambda x: -x[0]):
        if visibility >= threshold:
            label = name
            break
    
    phase_clean = phase.replace("_", " ").title()
    return f"[Visibility] {label} | Phase: {phase_clean} | {temp_c:.1f}C"


# ────────────────────────────────────────────────────────────────────────────
# Proximity-Triggered Night Observations
# ────────────────────────────────────────────────────────────────────────────

# Observations that fire when player enters a trigger volume, keyed by trigger type.
# The trigger system checks time-of-day before showing these.
PROXIMITY_NIGHT_OBSERVATIONS: Dict[str, List[tuple]] = {
    "canyon_wall": [
        ("night", "You hear the canyon wall creaking. The stone is cooling and contracting after the day's heat."),
        ("dawn", "Condensation beads run down the canyon wall. The temperature reached the dew point overnight."),
    ],
    "water_source": [
        ("night", "The water is still. No wind. The surface reflects starlight perfectly."),
        ("cold", "Ice crystals form at the water's edge. The temperature is below freezing."),
    ],
    "cracked_rock": [
        ("night", "This crack widened at night. Thermal contraction pulled the rock apart."),
        ("cold", "Frost wedging: water seeped into this crack, froze, and expanded. The crack is millimeters wider than yesterday."),
    ],
    "open_sky": [
        ("night", "The Milky Way stretches across the sky. Without atmospheric distortion, every star is sharp."),
        ("clear_night", "This is a good night for celestial navigation. The stars are reliable landmarks."),
    ],
}


def proximity_observation(trigger_type: str, phase: str, temp_c: float) -> Optional[str]:
    """Get a night-specific observation for a proximity trigger volume.
    
    Args:
        trigger_type: Trigger volume type (canyon_wall, water_source, etc.).
        phase: Night phase string.
        temp_c: Current temperature.
        
    Returns:
        Observation string if applicable, None otherwise.
    """
    import random
    
    if trigger_type not in PROXIMITY_NIGHT_OBSERVATIONS:
        return None
    
    candidates = []
    is_night = phase in ("night", "deep_night", "pre_dawn", "civil_twilight", "nautical_twilight")
    is_dawn = phase in ("dawn", "astronomical_twilight")
    is_cold = temp_c < 5.0
    
    for condition, text in PROXIMITY_NIGHT_OBSERVATIONS[trigger_type]:
        if condition == "night" and is_night:
            candidates.append(text)
        elif condition == "dawn" and is_dawn:
            candidates.append(text)
        elif condition == "cold" and is_cold:
            candidates.append(text)
        elif condition == "clear_night" and is_night and is_cold:  # cold = clear
            candidates.append(text)
    
    if not candidates:
        return None
    
    return f"[Discovery] {random.choice(candidates)}"
