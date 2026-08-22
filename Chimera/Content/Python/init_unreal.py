# init_unreal.py -- Chimera project Python startup hook.
# Verification harness: if E:/PythonChimera/.tmp/ue_shot.flag exists, this launch is a
# verification run. The flag file holds JSON: {"wait": seconds, "shots": [[pos],[rot]], ...}.
# After the wait: frame each camera, HighResShot each, then delete-the-flag semantics
# (flag removed at read time so normal launches are no-ops). Editor stays open.
import json
import os
import time
import unreal

FLAG = "E:/PythonChimera/.tmp/ue_shot.flag"


def _bootstrap(spec):
    wait = float(spec.get("wait", 30.0))
    shots = spec.get("shots", [])
    gap = float(spec.get("gap", 4.0))
    start = time.time()
    holder = {"handle": None, "i": 0}

    def _tick(_dt):
        el = time.time() - start
        i = holder["i"]
        if i < len(shots) and el >= wait + i * gap:
            pos, rot = shots[i]
            unreal.EditorLevelLibrary.set_level_viewport_camera_info(
                unreal.Vector(*pos), unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2]))
            unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
            unreal.log("UE_SHOT: shot %d issued" % i)
            holder["i"] = i + 1
        elif holder["i"] >= len(shots) and holder["handle"] is not None:
            unreal.unregister_slate_post_tick_callback(holder["handle"])
            holder["handle"] = None
            unreal.log("UE_SHOT: verification complete")

    holder["handle"] = unreal.register_slate_post_tick_callback(_tick)
    unreal.log("UE_SHOT: armed (%d shots after %.0fs)" % (len(shots), wait))


if os.path.exists(FLAG):
    try:
        with open(FLAG) as f:
            _spec = json.load(f)
        os.remove(FLAG)
        _bootstrap(_spec)
    except Exception as e:
        unreal.log_error("UE_SHOT: flag error: %s" % e)
