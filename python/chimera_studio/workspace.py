# SPDX-License-Identifier: AGPL-3.0-or-later
# Blender calls occur only on its main thread. Native solver remains authoritative.
import json
import math
import time
import uuid
from pathlib import Path
import bpy
import numpy as np
from bpy.props import BoolProperty,FloatProperty,StringProperty,EnumProperty,IntProperty,PointerProperty
from bpy_extras.io_utils import ExportHelper,ImportHelper
from mathutils import Matrix,Vector,Quaternion
from .native import NativeScene,NativeError,ROOT
from .geometry import compile_convex,attachment_between

_TO_ENGINE=Matrix(((1,0,0),(0,0,1),(0,-1,0)))
_TO_BLENDER=_TO_ENGINE.transposed()
_PREVIEW='Chimera Simulation'
_TRIAL_TEXT='Chimera Physical Trial.json'
_runtime=None
_PROFILES={'TIMBER':(600.,.3,(.45,.22,.07,1.)), 'STEEL':(7850.,.4,(.3,.4,.5,1.)), 'STONE':(2700.,.5,(.4,.4,.38,1.)), 'CUSTOM':(1000.,.4,(.2,.6,.6,1.))}

def lock_identity():
    import hashlib
    return hashlib.sha256((ROOT/'SOURCE_LOCK.json').read_bytes()).hexdigest()

class Session:
    def __init__(self):
        self.native=NativeScene();self.running=False;self.history=[];self.cursor=-1
        self.accumulator=0.;self.last_wall=time.perf_counter();self.preview={};self.source_visibility={}
        self.materials={};self.ports={};self.baseline=None;self.last_ms=0.;self.history_bytes=0
    def close(self):
        self.running=False;self.native.close()
        for name,hidden in self.source_visibility.items():
            obj=bpy.data.objects.get(name)
            if obj: obj.hide_set(hidden)
    def record(self):
        state=self.native.call('save');raw=json.dumps(state,separators=(',',':'))
        if self.cursor<len(self.history)-1:
            self.history=self.history[:self.cursor+1];self.history_bytes=sum(len(x) for x in self.history)
        self.history.append(raw);self.history_bytes+=len(raw)
        while len(self.history)>240 or self.history_bytes>32*1024*1024:
            self.history_bytes-=len(self.history.pop(0))
        self.cursor=len(self.history)-1
    def sync(self):
        parts=self.native.call('parts')['parts']
        for part in parts:
            obj=self.preview.get(part['id'])
            if not obj or obj.name not in bpy.data.objects: continue
            rot=Quaternion(part['pose_q_wxyz']).to_matrix()
            obj.matrix_world=(_TO_BLENDER@rot@_TO_ENGINE).to_4x4()
            obj.matrix_world.translation=_TO_BLENDER@Vector(part['pose_c_m'])
    def advance(self,steps=80):
        self.native.call('pause',False)
        t=time.perf_counter()
        try:self.native.advance(steps)
        finally:self.native.call('pause',True)
        self.last_ms=(time.perf_counter()-t)*1000;self.sync();self.record()
    def seek(self,index):
        if not 0<=index<len(self.history): raise ValueError('Replay frame outside recorded range')
        self.running=False;self.native.call('restore',json.loads(self.history[index]));self.native.call('pause',True)
        self.cursor=index;self.accumulator=0.;self.sync()
    def create_preview(self):
        col=bpy.data.collections.get(_PREVIEW)
        if col is None: col=bpy.data.collections.new(_PREVIEW);bpy.context.scene.collection.children.link(col)
        for obj in list(col.objects):
            if obj.get('chimera_preview'):
                mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
                if mesh.users==0: bpy.data.meshes.remove(mesh)
        state=self.native.call('save');self.preview={}
        for part in state['parts']:
            verts=part['vertices_local_m'];com=Vector(part['com_local_m'])
            points=[tuple(_TO_BLENDER@(Vector(verts[i:i+3])-com)) for i in range(0,len(verts),3)]
            tris=part['boundary_triangles'];faces=[tris[i:i+3] for i in range(0,len(tris),3)]
            mesh=bpy.data.meshes.new(part['id']+' view');mesh.from_pydata(points,[],faces);mesh.update()
            obj=bpy.data.objects.new('Sim '+part['id'],mesh);col.objects.link(obj);obj['chimera_preview']=True;obj['part_id']=part['id'];obj.hide_select=True
            info=self.materials.get(part['id'],{});obj.name='Sim '+info.get('object',part['id']);obj.color=info.get('color',[.2,.6,.6,1.]);self.preview[part['id']]=obj
        self.sync()

def current():
    if _runtime is None: raise RuntimeError('Build a scene first')
    return _runtime

def status(message):
    scene=bpy.context.scene
    if scene and hasattr(scene,'chimera'):scene.chimera.status=message[:500]

def build_selected(context):
    global _runtime
    selected=[o for o in context.selected_objects if o.type=='MESH' and not o.get('chimera_preview')]
    if not 2<=len(selected)<=6: raise ValueError('Select 2 to 6 separate convex material regions; current engine cap is 6')
    if abs(context.scene.unit_settings.scale_length-1)>1e-9: raise ValueError('Use meters with Unit Scale 1 for this bridge')
    parts=[];metadata={};ports={};ids=set()
    dg=context.evaluated_depsgraph_get()
    for obj in selected:
        cfg=obj.chimera
        if not cfg.material_id: raise ValueError(obj.name+': assign a Chimera material first')
        pid=cfg.part_id or uuid.uuid4().hex[:16]
        if pid in ids: raise ValueError('Duplicate part ID: reassign the copied object before building')
        ids.add(pid)
        evaluated=obj.evaluated_get(dg);mesh=evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            local=np.array([(*v.co,1.) for v in mesh.vertices],dtype=np.float64)
            world=(local@np.array(evaluated.matrix_world,dtype=np.float64).T)[:,:3]
            verts=(world@np.array(_TO_ENGINE,dtype=np.float64).T).tolist()
            tris=[list(t.vertices) for t in mesh.loop_triangles]
            part,receipt=compile_convex(pid,verts,tris,cfg.density,cfg.friction,cfg.source)
        finally:evaluated.to_mesh_clear()
        if obj.get('chimera_mount_face') is not None:
            if len(obj.modifiers):raise ValueError('Apply modifiers before using marked mounts')
            indices=list(obj['chimera_mount_face'])
            if any(i<0 or i>=len(verts) for i in indices) or not any(list(f.vertices)==indices for f in obj.data.polygons):raise ValueError('Mount topology changed; mark the face again')
            face=np.array([verts[i] for i in indices])
            if np.dot(np.cross(face[1]-face[0],face[2]-face[0]),face.mean(axis=0)-np.asarray(part['com_local_m']))<0:face=face[::-1]
            ports[pid]=face.tolist()
        parts.append(part);metadata[pid]={'object':obj.name,'material_id':cfg.material_id,'density_kg_m3':cfg.density,'source':cfg.source,'color':list(obj.color),'volume_m3':receipt['geometric_volume_m3']}
        cfg.part_id=pid
    candidate=Session()
    try:
        candidate.native.call('admit',{'schema':'chimera.b2_scene.v1','gravity_m_s2':9.81,'parts':parts,'reason':'Chimera Studio material regions'})
        candidate.native.call('pause',True);candidate.materials=metadata;candidate.ports=ports
        candidate.baseline=candidate.native.call('save')
    except Exception:candidate.close();raise
    if _runtime:_runtime.close()
    _runtime=candidate
    candidate.create_preview()
    for obj in selected:candidate.source_visibility[obj.name]=obj.hide_get();obj.hide_set(True)
    candidate.record();status('Built: rigid mass, inertia and contact. Strength/deformation not claimed.')
    return candidate

def tick():
    if _runtime and _runtime.running:
        try:
            now=time.perf_counter();_runtime.accumulator+=now-_runtime.last_wall;_runtime.last_wall=now
            # All admitted substeps run. Backlog slows visible simulation; none are discarded.
            n=min(200,int(_runtime.accumulator*4000))
            if n:
                _runtime.advance(n);_runtime.accumulator-=n/4000
                state=_runtime.native.call('state')
                status(f"Playing | {state.get('steps',0)} native steps | {_runtime.last_ms:.2f} ms batch | backlog {_runtime.accumulator:.3f}s")
        except Exception as exc:_runtime.running=False;status('Stopped: '+str(exc))
    return .02

class ObjectSettings(bpy.types.PropertyGroup):
    part_id:StringProperty(name='Part identity')
    material_id:StringProperty(name='Physical material',default='')
    profile:EnumProperty(name='Demo profile',items=[('TIMBER','Timber (authored)',''),('STEEL','Steel (authored)',''),('STONE','Stone (authored)',''),('CUSTOM','Custom','')])
    density:FloatProperty(name='Density kg/m³',default=600.,min=.001,max=100000.)
    friction:FloatProperty(name='Contact friction',default=.3,min=0.,max=2.)
    source:StringProperty(name='Source/conditions',default='Authored demo values; rigid mass/contact only')
class SceneSettings(bpy.types.PropertyGroup):
    status:StringProperty(name='State',default='Select objects, assign materials, then Build')
    replay_index:IntProperty(name='Recorded sample',default=0,min=0)

class Assign(bpy.types.Operator):
    bl_idname='chimera.assign_material';bl_label='Assign Physical Material';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        for obj in context.selected_objects:
            if obj.type!='MESH' or obj.get('chimera_preview'):continue
            cfg=obj.chimera;cfg.part_id=uuid.uuid4().hex[:16]
            if cfg.profile!='CUSTOM':cfg.density,cfg.friction,color=_PROFILES[cfg.profile];obj.color=color
            cfg.material_id=cfg.profile.lower()
        status('Material assigned to each whole object. Separate objects define separate regions.');return {'FINISHED'}

class MarkMount(bpy.types.Operator):
    bl_idname='chimera.mark_mount';bl_label='Mark Selected Face as Mount';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        obj=context.object
        if not obj or obj.type!='MESH' or obj.get('chimera_preview'):
            self.report({'ERROR'},'Select an authored mesh face');return {'CANCELLED'}
        if obj.mode=='EDIT':obj.update_from_editmode()
        faces=[p for p in obj.data.polygons if p.select]
        if len(faces)!=1 or len(obj.modifiers):
            self.report({'ERROR'},'Select exactly one face in Edit Mode; apply modifiers first');return {'CANCELLED'}
        obj['chimera_mount_face']=list(faces[0].vertices)
        status('Mount marked. Mark its opposing face on another region, align, then Build.');return {'FINISHED'}
class Join(bpy.types.Operator):
    bl_idname='chimera.join_mounts';bl_label='Join Two Marked Mounts'
    def execute(self,context):
        try:
            r=current();r.running=False
            if r.native.call('state')['steps']!=0:raise ValueError('Join before advancing; restore the built state first')
            keys=list(r.ports)
            if len(keys)!=2:raise ValueError('First bridge needs exactly two marked mount faces')
            doc=attachment_between(keys[0],r.ports[keys[0]],keys[1],r.ports[keys[1]])
            r.native.call('weld',doc);r.baseline=r.native.call('save');r.record();status('Finite-area native connection applied')
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class Build(bpy.types.Operator):
    bl_idname='chimera.build';bl_label='Build Selected Regions'
    def execute(self,context):
        try:build_selected(context)
        except Exception as exc:self.report({'ERROR'},str(exc));status(str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Play(bpy.types.Operator):
    bl_idname='chimera.play';bl_label='Play / Pause'
    def execute(self,context):
        try:
            r=current();r.running=not r.running;r.last_wall=time.perf_counter();status('Playing' if r.running else 'Paused')
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Step(bpy.types.Operator):
    bl_idname='chimera.step';bl_label='Step 20 ms'
    bl_description='Advance exactly 80 native substeps of 0.25 ms each'
    def execute(self,context):
        try:r=current();r.running=False;r.advance(80);status('Advanced 80 native substeps')
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Reset(bpy.types.Operator):
    bl_idname='chimera.reset';bl_label='Restore Built State'
    def execute(self,context):
        try:
            r=current();r.running=False;r.native.call('restore',r.baseline);r.sync();r.history=[];r.history_bytes=0;r.record();r.accumulator=0.;status('Restored the built physical state')
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
class Edit(bpy.types.Operator):
    bl_idname='chimera.edit';bl_label='Return to Authoring'
    def execute(self,context):
        global _runtime
        if _runtime:_runtime.close();_runtime=None
        col=bpy.data.collections.get(_PREVIEW)
        if col:
            for obj in col.objects:obj.hide_set(True)
        status('Authoring draft. Build explicitly to start a new simulation.');return {'FINISHED'}
class Seek(bpy.types.Operator):
    bl_idname='chimera.seek';bl_label='Inspect Recorded State'
    def execute(self,context):
        try:current().seek(context.scene.chimera.replay_index);status('Replay: exact native checkpoint restored; Play branches from here')
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class Save(bpy.types.Operator,ExportHelper):
    bl_idname='chimera.save_trial';bl_label='Save Physical Trial';filename_ext='.chimera.json'
    filter_glob:StringProperty(default='*.chimera.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            r=current();r.running=False
            bundle=trial_document(r)
            dest=Path(self.filepath);tmp=dest.with_name(dest.name+'.tmp');tmp.write_text(json.dumps(bundle,indent=2,allow_nan=False),encoding='utf-8');tmp.replace(dest)
            status('Saved physical state and material identities')
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}
def trial_document(r):
    return {'schema':'chimera.studio.trial.v1','source_lock':lock_identity(),
            'state':r.native.call('save'),'baseline':r.baseline,'materials':r.materials,
            'ports':r.ports,'authoring_visibility':r.source_visibility}


def restore_trial(doc,context,from_blend=False):
    global _runtime
    if not isinstance(doc,dict) or doc.get('schema')!='chimera.studio.trial.v1' or doc.get('source_lock')!=lock_identity():
        raise ValueError('Trial engine source identity mismatch')
    metadata=doc.get('materials');ports=doc.get('ports',{});visibility=doc.get('authoring_visibility',{})
    if not isinstance(metadata,dict) or not isinstance(ports,dict) or not isinstance(visibility,dict):raise ValueError('Malformed trial metadata')
    for info in metadata.values():
        if not isinstance(info,dict):raise ValueError('Malformed material record')
        color=info.get('color',[.2,.6,.6,1.])
        if not isinstance(color,list) or len(color)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in color):raise ValueError('Invalid material display color')
    for points in ports.values():
        arr=np.asarray(points,dtype=float)
        if arr.ndim!=2 or arr.shape[1]!=3 or len(arr)<3 or not np.isfinite(arr).all():raise ValueError('Malformed mount geometry')
    candidate=Session()
    try:
        candidate.native.call('restore',doc['baseline']);candidate.native.call('restore',doc['state']);candidate.native.call('pause',True)
        ids={p['id'] for p in candidate.native.call('parts')['parts']}
        if set(metadata)!=ids or not set(ports)<=ids:raise ValueError('Material/mount identities do not match native parts')
        candidate.baseline=doc['baseline'];candidate.materials=metadata;candidate.ports=ports
    except Exception:candidate.close();raise
    if _runtime:_runtime.close()
    _runtime=candidate;candidate.create_preview()
    for obj in context.scene.objects:
        if not obj.get('chimera_preview') and obj.chimera.part_id in candidate.materials:
            hidden=visibility.get(obj.name,False) if from_blend else obj.hide_get()
            candidate.source_visibility[obj.name]=bool(hidden);obj.hide_set(True)
    candidate.record();status('Physical trial restored')
    return candidate


class Load(bpy.types.Operator,ImportHelper):
    bl_idname='chimera.load_trial';bl_label='Open Physical Trial'
    filter_glob:StringProperty(default='*.chimera.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            file=Path(self.filepath)
            if file.stat().st_size>32*1024*1024:raise ValueError('Trial exceeds 32 MiB limit')
            restore_trial(json.loads(file.read_text(encoding='utf-8')),context)
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
        return {'FINISHED'}

class Demo(bpy.types.Operator):
    bl_idname='chimera.demo';bl_label='Add Starter Workshop'
    def execute(self,context):
        bpy.ops.object.select_all(action='DESELECT');added=[]
        for name,position,size,profile in [('Panel',(0,0,.2),(.45,.3,.12),'TIMBER'),('Block',(0,0,.35),(.18,.18,.18),'STEEL')]:
            bpy.ops.mesh.primitive_cube_add(size=1,location=position);obj=context.object;obj.name='Chimera '+name;obj.scale=size;obj.chimera.profile=profile
            bpy.ops.chimera.assign_material()
            face=max(obj.data.polygons,key=lambda f:f.normal.z*(1 if name=='Panel' else -1))
            obj['chimera_mount_face']=list(face.vertices);added.append(obj)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in added:obj.select_set(True)
        context.view_layer.objects.active=added[0];context.scene.unit_settings.system='METRIC';context.scene.unit_settings.scale_length=1
        status('Aligned starter regions added. Build, then optionally Join Two Marked Mounts before Play.');return {'FINISHED'}

class Panel(bpy.types.Panel):
    bl_label='Chimera Studio';bl_idname='CHIMERA_PT_workshop';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Chimera'
    def draw(self,context):
        l=self.layout;l.label(text='Native construction engine');l.operator('chimera.demo',icon='CUBE')
        o=context.object
        if _runtime is None and o and o.type=='MESH' and not o.get('chimera_preview'):
            b=l.box();b.label(text=o.name);b.prop(o.chimera,'profile');b.operator('chimera.assign_material');b.prop(o.chimera,'density');b.prop(o.chimera,'friction');b.prop(o.chimera,'material_id');b.prop(o.chimera,'source')
        l.operator('chimera.mark_mount');l.operator('chimera.build',icon='MOD_PHYSICS');l.operator('chimera.join_mounts');row=l.row();row.operator('chimera.play',icon='PLAY');row.operator('chimera.step')
        l.operator('chimera.reset',icon='LOOP_BACK');l.operator('chimera.edit',icon='EDITMODE_HLT')
        l.operator('chimera.save_trial',icon='FILE_TICK');l.operator('chimera.load_trial',icon='FILE_FOLDER')
        if _runtime:
            b=l.box();b.label(text=f'Replay: {len(_runtime.history)} checkpoints');b.prop(context.scene.chimera,'replay_index');b.operator('chimera.seek')
            try:
                for part in _runtime.native.call('parts')['parts']:b.label(text=f"{_runtime.materials.get(part['id'],{}).get('object',part['id'][:8])}: {part['mass_kg']:.3f} kg")
            except Exception:pass
        l.label(text=context.scene.chimera.status[:75]);l.label(text='Rigid/contact scope; 2–6 convex regions')

from bpy.app.handlers import persistent
@persistent
def before_file_load(_):
    global _runtime
    if _runtime:_runtime.close();_runtime=None

@persistent
def before_file_save(_):
    # Store plain JSON, never executable code. Native history stays bounded in memory.
    text=bpy.data.texts.get(_TRIAL_TEXT)
    if _runtime:
        raw=json.dumps(trial_document(_runtime),allow_nan=False,separators=(',',':'))
        if len(raw)>32*1024*1024:raise ValueError('Physical trial exceeds 32 MiB')
        if text is None:text=bpy.data.texts.new(_TRIAL_TEXT)
        text.clear();text.write(raw)
    elif text:bpy.data.texts.remove(text)

@persistent
def after_file_load(_):
    text=bpy.data.texts.get(_TRIAL_TEXT)
    if text:
        try:
            raw=text.as_string()
            if len(raw)>32*1024*1024:raise ValueError('Embedded trial exceeds 32 MiB')
            restore_trial(json.loads(raw),bpy.context,from_blend=True)
        except Exception as exc:status('Saved geometry loaded; physical trial refused: '+str(exc))

CLASSES=(ObjectSettings,SceneSettings,Assign,MarkMount,Join,Build,Play,Step,Reset,Edit,Seek,Save,Load,Demo,Panel)
_sidebar_attempts=0

def focus_sidebar():
    global _sidebar_attempts
    _sidebar_attempts+=1
    ready=True
    for window in bpy.context.window_manager.windows:
        screen=window.screen
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.show_region_ui=True
                for region in area.regions:
                    if region.type=='UI':
                        try:region.active_panel_category='Chimera';area.tag_redraw()
                        except (AttributeError,TypeError,ValueError,RuntimeError):ready=False
    return .25 if not ready and _sidebar_attempts<8 else None

def register():
    global _sidebar_attempts
    _sidebar_attempts=0
    for cls in CLASSES:bpy.utils.register_class(cls)
    bpy.types.Object.chimera=PointerProperty(type=ObjectSettings);bpy.types.Scene.chimera=PointerProperty(type=SceneSettings)
    for handlers,fn in ((bpy.app.handlers.load_pre,before_file_load),(bpy.app.handlers.load_post,after_file_load),(bpy.app.handlers.save_pre,before_file_save)):
        if fn not in handlers:handlers.append(fn)
    if not bpy.app.background:
        bpy.app.timers.register(tick,first_interval=.02,persistent=True)
        bpy.app.timers.register(focus_sidebar,first_interval=.5)
def unregister():
    global _runtime
    for handlers,fn in ((bpy.app.handlers.load_pre,before_file_load),(bpy.app.handlers.load_post,after_file_load),(bpy.app.handlers.save_pre,before_file_save)):
        if fn in handlers:handlers.remove(fn)
    for fn in (tick,focus_sidebar):
        if bpy.app.timers.is_registered(fn):bpy.app.timers.unregister(fn)
    if _runtime:_runtime.close();_runtime=None
    for typ in (bpy.types.Object,bpy.types.Scene):
        if hasattr(typ,'chimera'):delattr(typ,'chimera')
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)
