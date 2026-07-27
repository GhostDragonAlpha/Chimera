# -*- coding: utf-8 -*-
"""day_night_orchestrator.py — Integrates celestial_rotation, env_temperature,
and night_visibility into a single tick-driven system.

GRAPH-SPECIFIED DESIGN (Demo_Day_Night_Cycle, 44 Qs):
- Sun arc teaches time estimation (sun height = time).
- Star sphere world-aligned for celestial navigation.
- Temperature curve peaks 1-2h after solar noon (thermal inertia lesson).
- Night changes observations (stars, condensation, cold-related geology).
- 3 sub-features each drive specific education via shared time-of-day variable.
- All sub-features are independent, can be built in parallel.

This orchestrator ticks the shared clock and propagates state to
the temperature and night systems. Optionally sends state to UE5 via MCP.
"""

import time as _time
from typing import Optional

from celestial_rotation import CelestialClock, build_celestial_mcp_payload
from env_temperature import TemperatureCurve, temperature_observation, temperature_report
from night_visibility import NightState, night_observation, proximity_observation, night_visibility_report

try:
    import sys
    sys.path.insert(0, r"E:\PythonChimera\worker_bridge")
    from mcp_builder import MCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class DayNightOrchestrator:
    """Top-level orchestrator for the complete day/night cycle system.
    
    Tick this once per frame/step. It handles:
    1. Celestial clock advancement
    2. Temperature calculation
    3. Night visibility determination
    4. Educational observation generation
    5. Optional MCP sync to UE5
    """
    
    def __init__(self, day_duration_seconds: float = 360.0,
                 use_mcp: bool = False):
        self.clock = CelestialClock(day_duration=day_duration_seconds)
        self.temperature = TemperatureCurve()
        self.night = NightState()
        
        self._mcp = None
        self._use_mcp = use_mcp and MCP_AVAILABLE
        if self._use_mcp:
            try:
                self._mcp = MCP()
                print("[DayNightOrchestrator] MCP connected")
            except Exception as e:
                print(f"[DayNightOrchestrator] MCP connection failed: {e}")
                self._use_mcp = False
        
        self._last_logged_time = -1.0
    
    # ── Tick ────────────────────────────────────────────────────────────
    
    def tick(self, delta_seconds: float) -> dict:
        """Advance all systems by delta_seconds.
        
        Returns:
            dict with current state: time, temperature, visibility, observations.
        """
        # 1. Advance clock
        self.clock.tick(delta_seconds)
        t = self.clock.normalized_time
        
        # 2. Calculate temperature
        temp = self.temperature.temperature_at(t)
        self.temperature.check_threshold(temp)
        
        # 3. Update night tracking
        self.night.update(t, delta_seconds)
        
        # 4. Optionally sync to MCP
        if self._use_mcp and self._mcp:
            try:
                payload = build_celestial_mcp_payload(self.clock)
                dl = payload["directional_light"]
                self._mcp.tool_call(
                    "control_actor", "set_actor_transform",
                    actorName="DirectionalLight",
                    rotation={"pitch": dl["pitch"], "yaw": dl["yaw"], "roll": dl["roll"]},
                )
                ss = payload["star_sphere"]
                self._mcp.tool_call(
                    "control_actor", "set_actor_transform",
                    actorName="StarSphere",
                    rotation={"pitch": 0.0, "yaw": ss["yaw"], "roll": 0.0},
                )
            except Exception as e:
                print(f"[DayNightOrchestrator] MCP sync error: {e}")
        
        # 5. Build state dict
        state = self.get_state()
        return state
    
    # ── State query ─────────────────────────────────────────────────────
    
    def get_state(self) -> dict:
        """Return current full state without advancing time."""
        t = self.clock.normalized_time
        temp = self.temperature.temperature_at(t)
        night_phase = self.night.night_phase(t)
        vis = self.night.visibility_level(t)
        
        return {
            "time": {
                "normalized": t,
                "label": self.clock.time_of_day_label,
                "night": self.clock.is_night,
                "sun_elevation": self.clock.sun_elevation,
                "sun_azimuth": self.clock.sun_azimuth,
                "sun_intensity": self.clock.sun_intensity_factor,
                "star_visibility": self.clock.star_visibility,
            },
            "temperature": {
                "celsius": round(temp, 1),
                "curve": self.temperature.to_dict(),
            },
            "visibility": {
                "level": round(vis, 3),
                "phase": night_phase,
                "can_see_detail": self.night.can_see_detail(t),
                "silhouette_only": self.night.silhouette_only(t),
            },
        }
    
    # ── Educational observations ────────────────────────────────────────
    
    def get_observation(self, context: Optional[dict] = None) -> str:
        """Generate a context-aware educational observation.
        
        Args:
            context: Optional dict with keys like:
                - 'near_cracked_rock': bool
                - 'near_canyon_wall': bool
                - 'near_water': bool
                - 'open_sky': bool
                - 'trigger_type': str (for proximity observations)
                
        Returns:
            Observation string.
        """
        if context is None:
            context = {}
        
        t = self.clock.normalized_time
        temp = self.temperature.temperature_at(t)
        
        # Night observation takes priority if it's dark
        if self.clock.is_night:
            phase = self.night.night_phase(t)
            # Check proximity observation first
            trigger = context.get("trigger_type")
            if trigger:
                prox = proximity_observation(trigger, phase, temp)
                if prox:
                    return prox
            return night_observation(self.clock.sun_elevation, temp, phase, context)
        
        # Daytime: temperature-based observation
        return temperature_observation(temp, self.clock.time_of_day_label, context)
    
    def get_report(self) -> str:
        """Full environmental report string."""
        state = self.get_state()
        t = state["time"]["label"].upper()
        temp = state["temperature"]["celsius"]
        phase = state["visibility"]["phase"].replace("_", " ").title()
        
        lines = [
            "=== ENVIRONMENTAL SCAN ===",
            f"Time: {t}",
            f"Sun: {state['time']['sun_elevation']:.1f}deg elevation",
            f"Temperature: {temp}C",
            f"Visibility: {state['visibility']['level']:.0%} ({phase})",
            f"Stars: {state['time']['star_visibility']:.0%}",
            "",
            self.get_observation(),
        ]
        return "\n".join(lines)
    
    # ── Configuration ───────────────────────────────────────────────────
    
    def set_day_duration(self, seconds: float):
        self.clock.day_duration = seconds
    
    def set_speed(self, multiplier: float):
        self.clock.speed = multiplier
    
    def set_paused(self, paused: bool):
        self.clock.paused = paused
    
    def set_time(self, normalized: float):
        self.clock.normalized_time = normalized
    
    def configure_temperature(self, base_temp: Optional[float] = None,
                               amplitude: Optional[float] = None,
                               thermal_lag: Optional[float] = None):
        self.temperature.configure(base_temp, amplitude, thermal_lag)
    
    # ── Serialization ───────────────────────────────────────────────────
    
    def to_dict(self) -> dict:
        state = self.get_state()
        state["config"] = {
            "day_duration": self.clock.day_duration,
            "speed": self.clock.speed,
            "paused": self.clock.paused,
        }
        return state
    
    def __repr__(self) -> str:
        s = self.get_state()
        return (f"<DayNightOrchestrator "
                f"t={s['time']['normalized']:.3f} "
                f"{s['time']['label']} "
                f"{s['temperature']['celsius']}C "
                f"vis={s['visibility']['level']:.0%}>")


# ────────────────────────────────────────────────────────────────────────────
# Standalone test / demo
# ────────────────────────────────────────────────────────────────────────────

def run_demo(day_duration: float = 60.0, steps: int = 100):
    """Simulate a full day/night cycle with print output.
    
    Args:
        day_duration: Length of a full day in seconds (real time).
        steps: Number of ticks to simulate the full cycle.
    """
    dt = day_duration / steps
    orch = DayNightOrchestrator(day_duration_seconds=day_duration)
    
    print(f"{'='*60}")
    print(f"Day/Night Cycle Demo ({day_duration}s day, {steps} steps)")
    print(f"{'='*60}")
    
    for i in range(steps):
        state = orch.tick(dt)
        t = state["time"]
        temp = state["temperature"]
        vis = state["visibility"]
        
        print(f"  t={t['normalized']:.3f}  {t['label']:10s}  "
              f"sun={t['sun_elevation']:6.1f}deg  "
              f"temp={temp['celsius']:5.1f}C  "
              f"vis={vis['level']:.0%}  {vis['phase']:20s}  "
              f"obs={orch.get_observation()}")
    
    print(f"\n{'='*60}")
    print("Full report:", orch.get_report(), sep="\n")


def test_thermal_inertia():
    """Verify thermal lag: peak temp should occur AFTER noon (t=0.50)."""
    from env_temperature import DEFAULT_THERMAL_LAG, DEFAULT_NOON
    curve = TemperatureCurve()
    peak_t = 0.0
    peak_temp = float("-inf")
    for i in range(1000):
        t = i / 1000.0
        temp = curve.temperature_at(t)
        if temp > peak_temp:
            peak_temp = temp
            peak_t = t
    expected_peak = DEFAULT_NOON + DEFAULT_THERMAL_LAG
    print(f"  Peak temp {peak_temp:.1f}C at t={peak_t:.3f} "
          f"(expected ~t={expected_peak:.3f})")
    assert abs(peak_t - expected_peak) < 0.02, \
        f"Peak at {peak_t}, expected ~{expected_peak}"
    print("  PASS: Thermal inertia verified.")


def test_night_cycle():
    """Verify night state transitions."""
    from celestial_rotation import SUNRISE, SUNSET
    orch = DayNightOrchestrator(day_duration_seconds=360.0)
    day_visits = 0
    night_visits = 0
    for i in range(100):
        orch.set_time(i / 100.0)
        state = orch.get_state()
        if state["time"]["night"]:
            night_visits += 1
        else:
            day_visits += 1
    print(f"  Day ticks: {day_visits}, Night ticks: {night_visits}")
    assert day_visits > 0 and night_visits > 0, \
        "Night cycle should have both day and night phases"
    print("  PASS: Night cycle transitions verified.")


if __name__ == "__main__":
    import sys
    
    print()
    print("=" * 60)
    print("DEMO_DAY_NIGHT_CYCLE — Build Verification")
    print("=" * 60)
    print()
    
    # Test 1: Thermal inertia
    print("[Test 1] Thermal inertia (peak after noon)...")
    test_thermal_inertia()
    print()
    
    # Test 2: Night cycle
    print("[Test 2] Night cycle transitions...")
    test_night_cycle()
    print()
    
    # Test 3: Full cycle demo (fast)
    print("[Test 3] Full cycle demo (10s cycle)...")
    run_demo(day_duration=10.0, steps=50)
    print()
    
    # Test 4: Fast-forward to specific times
    print("[Test 4] Time queries at key moments...")
    orch = DayNightOrchestrator(day_duration_seconds=360.0)
    for test_t in [0.0, 0.25, 0.50, 0.58, 0.75, 0.85]:
        orch.set_time(test_t)
        state = orch.get_state()
        obs = orch.get_observation({"trigger_type": "canyon_wall"})
        print(f"  t={test_t:.2f}  {state['time']['label']:10s}  "
              f"temp={state['temperature']['celsius']}C  "
              f"night={state['time']['night']}  "
              f"obs={obs}")
    print()
    
    print("All builds complete. Modules ready:")
    print("  Chimera/core/celestial_rotation.py")
    print("  Chimera/core/env_temperature.py")
    print("  Chimera/core/night_visibility.py")
    print("  Chimera/core/day_night_orchestrator.py")
