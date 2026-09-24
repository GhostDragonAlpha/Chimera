"""R1 independent CLI battery (NOT W5's script): original M09 tool vs W5 home copy.
10 battery fixtures x {plain, --json} + 2 usage probes = 22 cases.
Compares (exit, stdout sha256, stderr sha256) triples. Also prints R1's own histogram.
"""
import hashlib, subprocess, sys
from pathlib import Path

WT = Path(r"E:/ChimeraWork/mvc-20260924")
FIX = WT / "material_volume_campaign/impl/W5_diag_promo/home/work"
ORIG = WT / "material_volume_campaign/agents/M09_diagnostic/material_volume_diagnostic.py"
HOME = Path(r"E:/ChimeraWork/mvc-20260924/material_volume_campaign/impl/W5_diag_promo/home/material_volume_diagnostic.py")
fixtures = sorted(p.name for p in FIX.glob("fixture_*.json"))
assert len(fixtures) == 10, fixtures
cases = []
for name in fixtures:
    arg = str(FIX / name)
    cases.append((f"{name}:plain", [arg]))
    cases.append((f"{name}:json", [arg, "--json"]))
cases.append(("usage:no_args", []))
cases.append(("usage:bad_flag", ["--definitely-not-a-flag"]))

env = {"PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
       "PATH": __import__("os").environ.get("PATH", "")}
mismatch = 0
hist = {}
for label, args in cases:
    outs = []
    for tool in (ORIG, HOME):
        p = subprocess.run([sys.executable, "-B", str(tool), *args],
                           capture_output=True, text=True, env=env, timeout=60)
        outs.append((p.returncode,
                     hashlib.sha256(p.stdout.encode()).hexdigest(),
                     hashlib.sha256(p.stderr.encode()).hexdigest()))
    hist[outs[0][0]] = hist.get(outs[0][0], 0) + 1
    status = "SAME" if outs[0] == outs[1] else "MISMATCH"
    if outs[0] != outs[1]:
        mismatch += 1
        print(f"{status} {label}: orig={outs[0]} home={outs[1]}")
    else:
        print(f"{status} {label}: exit={outs[0][0]}")
print(f"\ncases={len(cases)} mismatches={mismatch}")
print("R1 exit histogram (original tool):", hist)
