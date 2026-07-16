"""
Setup Script for Sky_Starfield (Loop 3, Step 5).

Idempotently creates the star-sphere actor labeled 'SM_StarSphere' carrying
MAT_Starfield, and ensures MAT_Starfield's T_Starfield texture sample is wired to
EmissiveColor (and BaseColor). Designed to run in the EDITOR world (via
PythonScriptPlugin startup, or system_control.execute_python); the level is saved
so a PIE session inherits the actor.

This script is the realization path for the Loop 3 Sky set: it was previously
orphaned (startup.py never called it), so the star sphere was never built into the
live level. It is now wired into setup_sky.py (run automatically on editor launch)
and into startup.py.

Idempotent: if an actor labeled SM_StarSphere already exists, only the material is
(re)applied and the level is saved -- no duplicate actors are spawned.
"""

import os
import unreal


MAT_PATH = "/Game/Celestial/Materials/MAT_Starfield/MAT_Starfield"
TEX_PATH = "/Game/Celestial/Textures/T_Starfield/T_Starfield"
STAR_SPHERE_LABEL = "SM_StarSphere"
STAR_SPHERE_MESH = "/Engine/BasicShapes/Sphere.Sphere"
# BasicShapes Sphere has radius ~50 UU; scale up so the dome encloses the play area.
STAR_SPHERE_SCALE = 4000.0
# Wiring the material creates a new texture node each run; do it ONCE and remember
# via a sentinel so the PythonScriptPlugin auto-run (every editor launch) stays clean.
_WIRE_SENTINEL = r"E:/PythonChimera/Chimera/Saved/.sky_starfield_wired"


def _find_actor_by_label(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def _ensure_material_wiring(material):
    """Connect a T_Starfield texture sample to EmissiveColor (and BaseColor).

    Material.expressions is a protected property and cannot be read via
    get_editor_property, so we create a fresh TextureSampleParameter2D and wire it.
    Connecting to an input pin replaces any existing link, so this is effectively
    idempotent for the EMISSIVE/BASE_COLOR inputs (at the cost of a few dangling
    nodes in the material graph across many launches -- cosmetic, non-breaking).
    """
    mel = unreal.MaterialEditingLibrary
    tex = unreal.load_asset(TEX_PATH)

    target = mel.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0
    )
    if tex is not None:
        try:
            target.set_editor_property("texture", tex)
            target.set_editor_property("parameter_name", "StarTexture")
        except Exception:
            pass

    # Wire the texture RGB to EmissiveColor (Unlit shows this) and BaseColor.
    mel.connect_material_property(target, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(target, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)


def run():
    material = unreal.load_asset(MAT_PATH)
    if material is None:
        unreal.log_warning(f"[setup_starfield] MAT_Starfield not found at {MAT_PATH}")
        return

    # MAT_Starfield is a purpose-built starfield material (Unlit / two-sided); only
    # the texture->emissive wiring was missing. Best-effort property ensures are
    # guarded so a wrong UPROPERTY name can never abort actor creation. The wiring
    # is done ONCE (sentinel-guarded) so repeated editor launches don't accumulate
    # dangling texture nodes in the material graph.
    for _prop, _val in (
        ("two_sided", True),
        ("bIsTwoSided", True),
        ("blend_mode", unreal.BlendMode.BLEND_OPAQUE),
        ("shading_model", unreal.MaterialShadingModel.MSM_UNLIT),
    ):
        try:
            material.set_editor_property(_prop, _val)
        except Exception:
            pass
    if not os.path.exists(_WIRE_SENTINEL):
        try:
            _ensure_material_wiring(material)
            with open(_WIRE_SENTINEL, "w") as _f:
                _f.write("wired")
            unreal.log("[setup_starfield] MAT_Starfield texture wiring applied (once)")
        except Exception as exc:
            unreal.log_warning(f"[setup_starfield] material wiring skipped: {exc}")
    else:
        unreal.log("[setup_starfield] MAT_Starfield already wired (sentinel present)")

    sphere = _find_actor_by_label(STAR_SPHERE_LABEL)
    if sphere is None:
        sphere = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(0.0, 0.0, 0.0),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        sphere.set_actor_label(STAR_SPHERE_LABEL)
        smc = sphere.get_component_by_class(unreal.StaticMeshComponent)
        if smc is not None:
            mesh = unreal.load_asset(STAR_SPHERE_MESH)
            if mesh is not None:
                smc.set_static_mesh(mesh)
            sphere.set_actor_scale3d(
                unreal.Vector(STAR_SPHERE_SCALE, STAR_SPHERE_SCALE, STAR_SPHERE_SCALE)
            )
            smc.set_material(0, material)
        unreal.log(f"[setup_starfield] spawned star sphere '{STAR_SPHERE_LABEL}'")
    else:
        smc = sphere.get_component_by_class(unreal.StaticMeshComponent)
        if smc is not None:
            smc.set_material(0, material)
        unreal.log(f"[setup_starfield] reused existing star sphere '{STAR_SPHERE_LABEL}'")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"[setup_starfield] Sky_Starfield realized: '{STAR_SPHERE_LABEL}' with MAT_Starfield")


if __name__ == "__main__":
    run()
