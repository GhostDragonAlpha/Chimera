# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate the fork's empty, meter-based authoring startup; no GPU render."""
import bpy
from pathlib import Path
from mathutils import Quaternion
root=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.workspace.name='Chimera Workshop'
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.show_region_ui=True
            area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='OBJECT'
            area.spaces.active.region_3d.view_distance=2.5
            area.spaces.active.region_3d.view_location=(0,0,.2)
bpy.data.orphans_purge(do_recursive=True)
path=root.parent/'blender/scripts/startup/bl_app_templates_system/ChimeraStudio/startup.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
