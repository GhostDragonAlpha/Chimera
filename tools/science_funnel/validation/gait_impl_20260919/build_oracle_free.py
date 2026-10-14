"""Generate the free-root oracle fixture (gait_impl lane, STAGE 0 baseline).

The free-root lane ran its native suite (native_free.cpp) against a locally
generated oracle_cases.json that was never committed; this script regenerates
an equivalent fixture deterministically from the Python Assembly oracle
(tools/science_funnel/coupled_arm.py) on the compiled free model, so the
free-root falsifier suite runs on this merged tree. Deterministic: fixed pose
seed, no clock, no randomness.

Run from the repo root:
    python -B tools/science_funnel/validation/gait_impl_20260919/build_oracle_free.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import numpy as np
from tools.science_funnel.coupled_free_scene import COORDINATE_ORDER, build_free_model
from tools.science_funnel.coupled_arm import Assembly
from tools.science_funnel.common import canonical
from tools.creature_graph.store import CreatureGraph

MODEL = 'model.dynamics.coupled_arm'
FREE_MODEL = 'model.dynamics.coupled_arm_free'


def main():
    graph = CreatureGraph.load(str(ROOT / 'tools/creature_graph/data/creature_graph.json'))
    stored = graph.get(MODEL)['physical']['contract']
    model = graph.get(stored['source_model_id'])['physical']['model']
    free_record = graph.get(FREE_MODEL)['physical']['contract']
    free = build_free_model(model, free_record)

    # Fixed deterministic pose seed: base identity + two joint sweeps.
    poses = []
    for sh in (0.0, 0.35, -0.61):
        for el in (1.92, 1.10):
            poses.append({'base_rot_x': 0.0, 'base_rot_y': 0.0, 'base_rot_z': 0.0,
                          'base_trans_x': 0.0, 'base_trans_y': -0.08977588222411312,
                          'base_trans_z': 0.0,
                          'shoulder_flexion': sh, 'elbow_flexion': el})
    rates = [{'shoulder_flexion': 0.13, 'elbow_flexion': -0.07},
             {'base_rot_z': 0.21, 'elbow_flexion': 0.05},
             {}, {}, {}, {}]

    gravity = (0., -9.80665, 0.)
    cases = []
    for i, pose in enumerate(poses):
        asm = Assembly(free, values=pose, rates=rates[i], gravity=gravity)
        hand_local = [0.001777657291666502, -0.036138621093750024, 0.002310406250000002]
        force_world = [3.1, -5.7, 1.9]
        p, jac = asm.point('hand', hand_local)
        gf = asm.point_force('hand', hand_local, force_world)
        acc = asm.acceleration(gf)
        cases.append({
            'angles_rad': {name: float(pose[name]) for name in COORDINATE_ORDER},
            'rates_rad_s': {name: float(rates[i].get(name, 0.)) for name in COORDINATE_ORDER},
            'hand_local_point_m': hand_local,
            'force_world_N': force_world,
            'hand_world_point_m': [float(v) for v in p],
            'hand_jacobian_m_per_rad': [[float(v) for v in row] for row in jac],
            'point_generalized_force_N_m': [float(v) for v in gf],
            'unconstrained_acceleration_rad_s2': [float(v) for v in acc],
            'reference': {
                'gravity_m_s2': list(gravity),
                'gravity_force_N_m': [float(v) for v in asm.gravity_force],
                'bias_force_N_m': [float(v) for v in asm.bias_force],
                'mass_matrix': [[float(v) for v in row] for row in asm.mass_matrix],
                'potential_J': float(asm.potential_J),
            },
        })

    out = ROOT / 'tools/science_funnel/validation/gait_impl_20260919/oracle_cases_free.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({'cases': cases}, indent=1, allow_nan=False) + '\n'
    out.write_text(payload, encoding='utf-8')
    print(json.dumps({'written': str(out), 'cases': len(cases)}))


if __name__ == '__main__':
    main()
