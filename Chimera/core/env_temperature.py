# -*- coding: utf-8 -*-
"""env_temperature.py — Temperature calculation module (Temperature_Time_System spec).

GRAPH-SPECIFIED DESIGN (Temperature_Time_System, 26 Qs):
- Temperature curve includes thermal lag: peak 1-2h after solar noon.
- Desert canyon diurnal swing: ~45C at 14:00, ~5C just before dawn.
- Configurable curve parameters (base temp, amplitude, lag offset).
- Smooth continuous curve (no snapping at boundaries).
- Shares time-of-day clock with Celestial_Light_Rotation (single source of truth).
- Educational observations keyed to temperature thresholds.
- Pure Python: unit-testable without UE5.
- MCP: temperature exposed as Blueprint property for override/testing.

Thermal inertia model: peak temperature occurs at configurable offset
after solar noon (default 0.08 normalized time ~ 1.9h in a 6-min day).
"""

import math
from typing import Optional, List, Dict, Callable

# ────────────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────────────

# Default desert diurnal parameters
DEFAULT_BASE_TEMP_C = 25.0          # midpoint of daily swing
DEFAULT_AMPLITUDE_C = 20.0          # +/- from base → 5C to 45C range
DEFAULT_THERMAL_LAG = 0.08          # normalized time offset after noon (peak)
DEFAULT_NOON = 0.50                 # solar noon in normalized time

# Temperature thresholds for educational observations (°C)
TEMP_THRESHOLDS = {
    "freezing": (None, 0.0),         # below 0C
    "cold": (0.0, 15.0),            # 0-15C
    "cool": (15.0, 25.0),           # 15-25C
    "warm": (25.0, 35.0),           # 25-35C
    "hot": (35.0, 45.0),            # 35-45C
    "extreme_heat": (45.0, None),   # above 45C
}

# ────────────────────────────────────────────────────────────────────────────
# Temperature Curve
# ────────────────────────────────────────────────────────────────────────────

class TemperatureCurve:
    """Temperature as a function of normalized time-of-day.
    
    Models a desert diurnal cycle with thermal inertia: the hottest part
    of the day occurs after solar noon, matching real physics.
    
    The curve is a cosine-based function:
        T(t) = base - amplitude * cos(2*pi*(t - lag_offset - noon))
    
    where t is normalized time [0.0, 1.0) from the shared CelestialClock.
    """
    
    def __init__(self,
                 base_temp: float = DEFAULT_BASE_TEMP_C,
                 amplitude: float = DEFAULT_AMPLITUDE_C,
                 thermal_lag: float = DEFAULT_THERMAL_LAG):
        self.base_temp = base_temp
        self.amplitude = amplitude
        self.thermal_lag = thermal_lag
        self._on_threshold: Optional[Callable[[str, float], None]] = None
        self._last_threshold: Optional[str] = None
    
    def temperature_at(self, normalized_time: float) -> float:
        """Calculate temperature at a given normalized time [0.0, 1.0).
        
        Args:
            normalized_time: Time of day (0.0-1.0) from CelestialClock.
            
        Returns:
            Temperature in Celsius.
        """
        # Cosine curve: peak temperature occurs at (noon + thermal_lag).
        # Thermal inertia: ground continues warming after solar noon.
        # Coolest point is just before dawn (t ~ 0.02-0.05).
        t_peak = DEFAULT_NOON + self.thermal_lag
        phase = 2.0 * math.pi * (normalized_time - t_peak)
        temp = self.base_temp + self.amplitude * math.cos(phase)
        return temp
    
    @property
    def min_temp(self) -> float:
        """Minimum temperature for current parameters (just before dawn)."""
        return self.base_temp - self.amplitude
    
    @property
    def max_temp(self) -> float:
        """Maximum temperature for current parameters (after noon)."""
        return self.base_temp + self.amplitude
    
    @property
    def diurnal_range(self) -> float:
        """Total diurnal temperature swing."""
        return self.amplitude * 2.0
    
    # ── Threshold monitoring ────────────────────────────────────────────
    
    def on_threshold_cross(self, callback: Callable[[str, float], None]):
        """Register callback invoked when temperature crosses a threshold band.
        
        Callback receives (threshold_label, current_temp).
        """
        self._on_threshold = callback
    
    def check_threshold(self, current_temp: float) -> Optional[str]:
        """Check which temperature band current temp falls in.
        
        Returns threshold label string if crossed, None if same as last.
        """
        label = None
        for band, (lo, hi) in TEMP_THRESHOLDS.items():
            if lo is None or lo <= current_temp:
                if hi is None or current_temp < hi:
                    label = band
                    break
        
        if label and label != self._last_threshold:
            self._last_threshold = label
            if self._on_threshold:
                self._on_threshold(label, current_temp)
            return label
        return None
    
    def reset_threshold(self):
        """Reset threshold tracking (use when time jumps)."""
        self._last_threshold = None
    
    # ── Configuration ───────────────────────────────────────────────────
    
    def configure(self, base_temp: Optional[float] = None,
                  amplitude: Optional[float] = None,
                  thermal_lag: Optional[float] = None):
        """Update curve parameters at runtime."""
        if base_temp is not None:
            self.base_temp = base_temp
        if amplitude is not None:
            self.amplitude = amplitude
        if thermal_lag is not None:
            self.thermal_lag = max(0.0, min(0.25, thermal_lag))  # 0-6h lag
        self.reset_threshold()
    
    # ── Serialization ───────────────────────────────────────────────────
    
    def to_dict(self) -> dict:
        return {
            "base_temp_c": self.base_temp,
            "amplitude_c": self.amplitude,
            "thermal_lag": self.thermal_lag,
            "min_temp_c": self.min_temp,
            "max_temp_c": self.max_temp,
            "diurnal_range_c": self.diurnal_range,
        }
    
    def __repr__(self) -> str:
        return (f"<TemperatureCurve base={self.base_temp}C "
                f"range=[{self.min_temp:.1f}, {self.max_temp:.1f}]C "
                f"lag={self.thermal_lag:.3f}>")


# ────────────────────────────────────────────────────────────────────────────
# Educational Mapping
# ────────────────────────────────────────────────────────────────────────────

# Temperature-gated educational observations
# Band → [(condition, observation), ...]
TEMPERATURE_OBSERVATIONS: Dict[str, List[tuple]] = {
    "extreme_heat": [
        (True, "The rock surface is too hot to touch. Thermal expansion is visible — you can hear the stone creaking."),
        (True, "Heat shimmers rise from the canyon floor. The air feels like an oven."),
        ("near_cracked_rock", "This crack was formed by thermal expansion. At noon, the rock expanded and fractured. Now it is cooling and contracting."),
    ],
    "hot": [
        (True, "The ground radiates heat. Different rocks conduct heat differently — try touching the shaded side of a boulder."),
        (True, "Sweat evaporates instantly. The low humidity makes the heat more bearable."),
        ("near_cracked_rock", "Thermal expansion is most active now. Rocks expand in the heat and contract at night."),
    ],
    "warm": [
        (True, "The temperature is pleasant but rising. Soon the canyon floor will be too hot for bare hands."),
        (True, "Birds (if present) are active now. Warmth brings life."),
        ("near_canyon_wall", "The canyon walls store solar energy. They release heat slowly, creating a microclimate."),
    ],
    "cool": [
        (True, "The air is cooling. This is the most comfortable time for physical activity."),
        (True, "Shadows are long. The sun's angle reduces heating efficiency."),
        ("near_water", "The water is warmer than the air. Steam rises gently from the surface."),
    ],
    "cold": [
        (True, "The temperature is dropping fast. Without atmospheric insulation, heat radiates into space quickly."),
        (True, "Breath becomes visible. Your fingers feel stiff."),
        ("near_canyon_wall", "The canyon walls still hold yesterday's heat. Press your hand against the stone — it is warmer than the air."),
    ],
    "freezing": [
        (True, "Frost forms on exposed surfaces. Water in cracks expands as it freezes, widening the fissures."),
        (True, "The stars are sharp and bright. Cold air holds less moisture, making the atmosphere perfectly clear."),
        ("near_water", "Ice crystals form at the water's edge. Freeze-thaw erosion is active at this temperature."),
        ("near_cracked_rock", "This rock cracked because water froze in a microscopic fissure and expanded. This is how mountains are worn down over eons."),
    ],
}

# Time-specific observations
TIME_TEMPERATURE_OBSERVATIONS = {
    "dawn": [
        "First light. The temperature is at its coldest point. Frost sparkles on every surface.",
        "Dawn chill. The night's cooling reached its maximum. Soon the sun will warm the canyon.",
    ],
    "noon": [
        "Solar noon. But the hottest hour is yet to come — thermal inertia keeps warming for another 1-2 hours.",
        "The sun is directly overhead. Heat builds in every rock and grain of sand.",
    ],
    "dusk": [
        "The sun is gone but the ground still radiates heat. Thermal lag in reverse — the air cools faster than the rock.",
        "Day's heat stored in the canyon walls. It will radiate for hours after sunset.",
    ],
    "night": [
        "Rapid cooling. Without an atmosphere, the surface temperature drops 10C per hour.",
        "The rocks are contracting audibly — the sound of cooling stone. This is thermal stress in reverse.",
    ],
}


def temperature_observation(temp_c: float, time_label: str,
                            context: Optional[Dict[str, bool]] = None) -> str:
    """Generate an educational observation based on current temperature.
    
    Args:
        temp_c: Current temperature in Celsius.
        time_label: Time-of-day label from CelestialClock (dawn/noon/dusk/night/...).
        context: Dict of boolean context flags, e.g. {'near_cracked_rock': True}.
        
    Returns:
        Educational observation string.
    """
    if context is None:
        context = {}
    
    # Determine temperature band
    band = None
    for label, (lo, hi) in TEMP_THRESHOLDS.items():
        if lo is None or lo <= temp_c:
            if hi is None or temp_c < hi:
                band = label
                break
    
    # Try context-matched observation first
    if band and band in TEMPERATURE_OBSERVATIONS:
        for condition, text in TEMPERATURE_OBSERVATIONS[band]:
            if isinstance(condition, str):
                if context.get(condition, False):
                    return f"[Temperature] {text}"
            elif condition is True:
                # Generic observation: always matches
                if context.get("allow_generic", True):
                    return f"[Temperature] {text}"
    
    # Fall back to time-specific observation
    if time_label in TIME_TEMPERATURE_OBSERVATIONS:
        import random
        return f"[Temperature] {random.choice(TIME_TEMPERATURE_OBSERVATIONS[time_label])}"
    
    return f"[Temperature] The temperature is {temp_c:.1f}C."


def thermal_inertia_lesson() -> str:
    """Return the thermal inertia educational fact (key lesson of this system)."""
    return (
        "[Temperature] Thermal inertia: the ground absorbs solar energy all morning, "
        "peaking 1-2 hours AFTER noon. This is why the hottest moment of the day "
        "is not when the sun is highest, but after the ground has had time to warm."
    )


def temperature_report(temp_c: float, time_label: str,
                       band: Optional[str] = None) -> str:
    """Short temperature report for HUD or scanner display."""
    if band is None:
        for label, (lo, hi) in TEMP_THRESHOLDS.items():
            if lo is None or lo <= temp_c:
                if hi is None or temp_c < hi:
                    band = label
                    break
    band_str = band.replace("_", " ").title() if band else "Unknown"
    return f"[{band_str}] {temp_c:.1f}C at {time_label.title()}"
