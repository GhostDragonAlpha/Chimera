# SPDX-License-Identifier: AGPL-3.0-or-later
"""Chimera Studio: Blender authoring around the existing native matter engine."""
bl_info={'name':'Chimera Studio','author':'Chimera','version':(0,1,0),'blender':(5,0,0),'location':'3D View > Sidebar > Chimera','description':'Native construction, material regions and physical replay','category':'Physics'}
def register():
    from . import workspace
    workspace.register()
def unregister():
    from . import workspace
    workspace.unregister()
