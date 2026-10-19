# SPDX-License-Identifier: AGPL-3.0-or-later
import bpy,json,os,sys
from pathlib import Path
root=Path(os.environ['CHIMERA_STUDIO_ROOT'])
assert hasattr(bpy.types.Object,'chimera'), 'Template did not register Chimera'
assert bpy.context.scene.unit_settings.system=='METRIC'
assert bpy.context.scene.unit_settings.scale_length==1
assert any(a.type=='VIEW_3D' and a.spaces.active.show_region_ui for s in bpy.data.screens for a in s.areas)
from chimera_studio import workspace as w
bpy.ops.chimera.demo();bpy.context.view_layer.update()
assert bpy.ops.chimera.build()=={'FINISHED'}
assert bpy.ops.chimera.step()=={'FINISHED'}
assert w.current().native.call('state')['steps']==80
bpy.ops.chimera.edit()
(root/'evidence/template-startup.json').write_text(json.dumps({'pass':True,'blender':bpy.app.version_string,'binary':bpy.app.binary_path,'build_hash':bpy.app.build_hash.decode(),'template':'ChimeraStudio','registered':True,'native_steps':80},indent=2))
print('PASS application-template startup and native scene')

import chimera_studio
chimera_studio.unregister()
