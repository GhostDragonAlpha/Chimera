"""seal2_run.py -- THE SEAL v2 live verification driver (prereg 4eb9480c).

Runs the S1'-S5' bars against the engine on 8107 in one clean sequence
and writes every response to .tmp/seal2_run.log for the run record.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8107"
PROOF = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\FEET")
LOG = Path(r"E:\ChimeraWork\slot-01\.tmp\seal2_run.log")
KAPPA = 4.6e-10


def req(method, path, body=None, timeout=30):
    r = urllib.request.Request(BASE + path, data=body, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read()


def post_json(path, obj):
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


note(f"seal2 run @ {time.strftime('%Y-%m-%d %H:%M:%S')}")

# S5'a -- refusals BEFORE the seal (cause = out of body, unambiguous)
for bad in (99.9, -5.0):
    note(f"S5'a refusal y={bad}: {post_json('/tick_seal', {'y': bad})}")

# evidence frame: the creature at rest, before the seal
note(f"frame: {frame('seal2_before_rest.png')}")

# S4' -- the mitosis intent
note(f"S4' seal y=2.6: {post_json('/tick_seal', {'y': 2.6})}")
time.sleep(1.5)
s = state()
note(f"S1'/S2' rest state: {json.dumps(s)}")
vl, vu, vw = s["V_lower"], s["V_upper"], s["V_whole"]
note(f"S2' rest: V_lower+V_upper = {vl + vu:.7f} vs V_whole {vw:.7f} "
     f"({s['conserve_pct_pct'] if 'conserve_pct_pct' in s else s['conserve_pct']} %), "
     f"sum vs 13.8245 m^3 target: {abs(vl + vu - 13.8245) / 13.8245 * 100:.2e} %")
note(f"S3' rest pressures: P_lower={s['P_lower']}, P_upper={s['P_upper']} (bar: |P| < 1 kPa)")

# S5'b -- re-seal refused (cause = already sealed)
note(f"S5'b re-seal: {post_json('/tick_seal', {'y': 2.6})}")

# S2'/S3' under pose: hip_L (joint 13) 30 deg
note(f"pose hip_L 30: {post_json('/tick_pose', {'joint_index': 13, 'deg': 30})}")
time.sleep(1.5)
s = state()
note(f"posed state: V_lower={s['V_lower']:.7f} V_upper={s['V_upper']:.7f} "
     f"V_whole={s['V_whole']:.7f} conserve={s['conserve_pct']} %")
note(f"posed pressures: P_lower={s['P_lower']:.1f} Pa P_upper={s['P_upper']:.1f} Pa")
pl_expected = (s["v0_lower"] - s["V_lower"]) / (KAPPA * s["v0_lower"])
pu_expected = (s["v0_upper"] - s["V_upper"]) / (KAPPA * s["v0_upper"])
note(f"kappa-law check: P_lower expected {pl_expected:.1f} Pa "
     f"(got {s['P_lower']:.1f}), P_upper expected {pu_expected:.1f} Pa "
     f"(got {s['P_upper']:.1f})")
dvl = s["V_lower"] - s["v0_lower"]
note(f"S3' response: dV_lower = {dvl:+.7f} m^3 -> P_lower {s['P_lower']:+.1f} Pa "
     f"(sign {'OK' if (dvl > 0) == (s['P_lower'] < 0) else 'WRONG'}: "
     f"{'expansion' if dvl > 0 else 'compression'} {'lowers' if s['P_lower'] < 0 else 'raises'} P)")
note(f"frame: {frame('seal2_posed_hipL30.png')}")

# S3' return: pose back to 0 -> P back to ~0
note(f"pose hip_L 0: {post_json('/tick_pose', {'joint_index': 13, 'deg': 0})}")
time.sleep(1.5)
s = state()
note(f"returned state: V_lower={s['V_lower']:.7f} V_upper={s['V_upper']:.7f} "
     f"V_whole={s['V_whole']:.7f} conserve={s['conserve_pct']} %")
note(f"S3' return: P_lower={s['P_lower']} Pa, P_upper={s['P_upper']} Pa "
     f"(bar: |P| < 1 kPa = 1000 Pa)")
note(f"frame: {frame('seal2_returned_rest.png')}")

note("run complete")
LOG.write_text("\n".join(log) + "\n")
print(f"\nlog -> {LOG}")
