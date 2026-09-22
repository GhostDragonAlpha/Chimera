"""diff_walk.py -- first-divergence scan: host kernel replay vs the C++ trace.

Reads FULL lines from hl_walk_full.txt (host ticks t=1..N) and cp_walk_full.txt
(C++ ticks t=0..N-1; C++ tick t is AFTER its (t+1)-th step, so C++ t aligns
with host t+1). Reports the first tick and component where |diff| exceeds the
threshold, plus the per-tick max for the first 12 ticks.
"""
import sys

def load(path):
    rows = {}
    for line in open(path):
        if not line.startswith('FULL'):
            continue
        kv = dict(p.split('=') for p in line.split()[1:])
        t = int(kv['t'])
        rows[t] = {k: float(v) for k, v in kv.items() if k != 't'}
    return rows

hl = load('hl_walk_full.txt')
cp = load('cp_walk_full.txt')

TH = 1e-9
first = None
for t in sorted(hl):
    ct = t - 1
    if ct not in cp:
        break
    a, b = hl[t], cp[ct]
    worst = max(((abs(a[k] - b[k]), k) for k in a), default=(0, '-'))
    if first is None and worst[0] > TH:
        first = (t, ct, worst)
    if t <= 12 or (first and t <= first[0] + 3):
        print(f'tick {t:3d} (cpp {ct:3d}): max|diff|={worst[0]:.3e} at {worst[1]}  '
              f'hl={a[worst[1]]:.17g} cp={b[worst[1]]:.17g}')
    if first and t > first[0] + 3:
        break
if first:
    t, ct, (d, k) = first
    print(f'\nFIRST DIVERGENCE: host tick {t} (cpp tick {ct}) at {k}: '
          f'host={hl[t][k]:.17g} cpp={cp[ct][k]:.17g} |diff|={d:.3e}')
    print('context at that tick (host vs cpp), selected components:')
    for k2 in sorted(hl[t]):
        dv = abs(hl[t][k2] - cp[ct][k2])
        if dv > 1e-9:
            print(f'  {k2}: host={hl[t][k2]:.17g} cpp={cp[ct][k2]:.17g} diff={dv:.3e}')
else:
    print('no divergence above', TH)
