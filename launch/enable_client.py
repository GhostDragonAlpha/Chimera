# Launcher helper (--python): invoke the same operator the human clicks in
# N > Chimera > Local Z Code Connection, once the window exists. Opt-in only:
# Start-ChimeraStudio.ps1 -EnableClient. Never raises out of the timer.
import bpy

_state = {"tries": 0}


def _enable():
    _state["tries"] += 1
    try:
        result = bpy.ops.chimera.enable_client()
        if result == {'FINISHED'}:
            print('CHIMERA_CLIENT_ENABLED ok', flush=True)
            return None
    except Exception as error:
        print('CHIMERA_CLIENT_ENABLE_FAILED: %s' % error, flush=True)
    if _state["tries"] >= 60:
        print('CHIMERA_CLIENT_ENABLED failed: enable_client operator did not '
              'finish within 60 retries', flush=True)
        return None
    return 1.0


bpy.app.timers.register(_enable, first_interval=1.0)
