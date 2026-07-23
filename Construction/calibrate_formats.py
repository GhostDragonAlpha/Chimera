"""Format calibration: load the SAME model (bonsai @7k iterations) from .ply and .splat and
compare the DNA feature distributions. They must match — any systematic gap is a container
conversion bug (scale log-vs-linear, colour activation, opacity logit) that would poison the
material library by making the genome depend on the FILE FORMAT instead of the material."""
import sys, numpy as np
sys.path.insert(0, "E:/PythonChimera")
from Construction.ksplat_io import load_any

D = "E:/PythonChimera/WorldModel/training_data/downloads/dyl"
pairs = [(".ply  (INRIA)", D + "/bonsai_7k.ply"), (".splat (a15)", D + "/bonsai_bonsai-7k.splat")]
out = {}
for name, path in pairs:
    pos, rgb, op, sc, q = load_any(path, full=True)
    out[name] = (pos, rgb, op, sc)
    print(f"{name:14} n={len(pos):>10,}   bbox={(pos.max(0)-pos.min(0)).round(2)}")

print(f"\n{'feature':10}{'format':16}{'p10':>10}{'p50':>10}{'p90':>10}{'mean':>10}")
print("-" * 66)
for feat, get in [("scale", lambda t: t[3].mean(1)), ("R", lambda t: t[1][:, 0]), ("G", lambda t: t[1][:, 1]),
                  ("B", lambda t: t[1][:, 2]), ("opacity", lambda t: t[2])]:
    for name, t in out.items():
        v = np.nan_to_num(get(t)); p = np.percentile(v, [10, 50, 90])
        print(f"{feat:10}{name:16}{p[0]:>10.4f}{p[1]:>10.4f}{p[2]:>10.4f}{v.mean():>10.4f}")
    print()
