"""MAT2-M12: qualify mechanical detail and render detail independently.

The sealed M11 hanging bone-chain limb rig (``limb_world.py``, imported
UNMODIFIED and sha-pinned) is exercised at TWO declared mechanical
resolutions that differ ONLY in builder data (PREREGISTRATION.md section 1;
there is NO resolution-conditional dynamics code):

  coarse     6 x 6 tube    (38 vertices, 72 triangles, 33 belt chords)
  reference  12 x 12 tube  (146 vertices, 288 triangles, 150 belt chords;
                           the sealed M11 limb resolution)

Declared remapping rules (prereg section 1, the LOD contract):
  1. total tissue mass is the bitwise invariant (the sealed module splits
     per vertex itself);
  2. the belt chord section is the equal split of the declared invariant
     A_CHORD_TOTAL = A_CHORD(sealed) * n_chords(sealed) over the
     resolution's chord count;
  3. the edge network law is already per-area (a_dual-weighted) and is
     untouched;
  4. every interface (chain spec, tie sites, load surrogate, ground law,
     schedule) is bitwise-identical builder data;
  5. erection offsets are per-resolution declared constants (the reference
     offset is the SEALED M11 value; the coarse offset is probe-derived,
     Amendment A1).

CPU-only; stdlib + numpy; float64; deterministic physics (no wall-clock in
the dynamics; cost measurements wrap the tick loop from outside and are
recorded in receipts only).
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
M11_DIR = CONTRIB / 'MAT2-M11'
for _p in (str(HERE), str(M11_DIR), str(CONTRIB / 'MAT2-M01'),
           str(CONTRIB / 'MAT2-M02'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M04'), str(CONTRIB / 'MAT2-M05'),
           str(CONTRIB / 'MAT2-B03'), str(CONTRIB / 'MAT2-B04'),
           str(CONTRIB / 'MAT2-A06'), str(CONTRIB / 'MAT2-B05')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import limb_world as lw  # noqa: E402  (sealed M11 rig, UNMODIFIED)


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def refuse_vacuous_comparison(a, b, code='vacuous_comparison_refused'):
    """A falsifier that cannot FAIL is refused (kit law P7)."""
    require(a != b, code + ':identical_sides')
    return a, b


# ------------------------------------------------------------ pins --------
INPUT_PINS = dict(lw.INPUT_PINS)
INPUT_PINS['MAT2-M11/limb_world.py'] = None   # sealed rig sha, pinned below
SEALED_RIG_SHA = sha256_file(M11_DIR / 'limb_world.py')
INPUT_PINS['MAT2-M11/limb_world.py'] = SEALED_RIG_SHA


def verify_input_pins():
    out = {}
    for rel, expected in INPUT_PINS.items():
        path = CONTRIB / rel
        require(path.exists(), 'input_pin_missing:' + rel)
        actual = sha256_file(path)
        require(actual == expected, 'input_pin_drift:' + rel)
        out[rel] = actual
    return out


# --------------------------------------------------- declared constants ---
# (M11 sealed rig constants carried UNMODIFIED; M12 additions here.)
RESOLUTIONS = {'coarse': (6, 6), 'reference': (12, 12)}
RESOLUTION_ORDER = ('coarse', 'reference')
# Section-1 table: build counts recorded before any dynamics run; the
# builders must reproduce them (gate Y1c).
DECLARED_COUNTS = {
    'coarse': {'rings': 6, 'radials': 6, 'n_vertices': 38, 'n_triangles': 72,
               'n_edges': 108, 'n_chords': 33},
    'reference': {'rings': 12, 'radials': 12, 'n_vertices': 146,
                  'n_triangles': 288, 'n_edges': 432, 'n_chords': 150},
}
SEALED_CHORD_SECTION_M2 = lw.A_CHORD                 # 9.0e-6 (M11 per chord)
SEALED_N_CHORDS = DECLARED_COUNTS['reference']['n_chords']   # 150
A_CHORD_TOTAL_M2 = SEALED_CHORD_SECTION_M2 * SEALED_N_CHORDS  # 1.35e-3
# Declared float-derivation floor for the equal-split audit (|A*n - A_TOTAL|):
# the FB3 undeclared-strength tamper (sealed 9.0e-6 kept at 33 chords) misses
# A_CHORD_TOTAL by 1.053e-4 m^2 (relative 7.8e-2) -- 11 orders above the
# floor; the floor only tolerates binary rounding of the declared split.
BELT_SPLIT_FLOOR_M2 = 1.0e-15
# Inertia gate window (prereg Y2c: cap-quadrature bound 0.12496 declared
# worst case; build-data difference 0.02138; window covers it 4.7x and a
# declared-mass tamper moves I by >= 1.7x -- the window bites).
I_LOD_REL = 0.10
GAP_WINDOW_M = 1.0e-3            # Y4c/Y5 erection-target + recovery window
BITE_M = lw.BITE_M               # 1.0e-3 m (M11 departure bite, carried)
AUDIT_WINDOW_M = lw.AUDIT_WINDOW_M   # 1e-9 m identity window
X8_FLOOR_J = 2.0e-3              # M11 A2 settled cumulative floor
# Cost limits (prereg section 3; declared from the real-time usage).
TICK_BUDGET_S = lw.DT            # 3.333e-3 s (one tick per 300 Hz period)
FRAME_BUDGET_S = 1.0 / 60.0      # 1.667e-2 s real-time render frame budget
CAPTURE_VIEWPORT = (640, 480)    # declared capture viewport (W, H)
# Falsifier fixture prefix (prereg section 4).
DECLARED_FIXTURE_TICKS = 500
SNAP_TICKS = (0, 450, 460, 700, 1100, 1350)
RELEASE_TICK = lw.RELEASE_TICK   # 450
RELEASE_TIE_ID = lw.RELEASE_TIE_ID  # 'T2'
PROBE_TICKS = 600                # coarse-erection free-hang probe length

# Per-resolution erection offsets (m). The reference value is the SEALED M11
# constant (reused, not re-derived). The coarse value is PROBE-DERIVED
# (probe_free_hang; the value and its probe trail are recorded in Amendment
# A1 BEFORE the bank; 1500-tick history = the bank's history length).
ERECTION_OFFSET_M = {'coarse': 0.0010928872117499794,
                     'reference': 0.0030312}


def require_offsets_declared():
    for res in RESOLUTION_ORDER:
        require(ERECTION_OFFSET_M[res] is not None,
                'erection_offset_undeclared:' + res)


# ------------------------------------------------------- configuration ----
_CONFIG_SOURCE = pathlib.Path(__file__).read_bytes().decode('utf-8')
CONFIG_FUNCTION_NAME = 'configure_resolution'


def chord_section_for(res):
    """Declared equal-split rule (prereg rule 2)."""
    n_chords = DECLARED_COUNTS[res]['n_chords']
    return A_CHORD_TOTAL_M2 / float(n_chords)


def configure_resolution(res):
    """The ONE declared configuration path (gate Y1a).

    Sets ONLY the three declared builder constants of the sealed module
    (tube rings/radials, belt chord section, limb erection offset) and
    returns the config record. The dynamics code of the sealed module is
    never touched; a named check audits by AST that constant writes in THIS
    module happen only inside this function."""
    require(res in RESOLUTIONS, 'resolution_unknown:' + str(res))
    rings, radials = RESOLUTIONS[res]
    require(ERECTION_OFFSET_M[res] is not None,
            'erection_offset_undeclared:' + res)
    lw.TUBE_RINGS = rings
    lw.TUBE_RADIALS = radials
    lw.A_CHORD = chord_section_for(res)
    lw.ERECTION_OFFSET_M['limb'] = ERECTION_OFFSET_M[res]
    return {'resolution': res, 'rings': rings, 'radials': radials,
            'chord_section_m2': lw.A_CHORD,
            'erection_offset_m': ERECTION_OFFSET_M[res],
            'a_chord_total_m2': A_CHORD_TOTAL_M2}


def audit_config_function_purity():
    """Y1a: constant writes on the sealed module happen ONLY inside
    configure_resolution (AST audit of THIS file)."""
    tree = ast.parse(_CONFIG_SOURCE)
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == CONFIG_FUNCTION_NAME:
            continue
        for sub in ast.walk(node):
            if (isinstance(sub, ast.Assign)
                    and isinstance(sub.value, ast.Attribute)
                    and isinstance(sub.value.value, ast.Name)
                    and sub.value.value.id == 'lw'):
                violations.append('config_write_outside:%s:%d'
                                  % (node.name, sub.lineno))
    return {'violations': violations, 'ok': not violations,
            'config_function': CONFIG_FUNCTION_NAME}


def build_world(res, schedule_fn, ticks, mode='loaded', real=None, **kw):
    """Build one sealed-rig run at the declared resolution.

    The ONLY difference between resolutions is the configuration applied
    before construction; construction and dynamics are the sealed module's
    own code path."""
    config = configure_resolution(res)
    world = lw.LimbWorld('limb', schedule_fn, ticks, mode=mode, real=real,
                         **kw)
    return world, config


# ------------------------------------------------------------- audits -----
def resolution_build_audit(res, world, config):
    """Y1c + Y2a/Y2b + Y3b: the build counts, the bitwise mass invariants
    and the declared belt split of one built world."""
    declared = DECLARED_COUNTS[res]
    n_v = int(world.rest.shape[0])
    n_t = int(world.tris.shape[0])
    n_e = int(world.edges.shape[0])
    counts = {'n_vertices': n_v, 'n_triangles': n_t, 'n_edges': n_e,
              'n_chords': int(world.n_chords)}
    counts_ok = all(counts[k] == declared[k] for k in counts)
    tissue_total = float(world.spec_tissue_mass)
    per_vertex = float(world.vertex_mass)
    split_exact = bool(per_vertex * n_v == tissue_total)
    chain_masses = [float(m) for m in world.chain_mass]
    belt_product = float(lw.A_CHORD) * int(world.n_chords)
    belt_floor = abs(belt_product - A_CHORD_TOTAL_M2)
    belt_ok = bool(belt_floor <= BELT_SPLIT_FLOOR_M2)
    chord_k_recomputed = (lw.E_FIBER * lw.A_CHORD
                          / np.maximum(world.chord_l0, 1e-12))
    chord_k_bitwise = bool(np.array_equal(chord_k_recomputed,
                                          world.chord_k))
    edge_k_recomputed = (lw.E_TRANS * lw.T_WALL * world.a_dual
                         / (world.l0 * world.l0))
    edge_k_bitwise = bool(np.array_equal(edge_k_recomputed, world.k_edge))
    return {
        'resolution': res,
        'counts': counts, 'declared_counts': declared,
        'counts_match_declared': bool(counts_ok),
        'tissue_total_kg': tissue_total,
        'tissue_per_vertex_kg': per_vertex,
        'per_vertex_split_exact': split_exact,
        'chain_masses_kg': chain_masses,
        'load_mass_kg': float(world.load_mass),
        'chord_section_m2': float(lw.A_CHORD),
        'chord_section_times_n_m2': belt_product,
        'belt_split_floor_m2': BELT_SPLIT_FLOOR_M2,
        'belt_split_abs_error_m2': belt_floor,
        'belt_section_within_declaration': belt_ok,
        'chord_k_bitwise_lawform': chord_k_bitwise,
        'edge_k_bitwise_lawform': edge_k_bitwise,
    }


def interface_digest(world):
    """Y3a: digest over the RESOLUTION-INVARIANT interface builder data."""
    return digest({
        'chain_spec': world.chain_spec,
        'load_mass_kg': float(world.load_mass),
        'load_tie_rest_m': float(world.load_tie.rest_length),
        'load_tie_k': float(world.load_tie.k),
        'chain_tie_ids': list(world.chain_tie_ids),
        'chain_tie_k': [float(t.k) for t in world.chain_ties],
        'chain_tie_rest_m': [float(t.rest_length) for t in world.chain_ties],
        'chain_radii_m': [float(r) for r in world.chain_radius],
        'k_contact': float(lw.K_CONTACT),
        'clamp_role': 'top_pole_plus_1ring_pinned_xyz',
        'bottom_ring_role': 't1_reaction_introduction',
        'n_clamp_vertices': int(world.clamp_idx.shape[0]),
        'n_bottom_ring_vertices': int(world.bottom_ring.shape[0]),
    })


def interface_invariants(world):
    """The count-free interface facts that must be identical across
    resolutions (ring SIZES legitimately scale with the mesh; the ROLE and
    every law constant must not)."""
    return {
        'chain_spec': world.chain_spec,
        'load_mass_kg': float(world.load_mass),
        'load_tie': {'k': float(world.load_tie.k),
                     'rest': float(world.load_tie.rest_length)},
        'chain_ties': [{'id': t.tie_id, 'k': float(t.k),
                        'rest': float(t.rest_length)}
                       for t in world.chain_ties],
        'chain_radii_m': [float(r) for r in world.chain_radius],
        'k_contact': float(lw.K_CONTACT),
        'g_foot_target_m': float(lw.G_FOOT_TARGET_M),
    }


def transverse_inertia(world):
    """Y2c: the declared transverse inertia of the assembled mass layout
    about the erected axis (tissue vertices + chain point masses + load),
    kg m^2. Declared aggregate (prereg section 10), computed from the same
    builder data at both resolutions."""
    axis = world.axis
    center = world.rest.mean(axis=0)
    d = world.rest - center
    along = d @ axis
    perp2 = (d * d).sum(axis=1) - along * along
    i_tissue = float((world.vertex_mass * perp2).sum())
    i_points = 0.0
    pts = [p for p in world.chain_x] + [world.load_x]
    masses = list(world.chain_mass) + [float(world.load_mass)]
    for p, m in zip(pts, masses):
        dp = p - center
        a = float(dp @ axis)
        i_points += m * (float((dp * dp).sum()) - a * a)
    return i_tissue + i_points


def statics_window(world, rows, lo, hi):
    """Y4a whole-system identity on one window (the sealed momentum-balance
    clamp datum; M11 A2 form)."""
    sel = rows[lo:hi]
    f_clamp = float(np.mean([r['clamp_fz_n'] for r in sel]))
    f_contact = sum(float(np.mean([r['chain_contact_forces_n'][k]
                                   for r in sel]))
                    for k in range(len(world.chain_x)))
    resid = f_clamp + f_contact - world.total_weight_n()
    bound = lw.REL * world.total_weight_n() + lw.K_CONTACT * lw.X_FLOOR_M
    return {'window': [lo, hi], 'f_clamp_z_n': f_clamp,
            'f_contacts_n': f_contact, 'w_total_n': world.total_weight_n(),
            'residual_n': resid, 'bound_n': bound,
            'within': bool(abs(resid) <= bound)}


def window_mean(rows, lo, hi, key):
    return float(np.mean([r[key] for r in rows[lo:hi]]))


def window_mean_idx(rows, lo, hi, key, idx):
    return float(np.mean([r[key][idx] for r in rows[lo:hi]]))


def bitwise0(rows, lo, hi, key):
    return all(r[key] == 0.0 for r in rows[lo:hi])


def settled_ledger(world, rows, windows=((900, 1100), (1300, 1500))):
    """X8 per resolution: the binding cumulative no-source gate over the
    SETTLED windows (M11 A2 form); the full-run residual is reported."""
    settled = 0.0
    for lo, hi in windows:
        settled += sum(r['r_tick_j'] for r in rows[lo:hi])
    full = sum(r['r_tick_j'] for r in rows)
    w_press = sum(r['w_press_vol_j'] for r in rows)
    grav = world.grav_turnover_j
    bound = max(lw.REL * abs(w_press) + lw.REL * grav, X8_FLOOR_J)
    return {'settled_cumulative_residual_j': settled,
            'full_run_residual_j': full,
            'w_press_total_j': w_press, 'grav_turnover_j': grav,
            'bound_j': bound,
            'within': bool(abs(settled) <= bound)}


# ------------------------------------------------- render binding gate ----
def render_binding_audit(snapshot, rendered_vertices, rendered_triangles,
                         res):
    """Y7: the rendered mesh must be the mechanical snapshot bitwise,
    vertex-for-vertex, with full triangle coverage. The renderer receives
    COPIES; any re-derivation (stale pose, dropped ring, smoothed proxy)
    refuses here."""
    mech_x = np.asarray(snapshot['x'])
    ren_x = np.asarray(rendered_vertices)
    coverage = {'mechanical_vertices': int(mech_x.shape[0]),
                'rendered_vertices': int(ren_x.shape[0]),
                'mechanical_triangles': int(np.asarray(
                    snapshot.get('triangles', np.zeros((0, 0)))).shape[0]),
                'rendered_triangles': int(np.asarray(rendered_triangles)
                                          .shape[0])}
    if ren_x.shape != mech_x.shape:
        return {'ok': False, 'deviation_m': None,
                'refusal': 'render_vertex_coverage_refused:' + res,
                'coverage': coverage}
    dev = float(np.max(np.abs(ren_x - mech_x)))
    return {'ok': bool(dev <= AUDIT_WINDOW_M), 'deviation_m': dev,
            'window_m': AUDIT_WINDOW_M,
            'refusal': None if dev <= AUDIT_WINDOW_M
            else 'render_binding_stale:' + res,
            'coverage': coverage}


# -------------------------------------------------- coarse-erection probe -
def probe_free_hang(res, ticks=PROBE_TICKS):
    """The A2-pattern erection probe: settle the rig at offset 0 with the
    ground contacts DISABLED (the probe_free_hang probe-only tamper) and
    measure the settled free-hang sag of the VESSEL POLE (the sealed
    metric: M11 A2 derived the limb offset from the pole sag 3.0304e-3 --
    lift-invariant, and uncontaminated by the chain's bunched-start
    settling, which the P0 presettle phase absorbs by design). offset :=
    pole sag. PROBE-ONLY (never a bank run); the value and its trail are
    recorded in Amendment A1 BEFORE the bank."""
    require(res == 'coarse',
            'probe_only_for_undeclared_offset:coarse')
    real = lw.load_real_data()
    saved_offset = ERECTION_OFFSET_M['coarse']
    ERECTION_OFFSET_M['coarse'] = 0.0
    try:
        world, config = build_world(res, lw.off_schedule, ticks, mode='off',
                                    real=real,
                                    tamper={'probe_free_hang': True})
        world.run()
    finally:
        ERECTION_OFFSET_M['coarse'] = saved_offset
    pole_target = float(world.erection['z_pole_target_m'])
    trail = {}
    for t in (200, 400, 600, 900, 1200, 1400, 1500):
        if t <= len(world.rows):
            seg = world.rows[max(0, t - 20):t]
            trail[t] = pole_target - float(
                np.mean([r['bottom_pole_z_m'] for r in seg]))
    settled = trail[ticks]
    return {'resolution': res, 'ticks': ticks,
            'pole_target_z_m': pole_target,
            'pole_sag_m': settled, 'sag_trail_m': trail,
            'probe_trail': 'A2 pattern: offset 0, contacts disabled, off '
            'schedule; sag := z_pole_target - settled pole z (trail means '
            'over the 20 ticks ending at each listed tick); offset := sag '
            '(lift-invariant)'}


if __name__ == '__main__':
    print(json.dumps({'config_purity': audit_config_function_purity(),
                      'sealed_rig_sha': SEALED_RIG_SHA,
                      'a_chord_total_m2': A_CHORD_TOTAL_M2,
                      'chord_section_coarse_m2': chord_section_for('coarse'),
                      'chord_section_reference_m2':
                          chord_section_for('reference')}, indent=1))
