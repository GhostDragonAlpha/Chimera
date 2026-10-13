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


# ─── B3: three dissimilar layers stacked into one visible shape ───────────
# The §13 B3 gate: "Three dissimilar layers in loose and bonded variants,
# same initial visible shape, inspection by stable IDs". Three rectangular
# layers of DIFFERENT material (granite / steel / timber densities), size
# and thickness, stacked so every upper layer's bottom vertices project
# STRICTLY inside the layer below (the contact law rejects boundary
# projections, and the insets also clear both face diagonals by >= 7 mm).
# Authored axes = world axes (identity pose); rung constants follow the
# same rest-sink / zeta derivation as the wedges.
# Outward-wound faces ((b-a)x(c-a) points OUT): the contact law's strict
# containment assumes CCW-about-outward winding, so a CW face would reject
# every projection and the stack would fall through itself.
BOX_FACES = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
             (3, 0, 4), (3, 4, 7), (1, 2, 6), (1, 6, 5),
             (4, 0, 1), (4, 1, 5), (2, 3, 7), (2, 7, 6)]


def box_document(pid: str, x0: float, x1: float, y0: float, y1: float,
                 z0: float, z1: float, density_kg_m3: float, mu: float) -> dict:
    vs = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    mass = density_kg_m3 * dx * dy * dz
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    ixx = mass / 12 * (dy * dy + dz * dz)
    iyy = mass / 12 * (dx * dx + dz * dz)
    izz = mass / 12 * (dx * dx + dy * dy)
    k_site, c_site = rung_constants(mass, 4)      # bottom face: 4 sites
    return {
        "id": pid,
        "mass_kg": mass,
        "com_local_m": [cx, cy, cz],
        "inertia_com_local_kg_m2": [ixx, 0, 0, 0, iyy, 0, 0, 0, izz],
        "vertices_local_m": [c for v in vs for c in v],
        "boundary_triangles": [i for f in BOX_FACES for i in f],
        "pose_c_m": [cx, cy, cz],
        "pose_q_wxyz": [1.0, 0.0, 0.0, 0.0],
        "ground": {"k_n_per_m": k_site, "c_n_s_per_m": c_site},
        "mu": mu,
    }


# Layer geometry (world = authored m, NOMINAL poses). Densities kg/m^3:
# granite 2700, steel 7850, timber 600. Masses: 29.16 / 48.984 / 1.536 kg.
# Footprint rule: every upper-layer corner must sit >= 15 mm away from
# BOTH diagonals of the face below (each quad is triangulated along one
# diagonal; a corner near it makes containment flicker as the layer
# rotates, and the flickering contact torques run away -- measured: the
# base yawed 31 deg with no external torque at all). The strips below
# keep >= 15 mm on every corner of every interface.
STACK_LAYERS = [
    # id,                    x0,   x1,   y0,   y1,   z0,   z1,  rho,  mu
    ("layer_base_granite",   0.00, 0.30, 0.00, 0.12, 0.00, 0.30, 2700, 0.5),
    ("layer_mid_steel",      0.03, 0.27, 0.12, 0.22, 0.09, 0.21, 7850, 0.4),
    ("layer_top_timber",     0.06, 0.24, 0.22, 0.30, 0.12, 0.18,  600, 0.3),
]


def stack_rest_offsets() -> list[float]:
    """Spawn y-offsets putting every interface at its analytic REST SINK.
    Admitting the layers from touching poses lets each free-fall into its
    penalty sink (the base sinks 27 mm into the ground under the whole
    stack, the steel overshoots into the granite, and the light timber
    top tunnels clean through -- measured). Pre-sinking every layer to its
    equilibrium penetration starts the scene with every rung ACTIVE and
    the transient is only the damping settling, exactly like the B2 wedges'
    1 cm rest sink."""
    w = [l[7] * (l[2] - l[1]) * (l[4] - l[3]) * (l[6] - l[5]) * G
         for l in STACK_LAYERS]                       # weights
    kt = [m * G / REST_SINK_M for m in
          (l[7] * (l[2] - l[1]) * (l[4] - l[3]) * (l[6] - l[5])
           for l in STACK_LAYERS)]                    # ground k_total
    # pair k_total = 4 * mean(k_site) = (kt_a + kt_b) / 2
    sink_ground = (w[0] + w[1] + w[2]) / kt[0]
    sink_01 = (w[1] + w[2]) / ((kt[0] + kt[1]) / 2)
    sink_12 = w[2] / ((kt[1] + kt[2]) / 2)
    b0 = -sink_ground
    b1 = (b0 + 0.12) - sink_01
    b2 = (b1 + 0.10) - sink_12
    return [b0 - 0.0, b1 - 0.12, b2 - 0.22]           # shift per nominal y0


def make_stack(bonded: bool = False) -> dict:
    """The B3 stack; `bonded` only changes the reason string -- the welds
    are set through the live control after admission, so BOTH variants
    admit the identical visible shape (spawned at the rest-sink poses)."""
    offs = stack_rest_offsets()
    parts = []
    for (lay, dy) in zip(STACK_LAYERS, offs):
        (pid, x0, x1, y0, y1, z0, z1, rho, mu) = lay
        parts.append(box_document(pid, x0, x1, y0 + dy, y1 + dy, z0, z1, rho, mu))
    reason = ("B3 stack: three dissimilar layers (granite/steel/timber), "
              + ("bonded variant" if bonded else "loose variant")
              + " | rung: rest sink 1 cm, zeta 0.7, per part"
              + " | spawn: pre-sunk to analytic rest")
    return {"schema": "chimera.b2_scene.v1", "gravity_m_s2": G,
            "parts": parts, "reason": reason}


def stack_weld_document(k: float = 50000.0, c_damp: float = 300.0) -> dict:
    """Weld anchors across the steel/timber interface AT ITS REST-SINK
    HEIGHT, inside the timber footprint; coincident pairs -> zero rest
    length, zero preload."""
    y = 0.22 + stack_rest_offsets()[2]
    anchors = [(0.09, y, 0.14), (0.21, y, 0.14), (0.15, y, 0.17)]
    return {"a": "layer_mid_steel", "b": "layer_top_timber",
            "k": k, "c_damp": c_damp,
            "anchors_world": [[*p, *p] for p in anchors]}


if __name__ == "__main__":
    print(json.dumps(make_scene(), indent=1))
