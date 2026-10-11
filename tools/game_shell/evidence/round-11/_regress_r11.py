"""Round-11 STEP E: regression probes on the scratch engine (:8119).

1. /tick_pose knee_L 40 while UNARMED must answer ok:true (the tendon drive
   refusal law only applies while the drive owns the pin).
2. Wake/pressure flow: arm the reflexes, press the belly with the prior
   round's probe pattern (POST /tick_touch px/py/force_n), read the pressure
   response out of /tick_state, then clear and disarm the reflexes.
3. Tendon state must still read unarmed/severed-frozen afterwards.
"""
import json, time, urllib.request

BASE = "http://127.0.0.1:8119"
OUT = open("E:/PythonChimera/tools/game_shell/evidence/round-11/11_regression_probe.txt", "w",
           encoding="utf-8")


def say(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True); OUT.write(m + "\n"); OUT.flush()


def post(path, obj=None):
    # COMPACT-JSON law (main.cpp /tick_reflex): the master "on" arms on the
    # literal substring "on":true -- a space parses as FALSE. No separators.
    data = json.dumps(obj, separators=(",", ":")).encode() if obj is not None else b""
    req = urllib.request.Request(BASE + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def state():
    with urllib.request.urlopen(BASE + "/tick_state", timeout=30) as r:
        return json.loads(r.read())


KEY = ("damage_sum", "failed", "capacity_sum", "force_l", "force_r",
       "load_l", "load_r", "reflex_cell_count", "tendon_armed", "tendon_severed")

s = state()
say("tendon before pose probe: armed", s["tendon_armed"], "severed", s["tendon_severed"])
say("1. /tick_pose knee_L 40 (unarmed):", post("/tick_pose", {"joint": "knee_L", "deg": 40}))
say("   /tick_pose knee_L 40 by index 15:", post("/tick_pose", {"joint_index": 15, "deg": 40}))

say("2. reflex arm:", post("/tick_reflex", {"on": True}))
b = {k: s.get(k) for k in KEY}
say("   before press:", json.dumps(b))

# THE BELLY POINT, read from the engine's own posed surface (GET /verts:
# [u32 n][f32*9n]) -- the front-most vertex at mid-body height. The press
# then uses the {"hit":[x,y,z]} form, which is camera-independent.
import struct
with urllib.request.urlopen(BASE + "/verts", timeout=60) as r:
    raw = r.read()
n = struct.unpack_from("<I", raw, 0)[0]
v = struct.unpack_from("<" + "f" * (9 * n), raw, 4)
ys = [v[i * 9 + 1] for i in range(n)]
y0, y1 = min(ys), max(ys)
ymid = 0.5 * (y0 + y1)
best, bestz = None, -1e9
for i in range(n):
    x, y, z = v[i * 9], v[i * 9 + 1], v[i * 9 + 2]
    if abs(y - ymid) < 0.12 * (y1 - y0) and z > bestz:
        bestz, best = z, (x, y, z)
say(f"   surface: {n} verts, y[{y0:.2f},{y1:.2f}], belly point={best}")
say("   belly press (hit form):",
    post("/tick_touch", {"hit": [round(best[0], 4), round(best[1], 4), round(best[2], 4)],
                         "force_n": 30000}))
time.sleep(1.5)
s2 = state()
a2 = {k: s2.get(k) for k in KEY}
say("   after press:", json.dumps(a2))
say("   reflex summary:", json.dumps(post("/tick_reflex", {"breathing": True})))
say("   touch clear:", post("/tick_touch_clear"))
time.sleep(1.0)
s3 = state()
say("   after clear:", json.dumps({k: s3.get(k) for k in KEY}))
say("   reflex off:", post("/tick_reflex", {"on": False}))

say("3. tendon after all probes: armed", s3["tendon_armed"], "severed", s3["tendon_severed"],
    "q_deg", round(s3["tendon_q_deg"], 3), "battery_J", round(s3["tendon_battery_J"], 4),
    "ledger frames", s3["tendon_ledger_frames"], "violations", s3["tendon_ledger_violations"])
OUT.close()
