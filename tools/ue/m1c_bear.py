# m1c_bear.py -- UE editor bootstrap: spawn bear_rebound.ply as a GaussianSplattingActor,
# frame the viewport camera on it, screenshot for machine verification, save the level.
# Run: UnrealEditor.exe Chimera.uproject -run=pythonscript -script=<this file>
import time
import unreal

PLY = "E:/PythonChimera/Chimera/Content/MLSLabsRenderer/ply/bear_rebound.ply"
LEVEL = "/Game/Maps/M1C_Bear"

unreal.log("M1C: creating blank level")
unreal.EditorLevelLibrary.new_level(LEVEL)

cls = unreal.load_class(None, "/Script/MLSLabsRenderer.GaussianSplattingActor")
if cls is None:
    unreal.log_error("M1C: FAILED to load GaussianSplattingActor class")
    raise SystemExit(1)

actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0))
actor.set_actor_label("BearRebound")
actor.set_actor_scale3d(unreal.Vector(100, 100, 100))  # splat units are meters -> UE cm

comp = actor.get_component_by_class(
    unreal.load_class(None, "/Script/MLSLabsRenderer.GaussianSplattingComponent"))
comp.set_editor_property("SplatDataPath", PLY)
unreal.log("M1C: splat load queued for " + PLY)

# async render-command load; give the DLL time to parse + upload
time.sleep(20)

# bear faces +X (canonical face +Z -> UE +X), ~30cm tall centered near z=15cm
unreal.EditorLevelLibrary.set_level_viewport_camera_info(
    unreal.Vector(80.0, 0.0, 20.0), unreal.Rotator(pitch=-8.0, yaw=180.0, roll=0.0))
time.sleep(2)

unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
time.sleep(3)

unreal.EditorLevelLibrary.save_current_level()
unreal.log("M1C: done -- level saved, editor left open")
