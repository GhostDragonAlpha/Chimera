# b3_import_bear.py -- import cad_bear.glb into /Game/CAD and build a verification level.
# Commandlet: UnrealEditor.exe Chimera.uproject -run=pythonscript -script=<this>
import unreal

GLB = "E:/PythonChimera/models/cad_bear/cad_bear.glb"

task = unreal.AssetImportTask()
task.filename = GLB
task.destination_path = "/Game/CAD"
task.automated = True
task.save = True
task.replace_existing = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

assets = unreal.EditorAssetLibrary.list_assets("/Game/CAD")
unreal.log("B3: assets in /Game/CAD: " + ", ".join(assets))

mesh_path = next((a for a in assets if "cad_bear" in a.lower()
                  and "skeleton" not in a.lower()), None)
if not mesh_path:
    unreal.log_error("B3: no skeletal mesh found after import")
    raise SystemExit(1)

mesh = unreal.load_asset(mesh_path)
unreal.log("B3: mesh = " + mesh_path + " class=" + mesh.get_class().get_name())

# verification level: bear at origin on a simple floor, camera framed by init_unreal.py
unreal.EditorLevelLibrary.new_level("/Game/Maps/B_CadBear")
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
actor.set_actor_label("CadBear")
smc = actor.skeletal_mesh_component
smc.set_skeletal_mesh_asset(mesh)
unreal.EditorLevelLibrary.save_current_level()
unreal.log("B3: level /Game/Maps/B_CadBear saved with CadBear")
