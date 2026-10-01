"""raster.py -- THE SOFTWARE RASTERIZER (the pilot's deterministic pixel metric).

The replay page (replay.html + system Chrome) produced real MADs early in the
session, then the environment degraded (the system Chrome broke loopback
connects ~16:00; the bundled headless chromium's WebGL readback returns empty
frames -- both recorded in the receipt). The metric must not depend on a
flaky browser, so the final instrument rasterizes in numpy with the SAME
vertex transform and the SAME fragment math as the playable slice's own
shader program (tools/playable_slice/index.html MESH_P, copied verbatim
there):

    clip = VP * vec4(pos, 1); n = normalize(aNrm); c = aCol
    d = max(dot(n, L), 0) * 0.75 + 0.25,  L = normalize(0.5, 0.9, 0.35)
    o = vec4(c * d, 1)

Coverage uses pixel-center sampling with a z-buffer; the guide grid and the
marker ring are omitted (they are pixel-identical on both sides of every
pair and contribute exactly zero to the difference). Same bytes in -> same
pixels out (F5 holds by construction and is still double-run tested).
"""
from __future__ import annotations

import numpy as np

W, H = 960, 540
L = np.array([0.5, 0.9, 0.35]); L = L / np.linalg.norm(L)
CLEAR = np.array([11, 13, 16], dtype=np.uint8)   # 0.043,0.051,0.063


def look_from(yaw, pit, dist, tx, ty, tz):
    cx, cy, cz = tx + dist * np.cos(pit) * np.sin(yaw), ty + dist * np.sin(pit), \
        tz + dist * np.cos(pit) * np.cos(yaw)
    f = np.array([cx - tx, cy - ty, cz - tz]); f = f / np.linalg.norm(f)
    up = np.array([0.0, 1.0, 0.0])
    s = np.cross(f, up); s = s / (np.linalg.norm(s) or 1e-9)
    u = np.cross(s, f)
    return np.array([
        [s[0], u[0], f[0], 0.0],
        [s[1], u[1], f[1], 0.0],
        [s[2], u[2], f[2], 0.0],
        [-np.dot(s, [cx, cy, cz]), -np.dot(u, [cx, cy, cz]),
         -np.dot(f, [cx, cy, cz]), 1.0]])


def persp(fov, asp, n, f):
    t = 1.0 / np.tan(fov / 2)
    return np.array([
        [t / asp, 0, 0, 0],
        [0, t, 0, 0],
        [0, 0, (f + n) / (n - f), -1],
        [0, 0, 2 * f * n / (n - f), 0]])


def camera_vp(cam, target, w=W, h=H):
    yaw, pit, dist = cam
    V = look_from(yaw, pit, dist, *target)
    P = persp(0.9, w / h, 0.05, 60)
    # THE TRANSPOSE FIX (lane/push-channel-20260920): look_from and persp
    # lay the page's COLUMN-major arrays into numpy, i.e. each grid is
    # M_true^T. raster_frame clips with pos @ vp.T (row-major M @ p), which
    # needs vp = (V_true @ P_true).T = (V @ P).T. The previous `P @ V`
    # applied both in the wrong order: the body projected to w ~ 0.02
    # (degenerate), MAD 0 whenever both sides degenerated identically and
    # ~13.3 when one side's vertices crossed the w-plane -- the pilot's
    # banked "13.33 torn frame" signature, now explained as an instrument
    # artifact class. Verified: body center projects to ndc (0, 0.27, 0.95).
    return (V @ P).T


def raster_frame(f32: np.ndarray, vp: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """f32: (n,9) pos|nrm|col -> (H,W,3) uint8, the page's shader in numpy."""
    img = np.zeros((H, W, 3), dtype=np.uint8)
    img[:] = CLEAR
    n_v = f32.shape[0]
    pos = np.concatenate([f32[:, 0:3], np.ones((n_v, 1))], axis=1)   # homog
    clip = pos @ vp.T                                                # (n,4)
    w = clip[:, 3]
    safe = np.abs(w) > 1e-9
    ndc = np.zeros((n_v, 3)); ndc[safe] = clip[safe, 0:3] / w[safe, None]
    sx = (ndc[:, 0] * 0.5 + 0.5) * W
    sy = (-ndc[:, 1] * 0.5 + 0.5) * H
    depth = ndc[:, 2]
    zbuf = np.full((H, W), np.inf, dtype=np.float64)

    nrm = f32[:, 3:6]
    col = f32[:, 6:9]
    for t in range(0, len(idx), 3):                  # indexed triangles
        ia, ib, ic = int(idx[t]), int(idx[t + 1]), int(idx[t + 2])
        if not (safe[ia] and safe[ib] and safe[ic]):
            continue
        x0, y0, d0 = sx[ia], sy[ia], depth[ia]
        x1, y1, d1 = sx[ib], sy[ib], depth[ib]
        x2, y2, d2 = sx[ic], sy[ic], depth[ic]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            continue
        xmin = max(0, int(min(x0, x1, x2))); xmax = min(W - 1, int(max(x0, x1, x2)) + 1)
        ymin = max(0, int(min(y0, y1, y2))); ymax = min(H - 1, int(max(y0, y1, y2)) + 1)
        if xmin > xmax or ymin > ymax:
            continue
        xs = np.arange(xmin, xmax + 1) + 0.5
        ys = np.arange(ymin, ymax + 1) + 0.5
        px, py = np.meshgrid(xs, ys)
        w0 = ((x1 - px) * (y2 - py) - (x2 - px) * (y1 - py)) / area
        w1 = ((x2 - px) * (y0 - py) - (x0 - px) * (y2 - py)) / area
        w2 = ((x0 - px) * (y1 - py) - (x1 - px) * (y0 - py)) / area
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        zz = w0 * d0 + w1 * d1 + w2 * d2
        sub_z = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        upd = inside & (zz < sub_z)
        if not upd.any():
            continue
        n_face = nrm[ia] + nrm[ib] + nrm[ic]
        nl = np.linalg.norm(n_face)
        n_face = n_face / (nl or 1e-9)
        dd = max(float(np.dot(n_face, L)), 0.0) * 0.75 + 0.25
        rgb = np.clip(col[ia] * dd + 0.5, 0, 255).astype(np.uint8)
        sub_img = img[ymin:ymax + 1, xmin:xmax + 1]
        sub_img[upd] = rgb
        sub_z[upd] = zz[upd]
    return img


def mad_frames(a: np.ndarray, b: np.ndarray) -> dict:
    diff = np.abs(a.astype(np.int16) - b.astype(np.int16))
    return {"mad": round(float(diff.mean()), 4),
            "max": int(diff.max()),
            "pct_nonzero": round(float((diff.sum(axis=2) > 0).mean() * 100.0), 3)}
