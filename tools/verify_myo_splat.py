"""verify_myo_splat.py -- VERIFY that MyoSuite's myobody renders through OUR Gaussian-splat
pipeline (ParticleEngine), not just through MuJoCo's own renderer.

The operator's rule: third-party models must be PROVEN against the rendering system we
generated, never assumed. So this renders the SAME rest pose twice -- MuJoCo's own renderer
(the reference) and our FullGPUPipeline (the system under test) -- side by side.

Mesh -> splat: every visual geom (STL mesh or primitive) is sampled into grains with surface
normals, transformed to world space at the model's rest pose, and uploaded as a standard
(N,28) particle buffer -- the same format every membrane's emit() produces.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
MYO = REPO / "external" / "myo_sim"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "ChimeraEngine"))

NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA, SIZE = 16, 17, 18, 19, 20
NX, NY, NZ = 21, 22, 23


def load_stl(path: Path):
    """Minimal binary-STL reader -> (vertices (m,3), faces (k,3))."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        raise ValueError(f"ASCII STL not supported here: {path.name}")
    n = struct.unpack_from("<I", data, 80)[0]
    tris = np.frombuffer(data, dtype=np.dtype([
        ("n", "<f4", (3,)), ("v", "<f4", (9,)), ("attr", "<u2")]), offset=84, count=n)
    v = tris["v"].reshape(n, 3, 3)
    faces = np.arange(3 * n).reshape(n, 3)
    return v.reshape(-1, 3), faces


def sample_mesh(verts, faces, world_mat, world_pos, scale, budget, rng, mesh_pos=None, mesh_quat=None):
    """Area-weighted uniform samples on the mesh surface, transformed to world space.
    mesh_pos/mesh_quat: the mesh frame's offset inside the geom frame (MuJoCo mesh convention)."""
    v = verts.astype(np.float64) * scale
    if mesh_quat is not None:
        import mujoco
        mrot = np.zeros(9)
        mujoco.mju_quat2Mat(mrot, mesh_quat)
        v = v @ mrot.reshape(3, 3).T
    if mesh_pos is not None:
        v = v + mesh_pos[None, :]
    tri = v[faces]                                  # (k,3,3)
    a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2.0
    total = a.sum()
    if total <= 0:
        return None
    p = a / total
    idx = rng.choice(len(faces), size=budget, p=p)
    t = tri[idx]
    u, w = rng.random(budget), rng.random(budget)
    su = np.sqrt(u)
    pts = t[:, 0] * (1 - su)[:, None] + t[:, 1] * (su * (1 - w))[:, None] + t[:, 2] * (su * w)[:, None]
    nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
    pts = pts @ world_mat.T + world_pos
    nrm = nrm @ world_mat.T
    return pts.astype(np.float32), nrm.astype(np.float32)


def _mesh_assets(model, xml_path: Path):
    """name -> (file, scale) from the model's own asset declarations -- the single source of truth
    for which STL a mesh geom draws and at what scale."""
    import xml.etree.ElementTree as ET
    root = ET.parse(xml_path).getroot()
    assets = {}
    for mel in root.iter("mesh"):
        name = mel.get("name")
        f = mel.get("file") or mel.get("fileName")
        sc = mel.get("scale")
        scale = float(sc.split()[0]) if sc else 1.0
        if name and f:
            assets[name] = (MYO / "meshes" / f, scale)
    return assets


def build_body_buffer(model, data, xml_path, total_grains=90000, seed=5):
    """Sample every visual geom of the model into one (N,28) splat buffer, using the COMPILED
    mesh data (vertices/faces live in the model after load -- no file lookup, no scale bugs)."""
    import mujoco
    rng = np.random.default_rng(seed)
    entries = []
    full_body_root = None
    for i in range(model.nbody):
        if model.body(i).name == "Full Body":
            full_body_root = i
    keep_body = set()
    def _walk(bid):
        keep_body.add(bid)
        for cid in range(model.nbody):
            if model.body_parentid[cid] == bid:
                _walk(cid)
    if full_body_root is not None:
        _walk(full_body_root)
    for gi in range(model.ngeom):
        gtype = model.geom_type[gi]
        if gtype == mujoco.mjtGeom.mjGEOM_PLANE:
            continue
        if keep_body and model.geom_bodyid[gi] not in keep_body:
            continue                                      # the room is not the body
        pos = data.geom_xpos[gi].copy()
        mat = data.geom_xmat[gi].reshape(3, 3).copy()
        mid = model.geom_dataid[gi] if gtype == mujoco.mjtGeom.mjGEOM_MESH else -1
        size = model.geom_size[gi].copy()
        entries.append((gtype, mid, pos, mat, size))

    weights = np.ones(len(entries)) / len(entries)
    out = []
    for ei, (gtype, mid, pos, mat, size) in enumerate(entries):
        budget = max(300, int(total_grains * weights[ei]))
        if mid >= 0:
            va, vn = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
            fa, fn = model.mesh_faceadr[mid], model.mesh_facenum[mid]
            verts = model.mesh_vert[va:va + vn].reshape(vn, 3)   # already in the GEOM frame --
            faces = model.mesh_face[fa:fa + fn].reshape(fn, 3)   # measured: refpos double-transforms
            got = sample_mesh(verts, faces, mat, pos, 1.0, budget, rng)
        else:
            got = sample_primitive(gtype, size, mat, pos, budget, rng)
        if got is None:
            continue
        pts, nrm = got
        b = np.zeros((len(pts), NCOLS), np.float32)
        b[:, PX:PZ + 1] = pts
        b[:, NX:NZ + 1] = nrm
        b[:, TYPE] = 3.0
        b[:, ALPHA] = 0.9
        out.append(b)
    buf = np.concatenate(out, axis=0)
    # MEASURED-LOOK PALETTE, matching the reference's own convention: bone white, muscle red,
    # joint grey -- the classes are the geom TYPES, not taste.
    bone = np.array([0.85, 0.83, 0.78], np.float32)
    muscle = np.array([0.55, 0.12, 0.10], np.float32)
    joint = np.array([0.45, 0.30, 0.26], np.float32)
    import mujoco as _mj
    kinds = []
    for gi in range(model.ngeom):
        gt = model.geom_type[gi]
        if gt == _mj.mjtGeom.mjGEOM_PLANE:
            continue
        if keep_body and model.geom_bodyid[gi] not in keep_body:
            continue
        kinds.append(gt)
    counts = [len(o) for o in out]
    colmap = {7: bone, 5: muscle, 3: muscle, 2: joint, 4: joint}
    cols = np.concatenate([np.tile(colmap.get(k, bone), (c, 1)) for k, c in zip(kinds, counts)], axis=0)
    # MEASURED LIGHT: the form is only legible if the light rakes it. The grains carry their own
    # surface normals, so light them the membranes' way: albedo x irradiance, one sun + ambient,
    # plus the Fresnel sheen every dielectric (skin included) shows at grazing angles.
    import sys as _sys
    _sys.path.insert(0, str(REPO / "story"))
    from matter import lit as _lit
    sun = np.array([0.55, -0.62, 0.56], np.float32)
    sun = sun / np.linalg.norm(sun)
    cosang = np.clip((buf[:, NX:NZ + 1] * sun[None, :]).sum(1), 0.0, None)
    buf[:, CR:CB + 1] = _lit(cols, 1.0 * cosang + 0.06, e_ref=1.0, tone=0.45)
    buf[:, SIZE] = 0.006
    return buf


def sample_primitive(gtype, size, mat, pos, budget, rng):
    """Uniform-ish samples on sphere/capsule/cylinder/ellipsoid primitives."""
    import mujoco
    if gtype == mujoco.mjtGeom.mjGEOM_SPHERE:
        r = size[0]
        d = _fib(budget)
        pts = d * r
        nrm = d.copy()
    elif gtype == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
        d = _fib(budget)
        pts = d * size[None, :]
        nrm = d.copy()
    elif gtype in (mujoco.mjtGeom.mjGEOM_CAPSULE, mujoco.mjtGeom.mjGEOM_CYLINDER):
        r, hh = size[0], size[1]
        z = rng.uniform(-hh, hh, budget)
        th = rng.uniform(0, 2 * np.pi, budget)
        pts = np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)
        nrm = np.stack([np.cos(th), np.sin(th), np.zeros(budget)], axis=1)
    else:
        return None
    return (pts @ mat.T + pos).astype(np.float32), (nrm @ mat.T).astype(np.float32)


def _fib(n):
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    th = np.pi * (1.0 + 5.0 ** 0.5) * i
    return np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)


def main() -> int:
    import mujoco
    from PIL import Image
    xml = sys.argv[1] if len(sys.argv) > 1 else str(MYO / "body" / "myobody.xml")
    m = mujoco.MjModel.from_xml_path(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)

    out_dir = REPO / "ChimeraEngine" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # REFERENCE: MuJoCo's own renderer, front three-quarter view
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.azimuth, cam.elevation = 2.6, 115.0, -6.0
    cam.lookat = np.array([0.0, 0.0, 0.95])
    ref = mujoco.Renderer(m, height=480, width=640)
    ref.update_scene(d, cam)
    ref_path = out_dir / "myobody_mujoco_ref.png"
    Image.fromarray(ref.render()).save(ref_path)
    print(f"reference (MuJoCo renderer): {ref_path}")

    # UNDER TEST: our splat pipeline
    buf = build_body_buffer(m, d, Path(xml))
    print(f"splat grains: {len(buf)}")
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    campos = (1.7, -1.9, 1.05)
    target = np.array([0.0, 0.0, 0.95])
    dvec = target - np.array(campos)
    yaw = float(np.arctan2(dvec[1], dvec[0]))          # yaw=0 looks +X; aim along dvec
    pitch = float(np.arctan2(dvec[2], float(np.hypot(dvec[0], dvec[1]))))
    cam2 = FirstPersonCamera(campos, yaw=yaw, pitch=pitch)
    p = cam2.params(720, 540)
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    pipe.upload(buf)
    ours_path = out_dir / "myobody_splat_ours.png"
    Image.fromarray(pipe.render_from_gpu(cam2, p)).save(ours_path)
    print(f"under test (our splat pipeline): {ours_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
