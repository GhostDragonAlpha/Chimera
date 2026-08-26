"""cpp_bridge.py -- point the appearance dyad at the C++ Vulkan engine's /frame.

The C++ engine is the emission target (docs/THE_RENDERER_DECISION.md). This module is the glue:
it reads a membrane's particle buffer from `splat_appearance.movie_buffers` (the Python story
membranes the C++ engine cannot run -- `story/*/physics.py` emit() functions), converts the
28-float splat buffer to the C++ engine's 7-float vertex layout, POSTs it to the engine's
`/membrane` endpoint (which frames the camera and loads the buffer into the Vulkan renderer), then
GETs the rendered PNG from `/frame`. The dyad judges THAT PNG -- so the C++ Vulkan engine is the
rasterizer the proof points at, not `splat_appearance`'s own GPU path.
"""
from __future__ import annotations

import json
import math
import os
import struct
import urllib.request
from pathlib import Path

import numpy as np

ENGINE_URL = os.environ.get("CHIMERA_ENGINE_URL", "http://localhost:8080")

# C++ vertex layout: [x,y,z, r,g,b, size] (7 floats). The membrane buffer is (N,28) with
# position 0..2, color 16..18, size 20 (ParticleEngine.core.COL).
CPP_POS = (0, 1, 2)
CPP_RGB = (16, 17, 18)
CPP_SIZE = 20


def engine_available(timeout: float = 0.5) -> bool:
    try:
        with urllib.request.urlopen(f"{ENGINE_URL}/state", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _to_cpp7(buf: np.ndarray) -> list:
    buf = np.ascontiguousarray(buf, dtype=np.float32)
    n = buf.shape[0]
    pos = np.empty(n * 7, dtype=np.float32)
    pos[0::7] = buf[:, CPP_POS[0]]
    pos[1::7] = buf[:, CPP_POS[1]]
    pos[2::7] = buf[:, CPP_POS[2]]
    pos[3::7] = buf[:, CPP_RGB[0]]
    pos[4::7] = buf[:, CPP_RGB[1]]
    pos[5::7] = buf[:, CPP_RGB[2]]
    pos[6::7] = buf[:, CPP_SIZE]
    return pos.tolist()


def _spherical(cam_pos) -> tuple:
    """Convert a Cartesian eye position (aiming at origin) to the C++ engine's orbit
    (radius, theta, phi), matching the spherical decomposition used in engine.cpp frame()."""
    cx, cy, cz = cam_pos
    r = math.sqrt(cx * cx + cy * cy + cz * cz)
    if r <= 0:
        return 12.0, 0.0, 0.3
    phi = math.asin(max(-1.0, min(1.0, cy / r)))
    h = math.hypot(cx, cz)
    theta = math.atan2(cx, -cz) if h > 1e-6 else 0.0
    return r, theta, phi


def _post_membrane(term: str, pos7, count: int, cam_pos, timeout: float = 10.0) -> bool:
    """POST an already-7-float particle array (x,y,z,r,g,b,size) to the engine's /membrane."""
    r, theta, phi = _spherical(cam_pos)
    payload = json.dumps({
        "term": term,
        "count": count,
        "particles": pos7,
        "cam_radius": r,
        "cam_theta": theta,
        "cam_phi": phi,
    }).encode("utf-8")
    req = urllib.request.Request(f"{ENGINE_URL}/membrane", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status == 200


def load_membrane(term: str, buf: np.ndarray, cam_pos, timeout: float = 60.0) -> bool:
    """Upload a membrane's (N,28) buffer through the BINARY 14-float path.

    The legacy /membrane JSON route kills the engine process at ~64k particles
    (measured 2026-08-19: WinError 10054 mid-POST, process death, reproduced
    twice on story/theSeed's 64,309-grain buffer). /membrane_bin was built for
    exactly this ("no JSON for 100k+ splats"). The grain row expands to the
    14-float splat layout exactly as _shell_level_buf does: alpha=1, isotropic
    sigma=SIZE, identity rotation. `term` is only a label and is not sent."""
    buf = np.ascontiguousarray(buf, dtype=np.float32)
    n = int(buf.shape[0])
    buf14 = np.empty((n, 14), dtype=np.float32)
    buf14[:, 0] = buf[:, CPP_POS[0]]
    buf14[:, 1] = buf[:, CPP_POS[1]]
    buf14[:, 2] = buf[:, CPP_POS[2]]
    buf14[:, 3] = buf[:, CPP_RGB[0]]
    buf14[:, 4] = buf[:, CPP_RGB[1]]
    buf14[:, 5] = buf[:, CPP_RGB[2]]
    buf14[:, 6] = 1.0                    # alpha — opaque
    buf14[:, 7:10] = buf[:, CPP_SIZE:CPP_SIZE + 1]   # sigma (isotropic)
    buf14[:, 10] = 1.0                   # quat w
    buf14[:, 11:14] = 0.0                # quat x,y,z
    return _post_membrane_bin(n, cam_pos, buf14, timeout=timeout)


def _set_camera(radius: float, theta: float, phi: float, timeout: float = 10.0) -> bool:
    payload = json.dumps({"cam_radius": radius, "cam_theta": theta, "cam_phi": phi}).encode("utf-8")
    req = urllib.request.Request(f"{ENGINE_URL}/camera", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status == 200


def _shell_cache_path(shell_json, level: int) -> Path:
    return Path(str(shell_json)).with_name(Path(shell_json).stem + f"_l{level}.f32")


def _shell_level_buf(shell_json, level: int, size_scale: float):
    """Load one LOD level of the teddy shell as an (n,14) float32 splat buffer
    [x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz] — the engine's /membrane_bin format.

    Reads a binary cache (`<stem>_l<level>.f32`) when present, else parses the JSON ONCE and writes
    the cache. The cache is `[f32 cell][f32*n*6]` — positions in world units, colors 0..1 — so the
    size (cell * size_scale) stays tunable at render time without re-parsing the 40MB JSON.
    The 7-float shell row expands to 14 floats with alpha=1, isotropic sigma=size,
    identity rotation. Returns (buf14, cell).
    """
    import numpy as _np
    shell = Path(shell_json)
    cache = _shell_cache_path(shell_json, level)
    if cache.exists():
        raw = _np.fromfile(cache, dtype=_np.float32)
        cell = float(raw[0])
        pos_col = raw[1:].reshape(-1, 6)
    else:
        import json as _json
        lv = _json.loads(shell.read_text(encoding="utf-8"))["levels"][level]
        cell = lv["cell"]
        pos = _np.asarray(lv["pos"], dtype=_np.float32) * cell   # cell units -> world
        col = _np.asarray(lv["col"], dtype=_np.float32)
        pos_col = _np.hstack([pos, col])
        header = _np.array([cell], dtype=_np.float32)
        _np.concatenate([header, pos_col.ravel()]).astype(_np.float32).tofile(cache)
    n = pos_col.shape[0]
    size = cell * size_scale
    buf14 = _np.empty((n, 14), dtype=_np.float32)
    buf14[:, 0:6] = pos_col
    buf14[:, 6] = 1.0                    # alpha — opaque
    buf14[:, 7:10] = size                # sigma (isotropic)
    buf14[:, 10] = 1.0                   # quat w
    buf14[:, 11:14] = 0.0                # quat x,y,z
    return buf14, cell


def _post_membrane_bin(count: int, cam_pos, buf14, timeout: float = 60.0) -> bool:
    """POST the (n,14) splat buffer as raw float32 bytes to /membrane_bin (no JSON for 100k+
    splats). The engine validates the byte count (16 + count*14*4) and answers 200 with
    {"ok":false,"error":...} on mismatch — so check the BODY, not just the status."""
    import struct
    r, theta, phi = _spherical(cam_pos)
    header = struct.pack("<I3f", count, r, theta, phi)
    payload = header + buf14.astype(np.float32).tobytes()
    req = urllib.request.Request(f"{ENGINE_URL}/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            return False
        return b'"ok":true' in resp.read()


def fetch_frame(timeout: float = 10.0) -> bytes:
    with urllib.request.urlopen(f"{ENGINE_URL}/frame", timeout=timeout) as r:
        return r.read()


def render_term(term: str, out_dir) -> dict | None:
    """Render a term THROUGH the C++ engine -> {"begin": path, "end": path} PNGs, or None."""
    if not engine_available():
        return None
    import splat_appearance as sa
    bufs = sa.movie_buffers(term)
    if bufs is None:
        return None
    begin_buf, end_buf, cam_pos = bufs

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for label, buf in (("begin", begin_buf), ("end", end_buf)):
        if not load_membrane(term, buf, cam_pos):
            return None
        png = out / f"cpp_{term}_{label}.png"
        png.write_bytes(fetch_frame())
        paths[label] = str(png)
    return paths


def render_term_movie(term: str, out_dir, frames: int = 12, timeout: float = 60.0) -> list | None:
    """Render a membrane's WHOLE TIMELINE as an N-frame movie through the C++ engine
    -> ordered list of PNG paths, or None.

    WHY NOT [begin, end]: the dyad's blind eye was given exactly two frames and read
    them as "the scene stays the same" / "only one frame is provided" (measured
    2026-08-19 on theSeed — the front and back of the same teddy bear are legitimately
    similar, so a 2-frame 'movie' is illegible as change). A membrane's movie is its
    timeline; sampling `frames` instants across t=0..1 gives the eye an actual
    unfolding to watch. Story membranes only (design scenes have just two states and
    keep the 2-frame path).
    """
    if not engine_available():
        return None
    import splat_appearance as sa
    if term not in sa.membrane_terms():
        return None
    settled = sa.membrane_buffer(term, 1.0)
    if settled is None:
        return None
    extent = float(np.linalg.norm(settled[:, 0:3], axis=1).max()) or 1.0
    cam_pos = (0.0, -2.7 * extent, 0.72 * extent)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    ts = np.linspace(0.0, 1.0, int(frames))
    for i, t in enumerate(ts):
        buf = sa.membrane_buffer(term, float(t))
        if buf is None:
            return None
        if not load_membrane(term, buf, cam_pos, timeout=timeout):
            return None
        png = out / f"cpp_{term}_movie_{i:02d}.png"
        png.write_bytes(fetch_frame())
        # The eye is calibrated at 384px wide (senses.FRAME_TOKENS = 86 tokens/frame, measured);
        # full-res 1920x1080 frames are ~25x the pixels and ~8MB each -- a 12-frame payload kills
        # the watch POST (measured 2026-08-19: the dyad reported the eye DARK on a live server).
        from PIL import Image
        im = Image.open(png)
        w, h = im.size
        if w > 384:
            im = im.resize((384, round(h * 384 / w)), Image.LANCZOS)
        small = out / f"cpp_{term}_movie_{i:02d}_384.png"
        im.save(small)
        paths.append(str(small))
    return paths


def render_teddy(shell_json, out_dir, level: int = 1, size_scale: float = 1.5,
                 timeout: float = 90.0) -> dict | None:
    """Render the TEDDY bear's splat shell THROUGH the C++ Vulkan engine.

    The teddy is not a `story/` membrane (it has no physics.py emit()) — it is the SPIACE native
    body: a splat pyramid (`native/teddy_pyramid.py` -> `genomes/teddy_*_shell.json`) whose levels
    carry `pos` (cell units), `col` (0..1), `nor`. This converts one LOD level to the engine's
    7-float vertex layout (x,y,z,r,g,b,size), frames the camera from the body's extent, POSTs
    `/membrane`, and GETs `/frame`. Returns {"path": ...} or None.
    """
    if not engine_available():
        return None
    import numpy as _np

    buf7, cell = _shell_level_buf(shell_json, level, size_scale)
    extent = float(_np.linalg.norm(buf7[:, 0:3], axis=1).max()) or 1.0
    cam_pos = (0.0, -2.7 * extent, 0.72 * extent)

    if not _post_membrane_bin(int(len(buf7)), cam_pos, buf7, timeout=timeout):
        return None
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    png = out / f"cpp_teddy_l{level}.png"
    png.write_bytes(fetch_frame(timeout=timeout))
    return {"path": str(png)}


def render_teddy_movie(shell_json, out_dir, level: int = 1, frames: int = 72,
                       size_scale: float = 1.5, timeout: float = 30.0,
                       elevations=None) -> list | None:
    """Render a ROTATION MOVIE of the teddy through the C++ engine -> list of PNG paths.

    The dyad needs the MOVIE, not a still, and it needs MULTIPLE ELEVATIONS, not one flat orbit: a
    single horizontal turntable misses the top of the head (patchy scalp) and the soles (flat-slab
    feet). `elevations` is a list of camera elevation angles (phi: negative = looking up from
    below, 0 = level, positive = looking down from above). By default it sweeps below → level →
    above, splitting `frames` evenly across the elevations. Feed the returned paths to
    `senses.watch()`.
    """
    if not engine_available():
        return None
    import numpy as _np

    buf7, cell = _shell_level_buf(shell_json, level, size_scale)
    extent = float(_np.linalg.norm(buf7[:, 0:3], axis=1).max()) or 1.0
    cam_pos = (0.0, -2.7 * extent, 0.72 * extent)
    radius, _, base_phi = _spherical(cam_pos)
    if elevations is None:
        # below (look up at the soles), level (face/body), above (look down on the head)
        elevations = (base_phi, 0.0, -base_phi)

    if not _post_membrane_bin(int(len(buf7)), cam_pos, buf7, timeout=timeout):
        return None

    per_orbit = max(1, frames // len(elevations))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    idx = 0
    for phi in elevations:
        for i in range(per_orbit):
            theta = 2.0 * math.pi * i / per_orbit
            if not _set_camera(radius, theta, phi, timeout=timeout):
                return None
            png = out / f"teddy_f{idx:03d}.png"
            png.write_bytes(fetch_frame(timeout=timeout))
            paths.append(str(png))
            idx += 1
    return paths


def encode_movie(frames, out_mp4, fps: int = 24) -> str:
    """Encode an ordered list of PNG frames -> H.264 MP4 (the dyad's MOVIE). Requires ffmpeg.

    The dyad's eye watches a MOVIE, not a still — a single frame hides the defects that a rotating
    object reveals. `render_teddy_movie` produces the frames; this turns them into the movie file
    the operator/dyad consumes.
    """
    import shutil
    import subprocess
    import tempfile

    out = Path(out_mp4)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        for i, f in enumerate(frames):
            shutil.copy(f, Path(td) / f"f{i:04d}.png")
        cmd = ["ffmpeg", "-y", "-framerate", str(fps),
               "-i", str(Path(td) / "f%04d.png"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {r.stderr[-500:]}")
    return str(out)


# ── real 3DGS (TripoSplat) — photoreal Gaussian splats ──────────────────────────────

C0 = 0.28209479177387814  # SH DC -> RGB basis constant


def _quat_to_matrix(q):
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return np.stack([
        1 - 2*(y*y + z*z), 2*(x*y - w*z),     2*(x*z + w*y),
        2*(x*y + w*z),     1 - 2*(x*x + z*z), 2*(y*z - w*x),
        2*(x*z - w*y),     2*(y*z + w*x),     1 - 2*(x*x + y*y),
    ], axis=-1).reshape(-1, 3, 3)


def _matrix_to_quat(R):
    """Full Shepperd's method (all four trace branches — the tr<=0 branches are what the
    triposplat.py copy omitted, which produced NaN and wrecked the rotation remap)."""
    n = R.shape[0]
    q = np.zeros((n, 4), dtype=np.float64)
    for i in range(n):
        m00, m11, m22 = R[i, 0, 0], R[i, 1, 1], R[i, 2, 2]
        tr = m00 + m11 + m22
        if tr > 0:
            s = np.sqrt(tr + 1.0) * 2
            q[i] = [0.25*s, (R[i,2,1]-R[i,1,2])/s, (R[i,0,2]-R[i,2,0])/s, (R[i,1,0]-R[i,0,1])/s]
        elif m00 > m11 and m00 > m22:
            s = np.sqrt(1.0 + m00 - m11 - m22) * 2
            q[i] = [(R[i,2,1]-R[i,1,2])/s, 0.25*s, (R[i,0,1]+R[i,1,0])/s, (R[i,0,2]+R[i,2,0])/s]
        elif m11 > m22:
            s = np.sqrt(1.0 + m11 - m00 - m22) * 2
            q[i] = [(R[i,0,2]-R[i,2,0])/s, (R[i,0,1]+R[i,1,0])/s, 0.25*s, (R[i,1,2]+R[i,2,1])/s]
        else:
            s = np.sqrt(1.0 + m22 - m00 - m11) * 2
            q[i] = [(R[i,1,0]-R[i,0,1])/s, (R[i,0,2]+R[i,2,0])/s, (R[i,1,2]+R[i,2,1])/s, 0.25*s]
    return q


def load_3dgs(ply_path, opacity_gain: float = 1.6) -> np.ndarray:
    """Load a 3DGS PLY (TripoSplat output) -> (n,14) float32 [x,y,z,r,g,b,a,sx,sy,sz,qw,qx,qy,qz].

    Decodes the raw PLY (SH->RGB, sigmoid opacity, exp scale) and remaps the splats from the
    PLY's Z-up frame (TripoSplat's default transform) to the engine's Y-up frame, remapping the
    rotation quaternion through the same coordinate transform so the anisotropic shape stays
    aligned with the position. `opacity_gain` sharpens alpha toward opaque (the raw sigmoid mean
    is ~0.77, which reads as see-through; 1.6 closes the surface to solid).
    """
    shell = Path(ply_path)
    with open(shell, "rb") as f:
        while True:
            if f.readline().strip() == b"end_header":
                break
        off = f.tell()
    dt = np.dtype([("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("nx", "<f4"), ("ny", "<f4"), ("nz", "<f4"),
                   ("f0", "<f4"), ("f1", "<f4"), ("f2", "<f4"), ("opacity", "<f4"),
                   ("s0", "<f4"), ("s1", "<f4"), ("s2", "<f4"),
                   ("r0", "<f4"), ("r1", "<f4"), ("r2", "<f4"), ("r3", "<f4")])
    v = np.fromfile(open(shell, "rb"), dtype=dt, offset=off)
    rgb = np.clip(0.5 + C0 * np.stack([v["f0"], v["f1"], v["f2"]], axis=1), 0, 1).astype(np.float32)
    alpha = (1.0 / (1.0 + np.exp(-v["opacity"].astype(np.float64)))).astype(np.float32)
    alpha = np.clip(alpha * opacity_gain, 0, 1)
    scale = np.exp(np.stack([v["s0"], v["s1"], v["s2"]], axis=1)).astype(np.float32)
    rot = np.stack([v["r0"], v["r1"], v["r2"], v["r3"]], axis=1)
    rot = (rot / np.linalg.norm(rot, axis=1, keepdims=True)).astype(np.float64)
    ply_pos = np.stack([v["x"], v["y"], v["z"]], axis=1).astype(np.float32)

    # remap PLY (Z-up) -> engine (Y-up): T = [[1,0,0],[0,0,1],[0,-1,0]]
    T = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=np.float32)
    pos = (ply_pos @ T.T).astype(np.float32)
    R_eng = T @ _quat_to_matrix(rot).astype(np.float32)
    rot_eng = _matrix_to_quat(R_eng)
    rot_eng = (rot_eng / np.linalg.norm(rot_eng, axis=1, keepdims=True)).astype(np.float32)

    return np.hstack([pos, rgb, alpha[:, None], scale, rot_eng]).astype(np.float32)


def render_3dgs(ply_path, out_dir, opacity_gain: float = 1.6, timeout: float = 60.0) -> dict | None:
    """Render a real 3DGS PLY (TripoSplat) through the C++ engine -> {"path": PNG} or None."""
    if not engine_available():
        return None
    import struct as _struct
    buf14 = load_3dgs(ply_path, opacity_gain=opacity_gain)
    pos = buf14[:, 0:3]
    extent = float(np.linalg.norm(pos, axis=1).max()) or 1.0
    # farther camera: a close camera makes the near parts (sitting bear's feet/legs) balloon when
    # viewed from above. ~5x extent flattens the perspective.
    cam_pos = (0.0, -5.0 * extent, 1.3 * extent)
    # sort back-to-front by VIEW-DIRECTION depth (not Euclidean distance): the perspective
    # camera's correct sort key is the depth along the forward axis, else off-axis splats get
    # mis-ordered and the surface 'flips' at certain angles (the curtain artifact).
    eye = np.array(cam_pos, dtype=np.float32)
    forward = -eye / np.linalg.norm(eye)
    depth = (pos - eye) @ forward
    buf14 = buf14[np.argsort(-depth)]
    r, th, ph = _spherical(cam_pos)
    header = _struct.pack("<I3f", int(len(buf14)), r, th, ph)
    payload = header + buf14.tobytes()
    req = urllib.request.Request(f"{ENGINE_URL}/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            return None
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    png = out / f"cpp_3dgs_{Path(ply_path).stem}.png"
    png.write_bytes(fetch_frame(timeout=timeout))
    return {"path": str(png)}


def render_3dgs_movie(ply_path, out_dir, frames: int = 72, elevations=None,
                      opacity_gain: float = 1.6, timeout: float = 60.0) -> list | None:
    """Render a rotation MOVIE of a 3DGS PLY through the engine -> list of PNG paths.

    Re-sorts the splats back-to-front for EVERY camera angle (the depth order changes as the
    camera orbits, so a single pre-sort would produce the 'curtain flip' at some angle).
    `elevations` = camera elevation angles (phi): negative looks up from below, ~1.1 looks down on
    the top of the head. Feed the returned paths to `senses.watch()`.
    """
    if not engine_available():
        return None
    import struct as _struct
    buf = load_3dgs(ply_path, opacity_gain=opacity_gain)
    pos = buf[:, 0:3]
    extent = float(np.linalg.norm(pos, axis=1).max()) or 1.0
    radius = 5.0 * extent   # farther camera — flattens the perspective on the sitting bear
    if elevations is None:
        elevations = (-0.35, 0.0, 1.1)   # below, level, top-of-head

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    per = max(1, frames // len(elevations))
    paths = []
    idx = 0
    for phi in elevations:
        for i in range(per):
            theta = 2.0 * math.pi * i / per
            c, s = math.cos(phi), math.sin(phi)
            cx, sx = math.cos(theta), math.sin(theta)
            eye = np.array([radius * c * sx, radius * s, -radius * c * cx], dtype=np.float32)
            forward = -eye / np.linalg.norm(eye)      # toward the origin
            depth = (pos - eye) @ forward             # view-direction depth (correct sort key)
            b = buf[np.argsort(-depth)]               # back-to-front for THIS camera
            header = _struct.pack("<I3f", int(len(b)), radius, theta, phi)
            req = urllib.request.Request(f"{ENGINE_URL}/membrane_bin", data=header + b.tobytes(),
                                         headers={"Content-Type": "application/octet-stream"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    return None
            png = out / f"teddy3dgs_f{idx:03d}.png"
            png.write_bytes(fetch_frame(timeout=timeout))
            paths.append(str(png))
            idx += 1
    return paths


# ── TripoSplat .splat (the web viewer's native format — THIS is the teddy) ──────────────

# viewer.html re-orients DEG's -Y-up .splat output to Three.js +Y-up with
#   splat.rotation.y = PI/2; splatRoot.rotation.x = PI   =>  M = Rx(PI) @ Ry(PI/2)
SPLAT_ORIENT = np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]], dtype=np.float64)


def load_splat(splat_path) -> np.ndarray:
    """Load a TripoSplat `.splat` -> (n,14) float32 [x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz].

    `.splat` is the compact 32-byte/splat 3DGS format the web viewer consumes
    (`viewer.html?ply=teddy.splat`): [f32 xyz][f32 scale][u8 rgba][u8 rot]. The color bytes are
    ALREADY linear RGB (the SH DC term is baked in as `(f_dc*C0 + 0.5)*255`), alpha is the sigmoid
    opacity, and rot is a normalized [w,x,y,z] quaternion packed as `u8 = q*128 + 128`. This
    applies the same orientation transform as viewer.html so the C++ engine matches the viewer.
    """
    raw = np.fromfile(splat_path, dtype=np.uint8)
    n = len(raw) // 32
    rec = raw[: n * 32].reshape(n, 32)
    pos = rec[:, 0:12].view(np.float32).reshape(n, 3).astype(np.float64)
    scale = rec[:, 12:24].view(np.float32).reshape(n, 3).astype(np.float32)
    rgba = rec[:, 24:28].astype(np.float32)
    rot_u8 = rec[:, 28:32].astype(np.float32)

    rgb = rgba[:, 0:3] / 255.0
    alpha = rgba[:, 3:4] / 255.0
    rot = (rot_u8 - 128.0) / 128.0
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)

    world_pos = (pos @ SPLAT_ORIENT.T).astype(np.float32)
    R = _quat_to_matrix(rot)
    R_world = np.einsum("ij,njk->nik", SPLAT_ORIENT, R)
    rot_world = _matrix_to_quat(R_world).astype(np.float32)
    rot_world = rot_world / np.linalg.norm(rot_world, axis=1, keepdims=True)

    return np.concatenate([world_pos, rgb, alpha, scale, rot_world], axis=1).astype(np.float32)


def save_splat(splat_path, buf: np.ndarray) -> None:
    """Inverse of load_splat: (n,14) [x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz] (WORLD space,
    the space load_splat returns) -> 32-byte/splat .splat file. Applies the inverse of
    SPLAT_ORIENT so a load_splat(save_splat(x)) round-trip is the identity up to u8 packing."""
    import struct as _struct  # noqa: F401 (kept for symmetry with load_splat's readers)
    buf = np.asarray(buf, dtype=np.float64)
    n = len(buf)
    pos_raw = buf[:, 0:3] @ SPLAT_ORIENT                       # world = raw @ S.T  =>  raw = world @ S
    R_world = _quat_to_matrix(buf[:, 10:14])
    R_raw = np.einsum("ij,njk->nik", SPLAT_ORIENT.T, R_world)  # R_world = S R_raw => R_raw = S.T R_world
    rot_raw = _matrix_to_quat(R_raw)
    rot_raw = rot_raw / np.linalg.norm(rot_raw, axis=1, keepdims=True)

    dt = np.dtype([("pos", "<f4", 3), ("scale", "<f4", 3), ("rgba", "u1", 4), ("rot", "u1", 4)])
    arr = np.zeros(n, dtype=dt)
    arr["pos"] = pos_raw.astype(np.float32)
    arr["scale"] = buf[:, 7:10].astype(np.float32)
    arr["rgba"][:, 0:3] = (np.clip(buf[:, 3:6], 0, 1) * 255.0).round().astype(np.uint8)
    arr["rgba"][:, 3] = (np.clip(buf[:, 6], 0, 1) * 255.0).round().astype(np.uint8)
    arr["rot"] = (np.clip(rot_raw, -1, 1) * 128.0 + 128.0).round().astype(np.uint8)
    Path(splat_path).parent.mkdir(parents=True, exist_ok=True)
    Path(splat_path).write_bytes(arr.tobytes())


def render_splat(splat_path, out_dir, cam_pos=(0.0, 0.3, 1.8), timeout: float = 60.0) -> dict | None:
    """Render a TripoSplat `.splat` through the C++ engine -> {"path": PNG} or None.

    Uses the web viewer's camera `(0, 0.3, 1.8)` at 45 deg FOV (the engine already uses a 45 deg
    vertical FOV), so the engine frame matches `viewer.html?ply=<splat>`.
    """
    if not engine_available():
        return None
    import struct as _struct
    buf14 = load_splat(splat_path)
    r, th, ph = _spherical(cam_pos)
    header = _struct.pack("<I3f", int(len(buf14)), r, th, ph)
    payload = header + buf14.tobytes()
    req = urllib.request.Request(f"{ENGINE_URL}/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            return None
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    png = out / f"cpp_splat_{Path(splat_path).stem}.png"
    png.write_bytes(fetch_frame(timeout=timeout))
    return {"path": str(png)}


def render_splat_movie(splat_path, out_dir, frames: int = 36, elevations=None,
                       radius_mult: float = 5.0, timeout: float = 60.0) -> list | None:
    """Orbit MOVIE of a TripoSplat `.splat` through the C++ engine -> list of PNG paths.

    Same buffer as `render_splat` (load_splat's 14-float, viewer-oriented). The engine's GPU
    bitonic sort is authoritative (it re-sorts every frame as the camera orbits), so there is
    NO per-camera CPU pre-sort here — unlike the legacy `render_3dgs_movie`. `elevations`
    defaults to below → level → above (soles, body, top of head). Feed the paths to
    `senses.watch()` — the dyad judges the movie, not a still.
    """
    if not engine_available():
        return None
    import struct as _struct
    buf14 = load_splat(splat_path)
    pos = buf14[:, 0:3]
    extent = float(np.linalg.norm(pos, axis=1).max()) or 1.0
    radius = radius_mult * extent
    if elevations is None:
        elevations = (-0.35, 0.0, 1.1)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    per = max(1, frames // len(elevations))
    payload_buf = buf14.tobytes()
    paths = []
    idx = 0
    for phi in elevations:
        for i in range(per):
            theta = 2.0 * math.pi * i / per
            header = _struct.pack("<I3f", int(len(buf14)), radius, theta, phi)
            req = urllib.request.Request(f"{ENGINE_URL}/membrane_bin", data=header + payload_buf,
                                         headers={"Content-Type": "application/octet-stream"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200 or b'"ok":true' not in resp.read():
                    return None
            png = out / f"splat_f{idx:03d}.png"
            png.write_bytes(fetch_frame(timeout=timeout))
            paths.append(str(png))
            idx += 1
    return paths


# ── Triangle mesh rendering (the new /mesh_bin path) ────────────────────────────────

def _read_bear_mesh(bin_path):
    """Read the SPIACE bear mesh bin: int32 N, int32 M, then N*3 float32 vertices (LE),
    then M*3 uint32 triangle indices (LE). Return (verts_np, tris_np)."""
    with open(bin_path, "rb") as f:
        N, M = struct.unpack("<ii", f.read(8))
        verts = np.fromfile(f, dtype=np.float32, count=int(N) * 3).reshape(int(N), 3)
        tris = np.fromfile(f, dtype=np.uint32, count=int(M) * 3).reshape(int(M), 3)
    return verts, tris


def _mesh_normals(verts: np.ndarray, tris: np.ndarray) -> np.ndarray:
    """Area-weighted per-vertex normals (accumulate each triangle's cross product)."""
    v0, v1, v2 = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)            # (M,3) — unnormalized face normal
    n = np.zeros_like(verts)
    np.add.at(n, tris[:, 0], fn)
    np.add.at(n, tris[:, 1], fn)
    np.add.at(n, tris[:, 2], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    return n / ln


def load_mesh_bin(bin_path, cam_pos=None, timeout: float = 60.0):
    """POST a mesh through the new /mesh_bin endpoint.

    Reads the bear mesh, computes area-weighted normals, interleaves [pos3, normal3, color3]
    (teddy brown), frames the camera from the body's extent, and POSTs the binary protocol
    `[u32 N][u32 idxCount][f32 r][f32 theta][f32 phi][f32 * N*9 verts][u32 * idxCount tris]`.
    Returns (ok, r, theta, phi)."""
    if not engine_available():
        return (False, 12.0, 0.0, 0.3)
    verts, tris = _read_bear_mesh(bin_path)
    verts = np.ascontiguousarray(verts, dtype=np.float32)
    tris = np.ascontiguousarray(tris, dtype=np.uint32)
    n = int(verts.shape[0])
    m = int(tris.shape[0])
    normals = _mesh_normals(verts, tris)
    color = np.full((n, 3), (0.8, 0.55, 0.35), dtype=np.float32)
    verts9 = np.hstack([verts, normals, color]).astype(np.float32)

    extent = float(np.linalg.norm(verts, axis=1).max()) or 1.0
    if cam_pos is None:
        cam_pos = (0.0, -2.7 * extent, 0.72 * extent)
    r, theta, phi = _spherical(cam_pos)

    # C++ /mesh_bin expects a 24-byte header: [u32 N][u32 idxCount][f32 r][f32 theta][f32 phi]
    # plus one trailing f32 (read as part of the 24-byte prefix). `idxCount` is the TOTAL number
    # of uint32 indices (= M*3), not the triangle count — the endpoint reads `idxCount` uint32s.
    header = struct.pack("<II4f", n, int(tris.size), r, theta, phi, 0.0)
    payload = header + verts9.tobytes() + tris.astype(np.uint32).tobytes()
    req = urllib.request.Request(f"{ENGINE_URL}/mesh_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return (False, r, theta, phi)
            ok = b'"ok":true' in resp.read()
            return (ok, r, theta, phi)
    except Exception:
        return (False, r, theta, phi)


def render_mesh_movie(bin_path, out_dir, frames: int = 36, elevations=(0.3, 0.0, -0.3),
                      timeout: float = 30.0) -> list | None:
    """Render a ROTATION MOVIE of a triangle mesh through the C++ engine -> list of PNG paths.

    Mirrors render_teddy_movie: load once with /mesh_bin, then orbit the camera over
    `elevations` (phi) and `frames` total angles, capturing a frame at each stop. Feed the
    returned paths to `senses.watch()` so the dyad can judge the mesh as real geometry."""
    if not engine_available():
        return None
    verts, _ = _read_bear_mesh(bin_path)
    extent = float(np.linalg.norm(verts, axis=1).max()) or 1.0
    cam_pos = (0.0, -2.7 * extent, 0.72 * extent)

    ok, radius, _, _ = load_mesh_bin(bin_path, cam_pos, timeout=timeout)
    if not ok:
        return None

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    per = max(1, frames // len(elevations))
    paths = []
    idx = 0
    for phi in elevations:
        for i in range(per):
            theta = 2.0 * math.pi * i / per
            if not _set_camera(radius, theta, phi, timeout=timeout):
                return None
            png = out / f"mesh_f{idx:03d}.png"
            png.write_bytes(fetch_frame(timeout=timeout))
            paths.append(str(png))
            idx += 1
    return paths
