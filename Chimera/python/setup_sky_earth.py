"""
Setup Script for Sky_Earth_Model + Sky_Earth_Material (Loop 3).

Idempotently realizes the Earth celestial body in the live editor world: a static
mesh actor labeled 'SM_Earth' carrying the SM_Earth mesh with the MAT_Earth PBR
material, placed at a distant sky position so it reads as the "blue marble".

This is the realization path for both Sky features:
  * Sky_Earth_Model     -> the SM_Earth actor (mesh + transform)
  * Sky_Earth_Material  -> MAT_Earth applied to that actor's static mesh component

The generator's create_level_*.py script is a no-op stub, so the Earth body is
realized here (like tb-0092's starfield/atmosphere) and wired into setup_sky.py /
startup.py so it is built automatically on editor launch. The level is saved so a
PIE session inherits the actor.

Canonical reference: Python/create_earth_celestial_automation.py (authoring of the
SM_Earth mesh + MAT_Earth material + placement at (50000,0,30000), scale 3.0).

Idempotent: if an actor labeled SM_Earth already exists, its material/transform are
(re)applied and the level is saved -- no duplicate actors are spawned.
"""

import unreal


EARTH_LABEL = "SM_Earth"
EARTH_MESH = "/Game/Celestial/SM_Earth"
# MAT_Earth is packaged as a folder asset: the .uasset lives one level deeper than
# the intuitive path. Try both so the script is robust to either layout.
EARTH_MATERIAL_CANDIDATES = [
    "/Game/Celestial/Materials/MAT_Earth/MAT_Earth",
    "/Game/Celestial/Materials/MAT_Earth",
]
EARTH_LOCATION = unreal.Vector(50000.0, 0.0, 30000.0)
EARTH_SCALE = 3.0


def _resolve_asset(candidates):
    for path in candidates:
        a = unreal.load_asset(path)
        if a is not None:
            return a, path
    return None, None


def _find_actor_by_label(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def run():
    mesh = unreal.load_asset(EARTH_MESH)
    material, material_path = _resolve_asset(EARTH_MATERIAL_CANDIDATES)
    if mesh is None:
        unreal.log_warning(f"[setup_sky_earth] SM_Earth mesh not found at {EARTH_MESH}")
        return
    if material is None:
        unreal.log_warning(f"[setup_sky_earth] MAT_Earth not found (tried {EARTH_MATERIAL_CANDIDATES})")
        return

    actor = _find_actor_by_label(EARTH_LABEL)
    if actor is None:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            EARTH_LOCATION,
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        actor.set_actor_label(EARTH_LABEL)
        unreal.log(f"[setup_sky_earth] spawned '{EARTH_LABEL}'")
    else:
        unreal.log(f"[setup_sky_earth] reused existing '{EARTH_LABEL}'")

    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc is not None:
        smc.set_static_mesh(mesh)
        smc.set_material(0, material)
    actor.set_actor_scale3d(unreal.Vector(EARTH_SCALE, EARTH_SCALE, EARTH_SCALE))

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"[setup_sky_earth] Sky_Earth_Model + Sky_Earth_Material realized: '{EARTH_LABEL}' with {material_path}")


if __name__ == "__main__":
    run()
