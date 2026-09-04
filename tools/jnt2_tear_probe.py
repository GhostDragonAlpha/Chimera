"""jnt2_tear_probe.py — the JNT2 falsifier instrument. (2026-09-03)

THE TEAR METRIC: background pixels ENCLOSED BY the creature's silhouette in
the elbow flexion region. The engine renders opaque geometry; the only way
background shows inside the outline is a hole — a skin tear. (A tighter flex
also shrinks the projected arm, so we report the metric, not the bbox.)

Run AFTER posting a pack; assumes the show is paused and thetas are held.
Usage: python tools/jnt2_tear_probe.py <flex_deg>
"""
import io, json, struct, sys, urllib.request
import zlib
import numpy as np

ENG = "http://127.0.0.1:8090"

def get(path, timeout=8):
    with urllib.request.urlopen(ENG + path, timeout=timeout) as r:
        return r.read()

def post(path, obj, timeout=8, raw=None):
    data = raw if raw is not None else json.dumps(obj).encode()
    req = urllib.request.Request(ENG + path, data=data,
                                 headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def png_rgba(buf):
    assert buf[:8] == b"\x89PNG\r\n\x1a\n", "not a png"
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(buf):
        ln, typ = struct.unpack(">I4s", buf[pos:pos + 8]); pos += 8
        data = buf[pos:pos + ln]; pos += ln + 4
        if typ == b"IHDR": w, h = struct.unpack(">II", data[:8])
        elif typ == b"IDAT": idat += data
        elif typ == b"IEND": break
    raw = zlib.decompress(idat)
    stride = w * 4 + 1
    img = np.zeros((h, w, 4), np.uint8)
    prev = np.zeros(w * 4, np.int32)
    for y in range(h):
        f = raw[y * stride]
        line = np.frombuffer(raw[y * stride + 1:(y + 1) * stride], np.uint8).astype(np.int32)
        if f == 0: cur = line
        elif f == 1:
            cur = line.copy()
            for i in range(4, len(cur)): cur[i] = (cur[i] + cur[i - 4]) & 255
        elif f == 2: cur = (line + prev) & 255
        elif f == 3:
            cur = line.copy()
            for i in range(len(cur)):
                a = cur[i - 4] if i >= 4 else 0
                cur[i] = (cur[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            cur = line.copy()
            for i in range(len(cur)):
                a = cur[i - 4] if i >= 4 else 0
                b, c = int(prev[i]), int(prev[i - 4]) if i >= 4 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 255
        else: raise ValueError(f"filter {f}")
        img[y] = cur.reshape(w, 4)
        prev = cur
    return img, w, h

def background_mask(img):
    # v2 (convicted v1): the cyclorama is a smooth gradient in x,y — fit
    # color(x,y) linearly from the guaranteed-background frame border, then
    # classify by model distance. v1's flatness test misread dark fur
    # ([37,25,16]) as background; fur is nowhere near the gradient's value.
    g = img[:, :, :3].astype(np.float64)
    h, w, _ = g.shape
    B = 60
    border = np.zeros((h, w), bool)
    border[:B, :] = border[-B:, :] = True
    border[:, :B] = border[:, -B:] = True
    ys, xs = np.where(border)
    A = np.stack([xs, ys, np.ones_like(xs)], axis=1).astype(np.float64)
    coef, *_ = np.linalg.lstsq(A, g[ys, xs], rcond=None)
    yy, xx = np.mgrid[0:h, 0:w]
    model = (coef[0][None, None] * xx[..., None] + coef[1][None, None] * yy[..., None]
             + coef[2][None, None])
    dist = np.linalg.norm(g - model, axis=2)
    return dist < 12.0

def tear_metric(mask, region):
    x0, x1, y0, y1 = region
    sub = mask[y0:y1, x0:x1]
    # enclosed holes: background components NOT touching the region border
    from collections import deque
    h, w = sub.shape
    seen = np.zeros_like(sub, bool)
    holes = 0
    for sy, sx in zip(*np.where(sub & ~seen)):
        if seen[sy, sx]: continue
        q = deque([(sy, sx)]); seen[sy, sx] = True
        comp = [(sy, sx)]; touches = False
        while q:
            y, x = q.popleft()
            if y in (0, h - 1) or x in (0, w - 1): touches = True
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and sub[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; q.append((ny, nx)); comp.append((ny, nx))
        if not touches: holes += len(comp)
    return holes

def main():
    flex = float(sys.argv[1]) if len(sys.argv) > 1 else 125.0
    # pause + select nothing (gizmo off the measurement), elbows to +/-flex
    post("/show", {"playing": False})
    post("/joint", {"select": -1})
    post("/joint", {"joint": "elbow_L", "theta": flex})
    post("/joint", {"joint": "elbow_R", "theta": flex})
    png = get("/frame", timeout=10)
    img, w, h = png_rgba(png)
    mask = background_mask(img)
    # elbow band from the pack: elbows sit near y 4.9, arms near x +/-1.8
    # screen-space: project via /project? no — fixed interior window derived
    # from the last audit's pixel bbox (arm region), generous on purpose.
    j = json.loads(get("/joints"))
    print(json.dumps({"law": j.get("law", "pre-JNT2 (no field)"),
                      "flex_deg": flex,
                      "note": "regions chosen from the 2560x1440 frame, arm band"},
                     indent=1))
    # two windows: left arm / right arm thirds of the frame, mid-height
    for label, region in [("arm_L", (200, 1100, 500, 1150)),
                          ("arm_R", (1500, 2400, 500, 1150))]:
        holes = tear_metric(mask, region)
        print(f"  {label}: enclosed-background pixels = {holes}")

if __name__ == "__main__":
    main()
