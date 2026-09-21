"""Muscle path geometry derivation for the macaque arm and hindlimb.

Lane brief (2026-09-18, branch lane/muscle-paths-20260918): bridge "we have
PCSA numbers" to "we can compute muscle forces at a pose" by deriving, from
pinned sources only:

  1. ARM PATH EXTRACTION   -- every monkeyArm_current.osim musculotendon path
     (attachment points, conditional via point, wrapping surfaces) as 3D
     coordinates in the body-fixed frames of the same parse_source() model
     that tools/science_funnel/coupled_arm.py consumes, evaluated at the
     neutral pose and at a declared second pose through
     macaque_anatomy.pose_frames().
  2. HINDLIMB PATH ESTIMATION -- Guimaraes 2026 gives fascicle length,
     pennation and PCSA for Macaca mulatta specimen 127 but NO path geometry.
     Simplified straight-line paths are derived from the Oku 2021 (pinned
     fulltext, Table 1) segment lengths plus each muscle's functional group
     (Guimaraes Table 3, pinned fulltext). Every attachment estimate is
     recorded as an assumption.
  3. MOMENT ARMS -- for both limbs, the signed perpendicular distance from
     the joint axis to the muscle's line of action at each pose,
     cross-checked against the exact kinematic quantity r = -dL/dq (central
     differences over the same kinematics; arm only -- the hindlimb has no
     parameterised kinematics, so its arms are the geometric definition
     directly).
  4. FORCE CAPABILITY -- arm: the model's own max_isometric_force; hindlimb:
     PCSA x specific tension with the specific tension DERIVED by least
     squares from the Oku 2021 Table 2 Fmax against the matched Guimaraes
     PCSA groups (mass-adjusted, per-group ratios published). Torque =
     force x moment arm; envelope = signed sum over muscles.
  5. VALIDATION -- (a) |r_geometric - r_fd| within the declared tolerance,
     cylinder-wrap contact sanity, and the measured length jump across the
     conditional point's range boundary; (b) the hindlimb envelope must
     cover the Oku 2021 walking joint torques after the declared mass
     adjustment; margins reported per joint and direction.

RULE-0 MEMBRANES (stated before the run):
  ARM  -- STATEMENT: via-point-resolved straight paths plus analytic cylinder
          wrapping reproduce the source model's moving-length behaviour;
          every non-cylinder wrap contact (ellipsoid/torus) leaves the
          straight length a declared lower bound with per-contact error
          bounded by r_eff*(pi-2).
          PREDICTION (unmeasured): at every pose, for every muscle whose
          resolved path has NO active wrap contact, |r_geometric -
          (-dL/dq)| is zero up to finite-difference error (declared
          tolerance 1e-6 m); for muscles WITH an active wrap contact the
          perpendicular distance is advisory only -- the tangent exit point
          slides on the cylinder as q changes, so -dL/dq (virtual work) is
          the authoritative moment arm and the difference is reported, not
          enforced. No resolved path endpoint lies inside a wrap cylinder.
          FALSIFIER: any straight-path tolerance violation, any endpoint
          inside a wrap cylinder, or a length jump across the conditional
          point's range boundary larger than the declared 5 mm bound marks
          this record false for that muscle; such a muscle's numbers must
          not be used for force computation.
  HIND -- STATEMENT: straight-line paths from Oku segment lengths +
          Guimaraes functional groups put enough physiological
          cross-sectional area around each walking joint to cover the Oku
          2021 walking torques under the derived specific tension.
          PREDICTION (unmeasured): envelope/required-torque ratio >= 1 at
          hip, knee and ankle after mass adjustment.
          FALSIFIER: any joint direction whose conservative envelope (worst
          side across the two poses) fails coverage by more than the
          declared 25% moment-arm uncertainty marks the estimated paths
          false for that joint direction.

Run from the repository root with the project Python:
  python -m tools.science_funnel.validation.muscle_paths_20260918.derive_muscle_paths

Scope: offline derivation only. No activation dynamics, no tendon compliance,
no time integration, no runtime actuation, and no claim that the estimated
hindlimb attachments reproduce dissection geometry.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from tools.science_funnel.macaque_anatomy import (DATA as ARM_DATA, ROOT,
                                                  frame, parse_source,
                                                  pose_frames, rotation)

GUIM_DIR = ROOT / 'tools/science_funnel/data/guimaraes_arch'
OKU_DIR = ROOT / 'tools/science_funnel/data/oku_bipedal'

# Oku 2021 (PMC7940622 fulltext, pinned) Table 1: limb segment dimensions (m).
OKU_SEGMENTS_M = {'thigh': 0.163, 'shank': 0.182, 'foot': 0.074,
                  'phalanges': 0.045}
OKU_SEGMENT_MASS_KG = {'HAT': 8.184, 'thigh': 0.557, 'shank': 0.269,
                       'foot': 0.080, 'phalanges': 0.021}
OKU_TOTAL_MASS_KG = (OKU_SEGMENT_MASS_KG['HAT']
                     + 2.0 * (OKU_SEGMENT_MASS_KG['thigh']
                              + OKU_SEGMENT_MASS_KG['shank']
                              + OKU_SEGMENT_MASS_KG['foot']
                              + OKU_SEGMENT_MASS_KG['phalanges']))
# Guimaraes Information sheet: Macaca mulatta specimen 127, body mass 8 kg.
GUIM_BODY_MASS_KG = 8.0
MASS_RATIO_MULATTA_OVER_FUSCATA = GUIM_BODY_MASS_KG / OKU_TOTAL_MASS_KG
# Oku 2021 Table 2: muscle groups -> Fmax (N), fuscata, from Ogihara et al.
OKU_FMAX_N = {'IL': 642, 'GMED': 738, 'VAS': 2514, 'TA': 390, 'SOL': 822,
              'RF': 720, 'BIFl': 804, 'GAS': 720, 'EDL': 140, 'FDL': 180}

FD_STEP_RAD = 1.0e-4
MOMENT_ARM_TOL_M = 1.0e-6
CONDITIONAL_JUMP_BOUND_M = 0.005
COVERAGE_MARGIN_FRACTION = 0.25
TANGENT_EPS = 1.0e-12


def _unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > TANGENT_EPS else v


# ---------------------------------------------------------------- arm kinematics

def arm_poses(model):
    """Neutral = source defaults; walking = midpoint of each unlocked range."""
    neutral = {name: c['default_rad'] for name, c in model['coordinates'].items()}
    walking = {}
    for name, c in model['coordinates'].items():
        walking[name] = (c['default_rad'] if c['locked']
                         else sum(c['range_rad']) / 2.0)
    return neutral, walking


def _values(model, base, coordinate, delta):
    values = dict(base)
    values[coordinate] = values.get(coordinate,
                                    model['coordinates'][coordinate]['default_rad']) + delta
    return values


def joint_axis_world(model, values, coordinate):
    """World origin + instantaneous world axis of one coordinate at a pose.

    CustomJoint rotation axes compose in body-fixed order (rotation1 first),
    so the instantaneous world direction of rotation_k is
    P * R1(q1) * ... * R_{k-1}(q_{k-1}) * axis_k: the prior axes of the SAME
    joint are composed with their CURRENT pose values. All axes pass through
    the joint frame origin (source translation axes are constant zero here;
    they are composed anyway for correctness).
    """
    frames = pose_frames(model, values)

    def value_of(ax):
        coeff = ax['function']['coefficients']
        if ax['function']['type'] == 'Constant':
            return coeff[0]
        q = values.get(ax['coordinate'],
                       model['coordinates'][ax['coordinate']]['default_rad'])
        return coeff[0] * q + coeff[1]

    for body in model['bodies']:
        j = body['joint']
        if not j:
            continue
        if not any(ax['coordinate'] == coordinate
                   and ax['name'].startswith('rotation') for ax in j['axes']):
            continue
        P = frames[j['parent']] @ frame(j['parent_location_m'],
                                        j['parent_orientation_rad'])
        R = np.eye(3)
        shift = np.zeros(3)
        for ax in j['axes']:
            if ax['name'].startswith('translation'):
                shift += np.asarray(ax['axis'], dtype=float) * value_of(ax)
                continue
            if ax['coordinate'] == coordinate:
                local = R @ np.asarray(ax['axis'], dtype=float)
                return {'body': body['name'],
                        'origin': P[:3, 3] + P[:3, :3] @ shift,
                        'axis': _unit(P[:3, :3] @ local)}
            R = R @ rotation(np.asarray(ax['axis'], dtype=float), value_of(ax))
    raise ValueError('coordinate has no rotation axis: %s' % coordinate)


def conditional_active(point, values):
    if point['type'] != 'ConditionalPathPoint':
        return True
    q = values[point['coordinate']]
    lo, hi = point['range_rad']
    return lo <= q <= hi


def _parent_of(model, name):
    for body in model['bodies']:
        if body['name'] == name:
            return body['joint']['parent'] if body['joint'] else None
    return None


def _on_child_side(model, name, child):
    node = name
    while node is not None:
        if node == child:
            return True
        node = _parent_of(model, node)
    return False


def spanning_segment(model, values, coordinate, points):
    """First resolved path segment whose endpoints straddle the coordinate's
    joint (proximal endpoint on a body that is NOT at/below the joint's child,
    distal endpoint on a body that is)."""
    child = joint_axis_world(model, values, coordinate)['body']
    for i in range(len(points) - 1):
        a = _on_child_side(model, points[i]['body'], child)
        b = _on_child_side(model, points[i + 1]['body'], child)
        if a != b:
            return i
    return None


# ------------------------------------------------------------------- wrapping

def _wrap_geometry(body, name):
    for rec in body['wrap_objects']:
        if rec['attributes'].get('name') == name:
            # OpenSim stores wrap-object parameters as child elements; only
            # the object name is an XML attribute.
            attrs = dict(rec['attributes'])
            for child in rec['children']:
                if not child['children'] and child['text']:
                    attrs[child['tag']] = child['text']
            rot = [float(x) for x in attrs['xyz_body_rotation'].split()]
            trans = [float(x) for x in attrs['translation'].split()]
            geom = {'name': name, 'tag': rec['tag'],
                    'quadrant': attrs.get('quadrant', 'all'),
                    'to_body': frame(trans, rot), 'body': body['name']}
            if rec['tag'] == 'WrapCylinder':
                geom['radius_m'] = float(attrs['radius'])
                geom['length_m'] = float(attrs['length'])
            elif rec['tag'] == 'WrapSphere':
                geom['radius_m'] = float(attrs['radius'])
            elif rec['tag'] == 'WrapEllipsoid':
                geom['dimensions_m'] = [float(x)
                                        for x in attrs['dimensions'].split()]
            elif rec['tag'] == 'WrapTorus':
                geom['inner_radius_m'] = float(attrs['inner_radius'])
                geom['outer_radius_m'] = float(attrs['outer_radius'])
            return geom
    raise ValueError('wrap object not found: %s' % name)


def _all_wrap_geometries(model):
    out = {}
    for body in model['bodies']:
        for rec in body['wrap_objects']:
            geom = _wrap_geometry(body, rec['attributes'].get('name'))
            out[geom['name']] = geom
    return out


def _quadrant_ok(quadrant, direction_body):
    if quadrant == 'all':
        return True
    axes = {'x': 0, 'y': 1, 'z': 2}
    for i in range(0, len(quadrant) - 1, 2):
        sign, key = quadrant[i], quadrant[i + 1]
        value = direction_body[axes[key]]
        if sign == '-' and value > 0:
            return False
        if sign == '+' and value < 0:
            return False
    return True


def _angle_in(phi, lo, span):
    return (phi - lo) % (2.0 * math.pi) <= span + 1e-12


def _plane_basis(axis):
    """Orthonormal in-plane basis (u, v) with plane angles measured as
    atan2(dot(v, basis_v), dot(v, basis_u)) -- the reference direction is the
    projection of the body x-axis (y-axis when the axis is parallel to x)."""
    if abs(float(axis @ np.array([1.0, 0.0, 0.0]))) < 0.9:
        basis_u = _unit(np.array([1.0, 0.0, 0.0])
                        - float(axis @ np.array([1.0, 0.0, 0.0])) * axis)
    else:
        basis_u = _unit(np.array([0.0, 1.0, 0.0])
                        - float(axis @ np.array([0.0, 1.0, 0.0])) * axis)
    return basis_u, np.cross(axis, basis_u)


def _plane_angle(v, axis):
    basis_u, basis_v = _plane_basis(axis)
    vp = _perp(v, axis)
    return math.atan2(float(vp @ basis_v), float(vp @ basis_u))


def wrap_cylinder(p1, p2, geom, forced=False):
    """Analytic tangent wrap of the segment p1->p2 about a Z-aligned cylinder.

    Both points are in the wrap BODY frame. Returns (exit1, exit2, arc_rad,
    mid_direction_body) or None when there is no contact, or the string
    'ENDPOINT_INSIDE' when a path endpoint lies inside the cylinder (source
    semantics violated -> falsifier). Axial components of the endpoints are
    preserved on their own side, matching OpenSim's tangent-line semantics;
    arcs are limited to <= pi (tangent-method rule).

    forced=True (frozen-topology finite differences): when the strict contact
    test fails, fall back to the tangency-limit construction so the wrapped
    length stays a continuous function of q across contact thresholds.
    """
    to_body = geom['to_body']
    center = to_body[:3, 3]
    axis = _unit(to_body[:3, :3] @ np.array([0.0, 0.0, 1.0]))
    half = geom['length_m'] / 2.0
    radius = geom['radius_m']
    if abs(float((p1 - center) @ axis)) > half or \
            abs(float((p2 - center) @ axis)) > half:
        return None
    e = [_perp(p1 - center, axis), _perp(p2 - center, axis)]
    z = [float((p1 - center) @ axis), float((p2 - center) @ axis)]
    rho = [float(np.linalg.norm(v)) for v in e]
    if rho[0] < radius - 1e-12 or rho[1] < radius - 1e-12:
        return 'ENDPOINT_INSIDE'
    d = e[1] - e[0]
    dd = float(d @ d)
    t = 0.0 if dd < TANGENT_EPS else min(1.0, max(0.0, -float(e[0] @ d) / dd))
    closest = e[0] + t * d
    if not forced and float(np.linalg.norm(closest)) >= radius:
        return None
    phi_c = _plane_angle(closest, axis)
    basis_u, basis_v = _plane_basis(axis)
    phis = [_plane_angle(v, axis) for v in e]
    alphas = [math.acos(min(1.0, radius / r)) for r in rho]
    best = None
    fallback = None
    for s1 in (1.0, -1.0):
        for s2 in (1.0, -1.0):
            a1 = phis[0] + s1 * alphas[0]
            a2 = phis[1] - s2 * alphas[1]
            ccw = (a2 - a1) % (2.0 * math.pi)
            for lo, span in ((a1, ccw), (a1 - (2.0 * math.pi - ccw),
                                         2.0 * math.pi - ccw)):
                if span <= TANGENT_EPS or span > math.pi + 1e-9:
                    continue
                mid = lo + span / 2.0
                direction = (math.cos(mid) * basis_u
                             + math.sin(mid) * basis_v)
                if fallback is None or span < fallback[2]:
                    fallback = (a1, a2, span, direction)
                if not _angle_in(phi_c, lo, span):
                    continue
                if best is None or span < best[2]:
                    best = (a1, a2, span, direction)
    chosen = best if best is not None else (fallback if forced else None)
    if chosen is None:
        return None
    a1, a2, span, direction = chosen
    if not _quadrant_ok(geom['quadrant'], to_body[:3, :3].T @ direction):
        return None
    exits = []
    for angle, zcomp in ((a1, z[0]), (a2, z[1])):
        radial = math.cos(angle) * basis_u + math.sin(angle) * basis_v
        exits.append(center + axis * zcomp + radius * radial)
    return exits[0], exits[1], span, direction


def _perp(v, axis):
    return v - (v @ axis) * axis


def obstacle_misses(p1_body, p2_body, geom):
    """Conservative contact test for an UNRESOLVED wrap object.

    Ellipsoids are tested exactly in normalized space (an ellipsoid there);
    spheres/tori are tested against a sphere of the outer (or only) radius.
    True = the straight segment stays clear, so no wrap contact is possible.
    """
    inv = np.linalg.inv(geom['to_body'])
    q1 = (inv @ np.r_[p1_body, 1.0])[:3]
    q2 = (inv @ np.r_[p2_body, 1.0])[:3]
    d = q2 - q1
    dd = float(d @ d)
    if geom['tag'] == 'WrapEllipsoid':
        dims = np.asarray(geom['dimensions_m'])
        if np.any(dims <= 0):
            raise ValueError('degenerate ellipsoid dimensions')
        s1, s2 = q1 / dims, q2 / dims
        sd = (s2 - s1) / dims
        a = float(sd @ sd)
        b = 2.0 * float(s1 @ sd)
        c = float(s1 @ s1) - 1.0
        disc = b * b - 4.0 * a * c
        if disc < 0.0:
            return True
        root = math.sqrt(disc)
        for t in ((-b - root) / (2.0 * a), (-b + root) / (2.0 * a)):
            if 0.0 <= t <= 1.0:
                return False
        return True
    radius = geom.get('outer_radius_m') or geom.get('radius_m')
    if dd < TANGENT_EPS:
        return float(np.linalg.norm(q1)) >= radius
    t = min(1.0, max(0.0, -float(q1 @ d) / dd))
    return float(np.linalg.norm(q1 + t * d)) >= radius


def _r_eff_bound(geom):
    """(pi-2)*r bound on |arc - chord| per contacting segment."""
    if geom['tag'] == 'WrapTorus':
        r = geom['outer_radius_m']
    elif geom['tag'] in ('WrapSphere', 'WrapCylinder'):
        r = geom['radius_m']
    else:
        r = max(geom['dimensions_m']) / 2.0
    return r * (math.pi - 2.0)


# ------------------------------------------------------------------ arm paths

def resolve_arm_path(model, values, muscle, wrap_geometries, inactive_points=None,
                     wrap_plan=None, conditional_plan=None):
    """Path points (body frame + world) at a pose with conditional resolution
    and analytic cylinder wrapping; unresolved obstacles get a conservative
    per-contact length-error bound r_eff*(pi-2).

    inactive_points forces named path points out of the path (measures the
    conditional-point jump without leaving the source coordinate range).
    wrap_plan / conditional_plan FREEZE the contact and activation decisions
    of a base resolution so finite differences differentiate smooth geometry
    instead of contact-state switches: wrap_plan maps cylinder names to
    active booleans (forced tangency-limit solve keeps active wraps
    continuous); conditional_plan maps path point names to booleans."""
    frames = pose_frames(model, values)
    resolved = []
    for point in muscle['points']:
        if inactive_points and point.get('name') in inactive_points:
            continue
        active = conditional_active(point, values)
        if conditional_plan is not None:
            active = conditional_plan.get(point.get('name'), active)
        if not active:
            continue
        T = frames[point['body']]
        resolved.append({'body': point['body'],
                         'location_m': [float(x) for x in point['location_m']],
                         'world': (T @ np.r_[np.asarray(point['location_m'],
                                                            dtype=float),
                                             1.0])[:3],
                         'kind': point['type']})
    wrap_events = []
    unresolved = []
    for wrap in muscle['wraps']:
        children = {c['tag']: (c['text'] or '').strip() for c in wrap['children']}
        name = children.get('wrap_object')
        if not name:
            raise ValueError('PathWrap without wrap_object on %s' % muscle['name'])
        geom = wrap_geometries[name]
        if geom['tag'] != 'WrapCylinder':
            unresolved.append({'wrap_object': name, 'tag': geom['tag'],
                               'body': geom['body'],
                               'treatment': 'unresolved; straight length is a '
                                            'lower bound within the recorded '
                                            'error bound'})
            continue
        if wrap_plan is not None and not wrap_plan.get(name, False):
            continue
        forced = wrap_plan is not None and wrap_plan.get(name, False)
        best = None
        for i in range(len(resolved) - 1):
            inv = np.linalg.inv(frames[geom['body']])
            p1 = (inv @ np.r_[resolved[i]['world'], 1.0])[:3]
            p2 = (inv @ np.r_[resolved[i + 1]['world'], 1.0])[:3]
            outcome = wrap_cylinder(p1, p2, geom, forced=forced)
            if outcome == 'ENDPOINT_INSIDE':
                raise ValueError('path endpoint inside wrap cylinder %s on %s'
                                 % (name, muscle['name']))
            if outcome is None:
                continue
            e1, e2, arc, direction = outcome
            if best is None or arc > best[2]:
                best = (i, e1, e2, arc, direction)
        if best is None:
            continue
        i, e1, e2, arc, direction = best
        T = frames[geom['body']]
        exit1 = {'body': geom['body'], 'location_m': e1.tolist(),
                 'world': (T @ np.r_[e1, 1.0])[:3], 'kind': 'WrapContact'}
        exit2 = {'body': geom['body'], 'location_m': e2.tolist(),
                 'world': (T @ np.r_[e2, 1.0])[:3], 'kind': 'WrapContact'}
        follower = resolved[i + 1]
        resolved[i + 1:i + 2] = [exit1, exit2, follower]
        wrap_events.append({'wrap_object': name, 'body': geom['body'],
                            'arc_rad': arc,
                            'entry_body_m': e1.tolist(),
                            'exit_body_m': e2.tolist()})
    for entry in unresolved:
        geom = wrap_geometries[entry['wrap_object']]
        contacts = 0
        inv = np.linalg.inv(frames[geom['body']])
        for i in range(len(resolved) - 1):
            p1 = (inv @ np.r_[resolved[i]['world'], 1.0])[:3]
            p2 = (inv @ np.r_[resolved[i + 1]['world'], 1.0])[:3]
            if not obstacle_misses(p1, p2, geom):
                contacts += 1
        entry['segments_contacting'] = contacts
        entry['length_lower_bound_error_m'] = contacts * _r_eff_bound(geom)
    length = sum(float(np.linalg.norm(resolved[i + 1]['world']
                                      - resolved[i]['world']))
                 for i in range(len(resolved) - 1))
    return {'points': resolved, 'wrap_events': wrap_events,
            'unresolved_wraps': unresolved, 'length_m': length}


def muscle_length(model, values, muscle, wrap_geometries, **kwargs):
    return resolve_arm_path(model, values, muscle, wrap_geometries,
                            **kwargs)['length_m']


def moment_arms_fd(model, values, muscle, coordinates, wrap_geometries):
    """r = -dL/dq by central differences with the base pose's contact and
    conditional topology frozen (differentiating smooth geometry, not
    contact-state switches)."""
    base = resolve_arm_path(model, values, muscle, wrap_geometries)
    wrap_plan = {e['wrap_object']: True for e in base['wrap_events']}
    for u in base['unresolved_wraps']:
        wrap_plan.setdefault(u['wrap_object'], False)
    conditional_plan = {p.get('name'): conditional_active(p, values)
                        for p in muscle['points']
                        if p['type'] == 'ConditionalPathPoint'}
    arms = {}
    for coord in coordinates:
        l_hi = muscle_length(model, _values(model, values, coord, +FD_STEP_RAD),
                             muscle, wrap_geometries, wrap_plan=wrap_plan,
                             conditional_plan=conditional_plan)
        l_lo = muscle_length(model, _values(model, values, coord, -FD_STEP_RAD),
                             muscle, wrap_geometries, wrap_plan=wrap_plan,
                             conditional_plan=conditional_plan)
        arms[coord] = -(l_hi - l_lo) / (2.0 * FD_STEP_RAD)
    return arms


def geometric_arm(p_line, direction, axis_origin, axis_dir):
    """Signed perpendicular distance from the joint axis to the line of
    action, signed to match the kinematic convention r = -dL/dq (positive =
    the muscle pulls the distal side in the coordinate's + rotational sense).

    For a single segment spanning the joint whose proximal endpoint is fixed
    under the coordinate, -dL/dq = -u.(d x (p2-o)) equals -u.(d x (p1-o))
    exactly (any point on the line gives the same magnitude), so this equals
    the FD quantity up to finite-difference error."""
    v = p_line - axis_origin
    return -float(axis_dir @ np.cross(v, _unit(direction)))


def derive_arm(model, poses=None):
    coordinates = sorted(k for k, v in model['coordinates'].items()
                         if not v['locked'])
    if poses is None:
        neutral, walking = arm_poses(model)
        poses = {'neutral': neutral, 'walking': walking}
    wrap_geometries = _all_wrap_geometries(model)
    out = {}
    for pose_name, values in poses.items():
        axis_cache = {c: joint_axis_world(model, values, c) for c in coordinates}
        muscles = {}
        for muscle in model['muscles']:
            resolved = resolve_arm_path(model, values, muscle, wrap_geometries)
            arms_fd = moment_arms_fd(model, values, muscle, coordinates,
                                     wrap_geometries)
            geom = {}
            for coord in coordinates:
                idx = spanning_segment(model, values, coord, resolved['points'])
                if idx is None:
                    geom[coord] = None
                    continue
                axis = axis_cache[coord]
                p1, p2 = resolved['points'][idx], resolved['points'][idx + 1]
                geom[coord] = geometric_arm(p1['world'],
                                            p2['world'] - p1['world'],
                                            axis['origin'], axis['axis'])
            wrapped = bool(resolved['wrap_events'])
            consistency = {c: (None if geom[c] is None else
                               abs(arms_fd[c] - geom[c]))
                           for c in coordinates}
            enforcement = ('straight_path_exact' if not wrapped
                           else 'advisory_contact_slide')
            force_n = float(muscle['parameters_source_text']['max_isometric_force'])
            muscles[muscle['name']] = {
                'points_body_frame': [{'body': p['body'],
                                       'location_m': p['location_m'],
                                       'kind': p['kind']}
                                      for p in resolved['points']],
                'points_world_m': [[float(x) for x in p['world']]
                                   for p in resolved['points']],
                'wrap_events': resolved['wrap_events'],
                'unresolved_wraps': resolved['unresolved_wraps'],
                'length_m': resolved['length_m'],
                'moment_arm_fd_m': arms_fd,
                'moment_arm_geometric_m': geom,
                'arm_consistency_m': consistency,
                'arm_consistency_enforcement': enforcement,
                'moment_arm_authoritative': ('geometric_equal_fd' if not wrapped
                                             else 'fd_virtual_work; geometric '
                                                  'is advisory because the '
                                                  'tangent exit point slides '
                                                  'with q'),
                'max_isometric_force_N': force_n,
                'torque_N_m_at_pose': {c: arms_fd[c] * force_n
                                       for c in coordinates},
            }
        envelope = {}
        for coord in coordinates:
            envelope[coord] = {
                'positive_N_m': sum(max(m['torque_N_m_at_pose'][coord], 0.0)
                                    for m in muscles.values()),
                'negative_N_m': sum(min(m['torque_N_m_at_pose'][coord], 0.0)
                                    for m in muscles.values()),
            }
        out[pose_name] = {'values_rad': values, 'muscles': muscles,
                          'torque_envelope_N_m': envelope,
                          'note': 'positive envelope = total capability '
                                  'driving the coordinate in its + direction; '
                                  'negative likewise for the - direction'}
    return out


def conditional_jump(model, wrap_geometries):
    """Measured length jump across each conditional point's activation edge.

    The via point activates inside its recorded coordinate range; crossing the
    edge swaps path-through-via against the straight neighbour connection. The
    edges may coincide with the source coordinate range, so the outside state
    is evaluated by deactivating the point at the neutral pose instead of
    moving the pose out of the model's range."""
    jumps = []
    neutral, _ = arm_poses(model)
    for muscle in model['muscles']:
        for point in muscle['points']:
            if point['type'] != 'ConditionalPathPoint':
                continue
            lo, hi = point['range_rad']
            inside = dict(neutral)
            inside[point['coordinate']] = min(max(neutral[point['coordinate']], lo),
                                              hi)
            l_in = muscle_length(model, inside, muscle, wrap_geometries)
            l_out = resolve_arm_path(model, inside, muscle, wrap_geometries,
                                     inactive_points={point.get('name')})['length_m']
            jumps.append({'muscle': muscle['name'],
                          'coordinate': point['coordinate'],
                          'range_rad': [lo, hi],
                          'evaluated_rad': inside[point['coordinate']],
                          'length_inside_m': l_in,
                          'length_outside_m': l_out,
                          'jump_m': abs(l_in - l_out)})
    return jumps


# ------------------------------------------------------------- hindlimb side

# Attachment landmarks for the straight-line hindlimb paths. (segment, u, v):
# u along the segment from its proximal joint, v perpendicular in the sagittal
# plane (+ = anterior), both in segment-length units; pelvis landmarks are
# (anterior(+)/posterior(-), height) offsets in thigh units from the hip joint.
# Every row is an ESTIMATE grounded in the muscle's known action per the
# Guimaraes Table 3 functional grouping; none is a dissection measurement.
HINDLIMB_ANATOMY = {
    'GMax':   {'origin': ('pelvis', -0.35, 0.20), 'insertion': ('thigh', 0.30, -0.08),
               'groups': ['hip_extensors']},
    'BFL':    {'origin': ('pelvis', -0.40, 0.12), 'insertion': ('thigh', 0.95, -0.05),
               'groups': ['hip_extensors', 'knee_flexors']},
    'ST':     {'origin': ('pelvis', -0.42, 0.10), 'insertion': ('shank', 0.10, -0.06),
               'groups': ['hip_extensors']},
    'SM':     {'origin': ('pelvis', -0.40, 0.10), 'insertion': ('shank', 0.08, -0.05),
               'groups': ['hip_extensors']},
    'ILI':    {'origin': ('pelvis', 0.20, 0.35), 'insertion': ('thigh', 0.10, 0.05),
               'groups': ['hip_flexors']},
    'GMed':   {'origin': ('pelvis', 0.00, 0.40), 'insertion': ('thigh', 0.05, 0.05),
               'groups': ['hip_abductors']},
    'GMin':   {'origin': ('pelvis', 0.05, 0.30), 'insertion': ('thigh', 0.08, 0.03),
               'groups': ['hip_abductors']},
    'PIRI':   {'origin': ('pelvis', -0.30, 0.02), 'insertion': ('thigh', 0.04, -0.04),
               'groups': ['hip_abductors', 'hip_rotators']},
    'AM':     {'origin': ('pelvis', -0.05, 0.15), 'insertion': ('thigh', 0.60, -0.05),
               'groups': ['hip_adductors']},
    'AL':     {'origin': ('pelvis', -0.02, 0.12), 'insertion': ('thigh', 0.40, -0.04),
               'groups': ['hip_adductors']},
    'PECT':   {'origin': ('pelvis', 0.00, 0.10), 'insertion': ('thigh', 0.25, -0.03),
               'groups': ['hip_adductors']},
    'GRA':    {'origin': ('pelvis', -0.25, 0.05), 'insertion': ('shank', 0.85, -0.04),
               'groups': ['hip_adductors', 'knee_flexors']},
    'GemSup': {'origin': ('pelvis', -0.20, 0.05), 'insertion': ('thigh', 0.03, -0.02),
               'groups': ['hip_rotators']},
    'GemInf': {'origin': ('pelvis', -0.28, 0.00), 'insertion': ('thigh', 0.03, -0.02),
               'groups': ['hip_rotators']},
    'ObtExt': {'origin': ('pelvis', -0.32, 0.00), 'insertion': ('thigh', 0.03, -0.02),
               'groups': ['hip_rotators']},
    'VI':     {'origin': ('thigh', 0.45, 0.02), 'insertion': ('shank', 0.08, 0.07),
               'groups': ['knee_extensors']},
    'VL':     {'origin': ('thigh', 0.55, -0.06), 'insertion': ('shank', 0.08, 0.07),
               'groups': ['knee_extensors']},
    'VM':     {'origin': ('thigh', 0.55, 0.06), 'insertion': ('shank', 0.08, 0.07),
               'groups': ['knee_extensors']},
    'POP':    {'origin': ('thigh', 0.98, -0.04), 'insertion': ('shank', 0.05, -0.04),
               'groups': ['knee_flexors']},
    'PLANT':  {'origin': ('thigh', 0.97, -0.05), 'insertion': ('foot', -0.12, -0.04),
               'groups': ['knee_flexors']},
    'SOL':    {'origin': ('shank', 0.20, -0.08), 'insertion': ('foot', -0.15, -0.05),
               'groups': ['ankle_plantarflexors']},
    'MG':     {'origin': ('thigh', 0.97, -0.06), 'insertion': ('foot', -0.15, -0.05),
               'groups': ['ankle_plantarflexors']},
    'LG':     {'origin': ('thigh', 0.95, -0.06), 'insertion': ('foot', -0.15, -0.05),
               'groups': ['ankle_plantarflexors']},
    'PB':     {'origin': ('shank', 0.45, -0.05), 'insertion': ('foot', 0.85, -0.02),
               'groups': ['ankle_plantarflexors']},
    'PL':     {'origin': ('shank', 0.40, -0.06), 'insertion': ('foot', 0.90, -0.04),
               'groups': ['ankle_plantarflexors']},
    'TA':     {'origin': ('shank', 0.15, 0.07), 'insertion': ('foot', 0.90, 0.02),
               'groups': ['ankle_dorsiflexors']},
    'EHL':    {'origin': ('shank', 0.50, 0.05), 'insertion': ('foot', 1.00, 0.02),
               'groups': ['ankle_dorsiflexors']},
    'EDL':    {'origin': ('shank', 0.25, 0.06), 'insertion': ('foot', 0.95, 0.01),
               'groups': ['ankle_dorsiflexors']},
    'FDL':    {'origin': ('shank', 0.55, -0.06), 'insertion': ('toe', 0.50, 0.00),
               'groups': ['mtp_flexors']},
    'FHL':    {'origin': ('shank', 0.80, -0.05), 'insertion': ('toe', 0.50, 0.00),
               'groups': ['mtp_flexors']},
}

# Hindlimb joints: thigh and shank vertical, foot horizontal (plantigrade
# standing); the foot segment runs ankle -> MTP (tarsometatarsus), then the
# phalanges segment MTP -> toe.
HIND_JOINT_ORDER = ('hip', 'knee', 'ankle', 'mtp', 'toe')
# Moment-arm sign convention per joint, in a flexion+ reading (positive arm =
# the muscle's pull produces flexion-direction moment):
#   hip flexion+ (thigh anterior), knee flexion+ (shank posterior),
#   ankle PLANTARFLEXION+ (foot rotates plantarward), mtp flexion+.
_HIND_SIGNS = {'hip': -1.0, 'knee': +1.0, 'ankle': +1.0, 'mtp': +1.0}


def hindlimb_joints(pose):
    """Sagittal 2D joint centres (x anterior, y up) for 'neutral'/'walking'.

    walking = Oku 2021 mid-stance (x=0.50 of the cycle, before alteration):
    hip angle -0.027 rad and knee angle -0.860 rad in the Oku sign convention
    (positive = hip flexion, knee EXTENSION), i.e. 0.860 rad knee flexion;
    foot held flat on the ground (assumption recorded: Oku's raw ankle-angle
    reading is NOT applied because its anatomical zero is not published --
    the shank-foot angle emerges from the foot-flat closure instead).
    """
    thigh = OKU_SEGMENTS_M['thigh']
    shank = OKU_SEGMENTS_M['shank']
    foot = OKU_SEGMENTS_M['foot']
    phal = OKU_SEGMENTS_M['phalanges']
    if pose == 'neutral':
        hip = np.array([0.0, 0.0])
        knee = hip + np.array([0.0, -thigh])
        ankle = knee + np.array([0.0, -shank])
        mtp = ankle + np.array([foot, 0.0])
        toe = mtp + np.array([phal, 0.0])
    elif pose == 'walking':
        hip_angle = -0.027
        knee_flexion = 0.860
        hip = np.array([0.0, 0.0])
        thigh_dir = np.array([math.sin(hip_angle), -math.cos(hip_angle)])
        knee = hip + thigh * thigh_dir
        shank_angle = hip_angle - knee_flexion
        shank_dir = np.array([math.sin(shank_angle), -math.cos(shank_angle)])
        ankle = knee + shank * shank_dir
        mtp = ankle + np.array([foot, 0.0])
        toe = mtp + np.array([phal, 0.0])
    else:
        raise ValueError('unknown hindlimb pose %s' % pose)
    return {'hip': hip, 'knee': knee, 'ankle': ankle, 'mtp': mtp, 'toe': toe}


def _segment_axis(joints, segment):
    thigh = OKU_SEGMENTS_M['thigh']
    shank = OKU_SEGMENTS_M['shank']
    if segment == 'thigh':
        return joints['hip'], _unit(joints['knee'] - joints['hip']), thigh
    if segment == 'shank':
        return joints['knee'], _unit(joints['ankle'] - joints['knee']), shank
    if segment == 'foot':
        return joints['ankle'], _unit(joints['mtp'] - joints['ankle']), OKU_SEGMENTS_M['foot']
    if segment == 'toe':
        return joints['mtp'], _unit(joints['toe'] - joints['mtp']), OKU_SEGMENTS_M['phalanges']
    raise ValueError('unknown segment %s' % segment)


def attachment_point(joints, segment, u, v):
    if segment == 'pelvis':
        # (u, v) = (anterior(+)/posterior(-), height) in thigh units, hip origin.
        return joints['hip'] + np.array([u, v]) * OKU_SEGMENTS_M['thigh']
    origin, direction, length = _segment_axis(joints, segment)
    perp = np.array([-direction[1], direction[0]])  # left of direction = anterior
    return origin + u * length * direction + v * length * perp


def hindlimb_path(joints, name):
    spec = HINDLIMB_ANATOMY[name]
    return (attachment_point(joints, *spec['origin']),
            attachment_point(joints, *spec['insertion']))


_SEGMENT_RANK = {'pelvis': 0, 'thigh': 1, 'shank': 2, 'foot': 3, 'toe': 4}
_JOINT_BOUNDARY = {'hip': 1, 'knee': 2, 'ankle': 3, 'mtp': 4}


def hindlimb_spanned_joints(name):
    """Joints the muscle actually crosses: its straight line of action loads
    only the segments distal of a boundary its attachments straddle. A muscle
    with both attachments on the same side of a joint exerts NO systematic
    moment about that joint, so its arm there is None (never summed)."""
    spec = HINDLIMB_ANATOMY[name]
    lo = _SEGMENT_RANK[spec['origin'][0]]
    hi = _SEGMENT_RANK[spec['insertion'][0]]
    if lo > hi:
        lo, hi = hi, lo
    return [joint for joint, boundary in _JOINT_BOUNDARY.items()
            if lo < boundary <= hi]


def hindlimb_moment_arms(joints, name):
    origin, insertion = hindlimb_path(joints, name)
    direction = _unit(insertion - origin)
    spanned = set(hindlimb_spanned_joints(name))
    arms = {}
    for joint in ('hip', 'knee', 'ankle', 'mtp'):
        if joint not in spanned:
            arms[joint] = None
            continue
        r = joints[joint] - origin
        cross = direction[0] * r[1] - direction[1] * r[0]
        arms[joint] = _HIND_SIGNS[joint] * cross
    return arms


def load_guimaraes_mulatta():
    """Admitted-adapter read of the pinned S1 xlsx -> {muscle: fields}."""
    from tools.science_funnel import adapters_muscle
    raw = (GUIM_DIR / 'AJPA-190-e70329-s001.xlsx').read_bytes()
    rows = adapters_muscle.guimaraes_arch(raw, {}, 'AJPA-190-e70329-s001.xlsx')
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
        table.setdefault(parts[2], {})[parts[4]] = payload['value_si']
    return table, quarantined


def load_oku_torques():
    """Signed peak joint torques over the cycle, before alteration.

    Returns {joint: (max, min)} in N*m under the Oku sign convention
    (positive = hip flexion, knee extension, ankle dorsiflexion)."""
    from tools.science_funnel import adapters_muscle
    raw = (OKU_DIR / '42003_2021_1831_MOESM2_ESM.xlsx').read_bytes()
    rows = adapters_muscle.oku_bipedal_series(
        raw, {}, '42003_2021_1831_MOESM2_ESM.xlsx')
    signed = {}
    for row in rows:
        if 'payload' not in row:
            raise ValueError('oku series refused: %s' % row.get('location'))
        payload = row['payload']
        if payload['conditions']['block'] != 'before_alteration':
            continue
        label = payload['subject']
        if not label.endswith('torque'):
            continue
        joint = label.split()[0].lower()
        values = [s['value'] for s in payload['samples']]
        entry = signed.setdefault(joint, {'max': -1e30, 'min': 1e30})
        entry['max'] = max(entry['max'], max(values))
        entry['min'] = min(entry['min'], min(values))
    return {j: (v['max'], v['min']) for j, v in signed.items()}


def derive_specific_tension(table):
    """Least-squares specific tension from matched Oku Fmax vs Guimaraes PCSA.

    Matching groups (Oku Table 2 muscle note vs Guimaraes muscles):
    IL->ILI, GMED->GMed, VAS->VI+VL+VM, TA->TA, SOL->SOL, GAS->MG+LG,
    EDL->EDL, FDL->FDL. Oku Fmax belongs to the fuscata model
    (total mass 10.038 kg); forces are mass-adjusted to the 8 kg mulatta by
    the body-mass ratio (force ~ mass at constant tissue stress). Per-group
    implied tensions are published so the spread stays visible; the slope
    hides nothing.
    """
    groups = {'IL': ['ILI'], 'GMED': ['GMed'], 'VAS': ['VI', 'VL', 'VM'],
              'TA': ['TA'], 'SOL': ['SOL'], 'GAS': ['MG', 'LG'],
              'EDL': ['EDL'], 'FDL': ['FDL']}
    ratio = MASS_RATIO_MULATTA_OVER_FUSCATA
    rows, num, den = [], 0.0, 0.0
    for group, members in groups.items():
        pcsa = sum(table[m]['pcsa_m2'] for m in members)
        force = OKU_FMAX_N[group] * ratio
        rows.append({'oku_group': group, 'guimaraes_muscles': members,
                     'pcsa_m2': pcsa, 'oku_fmax_N': OKU_FMAX_N[group],
                     'mass_adjusted_fmax_N': force,
                     'implied_tension_Pa': force / pcsa})
        num += force * pcsa
        den += pcsa * pcsa
    slope = num / den
    return {'specific_tension_Pa': slope,
            'specific_tension_N_per_cm2': slope / 1e4,
            'mass_ratio_mulatta_over_fuscata': ratio,
            'oku_total_body_mass_kg': OKU_TOTAL_MASS_KG,
            'guimaraes_body_mass_kg': GUIM_BODY_MASS_KG,
            'method': 'least squares through the origin of mass-adjusted Oku '
                      'Fmax vs matched Guimaraes PCSA sums (8 groups)',
            'groups': rows,
            'implied_tension_range_Pa': [min(r['implied_tension_Pa']
                                             for r in rows),
                                         max(r['implied_tension_Pa']
                                             for r in rows)]}


def derive_hindlimb(table):
    sigma = derive_specific_tension(table)
    poses = {}
    for pose in ('neutral', 'walking'):
        joints = hindlimb_joints(pose)
        muscles = {}
        for name in HINDLIMB_ANATOMY:
            if name not in table:
                raise ValueError('mulatta table lacks %s' % name)
            record = table[name]
            spec = HINDLIMB_ANATOMY[name]
            origin, insertion = hindlimb_path(joints, name)
            length = float(np.linalg.norm(insertion - origin))
            arms = hindlimb_moment_arms(joints, name)
            pcsa = record['pcsa_m2']
            pennation = record.get('penn_deg')
            cos_p = math.cos(pennation) if pennation is not None else 1.0
            force = pcsa * sigma['specific_tension_Pa'] * cos_p
            muscles[name] = {
                'origin_point_m': origin.tolist(),
                'insertion_point_m': insertion.tolist(),
                'origin_landmark_segment_u_v': list(spec['origin']),
                'insertion_landmark_segment_u_v': list(spec['insertion']),
                'functional_groups': spec['groups'],
                'spanned_joints': hindlimb_spanned_joints(name),
                'straight_length_m': length,
                'measured_mtu_length_m': record.get('musc_len'),
                'measured_fascicle_length_m': record.get('fl_m'),
                'pcsa_m2': pcsa,
                'pennation_rad': pennation,
                'pennation_treatment': 'guimaraes recorded' if pennation is not None
                                       else 'missing; cos(p)=1 upper bound used',
                'cos_pennation': cos_p,
                'max_force_N': force,
                'moment_arms_m_flexion_positive': arms,
                'torque_N_m_at_pose': {j: (None if arms[j] is None
                                           else force * arms[j]) for j in arms},
            }
        envelope = {}
        for joint in ('hip', 'knee', 'ankle', 'mtp'):
            torques = [m['torque_N_m_at_pose'][joint] for m in muscles.values()
                       if m['torque_N_m_at_pose'][joint] is not None]
            envelope[joint] = {
                'flexion_positive_N_m': sum(max(t, 0.0) for t in torques),
                'flexion_negative_N_m': sum(min(t, 0.0) for t in torques),
                'contributing_muscles': len(torques),
            }
        poses[pose] = {'joints_m': {k: v.tolist() for k, v in joints.items()},
                       'muscles': muscles, 'torque_envelope_N_m': envelope}
    return {'specific_tension': sigma, 'poses': poses,
            'sign_convention': 'moment arms are flexion-positive per joint: '
                               'hip flexion+, knee flexion+, ankle '
                               'PLANTARFLEXION+, mtp flexion+; envelopes sum '
                               'muscle torques (force x arm) on each side'}


def validate_hindlimb(hind):
    """Coverage of the Oku walking torques by the conservative envelope.

    Required torque at the 8 kg mulatta = Oku signed peak x mass ratio
    (dynamics scale ~ mass at fixed posture; paths use unscaled Oku segment
    lengths, so no length factor is applied -- recorded assumption).
    Capability = the WORST (smaller absolute) envelope side across the two
    derived poses, read on the matching side of the flexion+ convention.
    Falsifier margin: a ratio < 1 fails; the declared uncertainty is
    COVERAGE_MARGIN_FRACTION of the required torque.
    """
    ratio = MASS_RATIO_MULATTA_OVER_FUSCATA
    oku = load_oku_torques()
    required = {
        'hip_extension': abs(min(0.0, oku['hip'][1])) * ratio,
        'hip_flexion': max(0.0, oku['hip'][0]) * ratio,
        'knee_extension': max(0.0, oku['knee'][0]) * ratio,
        'knee_flexion': abs(min(0.0, oku['knee'][1])) * ratio,
        'ankle_plantarflexion': abs(min(0.0, oku['ankle'][1])) * ratio,
        'ankle_dorsiflexion': max(0.0, oku['ankle'][0]) * ratio,
        'mtp_flexion': abs(min(0.0, oku['mp'][1])) * ratio,
    }
    side = {'hip_extension': ('hip', 'flexion_negative_N_m'),
            'hip_flexion': ('hip', 'flexion_positive_N_m'),
            'knee_extension': ('knee', 'flexion_negative_N_m'),
            'knee_flexion': ('knee', 'flexion_positive_N_m'),
            'ankle_plantarflexion': ('ankle', 'flexion_positive_N_m'),
            'ankle_dorsiflexion': ('ankle', 'flexion_negative_N_m'),
            'mtp_flexion': ('mtp', 'flexion_positive_N_m')}
    results = {}
    for key, need in required.items():
        joint, field = side[key]
        caps = [abs(hind['poses'][p]['torque_envelope_N_m'][joint][field])
                for p in hind['poses']]
        capability = min(caps)
        results[key] = {'required_N_m': need, 'envelope_N_m': capability,
                        'ratio': (capability / need) if need > 0 else None,
                        'margin_N_m': capability - need,
                        'within_declared_uncertainty':
                            capability >= need * (1.0 - COVERAGE_MARGIN_FRACTION)}
    return {'oku_signed_peak_torques_N_m': {k: list(v) for k, v in oku.items()},
            'mass_ratio_mulatta_over_fuscata': ratio,
            'declared_uncertainty_fraction': COVERAGE_MARGIN_FRACTION,
            'coverage': results}


# ------------------------------------------------------------------ assembly

def _sha_of_pinned(data_dir, names):
    receipt = json.loads((data_dir / 'download_receipt.json')
                         .read_text(encoding='utf-8'))
    by_path = {f['path']: f for f in receipt.get('files', [])}
    out = {}
    for name in names:
        entry = by_path.get(name, {})
        raw = (data_dir / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if entry.get('sha256') not in (None, digest):
            raise ValueError('pin drift: %s' % name)
        out[name] = {'sha256': digest, 'bytes': len(raw),
                     'receipt_sha256': entry.get('sha256')}
    return out


def source_pins():
    return {
        'macaque_arm': _sha_of_pinned(ARM_DATA, ['monkeyArm_current.osim']),
        'guimaraes_arch': _sha_of_pinned(GUIM_DIR,
                                         ['AJPA-190-e70329-s001.xlsx',
                                          'PMC13425262_fulltext.xml']),
        'oku_bipedal': _sha_of_pinned(OKU_DIR,
                                      ['42003_2021_1831_MOESM2_ESM.xlsx',
                                       'PMC7940622_fulltext.xml']),
    }


def _jsonable(obj):
    """Recursively convert numpy scalars/arrays to plain JSON types."""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _jsonable(obj.tolist())
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return float(obj)
    return obj


def derive_all(output_dir):
    model, receipt = parse_source()
    arm = derive_arm(model)
    wrap_geometries = _all_wrap_geometries(model)
    jumps = conditional_jump(model, wrap_geometries)
    table, quarantined = load_guimaraes_mulatta()
    hind = derive_hindlimb(table)
    coverage = validate_hindlimb(hind)

    worst = 0.0
    violations = []
    for pose, record in arm.items():
        for muscle, data in record['muscles'].items():
            if data['arm_consistency_enforcement'] != 'straight_path_exact':
                continue
            for coord, delta in data['arm_consistency_m'].items():
                if delta is None:
                    continue
                worst = max(worst, delta)
                if delta > MOMENT_ARM_TOL_M:
                    violations.append({'pose': pose, 'muscle': muscle,
                                       'coordinate': coord, 'delta_m': delta})
    jump_violations = [j for j in jumps if j['jump_m'] > CONDITIONAL_JUMP_BOUND_M]
    neutral, walking = arm_poses(model)
    hind_failures = {k: v for k, v in coverage['coverage'].items()
                     if not v['within_declared_uncertainty']}
    deliverable = {
        'schema': 'chimera.muscle_path_geometry.v1',
        'derived_from': {
            'arm_model': {'source_revision': receipt['revision'],
                          'graph_object': 'model.anatomy.macaque_arm'},
            'guimaraes_arch': 'tools/science_funnel/data/guimaraes_arch '
                              '(pinned bytes; sha256 in source_pins)',
            'oku_bipedal': 'tools/science_funnel/data/oku_bipedal (pinned '
                           'bytes; sha256 in source_pins)',
            'batch_receipt': 'tools/science_funnel/validation/'
                             'batch_muscle_20260917/receipt.json (these bytes '
                             'passed the batch membrane 2026-09-17: 1908 '
                             'guimaraes + 40 oku records, count identity '
                             'closed)',
        },
        'source_pins': source_pins(),
        'units': {'length': 'm', 'force': 'N', 'torque': 'N*m',
                  'moment_arm': 'm (torque per N)', 'angle': 'rad',
                  'pcsa': 'm^2', 'specific_tension': 'Pa'},
        'method': {
            'arm': 'paths from parse_source() of the pinned .osim (the same '
                   'source-transform model coupled_arm.py consumes); '
                   'conditional path point active inside its recorded range; '
                   'analytic tangent wrapping for WrapCylinder (Z-aligned in '
                   'the wrap frame, quadrant rule, arc <= pi); ellipsoid and '
                   'torus contacts remain UNRESOLVED and contribute only the '
                   'conservative bound r_eff*(pi-2) per contacting segment; '
                   'moment arms computed twice: signed perpendicular distance '
                   'from the joint axis to the joint-spanning segment line of '
                   'action, and -dL/dq by central differences (step '
                   '%g rad) over the same kinematics' % FD_STEP_RAD,
            'hindlimb': 'straight-line paths from Oku 2021 Table 1 segment '
                        'lengths + Guimaraes Table 3 functional groups; '
                        'attachment landmarks are estimates recorded per '
                        'muscle; force = PCSA * derived specific tension * '
                        'cos(pennation)',
        },
        'poses': {
            'arm': {'neutral': {'values_rad': neutral,
                                'basis': 'source model defaults'},
                    'walking': {'values_rad': walking,
                                'basis': 'midpoint of each unlocked coordinate '
                                         'range in the source model (no taste '
                                         'constant)'}},
            'hindlimb': {'neutral': {'basis': 'plantigrade standing, all '
                                             'joint angles 0',
                                     'joints_m': {
                                         k: v.tolist() for k, v in
                                         hindlimb_joints('neutral').items()}},
                         'walking': {'basis': 'Oku 2021 mid-stance (x=0.50 of '
                                              'the cycle, before alteration): '
                                              'hip -0.027 rad, knee flexion '
                                              '0.860 rad, foot flat '
                                              '(assumption; Oku ankle-angle '
                                              'zero not published)',
                                     'joints_m': {
                                         k: v.tolist() for k, v in
                                         hindlimb_joints('walking').items()}}},
        },
        'arm': arm,
        'hindlimb': hind,
        'validation': {
            'arm': {
                'moment_arm_tolerance_m': MOMENT_ARM_TOL_M,
                'fd_step_rad': FD_STEP_RAD,
                'worst_fd_vs_geometric_m': worst,
                'violations': violations,
                'conditional_point_jumps': jumps,
                'conditional_jump_bound_m': CONDITIONAL_JUMP_BOUND_M,
                'conditional_jump_violations': jump_violations,
            },
            'hindlimb': coverage,
        },
        'falsifier_verdicts': {
            'arm_consistency': ('held' if not violations else 'falsified'),
            'conditional_continuity': ('held' if not jump_violations
                                       else 'falsified'),
            'hindlimb_torque_coverage': ('held' if not hind_failures
                                         else 'falsified: %s'
                                              % sorted(hind_failures)),
        },
        'quarantined_guimaraes_rows': quarantined,
        'unknowns': [
            'non-cylinder wrap contacts (ellipsoid/torus) are not resolved; '
            'straight lengths are lower bounds and wrapped muscles keep a '
            'conservative moment-arm uncertainty within the recorded bound',
            'arm pose "walking" is a range-midpoint surrogate, not a recorded '
            'quadrupedal stance',
            'hindlimb attachment landmarks are anatomical estimates, not '
            'dissection measurements; the walking-pose ankle is set by the '
            'foot-flat closure, not by the unpublished Oku ankle zero',
            'the specific tension is a derived group slope with wide '
            'per-group residuals (published); muscles absent from the fit '
            'inherit it without independent support',
            'Oku 2021 is a simulation of Macaca fuscata; the mass adjustment '
            'assumes torque scales with body mass at fixed posture',
            'no activation dynamics, tendon compliance, force-length/velocity '
            'or time integration is implied by any number in this record',
        ],
        'scope': 'Offline derivation record bridging admitted architecture '
                 'data to muscle force/torque capability at two declared '
                 'poses per limb. Not runtime actuation, not biological '
                 'verification, not a whole-animal claim.',
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / 'muscle_path_geometry.json'
    deliverable = _jsonable(deliverable)
    path.write_text(json.dumps(deliverable, indent=1, sort_keys=True) + '\n',
                    encoding='utf-8')
    return deliverable, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    deliverable, path = derive_all(args.output)
    summary = {
        'output': str(path),
        'arm_muscles': len(deliverable['arm']['neutral']['muscles']),
        'hindlimb_muscles': len(deliverable['hindlimb']['poses']['neutral']['muscles']),
        'arm_worst_consistency_m':
            deliverable['validation']['arm']['worst_fd_vs_geometric_m'],
        'hindlimb_coverage': {k: v['ratio'] for k, v in
                              deliverable['validation']['hindlimb']['coverage'].items()},
        'specific_tension_N_per_cm2':
            deliverable['hindlimb']['specific_tension']['specific_tension_N_per_cm2'],
        'falsifier_verdicts': deliverable['falsifier_verdicts'],
    }
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
