"""walk_test.py -- THE STANCE/BALANCE BARS (fleet F1, lead-completed).

HTTP-only verification of the stance servo: gravity on, stance on, a
lateral disturbance, and the lean (horizontal offset of the body
centroid from the support centroid) measured straight from /verts.

Usage: python tools/walk_test.py [--base URL]
"""
import argparse
import json
import struct
import time
import urllib.request

BASE = "http://127.0.0.1:8107"
BAND_M = 0.05          # support band: verts within 5 cm of the lowest point
CALM_PA = 1000.0


def get(path, timeout=15):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read()


def post(path, obj, timeout=15):
    r = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                               method="POST",
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read()


def verts():
    raw = get("/verts")
    n = struct.unpack("<I", raw[:4])[0]
    out = []
    for v in range(n):
        x, y, z = struct.unpack_from("<fff", raw, 4 + v * 12)
        out.append((x, y, z))
    return out


def lean(vs):
    ys = [p[1] for p in vs]
    floor = min(ys)
    band = [p for p in vs if p[1] - floor <= BAND_M]
    body = [p for p in vs if p[1] - floor > 2.0]
    if not band or not body:
        return None
    bx = sum(p[0] for p in band) / len(band)
    bz = sum(p[2] for p in band) / len(band)
    cx = sum(p[0] for p in body) / len(body)
    cz = sum(p[2] for p in body) / len(body)
    return ((cx - bx) ** 2 + (cz - bz) ** 2) ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    args = ap.parse_args()
    s = json.loads(get("/tick_state"))
    print(f"engine: sealed={s['sealed']} cells={s['n_cells']} "
          f"gravity={s.get('gravity_on')} stance={s.get('stance_on')}")
    if not s["sealed"]:
        print("the world is not sealed — run the payload+seal script first")
        return

    before = lean(verts())
    print(f"rest lean: {before:.4f} m")

    # disturb: a held 20 kN lateral touch at the hip height
    post("/tick_touch", {"hit": [0.48, 1.6, 0.2], "force_n": 20000})
    import time
    time.sleep(2.5)
    mid = lean(verts())
    post("/tick_touch_clear", {})
    time.sleep(4.0)
    after = lean(verts())
    st = json.loads(get("/tick_state"))
    print(f"lean: rest={before:.4f} disturbed={mid:.4f} healed={after:.4f} m")
    print(f"pressures healed to: {max(abs(c['P']) for c in st['cells']):.0f} Pa")
    ok = after < mid and mid > before
    print(f"STANCE VERDICT: {'PASS' if ok else 'CHECK'} "
          f"(disturbance raises lean; the body recovers after release)")


if __name__ == "__main__":
    main()
