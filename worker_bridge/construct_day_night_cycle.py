"""CONSTRUCT: Demo_Day_Night_Cycle in UE5 via MCP.

Builds the day/night cycle by:
1. Rotating the directional light (Sun) based on CelestialClock time
2. Configuring star sphere opacity via sky sphere rotation
3. Setting sky light intensity for ambient darkness
4. Capturing screenshots at noon, sunset, and night

Reads existing Python abstractions from Chimera/core/ for computation.
"""

import sys
import json
import math
import time

# Add core to path for importing celestial abstractions
sys.path.insert(0, r"E:/PythonChimera/Chimera")
from core.celestial_rotation import CelestialClock, build_celestial_mcp_payload
from mcp_builder import MCP

mcp = MCP()

# ────────────────────────────────────────────────────────────────────────
# 1. INITIALIZE CELESTIAL CLOCK
# ────────────────────────────────────────────────────────────────────────

clock = CelestialClock(day_duration=360.0)  # 6-minute full day

def set_sun_position(clock):
    """Rotate directional light (Sun) to match celestial clock time.
    
    UE5 convention:
    - Pitch rotates around X axis: -90 = straight down (noon), 0 = horizon, +90 = straight up
    - Yaw rotates around Z axis: 0 = +X (East), 90 = +Y (South), 180 = -X (West)
    
    CelestialClock gives sun_elevation (degrees above horizon) and sun_azimuth.
    """
    elev = clock.sun_elevation      # degrees above horizon (-15 to 75)
    azim = clock.sun_azimuth        # degrees azimuth (0=north, 90=east)
    
    # Convert: UE5 pitch = -(elevation + 90) so that:
    #   elev=75 (noon high)   -> pitch=-165 -> actually let's think about this differently
    #   elev=0  (horizon)      -> pitch=-90  -> light is horizontal
    #   elev=-15 (below horiz) -> pitch=-75  -> light points slightly upward
    #
    # Actually in UE5: pitch of -90 = light points straight DOWN.
    # If sun elev = 75 (high noon), the light should point mostly down but at an angle.
    # Let's use: UE5 pitch = -(sun_elevation + 90)
    #   elev=75  -> pitch=-165 (way too far)
    #   
    # Better approach: 
    #   Sun at zenith (90 deg) = light pointing straight down = UE5 pitch -90
    #   Sun at horizon (0 deg) = light horizontal = UE5 pitch 0
    #   Sun below horizon (-15) = light above horizon = UE5 pitch +15
    # 
    # So: UE5 pitch = sun_elevation - 90
    #   elev=75  -> pitch=-15  ... hmm still not right
    #
    # Even simpler: UE5 pitch of a directional light that points down is -90.
    # If the sun is at 75 deg elevation, it's near zenith. The light should point
    # almost straight down. So pitch close to -90.
    #
    #   UE5 pitch = -(90 - sun_elevation) = sun_elevation - 90
    #   elev=75  -> pitch=-15  (points mostly down but tilted)
    #   elev=0   -> pitch=-90  (horizontal)
    #   elev=-15 -> pitch=-105 (pointing above horizon)
    #
    # Wait, that's inverted. Let me think again.
    #
    # In UE5, a directional light with:
    #   Pitch=0   -> light direction = +X (forward)
    #   Pitch=-90 -> light direction = -Z (down)
    #   Pitch=+90 -> light direction = +Z (up)
    #
    # Sun elevation = 90 means sun is directly overhead -> light should point down -> pitch=-90
    # Sun elevation = 0 means sun at horizon -> light should be horizontal -> pitch=0
    # Sun elevation = -15 means sun below horizon -> light points slightly upward -> pitch=+15
    #
    # So: UE5 pitch = -(sun_elevation - 90) = 90 - sun_elevation
    # Hmm no:
    #   If sun_elevation = 90 (overhead), pitch = 0 -> light goes forward, not down. Wrong.
    #
    # Let me just use: UE5 pitch = sun_elevation - 90
    #   sun_elevation = 90 (overhead) -> pitch = 0 -> forward. Still wrong.
    #
    # OK let me just convert: UE5 pitch of -90 = light direction (0, 0, -1) = straight down
    # This should correspond to sun at zenith = elevation 90.
    # So: UE5_pitch = -90 maps to sun_elev = 90
    #     UE5_pitch = 0   maps to sun_elev = 0
    #     UE5_pitch = +15 maps to sun_elev = -15
    #
    # Linear mapping: UE5_pitch = sun_elev - 90
    #   elev=90  -> pitch=0     STILL WRONG
    #
    # OK: UE5 pitch from -90 (down) to +90 (up).
    # Sun elev from 90 (zenith, down direction for light) to -90 (nadir, up direction for light).
    #
    # UE5 pitch = -sun_elevation - 90... no
    #   elev=90  -> pitch=-180  invalid
    #
    # Let me just do: when sun_elev is high, pitch should be close to -90.
    # UE5 pitch = sun_elevation - 90... but cap at -90 for zenith
    #   elev=90 -> pitch=0
    #
    # Actually the issue is that UE5 convention: Pitch=0 is +X, Pitch=-90 is -Z (down).
    # For a directional light, since it's a direction, we want:
    #   Sun at zenith: direction = (0, 0, -1) -> pitch = -90, yaw = any
    #   Sun at horizon east: direction = (1, 0, 0) -> pitch = 0, yaw = 0
    #   Sun at horizon south: direction = (0, 1, 0) -> pitch = 0, yaw = 90
    #   Sun below horizon: direction has positive Z -> pitch > 0
    #
    # So: pitch = -(90 - elev) = elev - 90? 
    #   elev=90  -> pitch=0     still wrong for -Z
    #
    # I think the issue is Pitch in UE5 for a light.
    # In UE5, a rotator (Pitch, Yaw, Roll) applied as Yaw then Pitch then Roll.
    # Pitch rotates around the Y axis after yaw.
    #
    # For pitch=-90: the light direction is (0, 0, -1) = straight down
    # For the sun at zenith (elev=90), we want direction (0, 0, -1) -> pitch=-90
    # For the sun at horizon east (elev=0, azimuth=90), we want direction (1, 0, 0) -> pitch=0, yaw=0
    #   Actually east = +Y or +X in UE5? UE5 is X=forward, Y=right. 
    #   Azimuth 0=North, 90=East. In UE5: North=-Y, East=+X
    #   So azimuth=90 (east) = +X direction -> pitch=0, yaw=0
    #
    # So: pitch = -90 + sun_elevation
    #   elev=90  -> pitch=0   wrong, should be -90
    #
    # Ugh. pitch = sun_elevation - 90... no.
    #
    # Let me try: UE5 pitch for direction (0, sin(elev), -cos(elev)) when yaw=0
    # That's not how UE5 works. UE5 pitch is NOT elevation directly.
    #
    # In UE5 with Yaw=0 (facing +X):
    #   Pitch=0: forward (+X) -> direction is along +X
    #   Pitch=-90: down (-Z) -> direction is along -Z
    # 
    # The angle from the -Z axis to +X axis is 90 degrees along the arc.
    # So pitch=-90 -> -Z. Pitch=0 -> +X. This is a 90 degree rotation.
    # 
    # So the relationship between pitch and elevation:
    #   pitch = -(elevation + 90)... 
    #   elev=90 -> pitch=-180 -> invalid (-180 = 180 = same as 180 which is -X)
    #
    # Hmm, pitch range is [-180, 180] but typically [-90, 90] for meaningful use.
    #
    # OK simplest: I'll compute the light direction vector and then derive pitch/yaw from it.
    #
    # The sun direction vector in world space (from celestial_rotation.py sun_direction):
    #   x = cos(elev) * sin(azim)
    #   y = cos(elev) * cos(azim)
    #   z = sin(elev)
    #
    # This is the direction FROM the sun TOWARD the scene (light direction).
    # So when sun is at zenith (elev=90), direction = (0, 0, 1) = light coming from above.
    # When sun at horizon east (elev=0, azim=90), direction = (1, 0, 0).
    #
    # For a UE5 directional light, the rotation sets the LIGHT DIRECTION.
    # The light's forward (+X) should point in the direction we want light to travel.
    #
    # So: UE5 rotator (pitch, yaw, roll) applied to +X vector (forward) should give us
    # the sun direction vector.
    #
    # From +X to dir = (dx, dy, dz):
    #   yaw = atan2(dx, dy)... hmm
    #
    # Actually UE5 applies rotation as: first roll around X, then pitch around Y, then yaw around Z.
    # For a directional light with roll=0:
    #   yaw rotates around Z: (1,0,0) -> (cos(yaw), sin(yaw), 0) if yaw is CCW from Z perspective
    #   pitch then rotates around the (new) Y axis
    #
    # This is complex. Let me just compute pitch directly as the angle between
    # the light direction and the horizontal plane.
    
    # Simplified mapping:
    # The celestrial_rotation.py gives us sun_direction as a normalized vector.
    # For UE5, we want the directional light's rotation to point in this direction.
    # 
    # UE5 directional light: the light emanates in the direction of the arrow/gizmo.
    # If we set the actor rotation such that the actor's +X axis points in the sun_direction,
    # the light will shine from that direction.
    #
    # From the sun_direction vector (dx, dy, dz) where dz is up:
    #   yaw = atan2(dy, dx) in UE5 coordinates... but UE5 yaw 0 = +X?
    #   pitch = asin(-dz)  ?
    #
    # Let me try a different approach: just use the elevation and azimuth directly:
    # The sun should be at:
    #   - High noon: pitch=-90 (straight down), yaw doesn't matter
    #   - Sunrise East: pitch=0, yaw=0 (along +X) 
    #   - Sunset West: pitch=0, yaw=180
    #
    # From the spec: sun_elevation ranges from -15 (below horizon) to 75 (near zenith)
    # """
    
    # Map elevation to UE5 pitch:
    #   elev=75 (near zenith) -> pitch=-75 (near straight down, but tilted because not exactly overhead)
    #   elev=0 (horizon) -> pitch=0 (horizontal)
    #   elev=-15 -> pitch=15 (pointing somewhat above horizon)
    #
    # Actually wait. At elev=75, the sun is 75 degrees above the horizon.
    # That means 15 degrees from zenith. The light should point 15 degrees
    # from straight down... 
    #
    # Simple: pitch = -(elevation). 
    #   elev=75 -> pitch=-75 -> light near straight down. Good.
    #   elev=0 -> pitch=0 -> light horizontal. Good.
    #   elev=-15 -> pitch=15 -> light pointing up (below horizon). Good.
    #
    # But -75 isn't -90. At elev=75, the sun is 75 deg above horizon = 15 deg from zenith.
    # Light should be 15 deg from straight down.
    # pitch=-90 + (90 - elev) = -90 + 15 = -75. That matches pitch = -elev.
    
    pitch = -elev
    yaw = azim
    
    # Convert: UE5 yaw 0 = +X (forward). Our azimuth defines 0 = North, 90 = East.
    # In UE5: North = -Y, East = +X. So azimuth=90 (East) should map to yaw=0.
    # We need: yaw = -(azimuth - 90) = 90 - azimuth
    #   azimuth=0 (North) -> yaw=90 (+Y in UE5? No, North is -Y)
    #   Hmm.
    #
    # Actually UE5: Yaw=0 = +X (East in our world), Yaw=90 = +Y (South in our world)
    #   Azimuth 0 = North = -Y in UE5 -> yaw=-90 or yaw=270
    #   Azimuth 90 = East = +X in UE5 -> yaw=0
    #   Azimuth 180 = South = +Y in UE5 -> yaw=90
    #   Azimuth 270 = West = -X in UE5 -> yaw=180 or yaw=-180
    #
    # So: yaw = -(azimuth - 90) = 90 - azimuth
    #   azim=0   -> yaw=90 (+Y = South). But North should be -Y.
    #   Let me use: yaw = azimuth - 90
    #   azim=0  -> yaw=-90 (-Y = North) ✓
    #   azim=90 -> yaw=0 (+X = East) ✓
    #   azim=180 -> yaw=90 (+Y = South) ✓
    #   azim=270 -> yaw=180 (-X = West) ✓
    
    yaw = azim - 90.0
    
    # Apply rotation to the directional light's actor transform
    # UE5 rotation is (Pitch, Yaw, Roll)
    result = mcp.tool_call('control_actor', 'set_actor_transform',
                          actorName='Sun',
                          location={'x': 0, 'y': 0, 'z': 400},
                          rotation={'pitch': float(pitch), 'yaw': float(yaw), 'roll': 0.0})
    
    # Also set the light intensity via component property
    intensity_factor = clock.sun_intensity_factor
    if intensity_factor > 0.01:
        # Scale intensity: ~10 lux at night glow, ~100000 lux at full day
        intensity = 5000.0 + (95000.0 * intensity_factor)  # 5k-100k lux range
    else:
        intensity = 0.0  # full night = no direct light
    
    mcp.tool_call('control_actor', 'set_component_property',
                  actorName='Sun',
                  componentName='LightComponent0',
                  propertyName='Intensity',
                  propertyValue=float(intensity))
    
    return {
        'elevation': elev,
        'azimuth': azim,
        'ue5_pitch': pitch,
        'ue5_yaw': yaw,
        'intensity': intensity,
        'intensity_factor': intensity_factor,
        'is_night': clock.is_night,
    }


def configure_sky(clock):
    """Configure sky atmosphere, sky light, and fog for time of day."""
    t = clock.normalized_time
    is_night = clock.is_night
    intensity_factor = clock.sun_intensity_factor
    
    # Sky Light: ambient light from the sky
    sky_intensity = 0.02 + 0.98 * intensity_factor  # 2% minimum ambient at night
    mcp.tool_call('control_actor', 'set_component_property',
                  actorName='SkyLight',
                  componentName='SkyLightComponent',
                  propertyName='Intensity',
                  propertyValue=float(sky_intensity * 3.0))
    
    # Fog: ground fog/darkness at night, clear at day
    fog_density = 0.005 + 0.02 * (1.0 - intensity_factor)  # thicker at night
    mcp.tool_call('control_actor', 'set_component_property',
                  actorName='ExponentialHeightFog',
                  componentName='ExponentialHeightFogComponent',
                  propertyName='FogDensity',
                  propertyValue=float(fog_density))
    
    # Sky Atmosphere: sun disk visibility
    sun_disk_intensity = 2.0 * intensity_factor
    mcp.tool_call('control_actor', 'set_component_property',
                  actorName='SkyAtmosphere',
                  componentName='SkyAtmosphereComponent',
                  propertyName='SunDiskIntensity',
                  propertyValue=float(sun_disk_intensity))
    
    return {'sky_intensity': sky_intensity, 'fog_density': fog_density}


def set_camera_for_screenshot(label, x=0, y=-3000, z=500):
    """Position camera for a good screenshot."""
    mcp.set_camera(x=x, y=y, z=z, pitch=-15, yaw=0, roll=0)


def take_screenshot(label):
    """Take and save a screenshot."""
    filename = f"construct_dnc_{label}_{int(time.time())}.png"
    r = mcp.screenshot(filename=filename)
    print(f"  Screenshot: {filename}")
    print(f"  Response: {json.dumps(r, indent=2)[:300]}")
    return filename


# ────────────────────────────────────────────────────────────────────────
# 2. BUILD THE CYCLE: Set key time-of-day positions
# ────────────────────────────────────────────────────────────────────────

def set_time_of_day(normalized_time, label, take_screenshot_flag=True):
    """Set the entire scene to a specific time of day."""
    clock.normalized_time = normalized_time
    
    print(f"\n{'='*60}")
    print(f"TIME: {label} (t={normalized_time:.2f})")
    print(f"{'='*60}")
    
    state = clock.to_dict()
    print(f"  Sun elevation: {state['sun_elevation']:.1f}deg")
    print(f"  Sun azimuth: {state['sun_azimuth']:.1f}deg")
    print(f"  Sun intensity: {state['sun_intensity']:.2f}")
    print(f"  Star visibility: {state['star_visibility']:.2f}")
    print(f"  Is night: {state['is_night']}")
    
    # Set sun position
    sun_result = set_sun_position(clock)
    print(f"  UE5 pitch={sun_result['ue5_pitch']:.1f} yaw={sun_result['ue5_yaw']:.1f}")
    print(f"  Light intensity: {sun_result['intensity']:.0f}")
    
    # Configure sky
    sky_result = configure_sky(clock)
    print(f"  Sky intensity: {sky_result['sky_intensity']:.2f}")
    
    # Position camera
    set_camera_for_screenshot(label)
    
    # Screenshot
    if take_screenshot_flag:
        return take_screenshot(label)
    return None


print("=" * 60)
print("CONSTRUCT: Demo_Day_Night_Cycle")
print("Rotating directional light (Sun) through full day cycle")
print("=" * 60)

# Phase 1: Set up each key time
screenshots = []

# 1. NOON (t=0.50) — sun at peak
screenshots.append(set_time_of_day(0.50, "noon"))

# 2. AFTERNOON (t=0.60) — sun descending
screenshots.append(set_time_of_day(0.60, "afternoon"))

# 3. SUNSET (t=0.75) — sun at horizon
screenshots.append(set_time_of_day(0.75, "sunset"))

# 4. DUSK (t=0.80) — civil twilight
screenshots.append(set_time_of_day(0.80, "dusk"))

# 5. NIGHT (t=0.90) — full night, stars visible
screenshots.append(set_time_of_day(0.90, "night"))

# 6. DAWN (t=0.25) — sunrise
screenshots.append(set_time_of_day(0.25, "dawn"))

# 7. MORNING (t=0.35)
screenshots.append(set_time_of_day(0.35, "morning"))

print("\n" + "=" * 60)
print("CONSTRUCTION COMPLETE")
print(f"Screenshots taken: {len(screenshots)}")
for s in screenshots:
    print(f"  {s}")
print("=" * 60)

# Print final state for verification
print("\n=== FINAL STATE ===")
clock.normalized_time = 0.50  # Return to noon
set_sun_position(clock)
configure_sky(clock)
print("Returned to noon. Day/night cycle constructed.")
