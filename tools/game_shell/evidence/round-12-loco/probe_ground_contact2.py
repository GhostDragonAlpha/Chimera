# tools/game_shell/evidence/round-12-loco/probe_ground_contact2.py
# Round-12 probe 2: (a) correct stance/gait payloads (the routes parse
# "on":true as a literal substring -- main.cpp:1584/1590 -- so compact
# JSON is required); (b) the bank probe FROM A SETTLED, GROUNDED state;
# (c) the pose-launch event at 50 ms resolution. :8119 ONLY.
import json, time, urllib.request

BASE = "http://127.0.0.1:8119"
OUT = "E:/PythonChimera/tools/game_shell/evidence/round-12-loco/probe_ground_contact2.json"

def req(route, raw=None):
    data = raw.encode() if raw is not None else None
    r = urllib.request.Request(BASE + route, data=data,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)

def state():
    return req("/tick_state")

log = {}
def p(*a):
    print(*a, flush=True)

# ── 0. fresh settle: gravity off then on ──────────────────────────────────
req("/tick_gravity", '{"on":true}')
time.sleep(3.0)
s0 = state()
log["settled"] = {k: s0[k] for k in ("root_y","root_vy","g_contact_n","gravity_on")}
p("settled:", log["settled"])

# ── 1. stance/gait with the payload the routes actually parse ────────────
st = req("/tick_stance", '{"on":true}')
gt = req("/tick_gait", '{"on":true}')
log["stance_gait_jnt3"] = {"stance": st, "gait": gt,
    "stance_on_after": state()["stance_on"], "gait_on_after": state()["gait_on"]}
p("stance/gait on JNT3:", log["stance_gait_jnt3"])

# ── 2. the pose-launch event at 50 ms ────────────────────────────────────
launch = []
req("/tick_pose", '{"joint":"knee_L","deg":-60.0}')
for i in range(40):
    stt = state()
    launch.append({"t_ms": i*50, "root_y": stt["root_y"],
                   "root_vy": stt["root_vy"], "g_contact_n": stt["g_contact_n"]})
    time.sleep(0.05)
log["launch_event"] = launch
p("launch: root_y max %.3f  g_contact max %.0f N (cap %.0f N = 50mg)" % (
    max(r["root_y"] for r in launch), max(r["g_contact_n"] for r in launch),
    50*13824.5*9.81))
# recover: gravity off/on resets to authored rest exactly
req("/tick_gravity", '{"on":false}')
time.sleep(0.5)
req("/tick_gravity", '{"on":true}')
time.sleep(3.0)
s1 = state()
log["resettled"] = {k: s1[k] for k in ("root_y","root_vy","g_contact_n")}
p("resettled:", log["resettled"])

# ── 3. grounded bank probe: 3 drives, scripted anti-phase, 6 s ───────────
for pin in (15, 16, 13):
    req("/loco_arm", '{"joint_index":%d,"u":0.5}' % pin)
sc = req("/loco_script", '{"on":true,"freq_hz":1.2,"lo":0.05,"hi":0.95,"phase_rad":0.0}')
p("script on:", sc)
bank = []
for i in range(60):                      # 6 s at 100 ms
    stt = state()
    ls = json.loads(urllib.request.urlopen(BASE + "/loco_state").read())
    bank.append({"t_ms": i*100, "root_y": stt["root_y"], "root_vy": stt["root_vy"],
                 "g_contact_n": stt["g_contact_n"],
                 "loco_err_J": ls["loco_ledger_max_err_J"],
                 "loco_frames": ls["loco_ledger_frames"],
                 "loco_viol": ls["loco_ledger_violations"],
                 "q": {str(d["pin"]): round(d["q_deg"], 2) for d in ls["loco_drives"]},
                 "tau": {str(d["pin"]): round(d["tau_nm"], 3) for d in ls["loco_drives"]}})
    time.sleep(0.1)
req("/loco_script", '{"on":false}')
for pin in (15, 16, 13):
    req("/loco_arm", '{"joint_index":%d,"u":-1.0}' % pin)
log["bank_grounded"] = bank
ry = [r["root_y"] for r in bank]
gc = [r["g_contact_n"] for r in bank]
vy = [r["root_vy"] for r in bank]
p("bank grounded: root_y [%.5f, %.5f]  root_vy [%.4f, %.4f]" % (min(ry), max(ry), min(vy), max(vy)))
p("               g_contact_n [%.1f, %.1f] N  (mg=135618.3)" % (min(gc), max(gc)))
p("               loco ledger max err %.3e J, violations %d" % (
    max(r["loco_err_J"] for r in bank), max(r["loco_viol"] for r in bank)))

# ── 4. horizontal displacement witness: verts centroid x/z over the bank ─
# (root has no x/z DOF; a limb-driven horizontal shift of the WHOLE posed
# body would still show in the exported vertex centroid if any channel
# existed. Sample before/after a hard knee swing.)
def centroid_xz():
    import struct, urllib.request as u
    raw = u.urlopen(BASE + "/tick_body_bin").read() if False else None
    # /verts is the export the page renders; use it if present, else skip
    return None
log["note"] = ("root DOF fields in /tick_state: root_y, root_vy only "
               "(probe 1 root_keys); no root_x/root_z exists.")
json.dump(log, open(OUT, "w"), indent=1)
p("WROTE", OUT)
