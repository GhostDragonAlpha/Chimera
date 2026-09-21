"""OpenSim 4.x intake (Wiseman 2026 primate hindlimb models) -> anatomy store format.

This is the 4.x counterpart of macaque_anatomy.parse_source(). SHAPE DECISION
(justified): a PARALLEL parser, not a version-dispatch edit of macaque_anatomy.py.
parse_source() has the 3.x dialect welded into every require() line (Version=='30000',
Schutte1993Muscle_Deprecated, PathPoint <body>, Coordinate motion_type, VisibleObject/
DisplayGeometry, Weld/Custom joints only) and is byte-pinned by the validation receipt
osim4_adapter_20260920 (falsifier D: the file may not drift by one byte). Editing a
version gate into it risks the pinned behavior to save one import; a parallel module
risks nothing and converges on the SAME store target through SHARED code: the numeric,
frame and record helpers and the pose_frames hierarchy validator are imported from
macaque_anatomy, and the emitted model dict is the same chimera.anatomical_assembly.v1
shape the 3.x lane already feeds to build_proposal/compile_native. The version-
dispatching front end (parse_anatomy) lives HERE, additively.

4.x idioms translated, with zero record loss (falsifier A):
  PathPoint <socket_parent_frame>/bodyset/X   -> point['body'] (3.x <body> equivalent)
  Joint socket_parent_frame/socket_child_frame -> PhysicalOffsetFrame translation/
      orientation pairs become the 3.x joint record's parent_*/child_* fields, so the
      UNMODIFIED 3.x pose_frames() validates the converted hierarchy.
  PinJoint                                     -> implicit revolute about the joint
      frame +X axis (OpenSim 4.x semantics): synthesized rotation1 LinearFunction axis.
  Ground (massless, separate element)          -> synthesized, explicitly marked ground
      body record; the 3.x store format requires a ground body and the 4.x file has none.
  Millard2012EquilibriumMuscle                 -> muscle record; PLACEHOLDER forces
      (1 N / 1 m / 1 / 0) are kept as source text AND numeric data; every muscle is
      emitted force_runtime_ready=False. Name-level pairing onto the admitted Guimaraes
      batch is recorded per muscle (validation/osim4_adapter_20260920/
      guimaraes_name_pairing.json) but NO force number travels: that batch is not on
      this lineage (46ed85a3 is not an ancestor of aede5de9, measured before build).

No taxon conditionals exist in this file: all 7 deposited models parse through the same
code and each must reconcile against its own acquisition inventory record (falsifier E).
"""
import json, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from .common import Refusal, canonical, require, sha, local_file
from .macaque_anatomy import numbers, vec, frame, xml_record, pose_frames

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'tools/science_funnel/data/wiseman2026'
TAXA=('Bonobo','Chimpanzee','Gibbon','Gorilla','Macaque','Orangutan','Siamang')
SUPPORTED_VERSION='40600' # measured: all 7 deposited documents; anything else refuses
MANIFEST=json.loads((DATA/'sha256_manifest.json').read_text(encoding='utf-8'))
ACQUISITION=json.loads((DATA/'download_receipt.json').read_text(encoding='utf-8'))
INVENTORY=json.loads((DATA/'inventory.json').read_text(encoding='utf-8'))
PAIRING=json.loads((ROOT/'tools/science_funnel/validation/osim4_adapter_20260920/guimaraes_name_pairing.json').read_text(encoding='utf-8'))
SOURCE='source.anatomy.wiseman2026'
REASON='Source dynamics are placeholder forces (1 N / 1 m / 1 / 0) and the admitted Guimaraes numbers are not on this lineage; wrapping is unresolved geometry data. Paths are Wiseman 2026; force pairing is recorded by name only.'

def model_path(taxon):
    require(taxon in TAXA,'unknown_taxon',taxon)
    return f'models/{taxon}_model.osim'

def pinned_bytes(rel):
    raw=local_file(DATA,rel).read_bytes()
    entry=next((f for f in MANIFEST['files'] if f['path']==rel),None)
    require(entry is not None,'unpinned_file',rel)
    require(sha(raw)==entry['sha256'] and len(raw)==entry['bytes'],'source_pin_drift',rel)
    return raw

def resolve_body_socket(socket,bodies):
    require(isinstance(socket,str) and socket.startswith('/'),'malformed_socket',socket)
    name=socket.rstrip('/').rsplit('/',1)[-1]
    require(name in bodies,'socket_target_missing',socket)
    return name

def offset_frame(joint_node,name,bodies):
    f=joint_node.find(f"./frames/PhysicalOffsetFrame[@name='{name}']")
    require(f is not None,'offset_frame_missing',name)
    require(f.findtext('socket_parent') is not None,'offset_frame_orphan',name)
    return {'body':resolve_body_socket(f.findtext('socket_parent'),bodies),'location_m':vec(f,'translation'),'orientation_rad':vec(f,'orientation')}

def transform_axes(joint_node,coordinates):
    axes=[]
    st=joint_node.find('SpatialTransform');require(st is not None,'spatial_transform_missing')
    found=[x.get('name') for x in st.findall('TransformAxis')]
    require(found==['rotation1','rotation2','rotation3','translation1','translation2','translation3'],'transform_axis_order',str(found))
    for ax in st.findall('TransformAxis'):
        coord=(ax.findtext('coordinates') or '').strip()
        axis=vec(ax,'axis');require(abs(np.linalg.norm(axis)-1)<1e-6,'axis_not_unit')
        f=[c for c in ax if c.tag in ('function','LinearFunction','Constant')] # 4.x inlines <LinearFunction name="function">; 3.x wrapped it in <function>
        require(len(f)<=1,'multiple_transform_functions')
        if f:
            f=f[0];require(f.tag=='LinearFunction','unsupported_transform_function',f.tag)
            fun={'type':'LinearFunction','coefficients':vec(f,'coefficients',count=2)}
            require(bool(coord) and coord in coordinates,'function_coordinate',coord)
        else:
            require(not coord,'unoriented_transform_axis',ax.get('name')) # 4.x leaves driven axes function-less; a bare coordinate with no function is not decodable
            fun={'type':'Constant','coefficients':[0.]}
        require(np.isfinite(fun['coefficients']).all(),'nonfinite_function')
        axes.append({'name':ax.get('name'),'axis':axis,'coordinate':coord,'function':fun})
    return axes

def pin_joint_axes(joint_node,coordinates):
    names=[c.get('name') for c in joint_node.findall('./coordinates/Coordinate')]
    require(len(names)==1,'pin_joint_coordinate_count',str(names))
    return [{'name':'rotation1','axis':[1.,0.,0.],'coordinate':names[0],'function':{'type':'LinearFunction','coefficients':[1.,0.]}}] # OpenSim 4.x PinJoint: revolute about the joint frame +X

def parse_muscles(model_node,body_names):
    out=[]
    for msc in model_node.findall('./ForceSet/objects/*'):
        require(msc.tag=='Millard2012EquilibriumMuscle','unsupported_muscle_record',msc.tag)
        name=msc.get('name');points=[]
        for i,p in enumerate(msc.findall('./GeometryPath/PathPointSet/objects/*')):
            require(p.tag=='PathPoint','unsupported_path_point',p.tag)
            points.append({'ordinal':i,'name':p.get('name'),'type':p.tag,'body':resolve_body_socket(p.findtext('socket_parent_frame'),body_names),'location_m':vec(p,'location')})
        wraps=[xml_record(x) for x in msc.findall('./GeometryPath/PathWrapSet/objects/*')]
        params={};curves=[]
        for x in msc: # same split the 3.x parser uses: childless elements are scalar parameters, elements with children are curve records
            if x.tag=='GeometryPath':continue
            if len(x):curves.append(xml_record(x))
            else:params[x.tag]=(x.text or '').strip()
        placeholder={k:float(params[k]) for k in ('max_isometric_force','optimal_fiber_length','tendon_slack_length','pennation_angle_at_optimal')}
        require(np.isfinite(list(placeholder.values())).all(),'nonfinite_muscle_parameter',name)
        all_placeholder=(placeholder=={'max_isometric_force':1.,'optimal_fiber_length':1.,'tendon_slack_length':1.,'pennation_angle_at_optimal':0.})
        out.append({'name':name,'source_model':msc.tag,'points':points,'wraps':wraps,'parameters_source_text':params,'curves':curves,'force_placeholder':placeholder,'force_all_source_placeholder':all_placeholder,'force_pairing':pair_name(name),'force_runtime_ready':False,'reason':REASON})
    return out

def pair_name(wiseman_name):
    """Name-level pairing onto the admitted Guimaraes names. Numbers never travel here."""
    table=PAIRING;core=wiseman_name[2:] if wiseman_name.startswith('R_') else wiseman_name
    norm=table['aliases'].get(core.upper(),core.upper())
    names={n.upper():n for n in table['guimaraes_names_36']}
    if norm in names:return {'guimaraes_name':names[norm],'status':'name_exact','numbers':None,'note':'name match only; force numbers deferred until the admitted batch is on this lineage'}
    marker=table['split_marker']
    if marker in core:
        stem=table['aliases'].get(core.split(marker)[0].upper(),core.split(marker)[0].upper())
        if stem in names:return {'guimaraes_name':names[stem],'status':'split_homolog_deferred','numbers':None,'note':'digit-tendon slip of a single Guimaraes record; per-slip force division is an unstated law - mapping deferred'}
    return {'guimaraes_name':None,'status':'unmatched','numbers':None,'note':'no name-level homolog in the Guimaraes 36'}

def parse_wiseman(taxon):
    """Parse one deposited 4.6 model into the chimera.anatomical_assembly.v1 store format."""
    rel=model_path(taxon);raw=pinned_bytes(rel)
    doc=ET.fromstring(raw);require(doc.get('Version')==SUPPORTED_VERSION,'unsupported_opensim_version',doc.get('Version'))
    m=doc.find('Model');require(m is not None,'model_element_missing')
    bodies=[];coordinates={};body_names=set()
    for b in m.findall('./BodySet/objects/Body'):
        name=b.get('name');require(name not in body_names,'duplicate_body');body_names.add(name)
        inertia=vec(b,'inertia',count=6) # 4.x stores one inertia element: xx yy zz xy xz yz (the 3.x attribute set, flattened)
        require(np.isfinite(inertia).all(),'nonfinite_inertia',name)
        rec={'name':name,'mass_kg':float(b.findtext('mass')),'mass_center_m':vec(b,'mass_center'),'inertia_kg_m2':inertia,'mass_scope':'deposited segment mass (OpenSim 4.6 model; adult-scale per source mesh probe), not isolated visible bone','geometry':[],'geometry_source_names':[g.findtext('mesh_file') for g in b.findall('./attached_geometry/Mesh')],'wrap_objects':[xml_record(x) for x in b.findall('./WrapObjectSet/objects/*')]}
        require(np.isfinite(rec['mass_kg']) and rec['mass_kg']>=0,'invalid_mass',name)
        require(all(n is not None for n in rec['geometry_source_names']),'mesh_file_missing',name)
        bodies.append(rec)
    require('ground' not in body_names,'deposited_ground_body')
    body_names.add('ground') # joint parent sockets resolve against /ground; path sockets may too
    bodies.append({'name':'ground','mass_kg':0.,'mass_center_m':[0.,0.,0.],'inertia_kg_m2':[0.]*6,'mass_scope':'synthesized: the OpenSim 4.x Ground element is massless and separate; the 3.x store format requires a ground body record','geometry':[],'geometry_source_names':[],'wrap_objects':[],'origin':'synthesized_ground'})
    joint_by_child={};normalizations=[]
    for j in m.findall('./JointSet/objects/*'):
        require(j.tag in ('CustomJoint','PinJoint'),'unsupported_joint',j.tag)
        parent=offset_frame(j,j.findtext('socket_parent_frame'),body_names)
        child=offset_frame(j,j.findtext('socket_child_frame'),body_names)
        require(child['body'] not in joint_by_child,'multiple_body_joints',child['body'])
        coords={}
        for q in j.findall('./coordinates/Coordinate'):
            qn=q.get('name');require(qn not in coordinates,'duplicate_coordinate',qn)
            qr={'default_rad':float(q.findtext('default_value')),'range_rad':(vec(q,'range',count=2) if q.findtext('range') is not None else []),'locked':(q.findtext('locked','false')=='true'),'clamped':(q.findtext('clamped','false')=='true'),'range_source':'deposited'}
            if q.findtext('range') is None:
                # OpenSim 4.x Coordinate class default when the document deposits no range:
                # [-10*pi, +10*pi] rad. The deposited model RUNS with this in OpenSim, so the
                # parser records it, marked - it does not invent a number.
                qr['range_rad']=[-10*np.pi,10*np.pi];qr['range_source']='opensim4_class_default_-10pi_10pi'
            require(np.isfinite([qr['default_rad']]+qr['range_rad']).all(),'nonfinite_coordinate',qn)
            if not qr['range_rad'][0]<=qr['default_rad']<=qr['range_rad'][1]:
                # Deposited posing noise: right-limb defaults carry e.g. 1.7e-34 rad above a
                # [-1.6, 0] range. A violation below 1e-9 rad (6e-8 degrees, under any encoder's
                # noise floor) is clamped INTO range with the deposited value kept beside it.
                # Anything larger refuses: no silent edit of source data.
                violation=max(qr['range_rad'][0]-qr['default_rad'],qr['default_rad']-qr['range_rad'][1])
                require(violation<=1e-9,'coordinate_range',f'{qn} by {violation}')
                normalizations.append({'coordinate':qn,'deposited_default_rad':qr['default_rad'],'clamped_to_rad':min(max(qr['default_rad'],qr['range_rad'][0]),qr['range_rad'][1]),'violation_rad':violation})
                qr['default_rad_deposited']=qr['default_rad'];qr['default_rad']=normalizations[-1]['clamped_to_rad']
            coords[qn]=qr;coordinates[qn]=qr
        axes=transform_axes(j,coords) if j.tag=='CustomJoint' else pin_joint_axes(j,coords)
        joint_by_child[child['body']]={'name':j.get('name'),'type':j.tag,'parent':parent['body'],'parent_location_m':parent['location_m'],'parent_orientation_rad':parent['orientation_rad'],'child_location_m':child['location_m'],'child_orientation_rad':child['orientation_rad'],'axes':axes,'parent_offset_frame':j.findtext('socket_parent_frame'),'child_offset_frame':j.findtext('socket_child_frame')}
    for b in bodies:
        if b['name']=='ground':b['joint']=None;continue
        require(b['name'] in joint_by_child,'unconnected_body',b['name']);b['joint']=joint_by_child[b['name']]
    muscles=parse_muscles(m,body_names)
    require(muscles and all(mm['name'] for mm in muscles),'empty_muscle_set')
    default_ranges=sorted(qn for qn,qr in coordinates.items() if qr['range_source']!='deposited')
    inv=INVENTORY['models'][taxon]
    scope=f'Wiseman et al. 2026 RSOS deposited {taxon} hindlimb research geometry, OpenSim 4.6, adult-scale per source; right-limb muscles only; not full animal, raw scan certification, muscle volume, skin/fat geometry or living physics.'
    model={'schema':'chimera.anatomical_assembly.v1','opensim_document_version':SUPPORTED_VERSION,'taxon':taxon,'source_revision':next(f['sha256'] for f in MANIFEST['files'] if f['path']==rel),'units':{'length':'m','angle':'rad','mass':'kg','inertia':'kg m^2'},'gravity_m_s2':vec(m,'gravity'),'bodies':bodies,'coordinates':coordinates,'muscles':muscles,'coordinate_normalizations':normalizations,'scope':scope,'unknowns':['muscle forces are source placeholders (1 N / 1 m / 1 / 0); admitted Guimaraes numbers are NOT on this lineage (46ed85a3 is not an ancestor of aede5de9) - pairing recorded by name only','display meshes (.obj) are pinned in the gitignored Zenodo deposit (Primate_models.zip sha256 6cb8e29ad6d7664beb19ed8f5f6aadeef0153f49dd0aea052135c846768f6181), not admitted as bytes on this lineage','specimen stage is adult per publication and mesh-scale probe; per-specimen numeric age not stated','wrapping is unresolved geometry data; no contact law is qualified','left hindlimb carries no muscles (deposited muscles are right-limb R_ records)','SI2 moment-arm table states no units at source (inventory note)','coordinates depositing no <range> element take the OpenSim 4.x class default [-10pi, 10pi] rad, recorded per coordinate via range_source'+(f': {default_ranges}' if default_ranges else '')]}
    pose_frames(model) # the UNMODIFIED 3.x hierarchy validator runs on the converted model
    return model

def reconcile(model):
    """Falsifier A accounting: parsed records vs the acquisition inventory, no silent drops."""
    inv=INVENTORY['models'][model['taxon']]
    file_bodies=[b for b in model['bodies'] if b.get('origin')!='synthesized_ground']
    parsed={'body_count':len(file_bodies),'joint_count':sum(1 for b in model['bodies'] if b['joint']),'muscle_count':len(model['muscles']),'path_points':sum(len(mm['points']) for mm in model['muscles']),'wrap_surfaces':sum(len(b['wrap_objects']) for b in model['bodies']),'coordinate_count':len(model['coordinates'])}
    expected={'body_count':inv['body_count'],'joint_count':len(inv['joints']),'muscle_count':inv['muscle_count'],'path_points':inv['total_path_points'],'wrap_surfaces':len(inv['wrap_surfaces']),'coordinate_count':inv['coordinate_count']}
    require(parsed==expected,'inventory_reconciliation',f'{parsed} != {expected}')
    by_name={mm['name']:mm for mm in model['muscles']}
    require(set(by_name)==set(x['name'] for x in inv['muscles']),'muscle_set_mismatch')
    for entry in inv['muscles']:
        mm=by_name[entry['name']];points=mm['points']
        require(len(points)==entry['path_points'],'path_point_count',entry['name'])
        require(sorted(set(p['body'] for p in points))==sorted(entry['path_point_bodies']),'path_point_bodies',entry['name']) # inventory records the unique attachment set, not the point order
        wrap_names=[]
        for w in mm['wraps']:
            target=[c['text'] for c in w['children'] if c['tag']=='wrap_object']
            require(len(target)==1,'wrap_socket_count',entry['name']);wrap_names.append(target[0].rsplit('/',1)[-1])
        require(sorted(wrap_names)==sorted(entry['wraps']),'muscle_wrap_set',entry['name'])
    body_wrap_names=sorted(w['attributes'].get('name') for b in model['bodies'] for w in b['wrap_objects'])
    require(body_wrap_names==sorted(x['name'] for x in inv['wrap_surfaces']),'body_wrap_set')
    require(sorted(b['name'] for b in file_bodies)==sorted(inv['bodies']),'body_set_mismatch')
    return {'parsed':parsed,'expected':expected,'ground_bodies_synthesized':1,'match':'exact'}

def build_proposal(graph,model,manifest_entry=None):
    """Same proposal contract as the 3.x lane, without pretending an admission gate ran."""
    import copy
    from tools.creature_graph.views import layout_roadmap
    taxon=model['taxon'];prefix=f'ref.wiseman.{taxon.lower()}';rel=model_path(taxon)
    g=copy.deepcopy(graph);objects=[];relations=[]
    def relate(src,rel_,dst,note):
        if not any(e['src']==src and e['rel']==rel_ and e['dst']==dst and e['note']==note for e in g.relations):
            g.relate(src,rel_,dst,note);relations.append(dict(src=src,rel=rel_,dst=dst,note=note))
    def add(oid,kind,name,physical,**extra):
        o={'id':oid,'kind':kind,'name':name,'status':'extracted','dependencies':[],'evidence':[],'physical':physical,**extra}
        if kind!='source':o['provenance']={'source_id':SOURCE,'source_revision':model['source_revision']}
        if oid in g.objects:require(g.get(oid)==o,'wiseman_proposal_conflict',oid)
        else:g.add(o);objects.append(o)
        if kind!='source':relate(oid,'derived_from',SOURCE,f'Deposited {taxon} OpenSim 4.6 model intake')
        return o
    entry=manifest_entry or next(f for f in MANIFEST['files'] if f['path']==rel)
    add(SOURCE,'source','Wiseman 2026 RSOS primate hindlimb OpenSim models, pinned CC BY 4.0 deposit',{'receipt':{'deposit':INVENTORY['deposit'],'license':ACQUISITION['license'],'zenodo_zip_sha256':entry['sha256'],'zenodo_zip_bytes':entry['bytes']},'data_root':'tools/science_funnel/data/wiseman2026','limitation':model['scope'],'publication':'DOI 10.1098/rsos.260107'})
    MODEL=f'model.anatomy.wiseman_{taxon.lower()}'
    add(MODEL,'model_definition',f'{taxon} hindlimb assembly in SI units',{'model':model})
    frames=pose_frames(model)
    for b in model['bodies']:
        add(f'{prefix}.body.'+b['name'],'model_definition',b['name']+' modeled segment',b,spatial={'frame':f'wiseman_{taxon.lower()}_reference','units':'m','world_from_local':frames[b['name']].tolist()})
    for mm in model['muscles']:
        add(f'{prefix}.muscle.'+mm['name'],'model_definition',mm['name']+' source musculotendon',mm)
    for b in model['bodies']:
        oid=f'{prefix}.body.'+b['name'];relate(MODEL,'contains',oid,'Source body-frame membership')
        if b['joint']:relate(oid,'attached_to',f'{prefix}.body.'+b['joint']['parent'],'Source joint; kinematic relationship, not qualified reaction forces')
    for mm in model['muscles']:
        oid=f'{prefix}.muscle.'+mm['name'];relate(MODEL,'contains',oid,'Source musculotendon membership')
        for body in sorted(set(p['body'] for p in mm['points'])):relate(oid,'attached_to',f'{prefix}.body.'+body,'Source path anchors; wrapping remains unresolved')
    g.layout=layout_roadmap(g);require(not g.check(),'wiseman_graph_invalid',g.check())
    return g,{'objects':objects,'relations':relations}

def parse_anatomy(data,taxon=None):
    """Version-dispatching front end. The 3.x lane keeps calling its own parse_source();
    new callers route here. Deposited 4.x documents parse through parse_wiseman();
    anything else refuses rather than guessing."""
    if (Path(data)/'models').is_dir():
        require(taxon is not None,'taxon_required')
        version=ET.fromstring(pinned_bytes(model_path(taxon))).get('Version')
        require(version==SUPPORTED_VERSION,'unsupported_opensim_version',version)
        return parse_wiseman(taxon)
    raise Refusal('unsupported_anatomy_layout',str(data))

def pairing_report(taxon):
    model=parse_wiseman(taxon)
    table={'taxon':taxon,'exact':[{'wiseman':mm['name'],'guimaraes':mm['force_pairing']['guimaraes_name']} for mm in model['muscles'] if mm['force_pairing']['status']=='name_exact'],'split_homolog_deferred':[{'wiseman':mm['name'],'guimaraes':mm['force_pairing']['guimaraes_name']} for mm in model['muscles'] if mm['force_pairing']['status']=='split_homolog_deferred'],'unmatched':[mm['name'] for mm in model['muscles'] if mm['force_pairing']['status']=='unmatched']}
    matched={p['guimaraes'] for p in table['exact']}|{p['guimaraes'] for p in table['split_homolog_deferred']}
    table['guimaraes_without_wiseman_record']=[n for n in PAIRING['guimaraes_names_36'] if n not in matched]
    table['counts']={'wiseman_muscles':len(model['muscles']),'exact':len(table['exact']),'split_homolog_deferred':len(table['split_homolog_deferred']),'unmatched':len(table['unmatched']),'guimaraes_without_wiseman_record':len(table['guimaraes_without_wiseman_record']),'guimaraes_total':len(PAIRING['guimaraes_names_36']),'force_runtime_ready':0}
    return table
