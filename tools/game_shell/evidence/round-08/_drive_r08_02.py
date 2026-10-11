"""Round-08 Step 6 driver: post-fix regression in the visible game shell.

Pattern: _drive_r08.py (+ byhand_lessons.js pressWorld projection for the
wake_the_cell belly press). Drives http://127.0.0.1:8210 through
wake_the_cell (press) and bend_the_knee (knee_L=40 via the lesson's own
slider+post), captures the required screenshots and a machine record.
"""
import time, tempfile, json, math, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
ENGINE = "http://127.0.0.1:8110"
EV = r"E:\PythonChimera\tools\game_shell\evidence\round-08"
CAM = dict(r=26, theta=-0.55, phi=0.42, target=[0.0, 4.5, 0.0], fov=45.0)
BELLY = (0.0, 4.5, 0.35)   # lessons.json wake_the_cell touch_target
DEG = 40
log_lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    log_lines.append(s)


def engine_get(path):
    with urllib.request.urlopen(ENGINE + path, timeout=5) as r:
        return json.load(r)


def diag(page):
    return page.evaluate("""()=>{
        var v=document.getElementById('verdict');
        var jd=document.getElementById('judge-debug');
        return {
            verdict: v ? v.textContent : '',
            judge: jd ? jd.textContent : '',
            lessonTitle: (document.getElementById('lesson-title')||{textContent:''}).textContent,
            lessonIndex: (document.getElementById('lesson-index')||{textContent:''}).textContent,
            passed: !!v && v.textContent.indexOf('PASSED')>=0,
            judgePassed: !!jd && jd.textContent.indexOf('passed=true')>=0
        };
    }""")


def wait_for(pred, secs=10.0, interval=0.3):
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


def main():
    page_errors = []
    console_errors = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r08-02-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda e: console_errors.append(f"[{e.type}] {e.text}")
                if e.type == 'error' else None)
        log("fresh profile:", fresh_dir)

        log("=== LOAD ===")
        page.goto(URL, wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "Tiel-R08-02")
        page.click("#play-btn")
        time.sleep(1.5)
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            page.evaluate("()=>{var o=document.getElementById('intro-overlay'); if(o) o.classList.add('hidden');}")
        time.sleep(0.8)
        d = diag(page)
        log("lesson:", repr(d['lessonTitle']), "| index:", d['lessonIndex'])

        # ---------- wake_the_cell (lesson 1): press the belly ----------
        assert 'WAKE' in d['lessonTitle'].upper(), "not on wake_the_cell"
        page.evaluate("""(v)=>{var e=document.getElementById('force');
            e.value=String(v); e.dispatchEvent(new Event('input',{bubbles:true}));}""", 50000)
        fv = page.evaluate("()=>document.getElementById('force').value")
        log(f"force slider -> {fv} N")
        bx, by = project(page, *BELLY)
        log(f"belly aim px ({bx:.0f},{by:.0f})")
        page.mouse.move(bx, by, steps=14)
        time.sleep(0.2)
        page.mouse.down()
        time.sleep(2.5)
        page.mouse.up()
        time.sleep(0.3)
        try:
            page.click("#letgo-btn", timeout=2000)
            log("clicked let-go")
        except Exception:
            log("let-go button not clickable (may not be hot)")
        woke = wait_for(lambda: diag(page)['passed'] or diag(page)['judgePassed'], 30)
        d = diag(page)
        log(f"wake_the_cell PASSED: {woke} | verdict: {d['verdict'][:100]!r}")
        page.screenshot(path=f"{EV}/08_02_wake_passed.png")
        try:
            page.click("#payoff-continue", timeout=1500)
        except Exception:
            pass

        # ---------- bend_the_knee (lesson 4) ----------
        log("=== NAVIGATE to BEND THE KNEE (key '4') ===")
        page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'4',bubbles:true,cancelable:true}))")
        time.sleep(1.2)
        d = diag(page)
        log("lesson:", repr(d['lessonTitle']), "| verdict:", d['verdict'][:70])
        assert 'KNEE' in d['lessonTitle'].upper(), "not on the knee lesson"

        # rest screenshot FIRST (same view, pose 0)
        page.screenshot(path=f"{EV}/08_02_knee_0.png")
        log(f"screenshot: {EV}\\08_02_knee_0.png (rest)")

        log(f"=== SET knee_L slider to {DEG} deg + POST ===")
        page.evaluate("""(a)=>{var e=document.getElementById('pose-angle');
            e.value=String(a[0]); e.dispatchEvent(new Event('input',{bubbles:true}));}""", [DEG])
        time.sleep(0.2)
        page.click("#pose-post")
        latched = wait_for(lambda: diag(page)['passed'], 10)
        time.sleep(1.2)
        d = diag(page)
        log(f"bend_the_knee PASSED (pass_line visible): {latched} | verdict: {d['verdict'][:110]!r}")
        st = engine_get("/tick_state")
        log("engine ticks:", st['ticks'], "| body_model:", st['body_model'])
        page.screenshot(path=f"{EV}/08_02_knee_bent_foot_follows.png")
        log(f"screenshot: {EV}\\08_02_knee_bent_foot_follows.png (knee_L={DEG})")

        # reset pose to rest and leave the world at rest
        page.evaluate("""()=>{var e=document.getElementById('pose-angle');
            e.value='0'; e.dispatchEvent(new Event('input',{bubbles:true}));}""")
        time.sleep(0.2)
        page.click("#pose-post")
        time.sleep(1.0)
        ctx.close()

    log(f"PAGE ERRORS: {len(page_errors)}")
    for e in page_errors:
        log("  PAGEERROR:", e)
    with open(f"{EV}/08_02_drive.txt", "w") as f:
        f.write(f"tag=08_02 deg={DEG}\nfresh_profile={fresh_dir}\n")
        f.write(f"wake_the_cell_passed={woke}\n")
        f.write(f"bend_the_knee_passed={latched}\n")
        f.write(f"page_errors={len(page_errors)}\n")
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write("---- session log ----\n")
        f.write("\n".join(log_lines) + "\n")
    log(f"wrote {EV}\\08_02_drive.txt")


main()
