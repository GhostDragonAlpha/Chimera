"""B2 step 1 scene generator: chimera.b2_scene.v1 from the B1 packet wedges.

Two independent rigid parts (WEDGE_A granite, WEDGE_B steel) stand on the
ground plane y = 0 with gravity, each supported by its own per-site
one-sided penalty rung -- the FALL law's contact formulation, with the
rung constants DERIVED per part from the same derivation that produced
the resident body's k_ground_/c_ground_:

    rest sink under weight   s* = 0.01 m   ->  k_total = m g / s*
    damping ratio            zeta = 0.7    ->  c_total = 2 zeta sqrt(k_total m)
    per contact site (N sites): k_site = k_total / N, c_site = c_total / N

Reusing the resident constants verbatim would be wrong twice over: the
13.8 t body's c_ground_ on a ~10 kg part makes the explicit damping term
unstable at the fixed substep (h c/m >> 2), and a granite wedge should not
sink on a 13.8 t suspension. With the derived constants the per-site
damping number h c_site / m = 2 zeta h sqrt(g / (s* N)) is mass-independent
(~1.8e-3 at h = 250 us) and the rest sink is s* for every part.

Poses: authored wedges stand on their z = 0 face; R_x(-90 deg) maps
authored +z to world +y, so with translation (tx, 0, tz) the bottom face
sits exactly on y = 0.  Inertia is the compiled full 3x3 about the COM in
authored axes -- the native side validates symmetry, positivity and the
physical triangle inequality itself.

Run:  python tools/construction_packet/b2_scene_gen.py  (prints the scene)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import packet  # noqa: E402

G = 9.81
REST_SINK_M = 0.01
DAMPING_RATIO = 0.7

# R_x(-90 deg): authored +z -> world +y (bottom face z=0 lands on y=0).
Q_WXYZ = (math.cos(math.pi / 4.0), -math.sin(math.pi / 4.0), 0.0, 0.0)


def rung_constants(mass_kg: float, n_sites: int,
                   g: float = G, s_star: float = REST_SINK_M,
                   zeta: float = DAMPING_RATIO) -> tuple[float, float]:
    """Per-site (k, c) from the rest-sink + damping-ratio law above."""
    k_total = mass_kg * g / s_star
    c_total = 2.0 * zeta * math.sqrt(k_total * mass_kg)
    return k_total / n_sites, c_total / n_sites


def _rot_com(q: tuple[float, float, float, float], v: tuple[float, float, float]):
    """Rotate v by unit quaternion q (w,x,y,z): R v via q -> matrix rows."""
    w, x, y, z = q
    r = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(r[i][j] * v[j] for j in range(3)) for i in range(3))


def part_document(template: dict, translation: tuple[float, float, float],
                  reason: str) -> dict:
    """One chimera.b2_scene.v1 part from a packet wedge template."""
    compiled = packet.compile_wedge(template)
    mp = compiled.mass_properties
    assert mp is not None, f"{template['template_id']}: packet did not compile"
    vertices, _tets = packet.wedge_geometry(
        **{k: template[k] for k in "LWH"})
    tris = [idx for bf in compiled.boundary_faces for idx in bf.vertices]
    com = _rot_com(Q_WXYZ, mp.center_of_mass_m)
    # The engine reads the ground rung at every vertex, but only the bottom
    # face (authored z=0) can penetrate y=0 at rest, so the load is shared by
    # exactly those vertices. Deriving per-site constants from the full vertex
    # count would halve the effective stiffness and double the rest sink.
    n_sites = sum(1 for v in vertices if abs(v[2]) < 1e-12)
    k_site, c_site = rung_constants(mp.mass_kg, n_sites)
    return {
        "id": template["region"].mass_owner_id,
        "mass_kg": mp.mass_kg,
        "com_local_m": list(mp.center_of_mass_m),
        "inertia_com_local_kg_m2": [c for row in mp.inertia_com_kg_m2 for c in row],
        "vertices_local_m": [c for v in vertices for c in v],
        "boundary_triangles": tris,
        "pose_c_m": [com[i] + translation[i] for i in range(3)],
        "pose_q_wxyz": list(Q_WXYZ),
        "ground": {"k_n_per_m": k_site, "c_n_s_per_m": c_site},
        "_reason": reason,
    }


def make_scene() -> dict:
    a = part_document(packet.WEDGE_A, (0.0, 0.0, 0.0),
                      "B2 step 1 statics: granite wedge A on the ground plane")
    b = part_document(packet.WEDGE_B, (0.6, 0.0, 0.0),
                      "B2 step 1 statics: steel wedge B on the ground plane")
    reason = (a.pop("_reason") + " | " + b.pop("_reason")
              + " | rung: rest sink 1 cm, zeta 0.7, per part")
    return {"schema": "chimera.b2_scene.v1", "gravity_m_s2": G,
            "parts": [a, b], "reason": reason}


if __name__ == "__main__":
    print(json.dumps(make_scene(), indent=1))
