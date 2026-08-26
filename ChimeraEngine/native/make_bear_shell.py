"""Convert bear_mesh.bin (the SPIACE bear extracted from cad_bear.glb) into the
C++ Vulkan engine's splat-shell JSON that cpp_bridge.render_teddy_movie consumes.

Shell format (see cpp_bridge._shell_level_buf):
  {"levels":[ {"cell":float, "pos":[[x,y,z],...],   # cell units
               "col":[[r,g,b],...]}, ... ]}          # 0..1

Our bear has no vertex colors, so we assign a warm teddy tone. Two LOD levels:
level 0 = all ~30k surface verts, level 1 = 1/4 decimation. cell=1.0 -> world
units = model units (~0.3 across); the engine frames the camera from the extent.
"""
import struct, json
import numpy as np

BIN = r"E:\PythonChimera\Chimera\Python\bear_mesh.bin"
OUT = r"E:\PythonChimera\ChimeraEngine\native\bear_shell.json"

with open(BIN, "rb") as f:
    data = f.read()
N, M = struct.unpack_from("<ii", data, 0)
off = 8
verts = np.frombuffer(data[off:off + N * 3 * 4], dtype="<f4").astype(np.float32).reshape(-1, 3)

TONE = [0.58, 0.40, 0.26]  # teddy brown

def level(idxs):
    p = verts[idxs].tolist()
    c = [TONE for _ in idxs]
    return {"cell": 1.0, "pos": p, "col": c}

all_idx = np.arange(N)
dec_idx = np.arange(0, N, 4)
shell = {"levels": [level(all_idx), level(dec_idx)]}
with open(OUT, "w") as f:
    json.dump(shell, f)
print(f"wrote {OUT}: levels={len(shell['levels'])} "
      f"verts L0={len(shell['levels'][0]['pos'])} L1={len(shell['levels'][1]['pos'])}")
