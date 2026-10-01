"""mitosis_run.py -- THE MITOSIS OP live verification driver (prereg
be971e7c). One clean instance: hip -> knee -> ankle cuts, M1-M4 bars,
frames to CHIMERA_PROOF\\FEET, log to .tmp/mitosis_run.log."""
import json
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8107"
PROOF = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\FEET")
LOG = Path(r"E:\ChimeraWork\slot-01\.tmp\mitosis_run.log")
KAPPA = 4.6e-10
DERIVED = {  # offline prototype, corrected winding
    "hip":   {"parent": 13.824536, "below": 1.315499, "above": 12.509037},
    "knee":  {"parent": 1.315499,  "below": 0.622492, "above": 0.693007},
    "ankle": {"parent": 0.622492,  "below": 0.287914, "above": 0.334577},
}


def req(method, path, body=None, timeout=30):
    r = urllib.request.Request(BASE + path, data=body, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read()


def post(path, obj):
    return req("POST", path, json.dumps(obj).encode()).decode()


def state():
    return json.loads(req("GET", "/tick_state"))


def frame(name):
    PROOF.mkdir(parents=True, exist_ok=True)
    (PROOF / name).write_bytes(req("GET", "/frame", timeout=60))
    return name


log = []


def note(s):
    print(s)
    log.append(s)


def check_cells(s, tag):
    tot = sum(c["V"] for c in s["cells"])
    ok = True
    for i, c in enumerate(s["cells"]):
        dv = c["V"] - c["v0"]
        note(f"  {tag} cell {i}: v0={c['v0']:.6f} V={c['V']:.6f} P={c['P']:.1f} Pa "
             f"pieces={c['pieces']} caps={c['caps']} y[{c['ylo']:.3f},{c['yhi']:.3f}]")
        if abs(c["P"]) > 1000.0:
            ok = False
            note(f"    !! rest pressure {c['P']:.1f} Pa exceeds 1 kPa")
    note(f"  {tag} sum={tot:.6f} vs V_whole={s['V_whole']:.6f} "
         f"conserve={s['conserve_pct']:.2e}% n_cells={s['n_cells']}")
    return ok


note(f"mitosis run @ {time.strftime('%Y-%m-%d %H:%M:%S')}")

# M4 refusals BEFORE any cut: bad cell index, out-of-range plane
note(f"M4 refusal cell=7 (no such cell): {post('/tick_seal', {'y': 2.6, 'cell': 7})}")
note(f"M4 refusal y=99.9: {post('/tick_seal', {'y': 99.9})}")
note(f"frame: {frame('mitosis0_before.png')}")

# M1: hip cut
note(f"M1 hip cut: {post('/tick_seal', {'y': 3.415})}")
time.sleep(1.5)
s = state()
d = DERIVED["hip"]
for i, want in enumerate((d["below"], d["above"])):
    got = s["cells"][i]["v0"]
    err = abs(got - want) / want * 100
    note(f"M1 cell {i} v0={got:.6f} vs derived {want:.6f} ({err:.2e}%) "
         f"{'PASS' if err < 1 else 'FAIL'}")
check_cells(s, "M1")
note(f"  last-cut: split={s['seal_split']} cuts={s['seal_cuts']} "
     f"loops={s['seal_loops']} caps={s['seal_caps']}")

# M2: knee cut on cell 0 (the leg cell), then ankle on cell 0 (shin+foot)
note(f"M2 knee cut cell 0: {post('/tick_seal', {'y': 1.903, 'cell': 0})}")
time.sleep(1.5)
s = state()
d = DERIVED["knee"]
got0, last = s["cells"][0]["v0"], s["cells"][-1]["v0"]
note(f"M2 knee: shin+foot v0={got0:.6f} vs {d['below']:.6f} "
     f"({abs(got0 - d['below']) / d['below'] * 100:.2e}%), "
     f"thigh v0={last:.6f} vs {d['above']:.6f} "
     f"({abs(last - d['above']) / d['above'] * 100:.2e}%)")
check_cells(s, "M2-knee")

note(f"M2 ankle cut cell 0: {post('/tick_seal', {'y': 0.338, 'cell': 0})}")
time.sleep(1.5)
s = state()
d = DERIVED["ankle"]
got0, last = s["cells"][0]["v0"], s["cells"][-1]["v0"]
note(f"M2 ankle: foot v0={got0:.6f} vs {d['below']:.6f} "
     f"({abs(got0 - d['below']) / d['below'] * 100:.2e}%), "
     f"shin v0={last:.6f} vs {d['above']:.6f} "
     f"({abs(last - d['above']) / d['above'] * 100:.2e}%)")
ok_rest = check_cells(s, "M2-ankle")
note(f"  final cell map: {[round(c['v0'], 4) for c in s['cells']]} "
     f"(foot, body, thigh, shin)")

# M4: plane outside the named cell's range (foot cell 0 tops at 0.338)
note(f"M4 refusal y=2.0 on foot cell 0: {post('/tick_seal', {'y': 2.0, 'cell': 0})}")

# M3: per-cell hydraulics under a knee pose (joint 15 = knee_L, 25 deg)
note(f"frame: {frame('mitosis1_rest4cells.png')}")
note(f"M3 pose knee_L 25: {post('/tick_pose', {'joint_index': 15, 'deg': 25})}")
time.sleep(1.5)
s = state()
names = ["foot", "body", "thigh", "shin"]
for i, c in enumerate(s["cells"]):
    dV = c["V"] - c["v0"]
    pexp = (c["v0"] - c["V"]) / (KAPPA * c["v0"])
    note(f"M3 posed {names[i]:5s}: dV={dV:+.6f} m^3 P={c['P'] / 1e6:+9.3f} MPa "
         f"(kappa-law {pexp / 1e6:+9.3f})")
tot = sum(c["V"] for c in s["cells"])
note(f"M3 posed: sum={tot:.6f} vs whole={s['V_whole']:.6f} "
     f"conserve={s['conserve_pct']:.2e}%")
note(f"frame: {frame('mitosis2_posed_kneeL25.png')}")

# M3 return
note(f"M3 pose knee_L 0: {post('/tick_pose', {'joint_index': 15, 'deg': 0})}")
time.sleep(1.5)
s = state()
worst = max(abs(c["P"]) for c in s["cells"])
note(f"M3 return: worst |P| = {worst:.1f} Pa (bar: < 1000 Pa)")
check_cells(s, "M3-return")
note(f"frame: {frame('mitosis3_returned.png')}")

note("run complete")
LOG.write_text("\n".join(log) + "\n")
print(f"\nlog -> {LOG}")
