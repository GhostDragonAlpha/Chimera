import re, time, os, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
EV = r"E:\PythonChimera\tools\game_shell\evidence"


def diag(page):
    return page.evaluate("""()=>{
        var g=document.getElementById('gl-error');
        var ta=document.getElementById('try-again-btn');
        var io=document.getElementById('intro-overlay');
        return {
            verdict: document.getElementById('verdict').textContent,
            hand: document.getElementById('hand-state').textContent,
            blood: document.getElementById('blood').textContent.replace(/\s+/g,' '),
            forceVal: document.getElementById('force').value,
            introOpen: !!io && !io.classList.contains('hidden'),
            playScreenOn: document.getElementById('screen-play').classList.contains('on'),
            lessonTitle: document.getElementById('lesson-title').textContent,
            enteredName: document.getElementById('cam-name').textContent
        };
    }""")


def torso_p_mpa(page):
    bd = page.evaluate("()=>document.getElementById('blood').textContent")
    m = re.search(r'torso \(cell 1\):.*?P=([0-9.]+)\s*MPa', bd)
    return float(m.group(1)) if m else None


def set_force(page, v):
    page.evaluate("(a)=>{var e=document.getElementById('force');e.value=String(a[0]);e.dispatchEvent(new Event('input',{bubbles:true}));}", [v])


def center(page):
    return page.evaluate("()=>{var r=document.getElementById('gl').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2};}")


def down(page, x, y):
    page.evaluate("(a)=>{var c=document.getElementById('gl');var o={type:'pointerdown',clientX:a[0],clientY:a[1],button:0,buttons:1,pointerId:1,pointerType:'mouse',isPrimary:true,pressure:0.6,bubbles:true};c.dispatchEvent(new PointerEvent(o.type,o));}", [x, y])


def up(page, x, y):
    page.evaluate("(a)=>{var c=document.getElementById('gl');var w=window;var o1={type:'pointerup',clientX:a[0],clientY:a[1],button:0,buttons:0,pointerId:1,pointerType:'mouse',isPrimary:true,pressure:0,bubbles:true};c.dispatchEvent(new PointerEvent(o1.type,o1));w.dispatchEvent(new PointerEvent(o1.type,o1));}", [x, y])


def wait_for(pred, secs=8.0, interval=0.15):
    t = time.time()
    while time.time() - t < secs:
        if pred(): return True
        time.sleep(interval)
    return False


def main():
    page_errors = []
    console_msgs = []

    fresh_dir = tempfile.mkdtemp(prefix="chimera-clean-intro-")

    # ensure a never-seen camera for the required name so the intro greeting
    # actually appears (progress files are shared across profiles by name).
    prog = os.path.join(os.path.dirname(__file__), "..", "progress", "Tiel-Clean.json")
    prog = os.path.abspath(prog)
    if os.path.exists(prog):
        os.remove(prog)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]

        def on_pe(e): page_errors.append(str(e))
        def on_con(e): console_msgs.append(f"[{e.type}] {e.text}")

        page.on("pageerror", on_pe)
        page.on("console", on_con)

        print("fresh profile:", fresh_dir)

        # ---------- STEP 2: fresh name -> real PLAY -> WAIT intro -> click begin ----------
        print("\n=== [S2] LOAD (fresh profile, seen_intro unset) ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        d = diag(page)
        print("playScreenOn:", d['playScreenOn'], "| introOpen:", d['introOpen'])

        print("\n=== [S2] TYPE NAME 'Tiel-Clean' + CLICK REAL #play-btn ===")
        page.fill("#name-input", "Tiel-Clean")
        page.click("#play-btn")   # the actual button element
        time.sleep(0.4)

        print("=== [S2] WAIT for intro overlay to appear ===")
        intro_appeared = wait_for(lambda: diag(page)['introOpen'], 6)
        d = diag(page)
        print("introAppeared:", intro_appeared, "| lessonTitle:", repr(d['lessonTitle']),
              "| enteredName:", d['enteredName'])
        page.screenshot(path=f"{EV}/07_09a_intro_visible.png")

        # dismiss by REAL click on the begin button (not a keypress)
        print("=== [S2] CLICK real #intro-begin to dismiss ===")
        page.click("#intro-begin")
        time.sleep(0.6)
        d = diag(page)
        print("after-dismiss introOpen:", d['introOpen'], "| verdict:", d['verdict'])

        # ---------- STEP 2 cont: hand 6000 N, press belly cell past 0.02 MPa, release ----------
        print("\n=== [S2] set hand to 6000 N + gentle belly press past 0.02 MPa, then release ===")
        cx, cy, ok = None, None, False
        # set the slider first so it reads 6000 "hand open" at capture time
        set_force(page, 6000); time.sleep(0.3)
        c = center(page); cx, cy = c['x'], c['y']
        print("center:", cx, cy)
        # settle so the streamed body mesh is rendered/touchable before pressing;
        # retry a couple of times if swiftshader hasn't drawn the body yet.
        time.sleep(2.0)
        for attempt in range(3):
            down(page, cx, cy)
            got = wait_for(lambda: (torso_p_mpa(page) or 0) >= 0.02, 6)
            if got:
                ok = True
                break
            up(page, cx, cy); time.sleep(0.4)
            time.sleep(1.3)
        print("goal latched:", ok, "| torsoP:", torso_p_mpa(page), "| forceVal:", diag(page)['forceVal'])
        # hold briefly then release cleanly
        time.sleep(0.3)
        up(page, cx, cy); time.sleep(0.5)

        passed = wait_for(lambda: 'PASSED' in diag(page)['verdict'], 7)
        d = diag(page); page.screenshot(path=f"{EV}/07_10_passed_clean.png")
        print("PASSED:", passed, "| verdict:", repr(d['verdict']),
              "| introOpen:", d['introOpen'], "| forceVal:", d['forceVal'],
              "| blood:", d['blood'][:90])

        # ---------- STEP 3: wait ~5s, prove intro does NOT reappear ----------
        print("\n=== [S3] wait ~5s, then capture (intro must NOT reappear) ===")
        time.sleep(5.0)
        d2 = diag(page); page.screenshot(path=f"{EV}/07_11_still_passed.png")
        print("still PASSED:", 'PASSED' in d2['verdict'], "| verdict:", repr(d2['verdict']),
              "| introOpen:", d2['introOpen'], "| forceVal:", d2['forceVal'],
              "| blood:", d2['blood'][:90])

        page_errors_summary = list(page_errors)
        print("\n=== PAGE ERRORS (%d) ===" % len(page_errors_summary), page_errors_summary)
        print("=== CONSOLE MESSAGES (%d) ===" % len(console_msgs))
        for m in console_msgs:
            print("   ", m)

        ctx.close()

    with open(f"{EV}/07_drive_clean_intro.txt", "w") as f:
        f.write("fresh_profile=%s\n" % fresh_dir)
        f.write("page_errors=%d\n" % len(page_errors))
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write("console_messages=%d\n" % len(console_msgs))
        for m in console_msgs:
            f.write("CONSOLE: %s\n" % m)
        f.write("intro_appeared=%s\n" % intro_appeared)
        f.write("passed=%s\n" % passed)
        f.write("still_passed=%s\n" % ('PASSED' in d2['verdict']))
        f.write("intro_open_at_07_10=%s\n" % d['introOpen'])
        f.write("intro_open_at_07_11=%s\n" % d2['introOpen'])
    print("\nwrote 07_drive_clean_intro.txt")


main()
