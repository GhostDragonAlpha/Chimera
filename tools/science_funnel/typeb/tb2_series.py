"""TypeB-P1 M2 divergence analyzer (declared metric, prereg_typeb_p1.json).

Compares a perturbed run's [tb1] per-tick series (run 1) against the baseline:
first divergence tick, |dx|/|dy| at the earlier of refusal/tick 300, mean base_x
velocity over the last 50 pre-refusal ticks, and the verdict clauses.
Usage: python tb2_series.py <baseline_stderr> <perturbed_stderr>
"""
import sys, re

def load(p):
    rows = []
    refused = None
    for ln in open(p, encoding="utf-8", errors="replace"):
        m = re.match(r"\[tb1\] run=1 tick=(\d+) bx=([-\d.]+) by=([-\d.]+)", ln)
        if m:
            rows.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))
        if "WALK REFUSED tick" in ln and refused is None and ln.count("WALK REFUSED"):
            refused = rows[-1][0] if rows else None
            m2 = re.search(r"tick (\d+)", ln)
            if m2:
                refused = int(m2.group(1))
    return rows, refused

a, ra = load(sys.argv[1])
b, rb = load(sys.argv[2])
n = min(len(a), len(b))
first = None
for i in range(n):
    if a[i] != b[i]:
        first = i
        break
end = min((rb if rb is not None else 10**9), 300, len(b) - 1)
dx = abs(b[end][1] - a[min(end, len(a) - 1)][1]) if n else 0.0
dy = abs(b[end][2] - a[min(end, len(a) - 1)][2]) if n else 0.0
def tail_v(rows):
    k = rows[-50:]
    if len(k) < 2:
        return 0.0
    return (k[-1][1] - k[0][1]) / (k[-1][0] - k[0][0]) * 300.0
va, vb = tail_v(a), tail_v(b)
print("baseline ticks=%d refused=%s | perturbed ticks=%d refused=%s" % (len(a), ra, len(b), rb))
print("first_divergence_tick=%s" % first)
print("end_compare_tick=%d |dx|=%.4f m |dy|=%.4f m" % (end, dx, dy))
print("tail50 base_x velocity: baseline=%.4f m/s perturbed=%.4f m/s delta=%+.4f" % (va, vb, vb - va))
sustained = dx >= 0.05
graded = (rb is None) or (rb != ra and rb > 150)
onset = first is not None and first <= 170
print("sustained(|dx|>=0.05 at end)=%s onset_within_20=%s graded_response=%s" % (sustained, onset, graded))
print("AUTHORITY:", "YES" if (sustained and onset and graded) else "NO")
