"""measure_authority.py -- F-FULLPORT-COMMAND-AUTHORITY (PREREG_FULLPORT.md).

For cmd in {0.0, 0.5, 1.0} m/s on the nvcc DLL route, E=1, reflex_level=1:
  1. settle + 90 ticks uncommanded (gait established; CPU class fires ~92-98),
  2. set_command(cmd) -- the adapter channel (vx=cmd, live=1, all envs),
  3. step tick-by-tick to the FIRST post-command hind fire (rbi[0]+rbi[1]
     increments), read a_hind_xoff of the fired leg: the plant-law consumption
     must equal cmd*(DUTY_SAMPLED*T_CYCLE)/2 within 1e-9 ABSOLUTE,
  4. mean achieved body speed rb[:,2] (base vx) over the 120-tick window after
     the command is set; must be monotone NON-DECREASING across commands.

Falsifier fires if (3) deviates by >1e-9 for any command, or (4) is not
monotone. A fired falsifier is reported fired, with numbers. Nothing is
re-tuned. Trailer: Agent: GLM 5.3.
"""
import json
import sys
import numpy as np
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from walker_model import load_spec, DUTY_SAMPLED, T_CYCLE
from walker_env_host import WalkerEnvDLL

OUT = HERE.parents[1] / 'validation' / 'typeb_gpu_fullport_20260921'
SETTLE = 60
LEAD = 90       # uncommanded ticks after settle before the command
WINDOW = 120    # achieved-speed window after set_command
TOL = 1e-9

spec = load_spec(str(HERE.parents[2] / '.tmp' / 'gait-walker' / 'scene.json'))
R = {'tol': TOL, 'plant_law': DUTY_SAMPLED * T_CYCLE / 2.0,
     'duty_sampled': DUTY_SAMPLED, 't_cycle': T_CYCLE, 'commands': []}

fires_ok = True
speeds = []
for cmd in (0.0, 0.5, 1.0):
    env = WalkerEnvDLL(spec, 1, reflex_level=1, block=32)
    env.reset()
    for _ in range(SETTLE + LEAD):
        env.step(1)
    st0 = env.status()
    c0l, c0r = int(st0['rbi'][0][0]), int(st0['rbi'][0][1])
    env.set_command(cmd)
    fire_tick = None
    xoff_seen = None
    fired_leg = None
    speeds_win = []
    for t in range(1, WINDOW + 1):
        env.step(1)
        stt = env.status()
        c1l, c1r = int(stt['rbi'][0][0]), int(stt['rbi'][0][1])
        speeds_win.append(float(stt['rb'][0][2]))
        if fire_tick is None and c1l + c1r > c0l + c0r:
            fire_tick = t
            fired_leg = 0 if c1l > c0l else 1
            xo = env.read_xoff()
            xoff_seen = float(xo[fired_leg])
    mean_v = float(np.mean(speeds_win))
    expected = cmd * DUTY_SAMPLED * T_CYCLE / 2.0
    dev = abs(xoff_seen - expected) if xoff_seen is not None else None
    ok = dev is not None and dev <= TOL
    fires_ok = fires_ok and ok
    speeds.append(mean_v)
    R['commands'].append({'cmd': cmd, 'fire_tick': fire_tick, 'xoff': xoff_seen,
                          'expected_xoff': expected, 'dev': dev, 'plant_ok': ok,
                          'mean_vx': mean_v})
    print(f"cmd={cmd}: fire_tick={fire_tick} xoff={xoff_seen!r} expected={expected!r} "
          f"dev={dev!r} plant_ok={ok} mean_vx={mean_v:.9f}", flush=True)

mono = bool(speeds[0] <= speeds[1] <= speeds[2])
R['monotone'] = mono
R['authority_pass'] = bool(fires_ok and mono)
R['verdict'] = ('PASS' if R['authority_pass'] else
                f"FIRED: plant_law_ok={fires_ok} monotone={mono}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'authority_dll.json').write_text(json.dumps(R, indent=1))
print(f"F-FULLPORT-COMMAND-AUTHORITY: {R['verdict']}")
print(f"speeds={speeds} monotone={mono}")
