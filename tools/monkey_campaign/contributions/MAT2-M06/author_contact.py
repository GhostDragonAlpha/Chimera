"""MAT2-M06 fixture authoring and declaration emission (deterministic).

Builds the small contact fixtures over the PINNED MAT2-M02 inputs (mesh blob
+ independent shapes, pinned by file sha256; drift refuses
`input_pin_drift`), emits the chimera.local_contact.v1 declaration document
(contact_law.json) and the structured display (contact_display.json).

The block mass 0.12 kg and plate mass 0.02 kg reuse the pinned mass_tetra /
mass_plate values from the compiled independent-shape document; thickness
0.002 m is the compiled shell_thickness_m. Fixture geometry beyond that is
authored synthetic at chosen fidelity (declared in PREREGISTRATION.md).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M02'))

import local_contact as lc  # noqa: E402

M02 = HERE.parent / 'MAT2-M02'
BLOB = M02 / 'monkey_arm_independent_meshes.json'
INDEP = M02 / 'independent_shape_regions.json'
ARM = M02 / 'monkey_arm_regions.json'

FROZEN_PINS = {
    'monkey_arm_independent_meshes.json':
        '51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834',
    'independent_shape_regions.json':
        '0f0b7165883183446b15b7043fd5471f0b12d6d992ffabc27107f4de1238887e',
    'monkey_arm_regions.json':
        '15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9e8758366f1',
}

MASS_BLOCK = 0.12     # kg, pinned mass_tetra value
MASS_SHELL = 0.02     # kg, pinned mass_plate value
MU_BLOCK = (0.6, 0.4)
MU_PLATE = (0.7, 0.5)
SEED_BASE = 20260928


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def check_pins():
    for name, want in FROZEN_PINS.items():
        got = sha256_file(M02 / name)
        if got != want:
            raise ValueError('input_pin_drift:' + name)


def load_blob():
    return json.loads(BLOB.read_text(encoding='utf-8'))


def load_indep():
    return json.loads(INDEP.read_text(encoding='utf-8'))


# ---------- authored fixture geometry (frozen) ----------

def plate_vertices(z=0.0):
    """2-triangle support plate, 0.2 x 0.1 m, triangle areas 0.01 m^2 each
    (bitwise-equal, same construction as the pinned independent-shape plate),
    +z up."""
    v = [(0.0, 0.0, z), (0.2, 0.0, z), (0.2, 0.1, z), (0.0, 0.1, z)]
    return v, [(0, 1, 2), (0, 2, 3)]


def twin_plate_vertices(z=0.0):
    """Twin plate: triangle areas 0.01 and 0.02 m^2 (ratio exactly 2)."""
    v = [(0.0, 0.0, z), (0.2, 0.0, z), (0.2, 0.1, z), (-0.2, 0.1, z)]
    return v, [(0, 1, 2), (0, 2, 3)]


def block_vertices(z, x=0.0, y=0.0):
    """2-triangle block, 0.1 x 0.05 m (triangle areas 0.0025 m^2), +z up."""
    v = [(x, y, z), (x + 0.1, y, z), (x + 0.1, y + 0.05, z), (x, y + 0.05, z)]
    return v, [(0, 1, 2), (0, 2, 3)]


def shell_vertices(z, cx=0.0, cy=0.0):
    """2-triangle shell, 0.05 x 0.05 m, in the z=const plane."""
    v = [(cx - 0.025, cy - 0.025, z), (cx + 0.025, cy - 0.025, z),
         (cx + 0.025, cy + 0.025, z), (cx - 0.025, cy + 0.025, z)]
    return v, [(0, 1, 2), (0, 2, 3)]


GAP0 = 0.01            # m initial midsurface gap for X1/X2
ZCONTACT = 0.002001    # m block z for gap == MARGIN (persistent start)


def make_block(z, vel=(0.0, 0.0, 0.0), x=0.0, y=0.0):
    v, t = block_vertices(z, x, y)
    return lc.Body('block', 'block', 'mass_block', MASS_BLOCK, MU_BLOCK[0],
                   MU_BLOCK[1], lc.THICKNESS_M, v, t, velocity=vel)


def make_plate(z=0.0, pinned=True, twin=False):
    v, t = twin_plate_vertices(z) if twin else plate_vertices(z)
    return lc.Body('plate', 'plate', 'mass_plate', MASS_SHELL, MU_PLATE[0],
                   MU_PLATE[1], lc.THICKNESS_M, v, t, pinned=pinned)


def make_shells(gap, offset=(0.0, 0.0), closing=2.0):
    """Two shells approaching head-on along z, gap = midsurface distance."""
    va, ta = shell_vertices(+gap / 2.0, offset[0], offset[1])
    vb, tb = shell_vertices(-gap / 2.0, offset[0], offset[1])
    a = lc.Body('shell_a', 'shell_a', 'mass_shell_a', MASS_SHELL, 0.6, 0.4,
                lc.THICKNESS_M, va, ta, velocity=(0.0, 0.0, -closing))
    b = lc.Body('shell_b', 'shell_b', 'mass_shell_b', MASS_SHELL, 0.6, 0.4,
                lc.THICKNESS_M, vb, tb, velocity=(0.0, 0.0, +closing))
    return a, b


# ---------- compiled-geometry bodies (pinned M02 vocabulary) ----------

def bodies_from_compiled(region_ids):
    """Build static free bodies from the pinned compiled mesh blob for the
    named regions, in their compiled default-pose world positions."""
    blob = load_blob()
    bodies = []
    for rid in region_ids:
        r = blob['regions'][rid]
        bodies.append(lc.Body(rid, rid, 'mass_' + rid, 0.01, 0.6, 0.4,
                              lc.THICKNESS_M, r['world_vertices_m'],
                              r['triangles']))
    return bodies


# ---------- seeded LCG (frozen in PREREGISTRATION.md) ----------

def lcg_uniforms(seed, count):
    out = []
    state = seed & ((1 << 64) - 1)
    for _ in range(count):
        state = (state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        out.append((state >> 11) / float(1 << 53))
    return out


def axis_angle_rotate(v, axis, angle):
    c, s = math.cos(angle), math.sin(angle)
    k = axis
    return (
        v[0] * (c + k[0] * k[0] * (1 - c)) + v[1] * (k[0] * k[1] * (1 - c) - k[2] * s) + v[2] * (k[0] * k[2] * (1 - c) + k[1] * s),
        v[0] * (k[1] * k[0] * (1 - c) + k[2] * s) + v[1] * (c + k[1] * k[1] * (1 - c)) + v[2] * (k[1] * k[2] * (1 - c) - k[0] * s),
        v[0] * (k[2] * k[0] * (1 - c) - k[1] * s) + v[1] * (k[2] * k[1] * (1 - c) + k[0] * s) + v[2] * (c + k[2] * k[2] * (1 - c)),
    )


def random_scene(k):
    """Seeded small fixture: pinned ground plate + 2 free soups placed so the
    3-tick run produces real contact density (landings and mutual sweeps);
    random static orientation/offsets inside the frozen 0.5 m envelope, half
    the scenes with relative motion up to 0.02 m/tick."""
    u = lcg_uniforms(SEED_BASE + k, 200)
    ground = make_plate(z=-0.05, pinned=True)
    ground.id = 'ground'
    ground.surface_id = 'ground'
    bodies = [ground]
    for bi in range(2):
        cx = -0.05 + 0.3 * u[4 * bi]
        cy = -0.025 + 0.15 * u[4 * bi + 1]
        cz = -0.05 + 0.033 + 0.05 * u[4 * bi + 2]
        ang = math.radians(30.0) * u[8 + bi]
        axis = vnorm3((u[10 + bi] - 0.5, u[12 + bi] - 0.5, u[14 + bi] - 0.5))
        ntri = 2 + int(2 * u[16 + bi])
        verts = []
        tris = []
        for ti in range(ntri):
            base = 20 + 8 * ti + 40 * bi
            local = [(u[base] * 0.06, u[base + 1] * 0.06, 0.0),
                     (u[base + 2] * 0.06 + 0.04, u[base + 3] * 0.06, 0.0),
                     (u[base + 4] * 0.06, u[base + 5] * 0.06 + 0.04, 0.0)]
            world = [tuple(vadd3(axis_angle_rotate(p, axis, ang), (cx, cy, cz))) for p in local]
            idx = len(verts)
            verts.extend(world)
            tris.append((idx, idx + 1, idx + 2))
        if k % 2 == 0:
            vel = (0.4 * (u[18 + bi] - 0.5), 0.4 * (u[20 + bi] - 0.5),
                   -0.5 - 1.5 * u[22 + bi])
        else:
            vel = (1.6 * (u[18 + bi] - 0.5), 1.6 * (u[20 + bi] - 0.5),
                   -0.5 - 3.5 * u[22 + bi])
        bodies.append(lc.Body('soup%d' % bi, 'soup%d' % bi, 'mass_soup%d' % bi,
                              0.02, 0.6, 0.4, lc.THICKNESS_M, verts, tris,
                              velocity=vel))
    return bodies


def vnorm3(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n == 0.0:
        return (0.0, 0.0, 1.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def vadd3(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


# ---------- declaration document ----------

def emit():
    check_pins()
    indep = load_indep()
    blob = load_blob()
    surfaces = [
        {'id': 'plate', 'matter_id': 'mass_plate', 'mass_kg': MASS_SHELL,
         'pinned': True, 'mu_s': MU_PLATE[0], 'mu_k': MU_PLATE[1],
         'thickness_m': lc.THICKNESS_M, 'triangle_count': 2,
         'provenance': 'support fixture; area construction equal to the '
                       'pinned independent-shape plate (0.01 m^2 each, '
                       'bitwise equal); also carries the pinned compiled '
                       'plate triangles in the X0 vocabulary run; mass '
                       'value = pinned mass_plate'},
        {'id': 'block', 'matter_id': 'mass_block', 'mass_kg': MASS_BLOCK,
         'pinned': False, 'mu_s': MU_BLOCK[0], 'mu_k': MU_BLOCK[1],
         'thickness_m': lc.THICKNESS_M, 'triangle_count': 2,
         'provenance': 'authored sliding/resting fixture; mass value = '
                       'pinned mass_tetra'},
        {'id': 'twin_plate', 'matter_id': 'mass_plate', 'mass_kg': MASS_SHELL,
         'pinned': True, 'mu_s': MU_PLATE[0], 'mu_k': MU_PLATE[1],
         'thickness_m': lc.THICKNESS_M, 'triangle_count': 2,
         'provenance': 'authored area-scaling twin: triangle areas 0.01 and '
                       '0.02 m^2 (ratio 2)'},
        {'id': 'shell_a', 'matter_id': 'mass_shell_a', 'mass_kg': MASS_SHELL,
         'pinned': False, 'mu_s': 0.6, 'mu_k': 0.4,
         'thickness_m': lc.THICKNESS_M, 'triangle_count': 2,
         'provenance': 'authored crossing shell (high-speed fixture); mass '
                       'value = pinned mass_plate'},
        {'id': 'shell_b', 'matter_id': 'mass_shell_b', 'mass_kg': MASS_SHELL,
         'pinned': False, 'mu_s': 0.6, 'mu_k': 0.4,
         'thickness_m': lc.THICKNESS_M, 'triangle_count': 2,
         'provenance': 'authored crossing shell (high-speed fixture)'},
        {'id': 'tetra', 'matter_id': 'mass_tetra', 'mass_kg': 0.12,
         'pinned': False, 'mu_s': 0.6, 'mu_k': 0.4,
         'thickness_m': lc.THICKNESS_M, 'triangle_count': 4,
         'provenance': 'pinned MAT2-M02 independent-shape tetra (identity '
                       'visual/physical triangle lists; rigid placement '
                       'offset declared per scenario)'},
    ]
    doc = {
        'schema': lc.SCHEMA,
        'revision': 1,
        'object_id': 'local-contact-law',
        'provenance': {
            'base_revision': 'f67a622ab37bf0f3201613701cf89028d6a8eed4',
            'input_pins': {name: sha256_file(M02 / name)
                           for name in FROZEN_PINS},
            'thickness_source': 'MAT2-M02 independent_shape_regions.json '
                                'shell_thickness_m = 0.002',
            'mass_sources': 'mass_tetra 0.12 kg, mass_plate 0.02 kg (pinned '
                            'compiled matter rows)',
            'heritage': [
                'G3 deterministic Baumgarte contact solve, estimator B '
                'penetration proxy (docs/THE_MASTER_LIST.md H7 stage 3, '
                'agent_logs/kimi/contact_ref_01.md, .tmp/contact_ref.py: '
                '0 ULP double-run discipline)',
                'B2 bonds-are-materials: capacity = strength x area '
                '(area-scaled per-triangle load report)',
                'L3 tri_ca registry: triangle centers as stable addresses '
                '(stable triangle ids in contact records)',
                'req.teddy_gpu_matter_kernel law_families.local: contact/'
                'friction use local adjacency/constraint passes; a far-field '
                'monopole cannot substitute',
            ],
            'declarations_status': 'synthetic_authored law constants (mu, '
                                   'beta, slop, margin, dt); thickness and '
                                   'masses pinned from MAT2-M02',
        },
        'declarations': {
            'g': lc.G, 'dt': lc.DT, 'thickness_m': lc.THICKNESS_M,
            'slop_m': lc.SLOP_M, 'margin_m': lc.MARGIN, 'beta': lc.BETA,
            'restitution': lc.RESTITUTION,
            'pair_friction_rule': 'elementwise_min',
            'ccd': {'method': 'conservative_advancement',
                    'max_iters': lc.CCD_MAX_ITERS,
                    'activation_tolerance_m': lc.CCD_TOL_M,
                    'fallback': 'uniform resample of the remaining window '
                                '(S = max_iters samples) when the Lipschitz '
                                'advance crawls; under-detection bounded by '
                                '|w|*dt/S for the sampled interval',
                    'declared_capture_bound_m_per_tick': 0.02},
            'candidate_search': {'method': 'sweep_and_prune',
                                 'axis_rule': 'max_variance_center',
                                 'inflation': 'motion_bound + thickness + '
                                              'margin'},
            'area_report_rule': 'uniform contact pressure over contacted '
                                'area: p = Jn_total/(dt*sum(a)); F_i = p*a_i',
            'seeds': {'rng': 'lcg_64bit', 'seed_base': SEED_BASE,
                      'scenes': 32, 'scene_k_seed': 'seed_base + k'},
        },
        'surfaces': surfaces,
        'contacts': [],
    }
    known = {s['id'] for s in surfaces}
    lc.validate_local_contact(doc, known)
    (HERE / 'contact_law.json').write_text(
        json.dumps(doc, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')

    # structured display (records, not pixels) of the declaration + a snapshot
    display = {
        'schema': 'chimera.local_contact.display.v1',
        'object_id': doc['object_id'],
        'declarations': doc['declarations'],
        'surface_ids': [s['id'] for s in surfaces],
        'counts': {'surface_count': len(surfaces)},
        'identity_guards': {
            'visual_physical_identity': 'pinned blob declares identity '
                                        '(same triangle list); fixture builder '
                                        'asserts the pinned lists verbatim',
            'blob_sha256': FROZEN_PINS['monkey_arm_independent_meshes.json'],
        },
        'honest_gaps': [
            'rigid translation kinematics only: no rotation dynamics, no '
            'deformation, no pressure law (M03 pending, not merged)',
            'offline CPU experiment executable; not the native C++ engine, '
            'no GPU residency, no live renderer',
            'friction is Coulomb stick/slip on declared pair min rule; no '
            'spatially varying friction',
        ],
    }
    (HERE / 'contact_display.json').write_text(
        json.dumps(display, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')
    return doc, display


if __name__ == '__main__':
    doc, display = emit()
    print('contact_law.json surfaces:', len(doc['surfaces']),
          '| declarations:', len(doc['declarations']))
    print('blob pin verified:', FROZEN_PINS['monkey_arm_independent_meshes.json'][:16], '...')
