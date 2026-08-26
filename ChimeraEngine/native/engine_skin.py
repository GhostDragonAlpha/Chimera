"""engine_skin.py — upload a SKINNED splat to the C++ Vulkan engine (GPU LBS path).

The engine renders a static splat via POST /membrane_bin. This loader uses the skinning
endpoints instead: /skin_bin (rest splat + per-splat LBS weights), /pose_store (named
pose slots), /pose_apply (skin.comp poses the splats on the GPU). In the engine window,
'P' toggles slot 0 (rest) <-> slot 1 (wave).

Steps:
  1. cb.load_splat -> (N,14) rest buffer; hide generator-junk filler splats (section.py
     _body_mask) by zeroing their alpha — invisible haze at rest, streaks when posed
     (matches skin.py stage_pose).
  2. skin_weights.npz -> interleaved N*4 weights [float(bone0), w0, float(bone1), w1].
  3. FK (skin.py _skin_spec / _fk) turns the pose spec into per-bone world-frame delta
     transforms (Q, T): p' = qrot(Q, p) + T. Slot 1 = wave, slot 0 = identity.
     ASSERTS the npz bone order == _skin_spec bone order (matrix order must match the
     weights' bone indices).

Usage (from the repo root, engine running from ChimeraEngine/engine/build/Release):
  python ChimeraEngine/native/engine_skin.py models/genbear/genbear_front.splat \
      --dir models/genbear/genbear_front_section \
      --skeleton models/genbear/rig/skeleton_sym.json \
      --spec models/genbear/rig/pose_wave.json \
      --camera 2.2 0.0 0.15
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
for _p in (str(_CHIMERA_ENGINE), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpp_bridge as cb              # noqa: E402
from section import _body_mask       # noqa: E402
import skin as skin_mod              # noqa: E402  (_skin_spec, _fk)

ENGINE = "http://localhost:8090"


def _post(path: str, data: bytes) -> dict:
    req = urllib.request.Request(ENGINE + path, data=data,
                                 headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("splat")
    ap.add_argument("--dir", required=True, help="section workdir holding skin_weights.npz")
    ap.add_argument("--skeleton", required=True)
    ap.add_argument("--spec", required=True, help="pose spec JSON (slot 1)")
    ap.add_argument("--camera", nargs=3, type=float, default=[2.2, 0.0, 0.15],
                    metavar=("radius", "theta", "phi"))
    a = ap.parse_args()
    workdir = Path(a.dir)

    # 1. rest splat, filler splats hidden in the UPLOADED buffer (alpha = 0)
    buf = cb.load_splat(a.splat)
    n = len(buf)
    hidden = ~_body_mask(buf)
    buf = buf.copy()
    buf[hidden, 6] = 0.0
    print(f"  rest splat: N={n}; hid {int(hidden.sum())} generator-junk filler splats")

    # 2. weights -> N*4 [float(bone0), w0, float(bone1), w1]; bone idx -1 = no influence
    wz = np.load(workdir / "skin_weights.npz")
    bones = [str(b) for b in wz["bones"]]
    nb = len(bones)
    w = np.stack([wz["bone0"].astype(np.float32), wz["w0"].astype(np.float32),
                  wz["bone1"].astype(np.float32), wz["w1"].astype(np.float32)],
                 axis=1).astype("<f4")
    assert w.shape == (n, 4), f"weights rows {w.shape[0]} != splats {n}"
    print(f"  weights: B={nb} bones {bones}")

    # 3. FK -> per-bone delta transforms for the wave pose (slot 1); slot 0 = identity
    skel = json.loads(Path(a.skeleton).read_text(encoding="utf-8"))
    spec = skin_mod._skin_spec(skel)
    assert list(spec["bones"]) == bones, (
        f"bone order mismatch: spec {list(spec['bones'])} vs npz {bones}")
    J = {k: np.array(v, dtype=np.float64) for k, v in skel["joints"].items()}
    pose_spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    D = skin_mod._fk(J, pose_spec.get("rotations", {}), spec)

    slot0 = np.zeros((nb, 7), dtype=np.float32)
    slot0[:, 0] = 1.0                       # identity quat qw=1, zero translation
    slot1 = np.zeros((nb, 7), dtype=np.float32)
    for i, bone in enumerate(spec["bones"]):
        Q, T = D[bone]                      # world-frame delta: p' = qrot(Q, p) + T
        slot1[i, 0:4] = Q
        slot1[i, 4:7] = T

    # 4. upload: skin first, then both pose slots
    cr, ct, cp = a.camera
    skin_bin = (struct.pack("<IIfff", n, nb, cr, ct, cp)
                + buf.astype("<f4").tobytes() + w.tobytes())
    r = _post("/skin_bin", skin_bin)
    print(f"  POST /skin_bin   (N={n}, B={nb}): {'ok' if r.get('ok') else 'FAIL ' + str(r)}")
    if not r.get("ok"):
        return 1
    for slot, mat in ((0, slot0), (1, slot1)):
        r = _post("/pose_store", struct.pack("<II", slot, nb) + mat.astype("<f4").tobytes())
        print(f"  POST /pose_store slot={slot}: {'ok' if r.get('ok') else 'FAIL ' + str(r)}")
        if not r.get("ok"):
            return 1
    print("  done — in the engine window, 'P' toggles rest <-> wave "
          "(or POST /pose_apply with a u32 slot)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
