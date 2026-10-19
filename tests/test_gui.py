# SPDX-License-Identifier: AGPL-3.0-or-later
"""Short real-window probe; Blender's own API captures its viewport and exits."""
import bpy,sys,json,traceback,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'python'))
from chimera_studio import workspace as w
result={'pass':False,'scope':'Real UI, solid viewport, two native rigid regions; not production frame-rate qualification','blender':bpy.app.version_string,'binary':bpy.app.binary_path,'build_hash':bpy.app.build_hash.decode()}
phase=0
bpy.context.preferences.view.show_splash=False

def exercise():
    global phase
    try:
        if phase==0:
            bpy.context.preferences.view.show_splash=False
            bpy.ops.chimera.demo();bpy.context.view_layer.update()
            assert bpy.ops.chimera.build()=={'FINISHED'}
            assert bpy.ops.chimera.join_mounts()=={'FINISHED'}
            assert bpy.ops.chimera.play()=={'FINISHED'}
            phase=1;return 1.
        if phase==1:
            r=w.current();r.running=False;result['native_steps']=r.native.call('state')['steps']
            assert result['native_steps']>80
            result['native_batch_ms']=r.last_ms
            result['sidebar_visible']=any(a.type=='VIEW_3D' and any(x.type=='UI' and x.active_panel_category=='Chimera' for x in a.regions) for sc in bpy.data.screens for a in sc.areas)
            assert result['sidebar_visible']
            bpy.ops.screen.screenshot(filepath=str(root/'evidence/viewport.png'))
            result['pass']=True;phase=2;return .1
    except Exception as exc:
        result['error']=str(exc);result['traceback']=traceback.format_exc();phase=2
    (root/'evidence/gui-smoke.json').write_text(json.dumps(result,indent=2))
    import chimera_studio
    chimera_studio.unregister()
    bpy.ops.wm.quit_blender()
    return None

bpy.app.timers.register(exercise,first_interval=2.)
