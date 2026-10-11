"""Round-08 Step 6 driver v2: adaptive wake_the_cell press (v1 at 50000 N
ruptured: RUPTURE_PA=500k fires while holding), then bend_the_knee.
Polls the page's own /api/state cell pressure during the hold and releases
between the wake bar (20k Pa) and the burst bar, like a player watching the
gauge. Overwrites the 08_02_* artifacts with the clean pass.
"""
import time, tempfile, json, math, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
ENGINE = "http://127.0.0.1:8110"
EV = r"E:\PythonChimera\tools\game_shell\evidence\round-08"
CAM = dict(r=26, theta=-0.55, phi=0.42, target=[0.0, 4.5, 0.0], fov=45.0)
BELLY = (0.0, 4.5, 0.35)
DEG = 40
WAKE_PA, SAFE_PA = 20000, 300000
log_lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
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
            passed: !!v && v.textContent.indexOf('PASSED')>=0,
            judgePassed: !!jd && jd.textContent.indexOf('passed=true')>=0,
            ruptured: !!v && v.textContent.indexOf('ruptured')>=0
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


def cell_p(page):
    """Belly cell (index 1) signed pressure via the page's own state channel."""
    try:
        s = page.evaluate("()=>fetch('/api/state').then(r=>r.json())")
        cells = s.get('cells') or []
        return abs(float(cells[1].get('P') or 0)) if len(cells) > 1 else 0.0
    except Exception:
        return None


def main():
    page_errors = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-r08-02b-")
    woke = latched = False
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
        page.fill("#name-input", "Tiel-R08-02b")
        page.click("#play-btn")
        time.sleep(1.5)
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            page.evaluate("()=>{var o=document.getElementById('intro-overlay'); if(o) o.classList.add('hidden');}")
        time.sleep(0.8)
        d = diag(page)
        log("lesson:", repr(d['lessonTitle']))
        assert 'WAKE' in d['lessonTitle'].upper()

        bx, by = project(page, *BELLY)
        log(f"belly aim px ({bx:.0f},{by:.0f})")

        # ---- adaptive wake press: watch the gauge, release before burst ----
        force = 15000
        for attempt in range(1, 5):
            page.evaluate("""(v)=>{var e=document.getElementById('force');
                e.value=String(v); e.dispatchEvent(new Event('input',{bubbles:true}));}""", force)
            page.mouse.move(bx, by, steps=10)
            time.sleep(0.2)
            page.mouse.down()
            pmax, t0, released = 0.0, time.time(), False
            while time.time() - t0 < 4.0:
                time.sleep(0.35)
                pv = cell_p(page)
                if pv is None:
                    continue
                pmax = max(pmax, pv)
                if pv >= SAFE_PA or pv >= WAKE_PA * 3:
                    break
                if pv >= WAKE_PA:
                    break
            page.mouse.up()
            released = True
            try:
                page.click("#letgo-btn", timeout=1500)
            except Exception:
                pass
            d = diag(page)
            log(f"attempt {attempt}: force={force} N pmax={pmax:.0f} Pa "
                f"verdict={d['verdict'][:60]!r}")
            if d['ruptured']:
                log("  ruptured -> try again, lower force")
                try:
                    page.click("#try-again-btn", timeout=2000)
                except Exception:
                    pass
                time.sleep(1.2)
                force = int(force * 0.6)
                continue
            woke = wait_for(lambda: diag(page)['passed'] or diag(page)['judgePassed'], 15)
            if woke:
                break
            if pmax < WAKE_PA:
                force = min(50000, force + 8000)
            time.sleep(1.0)
        d = diag(page)
        log(f"wake_the_cell PASSED: {woke} | verdict: {d['verdict'][:110]!r}")
        page.screenshot(path=f"{EV}/08_02_wake_passed.png")
        try:
            page.click("#payoff-continue", timeout=1500)
        except Exception:
            pass

        # ---- bend_the_knee ----
        page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'4',bubbles:true,cancelable:true}))")
        time.sleep(1.2)
        d = diag(page)
        assert 'KNEE' in d['lessonTitle'].upper(), "not on the knee lesson"
        page.screenshot(path=f"{EV}/08_02_knee_0.png")
        log("screenshot: 08_02_knee_0.png (rest)")
        page.evaluate("""(a)=>{var e=document.getElementById('pose-angle');
            e.value=String(a[0]); e.dispatchEvent(new Event('input',{bubbles:true}));}""", [DEG])
        time.sleep(0.2)
        page.click("#pose-post")
        latched = wait_for(lambda: diag(page)['passed'], 10)
        time.sleep(1.2)
        d = diag(page)
        log(f"bend_the_knee PASSED: {latched} | verdict: {d['verdict'][:110]!r}")
        st = engine_get("/tick_state")
        log("engine ticks:", st['ticks'], "| body_model:", st['body_model'])
        page.screenshot(path=f"{EV}/08_02_knee_bent_foot_follows.png")
        log("screenshot: 08_02_knee_bent_foot_follows.png (knee_L=40)")
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
        f.write(f"wake_the_cell_passed={woke}\nbend_the_knee_passed={latched}\n")
        f.write(f"page_errors={len(page_errors)}\n")
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write("---- session log ----\n")
        f.write("\n".join(log_lines) + "\n")
    log(f"wrote {EV}\\08_02_drive.txt")


main()
