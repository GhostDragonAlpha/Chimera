"""Capture inputs and analytic reference outputs for a later native port.
Run from the repository root; the current graph identity is recorded, never forged.
The source/physics independent checks live in test_coupled_arm.py.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from tools.creature_graph.store import CreatureGraph
from tools.science_funnel.coupled_arm import Assembly
from tools.science_funnel.macaque_anatomy import parse_source
from tools.science_funnel.common import require


def capture():
    graph = CreatureGraph.load('tools/creature_graph/data/creature_graph.json')
    model = graph.get('model.anatomy.macaque_arm')['physical']['model']
    require(model == parse_source()[0], 'coupled_arm_source_model_drift')
    rng = np.random.default_rng(283)
    inputs = [({k: c['default_rad'] for k, c in model['coordinates'].items()}, {})]
    for _ in range(6):
        q = {k: c['range_rad'][0]+rng.uniform(.15, .85)*np.ptp(c['range_rad']) for k, c in sorted(model['coordinates'].items())}
        inputs.append((q, {k: rng.uniform(-1., 1.) for k in sorted(q)}))
    cases = []
    for index, (q, rates) in enumerate(inputs):
        a = Assembly(model, q, rates, model['gravity_m_s2'])
        point = [.01, -.02, .03]; force = [2., -3., .5]
        position, jacobian = a.point('hand', point); tau = a.point_force('hand', point, force)
        cases.append({'id': index, 'angles_rad': q, 'rates_rad_s': rates,
                      'reference': a.record(), 'hand_local_point_m': point,
                      'hand_world_point_m': position.tolist(), 'hand_jacobian_m_per_rad': jacobian.tolist(),
                      'force_world_N': force, 'point_generalized_force_N_m': tau.tolist(),
                      'unconstrained_acceleration_rad_s2': a.acceleration(tau).tolist()})
    return {'schema': 'chimera.coupled_arm_native_oracles.v1', 'graph_hash': graph.graph_hash(),
            'source_revision': model['source_revision'], 'seed': 283, 'cases': cases,
            'scope': 'Offline force/reference snapshots for native port parity. These are not time histories or evidence of native multibody motion.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('.tmp/coupled-arm/reference_cases.json'))
    target = parser.parse_args().output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(capture(), indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(str(target))
