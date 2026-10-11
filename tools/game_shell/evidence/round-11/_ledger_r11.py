"""Round-11 STEP D: the per-frame energy-ledger guard, exercised live.

Arm the knee_L tendon drive (/tick_effort u=0.6), run >= 600 armed frames,
read the guard's own counters out of /tick_state AND recompute the invariant
independently from the 10 published ledger fields, then sever, then disarm.
Engine stderr carries the guard's 300-frame summaries (11_ledger_guard.txt).
"""
import json, time, urllib.request

BASE = "http://127.0.0.1:8119"
OUT = open("E:/PythonChimera/tools/game_shell/evidence/round-11/11_ledger_probe.txt", "w",
           encoding="utf-8")


def say(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True); OUT.write(m + "\n"); OUT.flush()


def post(path, obj):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def state():
    with urllib.request.urlopen(BASE + "/tick_state", timeout=20) as r:
        return json.loads(r.read())


F10 = ("tendon_armed", "tendon_severed", "tendon_q_deg", "tendon_F_n",
       "tendon_battery_J", "tendon_battery0_J", "tendon_work_J",
       "tendon_heat_J", "tendon_elastic_J", "tendon_elastic0_J")

s0 = state()
say("baseline unarmed:", {k: s0[k] for k in F10})
say("armed before arm:", s0["tendon_armed"], "guard frames:", s0["tendon_ledger_frames"])

say("arm:", post("/tick_effort", {"joint_index": 15, "u": 0.6}))

frames = 0
worst_http = 0.0
samples = []
t0 = time.time()
while time.time() - t0 < 40.0:
    s = state()
    frames = s["tendon_ledger_frames"]
    drain = s["tendon_battery0_J"] - s["tendon_battery_J"]
    expect = s["tendon_work_J"] + s["tendon_heat_J"] + (s["tendon_elastic_J"] - s["tendon_elastic0_J"])
    err_http = abs(drain - expect)
    worst_http = max(worst_http, err_http)
    if len(samples) < 6 or frames >= 600:
        samples.append((frames, s["tendon_ledger_max_err_J"], s["tendon_ledger_violations"],
                        err_http, drain, expect, s["tendon_q_deg"], s["tendon_F_n"],
                        s["tendon_battery_J"]))
    if frames >= 600 and not s["tendon_armed"]:
        break
    if frames >= 660:
        break
    time.sleep(0.5)

say(f"armed frames observed: {frames} (elapsed {time.time()-t0:.1f} s)")
say("frame  guardMaxErr      guardViol  httpErr        drain            expected         q_deg   F_n     battery_J")
for f, gm, gv, eh, dr, ex, q, fn, bt in samples:
    say(f"{f:6d} {gm:.3e}  {gv:8d}  {eh:.3e}  {dr:.9f}  {ex:.9f}  {q:7.2f} {fn:8.2f} {bt:9.3f}")

s1 = state()
say("guard max err (engine):", f"{s1['tendon_ledger_max_err_J']:.3e} J",
    "| violations:", s1["tendon_ledger_violations"], "| frames:", s1["tendon_ledger_frames"])
say("max err recomputed over HTTP fields:", f"{worst_http:.3e} J")
say("GUARD PASS" if (frames >= 600 and s1["tendon_ledger_violations"] == 0
                     and s1["tendon_ledger_max_err_J"] < 1e-6 and worst_http < 1e-6)
    else "GUARD CHECK")

say("sever:", post("/tick_sever", {"joint_index": 15}))
time.sleep(1.0)
s2 = state()
say("after sever: armed", s2["tendon_armed"], "severed", s2["tendon_severed"],
    "F_n", round(s2["tendon_F_n"], 3), "q_deg", round(s2["tendon_q_deg"], 3))
say("disarm:", post("/tick_effort", {"joint_index": 15, "u": -1}))
time.sleep(0.5)
s3 = state()
say("after disarm: armed", s3["tendon_armed"], "severed", s3["tendon_severed"],
    "guard frames", s3["tendon_ledger_frames"])
OUT.close()
