"""Round-09 STEP 2 integration probe: tendon drive on knee_L (pin 15).

SCRATCH stack ONLY: engine 8117 from .tmp/tendon-engine (own build), game
shell 8217 -> engine 8117. The shared :8110/:8210 stack is never touched.
Kills only the processes this script starts. Checks 1-6 (HTTP) then the
wake_the_cell + bend_the_knee regressions in headless Chromium, with the
sever screenshots taken live in the browser. Evidence: round-09/.
"""
import subprocess, time, json, math, struct, sys, os, tempfile
import urllib.request
import numpy as np

ROOT = r"E:\PythonChimera"
EV = ROOT + r"\tools\game_shell\evidence\round-09"
ENGINE = "http://127.0.0.1:8117"
GAME = "http://127.0.0.1:8217"
EXE = ROOT + r"\.tmp\tendon-engine\Release\chimera_engine.exe"
PY = sys.executable
log_lines = []
R = {}                      # machine record: check -> value/verdict


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log_lines.append(s)


def engine_get(path):
    with urllib.request.urlopen(ENGINE + path, timeout=10) as r:
        return r.read()


def engine_post(path, obj):
    req = urllib.request.Request(
        ENGINE + path, data=json.dumps(obj).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def state():
    return json.loads(engine_get("/tick_state"))


def verts():
    raw = engine_get("/verts")
    n = struct.unpack_from('<I', raw)[0]
    return np.frombuffer(raw, '<f4', 9 * n, 4).reshape(n, 9)[:, :3].astype(np.float64)


def ledger_err(st):
    return abs((st['tendon_battery0_J'] - st['tendon_battery_J'])
               - (st['tendon_work_J'] + st['tendon_heat_J']
                  + (st['tendon_elastic_J'] - st['tendon_elastic0_J'])))


procs = []


def cleanup():
    for p in reversed(procs):
        try:
            p.terminate()
            p.wait(timeout=8)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


try:
    os.makedirs(EV, exist_ok=True)
    # ---- boot the scratch engine + scene + game shell ------------------
    elog = open(os.path.join(ROOT, r".tmp\tendon-engine\scratch_8117.log"), "w")
    procs.append(subprocess.Popen(
        [EXE, "8117", "--hidden", "1600", "900", "--no-restore"],
        cwd=os.path.dirname(EXE), stdout=elog, stderr=elog))
    ready = False
    t0 = time.time()
    while time.time() - t0 < 40:
        try:
            state(); ready = True; break
        except Exception:
            time.sleep(0.3)
    R["engine_ready"] = ready
    log("engine 8117 ready:", ready, f"({time.time()-t0:.1f}s)")
    if not ready:
        raise RuntimeError("scratch engine did not become ready")
    rc = subprocess.run([PY, "-B", "-m", "tools.science_funnel.creature_scene",
                         "--engine", ENGINE], cwd=ROOT).returncode
    R["scene_rc"] = rc
    log("creature_scene rc:", rc)
    if rc != 0:
        raise RuntimeError("scene admission refused")
    glog = open(os.path.join(ROOT, r".tmp\tendon-engine\scratch_8217.log"), "w")
    procs.append(subprocess.Popen(
        [PY, "-B", "tools/game_shell/server.py", "8217", "--engine", ENGINE],
        cwd=ROOT, stdout=glog, stderr=glog))

    # ---- CHECK 1: DEFAULT-OFF ------------------------------------------
    st = state()
    R["c1_armed_default"] = st["tendon_armed"]
    R["c1_fields"] = all(k in st for k in (
        "tendon_armed", "tendon_q_deg", "tendon_F_n", "tendon_battery_J",
        "tendon_work_J", "tendon_heat_J", "tendon_severed",
        "tendon_elastic_J", "tendon_battery0_J", "tendon_elastic0_J"))
    v_rest = verts()
    okp = engine_post("/tick_pose", {"joint": "knee_L", "deg": 40})
    time.sleep(0.7)
    d40 = float(np.linalg.norm(verts() - v_rest, axis=1).max())
    engine_post("/tick_pose", {"joint": "knee_L", "deg": 0})
    time.sleep(0.7)
    R["c1_pose40_ok"] = bool(okp.get("ok"))
    R["c1_pose40_verts_moved"] = d40
    log(f"C1 default-off: armed={st['tendon_armed']} fields={R['c1_fields']} "
        f"pose40 ok={okp.get('ok')} maxvert_disp={d40:.3f}")

    # ---- CHECK 2: ARM ----------------------------------------------------
    ok = engine_post("/tick_effort", {"joint_index": 15, "u": 1.0})
    R["c2_arm_ok"] = bool(ok.get("ok"))
    q_max = f_max = 0.0
    batt_min = 1e9
    led_max = 0.0
    t0 = time.time()
    while time.time() - t0 < 2.5:
        st = state()
        q_max = max(q_max, st["tendon_q_deg"])
        f_max = max(f_max, st["tendon_F_n"])
        batt_min = min(batt_min, st["tendon_battery_J"])
        led_max = max(led_max, ledger_err(st))
        time.sleep(0.25)
    d_flex = np.linalg.norm(verts() - v_rest, axis=1)
    shin = v_rest[:, 1] < 3.5                      # below the knee: shin/foot
    R["c2_q_deg_max"] = q_max
    R["c2_F_n_max"] = f_max
    R["c2_battery_min"] = batt_min
    R["c2_shin_mean_disp"] = float(d_flex[shin].mean())
    R["c2_shin_max_disp"] = float(d_flex[shin].max())
    R["c2_ledger_err"] = led_max
    log(f"C2 arm: ok={R['c2_arm_ok']} q_max={q_max:.2f}deg F_max={f_max:.2f}N "
        f"battery {st['tendon_battery0_J']:.1f}->{batt_min:.1f}J "
        f"shin disp mean={R['c2_shin_mean_disp']:.3f} max={R['c2_shin_max_disp']:.3f} "
        f"ledger_err={led_max:.2e}")

    # ---- CHECK 3: SEVER mid-flex ----------------------------------------
    st_pre = state()
    v_before = verts()
    ok = engine_post("/tick_sever", {"joint_index": 15})
    st_0 = state()
    time.sleep(1.5)
    st_1 = state()
    v_after = verts()
    d_sev = np.linalg.norm(v_after - v_before, axis=1)
    R["c3_sever_ok"] = bool(ok.get("ok"))
    R["c3_q_pre"] = st_pre["tendon_q_deg"]
    R["c3_F_after"] = st_0["tendon_F_n"]
    R["c3_severed_flag"] = st_1["tendon_severed"]
    R["c3_q_after"] = st_1["tendon_q_deg"]
    R["c3_verts_delta_mean"] = float(d_sev[shin].mean())
    R["c3_verts_delta_max"] = float(d_sev.max())
    R["c3_ledger_err"] = ledger_err(st_1)
    led_max = max(led_max, R["c3_ledger_err"])
    log(f"C3 sever: ok={R['c3_sever_ok']} q {R['c3_q_pre']:.2f}->{R['c3_q_after']:.2f}deg "
        f"F_after={R['c3_F_after']:.3f} severed={R['c3_severed_flag']} "
        f"shin delta mean={R['c3_verts_delta_mean']:.3f} max={R['c3_verts_delta_max']:.3f}")

    # ---- CHECK 4: REFUSAL while armed ------------------------------------
    r1 = engine_post("/tick_pose", {"joint": "knee_L", "deg": 40})
    r2 = engine_post("/tick_pose", {"joint_index": 15, "deg": 40})
    r3 = engine_post("/tick_pose", {"joint": "ankle_L", "deg": 5})
    R["c4_knee_name_refused"] = not r1.get("ok")
    R["c4_knee_idx_refused"] = not r2.get("ok")
    R["c4_ankle_accepted"] = bool(r3.get("ok"))
    R["c4_ankle_resp"] = str(r3)[:90]
    log(f"C4 refusal: knee_name_refused={R['c4_knee_name_refused']} "
        f"knee_idx_refused={R['c4_knee_idx_refused']} "
        f"ankle_L=5 accepted={R['c4_ankle_accepted']} {R['c4_ankle_resp']}")

    # ---- CHECK 5: DISARM ---------------------------------------------------
    ok = engine_post("/tick_effort", {"joint_index": 15, "u": -1})
    st = state()
    R["c5_disarm_ok"] = bool(ok.get("ok"))
    R["c5_armed_after"] = st["tendon_armed"]
    okp = engine_post("/tick_pose", {"joint": "knee_L", "deg": 40})
    time.sleep(0.7)
    d40b = float(np.linalg.norm(verts() - v_rest, axis=1).max())
    engine_post("/tick_pose", {"joint": "knee_L", "deg": 0})
    time.sleep(0.7)
    R["c5_pose40_ok"] = bool(okp.get("ok"))
    R["c5_pose40_verts_moved"] = d40b
    log(f"C5 disarm: ok={R['c5_disarm_ok']} armed={st['tendon_armed']} "
        f"pose40 ok={okp.get('ok')} maxvert_disp={d40b:.3f}")

    # ---- CHECK 6: LEDGER ----------------------------------------------------
    R["c6_ledger_err_max"] = led_max
    R["c6_pass"] = led_max < 1e-6
    log(f"C6 ledger: max |drain-(work+heat+delastic)| = {led_max:.3e} "
        f"pass={R['c6_pass']}")

    # ---- CHECK 7: REGRESSION in the browser (game shell -> scratch) ------
    from playwright.sync_api import sync_playwright
    CAM = dict(r=26, theta=-0.55, phi=0.42, target=[0.0, 4.5, 0.0], fov=45.0)
    BELLY = (0.0, 4.5, 0.35)
    WAKE_PA, SAFE_PA = 20000, 300000
    page_errors = []

    def diag(page):
        return page.evaluate("""()=>{
            var v=document.getElementById('verdict');
            var jd=document.getElementById('judge-debug');
            return {verdict: v?v.textContent:'',
                    lessonTitle:(document.getElementById('lesson-title')||{textContent:''}).textContent,
                    passed: !!v && v.textContent.indexOf('PASSED')>=0,
                    judgePassed: !!jd && jd.textContent.indexOf('passed=true')>=0};}""")

    def wait_for(pred, secs=15.0):
        t = time.time()
        while time.time() - t < secs:
            if pred():
                return True
            time.sleep(0.3)
        return False

    def project(page, wx, wy, wz):
        rect = page.evaluate("""()=>{var c=document.getElementById('gl');
            var r=c.getBoundingClientRect();
            return {left:r.left,top:r.top,width:r.width,height:r.height,
                    aspect:r.width/r.height};}""")
        r, th, ph = CAM['r'], CAM['theta'], CAM['phi']
        ch = math.cos(ph)
        eye = [CAM['target'][0]+r*ch*math.sin(th), CAM['target'][1]+r*math.sin(ph),
               CAM['target'][2]+r*ch*math.cos(th)]
        sub = lambda a, b: [a[0]-b[0], a[1]-b[1], a[2]-b[2]]
        dot = lambda a, b: a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
        crs = lambda a, b: [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
        nrm = lambda a: [x/(math.hypot(*a) or 1) for x in a]
        tanF = math.tan(math.radians(CAM['fov'])/2)
        fwd = nrm(sub(CAM['target'], eye)); right = nrm(crs(fwd, [0, 1, 0]))
        up = crs(right, fwd)
        d = sub([wx, wy, wz], eye); depth = dot(d, fwd)
        ndcX = (dot(d, right)/depth)/(tanF*rect['aspect'])
        ndcY = (dot(d, up)/depth)/tanF
        return (rect['left']+(ndcX+1)/2*rect['width'],
                rect['top']+(1-ndcY)/2*rect['height'])

    def cell_p(page):
        try:
            s = page.evaluate("()=>fetch('/api/state').then(r=>r.json())")
            cells = s.get('cells') or []
            return abs(float(cells[1].get('P') or 0)) if len(cells) > 1 else 0.0
        except Exception:
            return None

    def set_slider(page, sel, deg):
        page.evaluate("""(a)=>{var e=document.getElementById(a[0]);
            e.value=String(a[1]); e.dispatchEvent(new Event('input',{bubbles:true}));}""",
                      [sel, deg])
        time.sleep(0.2)

    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            urllib.request.urlopen(GAME + "/", timeout=2); break
        except Exception:
            time.sleep(0.4)
    woke = kneed = False
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r09-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True, viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(GAME, wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "Tiel-R09")
        page.click("#play-btn")
        time.sleep(1.5)
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            pass
        time.sleep(0.8)
        # wake_the_cell (adaptive belly press, r08 pattern)
        bx, by = project(page, *BELLY)
        force = 15000
        for attempt in range(1, 5):
            page.evaluate("""(v)=>{var e=document.getElementById('force');
                e.value=String(v); e.dispatchEvent(new Event('input',{bubbles:true}));}""", force)
            page.mouse.move(bx, by, steps=10)
            time.sleep(0.2)
            page.mouse.down()
            pmax, t1 = 0.0, time.time()
            while time.time() - t1 < 4.0:
                time.sleep(0.35)
                pv = cell_p(page)
                if pv is None:
                    continue
                pmax = max(pmax, pv)
                if pv >= SAFE_PA or pv >= WAKE_PA * 3 or pv >= WAKE_PA:
                    break
            page.mouse.up()
            try:
                page.click("#letgo-btn", timeout=1500)
            except Exception:
                pass
            d = diag(page)
            log(f"wake attempt {attempt}: force={force} pmax={pmax:.0f} verdict={d['verdict'][:60]!r}")
            if 'ruptured' in d['verdict']:
                try:
                    page.click("#try-again-btn", timeout=2000)
                except Exception:
                    pass
                time.sleep(1.2)
                force = int(force * 0.6)
                continue
            woke = wait_for(lambda: diag(page)['passed'] or diag(page)['judgePassed'])
            if woke:
                break
            force = min(50000, force + 8000)
            time.sleep(1.0)
        R["c7_wake_passed"] = woke
        try:
            page.click("#payoff-continue", timeout=1500)
        except Exception:
            pass
        # bend_the_knee (lesson 4)
        page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'4',bubbles:true,cancelable:true}))")
        time.sleep(1.2)
        set_slider(page, 'pose-angle', 40)
        page.click("#pose-post")
        kneed = wait_for(lambda: diag(page)['passed'])
        R["c7_knee_passed"] = kneed
        set_slider(page, 'pose-angle', 0)
        page.click("#pose-post")
        time.sleep(1.5)
        # live sever screenshots in the browser: arm, flex, sever, release
        engine_post("/tick_effort", {"joint_index": 15, "u": 1.0})
        time.sleep(1.8)
        q_before = state()["tendon_q_deg"]
        page.screenshot(path=f"{EV}/09_sever_before.png")
        engine_post("/tick_sever", {"joint_index": 15})
        time.sleep(1.8)
        q_after = state()["tendon_q_deg"]
        page.screenshot(path=f"{EV}/09_sever_after.png")
        engine_post("/tick_effort", {"joint_index": 15, "u": -1})
        R["c7_sever_q_before"] = q_before
        R["c7_sever_q_after"] = q_after
        log(f"sever screenshots: q {q_before:.2f}->{q_after:.2f} deg "
            f"(09_sever_before/after.png)")
        ctx.close()
    R["page_errors"] = len(page_errors)
    for e in page_errors:
        log("PAGEERROR:", e)
    log(f"C7 regression: wake={woke} knee={kneed} pageErrors={len(page_errors)}")
except Exception as e:
    R["fatal"] = repr(e)
    log("FATAL:", repr(e))
finally:
    with open(os.path.join(EV, "09_integration_probe.txt"), "w") as f:
        f.write(json.dumps(R, indent=1) + "\n---- session log ----\n")
        f.write("\n".join(log_lines) + "\n")
    cleanup()
    log("cleanup done (own processes only)")


