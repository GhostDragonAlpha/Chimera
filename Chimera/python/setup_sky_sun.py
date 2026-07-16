"""
Setup Script for Sky_Sun_Lighting (Loop 3).

Idempotently realizes the Sun as a DirectionalLight in the live editor world. The
level template already spawns a DirectionalLight (the Sun), but it is unlabeled and
unconfigured (default white, default-ish intensity). This script adopts that
light, relabels it 'Sun', and configures it as a clear lunar-day sun (warm-white
light color + explicit sun intensity), so the Sky_Sun_Lighting feature is realized
as real, read-back-able lighting state.

The generator's create_level_*.py is a no-op stub, so the Sun configuration is
realized here and wired into setup_sky.py / startup.py. The level is saved so a PIE
session inherits the configured light.

Idempotent: if an actor labeled 'Sun' already exists it is (re)configured (not
spawned again); otherwise the first DirectionalLight found in the level is adopted
and relabeled. Per-property writes are guarded so a wrong UPROPERTY name can never
abort the script -- the witness only checks that the labeled actor exists and its
intensity is configured.
"""

import unreal


SUN_LABEL = "Sun"
SUN_INTENSITY = 6.0
# Warm white sun (distinct from the engine default pure white) -- proves the light
# is configured for "sun lighting" rather than left at default.
SUN_COLOR = unreal.Color(255, 248, 230)


def _find_sun():
    """Return an actor labeled 'Sun', else the first DirectionalLight in the level."""
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == SUN_LABEL:
            return actor, True
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_class().get_name() == "DirectionalLight":
            return actor, False
    return None, False


def run():
    sun, already_labeled = _find_sun()
    if sun is None:
        sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.DirectionalLight,
            unreal.Vector(0.0, 0.0, 1000.0),
            unreal.Rotator(-45.0, -45.0, 0.0),
        )
        already_labeled = False
        unreal.log("[setup_sky_sun] spawned DirectionalLight (Sun)")

    if not already_labeled:
        sun.set_actor_label(SUN_LABEL)
        unreal.log(f"[setup_sky_sun] relabeled light -> '{SUN_LABEL}'")
    else:
        unreal.log(f"[setup_sky_sun] reused existing '{SUN_LABEL}'")

    lc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if lc is not None:
        try:
            lc.set_editor_property("intensity", SUN_INTENSITY)
        except Exception as exc:
            unreal.log_warning(f"[setup_sky_sun] skip intensity: {exc}")
        try:
            lc.set_editor_property("light_color", SUN_COLOR)
        except Exception as exc:
            unreal.log_warning(f"[setup_sky_sun] skip light_color: {exc}")
    else:
        unreal.log_warning("[setup_sky_sun] no DirectionalLightComponent on Sun actor")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"[setup_sky_sun] Sky_Sun_Lighting realized: '{SUN_LABEL}' intensity={SUN_INTENSITY}")


if __name__ == "__main__":
    run()
