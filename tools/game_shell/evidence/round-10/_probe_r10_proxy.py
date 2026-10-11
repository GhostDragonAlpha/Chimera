"""Round-10 STEP 2: numeric probe THROUGH THE SHELL PROXY (:8210).

Exercises the exact HTTP path the page uses: GET /api/state,
POST /api/effort -> /tick_effort, POST /api/sever -> /tick_sever,
plus the disarm regression and the slider-drag rate-limit check.
Shared stack :8110/:8210 (already running); never kills anything.
Evidence: round-10/10_probe_proxy.json + printed log.
"""
import time, json, sys, urllib.request, urllib.error

GAME = "http://127.0.0.1:8210"
R = {}


def get(path):
    with urllib.request.urlopen(GAME + path, timeout=10) as r:
        return json.loads(r.read())


def post(path, obj):
    req = urllib.request.Request(GAME + path, data=json.dumps(obj).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")[:120]}
    except Exception as e:
        return -1, {"error": str(e)}


def tstate():
    st = get("/api/state")
    return {k: st.get(k) for k in ("tendon_armed", "tendon_severed",
                                   "tendon_q_deg", "tendon_F_n",
                                   "tendon_battery_J")}


print("== a. GET /api/state tendon fields ==", flush=True)
st = get("/api/state")
tk = sorted(k for k in st if k.startswith("tendon"))
R["a_tendon_keys"] = tk
R["a_pass"] = all(k in st for k in ("tendon_armed", "tendon_severed",
                                    "tendon_q_deg", "tendon_battery_J"))
print("keys:", tk, "PASS:", R["a_pass"], flush=True)

print("== b. POST /api/effort u=1 -> q crosses 40 ==", flush=True)
code, body = post("/api/effort", {"joint_index": 15, "u": 1})
R["b_arm_status"] = code
R["b_arm_body"] = body
t0 = time.time()
qmax = 0.0
bmin = 1e9
t_cross = None
samples = []
while time.time() - t0 < 12.0:
    s = tstate()
    q = s["tendon_q_deg"] or 0.0
    b = s["tendon_battery_J"] or 0.0
    qmax = max(qmax, q)
    bmin = min(bmin, b)
    if t_cross is None and q >= 40.0:
        t_cross = time.time() - t0
    samples.append((round(time.time() - t0, 2), round(q, 2), round(b, 1)))
    if t_cross is not None and q >= 100:
        break
    time.sleep(0.1)
R["b_qmax_deg"] = qmax
R["b_t_cross_40_s"] = t_cross
R["b_battery_min_J"] = bmin
R["b_samples_head"] = samples[:12]
R["b_pass"] = (code == 200 and t_cross is not None and bmin < 1000)
print(f"qmax={qmax:.2f} cross40_t={t_cross} battery_min={bmin:.1f}J "
      f"PASS: {R['b_pass']}", flush=True)

print("== c. POST /api/sever -> severed, q<5 ==", flush=True)
before = tstate()
code, body = post("/api/sever", {"joint_index": 15})
R["c_sever_status"] = code
R["c_sever_body"] = body
t0 = time.time()
after = before
while time.time() - t0 < 10.0:
    after = tstate()
    if after["tendon_severed"] and (after["tendon_q_deg"] or 0) < 5:
        break
    time.sleep(0.1)
R["c_before"] = before
R["c_after"] = after
R["c_pass"] = bool(after["tendon_severed"]) and (after["tendon_q_deg"] or 99) < 5
print(f"before q={before['tendon_q_deg']:.2f} severed={before['tendon_severed']} "
      f"-> after q={after['tendon_q_deg']:.2f} severed={after['tendon_severed']} "
      f"PASS: {R['c_pass']}", flush=True)

print("== d. POST /api/effort u=-1 -> disarm; pose knee_L 40 ok ==", flush=True)
code, body = post("/api/effort", {"joint_index": 15, "u": -1})
time.sleep(0.3)
s = tstate()
R["d_disarm_status"] = code
R["d_armed_after"] = s["tendon_armed"]
code2, body2 = post("/api/pose", {"joint": "knee_L", "deg": 40})
time.sleep(0.6)
R["d_pose_status"] = code2
R["d_pose_body"] = body2
post("/api/pose", {"joint": "knee_L", "deg": 0})
time.sleep(0.4)
R["d_pass"] = (s["tendon_armed"] is False and code2 == 200
               and body2.get("ok") is True)
print(f"armed_after_disarm={s['tendon_armed']} pose={code2} {body2} "
      f"PASS: {R['d_pass']}", flush=True)

print("== e. rate limit: 100 rapid /api/effort u ramp ==", flush=True)
codes = []
for i in range(100):
    c, _ = post("/api/effort", {"joint_index": 15, "u": i / 99.0})
    codes.append(c)
n429 = sum(1 for c in codes if c == 429)
R["e_codes"] = sorted(set(codes))
R["e_429_count"] = n429
R["e_pass"] = n429 == 0
post("/api/effort", {"joint_index": 15, "u": -1})   # disarm after drag
print(f"distinct codes={R['e_codes']} 429s={n429} PASS: {R['e_pass']}", flush=True)

R["overall"] = all(R[k] for k in ("a_pass", "b_pass", "c_pass", "d_pass", "e_pass"))
with open(r"E:\PythonChimera\tools\game_shell\evidence\round-10\10_probe_proxy.json", "w") as f:
    json.dump(R, f, indent=1)
print("OVERALL:", "PASS" if R["overall"] else "FAIL", flush=True)
sys.exit(0 if R["overall"] else 1)
