# SPDX-License-Identifier: AGPL-3.0-or-later
import bpy,json,sys,time,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'python'))
from chimera_studio import gpu_workspace as w
result={'pass':False,'scope':'Real Blender window displaying saved native GPU membrane, then asynchronous native resume/load'}
phase=0;deadline=time.monotonic()+50

def exercise():
    global phase
    try:
        if time.monotonic()>deadline:raise TimeoutError('GPU UI probe deadline')
        if phase==0:
            w.load_document(json.loads((root/'evidence/gpu-membrane.matter.json').read_text()))
            bpy.ops.chimera.gpu_resume();phase=1;return .2
        if phase==1:
            if w.busy():return .2
            assert not w._message.startswith('GPU call failed'),w._message
            bpy.context.scene.chimera_gpu.load=1.;bpy.ops.chimera.gpu_load();phase=2;return .2
        if phase==2:
            if w.busy():return .2
            assert not w._message.startswith('GPU call failed'),w._message
            result['native_state_id']=w.current().state['accepted_state_id'];result['load_N']=w.current().state['centre_load_N']
            for area in bpy.context.screen.areas:
                if area.type=='VIEW_3D':
                    area.spaces.active.region_3d.view_distance=4.2
                    area.spaces.active.region_3d.view_location=(0,0,0)
            phase=3;return 1.
        if phase==3:
            bpy.ops.screen.screenshot(filepath=str(root/'evidence/gpu-viewport.png'))
            result['pass']=True;phase=4
    except Exception as e:result['error']=str(e);result['traceback']=traceback.format_exc();phase=4
    if phase==4:
        (root/'evidence/gpu-gui.json').write_text(json.dumps(result,indent=2))
        w.close_session();bpy.ops.wm.quit_blender();return None
    return .2
bpy.app.timers.register(exercise,first_interval=1.)
