# -*- coding: utf-8 -*-
"""celestial_rotation.py — Time-of-day controller (Celestial_Light_Rotation spec).

GRAPH-SPECIFIED DESIGN (Celestial_Light_Rotation, 26 Qs):
- Sun follows fixed equatorial arc. No axial tilt in v1.
- Sun height above horizon = time of day. Shadow length reinforces this.
- Star sphere is world-aligned: constellations maintain fixed terrain positions.
- Directional light rotates in world space; cloud lighting follows naturally.
- Configurable rotation speed (5-10 min full day).
- Shared time-of-day variable (float 0.0-1.0) consumed by Temperature_Time_System
  and Night_Visibility_Gameplay. Single source of truth.
- Can be paused, reversed, speed-controlled at runtime.

MCP integration: set directional light rotation transform + star sphere rotation.
"""

import math
import time as _time
from typing import Optional, Callable

# ────────────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────────────

DEFAULT_DAY_DURATION_SECONDS = 360.0  # 6 minutes = full day
MIN_DAY_DURATION = 60.0               # 1 minute fast-forward
MAX_DAY_DURATION = 3600.0             # 1 hour slow cycle

# Sun arc: elevation angle range
SUN_MIN_ELEVATION = -15.0   # degrees below horizon (astronomical twilight)
SUN_MAX_ELEVATION = 75.0    # degrees above horizon (desert noon)

# Star sphere rotation offset (world-aligned)
STAR_SPHERE_AXIAL_TILT = 23.5  # Earth-like tilt for star rotation axis

# Time-of-day thresholds
DAWN_START = 0.20    # 20% through cycle = first light
SUNRISE = 0.25       # 25% = sun crosses horizon
NOON = 0.50          # 50% = sun at peak
SUNSET = 0.75        # 75% = sun below horizon
DUSK_END = 0.80      # 80% = end of civil twilight
NIGHT = 0.85         # 85% = full night

# ────────────────────────────────────────────────────────────────────────────
# Celestial Clock
# ────────────────────────────────────────────────────────────────────────────

class CelestialClock:
    """Shared time-of-day clock. Single source of truth for all sub-features.
    
    Maintains a normalized time value [0.0, 1.0) representing the full
    day/night cycle. Systems read from this clock; they do not maintain
    their own time.
    """
    
    def __init__(self, day_duration: float = DEFAULT_DAY_DURATION_SECONDS):
        self._day_duration = day_duration
        self._elapsed = 0.0
        self._paused = False
        self._speed_multiplier = 1.0
        self._absolute_time: Optional[float] = None  # set externally to override
        self._on_time_change: Optional[Callable[[float], None]] = None
    
    # ── Properties ──────────────────────────────────────────────────────
    
    @property
    def normalized_time(self) -> float:
        """Current time of day as float in [0.0, 1.0)."""
        if self._absolute_time is not None:
            return max(0.0, min(0.999, self._absolute_time))
        if self._day_duration <= 0:
            return 0.0
        t = (self._elapsed % self._day_duration) / self._day_duration
        return max(0.0, min(0.999, t))
    
    @normalized_time.setter
    def normalized_time(self, value: float):
        """Set absolute time-of-day (clamped 0.0-1.0). Overrides simulation."""
        self._absolute_time = max(0.0, min(0.999, value))
    
    @property
    def day_duration(self) -> float:
        return self._day_duration
    
    @day_duration.setter
    def day_duration(self, seconds: float):
        self._day_duration = max(MIN_DAY_DURATION, min(MAX_DAY_DURATION, seconds))
    
    @property
    def paused(self) -> bool:
        return self._paused
    
    @paused.setter
    def paused(self, value: bool):
        self._paused = value
    
    @property
    def speed(self) -> float:
        return self._speed_multiplier
    
    @speed.setter
    def speed(self, multiplier: float):
        self._speed_multiplier = max(0.0, multiplier)  # 0 = frozen, negative = reverse
    
    @property
    def is_night(self) -> bool:
        """True when directional light is below horizon (sun elevation < 0)."""
        return self.sun_elevation < 0.0
    
    # ── Events ──────────────────────────────────────────────────────────
    
    def on_time_change(self, callback: Optional[Callable[[float], None]]):
        """Register callback invoked every time normalized_time changes."""
        self._on_time_change = callback
    
    # ── Simulation ──────────────────────────────────────────────────────
    
    def tick(self, delta_seconds: float):
        """Advance clock by delta_seconds (real time). Call every frame."""
        if self._paused:
            return
        # If absolute_time was set externally, release after one tick
        if self._absolute_time is not None:
            self._elapsed = self._absolute_time * self._day_duration
            self._absolute_time = None
            return
        self._elapsed += delta_seconds * self._speed_multiplier
        if self._on_time_change:
            self._on_time_change(self.normalized_time)
    
    def reset(self):
        """Reset clock to start of day."""
        self._elapsed = 0.0
        self._absolute_time = None
        self._paused = False
        self._speed_multiplier = 1.0
    
    # ── Derived values ──────────────────────────────────────────────────
    
    @property
    def sun_elevation(self) -> float:
        """Sun elevation angle in degrees. Negative = below horizon."""
        t = self.normalized_time
        # Map [0.0, 1.0] → [min_elev, max_elev, min_elev] (parabolic arc)
        # Peak at t=0.5 (noon)
        normalized_angle = 2.0 * math.pi * t
        # Sun rises at t=0.25, peaks at t=0.5, sets at t=0.75
        sin_val = math.sin(normalized_angle - math.pi / 2.0)
        elevation = SUN_MIN_ELEVATION + (SUN_MAX_ELEVATION - SUN_MIN_ELEVATION) * (sin_val + 1.0) / 2.0
        # Clamp so sun goes negative (below horizon) at night
        if t < DAWN_START or t > DUSK_END:
            elevation = max(-90.0, min(SUN_MIN_ELEVATION, elevation))
        return elevation
    
    @property
    def sun_azimuth(self) -> float:
        """Sun azimuth in degrees (0 = north, 90 = east)."""
        t = self.normalized_time
        # Full 360 rotation over the day
        azimuth = (t * 360.0) % 360.0
        return azimuth
    
    @property
    def sun_direction(self) -> tuple:
        """Sun direction vector (x, y, z) for UE5 directional light rotation."""
        elev_rad = math.radians(self.sun_elevation)
        azim_rad = math.radians(self.sun_azimuth)
        x = math.cos(elev_rad) * math.sin(azim_rad)
        y = math.cos(elev_rad) * math.cos(azim_rad)
        z = math.sin(elev_rad)
        return (x, y, z)
    
    @property
    def sun_intensity_factor(self) -> float:
        """Sun brightness multiplier [0.0, 1.0]. 0 at night, ramps at dawn."""
        elev = self.sun_elevation
        if elev >= 10.0:
            return 1.0
        elif elev <= -5.0:
            return 0.0
        else:
            # Smooth ramp between -5 and +10 degrees
            return max(0.0, min(1.0, (elev + 5.0) / 15.0))
    
    @property
    def star_visibility(self) -> float:
        """Star sphere opacity [0.0, 1.0]. Inversely related to sun intensity."""
        return 1.0 - self.sun_intensity_factor
    
    @property
    def star_sphere_rotation(self) -> float:
        """Star sphere yaw rotation in degrees (world-aligned, rotates slowly)."""
        t = self.normalized_time
        return (t * 360.0) % 360.0
    
    @property
    def time_of_day_label(self) -> str:
        """Human-readable time-of-day label for educational observations."""
        t = self.normalized_time
        if t < DAWN_START:
            return "night"
        elif t < SUNRISE:
            return "dawn"
        elif t < NOON - 0.05:
            return "morning"
        elif t < NOON + 0.05:
            return "noon"
        elif t < SUNSET:
            return "afternoon"
        elif t < DUSK_END:
            return "dusk"
        else:
            return "night"
    
    # ── Serialization ───────────────────────────────────────────────────
    
    def to_dict(self) -> dict:
        return {
            "normalized_time": self.normalized_time,
            "day_duration": self._day_duration,
            "paused": self._paused,
            "speed": self._speed_multiplier,
            "sun_elevation": self.sun_elevation,
            "sun_azimuth": self.sun_azimuth,
            "sun_intensity": self.sun_intensity_factor,
            "star_visibility": self.star_visibility,
            "is_night": self.is_night,
            "time_label": self.time_of_day_label,
        }
    
    def __repr__(self) -> str:
        return (f"<CelestialClock t={self.normalized_time:.3f} "
                f"elev={self.sun_elevation:.1f}deg "
                f"label='{self.time_of_day_label}'>")


# ────────────────────────────────────────────────────────────────────────────
# MCP Integration Helper
# ────────────────────────────────────────────────────────────────────────────

def build_celestial_mcp_payload(clock: CelestialClock) -> dict:
    """Build MCP tool-call payload for UE5 directional light + star sphere.
    
    Returns:
        dict with keys 'directional_light_rotation' (PYR) and 
        'star_sphere_rotation' (yaw) for use with MCP tool_call.
    """
    sun_dir = clock.sun_direction
    # UE5 uses pitch/yaw/roll for rotation
    # Direction vector → pitch (x-axis rotation) and yaw (z-axis rotation)
    pitch = math.degrees(math.asin(sun_dir[2]))  # vertical angle
    yaw = clock.sun_azimuth  # horizontal angle
    
    return {
        "directional_light": {
            "pitch": pitch,
            "yaw": yaw,
            "roll": 0.0,
            "intensity": clock.sun_intensity_factor,
        },
        "star_sphere": {
            "yaw": clock.star_sphere_rotation,
            "opacity": clock.star_visibility,
        },
        "time_of_day": clock.normalized_time,
        "is_night": clock.is_night,
    }


def mcp_sync_celestial(mcp_client, clock: CelestialClock) -> dict:
    """Send celestial state to UE5 via MCP.
    
    Args:
        mcp_client: An MCP instance from worker_bridge.mcp_builder.
        clock: CelestialClock instance.
        
    Returns:
        MCP response dict.
    """
    payload = build_celestial_mcp_payload(clock)
    # Set directional light rotation
    dl = payload["directional_light"]
    mcp_client.tool_call(
        "control_actor", "set_actor_transform",
        actorName="DirectionalLight",
        rotation={"pitch": dl["pitch"], "yaw": dl["yaw"], "roll": dl["roll"]},
    )
    # Set star sphere rotation
    ss = payload["star_sphere"]
    mcp_client.tool_call(
        "control_actor", "set_actor_transform",
        actorName="StarSphere",
        rotation={"pitch": 0.0, "yaw": ss["yaw"], "roll": 0.0},
    )
    return payload
