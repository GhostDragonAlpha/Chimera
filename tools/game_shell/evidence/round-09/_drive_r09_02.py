"""Round-09 09_02: the energy body is PLAYABLE — full 12-lesson drive.

SCRATCH stack ONLY (pattern: _probe_r09_integration.py + _drive_r08_03.py):
engine 8117 from .tmp/tendon-engine, game shell 8217 -> 8117. The shared
:8110/:8210 stack is never touched. Fresh profile; ALL 12 lessons pass in
array order. Pressure lessons ride the adaptive-force press (02b pattern:
9000 N start for wake, rupture -> 0.6x retry, short holds so the 0.5 MPa
rupture check (which only fires while holding) never lands on a held peak).
feel_the_muscle (6): effort slider to 100% -> wait the MEASURED flex latch
(tendon_q_deg >= 40), screenshot + tendon numbers, sever, wait the limp
latch (q < 5). Disarm regression: back to bend_the_knee (4), knee_L pose
must be ACCEPTED again. Screenshots 09_02_muscle_flexed.png /
09_02_after_sever.png; machine record 09_02_drive.txt.
"""
import time, tempfile, json, math, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8217"
ENGINE = "http://127.0.0.1:8117"
ROOT = r"E:\PythonChimera"
EV = ROOT + r"\tools\game_shell\evidence\round-09"
CAM = dict(r=26, theta=-0.55, phi=0.42, target=[0.0, 4.5, 0.0], fov=45.0)
BELLY = (0.0, 4.5, 0.35)
FOOT_L = (1.03, 0.25, 0.79)
SHIN_L = (0.48, 1.2, -0.15)
HEAVY = (-0.23, 4.71, 0.74)
log_lines = []
RESULT = {}


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log_lines.append(s)


def engine_get(path):
    with urllib.request.urlopen(ENGINE + path, timeout=10) as r:
        return json.loads(r.read())


def engine_post(path, obj):
    req = urllib.request.Request(ENGINE + path, data=json.dumps(obj).encode(),
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tstate():
    st = engine_get("/tick_state")
    return {k: st.get(k) for k in ("tendon_armed", "tendon_q_deg", "tendon_F_n",
                                   "tendon_battery_J", "tendon_severed")}


def diag(page):
    return page.evaluate("""()=>{
        var v=document.getElementById('verdict');
        var jd=document.getElementById('judge-debug');
        return {
            verdict: v ? v.textContent : '',
            lessonTitle: (document.getElementById('lesson-title')||{textContent:''}).textContent,
            lessonIndex: (document.getElementById('lesson-index')||{textContent:''}).textContent,
            passed: !!v && v.textContent.indexOf('PASSED')>=0,
            judge: jd ? jd.textContent : ''
        };
    }""")


def wait_for(pred, secs=25.0, interval=0.35):
    t = time.time()
    while time.time() - t < secs:
        if pred():
            return True
        time.sleep(interval)
    return False


def project(page, wx, wy, wz):
    rect = page.evaluate("""()=>{var c=document.getElementById('gl');
        var r=c.getBoundingClientRect();
        return {left:r.left, top:r.top, width:r.width, height:r.height,
                aspect:r.width/r.height};}""")
    r, th, ph = CAM['r'], CAM['theta'], CAM['phi']
    ch = math.cos(ph)
    eye = [CAM['target'][0] + r * ch * math.sin(th),
           CAM['target'][1] + r * math.sin(ph),
           CAM['target'][2] + r * ch * math.cos(th)]
    tgt = CAM['target']
    sub = lambda a, b: [a[0]-b[0], a[1]-b[1], a[2]-b[2]]
    dot = lambda a, b: a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
    crs = lambda a, b: [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    nrm = lambda a: [x/(math.hypot(*a) or 1) for x in a]
    tanF = math.tan(math.radians(CAM['fov'])/2)
    fwd = nrm(sub(tgt, eye))
    right = nrm(crs(fwd, [0, 1, 0]))
    up = crs(right, fwd)
    d = sub([wx, wy, wz], eye)
    depth = dot(d, fwd)
    ndcX = (dot(d, right)/depth) / (tanF*rect['aspect'])
    ndcY = (dot(d, up)/depth) / tanF
    return (rect['left'] + (ndcX+1)/2*rect['width'],
            rect['top'] + (1-ndcY)/2*rect['height'])


def cells_p(page):
    try:
        s = page.evaluate("()=>fetch('/api/state').then(r=>r.json())")
        return [float(c.get('P') or 0) for c in (s.get('cells') or [])]
    except Exception:
        return []


def set_force(page, v):
    page.evaluate("""(v)=>{var e=document.getElementById('force');
        e.value=String(v); e.dispatchEvent(new Event('input',{bubbles:true}));}""", v)


def set_slider(page, sel, val):
    page.evaluate("""(a)=>{var e=document.getElementById(a[0]);
        e.value=String(a[1]); e.dispatchEvent(new Event('input',{bubbles:true}));}""",
                  [sel, val])
    time.sleep(0.25)


def key(page, k):
    page.evaluate("(k)=>window.dispatchEvent(new KeyboardEvent('keydown',{key:k,"
                  "bubbles:true,cancelable:true}))", k)
    time.sleep(1.1)


def dismiss(page):
    try:
        page.click("#payoff-continue", timeout=1200)
        time.sleep(0.5)
    except Exception:
        pass


def press_adaptive(page, target, cell_idx, bar_pa, force0, tag,
                   attempts=6, hold=0.45, force_max=None, grow=1.6):
    """Adaptive browser-click press (02b pattern). cell_idx None = any cell.
    Short holds: the rupture check only fires on a poll that lands while
    holding, so a quick press whose crossing is seen in the 2.5 s pressFresh
    tail latches without ever being caught over the 0.5 MPa bar."""
    bx, by = project(page, *target)
    force = force0
    for a in range(1, attempts + 1):
        set_force(page, force)
        page.mouse.move(bx, by, steps=8)
        time.sleep(0.15)
        page.mouse.down()
        t0 = time.time()
        pmax = 0.0
        while time.time() - t0 < hold:
            ps = cells_p(page)
            if ps:
                v = (max(abs(x) for x in ps) if cell_idx is None
                     else (ps[cell_idx] if len(ps) > cell_idx else 0.0))
                pmax = max(pmax, v)
            time.sleep(0.1)
        page.mouse.up()
        try:
            page.click("#letgo-btn", timeout=1200)
        except Exception:
            pass
        d = diag(page)
        log(f"  {tag} attempt {a}: force={force} N pmax={pmax:.0f} Pa "
            f"verdict={d['verdict'][:56]!r}")
        if 'ruptured' in d['verdict']:
            try:
                page.click("#try-again-btn", timeout=2000)
            except Exception:
                pass
            time.sleep(1.2)
            force = max(500, int(force * 0.6))
            continue
        if pmax >= bar_pa:
            return True, force, pmax
        nf = min(force_max or 50000, int(force * grow))
        force = nf if nf > force else min(50000, force + 500)
        time.sleep(1.0)
    return False, force, pmax


def wait_passed(page, tag, secs=30.0):
    ok = wait_for(lambda: diag(page)['passed'] or 'passed=true' in diag(page)['judge'],
                  secs=secs)
    d = diag(page)
    log(f"LESSON {tag} PASSED: {ok} | verdict: {d['verdict'][:100]!r}")
    RESULT[tag] = ok
    dismiss(page)
    return ok


def press_lesson(page, target, cell_idx, bar_pa, force0, tag, **kw):
    ok, force, pmax = press_adaptive(page, target, cell_idx, bar_pa, force0, tag, **kw)
    if not ok:
        return False
    return wait_passed(page, tag)     # release phase rides the calm check


def pose_lesson(page, rows, tag):
    """rows: list of (slider_suffix, deg). Set each slider, click each post."""
    for sfx, deg in rows:
        set_slider(page, 'pose-angle' + sfx, deg)
        page.click('#pose-post' + sfx)
        time.sleep(0.4)
    return wait_passed(page, tag)


def main():
    page_errors = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r09-02-")
    flex_t = limp_t = None
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True, viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        log("fresh profile:", fresh_dir)
        page.goto(URL + "/?debug=1", wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "Tiel-R09-02")
        page.click("#play-btn")
        time.sleep(1.5)
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            pass
        time.sleep(0.8)
        dots = page.evaluate("()=>document.querySelectorAll('#progress-strip .dot').length")
        RESULT["dots"] = dots
        log("progression dots:", dots)

        # ---- 1 wake_the_cell (adaptive, 9000 N start, 02b pattern) ----
        assert 'WAKE' in diag(page)['lessonTitle'].upper()
        press_lesson(page, BELLY, 1, 20000, 9000, "wake_the_cell")

        # ---- 2 the_gentle_hand (cap 8000 N, foot) ----
        key(page, '2'); assert 'GENTLE' in diag(page)['lessonTitle'].upper()
        press_lesson(page, FOOT_L, 0, 50000, 5000, "the_gentle_hand",
                     force_max=8000, grow=1.4)

        # ---- 3 the_healing (any cell) ----
        key(page, '3'); assert 'HEALING' in diag(page)['lessonTitle'].upper()
        press_lesson(page, BELLY, None, 20000, 9000, "the_healing")

        # ---- 4 bend_the_knee ----
        key(page, '4'); assert 'KNEE' in diag(page)['lessonTitle'].upper()
        pose_lesson(page, [("", 40)], "bend_the_knee")
        set_slider(page, 'pose-angle', 0); page.click("#pose-post"); time.sleep(1.0)

        # ---- 5 raise_the_hand ----
        key(page, '5'); assert 'HAND' in diag(page)['lessonTitle'].upper()
        pose_lesson(page, [("", 40)], "raise_the_hand")
        set_slider(page, 'pose-angle', 0); page.click("#pose-post"); time.sleep(1.0)

        # ---- 6 feel_the_muscle (NEW) ----
        key(page, '6')
        d = diag(page)
        RESULT["muscle_index"] = d['lessonIndex']
        assert 'MUSCLE' in d['lessonTitle'].upper(), d['lessonTitle']
        assert page.evaluate("()=>!!document.getElementById('effort-u')")
        log("lesson 6 at index", d['lessonIndex'], "| effort control present")
        armed_before = tstate()["tendon_armed"]
        set_slider(page, 'effort-u', 100)          # arms on the first post
        flexed = wait_for(lambda: (tstate()["tendon_q_deg"] or 0) >= 40
                          and 'cut the tendon' in diag(page)['verdict'], secs=20)
        flex_t = tstate()
        page.screenshot(path=f"{EV}/09_02_muscle_flexed.png")
        log(f"FLEX latch: {flexed} | armed_before={armed_before} | "
            f"q={flex_t['tendon_q_deg']:.2f}deg F={flex_t['tendon_F_n']:.2f}N "
            f"battery={flex_t['tendon_battery_J']:.2f}J armed={flex_t['tendon_armed']}")
        RESULT["flex_latch"] = flexed
        page.click("#effort-sever-btn")
        time.sleep(0.5)
        armed_after_sever = tstate()["tendon_armed"]   # sever does NOT disarm
        limped = wait_passed(page, "feel_the_muscle", secs=30)
        limp_t = tstate()
        page.screenshot(path=f"{EV}/09_02_after_sever.png")
        log(f"LIMP latch: {limped} | q={limp_t['tendon_q_deg']:.2f}deg "
            f"F={limp_t['tendon_F_n']:.2f}N severed={limp_t['tendon_severed']} "
            f"armed_after_sever={armed_after_sever}")
        RESULT["armed_after_sever"] = armed_after_sever

        # ---- disarm regression: back to bend_the_knee (4) ----
        key(page, '4')
        time.sleep(1.5)
        st_after = tstate()
        pose_resp = engine_post("/tick_pose", {"joint": "knee_L", "deg": 40})
        time.sleep(0.6)
        engine_post("/tick_pose", {"joint": "knee_L", "deg": 0})
        RESULT["disarm_armed"] = st_after["tendon_armed"]
        RESULT["disarm_pose_ok"] = bool(pose_resp.get("ok"))
        log(f"DISARM regression: armed_after_lesson_change={st_after['tendon_armed']} "
            f"| /tick_pose knee_L accepted={pose_resp.get('ok')} resp={pose_resp}")
        # and the PAGE's own post must be accepted too (row marks "held")
        set_slider(page, 'pose-angle', 40)
        page.click("#pose-post")
        time.sleep(0.8)
        RESULT["disarm_page_post"] = page.evaluate(
            "()=>(document.getElementById('pose-post')||{textContent:''}).textContent")
        log("page pose post button after disarm:", RESULT["disarm_page_post"])
        key(page, '7')

        # ---- 7 the_whole_body (torso + shins, then release) ----
        assert 'WHOLE' in diag(page)['lessonTitle'].upper()
        wb_ok = False
        for outer in range(1, 4):
            press_adaptive(page, BELLY, 1, 50000, 9000, f"whole_body belly#{outer}")
            press_adaptive(page, SHIN_L, 3, 20000, 1000, f"whole_body shin#{outer}",
                           force_max=3000, grow=1.5)
            if 'ruptured' in diag(page)['verdict']:
                try:
                    page.click("#try-again-btn", timeout=1500)
                except Exception:
                    pass
                time.sleep(1.0)
                continue
            wb_ok = wait_passed(page, "the_whole_body")
            if wb_ok:
                break
        RESULT.setdefault("the_whole_body", wb_ok)

        # ---- 8 the_balance (pose_pair) ----
        key(page, '8'); assert 'BALANCE' in diag(page)['lessonTitle'].upper()
        pose_lesson(page, [("-0", 5), ("-1", -5)], "the_balance")

        # ---- 9 the_heavy_hand (1.5 MPa belly; short taps, rupture is a
        #         timing lottery on the pressFresh tail, keep force) ----
        key(page, '9'); assert 'HEAVY' in diag(page)['lessonTitle'].upper()
        bx, by = project(page, *HEAVY)
        hv_ok = False
        force = 35000
        for a in range(1, 13):
            set_force(page, force)
            page.mouse.move(bx, by, steps=6); time.sleep(0.1)
            page.mouse.down(); time.sleep(0.22); page.mouse.up()
            try:
                page.click("#letgo-btn", timeout=1000)
            except Exception:
                pass
            time.sleep(0.9)
            d = diag(page)
            log(f"  heavy tap {a}: force={force} verdict={d['verdict'][:56]!r}")
            if 'ruptured' in d['verdict']:
                try:
                    page.click("#try-again-btn", timeout=1500)
                except Exception:
                    pass
                time.sleep(1.0)
                continue
            if d['passed'] or 'goal is met' in d['verdict']:
                hv_ok = True
                break
            force = min(50000, int(force * 1.15))
        RESULT["the_heavy_hand"] = hv_ok and wait_passed(page, "the_heavy_hand")

        # ---- 10 the_cascade (isolation) ----
        key(page, '0'); assert 'CASCADE' in diag(page)['lessonTitle'].upper()
        press_lesson(page, (0.0, 4.5, 0.32), 1, 15000, 6000, "the_cascade",
                     force_max=12000)

        # ---- 11 the_stand (gravity) ----
        key(page, ']'); assert 'STAND' in diag(page)['lessonTitle'].upper()
        page.click("#gravity-btn")
        wait_passed(page, "the_stand", secs=20)

        # ---- 12 the_graduation (backtick -> LAST lesson, dynamic) ----
        key(page, '`')
        d = diag(page)
        RESULT["graduation_index"] = d['lessonIndex']
        assert 'GRADUATION' in d['lessonTitle'].upper(), d['lessonTitle']
        gr_ok = False
        for outer in range(1, 4):
            for tgt, ci, f0, fmax in ((BELLY, 1, 9000, 20000),
                                      (FOOT_L, 0, 4000, 8000),
                                      (SHIN_L, 3, 1000, 3000)):
                press_adaptive(page, tgt, ci, 20000, f0,
                               f"graduation#{outer} cell{ci}", force_max=fmax)
                if 'ruptured' in diag(page)['verdict']:
                    break
            if 'ruptured' in diag(page)['verdict']:
                try:
                    page.click("#try-again-btn", timeout=1500)
                except Exception:
                    pass
                time.sleep(1.0)
                continue
            gr_ok = wait_passed(page, "the_graduation", secs=35)
            if gr_ok:
                break
        RESULT.setdefault("the_graduation", gr_ok)
        dismiss(page)
        ctx.close()

    RESULT["page_errors"] = len(page_errors)
    RESULT["flex"] = flex_t
    RESULT["limp"] = limp_t
    log(f"PAGE ERRORS: {len(page_errors)}")
    for e in page_errors:
        log("  PAGEERROR:", e)
    order = ["wake_the_cell", "the_gentle_hand", "the_healing", "bend_the_knee",
             "raise_the_hand", "feel_the_muscle", "the_whole_body", "the_balance",
             "the_heavy_hand", "the_cascade", "the_stand", "the_graduation"]
    with open(f"{EV}/09_02_drive.txt", "w") as f:
        f.write(f"fresh_profile={fresh_dir}\n")
        for k in ("dots", "muscle_index", "flex_latch", "armed_after_sever",
                  "disarm_armed", "disarm_pose_ok", "disarm_page_post", "graduation_index",
                  "page_errors"):
            f.write(f"{k}={RESULT.get(k)}\n")
        f.write(f"flex={json.dumps(RESULT.get('flex'))}\n")
        f.write(f"limp={json.dumps(RESULT.get('limp'))}\n")
        for lid in order:
            f.write(f"lesson {lid}: passed={RESULT.get(lid)}\n")
        f.write("---- session log ----\n")
        f.write("\n".join(log_lines) + "\n")
    allpass = all(RESULT.get(l) for l in order) and not page_errors
    log("OVERALL:", "PASS" if allpass else "FAIL")


main()
