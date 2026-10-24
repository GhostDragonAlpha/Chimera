# SPDX-License-Identifier: AGPL-3.0-or-later
"""Author the asymmetric rescue cradle / haul load path (plan 13.0 R2, catalog I05-I09)
through the installed libuipc operators, as an OWNED copy under Studio evidence.

Never overwrites an existing user project or an existing owned output. Run in a
fresh, isolated Blender after Libuipc/tools/activate.py:

  blender.exe --factory-startup --app-template ChimeraStudio --background \
      --python Libuipc/tools/activate.py --python integration/tools/create_cradle_haul.py

Construction (all parts authored in world meters, one native world):
  01 Left rigid rail (fixed)     - RIGID ABD, unequal short rail, fully fixed
  02 Right FEM rail (pinned root)- FEM tet solid, unequal long rail, pinned far end
  03 Cloth sling strap           - CLOTH Baraff-Witkin shell (labeled rope surrogate)
  04 Compliant pad               - FEM tet solid in loose contact with the sling
  05 Off-center haul load        - RIGID ABD dropped off center onto the pad
  06 Static ground               - STATIC authored collider surrogate
Two ASYMMETRIC SoftVertexStitch seams: left 4 stitches (0.02-0.04 m spacing),
right 2 stitches (0.08 m spacing); same 500 N/m per-stitch stiffness, so the
asymmetry is authored spacing/count under an off-center load.
"""
from pathlib import Path
import hashlib
import importlib
import json
import runpy
import struct
import sys
import time
import traceback

import bpy
import numpy as np

STUDIO = Path(__file__).resolve().parents[2]
ROOT = STUDIO / 'integration'
LIBUIPC = STUDIO / 'Libuipc'
DEST = ROOT / 'evidence/cradle-haul/run-01'
PROJECT = DEST / 'Rescue cradle haul.blend'
EVIDENCE = DEST / 'authoring.json'
MODULE = 'bl_ext.user_default.libuipc_blender'

if PROJECT.exists() or EVIDENCE.exists():
    raise RuntimeError('Owned cradle-haul output already exists; choose a new run directory')
projects = STUDIO / 'Projects'
assert DEST.resolve().is_relative_to((ROOT / 'evidence').resolve()), 'Write only owned evidence'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Guard the untouched user projects by digest while this script runs.
PROJECT_GUARDS = {p: sha(p) for p in projects.rglob('*.blend')}

runpy.run_path(str(LIBUIPC / 'tools' / 'activate.py'))
addon = importlib.import_module(MODULE)
demo = importlib.import_module(MODULE + '.demo')
sys.path.insert(0, str(LIBUIPC / 'layered-source' / 'integrations' / 'blender' / 'tests'))
from blender_integration import evaluated  # noqa: E402

scene = bpy.data.scenes.new('Rescue Cradle Haul')
bpy.context.window.scene = scene
scene.unit_settings.scale_length = 1.0
scene.render.fps = 100
scene.frame_start = 0
scene.frame_end = 60
s = scene.uipc_settings
s.python_executable = str(LIBUIPC / '.venv' / 'Scripts' / 'python.exe')
s.cache_directory = str(DEST / 'cache')
s.solver_accuracy = 'CONVERGED'
s.substeps = 2
s.friction = 0.8

BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def part(name, vertices, faces, role):
    mesh = bpy.data.meshes.new(name + ' mesh')
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.uipc_body.role = role
    return obj


def box(name, lo, hi, role):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return part(name, verts, BOX_FACES, role)


def rail_vertices(x_inner, x_outer):
    """Unequal rail: inner end bottom and top edges carry four seam vertices each
    (y ascending) so a field repair can rebind the sling over the rail top."""
    y = (-0.04, -0.02, 0.02, 0.04)
    zlo, zhi = 0.96, 1.04
    return [(x_inner, yi, zlo) for yi in y] \
         + [(x_inner, yi, zhi) for yi in y] \
         + [(x_outer, yi, zlo) for yi in y] \
         + [(x_outer, -0.04, zhi), (x_outer, 0.04, zhi)]


RAIL_FACES = ([(0, 1, 9, 8), (1, 2, 10, 9), (2, 3, 11, 10)],          # bottom, 3 quads
              [(4, 5, 12), (5, 13, 12), (5, 6, 13), (6, 7, 13)],      # top, 4 triangles
              [(0, 4, 12, 8)],                                        # side y-
              [(7, 3, 11, 13)],                                       # side y+
              [(0, 1, 4), (1, 5, 4), (1, 2, 5), (2, 6, 5), (2, 3, 6), (3, 7, 6)],  # inner end strip
              [(8, 9, 12), (9, 13, 12), (9, 10, 13), (10, 11, 13)])  # outer end strip


def orient_closed(faces):
    """Orient faces so every directed edge occurs exactly once (closed, consistent)."""
    n = len(faces)
    for mask in range(1 << n):
        directed = {}
        for i, f in enumerate(faces):
            f = f if mask >> i & 1 else f[::-1]
            for a, b in zip(f, f[1:] + f[:1]):
                directed[(a, b)] = directed.get((a, b), 0) + 1
        if all(v == 1 for v in directed.values()):
            return [f if mask >> i & 1 else f[::-1] for i, f in enumerate(faces)]
    raise RuntimeError('Rail surface is not orientably closed')


RAIL_FACES = tuple(orient_closed([f for group in RAIL_FACES for f in group]))

# --- 01 left rail: RIGID, fixed, shorter (0.7 m) ---
left_rail = part('01 | Left rigid rail (fixed)', rail_vertices(-0.4, -1.1), RAIL_FACES, 'RIGID')
left_rail.uipc_body.density = 7800
left_rail.uipc_body.rigidity = 1e9
left_rail.uipc_body.fixed = True
left_rail.uipc_body.contact_material = 'Rail'
demo.material(left_rail, 'Left rail display (illustrative steel)', (.55, .57, .6), metallic=.6)
left_rail['chimera_cradle_role'] = 'left rail: fixed rigid support, 0.7 m'

# --- 02 right rail: FEM, pinned at outer end, longer (1.0 m) ---
right_rail = part('02 | Right FEM rail (pinned root)', rail_vertices(0.4, 1.4), RAIL_FACES, 'FEM')
right_rail.uipc_body.young_modulus = 5e7
right_rail.uipc_body.poisson = 0.4
right_rail.uipc_body.density = 1500
right_rail.uipc_body.thickness = 0.002
right_rail.uipc_body.tet_edge_length = 0.05
right_rail.uipc_body.tet_quality_passes = 2
right_rail.uipc_body.contact_material = 'Rail'
demo.material(right_rail, 'Right rail display (illustrative stiff polymer)', (.35, .6, .35))
right_rail['chimera_cradle_role'] = 'right rail: FEM cantilever, 1.0 m, pinned root'

# --- 03 cloth sling strap ---
NX, NY = 21, 4
YS = (-0.04, -0.02, 0.02, 0.04)
XS = [round(-0.4 + 0.04 * i, 6) for i in range(NX)]
cverts = [(x, y, 0.95) for x in XS for y in YS]
cfaces = []
for i in range(NX - 1):
    for j in range(NY - 1):
        a = i * NY + j
        cfaces.append((a, a + NY, a + NY + 1, a + 1))
cloth = part('03 | Cloth sling strap', cverts, cfaces, 'CLOTH')
cloth.uipc_body.stretch = 5e4
cloth.uipc_body.shear = 5e4
cloth.uipc_body.bending = 3e4
cloth.uipc_body.thickness = 0.001
cloth.uipc_body.density = 200
cloth.uipc_body.poisson = 0.3
cloth.uipc_body.contact_material = 'Sling fabric'
demo.material(cloth, 'Sling display (labeled cloth rope surrogate I06)', (.75, .55, .15))
cloth['chimera_cradle_role'] = 'sling: cloth strap, labeled rope surrogate (I06 specified-only)'

# --- 04 compliant pad (FEM, loose contact above the sling) ---
pad = box('04 | Compliant pad (FEM)', (-0.16, -0.06, 0.985), (0.0, 0.06, 1.015), 'FEM')
pad.uipc_body.young_modulus = 2e5
pad.uipc_body.poisson = 0.4
pad.uipc_body.density = 900
pad.uipc_body.thickness = 0.003
pad.uipc_body.tet_edge_length = 0.03
pad.uipc_body.tet_quality_passes = 2
pad.uipc_body.contact_material = 'Pad'
demo.material(pad, 'Pad display (illustrative silicone, I07 measured material missing)', (.8, .3, .5))
pad['chimera_cradle_role'] = 'pad: illustrative FEM silicone surrogate (I07)'

# --- 05 off-center haul load ---
load = box('05 | Off-center haul load', (-0.18, -0.06, 1.14), (-0.06, 0.06, 1.26), 'RIGID')
load.uipc_body.density = 4000
load.uipc_body.rigidity = 1e9
load.uipc_body.contact_material = 'Cargo'
demo.material(load, 'Haul load display', (.9, .45, .1))
load['chimera_cradle_role'] = 'haul load: rigid companion carrier, dropped off center toward the left seam'

# --- 06 static ground (authored surrogate) ---
ground = box('06 | Static ground (authored surrogate)', (-1.3, -0.5, -0.1), (1.3, 0.5, 0.0), 'STATIC')
ground.uipc_body.contact_material = 'Ground'
demo.material(ground, 'Ground display (authored terrain surrogate, I08)', (.4, .38, .34))
ground['chimera_cradle_role'] = 'ground: authored static terrain surrogate (I08)'

# --- volumes before binding (FEM parts) ---
for obj in (right_rail, pad):
    for other in scene.objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    assert bpy.ops.uipc.generate_volume(blocking=True) == {'FINISHED'}


def indices_at(obj, coords):
    found = []
    for v in obj.data.vertices:
        for c in coords:
            if abs(v.co[0] - c[0]) < 1e-6 and abs(v.co[1] - c[1]) < 1e-6 and abs(v.co[2] - c[2]) < 1e-6:
                found.append(v.index)
                break
    return sorted(found)


def group(obj, name, ids):
    vg = obj.vertex_groups.new(name=name)
    vg.add(list(ids), 1.0, 'REPLACE')
    return ids


# Endpoint groups (world coordinates; surfaces preserved by generate_volume).
left_ids = indices_at(left_rail, [(-0.4, y, 0.96) for y in YS])
assert left_ids == [0, 1, 2, 3], left_ids
group(left_rail, 'Left seam A', left_ids)
left_top_ids = indices_at(left_rail, [(-0.4, y, 1.04) for y in YS])
assert left_top_ids == [4, 5, 6, 7], left_top_ids
group(left_rail, 'Left seam A top', left_top_ids)
group(left_rail, 'Left seam A top outer', [left_top_ids[0], left_top_ids[-1]])
right_end = indices_at(right_rail, [(0.4, -0.04, 0.96), (0.4, 0.04, 0.96)])
right_root = indices_at(right_rail, [(1.4, y, z) for y in YS + (-0.04, 0.04) for z in (0.96, 1.04)])
assert len(right_end) == 2 and len(right_root) == 6, (right_end, right_root)
group(right_rail, 'Right seam A', right_end)
group(right_rail, 'Fixed root', right_root)
right_rail.uipc_body.pin_group = 'Fixed root'
cloth_left = indices_at(cloth, [(-0.4, y, 0.95) for y in YS])
cloth_right = indices_at(cloth, [(0.4, y, 0.95) for y in YS])
assert cloth_left == [0, 1, 2, 3] and cloth_right == [(NX - 1) * NY + j for j in range(NY)], (cloth_left, cloth_right)
group(cloth, 'Left edge B', cloth_left)
group(cloth, 'Left edge B outer', [cloth_left[0], cloth_left[-1]])
group(cloth, 'Right edge B', [cloth_right[0], cloth_right[-1]])

# --- two ASYMMETRIC SoftVertexStitch seams via the installed operators ---
def bind_seam(active, other, name, group_a, group_b, stiffness):
    for o in scene.objects:
        o.select_set(False)
    active.select_set(True)
    other.select_set(True)
    bpy.context.view_layer.objects.active = active
    assert bpy.ops.uipc.attachment_add() == {'FINISHED'}
    entry = s.attachments[-1]
    entry.name = name
    entry.group_a = group_a
    entry.group_b = group_b
    entry.pairing = 'INDEX'
    entry.stiffness = stiffness
    entry.max_gap = 0.05
    assert bpy.ops.uipc.attachment_bind() == {'FINISHED'}
    record = json.loads(entry.binding)
    assert record['law'] == 'SoftVertexStitch-v1'
    return {'name': name, 'pairs': len(record['pairs']), 'stiffness_N_per_m': stiffness,
            'rest_lengths_m': [round(float(r), 6) for r in record['rest_lengths']]}


seams = [bind_seam(left_rail, cloth, 'Left rail to sling (4 stitches, 0.02-0.04 m spacing)',
                   'Left seam A', 'Left edge B', 500.),
         bind_seam(right_rail, cloth, 'Right rail to sling (2 stitches, 0.08 m spacing)',
                   'Right seam A', 'Right edge B', 500.)]
left_index, right_index = 0, 1

# Explicit friction pairing for the haul contact.
for a, b, f in (('Cargo', 'Pad', 1.2), ('Pad', 'Sling fabric', 1.0)):
    pair = s.contact_pairs.add()
    pair.material_a, pair.material_b, pair.friction = a, b, f

# Starter text with honest labeling (kept next to the construction).
text = bpy.data.texts.new('START HERE - Rescue Cradle Haul')
text.write('''RESCUE CRADLE HAUL - Layered Materials Workshop profile (R2)
Space/scrub replays the saved 0.6 s native bake. N > libuipc: inspect parts and seams.
N > Chimera: Inspect Connection Loads, Layer Trial Comparison, Physical Layer Continuation.
Two unequal rails (left rigid fixed 0.7 m; right FEM pinned root 1.0 m) carry a cloth sling
via two ASYMMETRIC SoftVertexStitch seams (left 4 stitches, 0.02-0.04 m spacing; right
2 stitches, 0.08 m spacing; 500 N/m each). A rigid haul load drops off center onto an
illustrative FEM pad resting in the sling. Release = disable the loaded left seam; repair =
partial rebind of that seam over the rail top ('Left seam A top outer' / 'Left edge B outer', 2 of 4 stitches, authoring-level field repair).
Store A/B compares the drops.
HONEST LABELS: stitches are finite-gap springs, NOT fracture/delamination (no force-triggered
slip; I09 deferred). The sling is a cloth rope surrogate (I06 specified-only). The pad is
Two unequal rails (left rigid fixed 0.7 m; right FEM pinned root 1.0 m) carry a cloth sling
via two ASYMMETRIC SoftVertexStitch seams (left 4 stitches, 0.02-0.04 m spacing; right
2 stitches, 0.08 m spacing; 500 N/m each). A rigid haul load drops off center onto an
illustrative FEM pad resting in the sling. Release = disable the loaded left seam; repair =
partial rebind of that seam over the rail top ('Left seam A top outer' / 'Left edge B outer', 2 of 4 stitches, authoring-level field repair).
Store A/B compares the drops.
Cached mesh playback, not arbitrary-time continuation. Open this file starts no solver.
''')

camera_data = bpy.data.cameras.new('Cradle camera')
camera = bpy.data.objects.new('Cradle camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (-0.55, -2.2, 1.1)
camera.rotation_euler = (1.35, 0, -0.12)
scene.camera = camera
sun_data = bpy.data.lights.new('Cradle sun', 'SUN')
sun_data.energy = 3
sun = bpy.data.objects.new('Cradle sun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.7, 0.2, 0.4)

# --- bake once (attached reference) through the installed native owner ---
assert not addon.runtime.is_running()
t0 = time.perf_counter()
assert bpy.ops.uipc.bake(blocking=True) == {'FINISHED'}
wall = time.perf_counter() - t0
directory = Path(bpy.path.abspath(s.last_bake)).resolve()
assert DEST / 'cache' in directory.parents, directory
assert not addon.runtime.is_running()

request = json.loads((directory / 'request.json').read_text())
result = json.loads((directory / 'result.json').read_text())
assert result['frames'] == 61, result['frames']
assert len(request['settings']['attachments']) == 2

# --- independent raw-cache decode of the attached bake ---
def raw_points():
    points = {}
    settings = request['settings']
    outputs = {v['index']: v for v in result['objects']}
    for i, body in enumerate(request['objects']):
        with np.load(directory / f'input_{i:04d}.npz') as a:
            local = a['vertices'].copy()
            matrix = a['matrix'].copy()
        if i in outputs:
            data = (directory / f'object_{i:04d}.mdd').read_bytes()
            frames, n = struct.unpack('>ii', data[:8])
            v = np.frombuffer(data, dtype='>f4', offset=8 + frames * 4).astype(float).reshape(frames, n, 3)
            if outputs[i].get('encoding') == 'AFFINE':
                v = np.asarray([local @ x[1:] + x[0] for x in v])
        else:
            v = local[None, :, :]
            frames = 1
        if frames == 1:
            v = np.repeat(v, result['frames'], axis=0)
        points[body['id']] = (v @ matrix[:3, :3].T + matrix[:3, 3]) * settings['unit_scale']
    return points


points = raw_points()
start = request['settings']['frame_start']
decoded = {}
for seam in request['settings']['attachments']:
    pair = np.array(seam['pairs'])
    d = points[seam['b']][:, pair[:, 1]] - points[seam['a']][:, pair[:, 0]]
    length = np.sqrt(np.einsum('...i,...i->...', d, d))
    ext = length - np.array(seam['rest_lengths'])
    scalar = seam['stiffness'] * ext
    decoded[seam['name']] = {'ext': ext, 'scalar': scalar,
                             'f': scalar[..., None] * d / length[..., None]}

load_id = next(b['id'] for b in request['objects'] if b['name'] == load.name)
load_z = points[load_id][:, :, 2].mean(axis=1)
attached_drop = float(load_z[0] - load_z[-1])
peak = {name: {'peak_N': float(np.abs(v['scalar']).max()),
               'peak_frame': int(np.unravel_index(np.argmax(np.abs(v['scalar'])), v['scalar'].shape)[0]) + start,
               'rest_residual_frame0_N': float(np.abs(v['scalar'][0]).max()),
               'net_vertical_final_N': float(v['f'][-1][:, 2].sum())}
        for name, v in decoded.items()}

part_ids = {b['id']: b['name'] for b in request['objects']}
digests = {}
for obj in scene.objects:
    if not hasattr(obj, 'uipc_body') or obj.uipc_body.role in ('NONE', 'STATIC'):
        continue
    digests[obj.name] = {str(f): hashlib.sha256(evaluated(obj, scene, f).astype('<f4').tobytes()).hexdigest()
                         for f in (1, 31, 61)}

# --- relative cache paths, then save the owned project ---
def relativize(obj):
    for mod in obj.modifiers:
        if mod.type == 'MESH_CACHE' and mod.filepath:
            path = Path(bpy.path.abspath(mod.filepath)).resolve()
            if DEST in path.parents:
                mod.filepath = '//' + path.relative_to(DEST).as_posix()


for obj in scene.objects:
    relativize(obj)
for pobj in bpy.data.objects:
    if pobj.get('uipc_affine_cache') == 1:
        relativize(pobj)
s.last_bake = '//' + directory.relative_to(DEST).as_posix()
s.cache_directory = '//cache'
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT), check_existing=False)
assert PROJECT.is_file()

untouched = {p: sha(p) for p in projects.rglob('*.blend')} == PROJECT_GUARDS
assert untouched, 'A user project changed during authoring!'
report = {
    'project': str(PROJECT), 'bake_directory': str(directory), 'user_projects_byte_identical': True,
    'bake_wall_seconds': round(wall, 3), 'native_seconds': result.get('performance', {}),
    'frames': result['frames'], 'fps': 100, 'substeps': 2, 'horizon_seconds': 0.6,
    'build_info': result['build_info'],
    'parts': {b['name']: b['material']['role'] for b in request['objects']},
    'seams': seams, 'peak_seam_loads_attached': peak,
    'attached_load_drop_m': attached_drop,
    'geometry_digests': digests,
    'scope': 'Owned authoring of the R2 rescue cradle: two unequal rails (RIGID fixed / FEM pinned), '
             'cloth sling (labeled rope surrogate I06), illustrative FEM pad (I07), off-center rigid haul '
             'load, static ground surrogate (I08), two asymmetric SoftVertexStitch seams. One attached '
             'reference bake; release/repair comparisons run in the workflow test. Finite-gap stitches, '
             'authoring-level release/repair only; no fracture or force-triggered slip (I09 deferred).',
    'labels': {'rope': 'I06 cloth sling surrogate (specified-only, not measured rope)',
               'pad': 'I07 illustrative FEM silicone, measured material missing',
               'ground': 'I08 authored static surrogate',
               'release_repair': 'AUTHORING-LEVEL seam disable/rebind; NOT force-triggered slip',
               'slip': 'I09 force-triggered slip deferred pending a native-law decision'},
}
EVIDENCE.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('CRADLE_HAUL_AUTHORING_PASS', json.dumps({k: v for k, v in report.items()
      if k not in ('geometry_digests', 'cache_sha256_tree_sample')}), flush=True)
