import json
import struct
import hashlib

import numpy as np
import trimesh

GLB = r"E:/PythonChimera/models/cad_bear/cad_bear.glb"
OUT = r"E:/PythonChimera/Chimera/Python/bear_mesh.bin"
SUM = r"E:/PythonChimera/Chimera/Python/bear_mesh_summary.json"


def load_vertices_faces(glb):
    sc = trimesh.load(glb)
    if isinstance(sc, trimesh.Scene):
        verts, faces, base = [], [], 0
        for g in sc.geometry.values():
            v = np.asarray(g.vertices, dtype=np.float32)
            f = np.asarray(g.faces, dtype=np.int32)
            verts.append(v)
            faces.append(f + base)
            base += len(v)
        V = np.vstack(verts).astype(np.float32)
        F = np.vstack(faces).astype(np.int32)
    else:
        V = np.asarray(sc.vertices, dtype=np.float32)
        F = np.asarray(sc.faces, dtype=np.int32)
    return V, F


V, F = load_vertices_faces(GLB)
V = np.ascontiguousarray(V, dtype=np.float32)
F = np.ascontiguousarray(F, dtype=np.int32)
N, M = V.shape[0], F.shape[0]
ref = hashlib.sha256(V.tobytes()).hexdigest()

with open(OUT, "wb") as f:
    f.write(struct.pack("ii", N, M))
    f.write(V.tobytes())
    f.write(F.tobytes())

summary = {"glb": GLB, "vertices": int(N), "triangles": int(M),
           "sha256_vertices_ref": ref, "bin": OUT}
with open(SUM, "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
