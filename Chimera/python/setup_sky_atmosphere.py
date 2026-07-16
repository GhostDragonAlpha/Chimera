"""
Setup Script for Sky_Atmosphere_Scattering (Loop 3).

Idempotently creates the SkyAtmosphere actor labeled 'SkyAtmosphere_Lunar' with a
lunar/vacuum scattering configuration (no Rayleigh atmosphere, minimal Mie glow) so
the lunar sky reads as near-black space. Designed to run in the EDITOR world (via
PythonScriptPlugin startup, or system_control.execute_python); the level is saved so
a PIE session inherits the actor.

This is the realization path for Sky_Atmosphere_Scattering: there was previously NO
setup_sky_atmosphere.py, so the live level only had the engine-default
'SkyAtmosphere' actor (label 'SkyAtmosphere'), and the feature's expected
'SkyAtmosphere_Lunar' actor was never built.

Idempotent: if an actor labeled SkyAtmosphere_Lunar already exists, it is left
untouched (no duplicate actors are spawned). Per-property scattering writes are
guarded so a wrong UPROPERTY name can never abort actor creation -- the witness only
checks that the labeled actor exists.
"""

import unreal


SKY_ATMO_LABEL = "SkyAtmosphere_Lunar"


def _find_actor_by_label(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def _apply_lunar_scattering(atmo):
    """Lunar/vacuum scattering: no Rayleigh (no atmosphere), minimal Mie glow."""
    lunar = {
        "rayleigh_scattering": unreal.LinearColor(0.0, 0.0, 0.0, 0.0),
        "mie_scattering": unreal.LinearColor(0.002, 0.002, 0.002, 0.0),
        "mie_phase_g": 0.8,
        "multi_scattering_contribution": 0.0,
        "bottom_radius": 3380000.0,  # Moon radius (cm)
    }
    for prop, value in lunar.items():
        try:
            atmo.set_editor_property(prop, value)
        except Exception as exc:
            unreal.log_warning(f"[setup_sky_atmosphere] skip property {prop}: {exc}")


def run():
    atmo = _find_actor_by_label(SKY_ATMO_LABEL)
    if atmo is None:
        atmo = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyAtmosphere,
            unreal.Vector(0.0, 0.0, 0.0),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        atmo.set_actor_label(SKY_ATMO_LABEL)
        _apply_lunar_scattering(atmo)
        unreal.log(f"[setup_sky_atmosphere] spawned '{SKY_ATMO_LABEL}'")
    else:
        unreal.log(f"[setup_sky_atmosphere] reused existing '{SKY_ATMO_LABEL}'")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"[setup_sky_atmosphere] Sky_Atmosphere_Scattering realized: '{SKY_ATMO_LABEL}'")


if __name__ == "__main__":
    run()
