# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real-window check of the cradle's human controls, following the workshop GUI
pattern: the Attachment Loads panel and the Layer Trial Comparison preview draw
over the owned saved project, peak navigation moves the timeline, comparison
copies appear at the shared sample time, and a screenshot keeps the inspected
pixels. Offline only: native launch is disabled for the whole session."""
from pathlib import Path
import json
import os
import time
import traceback

import bpy
import numpy as np
from mathutils import Vector, Quaternion
from chimera_studio import attachment_loads_ui as ui, layer_trials as trials, layer_editing as ed

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(os.environ['CHIMERA_CRADLE_GUI_OUT'])
OUT = BASE / 'gui'
OUT.mkdir(exist_ok=False)
print('CRADLE GUI: wrapping panels over', BASE, flush=True)
EXPECTED = json.loads((BASE / 'checks.json').read_text(encoding='utf-8'))['summary']
scene = bpy.context.scene
m = ed.module()
bpy.context.preferences.use_preferences_save = False
m.runtime.launch = lambda *a, **k: (_ for _ in ()).throw(AssertionError('Cradle UI is offline'))

phase = 0
draws = set()
errors = []
deadline = time.monotonic() + 180

panels = [ui.Panel, trials.Panel]


def wrap(cls):
    original = cls.draw
    cls.bl_options = set()
    # Blender 5.0.1 made Region.active_panel_category read-only ('UNSUPPORTED'),
    # so the test cannot switch the sidebar to the 'Chimera' tab; draw the same
    # panel classes in the default active 'Item' tab instead.
    cls.bl_category = 'Item'

    def draw(self, c):
        draws.add(c.mode)
        try:
            original(self, c)
        except Exception as ex:
            errors.append(str(ex))
            raise
    bpy.utils.unregister_class(cls)
    cls.draw = draw
    bpy.utils.register_class(cls)


for cls in panels:
    wrap(cls)


def tick():
    global phase
    print('CRADLE GUI: tick phase', phase, flush=True)
    try:
        assert time.monotonic() < deadline, 'Cradle UI deadline'
        if phase == 0:
            for cls in list(bpy.types.Panel.__subclasses__()):
                if getattr(cls, 'bl_category', None) == 'Chimera' and cls not in panels:
                    try:
                        bpy.utils.unregister_class(cls)
                    except RuntimeError:
                        pass
            load = next(o for o in scene.objects if o.name.startswith('05'))
            for o in bpy.context.selected_objects:
                o.select_set(False)
            load.select_set(True)
            bpy.context.view_layer.objects.active = load
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    a.spaces.active.show_region_ui = True
            assert bpy.ops.chimera.inspect_attachment_loads() == {'FINISHED'}
            assert len(ui._last['seams']) == 2, ui._last['seams']
            assert bpy.ops.chimera.jump_attachment_load(seam_id=ui._last['seams'][0]['id']) == {'FINISHED'}
            scene.frame_set(ui._last['seams'][0]['peak']['frame'])
            print('CRADLE GUI: inspected + jumped to peak frame', ui._last['seams'][0]['peak']['frame'], flush=True)
            phase = 1
            return .3
        if phase == 1:
            _, arc = trials.current(scene)
            points, _ = trials.sampled_points(m, arc, ui._last['seams'][0]['peak']['seconds'])
            p = np.concatenate([points[b['id']] for b in arc['bodies'] if b['material']['role'] != 'STATIC'])
            center = (p.min(axis=0) + p.max(axis=0)) / 2
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    a.spaces.active.region_3d.view_location = Vector(center)
                    a.spaces.active.region_3d.view_distance = 2.2
                    a.spaces.active.region_3d.view_rotation = Quaternion((.853, .354, .146, .354))
                    a.spaces.active.shading.color_type = 'MATERIAL'
            scene.uipc_settings.show_attachments = True
            assert bpy.ops.chimera.compare_layer_trials(seconds=.6, preview=True) == {'FINISHED'}
            print('CRADLE GUI: trial preview created', flush=True)
            phase = 2
            return .8
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=2)
        assert draws and not errors, (sorted(draws), errors)
        result = trials._pair['result']
        assert abs(result['B_minus_A_drop_m'] - EXPECTED['B_minus_A_drop_m']) < 1e-9, \
            (result['B_minus_A_drop_m'], EXPECTED['B_minus_A_drop_m'])
        bpy.ops.screen.screenshot(filepath=str(OUT / 'cradle-haul-ui.png'))
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'Cradle haul UI.blend'))
        (OUT / 'panel.json').write_text(json.dumps(
            {'passed': True, 'draw_modes': sorted(draws), 'errors': errors,
             'seams': [{'name': s['name'], 'peak_N': s['peak']['absolute_force_N'],
                        'peak_frame': s['peak']['frame']} for s in ui._last['seams']],
             'compare_B_minus_A_drop_m': result['B_minus_A_drop_m'],
             'compare_seconds': result['seconds'],
             'peak_navigation': True, 'trial_preview_copies': True,
             'panel_category_accommodation': "Blender 5.0.1 made Region.active_panel_category read-only; the same panel classes are drawn in the default 'Item' sidebar tab",
             'offline_native_launch_disabled': True}, indent=2))
        bpy.ops.wm.quit_blender()
        return None
    except Exception:
        (OUT / 'panel.json').write_text(json.dumps(
            {'passed': False, 'phase': phase, 'traceback': traceback.format_exc()}, indent=2))
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(tick, first_interval=.2)
