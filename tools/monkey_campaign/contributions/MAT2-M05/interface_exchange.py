"""MAT2-M05: explicit physical contact, bond and release interfaces.

Implements the frozen preregistration (PREREGISTRATION.md, this directory):
two bodies exchange pressure/contact and bonded tension/shear through
IDENTIFIED interfaces (declared region ports), bond removal removes its
restoring forces bitwise and permits separation except for remaining contact,
shared faces and mass are counted once, and every interface transfer is
equal/opposite in loads AND moments (Newton's third law at the interface).

Upstream authority, reused verbatim and unmodified:
- tools/monkey_campaign/contributions/MAT2-M01/material_state.py
  (chimera.material_state.v1 validator; schema authority; contact/bond
  relation vocabulary; single-owner matter),
- tools/monkey_campaign/contributions/MAT2-M03/pressure_membrane.py
  (Membrane closure/lumping utilities, XPBD scaffold pattern with measured
  constraint-projection residual),
- tools/monkey_campaign/contributions/MAT2-M04/passive_response.py
  (strain-gate/ledger discipline: named refusals before state update).

Laws honoured: bonds are explicit (M01: "containment never creates a bond";
card falsifier: "a spatial neighbor is automatically bonded" must be
refused); the interface transfers equal/opposite loads and moments; the
shared interface face and shared matter are counted once.

CPU-only; stdlib + numpy; deterministic (no stochastic inputs anywhere).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))
sys.path.insert(0, str(HERE.parent / 'MAT2-M03'))

import material_state  # noqa: E402  (M01 validator, unmodified)
import pressure_membrane as pm  # noqa: E402  (M03 Membrane utilities)

XHAT = np.array([1.0, 0.0, 0.0])

# Declared scenario constants (PREREGISTRATION.md, laws 1-4, 8; correction A1).
K_CONTACT_PA_PER_M = 1.0e5      # contact penalty stiffness (Pa per m of gap)
C_CONTACT_N_S_PER_M = 12.0      # normal contact damping (N*s/m; correction A1)
K_TENSION_N_PER_M = 60.0        # bond tension stiffness
K_SHEAR_N_PER_M = 40.0          # bond shear stiffness
K_TWIST_N_M_PER_RAD = 0.8       # bond twist couple stiffness
BOND_REST_LENGTH_M = 0.0        # zero-rest-length tie (tension-only)
MASS_A_KG = 0.050               # mat_a, owner body_a
MASS_B_KG = 0.020               # mat_b, owner body_b
MASS_IFACE_KG = 0.002           # mat_iface, owner body_a, reference body_b
SUPPORT_A = True                # body A declared fixed support (visible)
DAMPING_B_PER_S = 8.0           # global velocity damping on B (correction A1)
DT_S = 1.0 / 300.0              # fixed 300 Hz physical tick (pinned)
XPBD_COMPLIANCE_M_PER_N = 1.0e-5
XPBD_ITERATIONS = 8
TILT_REFUSAL_M = 3.0e-3         # transverse anchor offset refusal bound
INTERFACE_SUBSTEPS = 32         # stiff interface-load substeps (correction A1:
# free-flight scaffold violation energy per substep scales with h^2; at
# h = dt/32 the projection churn and residual drop below 1e-2 of turnover)

# Declared actuator schedule on body B (ticks 1..23; tick 0 is rest;
# correction A1): squeeze 1..5, pull 6..10, release at 11 (pull continues
# 11..13), approach 14..23.
SCHEDULE = {1: -2.0, 2: -2.0, 3: -2.0, 4: -2.0, 5: -2.0,
            6: 2.0, 7: 2.0, 8: 2.0, 9: 2.0, 10: 2.0,
            11: 2.0, 12: 2.0, 13: 2.0,
            14: -6.0, 15: -6.0, 16: -6.0, 17: -6.0, 18: -6.0, 19: -6.0,
            20: -6.0, 21: -6.0, 22: -6.0, 23: -6.0}
RELEASE_TICK = 11               # explicit bond release (PREREGISTRATION law 4)

REFUSAL_AUTO_BOND = 'auto_bond_refused'
REFUSAL_CONTACT_UNDECLARED = 'contact_interface_undeclared'
REFUSAL_BOND_NOT_BOUND = 'bond_not_bound'
REFUSAL_BOND_ALREADY_BOUND = 'bond_already_bound'
REFUSAL_RELEASE_UNBOUND = 'release_of_unbound_bond'
REFUSAL_TILT = 'interface_tilt_exceeded'


def require(condition, code):
    """Named refusal; no numeric inference or repair."""
    if not condition:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------- geometry ----

def trapezoid_base_yz():
    """Interface trapezoid corners (y, z): (0,0), (0.2,0), (0.15,0.1), (0,0.1).

    Split into two UNEQUAL triangles (PREREGISTRATION law 1); areas derived:
    A1 = 0.0100 m^2, A2 = 0.0075 m^2, shared face A_iface = 0.0175 m^2.
    """
    return [(0.0, 0.0), (0.2, 0.0), (0.15, 0.1), (0.0, 0.1)]


def face_centroid_yz():
    """Area centroid of the trapezoid (derived: area-weighted triangle means)."""
    corners = trapezoid_base_yz()
    c1 = [(corners[0][i] + corners[1][i] + corners[2][i]) / 3.0 for i in (0, 1)]
    c2 = [(corners[0][i] + corners[2][i] + corners[3][i]) / 3.0 for i in (0, 1)]
    a1, a2 = 0.0100, 0.0075
    return [(a1 * c1[i] + a2 * c2[i]) / (a1 + a2) for i in (0, 1)]


class Body:
    """A pentahedron: trapezoid interface base + apex; XPBD scaffold body.

    Base vertices 0..3 lie in the plane x = base_x; vertex 4 is the apex.
    Triangles carry outward winding (asserted by M03 closure). The interface
    face is triangles 0 and 1 (the base split), with areas A1 > A2.
    """

    def __init__(self, body_id, base_x, apex_depth, mass_partition, fixed):
        require(isinstance(body_id, str) and body_id.strip(), 'body_id')
        yz = trapezoid_base_yz()
        yc, zc = face_centroid_yz()
        apex_x = base_x - apex_depth          # apex behind the base plane
        self.body_id = body_id
        self.base_x = float(base_x)
        self.vertices = np.array([
            [base_x, yz[0][0], yz[0][1]],
            [base_x, yz[1][0], yz[1][1]],
            [base_x, yz[2][0], yz[2][1]],
            [base_x, yz[3][0], yz[3][1]],
            [apex_x, yc, zc]], dtype=np.float64)
        # base split (interface) then four apex side faces; winding fixed below
        tris = [[0, 1, 2], [0, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
        self.iface_vids = (0, 1, 2, 3)
        centroid = self.vertices.mean(axis=0)
        oriented = []
        for tri in tris:
            v = self.vertices[tri]
            n = np.cross(v[1] - v[0], v[2] - v[0])
            if float(np.dot(n, v.mean(axis=0) - centroid)) < 0.0:
                tri = [tri[0], tri[2], tri[1]]
            oriented.append(tri)
        self.triangles = np.array(oriented, dtype=np.int64)
        self.rest = self.vertices.copy()
        self.membrane = pm.Membrane(self.rest, self.triangles, body_id)
        self.membrane.require_closed()
        self.fixed = bool(fixed)
        if fixed:
            self.masses = np.zeros(5)
            self.inv_masses = np.zeros(5)
        else:
            require(all(m > 0.0 and math.isfinite(m)
                        for m in mass_partition), 'mass_partition_invalid')
            self.masses = np.array(mass_partition, dtype=np.float64)
            self.inv_masses = 1.0 / self.masses
        self.x = self.vertices.copy()
        self.v = np.zeros_like(self.x)
        # interface bookkeeping
        iface_areas = [float(self.membrane.areas[i]) for i in (0, 1)]
        self.iface_areas = np.array(iface_areas, dtype=np.float64)
        self.iface_area = float(self.iface_areas.sum())
        for n in self.membrane.normals[:2]:
            require(np.all(n == np.sign(n[0]) * XHAT), 'iface_normal_not_x')
        # declared port anchor: material point at the rest shared-face
        # centroid, tracked by the MEAN BODY TRANSLATION (correction A1);
        # face bending changes the traction partition (current areas,
        # measured) but not the port kinematics.
        rest_areas = self.iface_areas
        rest_m = self.membrane
        self.rest_anchor = (rest_areas[0] * rest_m.centroids[0]
                            + rest_areas[1] * rest_m.centroids[1]) \
            / self.iface_area
        self.rest_mean = self.rest.mean(axis=0)

    def mean_translation(self):
        return self.x.mean(axis=0) - self.rest_mean

    def scaffold_energy(self):
        """Scaffold strain energy of the free body (correction A1).

        U = sum_edges (|d| - rest)^2 / (2 * alpha): the potential of the
        compliance constraints; the XPBD projection exchanges work with this
        reservoir, so the ledger must carry it (measured, never hidden).
        """
        total = 0.0
        for (a1, a2), rest in zip(self.edge_list, self.rest_lengths):
            length = float(np.linalg.norm(self.x[a2] - self.x[a1]))
            total += (length - rest) ** 2 / (2.0 * XPBD_COMPLIANCE_M_PER_N)
        return total

    def current_iface_areas(self):
        """Current interface triangle areas (deformation measured, law 2)."""
        m = pm.Membrane(self.x, self.triangles, self.body_id)
        return np.array([m.areas[0], m.areas[1]])

    @property
    def anchor(self):
        """Declared port anchor: rest shared-face centroid + mean translation."""
        return self.rest_anchor + self.mean_translation()

    def distribute_to_iface(self, force, areas=None):
        """Point force at the anchor -> per-vertex loads (exact resultant).

        Split across the two interface triangles with an exact complement on
        the second share (bitwise resultant), then equal thirds per triangle.
        `areas` overrides the partition (the shared-face partition of the
        supported body is used so both sides split identically).
        """
        a = self.iface_areas if areas is None else np.asarray(areas, float)
        total = float(a.sum())
        share0 = force * (a[0] / total)
        share1 = force - share0
        loads = np.zeros_like(self.x)
        for tri, share in ((self.triangles[0], share0),
                           (self.triangles[1], share1)):
            for vid in tri:
                loads[vid] += share / 3.0
        return loads


def build_bodies(gap=0.0):
    """Bodies at the declared initial gap (0 = coincident interface faces)."""
    body_a = Body('body_a', base_x=0.0, apex_depth=0.16, mass_partition=None,
                  fixed=SUPPORT_A)
    body_b = Body('body_b', base_x=gap, apex_depth=-0.16,
                  mass_partition=[MASS_B_KG / 5.0] * 5, fixed=False)
    return body_a, body_b


# ---------------------------------------------------------------- contact ----

class ContactInterface:
    """Declared unilateral penalty contact through IDENTIFIED ports.

    p = k_c * max(0, -g); traction per interface triangle is area-scaled and
    bitwise-reciprocal (law 2). States are the M01 contact vocabulary.
    """

    def __init__(self, contact_id, body_a, body_b, ports):
        require(isinstance(contact_id, str) and contact_id.strip(),
                'contact_id')
        self.contact_id = contact_id
        self.body_a = body_a
        self.body_b = body_b
        self.ports = dict(ports)          # {'body_a': port_id, 'body_b': ...}
        self.declared = True

    def gap(self):
        """Signed separation along the declared interface normal (+x opens)."""
        return float(self.body_b.anchor[0] - self.body_a.anchor[0])

    def normal_speed(self):
        return float(self.body_b.v[:, 0].mean())

    def state(self):
        g = self.gap()
        if g > 0.0:
            return 'separated'
        return 'loaded' if self.pressure() > 0.0 else 'touching'

    def pressure(self):
        require(self.declared, REFUSAL_CONTACT_UNDECLARED)
        return K_CONTACT_PA_PER_M * max(0.0, -self.gap())

    def tractions(self):
        """Per-triangle contact resultants: +x on B, bitwise negatives on A.

        The shared-face partition is the SUPPORTED body's (fixed) face areas,
        so both sides use bitwise-identical magnitudes (law 2); the free
        body's face-area drift is measured and reported by the run.
        """
        require(self.declared, REFUSAL_CONTACT_UNDECLARED)
        p = self.pressure()
        partition = self.body_a.current_iface_areas()
        f_b = p * partition[:, None] * XHAT
        f_a = -f_b                       # bitwise negatives (same floats)
        return f_a, f_b, p

    def shared_partition(self):
        return self.body_a.current_iface_areas()

    def damping_dissipation(self, damping_work_j):
        """Measured dissipation of the contact damping force (correction A1).

        The continuum law is Q = c_n * v_n^2 * dt; the discrete account
        measures Q as the NEGATIVE of the damping-force work over the tick
        (trapezoid displacement), which is the same quantity to O(dt^2) and
        stays consistent with the applied loads. A within-tick velocity
        reversal can make the measured value negative; it is reported as
        measured (the cumulative account is reported alongside).
        """
        return -damping_work_j

    def damping_force_on_b(self):
        """Declared normal damping force on B while loaded (-x opposes v_n)."""
        if self.state() == 'loaded':
            return -C_CONTACT_N_S_PER_M * self.normal_speed() * XHAT
        return np.zeros(3)

    def stored_energy(self):
        """Penalty-contact stored energy 0.5 * p^2 / k_c * A_iface."""
        p = self.pressure()
        return 0.5 * p * p / K_CONTACT_PA_PER_M * self.body_a.iface_area


# ------------------------------------------------------------------- bond ----

class BondElement:
    """Declared tension/shear/twist element between two IDENTIFIED ports.

    Tension-only along the declared axis (zero force in compression); shear
    and twist restore transversely/rotationally; transfers='force_moment'
    (M01 vocabulary). Release removes ALL restoring contributions bitwise
    (law 3-4).
    """

    def __init__(self, bond_id, body_a, body_b, ports, transfers='force_moment'):
        require(transfers in ('force', 'force_moment'), 'bond_transfers')
        self.bond_id = bond_id
        self.body_a = body_a
        self.body_b = body_b
        self.ports = dict(ports)
        self.transfers = transfers
        self.status = 'planned'
        self.bound_tick = None
        self.released_tick = None
        self.e_release_j = None

    def bind(self, tick):
        require(self.status == 'planned', REFUSAL_BOND_ALREADY_BOUND)
        self.status = 'qualified'
        self.bound_tick = int(tick)

    def release(self, tick):
        require(self.status == 'qualified', REFUSAL_RELEASE_UNBOUND)
        require(self.released_tick is None, REFUSAL_RELEASE_UNBOUND)
        self.e_release_j = self.stored_energy()
        self.status = 'released'
        self.released_tick = int(tick)

    @property
    def active(self):
        return self.status == 'qualified'

    def delta(self):
        return self.body_b.anchor - self.body_a.anchor

    def extension(self):
        d = self.delta()
        return float(np.dot(d, XHAT)) - BOND_REST_LENGTH_M

    def shear_offset(self):
        d = self.delta()
        return d - float(np.dot(d, XHAT)) * XHAT

    def tension(self):
        if self.status == 'planned':
            raise ValueError(REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return 0.0
        return K_TENSION_N_PER_M * max(0.0, self.extension())

    def force_on_b(self):
        if self.status == 'planned':
            raise ValueError(REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return np.zeros(3)
        t = self.tension()
        shear = K_SHEAR_N_PER_M * self.shear_offset()
        return -t * XHAT - shear

    def force_on_a(self):
        """Bitwise-negative reaction on body A (law 6)."""
        return -self.force_on_b()

    def twist_couple(self, theta_rad):
        """Element-level couple pair for a declared relative twist (law 3)."""
        if not self.active:
            return 0.0
        return K_TWIST_N_M_PER_RAD * theta_rad

    def stored_energy(self, theta_rad=0.0):
        if self.status == 'planned':
            raise ValueError(REFUSAL_BOND_NOT_BOUND)
        if not self.active:
            return 0.0
        e = max(0.0, self.extension())
        d = self.shear_offset()
        return (0.5 * K_TENSION_N_PER_M * e * e
                + 0.5 * K_SHEAR_N_PER_M * float(np.dot(d, d))
                + 0.5 * K_TWIST_N_M_PER_RAD * theta_rad * theta_rad)


def refuse_auto_bond():
    """Explicit guard: proximity/containment must never create a bond."""
    raise ValueError(REFUSAL_AUTO_BOND)


# -------------------------------------------------------------- inventory ----

def interface_inventory(body_a, body_b, bond_bound):
    """Once-only combined inventory (PREREGISTRATION law 7).

    The shared interface face is counted once (subtracted from the body sum);
    matter mass is counted once via owner/reference roles (the reference is
    listed but NOT re-counted).
    """
    area_a = float(body_a.membrane.surface_area())
    area_b = float(body_b.membrane.surface_area())
    shared = float(body_a.iface_area)
    require(abs(shared - float(body_b.iface_area)) <= 1e-12,
            'shared_face_area_mismatch')
    total_area = area_a + area_b - shared
    mass_rows = [
        {'matter_id': 'mat_a', 'owner_region': 'body_a', 'role': 'owner',
         'mass_kg': MASS_A_KG},
        {'matter_id': 'mat_b', 'owner_region': 'body_b', 'role': 'owner',
         'mass_kg': MASS_B_KG},
        {'matter_id': 'mat_iface', 'owner_region': 'body_a', 'role': 'owner',
         'mass_kg': MASS_IFACE_KG,
         'referenced_by': 'body_b'},
    ]
    total_mass = MASS_A_KG + MASS_B_KG + MASS_IFACE_KG  # reference not counted
    return {'area_body_a_m2': area_a, 'area_body_b_m2': area_b,
            'shared_face_area_m2': shared, 'total_area_m2': total_area,
            'mass_rows': mass_rows, 'total_mass_kg': total_mass,
            'bond_bound': bool(bond_bound)}


# ------------------------------------------------------------ state doc ------

def _geometry_dict(body):
    return {'vertices_m': [[float(c) for c in row] for row in body.rest],
            'triangles': [[int(i) for i in tri]
                          for tri in body.triangles],
            'frame': 'rest'}


def state_document(revision, bodies, contact_state, bond_bound, contained=False):
    """chimera.material_state.v1 document; validated by M01 UNMODIFIED."""
    body_a, body_b = bodies
    regions = [
        {'id': 'body_a', 'kind': 'region', 'parent': None,
         'rest_geometry': _geometry_dict(body_a),
         'current_geometry': _geometry_dict(body_a),
         'matter_claims': [
             {'matter_id': 'mat_a', 'role': 'owner'},
             {'matter_id': 'mat_iface', 'role': 'owner'}],
         'sources': ['MAT2-M05 interface experiment; supported body'],
         'ports': [
             {'id': 'port:seam', 'protocol': 'normal_pressure', 'unit': 'Pa'},
             {'id': 'port:bond_anchor', 'protocol': 'tension_shear_twist',
              'unit': 'N,N*m'}]},
        {'id': 'body_b', 'kind': 'region', 'parent': None,
         'rest_geometry': _geometry_dict(body_b),
         'current_geometry': _geometry_dict(body_b),
         'matter_claims': [
             {'matter_id': 'mat_b', 'role': 'owner'},
             {'matter_id': 'mat_iface', 'role': 'reference'}],
         'sources': ['MAT2-M05 interface experiment; free body'],
         'ports': [
             {'id': 'port:seam', 'protocol': 'normal_pressure', 'unit': 'Pa'},
             {'id': 'port:bond_anchor', 'protocol': 'tension_shear_twist',
              'unit': 'N,N*m'}]},
    ]
    if contained:
        # containment probe: body_b nested in a declared shell; never a bond
        regions.append({'id': 'shell_around_b', 'kind': 'shell',
                        'parent': None,
                        'rest_geometry': {'note': 'declared enclosing shell'},
                        'current_geometry': {'note': 'declared enclosing shell'},
                        'matter_claims': [], 'sources': [], 'ports': []})
        for row in regions:
            if row['id'] == 'body_b':
                row['parent'] = 'shell_around_b'
    doc = {
        'schema': material_state.SCHEMA,
        'revision': int(revision),
        'object_id': 'mat2_m05_interface_rig',
        'regions': regions,
        'matter': [
            {'id': 'mat_a', 'mass_kg': MASS_A_KG,
             'provenance': 'declared body A mass (PREREGISTRATION law 7)'},
            {'id': 'mat_b', 'mass_kg': MASS_B_KG,
             'provenance': 'declared body B mass (PREREGISTRATION law 7)'},
            {'id': 'mat_iface', 'mass_kg': MASS_IFACE_KG,
             'provenance': 'declared shared interface patch; owner body_a, '
                           'reference body_b; counted once'}],
        'directions': [
            {'id': 'dir:seam_normal', 'region_id': 'body_a',
             'axis': [1.0, 0.0, 0.0], 'frame': 'rest', 'history': [
                 {'revision': 0, 'state': 'declared interface normal'}]},
            {'id': 'dir:bond_axis', 'region_id': 'body_b',
             'axis': [1.0, 0.0, 0.0], 'frame': 'rest', 'history': [
                 {'revision': 0, 'state': 'declared bond axis'}]}],
        'laws': [
            {'id': 'law:contact_penalty', 'kind': 'pressure_deformation',
             'regions': ['body_a', 'body_b'],
             'parameters': {'k_c_Pa_per_m': K_CONTACT_PA_PER_M,
                            'c_n_N_s_per_m': C_CONTACT_N_S_PER_M},
             'provenance': 'declared unilateral penalty contact '
                           '(PREREGISTRATION law 2)'},
            {'id': 'law:bond_element', 'kind': 'pressure_deformation',
             'regions': ['body_a', 'body_b'],
             'parameters': {'k_t_N_per_m': K_TENSION_N_PER_M,
                            'k_s_N_per_m': K_SHEAR_N_PER_M,
                            'k_theta_N_m_per_rad': K_TWIST_N_M_PER_RAD,
                            'rest_length_m': BOND_REST_LENGTH_M,
                            'transfers': 'force_moment'},
             'provenance': 'declared bond element (PREREGISTRATION law 3)'}],
        'contacts': [
            {'id': 'contact:ab_seam',
             'endpoints': [
                 {'region_id': 'body_a', 'port': 'port:seam'},
                 {'region_id': 'body_b', 'port': 'port:seam'}],
             'state': contact_state,
             'interface': {'kind': 'planar_seam', 'normal': [1.0, 0.0, 0.0],
                           'shared_face_area_m2': float(body_a.iface_area)}}],
        'bonds': ([] if not bond_bound else [
            {'id': 'bond:strap',
             'endpoints': [
                 {'region_id': 'body_a', 'port': 'port:bond_anchor'},
                 {'region_id': 'body_b', 'port': 'port:bond_anchor'}],
             'status': 'qualified', 'transfers': 'force_moment'}]),
        'provenance': {
            'task': 'MAT2-M05',
            'preregistration': 'PREREGISTRATION.md (this directory)',
            'note': 'revision 1 = bound state; revision 2 = bond released '
                    '(bond relation removed; contact persists)'},
    }
    return doc


def validate_state(doc):
    """Validate with the UNMODIFIED M01 validator; return its summary."""
    return material_state.validate_material_state(doc)


# ------------------------------------------------------------- dynamics -----

def distribute_force_to_vertices(body, force, region='iface'):
    """Vertex loads for a force whose resultant acts at the interface anchor."""
    if region != 'iface':
        raise ValueError('distribution_region_invalid')
    return body.distribute_to_iface(force)


class TwoBodyRun:
    """XPBD scaffold run of the declared interface scenario (law 8, 10)."""

    def __init__(self, bodies, contact, bond):
        self.body_a, self.body_b = bodies
        self.contact = contact
        self.bond = bond
        self.bond.bind(0)
        self._edges = {}
        for body in bodies:
            edges = {}
            for a, b, c in body.triangles.tolist():
                for u, w in ((a, b), (b, c), (c, a)):
                    edges[(min(u, w), max(u, w))] = True
            edges[(1, 3)] = True          # declared second base diagonal brace
            body.edge_list = sorted(edges)
            body.rest_lengths = np.array([
                float(np.linalg.norm(body.rest[a2] - body.rest[a1]))
                for a1, a2 in body.edge_list])
        self.x0_anchor_gap = self.contact.gap()
        self.ticks = []

    def _interface_loads(self):
        """All interface loads as separate vertex-load components.

        Returns, per component (contact traction, contact damping, bond),
        the vertex-load arrays on both bodies plus the resultant force pairs
        used for the reciprocity check. The contact damping reaction acts on
        the supported body (declared; law 2), so the interface pair stays
        equal/opposite in loads AND moments.
        """
        f_a_tri, f_b_tri, p = self.contact.tractions()
        fd_b = self.contact.damping_force_on_b()
        fd_a = -fd_b                       # bitwise negative (law 6)
        fb_b = self.bond.force_on_b()
        fb_a = -fb_b                       # bitwise negative (law 6)
        partition = self.contact.shared_partition()
        traction_a = np.zeros_like(self.body_a.x)
        traction_b = np.zeros_like(self.body_b.x)
        for tri, f in ((self.body_a.triangles[0], f_a_tri[0]),
                       (self.body_a.triangles[1], f_a_tri[1])):
            for vid in tri:
                traction_a[vid] += f / 3.0
        for tri, f in ((self.body_b.triangles[0], f_b_tri[0]),
                       (self.body_b.triangles[1], f_b_tri[1])):
            for vid in tri:
                traction_b[vid] += f / 3.0
        damp_a = np.zeros_like(self.body_a.x)
        damp_b = np.zeros_like(self.body_b.x)
        if float(np.dot(fd_b, fd_b)) > 0.0:
            damp_b = self.body_b.distribute_to_iface(fd_b, partition)
            damp_a = self.body_a.distribute_to_iface(fd_a, partition)
        bond_a = np.zeros_like(self.body_a.x)
        bond_b = np.zeros_like(self.body_b.x)
        if float(np.dot(fb_b, fb_b)) > 0.0:
            bond_b = self.body_b.distribute_to_iface(fb_b, partition)
            bond_a = self.body_a.distribute_to_iface(fb_a, partition)
        res = {'contact_force_b': f_b_tri.sum(axis=0),
               'contact_force_a': f_a_tri.sum(axis=0),
               'damping_force_b': fd_b,
               'damping_force_a': fd_a,
               'bond_force_b': fb_b, 'bond_force_a': fb_a,
               'pressure_pa': p}
        return traction_a, traction_b, damp_a, damp_b, bond_a, bond_b, res

    def _reciprocity(self, res, origins):
        """Summed interface force/torque about each origin (law 6).

        Includes contact traction, contact damping and bond pairs; every
        pair is applied at the two anchors (coincident while touching,
        offset along x only during separation while the forces stay along
        x), so exact cancellation holds about ANY origin.
        """
        anchor_a = self.body_a.anchor
        anchor_b = self.body_b.anchor
        pairs = [(res['contact_force_b'], res['contact_force_a']),
                 (res['damping_force_b'], res['damping_force_a']),
                 (res['bond_force_b'], res['bond_force_a'])]
        net_f = np.zeros(3)
        torques = {name: np.zeros(3) for name in origins}
        for f_b, f_a in pairs:
            net_f = net_f + f_b + f_a
            for name, o in origins.items():
                torques[name] = (torques[name]
                                 + np.cross(anchor_b - o, f_b)
                                 + np.cross(anchor_a - o, f_a))
        return net_f, torques

    def _project(self, body):
        """XPBD edge projection (M03 scaffold pattern; residual measured)."""
        alpha_tilde = XPBD_COMPLIANCE_M_PER_N / (DT_S * DT_S)
        lam = np.zeros(len(body.edge_list))
        edge_arr = np.array(body.edge_list, dtype=np.int64)
        for _ in range(XPBD_ITERATIONS):
            for e, (a1, a2) in enumerate(body.edge_list):
                pa, pb = body.x[a1], body.x[a2]
                d = pb - pa
                length = float(np.linalg.norm(d))
                if length == 0.0:
                    continue
                grad = d / length
                c = length - body.rest_lengths[e]
                w_sum = body.inv_masses[a1] + body.inv_masses[a2]
                if w_sum == 0.0:
                    continue
                dlam = (-c - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
                lam[e] += dlam
                body.x[a1] -= body.inv_masses[a1] * dlam * grad
                body.x[a2] += body.inv_masses[a2] * dlam * grad
        return edge_arr

    def step(self, tick, origins):
        body_a, body_b = self.body_a, self.body_b
        # declared global damping on B (measured dissipation), before loads
        kin_before = float((0.5 * body_b.masses[:, None] * body_b.v ** 2).sum())
        body_b.v = body_b.v * (1.0 - DAMPING_B_PER_S * DT_S)
        kin_after = float((0.5 * body_b.masses[:, None] * body_b.v ** 2).sum())
        e_diss_damp = kin_before - kin_after
        # bond release at the declared tick (law 4)
        e_diss_release = 0.0
        if tick == RELEASE_TICK and self.bond.active:
            self.bond.release(tick)
            e_diss_release = self.bond.e_release_j
        # declared actuator (schedule), equal share per vertex of B, constant
        # over the tick (smooth declared forces)
        f_act = SCHEDULE.get(tick)
        act_loads = np.zeros_like(body_b.x)
        if f_act is not None:
            act_loads += (f_act / 5.0) * XHAT   # declared: along +x (law 8)
        # stiff interface loads integrated with substeps (correction A1):
        # work accounted per substep with the trapezoidal midpoint-velocity
        # rule, which equals the per-substep kinetic-energy change exactly
        # for the applied loads; the projection and integrator differences
        # stay in the measured residual.
        n_sub = INTERFACE_SUBSTEPS
        h = DT_S / n_sub
        w_act = w_contact = w_bond = 0.0
        q_contact = 0.0
        res = None
        for _ in range(n_sub):
            contact_a, contact_b, damp_a, damp_b, bond_a, bond_b, res_i = \
                self._interface_loads()
            res = res_i
            v_old = body_b.v
            loads = contact_b + damp_b + bond_b + act_loads
            v_load = v_old + loads * body_b.inv_masses[:, None] * h
            dx_trap = 0.5 * (v_old + v_load) * h
            x_pre = body_b.x.copy()
            body_b.x = body_b.x + v_load * h
            w_act += float((act_loads * dx_trap).sum())
            w_contact += float((contact_b * dx_trap).sum())
            w_bond += float((bond_b * dx_trap).sum())
            q_contact += -float((damp_b * dx_trap).sum())
            # scaffold projection every substep (constraint response resolved
            # at the interface-load timescale); the position-based solver's
            # constraint work is not force-integrable and stays in the
            # MEASURED residual (reported per tick, never hidden)
            self._project(body_b)
            body_b.v = (body_b.x - x_pre) / h
        # end-of-tick state snapshot (correction A1): energies are evaluated
        # at the SAME configuration as the reported kinetic energy
        u_bond = self.bond.stored_energy()
        u_contact = self.contact.stored_energy()
        u_scaffold = body_b.scaffold_energy()
        # transverse anchor offset guard (law 9)
        d = self.bond.delta()
        transverse = float(np.linalg.norm(d - float(np.dot(d, XHAT)) * XHAT))
        require(transverse <= TILT_REFUSAL_M, REFUSAL_TILT)
        # ledger (law 10, as re-issued by correction A1)
        kin = float((0.5 * body_b.masses[:, None] * body_b.v ** 2).sum())
        e_mech = kin + u_bond + u_contact + u_scaffold
        q_total = e_diss_damp + q_contact + e_diss_release
        prev = self.ticks[-1]['e_mechanical_j'] if self.ticks else 0.0
        w_sum = w_act + w_contact + w_bond
        residual = e_mech - prev - w_sum + q_total
        turnover = abs(w_act) + abs(w_contact) + abs(w_bond) + q_total + kin
        # Declared residual bound (correction A1): R is the measured artifact
        # of the position-based constraint solve, whose scale is bounded by
        # the reservoirs it exchanges with (penalty-spring, bond and scaffold
        # strain energies at this and the previous tick — transitions
        # discharge them) plus 5% of the accounted turnover. At a release
        # tick the release account must close to 5% of the released energy
        # (a dropped dissipation trips it). R is reported per tick, never
        # assumed away.
        u_contact_prev = self.ticks[-1]['u_contact_j'] if self.ticks else 0.0
        u_bond_prev = self.ticks[-1]['bond_stored_energy_j'] if self.ticks \
            else 0.0
        bound = (u_contact + u_contact_prev + u_bond + u_bond_prev
                 + u_scaffold + 5e-2 * turnover + 1e-9)
        if e_diss_release > 0.0:
            bound = min(bound, 5e-2 * e_diss_release + 1e-12)
        net_f, torques = self._reciprocity(res, origins)
        iface_area_drift = float(np.abs(
            self.contact.shared_partition()
            - self.body_b.current_iface_areas()).max())
        # interface pair-force scale (for the derived torque bound: two
        # equal/opposite forces at points offset transversely by d carry the
        # net couple |d| x F_pair — real physics, not an error)
        f_pair = float(np.linalg.norm(res['contact_force_b'])
                       + np.linalg.norm(res['damping_force_b'])
                       + np.linalg.norm(res['bond_force_b']))
        row = {
            'tick': tick,
            'gap_m': self.contact.gap(),
            'contact_state': self.contact.state(),
            'contact_pressure_pa': res['pressure_pa'],
            'contact_force_n': [float(c) for c in res['contact_force_b']],
            'iface_area_drift_m2': iface_area_drift,
            'bond_active': self.bond.active,
            'bond_status': self.bond.status,
            'bond_tension_n': self.bond.tension(),
            'bond_force_n': [float(c) for c in self.bond.force_on_b()],
            'bond_stored_energy_j': u_bond,
            'bond_extension_m': self.bond.extension(),
            'transverse_anchor_offset_m': transverse,
            'actuator_force_n': 0.0 if f_act is None else f_act,
            'w_actuator_j': w_act,
            'w_contact_j': w_contact,
            'w_bond_j': w_bond,
            'e_diss_damping_j': e_diss_damp,
            'e_diss_contact_j': q_contact,
            'e_diss_release_j': e_diss_release,
            'e_kinetic_j': kin,
            'e_mechanical_j': e_mech,
            'u_contact_j': u_contact,
            'u_scaffold_j': u_scaffold,
            'q_total_j': q_total,
            'residual_r_j': residual,
            'residual_bound_j': bound,
            'residual_within_bound': bool(abs(residual) <= bound),
            'interface_net_force_n': [float(c) for c in net_f],
            'interface_pair_force_n': f_pair,
            'interface_torque_nm': {name: [float(c) for c in vec]
                                    for name, vec in torques.items()},
            'body_b_com_m': [float(c) for c in
                             (body_b.x * body_b.masses[:, None]).sum(axis=0)
                             / body_b.masses.sum()],
            'max_speed_m_per_s': float(np.abs(body_b.v).max()),
            'state_hash': None,
        }
        row['state_hash'] = digest({k: row[k] for k in sorted(row)
                                    if k != 'state_hash'})
        self.ticks.append(row)
        return row

    def run(self, ticks, origins):
        for tick in range(ticks):
            self.step(tick, origins)
        return self.ticks


def replay_hash(ticks):
    return digest(ticks)
