"""MAT2-M08 local rehearsal: MirrorWorld vs the sealed M07 oracle (CPU).

Validates the kernel-mirror logic against integrated_step.IntegratedWorld on
the agreement fixture BEFORE any GPU job. Run: python local_rehearsal.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M04'), str(CONTRIB / 'MAT2-M06'),
           str(CONTRIB / 'MAT2-M07')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import integrated_step as iw   # noqa: E402
import kernel_mirror as km     # noqa: E402

TICKS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
COMPS = int(sys.argv[2]) if len(sys.argv) > 2 else 1


def main():
    offs = [(f'c{i}', 3.0 * i) for i in range(COMPS)]
    comps = [iw.Component(cid, off) for cid, off in offs]
    oracle = iw.IntegratedWorld([iw.Component(cid, off)
                                 for cid, off in offs])
    gpu = km.MirrorWorld(comps, gravity=True)
    assert oracle.declaration['order'] == gpu.declaration['order']
    worst = {}
    for tick in range(TICKS):
        dp = float(iw.PRESS_SCHEDULE.get(tick, 0.0))
        oracle.step(tick)
        gpu.step_tick(tick, dp)
        orow = oracle.ticks[-1]['components'][offs[0][0]]
        block = gpu.states[0]['block']
        checks = {
            'plate_x_m': (orow['plate_x_m'], block[km.D_PLX]),
            'F_N': (orow['F_N'], block[km.D_F]),
            'U_mat': (orow['U_mat_j'], block[km.D_UMAT]),
            'Q_mat': (orow['Q_mat_j'], block[km.D_QMAT]),
            'W_in': (orow['W_in_mat_j'], block[km.D_WIN]),
            'e_kin': (orow['e_kinetic_j'], block[km.D_KE]),
            'u_scaff': (orow['u_scaffold_j'], block[km.D_USCAFF]),
            'vol': (orow['membrane_volume_m3'], block[km.D_VOL]),
            'w_press': (orow['w_press_j'], block[km.D_WPRESS]),
            'w_grav': (orow['w_grav_j'], block[km.D_WGRAV]),
            'w_mat': (orow['w_mat_on_plate_j'], block[km.D_WMAT]),
            'q_tick': (orow['q_mat_tick_j'], block[km.D_QTICK]),
            'wcke': (orow['w_contact_ke_j'], block[km.D_WCKE]),
            'proj': (orow['projection_exchange_j'], block[km.D_PROJ]),
            'resid': (orow['residual_r_j'], block[km.D_RESID]),
            'jn_tot': (orow['jn_applied_total_N_s'], block[km.D_JNTOT]),
            'trap': (orow['impulse_trapezoid_work_j'], block[km.D_TRAP]),
            'iters': (orow['contact_iterations'], block[km.D_ITERS]),
            'active': (orow['contact_active_pairs'], block[km.D_ACTIVE]),
            'gs_res': (orow['contact_gs_residual_N_s'], block[km.D_GSRES]),
        }
        for name, (a, b) in checks.items():
            d = abs(float(a) - float(b))
            scale = max(1.0, abs(float(a)), abs(float(b)))
            rel = d / scale
            if name not in worst or rel > worst[name][0]:
                worst[name] = (rel, d, tick)
        # trajectory: plate vertices and membrane positions
        oplate = np.array([list(r) for r in
                           oracle._component(offs[0][0]).plate.x])
        gplate = gpu.states[0]['px']
        dpd = float(np.abs(oplate - gplate).max())
        omem = oracle._component(offs[0][0]).x
        gmem = gpu.states[0]['x']
        dmd = float(np.abs(omem - gmem).max())
        if 'plate_pos' not in worst or dpd > worst['plate_pos'][1]:
            worst['plate_pos'] = (dpd, dpd, tick)
        if 'mem_pos' not in worst or dmd > worst['mem_pos'][1]:
            worst['mem_pos'] = (dmd, dmd, tick)
    print(f'ticks={TICKS} comps={COMPS} worst relative/absolute deviations:')
    ok = True
    for name, (rel, d, t) in sorted(worst.items()):
        flag = 'OK ' if d <= 1e-12 else 'BAD'
        if d > 1e-12:
            ok = False
        print(f'  {flag} {name:10s} maxdiff={d:.3e} rel={rel:.3e} tick={t}')
    print('RESULT:', 'AGREED' if ok else 'DISAGREED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
