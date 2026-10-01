"""THE WAVE-28B SHARE LEVER (receipt_wave28b.json, deliverable 2).

Quantifies d(share)/d(table) on the Assembly at the measured walk geometry,
and closes the lever arithmetic against the two measured seals:

  seal 1 (the channel): race-B's refined zero-table intervention left the w26
  dynamics byte-identical -- the posture servo is railed at 11.2125 N.m with a
  measured tracking gain dtheta_act/dtheta* = 0.02401: any vault-table
  amendment's DELIVERED CoM lever is its static lever times 0.024.

  seal 2 (the map): the mined load map (derive_load_map_wave28b.py) measured
  that the fore share does NOT track the CoM-static line at all (residual
  ~93 pp at t=60) -- the split is servo-authored, so even the FULL static CoM
  lever does not map to the share.

The script measures, on the scene's own Assembly at the tick-100 pose mined
from the reproduced run: h = |dx_com/dtheta| (the posture table's CoM lever),
the static share-line sensitivity, the full-range arithmetic at the recipe's
own +-0.6 rad guard, and the delivered (x0.024) numbers.

Usage:
  python -B derive_share_lever_wave28b.py <scene.json> <state100.json> <out.json>
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tools.science_funnel.coupled_arm import Assembly  # noqa: E402


def main():
    scene_path, state_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    bundle = json.loads(Path(scene_path).read_text(encoding='utf-8'))
    model = bundle['gait_controller']['model']
    state = json.loads(Path(state_path).read_text(encoding='utf-8'))
    hind = {int(k): v for k, v in state['hind_deg'].items()}
    names = ['hip_flexion_left', 'knee_extension_left', 'ankle_dorsiflexion_left',
             'MP_dorsiflexion_left', 'hip_flexion_right', 'knee_extension_right',
             'ankle_dorsiflexion_right', 'MP_dorsiflexion_right']
    values = {}
    for k, nm in enumerate(names):
        values[nm] = math.radians(hind[k])
    for nm, deg in state['fore_deg'].items():
        values[nm] = math.radians(deg)
    pang = math.radians(state['pang_deg'])
    masses = [(b['name'], float(b['mass_kg']), b['mass_center_m']) for b in model['bodies']]

    def com_x(theta):
        v = dict(values)
        v['base_rot_z'] = theta
        asm = Assembly(model, values=v, gravity=[0., -9.80665, 0.])
        num = 0.0
        den = 0.0
        for nm, m, com in masses:
            p, _ = asm.point(nm, com)
            num += m * p[0]
            den += m
        return num / den

    th0 = pang
    dth = 0.05
    c0 = com_x(th0)
    cm = com_x(th0 - dth)
    cp = com_x(th0 + dth)
    lever = (cp - cm) / (2 * dth)          # dx_com/dtheta at the window geometry, m/rad
    full = com_x(-0.6) - com_x(0.6)        # the CoM swing across the recipe's full guard
    out = {
        'schema': 'chimera.share_lever.v1',
        'state': 'tick-100 measured pose of the reproduced w27 run',
        'pang_rad': th0, 'com_x_at_pang_m': c0,
        'h_lever_m_per_rad': lever,
        'h_lever_mm_per_rad': lever * 1000.0,
        'com_swing_full_guard_m': full,
        'note': ('nose-up (theta+) moves the CoM WEST: the lever is NEGATIVE -- '
                 'the wave-8 vault climb is the DESIGNED fore-to-hind load '
                 'transfer; the sign is the pre-registered derivation measured'),
        # the map's own geometry at tick 100 (derive_load_map_wave28b.py):
        'map_x_hind_m': 0.130115, 'map_x_fore_m': 0.234922,
        'static_share_slope_per_rad': None,
        'delivered_gain': 0.02401,
        'delivered_share_slope_pp_per_rad': None,
    }
    span = out['map_x_fore_m'] - out['map_x_hind_m']
    out['static_share_slope_per_rad'] = lever / span  # share fraction per rad IF the line held
    out['delivered_share_slope_pp_per_rad'] = 100.0 * lever / span * 0.02401
    json.dump(out, open(out_path, 'w', encoding='utf-8'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
