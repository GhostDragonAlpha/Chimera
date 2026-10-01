"""Pinned macaque anatomy -> typed graph proposal -> metric native bone assembly.

This is a strict OpenSim 3 geometry/parameter adapter, not an OpenSim dynamics
implementation. Muscle wrapping, conditional points and model assumptions survive
as data; no unresolved path is silently promoted to a functioning actuator.
"""
import argparse, copy, json, struct, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import numpy as np
from .common import canonical, require, sha, local_file
from tools.creature_graph.store import CreatureGraph
from tools.creature_graph.views import layout_roadmap

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'tools/science_funnel/data/macaque_arm'
SOURCE='source.anatomy.macaque_arm'
MODEL='model.anatomy.macaque_arm'

def numbers(text, count=None):
    require(text is not None,'missing_numeric_field')
    a=np.asarray([float(x) for x in text.split()],dtype=np.float64)
    require(np.isfinite(a).all() and (count is None or len(a)==count),'invalid_numeric_field',text)
    return a

def vec(node,name,default=None,count=3):
    return numbers(node.findtext(name,default),count).tolist()

def rotation(axis,angle):
    a=np.asarray(axis,dtype=float);require(abs(np.linalg.norm(a)-1)<1e-6,'axis_not_unit')
    x,y,z=a;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+np.sin(angle)*K+(1-np.cos(angle))*(K@K)

def frame(location,orientation):
    t=np.eye(4)
    for axis,angle in zip(np.eye(3),orientation):t[:3,:3]=t[:3,:3]@rotation(axis,angle)
    t[:3,3]=location
    return t

def xml_record(node):
    return {'tag':node.tag,'attributes':dict(node.attrib),'text':(node.text or '').strip(),'children':[xml_record(c) for c in node]}

def parse_source(data=DATA):
    receipt=json.loads((data/'download_receipt.json').read_text(encoding='utf-8'))
    require(receipt['revision']=='4fb7dddeec06a0df9525c18f37234a824cb1b5b1' and receipt['license']=='MIT','source_identity')
    blobs={}
    for f in receipt['files']:
        raw=local_file(data,f['path']).read_bytes();require(sha(raw)==f['sha256'] and len(raw)==f['bytes'],'source_pin_drift',f['path']);blobs[f['path']]=raw
    doc=ET.fromstring(blobs['monkeyArm_current.osim']);require(doc.get('Version')=='30000','unsupported_opensim_version')
    m=doc.find('Model');require(m.findtext('length_units')=='meters' and m.findtext('force_units')=='N','unsupported_units')
    bodies=[];coordinates={};body_names=set()
    for b in m.findall('./BodySet/objects/Body'):
        name=b.get('name');require(name not in body_names,'duplicate_body');body_names.add(name)
        inertia=[float(b.findtext('inertia_'+k)) for k in ('xx','yy','zz','xy','xz','yz')]
        require(np.isfinite(inertia).all(),'nonfinite_inertia')
        rec={'name':name,'mass_kg':float(b.findtext('mass')),'mass_center_m':vec(b,'mass_center'),'inertia_kg_m2':inertia,'mass_scope':'effective body segment, not isolated visible bone','geometry':[],'wrap_objects':[xml_record(x) for x in b.findall('./WrapObjectSet/objects/*')]}
        require(np.isfinite(rec['mass_kg']) and rec['mass_kg']>=0,'invalid_mass')
        joint=list(b.find('Joint'))
        require(len(joint)<=1,'multiple_body_joints')
        if joint:
            j=joint[0];require(j.tag in ('WeldJoint','CustomJoint'),'unsupported_joint',j.tag)
            require(j.findtext('reverse','false')=='false','reverse_joint_unsupported')
            jr={'name':j.get('name'),'type':j.tag,'parent':j.findtext('parent_body'),'parent_location_m':vec(j,'location_in_parent'),'parent_orientation_rad':vec(j,'orientation_in_parent'),'child_location_m':vec(j,'location'),'child_orientation_rad':vec(j,'orientation'),'axes':[]}
            for q in j.findall('./CoordinateSet/objects/Coordinate'):
                qn=q.get('name');require(qn not in coordinates,'duplicate_coordinate',qn)
                require(q.findtext('motion_type')=='rotational','unsupported_coordinate_type')
                coordinates[qn]={'default_rad':float(q.findtext('default_value')),'range_rad':vec(q,'range',count=2),'locked':q.findtext('locked','false')=='true'}
                qr=coordinates[qn];require(np.isfinite([qr['default_rad']]+qr['range_rad']).all() and qr['range_rad'][0]<=qr['default_rad']<=qr['range_rad'][1],'coordinate_range',qn)
            axes=j.findall('./SpatialTransform/TransformAxis')
            require(j.tag!='CustomJoint' or [x.get('name') for x in axes]==['rotation1','rotation2','rotation3','translation1','translation2','translation3'],'transform_axis_order')
            for ax in axes:
                f=list(ax.find('function'));require(len(f)==1 and f[0].tag in ('Constant','LinearFunction'),'unsupported_transform_function')
                f=f[0];coord=(ax.findtext('coordinates') or '').strip();axis=vec(ax,'axis')
                require(abs(np.linalg.norm(axis)-1)<1e-6,'axis_not_unit')
                fun={'type':f.tag,'coefficients':vec(f,'coefficients',count=2) if f.tag=='LinearFunction' else [float(f.findtext('value'))]}
                require(np.isfinite(fun['coefficients']).all(),'nonfinite_function')
                require((f.tag=='Constant' and not coord) or (f.tag=='LinearFunction' and coord in coordinates),'function_coordinate')
                jr['axes'].append({'name':ax.get('name'),'axis':axis,'coordinate':coord,'function':fun})
            rec['joint']=jr
        else:require(name=='ground','unconnected_body');rec['joint']=None
        v=b.find('VisibleObject');outer=vec(v,'scale_factors','1 1 1')
        require(np.asarray(outer).min()>0,'invalid_geometry_scale')
        for geom in v.findall('./GeometrySet/objects/DisplayGeometry'):
            path='Geometry/'+geom.findtext('geometry_file');require(path in blobs,'geometry_not_pinned',path)
            transform=vec(geom,'transform','0 0 0 0 0 0',6);require(not any(transform),'display_transform_unsupported')
            scale=(np.asarray(outer)*vec(geom,'scale_factors','1 1 1')).tolist()
            require(np.asarray(scale).min()>0,'invalid_geometry_scale')
            rec['geometry'].append({'path':path,'sha256':sha(blobs[path]),'source_units_to_m':scale})
        bodies.append(rec)
    muscles=[]
    for msc in m.findall('./ForceSet/objects/*'):
        require(msc.tag=='Schutte1993Muscle_Deprecated','unsupported_muscle_record',msc.tag)
        points=[]
        for i,p in enumerate(msc.findall('./GeometryPath/PathPointSet/objects/*')):
            require(p.tag in ('PathPoint','ConditionalPathPoint'),'unsupported_path_point')
            require(p.findtext('body') in body_names,'attachment_body_missing')
            pr={'ordinal':i,'name':p.get('name'),'type':p.tag,'body':p.findtext('body'),'location_m':vec(p,'location')}
            if p.tag=='ConditionalPathPoint':
                pr.update(coordinate=p.findtext('coordinate'),range_rad=vec(p,'range',count=2));require(pr['coordinate'] in coordinates,'condition_coordinate_missing')
            points.append(pr)
        wraps=[xml_record(x) for x in msc.findall('./GeometryPath/PathWrapSet/objects/*')]
        params={};curves=[]
        for x in msc:
            if x.tag=='GeometryPath':continue
            if len(x):curves.append(xml_record(x))
            else:params[x.tag]=(x.text or '').strip()
        muscles.append({'name':msc.get('name'),'source_model':msc.tag,'points':points,'wraps':wraps,'parameters_source_text':params,'curves':curves,'force_runtime_ready':False,'reason':'Source dynamics, wrapping and effective parameter assumptions have not been qualified in Chimera.'})
    model={'schema':'chimera.anatomical_assembly.v1','source_revision':receipt['revision'],'units':{'length':'m','angle':'rad','mass':'kg','inertia':'kg m^2'},'gravity_m_s2':vec(m,'gravity'),'bodies':bodies,'coordinates':coordinates,'muscles':muscles,'scope':'Macaque upper limb research geometry and modeled parameters; not full animal, raw scan certification, muscle volume, skin/fat geometry or living physics.','unknowns':['original specimen/mesh ancestry; source XML credits are placeholders','whole skeleton and tail','layer thickness and tissue surface geometry','force law implementation and physiological validation']}
    pose_frames(model) # Also validates hierarchy before admitting a proposal.
    return model,receipt

def pose_frames(model,values=None):
    values=values or {};require(set(values)<=set(model['coordinates']),'unknown_coordinate')
    q={n:float(values.get(n,c['default_rad'])) for n,c in model['coordinates'].items()}
    for n,v in q.items():
        c=model['coordinates'][n];require(np.isfinite(v) and c['range_rad'][0]-1e-9<=v<=c['range_rad'][1]+1e-9,'pose_out_of_range',n)
        require(not c['locked'] or v==c['default_rad'],'locked_coordinate',n)
    frames={'ground':np.eye(4)};bodies={b['name']:b for b in model['bodies']};pending=set(bodies)-{'ground'}
    while pending:
        progress=False
        for name in sorted(pending):
            b=bodies[name];j=b['joint'];require(j and j['parent'] in bodies,'missing_parent',name)
            if j['parent'] not in frames:continue
            motion=np.eye(4)
            for ax in j['axes']:
                f=ax['function'];a=f['coefficients'];v=a[0] if f['type']=='Constant' else a[0]*q[ax['coordinate']]+a[1]
                if ax['name'].startswith('rotation'):motion[:3,:3]=motion[:3,:3]@rotation(ax['axis'],v)
                else:motion[:3,3]+=np.asarray(ax['axis'])*v # translations expressed in parent joint frame
            frames[name]=frames[j['parent']]@frame(j['parent_location_m'],j['parent_orientation_rad'])@motion@np.linalg.inv(frame(j['child_location_m'],j['child_orientation_rad']))
            pending.remove(name);progress=True
        require(progress,'cyclic_body_hierarchy')
    return frames

def triangulate_polygon(ids,xyz):
    # Project onto the plane with greatest signed area, then ear-clip. Source
    # polygons may be concave; a fan is not a correct general triangulation.
    poly=list(ids)
    normal=np.sum(np.cross(xyz[poly],np.roll(xyz[poly],-1,axis=0)),axis=0)
    if np.linalg.norm(normal)==0:return []
    uv=np.delete(xyz,int(np.argmax(np.abs(normal))),axis=1)
    def cross(a,b,c):
        u=uv[b]-uv[a];v=uv[c]-uv[a];return u[0]*v[1]-u[1]*v[0]
    sign=1 if sum(uv[a,0]*uv[b,1]-uv[b,0]*uv[a,1] for a,b in zip(poly,np.roll(poly,-1)))>0 else -1
    eps=np.finfo(float).eps*max(1.,float(np.ptp(uv[poly],axis=0).max())**2)*32
    out=[]
    while len(poly)>3:
        found=False
        for i,b in enumerate(poly):
            a=poly[i-1];c=poly[(i+1)%len(poly)];turn=sign*cross(a,b,c)
            if abs(turn)<=eps:
                poly.pop(i);found=True;break
            if turn<0:continue
            if any(sign*cross(a,b,p)>=-eps and sign*cross(b,c,p)>=-eps and sign*cross(c,a,p)>=-eps for p in poly if p not in (a,b,c)):continue
            out.append((a,b,c));poly.pop(i);found=True;break
        require(found,'self_intersecting_or_untriangulable_polygon')
    if len(poly)==3 and abs(cross(*poly))>eps:out.append(tuple(poly))
    return out

def read_vtp(raw,report=None):
    root=ET.fromstring(raw);pieces=root.findall('./PolyData/Piece');require(len(pieces)==1,'unsupported_vtp_pieces');piece=pieces[0]
    require(all(int(piece.get(k,'0'))==0 for k in ('NumberOfVerts','NumberOfLines','NumberOfStrips')),'unsupported_vtp_primitives')
    def arr(node,ints=False):
        require(node is not None and node.get('format')=='ascii','unsupported_vtp_array')
        x=numbers(node.text);require(not ints or np.equal(x,np.floor(x)).all(),'nonintegral_index');return x.astype(np.int64) if ints else x
    source_xyz=arr(piece.find('./Points/DataArray')).reshape(-1,3);require(len(source_xyz)==int(piece.get('NumberOfPoints')),'vtp_vertex_count')
    # Exact-coordinate welding does not move any surface sample. Keep an explicit
    # map and repair report, and retain the original file unchanged.
    xyz,inverse=np.unique(source_xyz,axis=0,return_inverse=True)
    conn=arr(piece.find('./Polys/DataArray[@Name="connectivity"]'),True);ends=arr(piece.find('./Polys/DataArray[@Name="offsets"]'),True)
    require(len(ends)==int(piece.get('NumberOfPolys')) and len(ends)>0 and ends[-1]==len(conn) and np.diff(np.r_[0,ends]).min()>=3,'vtp_polygon_count')
    require(conn.min()>=0 and conn.max()<len(source_xyz),'vtp_index_range');tris=[];start=0;discarded=[]
    for i,end in enumerate(ends):
        mapped=inverse[conn[start:end]];start=end;poly=[]
        for v in mapped:
            if not poly or v!=poly[-1]:poly.append(int(v))
        if len(poly)>1 and poly[0]==poly[-1]:poly.pop()
        if len(set(poly))<3:discarded.append(i);continue
        require(len(set(poly))==len(poly),'self_touching_polygon')
        ts=triangulate_polygon(poly,xyz)
        if not ts:discarded.append(i)
        tris.extend(ts)
    require(tris,'empty_mesh_after_triangulation')
    if report is not None:report.update(source_vertices=len(source_xyz),exact_duplicate_vertices_welded=len(source_xyz)-len(xyz),source_vertex_to_render_vertex=inverse.tolist(),zero_area_polygons_omitted=discarded,triangulation='ear clipping projected source polygons; source sample coordinates unchanged; no holes filled')
    return xyz,np.asarray(tris,dtype=np.uint32)

def mesh_metrics(xyz,tris):
    edges=Counter(tuple(sorted((int(a),int(b)))) for t in tris for a,b in zip(t,np.roll(t,-1)))
    a,b,c=xyz[tris[:,0]],xyz[tris[:,1]],xyz[tris[:,2]]
    return {'vertices':len(xyz),'triangles':len(tris),'bounds_m':[xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],'surface_area_m2':float(np.linalg.norm(np.cross(b-a,c-a),axis=1).sum()/2),'signed_volume_m3':float(np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6),'edges_not_shared_twice':sum(v!=2 for v in edges.values()),'qualification':'Edge incidence and signed integral only; no self-intersection, material or anatomical validity claim.'}

def world_meshes(model,data=DATA,values=None):
    frames=pose_frames(model,values);result=[]
    for b in model['bodies']:
        for geom in b['geometry']:
            raw=local_file(data,geom['path']).read_bytes();require(sha(raw)==geom['sha256'],'geometry_pin_drift')
            repair={};xyz,tris=read_vtp(raw,repair);xyz*=geom['source_units_to_m'];T=frames[b['name']];world=xyz@T[:3,:3].T+T[:3,3]
            metrics=mesh_metrics(xyz,tris);metrics['processing']=repair
            result.append((b,geom,world,tris,metrics))
    return result

def build_proposal(graph,model,receipt,data=DATA):
    g=copy.deepcopy(graph);objects=[];relations=[]
    def relate(src,rel,dst,note):
        if not any(e['src']==src and e['rel']==rel and e['dst']==dst and e['note']==note for e in g.relations):
            g.relate(src,rel,dst,note);relations.append(dict(src=src,rel=rel,dst=dst,note=note))
    def add(oid,kind,name,physical,**extra):
        o={'id':oid,'kind':kind,'name':name,'status':'extracted','dependencies':[],'evidence':[],'physical':physical,**extra}
        if kind!='source':o['provenance']={'source_id':SOURCE,'source_revision':receipt['revision']}
        if oid in g.objects:require(g.get(oid)==o,'anatomy_proposal_conflict',oid)
        else:g.add(o);objects.append(o)
        if kind!='source':relate(oid,'derived_from',SOURCE,'Pinned macaque research-model intake')
        return o
    add(SOURCE,'source','Limblab macaque arm model, pinned MIT release',{'receipt':receipt,'license':'MIT','data_root':str(data.relative_to(ROOT)).replace('\\','/'),'limitation':model['scope'],'publication':'https://elifesciences.org/articles/48198'})
    add(MODEL,'model_definition','Macaque arm assembly in SI units',{'model':model})
    frames=pose_frames(model)
    for b in model['bodies']:
        add('ref.macaque_arm.body.'+b['name'],'model_definition',b['name']+' modeled segment',b,spatial={'frame':'macaque_arm_reference','units':'m','world_from_local':frames[b['name']].tolist()})
    for b,geom,xyz,tris,metrics in world_meshes(model,data):
        add('geom.macaque_arm.'+b['name'],'geometry_asset',b['name']+' source bone mesh',{'asset':geom,'metrics':metrics,'body':'ref.macaque_arm.body.'+b['name'],'anatomical_claim':'Published model geometry; original scan provenance unconfirmed.'})
    for m in model['muscles']:
        add('ref.macaque_arm.muscle.'+m['name'],'model_definition',m['name']+' source musculotendon',m)
    for b in model['bodies']:
        oid='ref.macaque_arm.body.'+b['name'];relate(MODEL,'contains',oid,'Source body-frame membership')
        if b['joint']:relate(oid,'attached_to','ref.macaque_arm.body.'+b['joint']['parent'],'Source joint; kinematic relationship, not qualified reaction forces')
        if b['geometry']:relate(oid,'contains','geom.macaque_arm.'+b['name'],'Source display geometry in this local body frame')
    for m in model['muscles']:
        oid='ref.macaque_arm.muscle.'+m['name'];relate(MODEL,'contains',oid,'Source musculotendon membership')
        for body in sorted(set(p['body'] for p in m['points'])):relate(oid,'attached_to','ref.macaque_arm.body.'+body,'Source path anchors; wrapping remains unresolved')
    g.layout=layout_roadmap(g);require(not g.check(),'anatomy_graph_invalid',g.check())
    return g,{'objects':objects,'relations':relations}

def compile_native(graph,output,data=DATA):
    """Compile admitted model semantics to rigid JNT3 bone bindings, in metres.

    The mesh is a reference assembly. It must not be sealed as water, and muscle
    path metadata is not executable force state. Dynamic anatomy is a later gate.
    """
    model=graph.get(MODEL)['physical']['model'];frames=pose_frames(model)
    joints=[{'name':'anatomy_mount','parent':-1,'pivot':[0.,0.,0.],'axis':[1.,0.,0.],'limits_deg':[0.,0.]}]
    owners={'ground':0};bodies={b['name']:b for b in model['bodies']};pending=set(bodies)-{'ground'}
    while pending:
        progress=False
        for name in sorted(pending):
            j=bodies[name]['joint']
            if j['parent'] not in owners:continue
            owner=owners[j['parent']];P=frames[j['parent']]@frame(j['parent_location_m'],j['parent_orientation_rad']);R=np.eye(3)
            for ax in j['axes']:
                f=ax['function'];a=f['coefficients'];value=a[0] if f['type']=='Constant' else a[0]*model['coordinates'][ax['coordinate']]['default_rad']+a[1]
                if ax['name'].startswith('translation'):
                    require(f['type']=='Constant' and value==0,'jnt3_translation_unsupported');continue
                if f['type']=='LinearFunction':
                    require(a==[1.,0.],'jnt3_coordinate_function_unsupported')
                    q=model['coordinates'][ax['coordinate']];limits=np.rad2deg(np.asarray(q['range_rad'])-q['default_rad']).tolist()
                    joints.append({'name':ax['coordinate'],'parent':owner,'pivot':P[:3,3].tolist(),'axis':(P[:3,:3]@R@ax['axis']).tolist(),'limits_deg':limits,'source_default_rad':q['default_rad']});owner=len(joints)-1
                R=R@rotation(ax['axis'],value)
            owners[name]=owner;pending.remove(name);progress=True
        require(progress,'cyclic_body_hierarchy')
    for i in range(len(joints)):
        n=0;j=i
        while j>=0:n+=1;j=joints[j]['parent']
        require(n<=8,'jnt3_chain_capacity')
    vertices=[];triangles=[];binding=[];parts=[];offset=0
    for b,geom,xyz,tris,metrics in world_meshes(model,data):
        record=graph.get('geom.macaque_arm.'+b['name'])['physical']
        require(record['asset']==geom and record['metrics']==metrics,'graph_geometry_drift')
        normals=np.zeros_like(xyz);a,bv,c=(xyz[tris[:,i]] for i in range(3));fn=np.cross(bv-a,c-a)
        for i in range(3):np.add.at(normals,tris[:,i],fn)
        ln=np.linalg.norm(normals,axis=1);normals[ln>0]/=ln[ln>0,None]
        color=np.tile([.82,.75,.60],(len(xyz),1));vertices.append(np.column_stack((xyz,normals,color)))
        triangles.append(tris+offset);binding.extend([owners[b['name']]]*len(xyz))
        parts.append({'body':b['name'],'vertex_start':offset,'vertex_count':len(xyz),'geometry_id':'geom.macaque_arm.'+b['name'],'metrics':metrics});offset+=len(xyz)
    v=np.concatenate(vertices).astype('<f4');t=np.concatenate(triangles).astype('<u4');nv=len(v);nj=len(joints)
    mesh=struct.pack('<IIffff',nv,t.size,.75,0.,.25,0.)+v.tobytes()+t.tobytes()
    names=b''.join(j['name'].encode()+b'\0' for j in joints)
    pack=struct.pack('<4sIII',b'JNT3',nv,nj,len(names))+names
    arrays=[(binding,'<i4'),(np.ones(nv),'<f4'),([j['pivot'] for j in joints],'<f4'),([j['axis'] for j in joints],'<f4'),([j['limits_deg'] for j in joints],'<f4'),([j['parent'] for j in joints],'<i4'),(np.full(nv,-1),'<i4'),(np.zeros(nv),'<f4')]
    for values,dtype in arrays:pack+=np.asarray(values,dtype=dtype).tobytes()
    output=Path(output);output.mkdir(parents=True,exist_ok=True);(output/'mesh.bin').write_bytes(mesh);(output/'body.bin').write_bytes(pack)
    scene={'schema':'chimera.anatomical_scene.v1','mode':'anatomy','graph_hash':graph.graph_hash(),'model_id':MODEL,'source_id':SOURCE,'title':'Macaque skeletal assembly','scope':model['scope'],'actuation':'kinematic reference','vertices':nv,'triangles':len(t),'bones':parts,'joints':joints,'camera':{'target':((v[:,:3].min(axis=0)+v[:,:3].max(axis=0))/2).tolist(),'radius':float(np.linalg.norm(np.ptp(v[:,:3],axis=0))*1.5)},'mesh_sha256':sha(mesh),'binding_sha256':sha(pack),'muscle_records':len(model['muscles']),'muscles_with_wrapping':sum(bool(m['wraps']) for m in model['muscles']),'water_sealing_allowed':False,'gaps':model['unknowns']}
    (output/'scene.json').write_bytes(canonical(scene));return scene

def load_native(output,engine):
    from urllib.parse import urlparse
    from .creature_scene import request
    url=urlparse(engine)
    require(url.scheme=='http' and url.hostname in ('127.0.0.1','localhost') and url.path in ('','/'),'private_loopback_engine_required')
    engine=engine.rstrip('/');output=Path(output)
    state=request(engine,'/tick_state')
    require(state.get('reflex_cell_count',0)==0 and state.get('body_model')!='JNT3_hierarchical','engine_not_empty')
    scene=json.loads((output/'scene.json').read_text())
    require(scene['schema']=='chimera.anatomical_scene.v1' and scene['water_sealing_allowed'] is False,'anatomy_scene_required')
    mesh=(output/'mesh.bin').read_bytes();body=(output/'body.bin').read_bytes()
    require(sha(mesh)==scene['mesh_sha256'] and sha(body)==scene['binding_sha256'],'compiled_payload_drift')
    request(engine,'/mesh_bin',mesh,True);request(engine,'/tick_body_bin',body,True)
    state=request(engine,'/tick_state');require(state.get('body_model')=='JNT3_hierarchical','body_admission_failed')
    (output/'loaded.json').write_bytes(canonical({'engine':engine,'scene':scene,'state':state}))
    return {'engine':engine,'vertices':scene['vertices'],'body_model':state['body_model'],'scope':scene['scope']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'.tmp/macaque-anatomy');ap.add_argument('--engine');args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    g=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'));require('work.creature.macaque_intake' in g.objects,'work_not_admitted')
    model,receipt=parse_source();proposal,fragment=build_proposal(g,model,receipt);proposal.save(str(args.output/'graph.json'))
    (args.output/'proposal.json').write_bytes(canonical(fragment));(args.output/'assembly.json').write_bytes(canonical(model));compile_native(proposal,args.output)
    if args.engine:load_native(args.output,args.engine)
    print(json.dumps({'bodies':len(model['bodies']),'bone_meshes':len(world_meshes(model)),'coordinates':len(model['coordinates']),'muscles':len(model['muscles']),'graph_hash':proposal.graph_hash(),'output':str(args.output)}))
if __name__=='__main__':main()
