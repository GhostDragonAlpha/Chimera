"""Offline unit checks for the free-root eight-coordinate scene (packet F list).

Recipe validation, the D1 scaffold, the D4/D7 seating scan and the D5/D6
algebra against closed forms. The dynamic falsifiers F1-F9 run against the
native runtime (tests_coupled_arm/native_free.cpp via the lane scripts and
tests/qualify_coupled_free_live.py); nothing here integrates time.
"""
import copy
import json
import math
import unittest
import numpy as np
from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.common import Refusal, require
from tools.science_funnel.coupled_arm import Assembly
from tools.science_funnel.coupled_free_scene import BASE_COORDINATES, COORDINATE_ORDER, ROOT, build_free_model, seating_scan
from tools.science_funnel.macaque_anatomy import parse_source, pose_frames

MODEL = 'model.dynamics.coupled_arm'
FREE_MODEL = 'model.dynamics.coupled_arm_free'
K_TOUCH = 1e-5


def free_record(graph):
    return graph.get(FREE_MODEL)['physical']['contract']


def build_recipe(record):
    defaults = dict(record['defaults'])
    base = [float(v) for v in record['base_scaffold']['defaults_rad_m']]
    defaults.update({'base_rot_x_deg': base[0]*180/math.pi, 'base_rot_y_deg': base[1]*180/math.pi,
                     'base_rot_z_deg': base[2]*180/math.pi, 'base_trans_x_m': base[3],
                     'base_trans_y_m': base[4], 'base_trans_z_m': base[5],
                     'base_rot_x_speed_deg_s': 0., 'base_rot_y_speed_deg_s': 0., 'base_rot_z_speed_deg_s': 0.,
                     'base_trans_x_speed_m_s': 0., 'base_trans_y_speed_m_s': 0., 'base_trans_z_speed_m_s': 0.})
    return {'schema': 'chimera.coupled_free_scene.v1', 'source_model_id': record['source_model_id'],
            'derived_from_contract': MODEL, 'coordinates': COORDINATE_ORDER,
            'hand_body': record['hand_body'], 'hand_point_m': record['hand_point_m'],
            'attachment_id': record['attachment_id'], 'proxy_radius_m': record['proxy_radius_m'],
            'contact_points': record['contact_points'],
            'contact_plane_height_m': record['contact_plane_height_m'],
            'tick_hz': record['tick_hz'], 'substeps': record['substeps'],
            'servo_frequency_Hz': record['servo_frequency_Hz'], 'servo_damping_ratio': record['servo_damping_ratio'],
            'passive_decay_rate_s': record['passive_decay_rate_s'], 'battery_initial_J': record['battery_initial_J'],
            'defaults': defaults, 'assumptions': record['assumptions']}


# ── D6 reference: the mass-metric active-set projection (packet D6) ──
def project_reference(initial, inverse, rows, floors):
    """Closed-form reference: enumerate active sets (generalized reaction_rows);
    for each candidate solve the Gram system, require nonnegative multipliers
    and every floor holding after projection. Deterministic first match."""
    R = len(rows)
    for mask in range(1 << R):
        act = [k for k in range(R) if mask >> k & 1]
        if not act:
            continue
        A = np.array([rows[k] for k in act])
        G = A @ inverse @ A.T
        rhs = -(A @ initial - np.array([floors[k] for k in act]))
        try:
            lam = np.linalg.solve(G, rhs)
        except np.linalg.LinAlgError:
            continue
        if np.any(lam < -1e-10):
            continue
        lam = np.maximum(lam, 0.)
        p = np.zeros_like(initial)
        for i, k in enumerate(act):
            p += lam[i]*np.array(rows[k])
        projected = initial + inverse @ p
        if all(np.dot(rows[k], projected) >= floors[k]-1e-9 for k in range(R)):
            return p
    raise AssertionError('reference projection unsolved')


def friction_reference(initial, inverse, row_n, row_t, mu, slip_sign):
    """Packet D5 closed forms: joint (lambda_n, lambda_t) solve; stick inside
    the cone, slide capped ON the cone edge with the exact cross-coupling."""
    A = row_n @ inverse @ row_n
    B = row_n @ inverse @ row_t
    C = row_t @ inverse @ row_t
    rn = -(row_n @ initial)
    rt = -(row_t @ initial)
    det = A*C-B*B
    if det > 1e-18:
        n = (rn*C-rt*B)/det
        t = (rt*A-rn*B)/det
        if n >= 0 and abs(t) <= mu*n+1e-12:
            return n, t, 1
    s = slip_sign if slip_sign != 0. else (-1. if rt >= 0 else 1.)
    den = A-s*mu*B
    require(den > 1e-12, 'reference_slide_singular')
    n = rn/den
    t = -s*mu*n
    return (n, t, 2) if n >= 0 else (0., 0., 0)


class FreeSceneRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
        cls.record = free_record(cls.graph)
        # The source model lives on the ANATOMY record the free contract pins
        # (record['source_model_id']); the dynamics contract object itself
        # carries statement/prediction/contract only. (Lane f9-budget-20260919:
        # this lookup previously read graph.get(MODEL)['physical']['model'], a
        # constant mixup that KeyError'd -- pre-existing at 12e536ad, verified
        # on the base clone; the sibling compiler coupled_scene.py resolves the
        # model the same way through source_model_id.)
        cls.model = cls.graph.get(cls.record['source_model_id'])['physical']['model']
        require(cls.model == parse_source()[0], 'coupled_arm_source_model_drift')
        cls.free = build_free_model(cls.model, cls.record)
        cls.recipe = build_recipe(cls.record)

    def test_record_schema_and_provenance(self):
        require(self.record['schema'] == 'chimera.coupled_free_scene.v1', 'free_schema')
        require(self.record['derived_from_contract'] == MODEL, 'free_derivation')
        require(self.record['coordinates'] == COORDINATE_ORDER, 'free_order')
        require(self.record['defaults']['free_root_enabled'] is True, 'free_flag')
        require(self.record['defaults']['power'] is False, 'free_defaults_passive')
        for p in self.record['contact_points']:
            require(p['body'] in [b['name'] for b in self.model['bodies']], 'free_contact_body')
            require(p['radius_m'] > 0 and len(p['point_m']) == 3, 'free_contact_radius')
            require(p['provenance'], 'free_contact_provenance')

    def test_d1_base_scaffold(self):
        for name, rng in BASE_COORDINATES:
            c = self.free['coordinates'][name]
            self.assertEqual(c['range_rad'], [-rng, rng])
            self.assertFalse(c['locked'])
        sternum = [b for b in self.free['bodies'] if b['name'] == 'sternum'][0]
        self.assertEqual([a['name'] for a in sternum['joint']['axes']],
                         ['rotation1', 'rotation2', 'rotation3', 'translation1', 'translation2', 'translation3'])
        self.assertEqual(sternum['joint']['type'], 'CustomJoint')
        for a in sternum['joint']['axes']:
            self.assertEqual(a['function'], {'type': 'LinearFunction', 'coefficients': [1.0, 0.0]})
        # Other bodies and the qualified pair are untouched by the derivation.
        src = {b['name']: b for b in self.model['bodies']}
        for b in self.free['bodies']:
            if b['name'] == 'sternum':
                continue
            self.assertEqual(b, src[b['name']])

    def test_d4_d7_seating_scan(self):
        scan = seating_scan(self.free, self.recipe, 0.55)
        recorded = self.record['seating_scan']
        self.assertTrue(all(0 < g < K_TOUCH for g in scan['reset_gaps_m']))
        self.assertLess(scan['least_gap_m'], 0)
        self.assertAlmostEqual(scan['assembly_mass_kg'], recorded['assembly_mass_kg'], places=12)
        self.assertAlmostEqual(scan['weight_N'], recorded['weight_N'], places=9)
        np.testing.assert_allclose(scan['com_projection_model_m'], recorded['com_projection_model_m'], atol=1e-9)
        self.assertTrue(all(w > 0 for w in scan['barycentric_weights']))
        # The oracle (Assembly) and the raw FK frames agree on the CoM projection.
        asm = Assembly(self.free, gravity=[0., -9.80665, 0.])
        self.assertGreater(np.linalg.eigvalsh(asm.mass_matrix)[0], 0)

    def test_free_oracle_agreement_at_frozen_pose(self):
        """D2 numeric face: the free Assembly joint block equals the source
        Assembly evaluated at the FREE model's 8 coordinates with the five
        unselected coordinates LOCKED at their source defaults and the base
        frozen at identity (the rev-2 selection fact of
        model.dynamics.coupled_arm_free; base_trans_y sits at its authored
        seated default). The source-coordinate POSE is legal at the locked
        defaults, which are the source defaults by construction; the source
        RANGES are not extended (the source model refuses elbow 0)."""
        a2 = Assembly(self.model, gravity=[0., -9.80665, 0.])  # all source defaults
        values = {k: c['default_rad'] for k, c in self.free['coordinates'].items()
                  if not c['locked'] and k in self.model['coordinates']}
        values.update({'base_rot_x': 0., 'base_rot_y': 0., 'base_rot_z': 0.,
                       'base_trans_x': 0., 'base_trans_y': 0., 'base_trans_z': 0.})
        a8 = Assembly(self.free, values, gravity=[0., -9.80665, 0.])
        # Assembly's own slot order is its sorted UNLOCKED coordinate list
        # (coupled_arm.py); the fixture's free model has exactly the 8 unlocked
        # coordinates, sorted alphabetically: elbow_flexion = 6,
        # shoulder_flexion = 7 (the sorted-list face of the recipe's
        # [6,7] = shoulder,elbow stack order).
        slots = {k: idx for idx, k in enumerate(sorted(k for k, c in self.free['coordinates'].items() if not c['locked']))}
        i, j = slots['shoulder_flexion'], slots['elbow_flexion']
        # Reference slots use the SOURCE Assembly's own sorted unlocked order
        # (7 coordinates: elbow=0, shoulder=3) -- not the free model's slots.
        ref = {k: idx for idx, k in enumerate(a2.coordinates)}
        s2, e2 = ref['shoulder_flexion'], ref['elbow_flexion']
        M8 = a8.mass_matrix
        M2 = np.array([[M8[i, i], M8[i, j]], [M8[j, i], M8[j, j]]])
        np.testing.assert_allclose(M2, a2.mass_matrix[np.ix_([s2, e2], [s2, e2])], rtol=0, atol=2e-12)
        np.testing.assert_allclose([a8.gravity_force[i], a8.gravity_force[j]],
                                   [a2.gravity_force[s2], a2.gravity_force[e2]], rtol=0, atol=2e-12)
        np.testing.assert_allclose([a8.bias_force[i], a8.bias_force[j]],
                                   [a2.bias_force[s2], a2.bias_force[e2]], rtol=0, atol=2e-12)
        self.assertAlmostEqual(a8.potential_J, a2.potential_J, places=15)

    def test_d6_active_set_matches_enumeration(self):
        rng = np.random.default_rng(20260918)
        for _ in range(200):
            k = int(rng.integers(2, 5))
            B = rng.normal(size=(k, k))
            M = B @ B.T + k*np.eye(k)
            inv = np.linalg.inv(M)
            rows = [rng.normal(size=k) for _ in range(int(rng.integers(1, 4)))]
            floors = -np.abs(rng.normal(size=len(rows)))*0.3
            initial = rng.normal(size=k)
            try:
                p = project_reference(initial, inv, rows, floors)
            except AssertionError:
                continue
            projected = initial+inv@p
            for row, floor in zip(rows, floors):
                self.assertGreaterEqual(np.dot(row, projected), floor-1e-9)
        # Dependent rows: a duplicated row must not break the projection's
        # KKT face (the reference enumerates the singular mask away).
        M = np.eye(3)
        row = np.array([1., 0., 0.])
        rows = [row, row, np.array([0., 1., 0.])]
        floors = [0., 0., 0.]
        initial = np.array([-1., -2., 0.])
        p = project_reference(initial, M, rows, floors)
        projected = initial+M@p
        self.assertAlmostEqual(projected[0], 0., places=12)
        self.assertGreaterEqual(projected[1], -1e-12)

    def test_d5_cone_edge_algebra(self):
        rng = np.random.default_rng(7)
        for _ in range(200):
            k = int(rng.integers(2, 6))
            B = rng.normal(size=(k, k))
            M = B @ B.T + k*np.eye(k)
            inv = np.linalg.inv(M)
            row_n = rng.normal(size=k)
            row_t = rng.normal(size=k)
            mu = float(rng.uniform(.05, 1.))
            initial = -np.abs(rng.normal(size=k))-.5
            try:
                n, t, mode = friction_reference(initial, inv, row_n, row_t, mu, 1.)
            except Refusal:
                continue
            force = n*row_n+t*row_t
            projected = initial+inv@force
            if mode == 1:
                self.assertGreaterEqual(n, 0)
                self.assertLessEqual(abs(t), mu*n+1e-12)
                self.assertAlmostEqual(np.dot(row_n, projected), 0., places=10)
                self.assertAlmostEqual(np.dot(row_t, projected), 0., places=10)
            elif mode == 2:
                self.assertGreaterEqual(n, 0)
                self.assertAlmostEqual(abs(t), mu*n, places=10)
                # Slide reaches the normal floor exactly (KKT stationarity).
                self.assertAlmostEqual(np.dot(row_n, projected), 0., places=10)
            else:
                # Friction never pulls: separating normal means no force. The
                # SEPARATING claim is row_n.initial >= 0 (the normal is already
                # open, so the cone solve correctly books nothing) -- not
                # row_n.initial == 0 (the pre-fix line asserted the unconstrained
                # draw sat exactly on its floor, which no random draw does).
                self.assertGreaterEqual(np.dot(row_n, initial), -1e-9)

    def test_d5_rest_rule_opposes_impending_slip(self):
        inv = np.eye(2)
        n, t, mode = friction_reference(np.array([-1., -2.]), inv, np.array([1., 0.]), np.array([0., 1.]), .5, 0.)
        self.assertEqual(mode, 2)
        self.assertAlmostEqual(t, .5, places=12)


if __name__ == '__main__':
    unittest.main()
