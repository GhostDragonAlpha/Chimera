import io, json, hashlib

p = r'E:/PythonChimera/Saved/gait/stride.json'
raw = io.open(p, 'rb').read()
h = hashlib.sha256(raw).hexdigest()
print('FILE:', p)
print('bytes:', len(raw))
print('SHA-256:', h)
print()

d = json.loads(raw.decode('utf-8'))
print('top-level keys:', sorted(d.keys()))
print('format:', d.get('format'))
print('dt:', d.get('dt'))
print('n_samples:', d.get('n_samples'))
print('n_joints:', d.get('n_joints'))
print('names count:', len(d.get('names', [])))
print('theta rows:', len(d.get('theta', [])))
print('theta[0] len:', len(d['theta'][0]) if d.get('theta') else None)
print('prep:', d.get('prep'))
print('loop_t0:', d.get('loop_t0'))
print('stride_t:', d.get('stride_t'))
print('clock:', json.dumps(d.get('clock')))
print('gates:', json.dumps(d.get('gates')))
print()
print('=== per-channel statistics ===')
print('%-14s %8s %12s %12s %12s %8s %8s %6s' % ('joint', 'count', 'min', 'max', 'range', 'nonzero', 'varying', 'uniq'))
th = d['theta']
n = len(th)
const_zero = []
const_nonzero = []
varying_nonzero = []
varying_passing = []
for k, name in enumerate(d['names']):
    col = [row[k] for row in th]
    mn = min(col)
    mx = max(col)
    rng = mx - mn
    nz = sum(1 for v in col if abs(v) > 1e-12)
    uniq = len(set('%.10f' % v for v in col))
    varying = uniq > 1
    if nz == 0:
        const_zero.append(name)
    elif nz == n and not varying:
        const_nonzero.append(name)
    elif nz > 0 and varying:
        varying_nonzero.append(name)
    else:
        varying_passing.append(name)
    print('%-14s %8d %12.6f %12.6f %12.6f %8d %8d %6d' % (name, n, mn, mx, rng, nz, varying, uniq))
print()
print('constant zero (%d):' % len(const_zero), const_zero)
print('constant nonzero (%d):' % len(const_nonzero), const_nonzero)
print('varying AND nonzero (%d):' % len(varying_nonzero), varying_nonzero)
print('varying but never nonzero (%d):' % len(varying_passing), varying_passing)
print()
print('NOTE: V02 said "26 of 28 joints zero" = constant-zero count', len(const_zero))
print('NOTE: nonzero channels =', len(const_nonzero) + len(varying_nonzero) + len(varying_passing))