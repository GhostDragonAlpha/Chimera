"""run_fullport.py -- the TypeB GPU full-body port falsifier suite.

Fires the PREREG_FULLPORT.md falsifiers honestly and writes the receipt JSON.
Trailer Agent: GLM 5.3.
"""
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np
import warp as wp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from walker_model import load_spec, T_CYCLE, DUTY_SAMPLED
from walker_gpu import GaitWalkEnv

ROOT = HERE.parent.parent
SCENE = ROOT / '.tmp' / 'gait-walker' / 'scene.json'
OUT = HERE.parent / 'validation' / 'typeb_gpu_fullport_20260921'


def f64(x):
    return wp.float64(x)


def i32(x):
    return wp.int32(x)


def probe_freefall(env):
    # F-G5 pattern: power off, contact off, defaults pose, 100 ticks at g
    env.cst.power = i32(0)
    env.cst.contact = i32(0)
    env.cst.gait_enabled = i32(0)
    q0 = np.tile(env.spec.defaults, env.E)
    env.reset(q0=q0, v0=np.zeros(env.E * 18), touching0=np.zeros(env.E, np.int32))
    ys = []
    for t in range(100):
        env.step(1, readback=True)
        ys.append(env.rb.numpy().reshape(env.E, 6)[0, 1])
    ys = np.array(ys)
    h = 1.0 / 300.0
    accs = []
    for i in range(2, len(ys) - 2):
        dd = (-ys[i + 2] + 16 * ys[i + 1] - 30 * ys[i] + 16 * ys[i - 1] - ys[i - 2]) / (12 * h * h)
        accs.append(dd)
    g_meas = float(np.mean(accs))
    return {'measured_g': g_meas, 'err': abs(g_meas - 9.80665), 'drop': float(ys[0] - ys[-1])}


def probe_stand(env, ticks=60):
    # the stage-E stand: contact on, power on, clock frozen (gait_enabled 0)
    env.cst.power = i32(1)
    env.cst.contact = i32(1)
    env.cst.gait_enabled = i32(0)
    env.reset()
    trace = []
    for t in range(ticks):
        env.step(1, readback=True)
        rb = env.rb.numpy().reshape(env.E, 6)[0]
        trace.append([rb[0], rb[1], rb[2]])
    return np.array(trace)


def load_cpu_trace(probe):
    p = HERE.parent / 'validation' / 'typeb_gpu_fullport_20260921' / f'cpu_{probe}.txt'
    rows = []
    for line in p.read_text().splitlines():
        if line.startswith('tick='):
            d = dict(kv.split('=') for kv in line.split()[1:])
            rows.append([float(d['q3']), float(d['q4']), float(d['v3'])])
    return np.array(rows)


def run_survival(env, seeds=64, cap=600, collapse_y=0.20):
    # the preregistered seed distribution
    q_base, v_base, _ = env.spec.reset_state()
    q0 = np.tile(q_base, seeds)
    v0 = np.tile(v_base, seeds)
    t0 = np.zeros(seeds, np.int32)
    for s in range(seeds):
        rng = np.random.Generator(np.random.PCG64(s))
        q = q0[s * 18:(s + 1) * 18]
        v = v0[s * 18:(s + 1) * 18]
        for d in range(12):
            c = env.spec.drive_coord[d]
            q[c] += rng.uniform(-1, 1) * 1e-3
            v[c] += rng.uniform(-1, 1) * 1e-2
        v[3] *= (1.0 + rng.uniform(-1, 1) * 0.02)
    env.cst.power = i32(1)
    env.cst.contact = i32(1)
    env.cst.gait_enabled = i32(1)
    env.cst.reflex_level = i32(1)
    env.reset(q0=q0, v0=v0, touching0=t0)
    horizons = np.full(seeds, cap, np.int64)
    classes = np.full(seeds, -1, np.int32)
    alive = np.ones(seeds, bool)
    for t in range(cap):
        env.step(1, readback=False)
        wp.synchronize()
        ref = env.a_refused.numpy()
        col = env.a_collapsed.numpy()
        tk = env.a_ticks.numpy()
        newly = np.where(alive & ((ref != 0) | (col != 0)))[0]
        for i in newly:
            horizons[i] = tk[i]
            classes[i] = env.a_refused_class.numpy()[i] if ref[i] != 0 else 9
            alive[i] = False
        if not alive.any():
            break
    return horizons, classes


def run_commanded(env, commands=(0.0, 0.5, 1.0), issue_tick=80, cap=200):
    results = []
    env.cst.power = i32(1)
    env.cst.contact = i32(1)
    env.cst.gait_enabled = i32(1)
    env.cst.reflex_level = i32(1)
    for cmd in commands:
        env.reset()
        for t in range(cap):
            if t == issue_tick:
                env.set_command(cmd)
            env.step(1, readback=False)
        wp.synchronize()
        st = env.status()
        i = 0
        xoff_at_fire = float('nan')
        hf = st['rbi'].reshape(env.E, 6)[0, 0] + st['rbi'].reshape(env.E, 6)[0, 1]
        fires = st['hind_fires'].reshape(env.E, 2)[0]
        # the xoff consumed at the FIRST post-command hind fire
        last_fire = st['cmd_first_tick'][0]
        if fires.sum() > 0:
            xoff = env.a_hind_xoff.numpy().reshape(env.E, 2)[0]
            xoff_at_fire = float(xoff.max())
        speeds = []
        for t in range(cap):
            env.readback_row = None
        results.append({'cmd': cmd, 'fires': fires.tolist(),
                        'cmd_first_tick': int(st['cmd_first_tick'][0]),
                        'cmd_fires_census': int(st['cmd_fires'][0]),
                        'xoff_seen': xoff_at_fire,
                        'rb_last': env.rb.numpy().reshape(env.E, 6)[0].tolist()})
    return results


def measure_speed_window(env, cmd, issue_tick=80, w0=90, w1=170):
    env.cst.power = i32(1)
    env.cst.contact = i32(1)
    env.cst.gait_enabled = i32(1)
    env.cst.reflex_level = i32(1)
    env.reset()
    vs = []
    for t in range(w1):
        if t == issue_tick:
            env.set_command(cmd)
        env.step(1, readback=False)
        if t >= w0:
            wp.synchronize()
            vs.append(env.rb.numpy().reshape(env.E, 6)[0, 2])
    return float(np.mean(vs))


def throughput(env, batch_label, warmup=30, reps=3, ticks=300):
    env.step(warmup)
    wp.synchronize()
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        env.step(ticks)
        wp.synchronize()
        times.append(time.perf_counter() - t0)
    med = sorted(times)[len(times) // 2]
    return {'batch': batch_label, 'E': env.E, 'ticks': ticks,
            'median_s': med, 'env_steps_per_s': env.E * ticks / med,
            'ms_per_tick': med / ticks * 1e3,
            'times': times}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', default='C', choices=['A', 'B', 'C'])
    ap.add_argument('--seeds', type=int, default=64)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    wp.init()
    spec = load_spec(str(SCENE))
    R = {'prereg': 'PREREG_FULLPORT.md', 'scene_sha': 'e61ad3864472453f2b2a77a71ca0579f1b78e905b2495f581a9f87f27502333c'}

    if a.phase in ('A', 'all'):
        env = GaitWalkEnv(spec, 1, reflex_level=0)
        ff = probe_freefall(env)
        R['freefall'] = ff
        st = probe_stand(env)
        cpu = load_cpu_trace('stand')
        n = min(len(st), len(cpu))
        if n:
            denom = 1.0 + np.abs(cpu[:n])
            diff = float(np.max(np.abs(st[:n] - cpu[:n]) / denom))
        else:
            diff = None
        R['stand'] = {'gpu_ticks': len(st), 'cpu_ticks': len(cpu), 'max_scaled_diff': diff}

    if a.phase in ('B', 'C', 'all'):
        env1 = GaitWalkEnv(spec, 1, reflex_level=1)
        # the nominal class run
        env1.reset()
        hind_fires = fore_lifts = 0
        refused = None
        horizon = 600
        for t in range(600):
            env1.step(1, readback=False)
            wp.synchronize()
            st = env1.status()
            hf = st['rbi'].reshape(1, 6)[0]
            hind_fires = int(hf[0] + hf[1])
            fore_lifts = int(hf[2] + hf[3])
            if st['refused'][0] or st['collapsed'][0]:
                refused = int(st['refused_class'][0]) if st['refused'][0] else 9
                horizon = int(st['ticks'][0])
                break
        R['nominal'] = {'horizon': horizon, 'refused_class': refused,
                        'hind_fires': hind_fires, 'fore_lifts': fore_lifts}
        # commanded runs
        env3 = GaitWalkEnv(spec, 1, reflex_level=1)
        cmd_results = []
        for cmd in (0.0, 0.5, 1.0):
            env3.reset()
            env3.cst.power = i32(1)
            env3.cst.contact = i32(1)
            env3.cst.gait_enabled = i32(1)
            env3.cst.reflex_level = i32(1)
            mean_v = measure_speed_window(env3, cmd)
            env3.reset()
            for t in range(200):
                if t == 80:
                    env3.set_command(cmd)
                env3.step(1, readback=False)
            wp.synchronize()
            st = env3.status()
            fires = st['hind_fires'].reshape(1, 2)[0]
            xo = env3.a_hind_xoff.numpy().reshape(1, 2)[0]
            expected = cmd * (DUTY_SAMPLED * T_CYCLE) / 2.0
            cmd_results.append({'cmd': cmd, 'mean_v_window': mean_v,
                                'fires': fires.tolist(),
                                'xoff_seen': float(xo.max()) if fires.sum() else None,
                                'xoff_expected': expected,
                                'cmd_first_tick': int(st['cmd_first_tick'][0])})
        R['commanded'] = cmd_results
        # survival
        env64 = GaitWalkEnv(spec, a.seeds, reflex_level=1)
        horizons, classes = run_survival(env64, seeds=a.seeds)
        R['survival'] = {'seeds': a.seeds,
                         'horizons': horizons.tolist(),
                         'classes': classes.tolist(),
                         'pass_100': int((horizons >= 100).sum()),
                         'median': float(np.median(horizons))}
        # throughput
        tp = []
        for B in (1024, 4096):
            envB = GaitWalkEnv(spec, B, reflex_level=1)
            envB.reset()
            tp.append(throughput(envB, B))
            del envB
        R['throughput'] = tp
    (OUT / f'results_{a.phase}.json').write_text(json.dumps(R, indent=1))
    print(json.dumps(R, indent=1))


if __name__ == '__main__':
    main()
