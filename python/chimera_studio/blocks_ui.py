# SPDX-License-Identifier: AGPL-3.0-or-later
"""Blender membrane authoring. Existing native law remains the sole solver."""
import json
import uuid
import bpy
import numpy as np
from bpy.props import FloatProperty, StringProperty, PointerProperty
from . import blocks, gpu_native as g, gpu_workspace as w

COLORS=((.12,.5,.8,1),(.85,.3,.12,1),(.25,.7,.3,1))

class BlockSettings(bpy.types.PropertyGroup):
    gamma:FloatProperty(name='Surface tension J/m²',default=1,min=.000001,max=1000)
    connections:StringProperty(default='[]')


def editable(context):
    objects=[o for o in context.selected_objects if o.type=='MESH' and not o.get('chimera_gpu_preview') and not o.get('chimera_preview')]
    if not objects:raise ValueError('Select editable membrane films')
    return objects


def part(obj):
    if obj.modifiers:raise ValueError('Apply modifiers before native compilation')
    if obj.mode=='EDIT':obj.update_from_editmode()
    if 'chimera_block_id' not in obj or 'chimera_free_center' not in obj or 'chimera_film_gamma' not in obj:
        raise ValueError('Mark an apex and assign a surface material to each film')
    mesh=obj.data;mesh.calc_loop_triangles()
    p=np.asarray([(*v.co,1) for v in mesh.vertices],dtype=float)@np.asarray(obj.matrix_world,dtype=float).T
    return {'id':obj['chimera_block_id'],'name':obj.name,'positions':p[:,:3].tolist(),
            'triangles':[list(t.vertices) for t in mesh.loop_triangles],
            'centre':int(obj['chimera_free_center']),'gamma':float(obj['chimera_film_gamma'])}


class Starter(bpy.types.Operator):
    bl_idname='chimera.add_membrane_assembly';bl_label='Add Existing Three-Film Assembly';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            parts,edges=blocks.starter();ids={p['id']:uuid.uuid4().hex for p in parts}
            bpy.ops.object.select_all(action='DESELECT')
            for i,p in enumerate(parts):
                mesh=bpy.data.meshes.new(p['name']);mesh.from_pydata(p['positions'],[],p['triangles']);mesh.update()
                obj=bpy.data.objects.new(p['name'],mesh);context.collection.objects.link(obj)
                obj['chimera_block_id']=ids[p['id']];obj['chimera_free_center']=p['centre'];obj['chimera_film_gamma']=1.
                obj['chimera_recipe']='assembly.star-k2 / '+p['id'];obj.color=COLORS[i];obj.select_set(True)
                for v in mesh.vertices:v.select=v.index==p['centre']
                context.view_layer.objects.active=obj
            current=json.loads(context.scene.chimera_blocks.connections)
            current.extend([[ids[a],ids[b]] for a,b in edges]);context.scene.chimera_blocks.connections=json.dumps(current)
            context.scene.unit_settings.scale_length=1
            w.message('Existing A/B/C films and two apex welds added. Build Connected Films.')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}

class Apex(bpy.types.Operator):
    bl_idname='chimera.mark_membrane_apex';bl_label='Mark Selected Vertex as Apex';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            obj=context.object
            if obj not in editable(context):raise ValueError('Select an authored film')
            if obj.mode=='EDIT':obj.update_from_editmode()
            selected=[v.index for v in obj.data.vertices if v.select]
            if len(selected)!=1:raise ValueError('Select exactly one vertex in Edit Mode')
            obj['chimera_free_center']=selected[0]
            if 'chimera_block_id' not in obj:obj['chimera_block_id']=uuid.uuid4().hex
            w.message('Apex marked; every other vertex is a fixed support in this native law.')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}

class NewIdentity(bpy.types.Operator):
    bl_idname='chimera.new_membrane_identity';bl_label='Make Selected Films New Instances';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            for obj in editable(context):obj['chimera_block_id']=uuid.uuid4().hex
            w.message('New identities assigned. Connect the new instances explicitly before building.')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}

class Assign(bpy.types.Operator):
    bl_idname='chimera.assign_membrane_material';bl_label='Assign Surface Material';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            objects=editable(context)
            for obj in objects:
                if 'chimera_block_id' not in obj:obj['chimera_block_id']=uuid.uuid4().hex
                obj['chimera_film_gamma']=context.scene.chimera_blocks.gamma
            w.message('Surface tension assigned. Build explicitly to apply to a new native trial.')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}

class Connect(bpy.types.Operator):
    bl_idname='chimera.connect_membrane_apices';bl_label='Connect Two Selected Apices';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            objects=editable(context)
            if len(objects)!=2:raise ValueError('Select exactly two films')
            parts=[part(o) for o in objects];edge=sorted(p['id'] for p in parts)
            blocks.compile_parts(parts,[edge])  # Same geometry/material gate used by Build.
            edges=json.loads(context.scene.chimera_blocks.connections)
            if edge not in [sorted(e) for e in edges]:edges.append(edge)
            context.scene.chimera_blocks.connections=json.dumps(edges)
            w.message('Apex weld recorded; build to apply. Rims remain fixed supports.')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}

class Disconnect(bpy.types.Operator):
    bl_idname='chimera.disconnect_membrane_apices';bl_label='Disconnect Two Selected Apices';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            objects=editable(context)
            if len(objects)!=2:raise ValueError('Select exactly two films')
            pair=sorted(str(o.get('chimera_block_id','')) for o in objects)
            edges=json.loads(context.scene.chimera_blocks.connections)
            context.scene.chimera_blocks.connections=json.dumps([e for e in edges if sorted(e)!=pair])
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}

class Build(bpy.types.Operator):
    bl_idname='chimera.build_membrane_assembly';bl_label='Build Connected Films'
    def execute(self,context):
        try:
            if w.busy():raise RuntimeError('A native operation is in progress')
            if abs(context.scene.unit_settings.scale_length-1)>1e-9:raise ValueError('Use meters and Unit Scale 1')
            objects=editable(context);parts=[part(o) for o in objects];ids={p['id'] for p in parts}
            edges=[e for e in json.loads(context.scene.chimera_blocks.connections) if all(i in ids for i in e)]
            spec=blocks.compile_parts(parts,edges)
            visibility={'block:'+o['chimera_block_id']:o.hide_get() for o in objects}
            # Keep the previous confirmed trial until the candidate launches and validates.
            w.submit(lambda:(g.GpuSession(spec),visibility))
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


def sync_preview(doc):
    spec=doc['spec'];render,positions=g.validate_render(doc['render'],spec,doc['state'])
    normals=render[:,[3,5,4]].copy();normals[:,1]*=-1
    col=bpy.data.collections.get(w.COLLECTION)
    if col is None:col=bpy.data.collections.new(w.COLLECTION);bpy.context.scene.collection.children.link(col)
    for obj in col.objects:
        if obj.get('chimera_gpu_preview'):obj.hide_set(True)
    faces=np.asarray(spec['triangles'])
    for k,region in enumerate(spec['assembly']['regions']):
        ids=region['vertices'];remap={v:i for i,v in enumerate(ids)}
        localfaces=[[remap[int(v)] for v in face] for face in faces[region['faces']]]
        obj=next((o for o in col.objects if o.get('chimera_block_preview')==region['id']),None)
        if obj and (len(obj.data.vertices)!=len(ids) or [list(f.vertices) for f in obj.data.polygons]!=localfaces):
            mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
            if not mesh.users:bpy.data.meshes.remove(mesh)
            obj=None
        if obj is None:
            mesh=bpy.data.meshes.new(region['name']+' native output');mesh.from_pydata(positions[ids],[],localfaces);mesh.update()
            obj=bpy.data.objects.new(region['name']+' [computed]',mesh);col.objects.link(obj)
        obj['chimera_gpu_preview']=True;obj['chimera_block_preview']=region['id']
        obj['accepted_state_id']=doc['state']['accepted_state_id'];obj['render_state_id']=doc['render']['render_state_id']
        obj['surface_tension_J_m2']=spec['gamma'];obj['attachment']='shared world-Z rail apex; rim fixed'
        obj.data.vertices.foreach_set('co',positions[ids].ravel());obj.data.update()
        for face in obj.data.polygons:face.use_smooth=True
        obj.data.normals_split_custom_set_from_vertices(normals[ids])
        color=obj.data.color_attributes.get('Native kernel color') or obj.data.color_attributes.new(name='Native kernel color',type='FLOAT_COLOR',domain='POINT')
        rgba=np.column_stack((render[ids,6:9],np.ones(len(ids))))
        color.data.foreach_set('color',rgba.ravel());obj.data.color_attributes.active_color=color
        obj.color=COLORS[k%len(COLORS)];obj.hide_set(False);obj.hide_select=False
        obj.lock_location=(True,True,True);obj.lock_rotation=(True,True,True);obj.lock_scale=(True,True,True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.shading.color_type='OBJECT'


def ensure_authoring(doc):
    # A standalone trial contains its construction, not just an opaque preview.
    # Reuse matching stable identities and never overwrite someone's edited mesh.
    parts=doc['spec']['assembly']['parts'];objects={}
    for p in parts:
        hits=[o for o in bpy.data.objects if o.get('chimera_block_id')==p['id']]
        if len(hits)>1:raise ValueError('Duplicate source identity in Blender: '+p['id'])
        objects[p['id']]=hits[0] if hits else None
    visibility={}
    for p in parts:
        obj=objects[p['id']]
        if obj is None:
            mesh=bpy.data.meshes.new(p['name']);mesh.from_pydata(p['positions'],[],p['triangles']);mesh.update()
            obj=bpy.data.objects.new(p['name'],mesh);bpy.context.scene.collection.objects.link(obj)
            obj['chimera_block_id']=p['id'];obj['chimera_free_center']=p['centre'];obj['chimera_film_gamma']=p['gamma']
        visibility['block:'+p['id']]=doc.get('authoring_visibility',{}).get('block:'+p['id'],doc.get('authoring_visibility',{}).get(p['name'],False))
    edges=json.loads(bpy.context.scene.chimera_blocks.connections)
    for e in doc['spec']['assembly']['connections']:
        if e not in [sorted(x) for x in edges]:edges.append(e)
    bpy.context.scene.chimera_blocks.connections=json.dumps(edges)
    return visibility


def show_frame(raw):
    path=g.ROOT/'.user/native-render.png';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    image=bpy.data.images.load(str(path),check_existing=True);image.reload();image.name='Chimera Native Render'
    image.pack()
    if not bpy.app.background:
        areas=[a for a in bpy.context.screen.areas if a.type=='IMAGE_EDITOR'] or [a for a in bpy.context.screen.areas if a.type=='VIEW_3D']
        if areas:
            area=max(areas,key=lambda a:a.width*a.height);area.type='IMAGE_EDITOR';area.spaces.active.image=image
    return image

class NativeFrame(bpy.types.Operator):
    bl_idname='chimera.native_render_frame';bl_label='Show Native Render in Image Editor'
    def execute(self,context):
        try:
            r=w.current()
            def capture():
                r.snapshot()
                r.engine.request('POST','/camera',{'cam_radius':3.3,'cam_theta':.6,'cam_phi':.45})
                return r.engine.request('GET','/frame',binary=True)
            w.submit(capture)
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}

class Panel(bpy.types.Panel):
    bl_label='Membrane Assembly';bl_idname='CHIMERA_PT_blocks';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Chimera'
    def draw(self,context):
        l=self.layout;s=context.scene.chimera_blocks
        l.label(text='Existing films and apex-weld law')
        col=l.column();col.enabled=not w.busy()
        col.operator('chimera.add_membrane_assembly');col.operator('chimera.mark_membrane_apex');col.operator('chimera.new_membrane_identity')
        col.prop(s,'gamma');col.operator('chimera.assign_membrane_material')
        col.operator('chimera.connect_membrane_apices');col.operator('chimera.disconnect_membrane_apices');col.operator('chimera.build_membrane_assembly')
        col.prop(context.scene.chimera_gpu,'load');col.operator('chimera.gpu_load')
        col.operator('chimera.native_render_frame')
        col.operator('chimera.gpu_resume');col.prop(context.scene.chimera_gpu,'replay');col.operator('chimera.gpu_seek')
        col.operator('chimera.gpu_save');col.operator('chimera.gpu_open');col.operator('chimera.gpu_authoring');col.operator('chimera.gpu_release')
        obj=context.object
        if obj and obj.get('chimera_block_preview'):
            l.label(text=obj.name);l.label(text=f"Surface tension: {obj.get('surface_tension_J_m2',0):g} J/m²")
            l.label(text='Connected apex; fixed rim supports')
        l.label(text=w._message[:65]);l.label(text=w._message[65:130])
        l.label(text='Uniform tension across joined films')
        l.label(text='One rail DOF; no water or solid materials')

CLASSES=(BlockSettings,Starter,Apex,NewIdentity,Assign,Connect,Disconnect,Build,NativeFrame,Panel)
def register():
    for cls in CLASSES:bpy.utils.register_class(cls)
    bpy.types.Scene.chimera_blocks=PointerProperty(type=BlockSettings)
def unregister():
    if hasattr(bpy.types.Scene,'chimera_blocks'):del bpy.types.Scene.chimera_blocks
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)
