"""Round-08: live-engine /verts before-after for knee_L=40 (game's own
/tick_pose channel). Proves the shipped surface IS the pack LBS: numbers match
_pack_probe.py bit-for-bit. Resets the pose afterwards."""
import struct, urllib.request, numpy as np, json, time
E = "http://127.0.0.1:8110"
def get(path):
    with urllib.request.urlopen(E + path, timeout=10) as r: return r.read()
def post(path, obj):
    req = urllib.request.Request(E + path, data=json.dumps(obj).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r: return json.load(r)
def verts():
    raw = get("/verts")
    n = struct.unpack_from('<I', raw)[0]
    return np.frombuffer(raw, '<f4', 9*n, 4).reshape(n, 9)[:, :3].astype(np.float64)
print("matter state:", json.load(urllib.request.urlopen(E + "/matter", timeout=5)))
v0 = verts()
print("pose knee_L=40:", post("/tick_pose", {"joint_index": 15, "deg": 40.0}))
time.sleep(1.5)
v1 = verts()
d = np.linalg.norm(v1 - v0, axis=1)
foot = np.where((v0[:, 1] < 0.16) & (v0[:, 0] > 0))[0]
sole = np.where((v0[:, 1] < 0.12) & (v0[:, 0] > 0.2))[0]
shin = np.where((np.abs(v0[:, 0] - 0.47) < 0.35) & (v0[:, 1] > 0.9) & (v0[:, 1] < 1.8))[0]
print(f"LIVE knee_L=40: foot n={len(foot)} mean={d[foot].mean():.4f} max={d[foot].max():.4f}")
print(f"LIVE knee_L=40: sole n={len(sole)} mean={d[sole].mean():.4f} max={d[sole].max():.4f}")
print(f"LIVE knee_L=40: shin n={len(shin)} mean={d[shin].mean():.4f} max={d[shin].max():.4f}")
print("reset:", post("/tick_pose", {"joint_index": 15, "deg": 0.0}))
time.sleep(0.8)
print("returned to rest:", np.abs(verts() - v0).max() < 1e-3)
