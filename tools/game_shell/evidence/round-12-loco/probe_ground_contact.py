# tools/game_shell/evidence/round-12-loco/probe_ground_contact.py
# Round-12 locomotion spike, deliverable D probe. Runs against the scratch
# engine on :8119 ONLY (launched with --loco-spike, creature loaded).
# Every step snapshots /tick_state (and /loco_state when armed) into a
# JSON evidence file. Numbers in the report come from this run.
import json, time, urllib.request, sys

BASE = "http://127.0.0.1:8119"
OUT = "E:/PythonChimera/tools/game_shell/evidence/round-12-loco/probe_ground_contact.json"

def req(route, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    r = urllib.request.Request(BASE + route, data=data,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)

KEYS = ["gravity_on","root_y","root_vy","g_contact_n","stance_on","gait_on",
        "tendon_armed","tendon_q_deg","tendon_F_n","tendon_battery_J",
        "tendon_ledger_max_err_J","tendon_ledger_violations",
        "body_model","n_cells","sealed","V_lower","P_lower"]

def snap(label, extra=None):
    st = req("/tick_state")
    rec = {"label": label, "t": time.time()}
    for k in KEYS:
        if k in st: rec[k] = st[k]
    rec["root_keys"] = sorted([k for k in st if "root" in k])
    if extra:
        rec["loco"] = req("/loco_state")
    return rec

log = {"steps": []}
def step(label, **kw):
    r = {"label": label}
    r.update(kw)
    log["steps"].append(r)
    print(label, json.dumps({k: v for k, v in r.items() if k != "label"}))

t0 = req("/tick_state")
log["boot_state"] = {k: t0.get(k) for k in KEYS}
step("boot", root_y=t0.get("root_y"), g_contact_n=t0.get("g_contact_n"),
     body_model=t0.get("body_model"))

# ── 1. gravity ON: does the ground support the body? ──────────────────────
g = req("/tick_gravity", {"on": True})
step("gravity_arm_response", ok=g.get("ok"))
time.sleep(2.0)   # settle
s = snap("gravity_settled_2s")
log["gravity_settled"] = s
step("gravity_settled", root_y=s["root_y"], root_vy=s["root_vy"],
     g_contact_n=s["g_contact_n"])

# ── 2. pose limbs INTO the ground: does contact force change? ────────────
before = snap("pose_before")
poses = [("knee_L", -60.0), ("hip_L", 40.0), ("ankle_L", -30.0),
         ("knee_L", 0.0), ("hip_L", 0.0), ("ankle_L", 0.0)]
pose_rows = []
for name, deg in poses:
    r = req("/tick_pose", {"joint": name, "deg": deg})
    time.sleep(0.6)
    st = snap("pose_" + name)
    pose_rows.append({"pose": f"{name}={deg}", "ok": r.get("ok"),
                      "root_y": st["root_y"], "g_contact_n": st["g_contact_n"],
                      "root_vy": st["root_vy"]})
log["pose_probe"] = {"before": before, "rows": pose_rows}
step("pose_probe_done", rows=json.dumps(pose_rows))

# ── 3. shipped tendon drive (knee_L pin 15) under gravity ─────────────────
e = req("/tick_effort", {"joint_index": 15, "u": 1.0})
step("effort_arm", ok=e.get("ok"))
drive_rows = []
for i in range(8):
    time.sleep(0.5)
    st = snap("drive_t%.1f" % (0.5 * (i + 1)))
    drive_rows.append({"t": 0.5 * (i + 1), "tendon_q_deg": st["tendon_q_deg"],
                       "tendon_F_n": st["tendon_F_n"],
                       "root_y": st["root_y"], "g_contact_n": st["g_contact_n"],
                       "battery_J": st["tendon_battery_J"],
                       "ledger_err": st["tendon_ledger_max_err_J"]})
req("/tick_effort", {"joint_index": 15, "u": -1.0})   # disarm
log["drive_probe"] = drive_rows
step("drive_probe_done", rows=json.dumps(drive_rows))

# ── 4. LOCO SPIKE bank: 3 drives + scripted anti-phase ───────────────────
a1 = req("/loco_arm", {"joint_index": 15, "u": 0.5})
a2 = req("/loco_arm", {"joint_index": 16, "u": 0.5})
a3 = req("/loco_arm", {"joint_index": 13, "u": 0.5})
step("loco_arm", r15=a1.get("ok"), r16=a2.get("ok"), r13=a3.get("ok"))
# pose refusal on an owned pin (ownership law check)
own = req("/tick_pose", {"joint": "knee_R", "deg": 10.0})
step("pose_refusal_owned_pin", ok=own.get("ok"), err=own.get("error"))
sc = req("/loco_script", {"on": True, "freq_hz": 1.2, "lo": 0.05,
                          "hi": 0.95, "phase_rad": 0.0})
step("loco_script_on", ok=sc.get("ok"), err=sc.get("error"))
bank_rows = []
for i in range(16):
    time.sleep(0.25)
    st = snap("bank_t%.2f" % (0.25 * (i + 1)), extra=True)
    ls = st["loco"]
    bank_rows.append({"t": 0.25 * (i + 1), "root_y": st["root_y"],
                      "root_vy": st["root_vy"], "g_contact_n": st["g_contact_n"],
                      "loco_t_s": ls.get("loco_t_s"),
                      "loco_max_err_J": ls.get("loco_ledger_max_err_J"),
                      "loco_frames": ls.get("loco_ledger_frames"),
                      "loco_violations": ls.get("loco_ledger_violations"),
                      "pins": {d["pin"]: {"q_deg": d["q_deg"], "tau_nm": d["tau_nm"],
                                          "ledger_err_J": d["ledger_err_J"]}
                               for d in ls.get("loco_drives", [])}})
req("/loco_script", {"on": False})
for p in (15, 16, 13):
    req("/loco_arm", {"joint_index": p, "u": -1.0})
log["bank_probe"] = bank_rows
ry = [r["root_y"] for r in bank_rows]
gc = [r["g_contact_n"] for r in bank_rows]
step("bank_probe_done", root_y_min=min(ry), root_y_max=max(ry),
     g_contact_min=min(gc), g_contact_max=max(gc),
     max_err_J=max(r["loco_max_err_J"] for r in bank_rows),
     violations=max(r["loco_violations"] for r in bank_rows))

# ── 5. stance/gait machines on the JNT3 body (expected refusal) ───────────
st1 = req("/tick_stance", {"on": True})
gt1 = req("/tick_gait", {"on": True})
step("stance_gait_on_jnt3", stance_ok=st1.get("ok"), stance_err=st1.get("error"),
     gait_ok=gt1.get("ok"), gait_err=gt1.get("error"))

# ── 6. horizontal root channel: does ANY root x/z state exist? ────────────
fin = req("/tick_state")
log["final_state_root_keys"] = sorted([k for k in fin if "root" in k])
log["final_state_has_xz"] = [k for k in fin if "root_x" in k or "root_z" in k]
step("root_dof_fields", root_keys=log["final_state_root_keys"],
     xz_fields=log["final_state_has_xz"])

req("/tick_gravity", {"on": False})
json.dump(log, open(OUT, "w"), indent=1)
print("WROTE", OUT)
