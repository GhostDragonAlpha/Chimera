# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
import chimera_studio
if not hasattr(bpy.types.Object,'chimera'):chimera_studio.register()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.show_region_ui=True
            area.spaces.active.shading.type='SOLID'
            area.spaces.active.shading.color_type='OBJECT'
            area.spaces.active.region_3d.view_distance=2.5
bpy.context.workspace.name='Chimera Workshop'
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
