# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed convex import adapter; uses the project's original volume compiler.
No bounding-box substitute. Material response in this first bridge is rigid
mass/inertia/contact, not an invented elastic law for a named material.
"""
from collections import Counter
import importlib.util
import math
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
name='_chimera_pinned_material_volume'
if name not in sys.modules:
    spec=importlib.util.spec_from_file_location(name,ROOT/'vendor/chimera/material_volume.py')
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
compiler=sys.modules[name]
class GeometryError(ValueError): pass

def compile_convex(part_id, vertices, triangles, density, friction, source='Authored game profile'):
    p=np.asarray(vertices,dtype=float);t=np.asarray(triangles,dtype=int)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all(): raise GeometryError('Non-finite or malformed vertices')
    if t.ndim!=2 or t.shape[1]!=3 or len(t)<4 or len(t)>128: raise GeometryError('First bridge accepts 4..128 triangles per convex part')
    if t.min()<0 or t.max()>=len(p): raise GeometryError('Triangle index outside mesh')
    if not math.isfinite(density) or density<=0 or not math.isfinite(friction) or not 0<=friction<=2: raise GeometryError('Invalid density or friction')
    edges=Counter(tuple(sorted((int(a),int(b)))) for f in t for a,b in zip(f,np.roll(f,-1)))
    if any(n!=2 for n in edges.values()): raise GeometryError('Closed manifold surface required')
    center=p.mean(axis=0);scale=float(np.linalg.norm(np.ptp(p,axis=0)))
    if scale<=1e-9: raise GeometryError('Part has no measurable extent')
    signed=np.array([np.dot(np.cross(p[b]-p[a],p[c]-p[a]),p[a]-center) for a,b,c in t])
    if np.all(signed<0): t=t[:,[0,2,1]]
    elif not np.all(signed>0): raise GeometryError('Concave or inconsistently wound mesh; split into convex regions')
    for a,b,c in t:
        n=np.cross(p[b]-p[a],p[c]-p[a]);length=np.linalg.norm(n)
        if length<scale*scale*1e-12: raise GeometryError('Degenerate face')
        if np.max((p-p[a])@(n/length))>scale*1e-8: raise GeometryError('Concave region: preserve it for later decomposition')
    cells=[[len(p),*map(int,face)] for face in t]
    material=compiler.MaterialSpec('authored',float(density),source,'Rigid mass/contact demonstration; no strength or failure claim')
    region=compiler.RegionSpec('region',part_id,'authored')
    cp=compiler.compile_partition(np.vstack((p,center)),cells,[material],[region],[['region'] for _ in cells])
    mp=cp.mass_properties
    if not cp.complete or cp.connected_components!=1 or mp is None: raise GeometryError('Incomplete or disconnected material volume')
    # Existing B2 ground derivation: 1 cm nominal rest sink and damping ratio .7.
    nbase=int(np.sum(np.abs(p[:,1]-p[:,1].min())<max(scale*1e-8,1e-9)))
    k=mp.mass_kg*9.81/.01/nbase;c=2*.7*math.sqrt(mp.mass_kg*mp.mass_kg*9.81/.01)/nbase
    part={'id':part_id,'mass_kg':mp.mass_kg,'com_local_m':list(mp.center_of_mass_m),
          'inertia_com_local_kg_m2':[v for row in mp.inertia_com_kg_m2 for v in row],
          'vertices_local_m':p.reshape(-1).tolist(),'boundary_triangles':t.reshape(-1).tolist(),
          'pose_c_m':list(mp.center_of_mass_m),'pose_q_wxyz':[1.,0.,0.,0.],
          'ground':{'k_n_per_m':k,'c_n_s_per_m':c},'mu':float(friction)}
    return part,cp.to_dict()


def attachment_between(a_id,a_points,b_id,b_points,stiffness=5000.,damping=30.):
    """Author three non-collinear anchor pairs on opposed, overlapping convex faces."""
    a=np.asarray(a_points,dtype=float);b=np.asarray(b_points,dtype=float)
    if len(a)<3 or len(b)<3 or not np.isfinite(a).all() or not np.isfinite(b).all():raise GeometryError('Invalid mount faces')
    def normal(v):
        n=np.cross(v[1]-v[0],v[2]-v[0]);l=np.linalg.norm(n)
        if l<1e-12:raise GeometryError('Mount face has no area')
        return n/l
    na,nb=normal(a),normal(b)
    if np.dot(na,nb)>-.999:raise GeometryError('Mount faces must face each other')
    if max(abs((a-b[0])@nb))>1e-5 or max(abs((b-a[0])@na))>1e-5:raise GeometryError('Align mount faces to within 10 micrometers before joining')
    if np.linalg.norm(np.cross(a[1]-a[0],a[2]-a[0]))>np.linalg.norm(np.cross(b[1]-b[0],b[2]-b[0])):
        x,y,nx,ny,reverse=b,a,nb,na,True
    else:x,y,nx,ny,reverse=a,b,na,nb,False
    center=x.mean(axis=0);anchors=[]
    for point in (center+.6*(x[:3]-center)):
        projected=point-np.dot(point-y[0],ny)*ny
        for u,v in zip(y,np.roll(y,-1,axis=0)):
            if np.dot(np.cross(v-u,projected-u),ny)<-1e-10:raise GeometryError('Mounts do not share enough usable area')
        first,second=(projected,point) if reverse else (point,projected)
        anchors.append([*map(float,first),*map(float,second)])
    return {'a':a_id,'b':b_id,'k':float(stiffness),'c_damp':float(damping),'anchors_world':anchors}
