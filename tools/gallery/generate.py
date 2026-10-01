"""generate.py -- five varied CLOSED OBJ creatures, math only (agent G4).

THE CLAIM UNDER TEST (the bring-alive law): POST /mesh_import converts any
closed OBJ. So the gallery's job is to make "any" work hard: five bodies
that differ in genus, curvature profile and corner structure —

  blob      ellipsoid, semi-axes 2:1:1 (tall)          genus 0, smooth
  torus     major R=1.5, minor r=0.5, standing wheel   genus 1 (a HOLE)
  capsule   cylinder r=0.5 half-len 0.75 + hemispheres genus 0, C1 seams
  peanut    two-lobe surface of revolution             genus 0, waist
  rbox      superquadric rounded cube (eps 0.3)        genus 0, corners

Each mesh is verified WATERTIGHT IN PYTHON before it may be posted:
  1. edge-pair check: every directed edge appears exactly once and its
     reversed twin exactly once (closed 2-manifold, consistent winding);
  2. divergence volume: V = (1/6) SUM dot(v0, v1 x v2) over triangles,
     positive (outward) and above the engine's own epsilon rule
     (|V| > bbox_volume * 1e-6).
The check runs on the PARSED TEXT of the written OBJ — the same bytes the
engine's importer will read — not on the in-memory floats.

Usage:  python tools/gallery/generate.py [--out tools/gallery/obj]
Writes <name>.obj for each creature and prints the proof table.
"""
from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

import numpy as np

TWOPI = 2.0 * math.pi


# ── builders ────────────────────────────────────────────────────────────
def revolve(profile, ys: np.ndarray, nu: int):
    """Surface of revolution about the y axis (the engine's spine axis).

    profile[j] is the radius at height ys[j]; a row whose radius is exactly
    0 becomes ONE apex vertex (a pole), never a degenerate ring. Returns
    (verts (n,3) f64, faces (m,3) i64) with OUTWARD winding (asserted by
    the verifier, flipped here if the raw winding comes out inward).
    """
    ys = np.asarray(ys, dtype=np.float64)
    prof = np.asarray(profile, dtype=np.float64)
    assert ys.shape == prof.shape and ys.size >= 3

    verts: list[tuple[float, float, float]] = []
    rings: list[list[int]] = []
    ang = TWOPI * np.arange(nu) / nu
    ca, sa = np.cos(ang), np.sin(ang)
    for y, r in zip(ys, prof):
        if r == 0.0:
            rings.append([len(verts)] * nu)
            verts.append((0.0, float(y), 0.0))
        else:
            base = len(verts)
            for i in range(nu):
                verts.append((float(r) * ca[i], float(y), float(r) * sa[i]))
            rings.append(list(range(base, base + nu)))

    faces: list[tuple[int, int, int]] = []
    for j in range(len(rings) - 1):
        lo, hi = rings[j], rings[j + 1]
        lo_apex = len(set(lo)) == 1
        hi_apex = len(set(hi)) == 1
        for i in range(nu):
            k = (i + 1) % nu
            if lo_apex and hi_apex:
                continue                       # zero-height sliver: skip
            if lo_apex:
                faces.append((lo[0], hi[k], hi[i]))    # fan off bottom pole
            elif hi_apex:
                faces.append((lo[i], lo[k], hi[0]))    # fan off top pole
            else:
                faces.append((lo[i], lo[k], hi[k]))
                faces.append((lo[i], hi[k], hi[i]))
    return np.asarray(verts), np.asarray(faces, dtype=np.int64)


def blob(nu: int = 64, nv: int = 33):
    """Ellipsoid, semi-axes (x,y,z) = (1, 2, 1) — the 2:1:1 proportion."""
    ys = np.linspace(-2.0, 2.0, nv)
    r = 1.0 * np.sqrt(np.maximum(0.0, 1.0 - (ys / 2.0) ** 2))
    return revolve(r, ys, nu)


def torus(R: float = 1.5, r: float = 0.5, nu: int = 64, nv: int = 32):
    """Standing wheel: big circle in the x-y plane, hole axis along z.

    Genus 1 — the seal plane at mid-height must cut TWO disjoint loops
    (front and back of the tube) and the seal must still close the body.
    """
    u = TWOPI * np.arange(nu) / nu
    v = TWOPI * np.arange(nv) / nv
    verts = np.empty((nu * nv, 3))
    for j, vv in enumerate(v):
        for i, uu in enumerate(u):
            cx, cy = R * math.cos(uu), R * math.sin(uu)   # tube center
            nx, ny = math.cos(uu), math.sin(uu)           # radial normal
            verts[j * nu + i] = (cx + r * math.cos(vv) * nx,
                                 cy + r * math.cos(vv) * ny,
                                 r * math.sin(vv))
    faces = []
    for j in range(nv):
        for i in range(nu):
            i2, j2 = (i + 1) % nu, (j + 1) % nv
            a = j * nu + i
            b = j * nu + i2
            c = j2 * nu + i2
            d = j2 * nu + i
            faces += [(a, b, c), (a, c, d)]
    return verts, np.asarray(faces, dtype=np.int64)


def capsule(r: float = 0.5, half_len: float = 0.75,
            nu: int = 48, n_cap: int = 12, n_cyl: int = 6):
    """Cylinder of half-length `half_len` capped with hemispheres."""
    H = half_len + r                                   # total half-height
    ys = [-H]                                          # bottom apex (r=0)
    for k in range(1, n_cap):                          # bottom hemisphere
        phi = 0.5 * math.pi * k / n_cap                # 0..pi/2 from pole
        ys.append(-(half_len + r * math.cos(phi)))
    for k in range(1, n_cyl + 1):                      # cylinder interior
        ys.append(-half_len + (2.0 * half_len) * k / (n_cyl + 1))
    for k in range(n_cap - 1, 0, -1):                  # top hemisphere
        phi = 0.5 * math.pi * k / n_cap
        ys.append(+(half_len + r * math.cos(phi)))
    ys.append(+H)                                      # top apex (r=0)
    ys = np.asarray(sorted(ys))
    d = np.maximum(np.abs(ys) - half_len, 0.0)
    prof = r * np.sqrt(np.maximum(0.0, 1.0 - (d / r) ** 2))
    prof[np.abs(ys) <= half_len] = r
    prof[0] = prof[-1] = 0.0                           # exact apexes
    return revolve(prof, ys, nu)


def peanut(a: float = 0.5, Y: float = 1.2, dip: float = 0.55,
           nu: int = 64, nv: int = 33):
    """Two-lobe body of revolution: an envelope hemisphere squeezed by a
    Gaussian waist dip at y=0 — two lobes, zero radius at the tips."""
    ys = np.linspace(-Y, Y, nv)
    envelope = a * np.sqrt(np.maximum(0.0, 1.0 - (ys / Y) ** 2))
    r = envelope * (1.0 - dip * np.exp(-((ys / (0.24 * Y)) ** 2)))
    return revolve(r, ys, nu)


def rbox(a: float = 1.05, e: float = 0.3, nu: int = 64, nv: int = 33):
    """Superquadric rounded cube: |x/a|^n + |y/a|^n + |z/a|^n = 1 with
    n = 2/e ~ 6.7 — flat-ish faces, rounded edges, real corners."""
    def c(w: np.ndarray) -> np.ndarray:
        return np.sign(np.cos(w)) * np.abs(np.cos(w)) ** e

    def s(w: np.ndarray) -> np.ndarray:
        return np.sign(np.sin(w)) * np.abs(np.sin(w)) ** e

    eta = np.linspace(-0.5 * math.pi, 0.5 * math.pi, nv)   # latitude
    omg = TWOPI * np.arange(nu) / nu                       # longitude
    verts: list[tuple[float, float, float]] = []
    rings: list[list[int]] = []
    for i, th in enumerate(eta):
        if i == 0 or i == nv - 1:                    # exact poles
            rings.append([len(verts)] * nu)
            verts.append((0.0, a if i == nv - 1 else -a, 0.0))
            continue
        row = []
        for ph in omg:
            row.append(len(verts))
            verts.append((float(a * c(th) * c(ph)),
                          float(a * s(th)),
                          float(a * c(th) * s(ph))))
        rings.append(row)
    faces = []
    for j in range(nv - 1):
        lo, hi = rings[j], rings[j + 1]
        lo_apex = len(set(lo)) == 1
        hi_apex = len(set(hi)) == 1
        for i in range(nu):
            k = (i + 1) % nu
            if lo_apex:
                faces.append((lo[0], hi[k], hi[i]))
            elif hi_apex:
                faces.append((lo[i], lo[k], hi[0]))
            else:
                faces.append((lo[i], lo[k], hi[k]))
                faces.append((lo[i], hi[k], hi[i]))
    return np.asarray(verts), np.asarray(faces, dtype=np.int64)


# ── the watertight PROOF (runs before any POST may happen) ──────────────
def edge_pair_check(verts: np.ndarray, faces: np.ndarray) -> dict:
    """Closed 2-manifold: every directed edge used exactly once, twin used
    exactly once; every vertex referenced; nothing NaN/inf."""
    de: Counter = Counter()
    for f in faces:
        a, b, cc = (int(x) for x in f)
        de[(a, b)] += 1
        de[(b, cc)] += 1
        de[(cc, a)] += 1
    dup = sum(1 for v in de.values() if v != 1)
    boundary = sum(1 for (a, b) in de if de.get((b, a), 0) != 1)
    used = np.zeros(len(verts), dtype=bool)
    used[faces.ravel()] = True
    finite = bool(np.isfinite(verts).all())
    return {"dup_directed": dup, "boundary_edges": boundary,
            "orphans": int((~used).sum()), "finite": finite,
            "directed_edges": len(de)}


def divergence_volume(verts: np.ndarray, faces: np.ndarray) -> float:
    p = verts[faces]
    return float(np.einsum("ij,ij->i", p[:, 0],
                           np.cross(p[:, 1], p[:, 2])).sum() / 6.0)


def verify(verts: np.ndarray, faces: np.ndarray, name: str) -> float:
    """Assert watertight; return the signed divergence volume (flips the
    whole mesh to outward winding first if the raw sign is inward)."""
    if divergence_volume(verts, faces) < 0.0:
        faces[:] = faces[:, ::-1]        # flip IN PLACE: the caller posts
    chk = edge_pair_check(verts, faces)  # the same array it will verify
    vol = divergence_volume(verts, faces)
    lo, hi = verts.min(axis=0), verts.max(axis=0)
    bbox = float(np.prod(hi - lo))
    ok = (chk["dup_directed"] == 0 and chk["boundary_edges"] == 0
          and chk["orphans"] == 0 and chk["finite"] and vol > bbox * 1e-6)
    if not ok:
        raise AssertionError(f"{name}: NOT watertight -- {chk} V={vol:.6g}")
    verts[:], faces[:] = verts, faces
    print(f"  {name:8s} CLOSED: {chk['directed_edges']} edges, 0 dup, "
          f"0 boundary, 0 orphans | divergence V = {vol:+.6f} "
          f"(bbox eps floor {bbox * 1e-6:.2e}) -> OUTWARD")
    return vol


def write_obj(path: Path, verts: np.ndarray, faces: np.ndarray) -> dict:
    """Write 'v'/'f' text, then RE-PARSE the text and re-verify — the
    proof must hold on the exact bytes the engine will read."""
    lines = [f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" for p in verts]
    lines += [f"f {f[0] + 1} {f[1] + 1} {f[2] + 1}" for f in faces]
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="ascii", newline="\n")

    v2 = np.array([[float(t) for t in ln.split()[1:4]]
                   for ln in text.splitlines() if ln.startswith("v ")])
    f2 = np.array([[int(t) - 1 for t in ln.split()[1:4]]
                   for ln in text.splitlines() if ln.startswith("f ")])
    if divergence_volume(v2, f2) < 0.0:
        raise AssertionError(f"{path.name}: text winding came out inward")
    chk = edge_pair_check(v2, f2)
    vol = divergence_volume(v2, f2)
    lo, hi = v2.min(axis=0), v2.max(axis=0)
    bbox = float(np.prod(hi - lo))
    assert chk["dup_directed"] == 0 and chk["boundary_edges"] == 0 \
        and chk["orphans"] == 0 and vol > bbox * 1e-6, \
        f"{path.name}: parsed text is NOT watertight: {chk} V={vol}"
    print(f"  {path.name:12s} TEXT RE-VERIFIED closed, V={vol:+.6f} "
          f"({len(v2)} verts, {len(f2)} tris, {len(text):,} bytes)")
    return {"verts": int(len(v2)), "tris": int(len(f2)),
            "V_text": vol, "bytes": len(text)}


def build_all(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, (verts, faces) in [
        ("blob", blob()),
        ("torus", torus()),
        ("capsule", capsule()),
        ("peanut", peanut()),
        ("rbox", rbox()),
    ]:
        print(name)
        verify(verts, faces, name)
        manifest[name] = write_obj(out / f"{name}.obj", verts, faces)
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent / "obj"))
    args = ap.parse_args()
    m = build_all(Path(args.out))
    print("\nALL FIVE WATERTIGHT — cleared to post:")
    for k, v in m.items():
        print(f"  {k:8s} {v['verts']:5d} verts {v['tris']:5d} tris "
              f"V={v['V_text']:+.6f} {v['bytes']:,} B")
