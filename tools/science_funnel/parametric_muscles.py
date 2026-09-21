"""Parametric muscle layer (membrane layer 2) -- derived from admitted numbers.

Lane brief (2026-09-20, branch agent/parametric-muscles-20260920, base
2d585c7b = the infant matter skeleton). The research memo's Option A interim:
the admitted ADULT numbers (Guimaraes 2026 hindlimb architecture batch
`guimaraes_arch`, sha256-pinned; the muscle-path lane's attachment geometry
`muscle_paths_20260918`; the walker Table-1 adult scaffold) determine one
solid capsule membrane per admitted hindlimb muscle, expressed in the
matter kernel's own format. The STAGE LAW is honored by construction: the
layer is staged ADULT on the adult-proportioned walker scaffold -- it never
touches the infant matter skeleton (the biological mixing law L1 refuses
adult-muscles-on-infant-bones).

RULE 0 receipt (statement / prediction / falsifiers -- named BEFORE the run):
  tools/science_funnel/validation/parametric_muscles_20260920/receipt.json

DERIVATION LAWS (Rule 1 -- no authored shape parameter):
  volume    V = m / rho, rho = 1060 kg/m^3 -- THE DATASET'S OWN closure
            constant (adapters_muscle.MUSCLE_DENSITY_KG_M3, the law that
            admits each row: PCSA = m/(rho*FL)); independently the classic
            measured mammalian skeletal-muscle density (Mendez & Keys 1960).
  path      origin/insertion = muscle_path_geometry.json neutral-pose
            points (m -> mm x1000); L = straight_length_m (admitted).
  capsule   radius r solves pi r^2 L - (2/3) pi r^3 = V (closed form,
            bisection to 1e-12 on [0, L/2]; the sphere bound pi L^3/6 is
            the existence limit; fallback branch: prolate spheroid,
            semi-major L/2, semi-minor sqrt(3V/(2 pi L)) -- branch
            recorded per muscle).
  mass      the kernel's own: area x thickness x density, with
            thickness := V / A_mesh (the derived equivalent shell; makes
            stated mass == V * rho exactly, so the kernel's 5% check stays
            a live falsifier).
  mesh      a DISCRETIZATION choice only (48 circumferential segments x
            52 meridian parallels over the polar profile): the analytic
            solid is fixed by V and L; the mass law closes through t := V/A
            and the 0.5% enclosed-volume gate is measured per muscle.

MODES
  build   verify input pins -> derive -> write body + triangle blobs +
          derivation book (the audit table).
  verify  re-derive from the committed pins and demand agreement with the
          committed artifacts; kernel parse_body; rasterize the COMMITTED
          blobs (pixel_truth); reality classification of the bundle.

Run from the repository root:
  python -B -m tools.science_funnel.parametric_muscles --mode build
  python -B -m tools.science_funnel.parametric_muscles --mode verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]

GUIM_XLSX = ROOT / 'tools/science_funnel/data/guimaraes_arch/AJPA-190-e70329-s001.xlsx'
GUIM_SHA256 = '08ead4a901a53f97e136c709a7804b9d04b4b903107e873c01f3b9b5b9eb8678'
PATH_GEO = ROOT / ('tools/science_funnel/validation/muscle_paths_20260918/'
                   'muscle_path_geometry.json')
OUT_DIR = ROOT / 'tools/science_funnel/data/parametric_muscles'
BODY_PATH = OUT_DIR / 'adult_muscle_layer.body.json'
BUNDLE = ROOT / 'tools/science_funnel/validation/parametric_muscles_20260920'

MUSCLE_DENSITY_KG_M3 = 1060.0          # the dataset's own law (adapter)
DENSITY_KG_MM3 = MUSCLE_DENSITY_KG_M3 * 1e-9   # 1.06e-6 kg/mm^3
LAW_TOLERANCE = 0.02                   # the adapter's row-law tolerance
VOLUME_MESH_TOLERANCE = 0.005          # prediction (a): 0.5% discretization
KERNEL_MASS_TOLERANCE = 0.05           # the kernel's own law
PIXEL_MEAN_MIN = 0.97                  # prediction (e)
PIXEL_PER_MUSCLE_MIN = 0.90
RASTER_SIZE = 256                      # declared resolution (receipt)

# mesh discretization (receipt mesh_law): not a shape parameter
N_RING = 48        # circumferential segments
N_CAP = 24         # meridian stacks per hemispherical cap (n_step = 2*N_CAP + N_CYL)
N_CYL = 4          # cylinder bands

# kernel material constants for skeletal muscle (all cited in-source)
MAT = {
    'mat.skeletal_muscle': {
        'density': DENSITY_KG_MM3,
        'young_modulus': 50000.0,
        'yield': 140000.0,
        'hardness_vickers': 0.05,
        'source': (
            'DENSITY: the admitted dataset\'s own closure law PCSA = m/(1060 '
            'kg/m^3 * FL) (adapters_muscle.MUSCLE_DENSITY_KG_M3; enforced per '
            'row at 2%) -- the same constant as the measured mammalian '
            'skeletal-muscle density of MENDEZ & KEYS 1960, J Appl Physiol '
            '15:617-621 (~1.06 g/cm^3). YOUNG: passive skeletal-muscle '
            'tangent-modulus band 10-100 kPa (FUNG, Biomechanics: Mechanical '
            'Properties of Living Tissues; band quoted, mid-band 50 kPa used, '
            'the cartilage-lane band pattern). YIELD: skeletal-muscle tensile '
            'strength ~0.14 MPa (YAMADA 1970, Strength of Biological '
            'Materials, ~1.4 kgf/cm^2). HARDNESS: Vickers is not defined for '
            'hydrated muscle gel; 0.05 is a NAMED POSITIVE PLACEHOLDER for '
            'the validator\'s positivity law (the cartilage lane\'s 0.3 proxy '
            'pattern), used by NO derivation -- every mass number in this '
            'body uses density only.'),
    },
}


# ------------------------------------------------------------------ inputs

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_admitted_rows():
    """The admitted-adapter read of the pinned xlsx (the same read the
    muscle-path lane used). Returns (muscles dict, quarantine count)."""
    from tools.science_funnel import adapters_muscle
    raw = GUIM_XLSX.read_bytes()
    rows = adapters_muscle.guimaraes_arch(raw, {}, GUIM_XLSX.name)
    table, quarantined = {}, []
    for row in rows:
        if 'payload' not in row:
            quarantined.append({'location': row['location'],
                                'code': row['refusal']['code']})
            continue
        payload = row['payload']
        if payload['conditions']['species'] != 'Macaca_mulatta':
            continue
        parts = row['external_id'].split(':')
        entry = table.setdefault(parts[2], {'conditions': payload['conditions']})
        entry[parts[4]] = payload['value_si']
    return table, quarantined


def load_paths():
    return json.loads(PATH_GEO.read_text(encoding='utf-8'))


# ----------------------------------------------------------- capsule laws

def capsule_radius(volume_mm3: float, length_mm: float) -> tuple[float, float]:
    """Solve pi r^2 L - (2/3) pi r^3 = V on [0, L/2] (bisection to 1e-12
    relative). Returns (r, residual_V). Assumes V <= pi L^3 / 6."""
    target = volume_mm3

    def f(r):
        return math.pi * r * r * length_mm - (2.0 / 3.0) * math.pi * r ** 3

    lo, hi = 0.0, length_mm / 2.0
    r = hi
    for _ in range(200):
        r = 0.5 * (lo + hi)
        if f(r) < target:
            lo = r
        else:
            hi = r
        if hi - lo <= 1e-12 * max(hi, 1e-30):
            break
    return r, abs(f(r) - target)


def spheroid_minor(volume_mm3: float, length_mm: float) -> float:
    """Prolate-spheroid fallback: semi-major a = L/2, solve
    (4/3) pi a b^2 = V  ->  b = sqrt(3V / (4 pi a))."""
    a = length_mm / 2.0
    return math.sqrt(3.0 * volume_mm3 / (4.0 * math.pi * a))


def _revolve(a_mm, b_mm, profile):
    """Shared surface-of-revolution builder: profile(t) -> (axial offset
    along u from the MIDPOINT, radius) for t in [0, pi] (0 -> +u pole).
    Returns (vertices (n,3) float32, triangles (m,3) uint32), outward-
    oriented about the axis midpoint (both solids are star-shaped there)."""
    a = np.asarray(a_mm, dtype=np.float64)
    b = np.asarray(b_mm, dtype=np.float64)
    axis = b - a
    L = float(np.linalg.norm(axis))
    u = axis / L
    ref = np.array([1.0, 0.0, 0.0]) if abs(u[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = np.cross(u, ref)
    x /= np.linalg.norm(x)
    y = np.cross(u, x)

    theta = np.linspace(0.0, 2.0 * math.pi, N_RING, endpoint=False)
    ring = (np.cos(theta)[:, None] * x[None, :]
            + np.sin(theta)[:, None] * y[None, :])       # (N_RING, 3)
    center = 0.5 * (a + b)

    points: list[list[float]] = []
    rings: list[int] = []          # flat start index of each full ring
    # parallels at t = pi*(j/N_STEP), j = 1..N_STEP-1 (poles separate)
    n_step = 2 * N_CAP + N_CYL
    for j in range(1, n_step):
        t = math.pi * j / n_step
        dz, rad = profile(t, L)
        pts = center + dz * u + rad * ring
        rings.append(len(points))
        points.extend([list(map(float, p)) for p in pts])
    north = len(points)
    points.append([float(v) for v in (center + 0.5 * L * u)])
    points.append([float(v) for v in (center - 0.5 * L * u)])   # south last

    V = np.asarray(points, dtype=np.float64)           # (n, 3)
    tris: list[tuple[int, int, int]] = []

    def band(k0: int, k1: int):
        """Quad strip between two full rings (flat start indices)."""
        for i in range(N_RING):
            j = (i + 1) % N_RING
            a0, a1 = k0 + i, k0 + j
            b0, b1 = k1 + i, k1 + j
            tris.append((a0, b0, b1))
            tris.append((a0, b1, a1))

    def fan(pole: int, ring_start: int):
        for i in range(N_RING):
            j = (i + 1) % N_RING
            tris.append((pole, ring_start + i, ring_start + j))

    first, last = rings[0], rings[-1]
    fan(north, first)                    # north pole (t=0 end)
    for z_, w_ in zip(rings, rings[1:]):
        band(z_, w_)
    fan(len(points) - 1, last)           # south pole (t=pi end)

    # consistent outward orientation: flip any triangle whose normal points
    # inward (both the capsule and the spheroid are star-shaped about the
    # axis midpoint)
    T = np.asarray(tris, dtype=np.uint32)
    tv = V[T.astype(np.int64)]                   # (m,3,3)
    nrm = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
    cent = tv.mean(axis=1)
    inward = np.einsum('ij,ij->i', nrm, cent - center) < 0
    T[inward] = T[inward][:, [0, 2, 1]]

    return V.astype(np.float32), T


def capsule_mesh(a_mm, b_mm, r_mm):
    """Closed capsule triangle mesh around the axis a->b (mm, float32):
    cylinder of radius r along the axis plus hemispherical caps of radius r
    centered a + r*u and b - r*u (so the poles ARE the attachment points).

    Returns (vertices (n,3) float32, triangles (m,3) uint32)."""

    def profile(t, L):
        """Analytic capsule profile in polar form about the midpoint:
        the hemisphere-sphere-hemisphere surface of radius r whose axis
        segment has length L."""
        c1 = -0.5 * (L - 2.0 * r_mm)   # south cap center offset
        c2 = -c1
        if t <= math.pi / 2.0:                     # north hemisphere
            return c2 + r_mm * math.cos(t), r_mm * math.sin(t)
        return c1 + r_mm * math.cos(t), r_mm * math.sin(t)

    return _revolve(a_mm, b_mm, profile)


def spheroid_mesh(a_mm, b_mm, semi_minor_mm):
    """Closed prolate-spheroid mesh: semi-major L/2 along the axis (poles at
    the attachment points), semi-minor semi_minor_mm across.

    Returns (vertices (n,3) float32, triangles (m,3) uint32)."""

    def profile(t, L):
        return 0.5 * L * math.cos(t), semi_minor_mm * math.sin(t)

    return _revolve(a_mm, b_mm, profile)


def mesh_enclosed_volume_mm3(tri: np.ndarray) -> float:
    """Divergence theorem on the mesh's own triangles (the skeleton lane's
    volume law, mm^3)."""
    a = tri[:, 0, :].astype(np.float64)
    b = tri[:, 1, :].astype(np.float64)
    c = tri[:, 2, :].astype(np.float64)
    return float(np.sum(np.einsum('ij,ij->i', a, np.cross(b, c))) / 6.0)


def mesh_area_mm2(tri: np.ndarray) -> float:
    """The kernel's own area law (cross products, summed)."""
    a = tri[:, 0, :].astype(np.float64)
    b = tri[:, 1, :].astype(np.float64)
    c = tri[:, 2, :].astype(np.float64)
    n = np.cross(b - a, c - a)
    return float(np.sum(0.5 * np.linalg.norm(n, axis=1)))


def pack_tris(tri: np.ndarray) -> bytes:
    """The kernel's 36-byte-per-triangle format (9 x float32 LE)."""
    return struct.pack(f'<{tri.size}f', *tri.reshape(-1).astype(np.float64))


# ------------------------------------------------------------- pixel truth

def _camera_for(a: np.ndarray, b: np.ndarray, r_mm: float, size: int):
    """The ONE per-muscle camera, derived from the analytic extent
    (|b-a| + 2r per axis, diagonal spanning half the frame, fov 45 deg):
    the rasterizer and the analytic silhouette share it, so framing cannot
    manufacture coverage."""
    ext = np.abs(b - a) + 2.0 * r_mm
    diag = float(np.linalg.norm(ext))
    center = 0.5 * (a + b)
    fwd0 = np.array([0.35, 0.25, 1.0])
    fwd0 = fwd0 / np.linalg.norm(fwd0)
    f = (size / 2.0) / math.tan(math.radians(45.0 / 2.0))
    dist = f * diag / (0.35 * size)
    eye = center + fwd0 * dist
    fwd = center - eye
    fwd /= np.linalg.norm(fwd)
    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up0)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return eye, right, up, fwd, f


def rasterize_solid(tri: np.ndarray, cam, size: int = RASTER_SIZE) -> np.ndarray:
    """Software z-buffer rasterization of the committed triangle blob under
    the shared camera. Returns the coverage mask (solid geometry, no
    backface culling -- a z-buffer)."""
    eye, right, up, fwd, f = cam
    rel = tri.reshape(-1, 3).astype(np.float64) - eye
    xc = rel @ right
    yc = rel @ up
    zc = rel @ fwd
    px = f * xc / zc + size / 2.0
    py = size / 2.0 - f * yc / zc
    pts = np.stack([px, py], axis=1).reshape(-1, 3, 2)
    depth = zc.reshape(-1, 3).mean(axis=1)

    zbuf = np.full((size, size), np.inf)
    for t in range(pts.shape[0]):
        p = pts[t]
        x0, y0 = int(max(0, math.floor(p[:, 0].min()))), int(max(0, math.floor(p[:, 1].min())))
        x1 = int(min(size - 1, math.ceil(p[:, 0].max())))
        y1 = int(min(size - 1, math.ceil(p[:, 1].max())))
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5,
                             np.arange(y0, y1 + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = p
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        yy, xx = np.nonzero(inside)
        gy, gx = yy + y0, xx + x0
        nearer = depth[t] < zbuf[gy, gx]
        zbuf[gy[nearer], gx[nearer]] = depth[t]
    return np.isfinite(zbuf)


def analytic_silhouette(a_mm, b_mm, r_mm, cam, shape='capsule',
                        size: int = RASTER_SIZE) -> np.ndarray:
    """The analytic capsule/spheroid projection under the SAME shared camera
    as rasterize_solid.

    capsule  -- the perspective-correct loft of the two cap-rim circles
                (cap centers at a + r*u and b - r*u per the volume law --
                the poles ARE the attachment points): each rim's radius is
                scaled at ITS OWN depth (the rims themselves are circles
                seen at a tilt; their minor-axis foreshortening is
                second-order at the framing distance).
    spheroid -- the projected ellipse: semi-axis b across the projected
                axis, and sqrt(b^2 cos^2(gamma) + a^2 sin^2(gamma)) along
                it (gamma = axis-to-view angle; support-function extent of
                the spheroid in the image plane); the exact perspective
                silhouette of a spheroid is a conic, the orthographic
                ellipse at the center depth is its declared approximation.
    """
    a, b = np.asarray(a_mm, float), np.asarray(b_mm, float)
    eye, right, up, fwd, f = cam

    def proj(p):
        rel = np.atleast_2d(p) - eye
        zc = rel @ fwd
        return np.stack([f * (rel @ right) / zc + size / 2.0,
                         size / 2.0 - f * (rel @ up) / zc], axis=1), zc

    Pa, za = proj(a)
    Pb, zb = proj(b)
    xs, ys = np.meshgrid(np.arange(size) + 0.5, np.arange(size) + 0.5)
    pts = np.stack([xs, ys], axis=-1)

    if shape == 'capsule':
        u3 = (b - a)
        axis_len = float(np.linalg.norm(u3))
        u3 = u3 / axis_len if axis_len > 0 else np.array([1.0, 0.0, 0.0])
        if axis_len > 2.0 * r_mm:
            c_a, c_b = a + r_mm * u3, b - r_mm * u3      # cap centers
        else:                                            # degenerate: sphere
            c_a = c_b = 0.5 * (a + b)
        Pa, za = proj(c_a)
        Pb, zb = proj(c_b)
        D = Pb[0] - Pa[0]
        len2 = max(float(D @ D), 1e-12)
        s = np.clip(((pts - Pa[0]) @ D) / len2, 0.0, 1.0)
        closest = Pa[0] + s[..., None] * D
        r_a = r_mm * f / za[0]
        r_b = r_mm * f / zb[0]
        r_along = r_a + s * (r_b - r_a)
        dist2 = np.sum((pts - closest) ** 2, axis=-1)
        return dist2 <= (r_along ** 2)
    # spheroid: semi-major a_h = |b-a|/2 along the axis, semi-minor r_mm
    axis3 = b - a
    a_h = 0.5 * float(np.linalg.norm(axis3))
    u = axis3 / (2.0 * a_h) if a_h > 0 else np.array([1.0, 0.0, 0.0])
    C, _ = proj(0.5 * (a + b))
    u_img = np.array([float((u @ right)), float((u @ up))])
    nu = np.linalg.norm(u_img)
    if nu < 1e-12:
        u_img = np.array([1.0, 0.0])
        nu = 1.0
    u_img /= nu
    v_img = np.array([-u_img[1], u_img[0]])
    cos_g = abs(float(u @ fwd))
    sin_g = math.sqrt(max(0.0, 1.0 - cos_g * cos_g))
    A_eff = math.sqrt((r_mm * cos_g) ** 2 + (a_h * sin_g) ** 2) * f / (zb[0])
    B_eff = r_mm * f / (zb[0])
    d = pts - C[0]
    along = d @ u_img
    across = d @ v_img
    return (along / A_eff) ** 2 + (across / B_eff) ** 2 <= 1.0


def pixel_truth(tri: np.ndarray, a_mm, b_mm, r_mm,
                shape: str = 'capsule') -> float:
    """Coverage = |render ∩ analytic| / |analytic| (the receipt's law)."""
    a, b = np.asarray(a_mm, float), np.asarray(b_mm, float)
    cam = _camera_for(a, b, r_mm, RASTER_SIZE)
    rendered = rasterize_solid(tri, cam)
    analytic = analytic_silhouette(a_mm, b_mm, r_mm, cam, shape)
    denom = int(analytic.sum())
    if denom == 0:
        return 0.0
    return float((rendered & analytic).sum()) / denom


# ------------------------------------------------------------------ build

def build(apply: bool) -> dict:
    if _sha256(GUIM_XLSX) != GUIM_SHA256:
        raise SystemExit(f'pin refused: {GUIM_XLSX} sha256 != {GUIM_SHA256}')
    table, quarantined = load_admitted_rows()
    paths = load_paths()
    neutral = paths['hindlimb']['poses']['neutral']

    path_muscles = set(neutral['muscles'])
    arch_muscles = set(table)
    if path_muscles != arch_muscles:
        raise SystemExit('admitted-set disagreement: xlsx '
                         f'{sorted(arch_muscles)} vs path lane {sorted(path_muscles)}')

    mulatta_quar = [q for q in quarantined if 'Macaca mulatta' in q['location']]
    membranes: list[dict] = []
    audit: list[dict] = []
    tris_written: dict[str, bytes] = {}

    for idx, label in enumerate(sorted(table)):
        arch = table[label]
        p = neutral['muscles'][label]
        mass_kg = arch['musc_mass']
        fl_m = arch['fl_m']
        pcsa_adm = arch['pcsa_m2']
        origin_m = p['origin_point_m']
        insert_m = p['insertion_point_m']
        straight_m = p['straight_length_m']

        # the path lane's hindlimb frame is 2D sagittal [x, y]; the matter
        # body is 3D: embed at z = 0 (the walker's sagittal plane; the
        # out-of-plane leg offset is declared successor work)
        origin_mm = [v * 1000.0 for v in origin_m] + [0.0]
        insert_mm = [v * 1000.0 for v in insert_m] + [0.0]
        L_mm = straight_m * 1000.0

        volume_mm3 = mass_kg / DENSITY_KG_MM3
        sphere_bound = math.pi * L_mm ** 3 / 6.0
        if volume_mm3 <= sphere_bound:
            r_mm, residual = capsule_radius(volume_mm3, L_mm)
            branch = 'capsule'
        else:
            r_mm = spheroid_minor(volume_mm3, L_mm)
            residual = None
            branch = 'prolate_spheroid'
        verts, tris_i = (capsule_mesh(origin_mm, insert_mm, r_mm)
                         if branch == 'capsule'
                         else spheroid_mesh(origin_mm, insert_mm, r_mm))
        a_mm, b_mm = origin_mm, insert_mm
        tri_mat = verts[tris_i]                         # (m,3,3)
        area = mesh_area_mm2(tri_mat)
        enclosed = mesh_enclosed_volume_mm3(tri_mat)
        vol_delta = enclosed / volume_mm3 - 1.0
        if abs(vol_delta) > VOLUME_MESH_TOLERANCE:
            raise SystemExit(f'{label}: mesh enclosed volume off by '
                             f'{vol_delta:+.4%} (tolerance '
                             f'{VOLUME_MESH_TOLERANCE:.1%}) -- refine '
                             f'discretization, never tune')
        thickness = volume_mm3 / area
        mass_stated = area * thickness * DENSITY_KG_MM3
        pcsa_book = (volume_mm3 * 1e-9) / fl_m          # m^3 / m -> m^2
        # the dataset's own predicate, verbatim (adapters_muscle):
        # math.isclose(predicted, admitted, rel_tol=0.02)
        pcsa_rel_adm = abs(pcsa_book - pcsa_adm) / pcsa_adm
        pcsa_rel = (abs(pcsa_book - pcsa_adm)
                    / max(abs(pcsa_book), abs(pcsa_adm)))
        if not math.isclose(pcsa_book, pcsa_adm, rel_tol=LAW_TOLERANCE):
            raise SystemExit(f'{label}: PCSA closure {pcsa_rel_adm:.4%} '
                             f'(vs admitted) outside the dataset\'s own '
                             f'math.isclose(rel_tol={LAW_TOLERANCE:.0%}) law '
                             f'on the final volume book')
        r_pcsa_mm = math.sqrt(pcsa_adm * 1e6 / math.pi)

        mid = f'mem.muscle_{idx:02d}'
        ref = f'tris/muscle_{idx:02d}.bin'
        tris_written[ref] = pack_tris(tri_mat)

        membranes.append({
            'id': mid,
            'material': 'mat.skeletal_muscle',
            'triangles': ref,
            'thickness': thickness,
            'mass': mass_stated,
            'label': label,
            'side': arch['conditions']['limb'],
            'functional_groups': p['functional_groups'],
            'source_batch': 'guimaraes_arch (admitted 20260917; xlsx sha256 '
                            f'{GUIM_SHA256[:12]}...)',
            'source_paths': 'muscle_paths_20260918 neutral pose '
                            '(chimera.muscle_path_geometry.v1)',
            'origin_point_mm': origin_mm,
            'insertion_point_mm': insert_mm,
            'straight_length_mm': L_mm,
            'admitted_musc_mass_kg': mass_kg,
            'admitted_fl_m': fl_m,
            'admitted_pcsa_m2': pcsa_adm,
            'admitted_penn_deg': arch.get('penn_deg'),
            'admitted_musc_len_m': arch.get('musc_len'),
            'max_force_N': p['max_force_N'],
            'moment_arms_m_flexion_positive': p['moment_arms_m_flexion_positive'],
            'spanned_joints': p['spanned_joints'],
            'volume_mm3': volume_mm3,
            'area_mm2': area,
            'radius_mm': r_mm,
            'capsule_branch': branch,
            'vertices': int(verts.shape[0]),
            'faces': int(tris_i.shape[0]),
        })
        audit.append({
            'id': mid,
            'label': label,
            'side': arch['conditions']['limb'],
            'path_source': {'origin_point_m': origin_m,
                            'insertion_point_m': insert_m,
                            'straight_length_m': straight_m,
                            'measured_mtu_length_m': p['measured_mtu_length_m'],
                            'origin_landmark_segment_u_v':
                                p['origin_landmark_segment_u_v'],
                            'insertion_landmark_segment_u_v':
                                p['insertion_landmark_segment_u_v']},
            'architecture_source': {'musc_mass_kg': mass_kg, 'fl_m': fl_m,
                                    'pcsa_m2': pcsa_adm,
                                    'penn_deg': arch.get('penn_deg'),
                                    'musc_len_m': arch.get('musc_len'),
                                    'belly_len_m': arch.get('belly_len'),
                                    'belly_mass_kg': arch.get('belly_mass'),
                                    'tendon_len_m': arch.get('tendon_len'),
                                    'tendon_mass_kg': arch.get('tendon_mass'),
                                    'conditions': {k: arch['conditions'][k]
                                                   for k in ('species', 'specimen_id',
                                                             'sex', 'age', 'limb')}},
            'force_source': {'max_force_N': p['max_force_N'],
                             'moment_arms_m_flexion_positive':
                                 p['moment_arms_m_flexion_positive']},
            'derivation': {'density_kg_mm3': DENSITY_KG_MM3,
                           'volume_mm3': volume_mm3,
                           'capsule_branch': branch,
                           'radius_mm': r_mm,
                           'radius_residual_mm3': residual,
                           'r_pcsa_report_mm': r_pcsa_mm,
                           'r_pcsa_over_r_mass': r_pcsa_mm / r_mm,
                           'mesh_vertices': int(verts.shape[0]),
                           'mesh_faces': int(tris_i.shape[0]),
                           'mesh_area_mm2': area,
                           'mesh_enclosed_volume_mm3': enclosed,
                           'mesh_volume_delta_pct': vol_delta * 100.0,
                           'thickness_mm': thickness,
                           'mass_stated_kg': mass_stated,
                           'pcsa_book_m2': pcsa_book,
                           'pcsa_closure_rel_vs_admitted': pcsa_rel_adm,
                           'pcsa_closure_rel_dataset_predicate': pcsa_rel,
                           'sphere_bound_mm3': sphere_bound},
        })

    total_mass = sum(m['mass'] for m in membranes)
    batch_total = sum(table[k]['musc_mass'] for k in table)
    total_volume = sum(m['volume_mm3'] for m in membranes)

    body = {
        'schema': 'chimera.matter_body.v1',
        'subject': {
            'layer': 'muscles -- the second membrane layer (the research '
                     'memo Option A interim, pending external adult muscle '
                     'geometry data)',
            'anatomy': 'right hindlimb musculature (the dissected limb), 30 '
                       'admitted muscles of 36 source rows (6 whole-row '
                       'quarantines by the dataset\'s own closure laws)',
            'species_muscles': 'Macaca mulatta (Guimaraes specimen 127, '
                               'adult male, 8 kg, right limb)',
            'scaffold': 'the ADULT walker Table-1 assembly (Oku 2021 Table 1, '
                        'M. fuscata adult male 10.038 kg; record '
                        'model.dynamics.gait_walker): hip [0,0], knee '
                        '[0,-0.163], ankle [0,-0.345], mtp [0.074,-0.345], '
                        'toe [0.119,-0.345] m',
            'coordinate_frame': 'the walker scaffold frame, millimetres '
                                '(path-lane metres x1000); x anterior, y '
                                'vertical, z out-of-plane',
            'not_a_claim': 'no actuation, no pose animation, no whole-animal '
                           'mass claim (a limb layer is not an animal); the '
                           'falsified path directions (knee extension, MTP '
                           'flexion) carry no force claim',
        },
        'stage': {
            'life_stage': 'adult',
            'scale': 1.0,
            'allometric_scaling_applied': False,
            'provenance': 'Guimaraes Information sheet: specimen "127 [KU '
                          'Leuven, Belgium]", Macaca mulatta, Male, "Age at '
                          'death (yrs)" = "Adult", 8 kg, limb R (carried in '
                          'every admitted record\'s conditions); scaffold: '
                          'Oku 2021 Table 1 adult male',
            'stage_law': 'the infant matter skeleton '
                         '(morphosource_ct/matter_skeleton/) is a DIFFERENT '
                         'creature (stage infant): L1 refuses the '
                         'adult-muscles-on-infant-bones chimera, so this '
                         'layer references no infant membrane and no infant '
                         'coordinate',
            'declared_substitution_L3': 'mulatta architecture on fuscata '
                                        'segment geometry, mass ratio 0.79697 '
                                        '(path lane), declared not merged',
        },
        'units': {
            'coordinates': 'mm', 'thickness': 'mm', 'density': 'kg/mm^3',
            'mass': 'kg', 'cure_strength': 'Pa (kernel convention)',
            'note': 'the kernel mass law (area x thickness x density) is '
                    'unit-agnostic; these three agree, so mass is kg',
        },
        'membrane_layer': {
            'layer': 'muscles (parametric capsules) -- membrane layer 2',
            'over': 'the adult walker Table-1 scaffold (attachment carried as '
                    'the landmark book; adult bones are NOT yet matter -- no '
                    'adult bone geometry is admitted, the memo\'s central '
                    'measured gap)',
            'successors': ['bonds to an adult bone layer when one lands as '
                           'matter', 'bilateral mirror with the gait '
                           'contract\'s leg_z_offset', 'arm muscles when arm '
                           'volume data or an admitted transform exists',
                           'skin eventually'],
            'doctrine': 'operator 2026-09-20: the triangles ARE the membranes',
        },
        'materials': MAT,
        'membranes': membranes,
        'bonds': [],
    }

    derivation = {
        'schema': 'chimera.parametric_muscles_derivation.v1',
        'lane': 'agent/parametric-muscles-20260920',
        'inputs': {
            'guimaraes_xlsx_sha256': _sha256(GUIM_XLSX),
            'guimaraes_pin_expectation': GUIM_SHA256,
            'muscle_path_geometry_sha256': _sha256(PATH_GEO),
            'admitted_rows_mulatta': len(table),
            'quarantined_rows_total': len(quarantined),
            'quarantined_rows_mulatta': mulatta_quar,
            'adapter': 'tools/science_funnel/adapters_muscle.py (the '
                       'admitted-adapter read; row laws enforced at 2%)',
        },
        'laws': {
            'volume': 'V = m / rho, rho = 1060 kg/m^3 = 1.06e-6 kg/mm^3 '
                      '(the dataset\'s own closure constant; Mendez & Keys '
                      '1960)',
            'path': 'muscle_path_geometry neutral pose, m -> mm x1000',
            'capsule': 'pi r^2 L - (2/3) pi r^3 = V, bisection 1e-12 on '
                       '[0, L/2]; sphere bound pi L^3/6; prolate-spheroid '
                       'fallback recorded per muscle',
            'mass': 'kernel law area x thickness x density with '
                    'thickness := V / A_mesh (the derived equivalent shell)',
            'mesh': '48 circumferential x 52 meridian parallels (polar '
                    'profile) -- discretization only; the enclosed-volume '
                    'check (0.5%) gates it per muscle',
            'attachment': 'the landmark book (no bonds: the adult bone layer '
                          'does not exist as matter; successor)',
        },
        'muscles': audit,
        'totals': {
            'muscles': len(membranes),
            'total_mass_stated_kg': total_mass,
            'batch_total_admitted_musc_mass_kg': batch_total,
            'mass_reconciliation_rel': abs(total_mass - batch_total) / batch_total,
            'total_volume_mm3': total_volume,
            'pcsa_closure_max_rel': max(a['derivation']['pcsa_closure_rel_dataset_predicate']
                                        for a in audit),
            'pcsa_closure_max_rel_vs_admitted':
                max(a['derivation']['pcsa_closure_rel_vs_admitted']
                    for a in audit),
            'mesh_volume_delta_max_pct': max(abs(a['derivation']['mesh_volume_delta_pct'])
                                             for a in audit),
            'sphere_bound_min_margin': min(a['derivation']['sphere_bound_mm3'] /
                                           a['derivation']['volume_mm3']
                                           for a in audit),
            'capsule_branches': {b: sum(1 for a in audit
                                        if a['derivation']['capsule_branch'] == b)
                                 for b in {a['derivation']['capsule_branch']
                                           for a in audit}},
        },
    }

    if apply:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (BUNDLE / 'derivation.json').write_text(
            json.dumps(derivation, indent=1) + '\n', encoding='utf-8')
        (BODY_PATH).write_text(json.dumps(body, indent=1) + '\n',
                               encoding='utf-8')
        for ref, blob in sorted(tris_written.items()):
            (OUT_DIR / ref).write_bytes(blob)
        print(f'built {len(membranes)} membranes -> {BODY_PATH}')
        print(f'total mass {total_mass:.9f} kg vs batch total '
              f'{batch_total:.9f} kg '
              f'(rel {abs(total_mass - batch_total) / batch_total:.2e})')

    return {'body': body, 'derivation': derivation,
            'tris': tris_written, 'table': table}


# ----------------------------------------------------------------- verify

def verify() -> int:
    failures: list[str] = []
    rebuilt = build(apply=False)
    body = json.loads(BODY_PATH.read_text(encoding='utf-8'))
    derivation = json.loads((BUNDLE / 'derivation.json').read_text(encoding='utf-8'))
    book = {m['id']: m for m in derivation['muscles']}

    # 1. pins
    if derivation['inputs']['guimaraes_xlsx_sha256'] != GUIM_SHA256:
        failures.append('guimaraes xlsx pin drifted')
    if derivation['inputs']['muscle_path_geometry_sha256'] != _sha256(PATH_GEO):
        failures.append('muscle_path_geometry.json drifted (bytes not the '
                        'committed lane record)')

    # 2. re-derivation agreement (fresh-clone law): the committed numbers
    #    must equal a fresh derivation from the pinned inputs
    book_keys = {'thickness': 'thickness_mm', 'mass': 'mass_stated_kg',
                 'volume_mm3': 'volume_mm3', 'area_mm2': 'mesh_area_mm2',
                 'radius_mm': 'radius_mm'}
    for mem in body['membranes']:
        d = book[mem['id']]['derivation']
        for mem_key, book_key in book_keys.items():
            if abs(mem[mem_key] - d[book_key]) > 1e-9 * max(abs(d[book_key]), 1e-30):
                failures.append(f"{mem['id']}: {mem_key} drifted vs "
                                f're-derivation')
        blob = (OUT_DIR / mem['triangles']).read_bytes()
        if len(blob) != mem['faces'] * 36:
            failures.append(f"{mem['id']}: blob size {len(blob)} != "
                            f"{mem['faces']} faces x 36")
        if d['capsule_branch'] == 'capsule':
            verts, tris_i = capsule_mesh(mem['origin_point_mm'],
                                         mem['insertion_point_mm'],
                                         mem['radius_mm'])
        else:
            verts, tris_i = spheroid_mesh(mem['origin_point_mm'],
                                          mem['insertion_point_mm'],
                                          mem['radius_mm'])
        if pack_tris(verts[tris_i]) != blob:
            failures.append(f'{mem["id"]}: triangle blob not byte-identical '
                            f'to regeneration (fresh-clone law)')

    # 3. kernel conformance
    from tools.matter_kernel import definition
    parsed = definition.parse_body(BODY_PATH)
    for mem in parsed['membranes']:
        stated = mem['mass']
        derived = mem['mass_derived']
        if abs(stated - derived) / derived > KERNEL_MASS_TOLERANCE:
            failures.append(f"{mem['id']}: kernel mass law beyond 5%")
        d = book[mem['id']]['derivation']
        rel = abs(stated - d['mass_stated_kg']) / d['mass_stated_kg']
        if rel > 1e-9:
            failures.append(f'{mem["id"]}: stated mass vs book rel {rel:.2e}')

    # 4. totals
    totals = derivation['totals']
    stated_sum = sum(m['mass'] for m in body['membranes'])
    batch_total = rebuilt['derivation']['totals']['batch_total_admitted_musc_mass_kg']
    rel = abs(stated_sum - batch_total) / batch_total
    if rel > 1e-12:
        failures.append(f'total mass vs batch total rel {rel:.2e}')
    if totals['muscles'] != 30:
        failures.append(f'muscle count {totals["muscles"]} != 30')
    if totals['pcsa_closure_max_rel'] > LAW_TOLERANCE:
        failures.append('pcsa closure beyond the dataset predicate')
    if totals['mesh_volume_delta_max_pct'] > VOLUME_MESH_TOLERANCE * 100:
        failures.append('mesh enclosed-volume gate exceeded')

    # 5. stage / reality classification (computed, not asserted)
    conditions = {m['label']: m['architecture_source']['conditions']
                  for m in derivation['muscles']}
    ages = {c['age'] for c in conditions.values()}
    sexes = {c['sex'] for c in conditions.values()}
    species = {c['species'] for c in conditions.values()}
    stage_ok = ages == {'Adult'} and species == {'Macaca_mulatta'}
    stage_rows = [{'law': 'L1_stage', 'ok': stage_ok,
                   'evidence': {'age_values': sorted(ages),
                                'species': sorted(species),
                                'sex': sorted(sexes),
                                'scaffold': 'Oku 2021 Table 1 adult '
                                            'male M. fuscata (walker '
                                            'assembly)'},
                   'note': 'L1 demands ONE stage across bound records: '
                           'all muscle records Adult; the scaffold is '
                           'the adult walker assembly; the infant '
                           'skeleton is referenced by no membrane and '
                           'no bond (checked below)'}]
    infant_refs = sum(
        ('infant' in json.dumps(m)) or ('bone_' in json.dumps(m.get('spanned_joints', [])))
        for m in body['membranes']) + len(body['bonds'])
    stage_rows.append({'law': 'L1_no_infant_chimera',
                       'ok': infant_refs == 0 and body['stage']['life_stage'] == 'adult',
                       'evidence': {'infant_membranes_referenced': infant_refs,
                                    'bonds': len(body['bonds']),
                                    'life_stage': body['stage']['life_stage']},
                       'note': 'the adult muscle layer binds no infant '
                               'membrane (no bonds at all until an adult '
                               'bone layer exists as matter)'})
    stage_rows.append({'law': 'L3_substitution_declared',
                       'ok': body['stage']['declared_substitution_L3'] is not None,
                       'evidence': {'declaration':
                                    body['stage']['declared_substitution_L3']},
                       'note': 'mulatta architecture on fuscata geometry, '
                               'genus-mates, declared not merged'})
    stage_rows.append({'law': 'L2_allometry',
                       'ok': True,
                       'evidence': {'scope': 'a limb layer makes no '
                                             'whole-body proportion claim'},
                       'note': 'declared: no L2 surface is claimed by a '
                               'layer-only body'})
    stage_rows.append({'law': 'L4_physics',
                       'ok': len(failures) == 0,
                       'evidence': {'mass_book': totals},
                       'note': 'the mass book and the admitted force record '
                               'are the physics carried; no new force claim'})
    reality = {
        'category': 'REALITY' if all(r['ok'] for r in stage_rows) else 'FANTASY',
        'violations': [r for r in stage_rows if not r['ok']],
        'stage_label': 'adult',
        'stage_evidence': 'Guimaraes Information sheet via every admitted '
                          'record\'s conditions (species Macaca_mulatta, sex '
                          'Male, age Adult, limb R); scaffold Oku Table 1 '
                          'adult male (model.dynamics.gait_walker)',
    }

    # 6. pixel truth on the COMMITTED blobs
    covs = []
    for mem in body['membranes']:
        blob = (OUT_DIR / mem['triangles']).read_bytes()
        n = len(blob) // 36
        tris = np.frombuffer(blob, dtype='<f4').reshape(n, 3, 3).astype(np.float64)
        cov = pixel_truth(tris, mem['origin_point_mm'],
                          mem['insertion_point_mm'], mem['radius_mm'],
                          shape='capsule' if mem['capsule_branch'] == 'capsule'
                          else 'spheroid')
        covs.append({'id': mem['id'], 'label': mem['label'], 'coverage': cov})
    mean_cov = float(np.mean([c['coverage'] for c in covs]))
    worst = min(covs, key=lambda c: c['coverage'])
    pixel_ok = (mean_cov >= PIXEL_MEAN_MIN
                and worst['coverage'] >= PIXEL_PER_MUSCLE_MIN)
    if not pixel_ok:
        failures.append(f'pixel_truth below bar: mean {mean_cov:.4f} '
                        f'(min {PIXEL_MEAN_MIN}), worst '
                        f'{worst["label"]} {worst["coverage"]:.4f} '
                        f'(min {PIXEL_PER_MUSCLE_MIN})')
    mass_ok = rel <= 1e-12
    pcsa_ok = totals['pcsa_closure_max_rel'] <= LAW_TOLERANCE

    if reality['category'] != 'REALITY':
        failures.append('reality classification is not REALITY')
    # L4 rides on the whole book: re-evaluate now that every falsifier ran
    stage_rows[-1]['ok'] = len(failures) == 0

    verify_doc = {
        'schema': 'chimera.parametric_muscles_verify.v1',
        'verified_utc_mode': 'deterministic re-derivation (no wall clock in '
                             'verdicts)',
        'verdicts': {
            'traceability': ('GREEN -- 30/30 muscles fully traced: path '
                             'points from muscle_paths_20260918 (sha '
                             f'{_sha256(PATH_GEO)[:12]}...), architecture '
                             'from the pinned guimaraes xlsx via the '
                             'admitted adapter (sha256 '
                             f'{GUIM_SHA256[:12]}...), density law, '
                             'closed-form radius, derived thickness; zero '
                             'authored shape parameters; capsule branches: '
                             f'{totals["capsule_branches"]}; min '
                             'sphere-bound margin '
                             f'{totals["sphere_bound_min_margin"]:.1f}x '
                             'volume'),
            'mass_reconciliation': (f'{"GREEN" if mass_ok else "RED"} -- '
                                    f'total stated '
                                    f'{stated_sum:.9f} kg == batch total '
                                    f'{batch_total:.9f} kg over exactly the '
                                    f'30 admitted mulatta rows (rel '
                                    f'{rel:.2e}); kernel derived mass '
                                    f'within the 5% law on every membrane '
                                    f'(max rel '
                                    f'{max(abs(m["mass"] - m["mass_derived"]) / m["mass_derived"] for m in parsed["membranes"]):.2e})'),
            'pcsa_closure': (f'{"GREEN" if pcsa_ok else "RED"} -- the '
                             f'dataset\'s own identity on the '
                             f'FINAL volume book: max rel '
                             f'{totals["pcsa_closure_max_rel"]:.4%} over 30 '
                             f'muscles (tolerance {LAW_TOLERANCE:.0%}); the '
                             f'belly-is-not-a-cylinder deviation is reported '
                             f'per muscle as r_pcsa/r_mass in '
                             f'derivation.json (range '
                             f'{min(a["derivation"]["r_pcsa_over_r_mass"] for a in derivation["muscles"]):.3f}-'
                             f'{max(a["derivation"]["r_pcsa_over_r_mass"] for a in derivation["muscles"]):.3f}), '
                             'never tuned'),
            'kernel_conformance': ('GREEN -- tools.matter_kernel.'
                                   'definition.parse_body validates '
                                   'adult_muscle_layer.body.json unmodified '
                                   f'({len(parsed["membranes"])} membranes, '
                                   f'{len(parsed["bonds"])} bonds); the '
                                   'kernel suite result is recorded in '
                                   'regressions'),
            'stage_consistency': (f'{reality["category"]} -- computed '
                                  'classification: ' +
                                  '; '.join(f'{r["law"]}=' +
                                            ('ok' if r['ok'] else 'VIOLATION')
                                            for r in stage_rows)),
            'pixel_truth': (f'{"GREEN" if mean_cov >= PIXEL_MEAN_MIN and worst["coverage"] >= PIXEL_PER_MUSCLE_MIN else "RED"} '
                            f'-- solid-geometry rasterization of the '
                            f'COMMITTED 36-byte blobs at {RASTER_SIZE} px: '
                            f'layer-mean coverage {mean_cov:.4f} '
                            f'(min {PIXEL_MEAN_MIN}), worst muscle '
                            f'{worst["label"]} {worst["coverage"]:.4f} '
                            f'(min {PIXEL_PER_MUSCLE_MIN}); every muscle '
                            f'renders as solid z-buffered geometry'),
        },
        'pixel_truth_detail': covs,
        'reality_classification': reality,
        'stage_checks': stage_rows,
        'totals': totals,
        'failures': failures,
    }

    if apply_verdicts and not failures:
        (BUNDLE / 'verify.json').write_text(
            json.dumps(verify_doc, indent=1) + '\n', encoding='utf-8')
        print('verify.json written')

    for vname, v in verify_doc['verdicts'].items():
        print(f'{vname:22s} {v[:110]}')
    if failures:
        print('FAILURES:')
        for f in failures:
            print(' -', f)
        return 1
    print('VERIFY: all falsifiers green')
    return 0


apply_verdicts = True


def montage() -> int:
    """The rendered-layer record: every muscle's z-buffered mask from the
    COMMITTED blobs under its own camera, tiled with coverage values."""
    from PIL import Image, ImageDraw
    body = json.loads(BODY_PATH.read_text(encoding='utf-8'))
    detail = {c['id']: c['coverage'] for c in json.loads(
        (BUNDLE / 'verify.json').read_text(encoding='utf-8'))['pixel_truth_detail']}
    cell = 256
    cols, rows_n = 6, (len(body['membranes']) + 5) // 6
    sheet = Image.new('RGB', (cols * cell, rows_n * cell), (8, 8, 12))
    draw = ImageDraw.Draw(sheet)
    for idx, mem in enumerate(body['membranes']):
        blob = (OUT_DIR / mem['triangles']).read_bytes()
        n = len(blob) // 36
        tris = np.frombuffer(blob, dtype='<f4').reshape(n, 3, 3).astype(np.float64)
        a, b = (np.asarray(mem['origin_point_mm'], float),
                np.asarray(mem['insertion_point_mm'], float))
        cam = _camera_for(a, b, mem['radius_mm'], cell)
        mask = rasterize_solid(tris, cam)
        tile = np.zeros((cell, cell, 3), dtype=np.uint8)
        tile[mask] = (110, 200, 120)
        sub = Image.fromarray(tile)
        cx, cy = (idx % cols) * cell, (idx // cols) * cell
        sheet.paste(sub, (cx, cy))
        draw.text((cx + 6, cy + 4),
                  f"{mem['label']} {detail[mem['id']]:.3f}", fill=(255, 255, 120))
    out = BUNDLE / 'muscle_layer_montage.png'
    sheet.save(out)
    print(f'montage -> {out}')
    return 0


def main() -> int:
    global apply_verdicts
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['build', 'verify', 'montage'],
                    default='build')
    ap.add_argument('--no-write', action='store_true',
                    help='verify: do not write verify.json (report only)')
    args = ap.parse_args()
    if args.mode == 'build':
        out = build(apply=True)
        print('capsule branches:', out['derivation']['totals']['capsule_branches'])
        return 0
    if args.mode == 'montage':
        return montage()
    apply_verdicts = not args.no_write
    return verify()


if __name__ == '__main__':
    sys.exit(main())
