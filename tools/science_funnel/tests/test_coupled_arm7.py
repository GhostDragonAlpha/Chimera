"""Seven-coordinate lift: S6 oracle fixture (recorded seed, no sweep) and the
per-stage offline checks of docs/packets/seven_coordinate_lift_v1.md.

The fixture is REGENERATED deterministically from the committed seed and
audited against the committed copy; the native unit binary
(ChimeraEngine/engine/tests_coupled_arm/multidynamics_unit.cpp) consumes the
same JSON. The permutation between the pinned recipe order (chain depth) and
the Python oracle's own sorted() order is declared once per stage, here.
"""
import copy,json,math,unittest
from pathlib import Path
import numpy as np
from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.coupled_arm import Assembly
from tools.science_funnel.common import Refusal
from tools.science_funnel.coupled_scene7 import COORDINATES,MODEL,ROOT
from tools.science_funnel.macaque_anatomy import parse_source

SEED=20260918
POSES_PER_STAGE=100
MARGIN=1e-3          # rad kept from every bound (S6)
STAGE_SIZES=(3,5,7)  # the qualification ladder's oracle widths
HAND_POINT=[0.001777657291666502,-0.036138621093750024,0.002310406250000002]
HAND_FORCE=[2.,-3.,.5]
COMMITTED=ROOT/'tools/science_funnel/validation/seven_coord_complete_20260918/oracle_cases7.json'
GENERATED=ROOT/'.tmp/seven-arm/oracle_cases7.json'


def submodel(model,coords):
    """The source model with every non-selected coordinate locked at its
    default: the Python oracle of the n-coordinate prefix stage."""
    m=copy.deepcopy(model)
    for k,v in m['coordinates'].items():v['locked']=k not in coords
    return m


def build_cases():
    graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
    model=graph.get('model.anatomy.macaque_arm')['physical']['model']
    require_model=model==parse_source()[0]
    assert require_model,'coupled_arm_source_model_drift'
    rng=np.random.default_rng(SEED)
    stages=[]
    for n in STAGE_SIZES:
        coords=COORDINATES[:n]
        order=sorted(coords)
        perm=[order.index(c) for c in coords] # recipe index i -> oracle index perm[i]
        sub=submodel(model,coords)
        poses=[]
        for _ in range(POSES_PER_STAGE):
            q={};rates={}
            for c in coords:
                lo,hi=model['coordinates'][c]['range_rad']
                q[c]=float(lo)+rng.uniform(MARGIN,float(hi-lo)-MARGIN)
                rates[c]=float(rng.uniform(-2.,2.))
            a=Assembly(sub,q,rates,model['gravity_m_s2'])
            position,jacobian=a.point('hand',HAND_POINT)
            tau=a.point_force('hand',HAND_POINT,HAND_FORCE)
            poses.append({'q':[q[c] for c in coords],'rates':[rates[c] for c in coords],
                          'reference':a.record(),
                          'hand_world_point_m':position.tolist(),
                          'hand_jacobian_m_per_rad':jacobian.tolist(),
                          'point_generalized_force_N_m':tau.tolist()})
        stages.append({'n':n,'coordinates':coords,'sorted_coordinates':order,
                       'permutation_recipe_to_sorted':perm,'poses':poses})
    return {'schema':'chimera.coupled_arm7_oracles.v1','seed':SEED,
            'poses_per_stage':POSES_PER_STAGE,'margin_rad':MARGIN,
            'recipe_coordinates':COORDINATES,'hand_local_point_m':HAND_POINT,
            'force_world_N':HAND_FORCE,'stages':stages,
            'scope':'Offline force/reference snapshots for the seven-coordinate '
                    'native lift parity at 1e-12 relative. Not time histories; '
                    'no contact, actuation or GPU claim.'}


class CoupledArm7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=parse_source()[0]
        cls.cases=build_cases()

    def test_fixture_regenerates_deterministic_and_matches_committed(self):
        committed=json.loads(COMMITTED.read_text(encoding='utf-8-sig'))
        self.assertEqual(self.cases,committed,'S6: the fixture is regenerated, '
                         'never hand-edited; a drift from the committed audit '
                         'copy is a fixture lie')

    def test_pinned_order_is_chain_depth_prefix_with_qualified_pair_first(self):
        self.assertEqual(COORDINATES[:2],['shoulder_flexion','elbow_flexion'])
        self.assertEqual(sorted(COORDINATES),sorted(k for k,v in self.model['coordinates'].items() if not v['locked']))
        for stage in self.cases['stages']:
            coords=stage['coordinates']
            self.assertEqual(coords,COORDINATES[:stage['n']],'stages are prefix expansions')
            self.assertEqual(stage['sorted_coordinates'],sorted(coords))
            self.assertEqual(stage['permutation_recipe_to_sorted'],[sorted(coords).index(c) for c in coords])

    def test_oracle_mass_identities_at_every_stage(self):
        for stage in self.cases['stages']:
            n=stage['n']
            for pose in (stage['poses'][0],stage['poses'][len(stage['poses'])//2],stage['poses'][-1]):
                m=np.array(pose['reference']['mass_matrix'])
                np.testing.assert_allclose(m,m.T,atol=1e-17)
                eigen=np.linalg.eigvalsh(m)
                self.assertGreater(eigen[0],0.,msg=f'stage {n}: mass not SPD')
                np.testing.assert_allclose(eigen,pose['reference']['mass_eigenvalues_kg_m2'],rtol=1e-14)

    def test_prefix_expansion_identity_across_stages(self):
        """The packet's derivation: the pinned order keeps stages as prefix
        expansions -- the n=3 oracle at (leading values, trailing coordinates
        at defaults) equals the leading block of the n=7 oracle at the same
        values (locked-at-default and free-at-default are the same kinematics)."""
        coords7=COORDINATES;coords3=COORDINATES[:3]
        q7={};r7={}
        for i,c in enumerate(coords7):
            lo,hi=self.model['coordinates'][c]['range_rad']
            span=hi-lo
            q7[c]=float(lo)+(0.25+0.05*(i%5))*span
            r7[c]=0.4-0.11*(i%7)
        for c in coords7:
            if c not in coords3:
                q7[c]=float(self.model['coordinates'][c]['default_rad']);r7[c]=0.
        q3={c:q7[c] for c in coords3};r3={c:r7[c] for c in coords3}
        a7=Assembly(submodel(self.model,coords7),q7,r7,self.model['gravity_m_s2'])
        a3=Assembly(submodel(self.model,coords3),q3,r3,self.model['gravity_m_s2'])
        # Compare in the PINNED recipe order: recipe slot i of the n=3 stage
        # is the same physical coordinate as recipe slot i of the n=7 stage.
        s3={c:i for i,c in enumerate(a3.coordinates)}
        s7={c:i for i,c in enumerate(a7.coordinates)}
        m7=np.array(a7.mass_matrix);m3=np.array(a3.mass_matrix)
        for i,ci in enumerate(coords3):
            for j,cj in enumerate(coords3):
                self.assertAlmostEqual(m3[s3[ci]][s3[cj]],m7[s7[ci]][s7[cj]],delta=1e-15,
                                       msg=f'prefix expansion {ci}/{cj}')
        g3=np.array(a3.gravity_force);g7=np.array(a7.gravity_force)
        b3=np.array(a3.bias_force);b7=np.array(a7.bias_force)
        for i,ci in enumerate(coords3):
            self.assertAlmostEqual(g3[s3[ci]],g7[s7[ci]],delta=1e-15,msg=f'prefix gravity {ci}')
            self.assertAlmostEqual(b3[s3[ci]],b7[s7[ci]],delta=1e-15,msg=f'prefix bias {ci}')

    def test_contract_pins_recipe_and_stores(self):
        graph=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'))
        contract=graph.get(MODEL)['physical']['contract']
        self.assertEqual(contract['schema'],'chimera.coupled_scene7.v1')
        self.assertEqual(contract['coordinates'],COORDINATES)
        self.assertEqual(contract['battery_initial_J'],2.0)
        self.assertEqual(contract['tick_hz'],300);self.assertEqual(contract['substeps'],4)
        for c in COORDINATES:
            self.assertIs(contract['defaults'][c+'_drive'],True)
            target=contract['defaults'][c+'_target_deg']*np.pi/180
            lo,hi=self.model['coordinates'][c]['range_rad']
            self.assertGreaterEqual(target,lo-1e-8);self.assertLessEqual(target,hi+1e-8)
            self.assertGreater(contract['defaults'][c+'_torque_limit_N_m'],0.)

    def test_submodel_locking_refuses_foreign_rates(self):
        sub3=submodel(self.model,COORDINATES[:3])
        with self.assertRaises(Refusal):
            Assembly(sub3,rates={'wrist_flexion':1.})


if __name__=='__main__':
    unittest.main()
