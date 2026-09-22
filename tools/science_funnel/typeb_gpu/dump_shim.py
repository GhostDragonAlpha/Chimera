"""dump_shim.py -- regenerate host_shim/ inputs from walker_env_host's OWN
array construction so host_loop.cxx replays exactly what the DLL consumes.

Writes: mdl.txt mdi.txt cst.txt csti_nom.txt csti_ff.txt q.txt v.txt store.txt
touch0.txt. The q/v/touching0 are the env_reset() arguments the DLL env uses
(spec.reset_state() + the reset touching computation). Trailer Agent: GLM 5.3.
"""
import numpy as np
from pathlib import Path
from walker_env_host import build_env_arrays, load_spec, _dp, _ip
from walker_numba import K_TOUCH

HERE = Path(__file__).parent
SHIM = HERE / 'host_shim'
spec = load_spec()

mdl, mdi, cst, csti_nom, store_floor = build_env_arrays(spec, reflex_level=1)
_, _, _, csti_ff, _ = build_env_arrays(spec, reflex_level=0)
csti_ff[1] = 0   # contact off
csti_ff[2] = 0   # power off
csti_ff[3] = 0   # gait off

def wr(name, a, fmt):
    with open(SHIM / name, 'w') as f:
        for x in np.asarray(a).ravel():
            f.write(fmt % x)

wr('mdl.txt', mdl, '%.18e\n')
wr('mdi.txt', mdi, '%d\n')
wr('cst.txt', cst, '%.18e\n')
wr('csti_nom.txt', csti_nom, '%d\n')
wr('csti_ff.txt', csti_ff, '%d\n')
wr('store.txt', store_floor, '%.18e\n')

q, v, phi = spec.reset_state()
wr('q.txt', q, '%.18e\n')
wr('v.txt', v, '%.18e\n')

# the reset touching computation, byte-mirroring WalkerEnvDLL.reset's default
frames, _, _ = spec._fk(np.asarray(q)[:18])
t0 = []
for leg in range(2):
    gmin = 1e300
    for pt in range(2):
        k = leg * 2 + pt
        p = frames[spec.pt_body[k]] @ np.append(spec.pt_local[k], 1.0)
        gmin = min(gmin, p[1] + spec.pt_radius[k] - spec.plane_model_y)
    t0.append(1 if gmin <= K_TOUCH else 0)
(SHIM / 'touch0.txt').write_text(''.join(str(t) for t in t0) + '\n')
print('shim rewritten: csti_nom drive_en=%d tair=%d; cst[plane_y]=%.17g mu=%.17g '
      'k_touch=%.17g fore_sh=%.17g fore_el=%.17g kp_post=%.17g; touch0=%s' %
      (csti_nom[6], csti_nom[10], cst[0], cst[3], cst[4], cst[22], cst[23], cst[11], t0))
