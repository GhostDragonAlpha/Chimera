"""Field-by-field diff of two JNT3 packs: shipped vs regenerated."""
import struct, numpy as np

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
    owner = ints(nv); w = floats(nv)
    J = floats(3*nj).reshape(nj,3); AX = floats(3*nj).reshape(nj,3)
    ROM = floats(2*nj).reshape(nj,2); parents = ints(nj)
    j2 = ints(nv); w2 = floats(nv)
    assert p == len(b), (p, len(b))
    return dict(nv=nv, nj=nj, names=names, owner=owner, w=w, J=J, AX=AX,
                ROM=ROM, parents=parents, j2=j2, w2=w2)

A = parse(r"E:/PythonChimera/Saved/meshes/monkey_joints.bin")
B = parse(r"E:/PythonChimera/tools/game_shell/evidence/round-08/_scratch_gen/monkey_joints_repro.bin")
print('nv', A['nv'], B['nv'], ' nj', A['nj'], B['nj'], ' names equal:', A['names']==B['names'])
for f in ('owner','w','J','AX','ROM','parents','j2','w2'):
    a, b = A[f], B[f]
    if a.shape != b.shape:
        print(f, 'SHAPE DIFF', a.shape, b.shape); continue
    if np.array_equal(a, b):
        print(f'{f:8s} identical')
    else:
        d = (a != b) if a.dtype.kind=='i' or a.dtype.kind=='u' else (np.abs(a-b) > 0)
        n = int(d.sum()) if d.ndim==1 else int(d.any(axis=-1).sum())
        print(f'{f:8s} DIFFERS in {n} rows')
        if f == 'ROM':
            for i in range(A['nj']):
                if not np.array_equal(A['ROM'][i], B['ROM'][i]):
                    print(f"   {A['names'][i]:12s} shipped {A['ROM'][i]} vs regen {B['ROM'][i]}")
        if f == 'owner':
            import collections
            idx = np.where(A['owner'] != B['owner'])[0]
            pairs = collections.Counter((A['names'][A['owner'][i]], B['names'][B['owner'][i]]) for i in idx)
            for k,v in pairs.most_common(20): print('   ', k, v)
        if f == 'j2':
            idx = np.where(A['j2'] != B['j2'])[0]
            import collections
            pairs = collections.Counter((A['names'][A['j2'][i]], B['names'][B['j2'][i]]) for i in idx)
            for k,v in pairs.most_common(20): print('   ', k, v)
        if f in ('w','w2'):
            idx = np.where(a != b)[0]
            print('    max abs diff', np.abs(a-b).max(), ' n=', len(idx), ' sample idx', idx[:10])
        if f in ('J','AX'):
            idx = np.where((a != b).any(axis=1))[0]
            for i in idx[:30]: print('   ', A['names'][i], a[i], b[i])
