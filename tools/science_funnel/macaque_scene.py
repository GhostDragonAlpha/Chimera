"""Compile the coupled macaque-on-Earth scene.

This is an opt-in sibling of coupled_free_scene.py. The qualified arm bundle
and its compiler remain untouched; this scene changes only the world placement
and presentation contract.
"""
import argparse
import copy
import json
from pathlib import Path

from .common import canonical, digest, require
from .coupled_free_scene import FREE_MODEL, compile_free
from .coupled_free_scene import ROOT
from .ct_skeleton_layer import measure_falsifier
from tools.creature_graph.store import CreatureGraph

TERRAIN_HEIGHT_M = -42.827
BUNDLE_KIND = "coupled_macaque_scene"


def compile_macaque(graph, output):
    graph = copy.deepcopy(graph)
    earth = graph.get("model.environment.earth_patch")["physical"]["contract"]
    free = graph.get(FREE_MODEL)["physical"]["contract"]
    surface = graph.get("world.earth.patch.coupled_arm_contact_plane")["physical"]
    require(abs(TERRAIN_HEIGHT_M - (-42.827)) < 1e-12, "macaque_terrain_height_pin")

    # Preserve the free-root solver's admitted local seating geometry while
    # placing that frame at the absolute Cayo Santiago reduction height.
    earth["arm_translation_m"] = [0.0, TERRAIN_HEIGHT_M + 0.2, 0.0]
    free["contact_plane_height_m"] = TERRAIN_HEIGHT_M
    surface["height_world_up_m"] = TERRAIN_HEIGHT_M

    output = Path(output).resolve()
    bundle = compile_free(graph, output)
    bundle["bundle_kind"] = BUNDLE_KIND
    bundle["scene_kind"] = BUNDLE_KIND
    # EarthTrial remains a local environment health source at its normal mount;
    # the free-root solver and rendered body use this separate world placement.
    bundle["solver_shift_m"] = [0.0, TERRAIN_HEIGHT_M + 0.2, 0.0]
    bundle["scene"]["arm_translation_m"] = [0.0, 0.55, 0.0]
    bundle["coupled_free_dynamics"]["recipe"]["defaults"].update({"power": True, "shoulder_target_deg": 0.0, "elbow_target_deg": 90.0, "contact_friction": 0.0})
    bundle["page_file"] = str(ROOT / "tools/science_funnel/earth.html")
    bundle["terrain"] = {
        "name": "Cayo Santiago admitted terrain reduction",
        "height_world_up_m": TERRAIN_HEIGHT_M,
        "representation": "authored flat terrain plane at the admitted reduction value; not a DEM surface",
        "normal_world": [0.0, 1.0, 0.0],
    }
    bundle["scope"] = (
        "Coupled macaque free-root scene using the seven pinned source bone meshes, "
        "the admitted Cayo Santiago terrain reduction plane at -42.827 m, and "
        "support-hull state from the native solver. No skin, muscles, whole-animal "
        "anatomy, scanned terrain relief, or walking controller claim."
    )
    # CT skeleton VISUAL layer (lane buffy/ct-skeleton-visual-20260919): the
    # committed MorphoSource CT previews in their own CT frame, placed by ONE
    # documented rigid registration into the scene frame. Purely additive: the
    # visual layer carries no physics claim, so the solver/dynamics contract
    # above is untouched and the scene hash still covers the physics bundle.
    # Measured here so the falsifier verdict ships with the bundle.
    bundle["ct_skeleton_layer"] = {
        "schema": "chimera.ct_skeleton_layer.v1",
        "mode": "visual_only_no_physics_claim",
        "frame": "own CT frame, rigidly registered (uniform scale + one rotation + translation)",
        "source": "tools/science_funnel/data/morphosource_ct (committed previews, millimetre units)",
        "falsifier": measure_falsifier()["falsifier"],
    }
    bundle.pop("scene_sha256", None)
    bundle["scene_sha256"] = digest(bundle)
    output.mkdir(parents=True, exist_ok=True)
    (output / "scene.json").write_bytes(canonical(bundle))
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".tmp/macaque-scene")
    args = parser.parse_args()
    graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))
    require(FREE_MODEL in graph.objects, "free_model_record_missing")
    bundle = compile_macaque(graph, args.output)
    print(json.dumps({
        "scene": str(args.output / "scene.json"),
        "scene_sha256": bundle["scene_sha256"],
        "bundle_kind": bundle["bundle_kind"],
        "terrain_height_world_up_m": bundle["terrain"]["height_world_up_m"],
    }))


if __name__ == "__main__":
    main()
