"""Build the emergent world level from decoded training parameters.
Run this in UE5 editor Python console (Window > Developer Tools > Python).
Opens the emergent_world level, spawns all actors, sets up lighting, saves.
"""

import unreal
import json, os, math, sys

CONTENT_DIR = unreal.Paths.project_content_dir()
LEVEL_PATH = "/Game/Levels/emergent_world/emergent_world"
DECODED_DIR = os.path.join(unreal.Paths.project_dir(), "docs/decoded")


def load_decoded():
    """Load all decoded JSON files."""
    decoded = {}
    if not os.path.isdir(DECODED_DIR):
        print(f"Decoded dir not found: {DECODED_DIR}")
        return decoded
    for f in os.listdir(DECODED_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(DECODED_DIR, f)) as fh:
                    decoded[f.replace(".json", "")] = json.load(fh)
            except Exception as e:
                print(f"  Error loading {f}: {e}")
    print(f"Loaded {len(decoded)} decoded rungs")
    return decoded


def _get(d, *keys, default=None):
    genome = d.get("genome", d)
    for k in keys:
        v = genome.get(k, d.get(k))
        if v is not None:
            return v
    return default


def spawn_static_mesh(name, mesh_path, location, scale=(1,1,1), rotation=(0,0,0)):
    """Spawn a static mesh actor in the level."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor_loc = unreal.Vector(location[0], location[1], location[2])
    actor_rot = unreal.Rotator(rotation[0], rotation[1], rotation[2])
    actor_scale = unreal.Vector(scale[0], scale[1], scale[2])
    
    mesh = unreal.load_asset(name=mesh_path)
    if mesh is None:
        print(f"  [ERR] Cannot load mesh: {mesh_path}")
        return None
    
    actor = actor_subsystem.spawn_actor_from_object(mesh, actor_loc, actor_rot)
    if actor is None:
        print(f"  [ERR] Cannot spawn: {name}")
        return None
    
    actor.set_actor_label(name)
    actor.set_actor_scale3d(actor_scale)
    print(f"  [OK] {name} at {location}")
    return actor


def spawn_blueprint(name, bp_path, location, scale=(1,1,1), rotation=(0,0,0)):
    """Spawn a Blueprint actor."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor_loc = unreal.Vector(location[0], location[1], location[2])
    actor_rot = unreal.Rotator(rotation[0], rotation[1], rotation[2])
    actor_scale = unreal.Vector(scale[0], scale[1], scale[2])
    
    bp = unreal.load_asset(name=bp_path)
    if bp is None:
        print(f"  [ERR] Cannot load Blueprint: {bp_path}")
        return None
    
    actor = actor_subsystem.spawn_actor_from_object(bp, actor_loc, actor_rot)
    if actor is None:
        print(f"  [ERR] Cannot spawn Blueprint actor: {name}")
        return None
    
    actor.set_actor_label(name)
    actor.set_actor_scale3d(actor_scale)
    print(f"  [OK] {name} at {location}")
    return actor


def spawn_light(name, light_type, location, color=(1,1,1), intensity=5000, 
                rotation=(0,0,0), attenuation=5000):
    """Spawn a light actor using the actor subsystem."""
    actor_loc = unreal.Vector(location[0], location[1], location[2])
    actor_rot = unreal.Rotator(rotation[0], rotation[1], rotation[2])
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    
    actor_class = None
    if light_type == "DirectionalLight":
        actor_class = unreal.DirectionalLight.static_class()
    elif light_type == "PointLight":
        actor_class = unreal.PointLight.static_class()
    elif light_type == "ExponentialHeightFog":
        actor_class = unreal.ExponentialHeightFog.static_class()
    elif light_type == "SkyLight":
        actor_class = unreal.SkyLight.static_class()
    
    if actor_class is None:
        print(f"  [ERR] Unknown light type: {light_type}")
        return None
    
    actor = actor_subsystem.spawn_actor_from_class(actor_class, actor_loc, actor_rot)
    if actor is None:
        print(f"  [ERR] Cannot spawn light: {light_type}")
        return None
    
    actor.set_actor_label(name)
    
    # Set light properties
    light_component = actor.get_component_by_class(unreal.LightComponent)
    if light_component:
        light_component.set_editor_property("intensity", intensity)
        col = unreal.Color(int(color[0]*255), int(color[1]*255), int(color[2]*255), 255)
        light_component.set_editor_property("light_color", col)
        # Attenuation is PointLightComponent only
        pc = actor.get_component_by_class(unreal.PointLightComponent)
        if pc and attenuation:
            pc.set_editor_property("attenuation_radius", attenuation)
    
    print(f"  [OK] {name} at {location}")
    return actor


def build_sky():
    """Add sky sphere, atmospheric fog, and height fog."""
    print("\n=== Building Sky ===")
    
    # Sky sphere
    spawn_static_mesh("SkySphere", 
        "/Engine/Blueprints/Sky/BP_SkySphere.BP_SkySphere",
        (0, 0, 0), scale=(100, 100, 100))
    
    # Exponential height fog
    fog = spawn_light("AtmosphereFog", "ExponentialHeightFog", (0, 0, 0),
                      color=(0.5, 0.6, 0.8), intensity=0.002)
    if fog:
        fog_component = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if fog_component:
            fog_component.set_editor_property("fog_density", 0.002)
            fog_component.set_editor_property("fog_height_falloff", 0.2)
            fog_component.set_editor_property("start_distance", 10000)


def build_sun(decoded):
    """Build the sun — warm directional light with atmosphere."""
    print("\n=== Building Sun ===")
    
    ss = decoded.get("solar_system", {})
    star = ss.get("star", {})
    mass = star.get("mass_frac", 0.98)
    
    # Warm yellow sun for G-type star
    if mass > 0.9:
        color = (1.0, 0.85, 0.5)
        intensity = 10.0
    elif mass > 0.5:
        color = (1.0, 0.75, 0.4)
        intensity = 7.0
    else:
        color = (0.8, 0.6, 0.3)
        intensity = 4.0
    
    sun = spawn_light("SunLight", "DirectionalLight", (0, 0, 2000),
                      color=color, intensity=intensity, rotation=(330, -45, 0))
    if sun:
        light_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if light_comp:
            try:
                light_comp.set_editor_property("cast_shadows", True)
                light_comp.set_editor_property("light_source_angle", 0.5)
            except:
                pass


def build_terrain(decoded):
    """Build the ground plane."""
    print("\n=== Building Terrain ===")
    
    gt = decoded.get("ground_terrain", {})
    extent = _get(gt, "extent", "Extent", default=(5000, 5000, 100))
    origin = _get(gt, "origin", "Origin", default=(0, 0, -50))
    
    # Large ground plane
    spawn_static_mesh("Ground",
        "/Engine/BasicShapes/Plane.Plane",
        (origin[0], origin[1], extent[2]),
        scale=(extent[0] / 100, extent[1] / 100, 1))


def build_resources(decoded):
    """Scatter resource pickups."""
    print("\n=== Building Resources ===")
    
    br = decoded.get("biome_resources", {})
    n_types = int(_get(br, "n_types", "n_types", default=7))
    
    for i in range(min(n_types, 12)):
        angle = i * 2 * math.pi / n_types
        dist = 300 + i * 150
        x = math.cos(angle) * dist
        y = math.sin(angle) * dist
        hue = [0.3 + (i % 3) * 0.2, 0.5, 0.2]
        
        spawn_static_mesh(f"Resource_{i}",
            "/Engine/BasicShapes/Sphere.Sphere",
            (x, y, 50), scale=(0.5, 0.5, 0.5))


def build_shelter(decoded):
    """Build shelter with zone indicator."""
    print("\n=== Building Shelter ===")
    
    st = decoded.get("shelter_threshold", {})
    pos = _get(st, "pos", "pos", default=(0, -800, 0))
    radius = _get(st, "radius", "radius", default=300)
    
    # Shelter platform
    spawn_static_mesh("Shelter",
        "/Engine/BasicShapes/Cylinder.Cylinder",
        (pos[0], pos[1], 0),
        scale=(radius / 50, radius / 50, 0.1))
    
    # Shelter light (blue, welcoming)
    spawn_light("ShelterLight", "PointLight",
        (pos[0], pos[1], 200),
        color=(0.2, 0.8, 1.0), intensity=5000, attenuation=radius * 2)


def build_npcs(decoded):
    """Place NPCs around shelter."""
    print("\n=== Building NPCs ===")
    
    ns = decoded.get("npc_social", {})
    n_npcs = int(_get(ns, "n_npcs", "n_npcs", default=3))
    
    for i in range(min(n_npcs, 6)):
        angle = i * 2 * math.pi / n_npcs + 0.5
        dist = 600 + i * 100
        x = math.cos(angle) * dist
        y = math.sin(angle) * dist
        
        # NPC spawn point (cylinder marker)
        spawn_static_mesh(f"NPC_{i}",
            "/Engine/BasicShapes/Cylinder.Cylinder",
            (x, y, 50), scale=(0.3, 0.3, 1))


def build_beacon(decoded):
    """Build the beacon — Mirror terminal."""
    print("\n=== Building Beacon ===")
    
    bn = decoded.get("beacon_narrative", {})
    sig = decoded.get("beacon_narrative_signal", decoded.get("latest", {}))
    
    pos = _get(bn, "pos", "pos", default=(2000, 0, 0))
    height = _get(bn, "height", "height", default=50)
    pulse_0 = _get(sig, "pulse_rate_0", default=0.18)
    pulse_3 = _get(sig, "pulse_rate_3", default=1.55)
    
    # Beacon tower
    spawn_static_mesh("BeaconTower",
        "/Engine/BasicShapes/Cylinder.Cylinder",
        (pos[0], pos[1], pos[2] + height / 2),
        scale=(0.3, 0.3, height / 100))
    
    # Beacon light (red at 0 helps)
    spawn_light("BeaconSignal",
        "PointLight",
        (pos[0], pos[1], pos[2] + height),
        color=(1.0, 0.2, 0.1), intensity=10000, attenuation=5000)
    
    # Light sphere on top
    spawn_static_mesh("BeaconLight",
        "/Engine/BasicShapes/Sphere.Sphere",
        (pos[0], pos[1], pos[2] + height),
        scale=(2, 2, 2))


def delete_debug_actors():
    """Remove any leftover debug/placeholder actors."""
    print("\n=== Cleaning Up ===")
    actors_to_delete = []
    
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    for actor in all_actors:
        label = actor.get_actor_label()
        if label.startswith("TextRenderActor") or "TextRender" in str(type(actor)):
            actors_to_delete.append(actor)
    
    for a in actors_to_delete:
        actor_subsystem.destroy_actor(a)
    if actors_to_delete:
        print(f"  Removed {len(actors_to_delete)} debug actors")


def build_level():
    """Main build function."""
    print("=" * 50)
    print("BUILDING EMERGENT WORLD")
    print("=" * 50)
    
    # Load decoded parameters
    decoded = load_decoded()
    
    # Open the level
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_path = LEVEL_PATH
    if not level_subsystem.load_level(level_path):
        print(f"Level not found at {level_path}, using current level")
    
    # Delete old junk
    delete_debug_actors()
    
    # Build each system (tolerate individual failures)
    for fn, args, name in [
        (build_sun, (decoded,), "Sun"),
        (build_sky, (), "Sky"),
        (build_terrain, (decoded,), "Terrain"),
        (build_resources, (decoded,), "Resources"),
        (build_shelter, (decoded,), "Shelter"),
        (build_npcs, (decoded,), "NPCs"),
        (build_beacon, (decoded,), "Beacon"),
    ]:
        try:
            fn(*args)
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
    
    # Save
    level_subsystem.save_current_level()
    print("\n" + "=" * 50)
    print("LEVEL BUILD COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    build_level()
