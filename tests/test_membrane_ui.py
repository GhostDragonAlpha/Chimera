# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded Blender UI check, owned window/helper only."""
import bpy,json,time,traceback
from pathlib import Path
from mathutils import Quaternion
from chimera_studio import gpu_workspace as w,gpu_native as g
root=Path(__file__).resolve().parents[1]
report={'pass':False,'scope':'Blender UI panels, selectable computed membranes and native render Image Editor','runtime':g.identity()}
phase=0;deadline=time.monotonic()+45
bpy.context.preferences.view.show_splash=False

def run():
    global phase
    try:
        if time.monotonic()>deadline:raise TimeoutError('Blender UI test deadline')
        if w.busy():return .1
        if w._message.startswith('GPU call failed'):raise RuntimeError(w._message)
        if phase==0:
            bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
            bpy.ops.chimera.add_membrane_assembly();bpy.context.view_layer.update();bpy.ops.chimera.build_membrane_assembly()
            phase=1;return .2
        if phase==1:
            bpy.context.scene.chimera_gpu.load=.8;bpy.ops.chimera.gpu_load();phase=2;return .2
        if phase==2:
            preview=next(o for o in bpy.data.objects if o.get('chimera_block_preview'))
            bpy.ops.object.select_all(action='DESELECT');preview.select_set(True);bpy.context.view_layer.objects.active=preview
            for area in bpy.context.screen.areas:
                if area.type=='VIEW_3D':
                    space=area.spaces.active;space.show_region_ui=True
                    space.region_3d.view_rotation=Quaternion((.83,.47,.12,.27)).normalized()
                    space.region_3d.view_location=(0,0,.3);space.region_3d.view_distance=3.5
                    for reg in area.regions:
                        if reg.type=='UI':reg.active_panel_category='Chimera'
            phase=3;return 1.
        if phase==3:
            bpy.ops.screen.screenshot(filepath=str(root/'evidence/membrane-blender-viewport.png'))
            report['computed_pick_id']=bpy.context.object['chimera_block_preview']
            report['state_id']=w.current().state['accepted_state_id']
            bpy.ops.chimera.native_render_frame();phase=4;return .2
        if phase==4:
            assert any(a.type=='IMAGE_EDITOR' and a.spaces.active.image and a.spaces.active.image.name=='Chimera Native Render' for a in bpy.context.screen.areas)
            phase=5;return 1.
        if phase==5:
            bpy.ops.screen.screenshot(filepath=str(root/'evidence/membrane-blender-native-view.png'))
            report['pass']=True
    except Exception as exc:
        report['error']=str(exc);report['traceback']=traceback.format_exc()
    finally:
        if report['pass'] or 'error' in report:
            (root/'evidence/membrane-ui-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            import chimera_studio
            chimera_studio.unregister();bpy.ops.wm.quit_blender()
    return .1
bpy.app.timers.register(run,first_interval=1.)
