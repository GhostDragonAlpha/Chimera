import io, os, hashlib, json

base = r'E:/PythonChimera/.tmp/p02_visual_20260906_122824'
files = sorted(f for f in os.listdir(base) if f.endswith('.png'))

md5 = {}
sha = {}
mt = {}
for f in files:
    p = os.path.join(base, f)
    b = io.open(p, 'rb').read()
    md5[f] = hashlib.md5(b).hexdigest()
    sha[f] = hashlib.sha256(b).hexdigest()
    mt[f] = os.stat(p).st_mtime

print('PNG count:', len(files))
print()

# duplicate groups by md5
from collections import defaultdict
by_md5 = defaultdict(list)
for f in files:
    by_md5[md5[f]].append(f)
print('distinct md5:', len(by_md5))
print()
print('=== DUPLICATE GROUPS (md5 collision) ===')
for h, fs in sorted(by_md5.items(), key=lambda x: -len(x[1])):
    if len(fs) > 1:
        times = [mt[f] for f in fs]
        same_mtime = (max(times) - min(times)) < 1.0
        print('md5=%s  n=%d  same_subsecond_mtime=%s' % (h[:16], len(fs), same_mtime))
        for f in fs:
            print('    %-26s %s' % (f, __import__('datetime').datetime.fromtimestamp(mt[f]).isoformat()))
print()
print('=== SINGLETONS (one file per md5) ===')
singles = [h for h, fs in by_md5.items() if len(fs) == 1]
print('count:', len(singles))
print()

# audit claims 59; measured 56
print('AUDIT CLAIM: 59 PNGs')
print('MEASURED   : %d PNGs + 2 scripts = %d files' % (len(files), len(files)+2))
print('DISCREPANCY: %d' % (59 - len(files)))
print()
print('possible sources of the 3-count gap:')
print('  (a) 3 files counted that are not PNGs (the 2 .py scripts = 2, not 3)')
print('  (b) 3 files counted twice because 3 PNG pairs are byte-identical duplicates')
print('      -> baseline_view == final_baseline, orbitOK_00 == orbit_view00,')
print('         orbitOK_05 == orbit_view05')
print('  (c) 3 files that were never written to disk')
print()
print('=== exact duplicate pairs (byte-identical AND same sub-second mtime) ===')
for f1 in files:
    for f2 in files:
        if f1 < f2 and md5[f1] == md5[f2] and abs(mt[f1]-mt[f2]) < 0.5:
            print('  %s  ==  %s' % (f1, f2))