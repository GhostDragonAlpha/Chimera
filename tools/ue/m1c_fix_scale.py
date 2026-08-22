# m1c_fix_scale.py -- set BearRebound actor scale to 1 (MLSLabs already converts PLY meters to UE cm).
import unreal

unreal.EditorLevelLibrary.load_level("/Game/Maps/M1C_Bear")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
found = False
for a in actors:
    if a.get_actor_label() == "BearRebound":
        a.set_actor_scale3d(unreal.Vector(1, 1, 1))
        unreal.log("M1C: scale reset to 1 on " + a.get_actor_label())
        found = True
if not found:
    unreal.log_error("M1C: BearRebound actor not found")
unreal.EditorLevelLibrary.save_current_level()
unreal.log("M1C: map saved")
