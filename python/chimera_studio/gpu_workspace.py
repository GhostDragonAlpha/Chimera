# SPDX-License-Identifier: AGPL-3.0-or-later
"""Blender matter controls; GPU calls run off the UI thread, native state owns the view."""
import concurrent.futures
import copy
import json
from pathlib import Path
import time
import bpy
import numpy as np
from bpy.props import FloatProperty,IntProperty,PointerProperty,StringProperty
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ImportHelper,ExportHelper
from . import gpu_native as g

TEXT='Chimera GPU Matter.json';COLLECTION='Chimera GPU Matter'
_session=None;_future=None;_executor=None;_generation=0;_saved=None;_visibility={};_message='Native membrane and CA field; start explicitly'

def message(s):
    global _message
    _message=str(s)[:450]

def current():
    if not _session:raise RuntimeError('Load or resume a GPU matter trial first')
    return _session

def document():
    doc=copy.deepcopy(_session.document() if _session else _saved)
    if doc is not None:doc['authoring_visibility']=dict(_visibility)
    return doc

def busy():return _future is not None

def submit(fn):
    global _executor,_future
    if busy():raise RuntimeError('A native GPU call is still in progress')
    if _executor is None:_executor=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix='ChimeraGPU')
    generation=_generation
    _future=(_executor.submit(fn),generation);message('Waiting for native GPU result…')

def poll():
    global _future,_session,_saved
    if _future and _future[0].done():
        future,generation=_future;_future=None
        try:
            result=future.result()
            if generation!=_generation:
                if isinstance(result,g.GpuSession):result.close()
                return .1
            if isinstance(result,g.GpuSession):
                if _session and _session is not result:_session.close()
                _session=result
            _saved=document();sync_preview(_saved)
            state=_saved['state'];mode=_saved['spec']['mode']
            if mode=='membrane':message(f"GPU membrane | {state['energy_J']:.6g} J | center load {state['centre_load_N']:.4g} N")
            else:message(f"GPU CA | {state['steps']} steps | {state['simulated_seconds']:.3f} s | {sum(state['volumes'])} volume quanta")
        except Exception as exc:message('GPU call failed: '+str(exc))
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':area.tag_redraw()
    return .1

def close_session():
    global _session,_future,_generation,_executor
    _generation+=1
    if _future:
        future,_=_future
        session=_session
        def cleanup(f):
            try:
                result=f.result()
                if isinstance(result,g.GpuSession):result.close()
            except Exception:pass
            if session:session.close()
        future.add_done_callback(cleanup);_future=None
    elif _session:_session.close()
    _session=None
    if _executor:_executor.shutdown(wait=False,cancel_futures=True);_executor=None

def sync_preview(doc):
    if not doc:return
    spec=doc['spec'];state=doc['state']
    for name in _visibility:
        source=bpy.data.objects.get(name)
        if source:source.hide_set(True)
    positions=state['positions_f32'] if spec['mode']=='membrane' else spec['positions']
    points=np.asarray(positions,dtype=float).reshape(-1,3);faces=spec['triangles']
    col=bpy.data.collections.get(COLLECTION)
    if col is None:col=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(col)
    obj=next((o for o in col.objects if o.get('chimera_gpu_preview')),None)
    if obj and (len(obj.data.vertices)!=len(points) or [list(p.vertices) for p in obj.data.polygons]!=faces):
        mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
        if not mesh.users:bpy.data.meshes.remove(mesh)
        obj=None
    if obj is None:
        mesh=bpy.data.meshes.new('Native matter state');mesh.from_pydata(points,[],faces);mesh.update()
        obj=bpy.data.objects.new('GPU '+spec['mode'],mesh);col.objects.link(obj);obj['chimera_gpu_preview']=True;obj.hide_select=True
    obj.hide_set(False);obj.data.vertices.foreach_set('co',points.ravel());obj.data.update();obj.color=(.1,.6,.8,1)
    if spec['mode']=='water':
        colors=obj.data.color_attributes.get('CA volume') or obj.data.color_attributes.new(name='CA volume',type='FLOAT_COLOR',domain='CORNER')
        vmax=max(1,max(state['volumes']));flat=[]
        for face,v in zip(obj.data.polygons,state['volumes']):
            fraction=v/vmax;color=(.04+.25*(1-fraction),.15+.55*fraction,.25+.7*fraction,1.)
            for _ in face.loop_indices:flat.extend(color)
        colors.data.foreach_set('color',flat);obj.data.color_attributes.active_color=colors
        obj['volume_quanta']=state['volumes'];obj['quantum_m3']=spec['quantum']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.shading.color_type='VERTEX' if spec['mode']=='water' else 'OBJECT'

def selected_geometry(context):
    obj=context.object
    if not obj or obj.type!='MESH' or obj.get('chimera_gpu_preview') or obj.get('chimera_preview'):raise ValueError('Select an editable mesh')
    if abs(context.scene.unit_settings.scale_length-1)>1e-9:raise ValueError('Use meters, Unit Scale 1')
    if obj.mode=='EDIT':obj.update_from_editmode()
    if obj.modifiers:raise ValueError('Apply modifiers before assigning native topology')
    mesh=obj.data;mesh.calc_loop_triangles()
    p=np.asarray([(*v.co,1) for v in mesh.vertices],dtype=float)@np.asarray(obj.matrix_world,dtype=float).T
    return obj,p[:,:3],[list(t.vertices) for t in mesh.loop_triangles]

class Settings(bpy.types.PropertyGroup):
    tension:FloatProperty(name='Surface tension J/m²',default=1,min=.000001,max=1000)
    load:FloatProperty(name='Center load N',default=.5,min=0,max=10)
    volume:FloatProperty(name='Water m³',default=.0001,min=1e-10,max=1,precision=6)
    pipe:FloatProperty(name='CA pipe height m',default=.01,min=.000001,max=1,precision=5)
    ca_steps:IntProperty(name='CA steps per advance',default=1,min=1,max=64)
    replay:IntProperty(name='Checkpoint',default=0,min=0)

class Demo(bpy.types.Operator):
    bl_idname='chimera.gpu_demo';bl_label='Add Membrane GPU Fixture';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        spec=g.fixture_spec();mesh=bpy.data.meshes.new('Pinned B2 membrane');mesh.from_pydata(spec['positions'],[],spec['triangles']);mesh.update()
        obj=bpy.data.objects.new('Matter membrane fan',mesh);context.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);context.view_layer.objects.active=obj
        for v in mesh.vertices:v.select=v.index==spec['centre']
        obj['chimera_free_center']=spec['centre'];context.scene.unit_settings.scale_length=1
        message('Fixture added: one free Z-rail center, pinned rim. Build Membrane on GPU.');return {'FINISHED'}

class BuildMembrane(bpy.types.Operator):
    bl_idname='chimera.gpu_membrane';bl_label='Build Membrane on GPU'
    def execute(self,context):
        try:
            obj,p,t=selected_geometry(context);selected=[v.index for v in obj.data.vertices if v.select]
            if len(selected)!=1:raise ValueError('In Edit Mode select exactly one free center vertex; all others are pinned')
            spec=g.membrane_spec(p,t,selected[0],context.scene.chimera_gpu.tension)
            if busy():raise RuntimeError('GPU operation in progress')
            return_to_authoring()
            _visibility[obj.name]=obj.hide_get()
            submit(lambda:g.GpuSession(spec))
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class BuildWater(bpy.types.Operator):
    bl_idname='chimera.gpu_water';bl_label='Build CA Water Field'
    def execute(self,context):
        try:
            obj,p,t=selected_geometry(context)
            selected=[i for i,tr in enumerate(obj.data.loop_triangles) if obj.data.polygons[tr.polygon_index].select]
            if len(selected)!=1:raise ValueError('Select exactly one triangular face as the initial water cell')
            settings=context.scene.chimera_gpu;spec=g.water_spec(p,t,selected[0],settings.volume,settings.pipe)
            if busy():raise RuntimeError('GPU operation in progress')
            return_to_authoring()
            _visibility[obj.name]=obj.hide_get()
            submit(lambda:g.GpuSession(spec))
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class Advance(bpy.types.Operator):
    bl_idname='chimera.gpu_step';bl_label='Advance Native GPU Step'
    def execute(self,context):
        try:
            r=current();count=context.scene.chimera_gpu.ca_steps if r.spec['mode']=='water' else 1
            submit(lambda:r.advance(count))
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Deform(bpy.types.Operator):
    bl_idname='chimera.gpu_load';bl_label='Apply Center Load'
    def execute(self,context):
        try:r=current();load=context.scene.chimera_gpu.load;submit(lambda:r.deform(load))
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Seek(bpy.types.Operator):
    bl_idname='chimera.gpu_seek';bl_label='Replay Native Checkpoint'
    def execute(self,context):
        try:r=current();index=context.scene.chimera_gpu.replay;submit(lambda:r.seek(index))
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Resume(bpy.types.Operator):
    bl_idname='chimera.gpu_resume';bl_label='Resume Saved GPU Matter'
    def execute(self,context):
        try:
            doc=document()
            if not doc:raise ValueError('No saved matter trial')
            if busy():raise RuntimeError('GPU operation in progress')
            close_session();submit(lambda:g.GpuSession.restore(doc))
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Release(bpy.types.Operator):
    bl_idname='chimera.gpu_release';bl_label='Release Studio GPU Memory'
    def execute(self,context):
        global _saved
        _saved=document();close_session();message('Private engine closed. Confirmed checkpoint retained for resume.');return {'FINISHED'}

def return_to_authoring():
    global _saved,_visibility
    close_session()
    for name,hidden in _visibility.items():
        obj=bpy.data.objects.get(name)
        if obj:obj.hide_set(hidden)
    _visibility={};_saved=None
    col=bpy.data.collections.get(COLLECTION)
    if col:
        for obj in col.objects:
            if obj.get('chimera_gpu_preview'):obj.hide_set(True)
class Authoring(bpy.types.Operator):
    bl_idname='chimera.gpu_authoring';bl_label='Return to Matter Authoring'
    def execute(self,context):
        return_to_authoring();message('Editable source restored; GPU preview hidden.');return {'FINISHED'}

class Save(bpy.types.Operator,ExportHelper):
    bl_idname='chimera.gpu_save';bl_label='Save GPU Matter Trial';filename_ext='.matter.json'
    filter_glob:StringProperty(default='*.matter.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            doc=document()
            if not doc:raise ValueError('No confirmed GPU state to save')
            p=Path(self.filepath);temp=p.with_name(p.name+'.tmp');temp.write_text(json.dumps(doc,allow_nan=False,indent=2),encoding='utf-8');temp.replace(p)
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
def load_document(doc):
    global _saved,_visibility
    g.validate_document(doc)
    visibility=doc.get('authoring_visibility',{})
    if not isinstance(visibility,dict) or len(visibility)>32 or any(not isinstance(k,str) or type(v)!=bool for k,v in visibility.items()):raise ValueError('Invalid authoring visibility metadata')
    return_to_authoring();_visibility=dict(visibility);_saved=copy.deepcopy(doc);sync_preview(_saved);message('Saved native checkpoint displayed. Resume explicitly to use GPU.')
class Load(bpy.types.Operator,ImportHelper):
    bl_idname='chimera.gpu_open';bl_label='Open GPU Matter Trial'
    filter_glob:StringProperty(default='*.matter.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            p=Path(self.filepath)
            if p.stat().st_size>g.MAX_DOC:raise ValueError('Matter trial exceeds 8 MiB')
            load_document(json.loads(p.read_text(encoding='utf-8')))
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Panel(bpy.types.Panel):
    bl_label='GPU Matter';bl_idname='CHIMERA_PT_gpu';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Chimera'
    def draw(self,context):
        l=self.layout;s=context.scene.chimera_gpu
        l.label(text='Existing Chimera Vulkan solver');l.operator('chimera.gpu_demo')
        box=l.box();box.enabled=not busy();box.prop(s,'tension');box.operator('chimera.gpu_membrane');box.prop(s,'load');box.operator('chimera.gpu_load')
        box=l.box();box.enabled=not busy();box.prop(s,'volume');box.prop(s,'pipe');box.operator('chimera.gpu_water')
        row=l.column();row.enabled=not busy();row.prop(s,'ca_steps');row.operator('chimera.gpu_step');row.operator('chimera.gpu_resume')
        if _session:
            l.label(text=f'{len(_session.history)} confirmed checkpoints');row=l.column();row.enabled=not busy();row.prop(s,'replay');row.operator('chimera.gpu_seek')
        l.operator('chimera.gpu_save');l.operator('chimera.gpu_open');l.operator('chimera.gpu_release');l.operator('chimera.gpu_authoring')
        l.label(text=_message[:65]);l.label(text=_message[65:130])
        l.label(text='Fan: one free center, pinned rim');l.label(text='CA: closed boundary; full-flow replay')

@persistent
def save_pre(_):
    doc=document();text=bpy.data.texts.get(TEXT)
    if doc:
        raw=json.dumps(doc,allow_nan=False,separators=(',',':'))
        if len(raw)>g.MAX_DOC:raise ValueError('GPU trial exceeds 8 MiB')
        if text is None:text=bpy.data.texts.new(TEXT)
        text.clear();text.write(raw)
    elif text:bpy.data.texts.remove(text)
@persistent
def load_pre(_):
    global _saved,_visibility
    close_session();_saved=None;_visibility={}
@persistent
def load_post(_):
    text=bpy.data.texts.get(TEXT)
    if text:
        try:
            raw=text.as_string()
            if len(raw)>g.MAX_DOC:raise ValueError('GPU trial exceeds 8 MiB')
            load_document(json.loads(raw))
        except Exception as exc:message('Saved GPU matter refused: '+str(exc))
CLASSES=(Settings,Demo,BuildMembrane,BuildWater,Advance,Deform,Seek,Resume,Release,Authoring,Save,Load,Panel)
def register():
    for cls in CLASSES:bpy.utils.register_class(cls)
    bpy.types.Scene.chimera_gpu=PointerProperty(type=Settings)
    for handlers,fn in ((bpy.app.handlers.save_pre,save_pre),(bpy.app.handlers.load_pre,load_pre),(bpy.app.handlers.load_post,load_post)):
        if fn not in handlers:handlers.append(fn)
    if not bpy.app.background:bpy.app.timers.register(poll,first_interval=.1,persistent=True)
def unregister():
    close_session()
    if bpy.app.timers.is_registered(poll):bpy.app.timers.unregister(poll)
    for handlers,fn in ((bpy.app.handlers.save_pre,save_pre),(bpy.app.handlers.load_pre,load_pre),(bpy.app.handlers.load_post,load_post)):
        if fn in handlers:handlers.remove(fn)
    if hasattr(bpy.types.Scene,'chimera_gpu'):del bpy.types.Scene.chimera_gpu
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)
