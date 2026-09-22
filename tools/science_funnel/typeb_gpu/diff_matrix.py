"""diff_matrix.py -- mechanism-split: which subsystem owns the tick-1 v divergence.

For each (cpp config, host config) pair, prints the tick-1 per-component diff
and the total. Contact-off removes impact/projection; power-off removes the
servo tau.
"""
import re

def load(path, prefix='FULL t='):
    rows = {}
    for line in open(path):
        if not line.startswith(prefix):
            continue
        kv = dict(p.split('=') for p in line.split()[1:])
        t = int(kv['t'])
        rows[t] = {k: float(v) for k, v in kv.items() if k != 't'}
    return rows

def tick1_diff(name, cp_rows, hl_rows):
    if 0 not in cp_rows or 1 not in hl_rows:
        print(f'{name}: MISSING DATA cp={sorted(cp_rows)[:2]} hl={sorted(hl_rows)[:2]}')
        return
    a, b = hl_rows[1], cp_rows[0]
    ds = sorted(((abs(a[k] - b[k]), k) for k in a), reverse=True)
    tot = sum(d for d, _ in ds)
    print(f'{name}: total={tot:.4e}  top: ' +
          '  '.join(f'{k}:{d:.2e}' for d, k in ds[:6]))

cp_base = load('cp_base.txt')
cp_nc = load('cp_nocontact.txt')
cp_np = load('cp_nopower.txt')
hl_base = load('hl_base.txt')
hl_nc = load('hl_nocontact.txt')
hl_np = load('hl_nopower.txt')

tick1_diff('BASE      (contact+power)  ', cp_base, hl_base)
tick1_diff('NOCONTACT (contact OFF)    ', cp_nc, hl_nc)
tick1_diff('NOPOWER   (power OFF)      ', cp_np, hl_np)
# cross: does the cpp base equal cpp nocontact at tick1? (how big is contact on cpp side)
a, b = cp_base[0], cp_nc[0]
ds = sorted(((abs(a[k] - b[k]), k) for k in a), reverse=True)
print(f'\ncpp tick1 base-vs-nocontact: total={sum(d for d,_ in ds):.4e}  top: ' +
      '  '.join(f'{k}:{d:.2e}' for d, k in ds[:6]))
a, b = cp_base[0], cp_np[0]
ds = sorted(((abs(a[k] - b[k]), k) for k in a), reverse=True)
print(f'cpp tick1 base-vs-nopower:   total={sum(d for d,_ in ds):.4e}  top: ' +
      '  '.join(f'{k}:{d:.2e}' for d, k in ds[:6]))
a, b = hl_base[1], hl_nc[1]
ds = sorted(((abs(a[k] - b[k]), k) for k in a), reverse=True)
print(f'host tick1 base-vs-nocontact: total={sum(d for d,_ in ds):.4e}  top: ' +
      '  '.join(f'{k}:{d:.2e}' for d, k in ds[:6]))
a, b = hl_base[1], hl_np[1]
ds = sorted(((abs(a[k] - b[k]), k) for k in a), reverse=True)
print(f'host tick1 base-vs-nopower:   total={sum(d for d,_ in ds):.4e}  top: ' +
      '  '.join(f'{k}:{d:.2e}' for d, k in ds[:6]))
