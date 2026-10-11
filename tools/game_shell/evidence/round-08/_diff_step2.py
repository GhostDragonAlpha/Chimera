"""Round-08 Step 3 ownership diff: regenerated pack vs shipped backup.

Usage: python _diff_step2.py NEW_PACK
Compares per-vertex owner/w/joint2/w2 and the joint tables (J, AX, ROM,
parents) against monkey_joints.bin.bak-74b3ab04. Every changed vertex must be
in the foot or hand region; ROM/J/AX/parents must be IDENTICAL.
"""
import struct, sys, collections
import numpy as np

ROOT = r"E:/PythonChimera"
EV = ROOT + r"/tools/game_shell/evidence/round-08"


def parse(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'JNT3'
    nv, nj, nl = struct.unpack_from('<III', b, 4)
    p = 16; names = []
    while len(names) < nj:
        z = b.index(b'\x00', p); names.append(b[p:z].decode()); p = z + 1
    def ints(n):
        nonlocal p
        a = np.frombuffer(b, '<i4', n, p).copy(); p += 4*n; return a
    def floats(n):
        nonlocal p
        a = np.frombuffer(b, '<f4', n, p).copy(); p += 4*n; return a
    d = {}
    d['names'] = names; d['nv'] = nv; d['nj'] = nj
    d['owner'] = ints(nv); d['w'] = floats(nv)
    d['J'] = floats(3*nj).reshape(nj, 3); d['AX'] = floats(3*nj).reshape(nj, 3)
    d['ROM'] = floats(2*nj).reshape(nj, 2); d['parents'] = ints(nj)
    d['joint2'] = ints(nv); d['w2'] = floats(nv)
    return d


new = parse(sys.argv[1])
old = parse(EV + r"/monkey_joints.bin.bak-74b3ab04")
assert new['names'] == old['names'] and new['nv'] == old['nv']

# mesh for region classification (engine order == pack order)
mesh = open(ROOT + r"/Saved/meshes/monkey_birth.bin", 'rb').read()
nv_m, _ = struct.unpack_from('<II', mesh)
xyz = np.frombuffer(mesh, '<f4', 3*nv_m, 8).reshape(nv_m, 3).astype(np.float64)
assert nv_m == new['nv']

print('=== joint tables (must be IDENTICAL) ===')
for k in ('J', 'AX', 'ROM', 'parents'):
    same = np.array_equal(new[k], old[k])
    print(f'{k:8s} identical: {same}')
    if not same and k == 'ROM':
        for i, n in enumerate(new['names']):
            if not np.array_equal(new['ROM'][i], old['ROM'][i]):
                print(f'  ROM DIFF {n}: {old["ROM"][i]} -> {new["ROM"][i]}')

names = np.array(new['names'])
changed = np.where((new['owner'] != old['owner']) | (new['w'] != old['w'])
                   | (new['joint2'] != old['joint2']) | (new['w2'] != old['w2']))[0]
print(f'\n=== per-vertex fields: {len(changed)}/{new["nv"]} verts changed any of owner/w/joint2/w2 ===')

# region classification of every changed vert
def region(v):
    x, y, z = xyz[v]
    if y < 0.38 and abs(x) > 0.2:
        return 'foot'
    if abs(x) > 1.8 and y < 4.15 and np.hypot(x - 2.23*np.sign(x), y - 4.02) < 2.2:
        return 'hand'
    return 'OTHER'

regs = collections.Counter(region(v) for v in changed)
print('changed-vert regions:', dict(regs))
other = [v for v in changed if region(v) == 'OTHER']
for v in other[:20]:
    print(f'  OTHER v={v} xyz={xyz[v].round(2)} '
          f'{names[old["owner"][v]]}(w={old["w"][v]:.2f},j2={names[old["joint2"][v]]},w2={old["w2"][v]:.2f}) -> '
          f'{names[new["owner"][v]]}(w={new["w"][v]:.2f},j2={names[new["joint2"][v]]},w2={new["w2"][v]:.2f})')

print('\n=== owner transitions (from -> to), counts ===')
tr = collections.Counter()
for v in changed:
    o, n = names[old['owner'][v]], names[new['owner'][v]]
    if o != n:
        tr[(o, n)] += 1
for (o, n), c in sorted(tr.items(), key=lambda kv: -kv[1]):
    print(f'  {o:>13s} -> {n:<13s} {c}')
n_own = sum(tr.values())
print(f'owner changed: {n_own}; w/j2/w2-only changed: {len(changed) - n_own}')

# rest pose must stay bit-identical: identity check is w+j2 law-independent,
# but assert w in [0,1] and share law w2 == 1-w
share = np.abs(new['w'].astype(np.float64) + new['w2'].astype(np.float64) - 1.0).max()
print(f'\nshare law max |w + w2 - 1| = {share:.3e}')
print(f'owner range: [{new["owner"].min()}, {new["owner"].max()}] (decoder requires >= 0)')
