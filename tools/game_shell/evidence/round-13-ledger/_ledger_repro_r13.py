"""Round-13 verification (HTTP direct-to-engine): the arm-time ledger
continuity fix (tendon_drive.hpp init_at + tendon_reset_ q0) against the
round-12 repro sequence, on a FRESH creature scene (joint q = 0).

Context A: arm from the authored REST pose (fresh binding zeroes
           joint_deg_, theta_rest = 0 -> the fix is a no-op there; the
           numbers must match round-12 A_after_arm_from_rest on the
           deterministic arm-time fields, ~1e-9).
Context B: limp the tendon (arm -> sever -> settle -> disarm), then
           RE-ARM from the limp pose. Pre-fix (round-12): violations ==
           frames, constant 1.1111 J. Post-fix prediction: 0 violations,
           max err ~1e-12, elastic0 = full tendon+capsule energy at the
           limp angle.

Same snapshot keys, tags and format as round-12/12_ledger_repro.txt.
Engine routes used directly (round-12 used the shell proxy on :8210):
/tick_effort, /tick_sever, /tick_state. No source edits, no kills here.
"""
import json, time, urllib.request

GAME = "http://127.0.0.1:8119"
EV = r"E:\PythonChimera\tools\game_shell\evidence\round-13-ledger"
out = []


def get(path):
    with urllib.request.urlopen(GAME + path, timeout=10) as r:
        return json.loads(r.read())


def post(path, obj):
    req = urllib.request.Request(GAME + path, data=json.dumps(obj).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def snap(tag):
    s = get("/tick_state")
    d = {k: s.get(k) for k in ("tendon_armed", "tendon_severed", "tendon_q_deg",
                               "tendon_elastic_J", "tendon_elastic0_J",
                               "tendon_work_J", "tendon_heat_J",
                               "tendon_battery_J", "tendon_ledger_max_err_J",
                               "tendon_ledger_frames", "tendon_ledger_violations")}
    d["tag"] = tag
    out.append(d)
    print(json.dumps(d), flush=True)
    return d


# ---- Context A: short arm from the authored REST pose (fresh scene) ----
pre = snap("A_pre_rest")
post("/tick_effort", {"joint_index": 15, "u": 0.6}); time.sleep(1.5)
post("/tick_effort", {"joint_index": 15, "u": -1}); time.sleep(0.5)
snap("A_after_arm_from_rest")

# ---- Context B: limp the tendon (arm, sever, settle, disarm), then arm ----
post("/tick_effort", {"joint_index": 15, "u": 1}); time.sleep(1.5)
post("/tick_sever", {"joint_index": 15}); time.sleep(3.5)
post("/tick_effort", {"joint_index": 15, "u": -1}); time.sleep(0.5)
pre_b = snap("B_pre_limp")
post("/tick_effort", {"joint_index": 15, "u": 0.6}); time.sleep(1.5)
post("/tick_effort", {"joint_index": 15, "u": -1}); time.sleep(0.5)
snap("B_after_arm_from_limp")

# leave the tendon UNSEVERED + disarmed at the authored rest for teardown
post("/tick_effort", {"joint_index": 15, "u": 0.05}); time.sleep(0.6)
post("/tick_effort", {"joint_index": 15, "u": -1}); time.sleep(0.5)
snap("Z_final")

with open(f"{EV}/13_ledger_armfix_repro.txt", "w") as f:
    f.write("ledger arm-continuity fix repro: arm-from-rest vs arm-from-limp "
            "(round-13, post-fix, fresh scene)\n")
    for d in out:
        f.write(json.dumps(d) + "\n")
print("done", flush=True)
