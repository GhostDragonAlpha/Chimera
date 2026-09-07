import io, json

d = json.load(io.open(r'E:/PythonChimera/Saved/gait/stride.json', encoding='utf-8'))
th = d['theta']
names = d['names']
idx = {n: i for i, n in enumerate(names)}
n = len(th)

def col(name):
    return [row[idx[name]] for row in th]

print('=== L/R pair agreement ===')
for L, R in [('hip_L','hip_R'),('knee_L','knee_R'),('ankle_L','ankle_R')]:
    a, b = col(L), col(R)
    mx = max(abs(x-y) for x, y in zip(a, b))
    same_sign = all((x>0) == (y>0) for x, y in zip(a, b) if abs(x)>1e-9 or abs(y)>1e-9)
    mean_a = sum(a)/n; mean_b = sum(b)/n
    num = sum((x-mean_a)*(y-mean_b) for x,y in zip(a,b))
    da = (sum((x-mean_a)**2 for x in a))**0.5
    db = (sum((y-mean_b)**2 for y in b))**0.5
    r = num/(da*db) if da*db else 0
    print('%s vs %s: max_abs_diff=%.6f  pearson_r=%.4f  same_sign_fraction=%.3f' % (L, R, mx, r, same_sign))

print()
print('=== hip-knee relationship per leg ===')
for leg in ['L','R']:
    h = col('hip_'+leg); k = col('knee_'+leg)
    mh = sum(h)/n; mk = sum(k)/n
    num = sum((x-mh)*(y-mk) for x,y in zip(h,k))
    dh = (sum((x-mh)**2 for x in h))**0.5
    dk = (sum((y-mk)**2 for y in k))**0.5
    r = num/(dh*dk) if dh*dk else 0
    print('hip_%s vs knee_%s: pearson_r=%.4f' % (leg, leg, r))

print()
print('=== sampled trajectory (every 40th sample) ===')
print('%-8s %8s %8s %8s %8s %8s' % ('sample', 'hip_L', 'hip_R', 'knee_L', 'knee_R', 'ankle_L'))
for i in range(0, n, 40):
    row = th[i]
    print('%-8d %8.3f %8.3f %8.3f %8.3f %8.3f' % (i, row[idx['hip_L']], row[idx['hip_R']], row[idx['knee_L']], row[idx['knee_R']], row[idx['ankle_L']]))

print()
print('dt=%.6f  n_samples=%d  total_duration=%.3f s' % (d['dt'], n, d['dt']*n))
print('loop_t0=%.4f  stride_t=%.4f' % (d['loop_t0'], d['stride_t']))
print('clock:', json.dumps(d['clock']))
h = col('hip_L')
zc = sum(1 for i in range(1, n) if h[i-1] < 0 and h[i] >= 0)
peaks = sum(1 for i in range(1, n-1) if h[i] > h[i-1] and h[i] > h[i+1])
print('hip_L upward zero-crossings: %d' % zc)
print('hip_L local maxima: %d' % peaks)