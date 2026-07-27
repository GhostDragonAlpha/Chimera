# -*- coding: utf-8 -*-
"""cloud_weather.py - Cloud state to weather connection.

Sub-feature of Demo_Volumetric_Clouds: Connect cloud visual states to the
weather system — cloud type drives precipitation, wind speed, and storm
severity, making cloud reading a core survival skill.

Teaches: Players predict storms, plan flights around weather, seek shelter
before bad weather arrives.
"""

import json, os, random, time
from pathlib import Path
from typing import Optional, Dict, Callable

from . import cloud_education

# --- Wind system ---

WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

class WindState:
    """Current wind conditions tied to cloud state."""
    
    def __init__(self):
        self.direction: str = "W"
        self.speed_kmh: float = 10.0  # low-level wind speed
        self.gust_factor: float = 1.0
        self._last_update: float = time.time()
    
    def update_from_cloud(self, cloud_type_id: str, transition_minutes: float = 5.0):
        """Update wind based on cloud type (education: wind matches cloud movement)."""
        base_winds = {
            "cumulus":       {"speed": 10, "gust": 1.2, "dir_change_prob": 0.1},
            "stratus":       {"speed": 15, "gust": 1.0, "dir_change_prob": 0.05},
            "cirrus":        {"speed": 40, "gust": 1.5, "dir_change_prob": 0.3},  # high-level
            "nimbostratus":  {"speed": 25, "gust": 1.8, "dir_change_prob": 0.2},
            "cumulonimbus":  {"speed": 30, "gust": 3.0, "dir_change_prob": 0.4},
        }
        cfg = base_winds.get(cloud_type_id, {"speed": 10, "gust": 1.0, "dir_change_prob": 0.1})
        
        self.speed_kmh = cfg["speed"] + random.uniform(-3, 3)
        self.gust_factor = cfg["gust"]
        
        if random.random() < cfg["dir_change_prob"]:
            self.direction = random.choice(WIND_DIRECTIONS)
        
        self._last_update = time.time()
    
    def gust_speed(self) -> float:
        return self.speed_kmh * self.gust_factor
    
    def cloud_movement_description(self) -> str:
        """Educational text: wind moves clouds."""
        speed_word = "fast" if self.speed_kmh > 30 else "moderate" if self.speed_kmh > 15 else "gentle"
        return f"[Weather] {speed_word.capitalize()} wind from the {self.direction} at {self.speed_kmh:.0f} km/h. Clouds moving {speed_word}ly across the sky."


# --- Weather state machine ---

class WeatherStateMachine:
    """Gradual weather transitions driven by cloud type changes.
    
    Education: weather transition feels gradual, not binary.
    Cloud types drive precipitation, wind speed, and storm severity.
    """
    
    # Cloud type -> weather state mapping
    CLOUD_TO_WEATHER = {
        None:            "clear",
        "cumulus":       "fair_weather",
        "stratus":       "overcast",
        "cirrus":        "changing",
        "nimbostratus":  "rain",
        "cumulonimbus":  "storm",
    }
    
    def __init__(self):
        self.current_state: str = "clear"
        self.previous_state: str = "clear"
        self.transition_progress: float = 1.0  # 0.0 = just left previous, 1.0 = fully in current
        self.current_cloud_type: Optional[str] = None
        self.wind = WindState()
        self._state_start_time: float = time.time()
        self._rain_intensity: float = 0.0
        self._storm_severity: float = 0.0
    
    def set_cloud_type(self, cloud_type_id: Optional[str]):
        """Set the dominant cloud type and transition weather accordingly.
        
        Education: dark low clouds = imminent rain,
        towering cumulonimbus = seek shelter now,
        clearing cirrus after rain = improving weather.
        """
        self.current_cloud_type = cloud_type_id
        new_state = self.CLOUD_TO_WEATHER.get(cloud_type_id, "clear")
        
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.transition_progress = 0.0
            self._state_start_time = time.time()
            
            # Update wind from cloud type
            self.wind.update_from_cloud(cloud_type_id if cloud_type_id else "cumulus")
            
            # Set rain/storm intensity based on state
            if new_state == "rain":
                self._rain_intensity = 0.5 + random.random() * 0.5  # 0.5-1.0
            elif new_state == "storm":
                self._rain_intensity = 0.8 + random.random() * 0.2  # 0.8-1.0
                self._storm_severity = 0.6 + random.random() * 0.4  # 0.6-1.0
            else:
                self._rain_intensity = max(0, self._rain_intensity - 0.3)
                self._storm_severity = max(0, self._storm_severity - 0.3)
    
    def tick(self, delta_minutes: float = 1.0):
        """Advance the transition by delta_minutes.
        
        Education: transitions are gradual (clear -> cloudy -> rain -> clearing).
        """
        if self.transition_progress < 1.0:
            # Each transition takes ~5-10 minutes to fully blend
            self.transition_progress = min(1.0, self.transition_progress + delta_minutes / 8.0)
            
            # Gradually intensify/de-escalate rain
            if self.current_state in ("rain", "storm"):
                target_rain = 0.8 if self.current_state == "storm" else 0.7
                self._rain_intensity = min(target_rain, self._rain_intensity + delta_minutes * 0.05)
            elif self.current_state in ("clear", "fair_weather"):
                self._rain_intensity = max(0, self._rain_intensity - delta_minutes * 0.05)
    
    def get_precipitation_description(self) -> str:
        """Describe current precipitation based on cloud/weather state.
        
        Education: rain intensity matches cloud darkness and altitude.
        """
        if self.current_state == "storm" and self._storm_severity > 0.5:
            return "[Weather] Torrential rain with hail. Lightning strikes nearby. Extreme danger."
        elif self.current_state == "storm":
            return "[Weather] Heavy rain and thunder. The storm is active."
        elif self.current_state == "rain":
            if self._rain_intensity > 0.7:
                return "[Weather] Heavy, steady rain. Visibility reduced. Seek shelter."
            else:
                return "[Weather] Light to moderate rain. Steady precipitation."
        elif self.current_state == "overcast":
            return "[Weather] Light drizzle possible. Sky is uniformly gray."
        else:
            return "[Weather] No precipitation."
    
    def get_prediction_text(self) -> str:
        """Predict weather 5-10 minutes ahead from cloud trends.
        
        Education: player learns to predict weather from cloud trends.
        """
        ct = self.current_cloud_type
        if ct == "cumulus":
            return "[Weather Prediction] Fair weather continuing. Watch for vertical cloud growth — that means storms later."
        elif ct == "cirrus":
            return "[Weather Prediction] Weather changing within 24-48 hours. Enjoy clear skies while they last."
        elif ct == "stratus":
            return "[Weather Prediction] Gradual thickening possible. Light rain within a few hours."
        elif ct == "nimbostratus":
            return "[Weather Prediction] Prolonged rain for hours. Storm not expected, but steady precipitation."
        elif ct == "cumulonimbus":
            return "[Weather Prediction] SEVERE: Storm is here. Lightning, hail, dangerous winds. Shelter now."
        return "[Weather Prediction] No clear pattern. Conditions stable."
    
    def get_shelter_advice(self) -> str:
        """Survival advice based on weather state.
        
        Education: cumulonimbus = seek shelter. Stratus/nimbostratus = find cover.
        """
        if self.current_state == "storm":
            return "[Survival] SEEK SHELTER NOW. Avoid high ground, tall objects, and open water. Lightning danger."
        elif self.current_state == "rain":
            return "[Survival] Find shelter from rain. Extended wet conditions cause hypothermia. Stay dry."
        elif self.current_state == "overcast":
            return "[Survival] Reduced visibility. Stay near recognizable landmarks."
        return "[Survival] Clear conditions. Good for travel."
    
    def state_summary(self) -> str:
        """Full weather status report."""
        lines = ["=== WEATHER STATUS ==="]
        lines.append(f"State: {self.current_state.upper()} (transition: {self.transition_progress:.0%})")
        
        if self.current_cloud_type:
            ct = cloud_education.get_cloud_type(self.current_cloud_type)
            if ct:
                lines.append(f"Cloud: {ct['display_name']} - {ct['educational_fact']}")
        
        lines.append(self.wind.cloud_movement_description())
        lines.append(self.get_precipitation_description())
        lines.append(self.get_prediction_text())
        lines.append(self.get_shelter_advice())
        
        return "\n".join(lines)


# --- MCP cloud control bridge ---

class CloudMCPBridge:
    """Bridge between Python weather state and UE5 VolumetricCloud actor.
    
    Uses MCP to set cloud material parameters per type:
    - density, color, altitude, shadow properties.
    """
    
    def __init__(self, actor_name: str = "DemoClouds", component_name: str = "VolumetricCloudComponent"):
        self.actor_name = actor_name
        self.component_name = component_name
        self._mcp = None
    
    def _get_mcp(self):
        if self._mcp is None:
            import sys
            sys.path.insert(0, str(Path(__file__).parents[2] / "worker_bridge"))
            from mcp_builder import MCP
            self._mcp = MCP()
        return self._mcp
    
    def apply_cloud_type(self, cloud_type_id: str):
        """Set UE5 VolumetricCloud component properties for a cloud type.
        
        Education: cloud parameters (density, altitude, color) are 
        MCP-configurable from Python.
        """
        ct = cloud_education.get_cloud_type(cloud_type_id)
        if ct is None:
            return {"error": f"Unknown cloud type: {cloud_type_id}"}
        
        mcp = self._get_mcp()
        
        # Map cloud type to material properties
        props = self._cloud_type_to_properties(cloud_type_id)
        
        results = []
        for prop_name, prop_value in props.items():
            try:
                r = mcp.tool_call("control_actor", "set_component_property",
                    actorName=self.actor_name,
                    componentName=self.component_name,
                    properties={prop_name: prop_value})
                results.append({prop_name: r.get("result", {}).get("structuredContent", {})})
            except Exception as e:
                results.append({prop_name: f"error: {e}"})
        
        return {
            "cloud_type": cloud_type_id,
            "applied_properties": list(props.keys()),
            "results": results,
        }
    
    def _cloud_type_to_properties(self, cloud_type_id: str) -> dict:
        """Map cloud type to VolumetricCloudComponent property values."""
        presets = {
            "cumulus": {
                "LayerBottomAltitude": 1000,
                "LayerHeight": 2000,
                "CloudDensity": 0.4,
                "CloudColor": {"R": 1.0, "G": 1.0, "B": 1.0, "A": 1.0},
                "bCastCloudShadows": True,
                "ShadowResolution": 512,
            },
            "stratus": {
                "LayerBottomAltitude": 200,
                "LayerHeight": 1500,
                "CloudDensity": 0.8,
                "CloudColor": {"R": 0.7, "G": 0.7, "B": 0.72, "A": 1.0},
                "bCastCloudShadows": True,
                "ShadowResolution": 256,
            },
            "cirrus": {
                "LayerBottomAltitude": 8000,
                "LayerHeight": 5000,
                "CloudDensity": 0.15,
                "CloudColor": {"R": 0.95, "G": 0.95, "B": 1.0, "A": 0.6},
                "bCastCloudShadows": False,
                "ShadowResolution": 128,
            },
            "nimbostratus": {
                "LayerBottomAltitude": 500,
                "LayerHeight": 2500,
                "CloudDensity": 0.95,
                "CloudColor": {"R": 0.3, "G": 0.3, "B": 0.35, "A": 1.0},
                "bCastCloudShadows": True,
                "ShadowResolution": 512,
            },
            "cumulonimbus": {
                "LayerBottomAltitude": 500,
                "LayerHeight": 10000,
                "CloudDensity": 0.9,
                "CloudColor": {"R": 0.2, "G": 0.2, "B": 0.3, "A": 1.0},
                "bCastCloudShadows": True,
                "ShadowResolution": 1024,
            },
        }
        return presets.get(cloud_type_id, presets["cumulus"])
    
    def set_shadow_properties(self, cast_shadows: bool = True, resolution: int = 512):
        """Configure cloud shadow rendering.
        
        Education: bCastCloudShadows enables dynamic cloud shadows
        that move across terrain and teach wind direction.
        """
        mcp = self._get_mcp()
        results = []
        
        r1 = mcp.tool_call("control_actor", "set_component_property",
            actorName=self.actor_name,
            componentName=self.component_name,
            properties={"bCastCloudShadows": cast_shadows})
        results.append({"bCastCloudShadows": r1.get("result", {})})
        
        r2 = mcp.tool_call("control_actor", "set_component_property",
            actorName=self.actor_name,
            componentName=self.component_name,
            properties={"ShadowResolution": resolution})
        results.append({"ShadowResolution": r2.get("result", {})})
        
        return {
            "shadows_enabled": cast_shadows,
            "shadow_resolution": resolution,
            "results": results,
        }
    
    def apply_weather_state(self, weather_state_id: str):
        """Apply a full weather state to the cloud actor.
        
        Education: cloud visual states connect to weather — cloud type
        drives precipitation, wind speed, and storm severity.
        """
        ws = cloud_education.get_weather_state(weather_state_id)
        if ws is None:
            return {"error": f"Unknown weather state: {weather_state_id}"}
        
        cloud_types = ws.get("cloud_types_present", [])
        results = []
        
        if cloud_types:
            # Apply the first matching cloud type
            ct_id = cloud_types[0]
            results.append(self.apply_cloud_type(ct_id))
        else:
            # Clear skies
            results.append(self.apply_cloud_type("cumulus"))
        
        return {
            "weather_state": weather_state_id,
            "cloud_types_applied": cloud_types,
            "results": results,
        }
