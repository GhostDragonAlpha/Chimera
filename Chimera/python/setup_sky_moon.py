"""
Setup Script for Sky_Moon_Model + Sky_Moon_Material (Loop 3).

Idempotently realizes the Moon celestial body in the live editor world: a static
mesh actor labeled 'SM_Moon' carrying the SM_Moon mesh with the MAT_Moon_Regolith
PBR material, placed at a sky position offset from Earth so the two read as a
matched pair.

This is the realization path for both Sky features:
  * Sky_Moon_Model     -> the SM_Moon actor (mesh + transform)
  * Sky_Moon_Material  -> MAT_Moon_Regolith applied to that actor's static mesh

Mirrors Python/setup_sky_earth.py (tb-0099). The generator's create_level_*.py is a
no-op stub, so the Moon is realized here and wired into setup_sky.py / startup.py.
The level is saved so a PIE session inherits the actor.

Asset facts (verified via editor load): SM_Moon sphere radius 100 UU, SM_Earth
sphere radius 500 UU (5:1). A Moon scale of 0.8 (visible radius ~80 UU) keeps the
correct Earth:Moon size relationship while both remain visible sky bodies.

Idempotent: if an actor labeled SM_Moon already exists, its material/transform are
(re)applied and the level is saved -- no duplicate actors are spawned.
"""

import unreal


MOON_LABEL = "SM_Moon"
MOON_MESH = "/Game/Celestial/SM_Moon"
MOON_MATERIAL = "/Game/Celestial/Materials/MAT_Moon_Regolith"
MOON_LOCATION = unreal.Vector(68000.0, 0.0, 39000.0)
MOON_SCALE = 0.8


def _find_actor_by_label(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def run():
    mesh = unreal.load_asset(MOON_MESH)
    material = unreal.load_asset(MOON_MATERIAL)
    if mesh is None:
        unreal.log_warning(f"[setup_sky_moon] SM_Moon mesh not found at {MOON_MESH}")
        return
    if material is None:
        unreal.log_warning(f"[setup_sky_moon] MAT_Moon_Regolith not found at {MOON_MATERIAL}")
        return

    actor = _find_actor_by_label(MOON_LABEL)
    if actor is None:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            MOON_LOCATION,
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        actor.set_actor_label(MOON_LABEL)
        unreal.log(f"[setup_sky_moon] spawned '{MOON_LABEL}'")
    else:
        unreal.log(f"[setup_sky_moon] reused existing '{MOON_LABEL}'")

    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc is not None:
        smc.set_static_mesh(mesh)
        smc.set_material(0, material)
    actor.set_actor_scale3d(unreal.Vector(MOON_SCALE, MOON_SCALE, MOON_SCALE))

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"[setup_sky_moon] Sky_Moon_Model + Sky_Moon_Material realized: '{MOON_LABEL}' with {MOON_MATERIAL}")


if __name__ == "__main__":
    run()
