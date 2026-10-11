"""Round-08 Step 5: live-engine verification of the REPAIRED pack (8ef83b7f).

Pattern: _live_verts_probe.py. Exercises the game's own /tick_pose channel and
/verts stream, comparing against the pure-LBS sim predictions recorded in
08_step3_scope.md. Resets every pose afterwards; ends at rest.
"""
import struct, urllib.request, json, time, sys
import numpy as np

E = "http://127.0.0.1:8110"
ROOT = r"E:/PythonChimera"
EV = ROOT + r"/tools/game_shell/evidence/round-08"


def get(path):
    with urllib.request.urlopen(E + path, timeout=10) as r:
        return r.read()


def post(path, obj):
    req = urllib.request.Request(E + path, data=json.dumps(obj).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def verts():
    raw = get("/verts")
    n = struct.unpack_from('<I', raw)[0]
    return np.frombuffer(raw, '<f4', 9 * n, 4).reshape(n, 9)[:, :3].astype(np.float64)


def parse_pack(path):
    b = open(path, 'rb').read()
    assert b[:4] == b'JNT3'
    nv, nj, nl = struct.unpack_from('<III', b, 4)
    p = 16; names = []
    while len(names) < nj:
        z = b.index(b'\x00', p); names.append(b[p:z].decode()); p = z + 1

    def ints(n):
        nonlocal p
        a = np.frombuffer(b, '<i4', n, p).copy(); p += 4 * n; return a

    def floats(n):
        nonlocal p
        a = np.frombuffer(b, '<f4', n, p).copy(); p += 4 * n; return a
    return {'names': names, 'nv': nv, 'nj': nj,
            'owner': ints(nv), 'w': floats(nv),
            'J': floats(3 * nj).reshape(nj, 3), 'AX': floats(3 * nj).reshape(nj, 3),
            'ROM': floats(2 * nj).reshape(nj, 2), 'parents': ints(nj),
            'joint2': ints(nv), 'w2': floats(nv)}


new = parse_pack(ROOT + r"/Saved/meshes/monkey_joints.bin")
old = parse_pack(EV + r"/monkey_joints.bin.bak-74b3ab04")
assert new['names'] == old['names']
unchanged_bind = ((new['owner'] == old['owner']) & (new['w'] == old['w'])
                  & (new['joint2'] == old['joint2']) & (new['w2'] == old['w2']))

mesh = open(ROOT + r"/Saved/meshes/monkey_birth.bin", 'rb').read()
nv_m, nf_m = struct.unpack_from('<II', mesh)
xyz = np.frombuffer(mesh, '<f4', 3 * nv_m, 8).reshape(nv_m, 3).astype(np.float64)

names = new['names']
i_knee, i_ankle = names.index('knee_L'), names.index('ankle_L')
i_wrist, i_tmid = names.index('wrist_L'), names.index('tail_mid')
i_tbase, i_ttip = names.index('tail_base'), names.index('tail_tip')
print(f"joint idx: knee_L={i_knee} ankle_L={i_ankle} wrist_L={i_wrist} "
      f"tail_mid={i_tmid} tail_base={i_tbase} tail_tip={i_ttip}")
print(f"ROM knee_L={new['ROM'][i_knee]} ankle_L={new['ROM'][i_ankle]} "
      f"wrist_L={new['ROM'][i_wrist]} tail_mid={new['ROM'][i_tmid]}")

# bands (rest geometry, engine order == mesh order)
foot = np.where((xyz[:, 1] < 0.16) & (xyz[:, 0] > 0))[0]
sole = np.where((xyz[:, 1] < 0.12) & (xyz[:, 0] > 0.2))[0]
shin = np.where((np.abs(xyz[:, 0] - 0.47) < 0.35) & (xyz[:, 1] > 0.9) & (xyz[:, 1] < 1.8))[0]
shin_unch = shin[unchanged_bind[shin]]
handL = np.where((xyz[:, 0] > 1.8) & (xyz[:, 1] < 4.15)
                 & (np.hypot(xyz[:, 0] - 2.23, xyz[:, 1] - 4.02) < 2.2))[0]
band_tb = np.where(new['owner'] == i_tbase)[0]
band_tm = np.where(new['owner'] == i_tmid)[0]
band_tt = np.where(new['owner'] == i_ttip)[0]
band_tb_old = np.where(old['owner'] == i_tbase)[0]
print(f"tail bands (new pack): base n={len(band_tb)} mid n={len(band_tm)} tip n={len(band_tt)}"
      f" | old tail_base n={len(band_tb_old)} (delta {len(band_tb) - len(band_tb_old)})")


def stats(d, idx):
    return f"n={len(idx)} mean={d[idx].mean():.4f} max={d[idx].max():.4f}"


def probe_pose(label, body, bands):
    r = post("/tick_pose", body)
    assert r.get('ok'), f"{label} refused: {r}"
    time.sleep(1.5)
    d = np.linalg.norm(verts() - v0, axis=1)
    out = {nm: stats(d, ix) for nm, ix in bands.items()}
    post("/tick_pose", {**{k: v for k, v in body.items() if k != 'deg'}, "deg": 0.0})
    time.sleep(0.8)
    back = np.abs(verts() - v0).max()
    out['reset_max_dev'] = f"{back:.2e}"
    print(f"--- {label} ---")
    for k, v in out.items():
        print(f"  {k:16s} {v}")
    return d


print("matter state:", json.loads(get("/matter")))
st = json.loads(get("/tick_state"))
print(f"body_model: {st.get('body_model')} | ticks: {st.get('ticks')}")

v0 = verts()
rest_dev = np.abs(v0 - xyz).max()
print(f"REST vs mesh: max|live-rest - mesh| = {rest_dev:.3e} (bit-identical: {rest_dev == 0})")

probe_pose("knee_L=40 (name)", {"joint": "knee_L", "deg": 40.0},
           {"foot_L": foot, "sole_L": sole, "shin_box": shin,
            "shin_unchanged_bind": shin_unch})
probe_pose("ankle_L=30 (name)", {"joint": "ankle_L", "deg": 30.0},
           {"foot_L": foot, "sole_L": sole, "shin_box": shin})
probe_pose("wrist_L=40 (name)", {"joint": "wrist_L", "deg": 40.0},
           {"hand_L": handL})
probe_pose("tail_mid=30 (name)", {"joint": "tail_mid", "deg": 30.0},
           {"tail_base_band": band_tb, "tail_mid_band": band_tm, "tail_tip_band": band_tt})

vf = verts()
print(f"FINAL at rest: max|v_final - v_rest| = {np.abs(vf - v0).max():.3e}")
print("DONE")
