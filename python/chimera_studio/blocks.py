# SPDX-License-Identifier: AGPL-3.0-or-later
"""Authoring adapter for existing apex-weld films. No physical solve here."""
import copy
import hashlib
import json
import numpy as np
from . import gpu_native as g


def starter():
    folder=g.ROOT/'vendor/membrane_blocks'
    lock=json.loads((folder/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
    raw=(folder/'star-transaction.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=lock['transaction_sha256']:
        raise ValueError('Pinned membrane starter changed')
    txn=json.loads(raw); comp=txn['compiled']; seam=txn['ids']['seam_vertex']
    positions=np.frombuffer(bytes.fromhex(comp['positions_f64']),dtype='<f8').reshape(-1,3)
    faces=np.asarray(comp['faces'])
    parts=[]
    for region in txn['ids']['regions']:
        ids=region['vertex_block']; local={v:i for i,v in enumerate(ids)}
        parts.append({'id':region['region_id'],'name':'Film '+region['region_id'],
                      'positions':positions[ids].tolist(),
                      'triangles':[[local[int(v)] for v in face] for face in faces[region['face_block']]],
                      'centre':local[seam],'gamma':1.0})
    return parts,[['A','B'],['A','C']]


def compile_parts(parts,connections):
    if not isinstance(parts,list) or not 2<=len(parts)<=6:
        raise ValueError('Connect 2–6 membrane films')
    ids=[p.get('id') for p in parts]
    if any(not isinstance(i,str) or not i or len(i)>80 for i in ids) or len(set(ids))!=len(ids):
        raise ValueError('Missing or duplicate block identity; assign a new identity to duplicated objects')
    parts=sorted(copy.deepcopy(parts),key=lambda p:p['id']); ids=[p['id'] for p in parts]
    adj={i:set() for i in ids}; edges=[]
    if not isinstance(connections,list):raise ValueError('Missing attachment list')
    for e in connections:
        if not isinstance(e,list) or len(e)!=2 or any(i not in adj for i in e) or e[0]==e[1]:
            raise ValueError('Attachment refers to a missing or identical block')
        edge=sorted(e)
        if edge in edges:raise ValueError('Duplicate attachment')
        edges.append(edge);adj[e[0]].add(e[1]);adj[e[1]].add(e[0])
    seen=set();todo=[ids[0]]
    while todo:
        i=todo.pop()
        if i not in seen:seen.add(i);todo.extend(adj[i]-seen)
    if len(seen)!=len(ids):raise ValueError('Every film needs an explicit apex connection')
    if len(edges)!=len(parts)-1:raise ValueError('Use one attachment tree; redundant apex connections are unnecessary')
    checked=[]
    for p in parts:
        if not isinstance(p.get('name'),str) or len(p['name'])>128:raise ValueError('Invalid block name')
        checked.append(g.membrane_spec(p['positions'],p['triangles'],p['centre'],p['gamma']))
    if len({s['gamma'] for s in checked})!=1:
        raise ValueError('Current native membrane owner supports one uniform surface tension per joined assembly; assign the same value to all films')
    seam=np.array(checked[0]['positions'][checked[0]['centre']])
    positions=[seam.tolist()];triangles=[];regions=[]
    for p,s in zip(parts,checked):
        if np.linalg.norm(np.array(s['positions'][s['centre']])-seam)>1e-7:
            raise ValueError('Apex attachment points must coincide within 0.1 micrometer; align them explicitly')
        remap={s['centre']:0}
        for i,v in enumerate(s['positions']):
            if i!=s['centre']:remap[i]=len(positions);positions.append(v)
        first=len(triangles)
        triangles.extend([[remap[i] for i in face] for face in s['triangles']])
        regions.append({'id':p['id'],'name':p['name'],'vertices':[remap[i] for i in range(len(s['positions']))],
                        'faces':list(range(first,len(triangles)))})
    g.geometry(positions,triangles)
    return {'mode':'membrane','positions':positions,'triangles':triangles,'centre':0,
            'gamma':checked[0]['gamma'],
            'assembly':{'schema':'chimera.studio.apex-assembly.v1','parts':parts,'connections':sorted(edges),
                        'regions':regions,'constraints':'One shared world-Z rail apex; every rim vertex fixed',
                        'law':'constant-gamma-current-area + apex-weld'}}


def validate(spec):
    a=spec['assembly']
    if not isinstance(a,dict) or a.get('schema')!='chimera.studio.apex-assembly.v1':raise ValueError('Unknown membrane assembly')
    expected=compile_parts(a['parts'],a['connections'])
    if spec!=expected:raise ValueError('Assembly geometry, material or attachment metadata changed inconsistently')
    return expected
