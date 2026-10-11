"""Round-08 08_03: the raise_the_hand lesson drive.

Fresh-profile headless Chromium (pattern: _drive_r08_02b.py):
  1. wake_the_cell regression  — adaptive 15000 N belly press, watch the gauge.
  2. bend_the_knee regression  — slider+post knee_L=40, then post 0 (rest).
  3. raise_the_hand (NEW, lesson 5/11) — assert it appears right after the
     knee lesson; screenshot at rest; drive the lesson's OWN wrist_L slider
     to 40 and press post; on PASS probe the engine's live /verts and prove
     the hand_L band really moved (mean displacement > 0.5 m).
Screenshots: 08_03_hand_rest.png / 08_03_hand_raised_passed.png.
Machine record: 08_03_drive.txt. Leaves the body at rest (wrist post 0).
"""
import time, tempfile, json, math, struct, urllib.request
import numpy as np
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
ENGINE = "http://127.0.0.1:8110"
ROOT = r"E:\PythonChimera"
EV = ROOT + r"\tools\game_shell\evidence\round-08"
CAM = dict(r=26, theta=-0.55, phi=0.42, target=[0.0, 4.5, 0.0], fov=45.0)
BELLY = (0.0, 4.5, 0.35)
DEG = 40
WAKE_PA, SAFE_PA = 20000, 300000
PASS_LINE = "you wished with your wrist"
log_lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log_lines.append(s)


def engine_get(path):
    with urllib.request.urlopen(ENGINE + path, timeout=10) as r:
        return r.read()


def verts():
    raw = engine_get("/verts")
    n = struct.unpack_from('<I', raw)[0]
    return np.frombuffer(raw, '<f4', 9 * n, 4).reshape(n, 9)[:, :3].astype(np.float64)


def hand_band():
    mesh = open(ROOT + r"\Saved\meshes\monkey_birth.bin", 'rb').read()
    nv_m, nf_m = struct.unpack_from('<II', mesh)
    xyz = np.frombuffer(mesh, '<f4', 3 * nv_m, 8).reshape(nv_m, 3).astype(np.float64)
    return np.where((xyz[:, 0] > 1.8) & (xyz[:, 1] < 4.15)
                    & (np.hypot(xyz[:, 0] - 2.23, xyz[:, 1] - 4.02) < 2.2))[0]


def diag(page):
    return page.evaluate("""()=>{
        var v=document.getElementById('verdict');
        var jd=document.getElementById('judge-debug');
        return {
            verdict: v ? v.textContent : '',
            lessonTitle: (document.getElementById('lesson-title')||{textContent:''}).textContent,
            lessonIndex: (document.getElementById('lesson-index')||{textContent:''}).textContent,
            passed: !!v && v.textContent.indexOf('PASSED')>=0,
            judgePassed: !!jd && jd.textContent.indexOf('passed=true')>=0
        };
    }""")


def wait_for(pred, secs=15.0, interval=0.3):
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
    sub = lambda a, b: [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
    dot = lambda a, b: a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
    crs = lambda a, b: [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
                        a[0] * b[1] - a[1] * b[0]]
    nrm = lambda a: [x / (math.hypot(*a) or 1) for x in a]
    tanF = math.tan(math.radians(CAM['fov']) / 2)
    fwd = nrm(sub(tgt, eye))
    right = nrm(crs(fwd, [0, 1, 0]))
    up = crs(right, fwd)
    d = sub([wx, wy, wz], eye)
    depth = dot(d, fwd)
    ndcX = (dot(d, right) / depth) / (tanF * rect['aspect'])
    ndcY = (dot(d, up) / depth) / tanF
    bx = rect['left'] + (ndcX + 1) / 2 * rect['width']
    by = rect['top'] + (1 - ndcY) / 2 * rect['height']
    return bx, by


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


def main():
    page_errors = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r08-03-")
    woke = kneed = handed = False
    hand_mean = hand_max = None
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        log("fresh profile:", fresh_dir)

        page.goto(URL, wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "Tiel-R08-03")
        page.click("#play-btn")
        time.sleep(1.5)
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            page.evaluate("()=>{var o=document.getElementById('intro-overlay'); if(o) o.classList.add('hidden');}")
        time.sleep(0.8)
        d = diag(page)
        log("lesson:", repr(d['lessonTitle']), "|", d['lessonIndex'])
        assert 'WAKE' in d['lessonTitle'].upper()

        # ---- regression 1: wake_the_cell (adaptive 15 kN press, 02b pattern) ----
        bx, by = project(page, *BELLY)
        force = 15000
        for attempt in range(1, 5):
            page.evaluate("""(v)=>{var e=document.getElementById('force');
                e.value=String(v); e.dispatchEvent(new Event('input',{bubbles:true}));}""", force)
            page.mouse.move(bx, by, steps=10)
            time.sleep(0.2)
            page.mouse.down()
            pmax, t0 = 0.0, time.time()
            while time.time() - t0 < 4.0:
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
            log(f"wake attempt {attempt}: force={force} N pmax={pmax:.0f} Pa "
                f"verdict={d['verdict'][:60]!r}")
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
            if pmax < WAKE_PA:
                force = min(50000, force + 8000)
            time.sleep(1.0)
        d = diag(page)
        log(f"REGRESSION wake_the_cell PASSED: {woke} | verdict: {d['verdict'][:110]!r}")
        try:
            page.click("#payoff-continue", timeout=1500)
        except Exception:
            pass

        # ---- regression 2: bend_the_knee (lesson 4) ----
        page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'4',bubbles:true,cancelable:true}))")
        time.sleep(1.2)
        d = diag(page)
        assert 'KNEE' in d['lessonTitle'].upper(), "not on the knee lesson"
        set_slider(page, 'pose-angle', DEG)
        page.click("#pose-post")
        kneed = wait_for(lambda: diag(page)['passed'])
        d = diag(page)
        log(f"REGRESSION bend_the_knee PASSED: {kneed} | verdict: {d['verdict'][:110]!r}")
        set_slider(page, 'pose-angle', 0)      # back to rest before the hand lesson
        page.click("#pose-post")
        time.sleep(1.5)

        # ---- NEW lesson: raise_the_hand (lesson 5) ----
        dots = page.evaluate("()=>document.querySelectorAll('#progress-strip .dot').length")
        log(f"progression dots: {dots}")
        page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'5',bubbles:true,cancelable:true}))")
        time.sleep(1.2)
        d = diag(page)
        log("lesson 5:", repr(d['lessonTitle']), "|", d['lessonIndex'])
        assert 'HAND' in d['lessonTitle'].upper(), "raise_the_hand did not appear at 5/11"
        joint_lbl = page.evaluate(
            "()=>(document.querySelector('.pose-joint')||{textContent:''}).textContent")
        log("pose row joint label:", repr(joint_lbl))
        assert joint_lbl == 'wrist_L', "pose control not bound to wrist_L"

        page.screenshot(path=f"{EV}/08_03_hand_rest.png")
        log("screenshot: 08_03_hand_rest.png (hand lesson, at rest)")
        v_rest = verts()

        set_slider(page, 'pose-angle', DEG)
        page.click("#pose-post")
        handed = wait_for(lambda: PASS_LINE in diag(page)['verdict'])
        time.sleep(1.5)                      # let the engine settle on the held pose
        d = diag(page)
        log(f"raise_the_hand PASSED: {handed} | verdict: {d['verdict'][:110]!r}")

        # live /verts DURING the pass: the hand must have really moved
        hb = hand_band()
        disp = np.linalg.norm(verts() - v_rest, axis=1)
        hand_mean, hand_max = float(disp[hb].mean()), float(disp[hb].max())
        log(f"live /verts during pass: hand_L n={len(hb)} "
            f"mean={hand_mean:.4f} max={hand_max:.4f} (bar: mean > 0.5)")
        st = engine_get("/tick_state")
        log("engine ticks:", json.loads(st)['ticks'], "| body_model:", json.loads(st)['body_model'])
        page.screenshot(path=f"{EV}/08_03_hand_raised_passed.png")
        log("screenshot: 08_03_hand_raised_passed.png (wrist_L=40, passed)")

        # leave the body at rest: post wrist 0 and verify verts return home
        set_slider(page, 'pose-angle', 0)
        page.click("#pose-post")
        time.sleep(1.5)
        back = float(np.abs(verts() - v_rest).max())
        log(f"rest check: max|verts - rest| after wrist 0 = {back:.2e}")
        ctx.close()

    log(f"PAGE ERRORS: {len(page_errors)}")
    for e in page_errors:
        log("  PAGEERROR:", e)
    with open(f"{EV}/08_03_drive.txt", "w") as f:
        f.write(f"tag=08_03 deg={DEG}\nfresh_profile={fresh_dir}\n")
        f.write(f"wake_the_cell_passed={woke}\nbend_the_knee_passed={kneed}\n")
        f.write(f"raise_the_hand_passed={handed}\n")
        f.write(f"hand_L_mean_disp={hand_mean:.4f} hand_L_max_disp={hand_max:.4f}\n")
        f.write(f"page_errors={len(page_errors)}\n")
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write("---- session log ----\n")
        f.write("\n".join(log_lines) + "\n")
    log(f"wrote {EV}\\08_03_drive.txt")
    ok = woke and kneed and handed and hand_mean is not None and hand_mean > 0.5 \
        and not page_errors
    log("OVERALL:", "PASS" if ok else "FAIL")


main()
