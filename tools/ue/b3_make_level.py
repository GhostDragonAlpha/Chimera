# b3_make_level.py -- build /Game/Maps/B_CadBear with the imported skeletal mesh.
# Commandlet-safe: no Interchange, no Slate.
import unreal

MESH = "/Game/CAD/cad_bear/SkeletalMeshes/cad_bear"

mesh = unreal.load_asset(MESH)
if mesh is None:
    unreal.log_error("B3L: mesh asset missing")
    raise SystemExit(1)
unreal.log("B3L: mesh loaded: " + mesh.get_class().get_name())

unreal.EditorLevelLibrary.new_level("/Game/Maps/B_CadBear")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.SkeletalMeshActor, unreal.Vector(0, 0, 15))  # bear center ~15cm up
actor.set_actor_label("CadBear")
actor.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
unreal.EditorLevelLibrary.save_current_level()
unreal.log("B3L: level saved")
