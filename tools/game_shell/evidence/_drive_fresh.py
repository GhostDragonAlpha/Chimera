import re, time, os, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
EV = r"E:\PythonChimera\tools\game_shell\evidence"


def diag(page):
    return page.evaluate("""()=>{
        var g=document.getElementById('gl-error');
        var ta=document.getElementById('try-again-btn');
        return {
            glErrorVisible: !!g && !g.classList.contains('hidden') && g.offsetParent!==null,
            verdict: document.getElementById('verdict').textContent,
            hand: document.getElementById('hand-state').textContent,
            blood: document.getElementById('blood').textContent.replace(/\\s+/g,' '),
            forceVal: document.getElementById('force').value,
            tryAgainVisible: !!ta && !ta.classList.contains('hidden') && ta.offsetParent!==null,
            playScreenOn: document.getElementById('screen-play').classList.contains('on'),
            startScreenOn: document.getElementById('screen-start').classList.contains('on'),
            lessonTitle: document.getElementById('lesson-title').textContent,
            nameHintVisible: (function(){var h=document.getElementById('name-hint');return !!h && h.style.display!=='none';})(),
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


def space_press(page):
    page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:' ',code:'Space',bubbles:true,cancelable:true}))")


def wait_for(pred, secs=8.0, interval=0.15):
    t = time.time()
    while time.time() - t < secs:
        if pred(): return True
        time.sleep(interval)
    return False


def press_center_hold(page, force, need_mpa=0.02):
    set_force(page, force); time.sleep(0.2)
    c = center(page); cx, cy = c['x'], c['y']
    down(page, cx, cy)
    ok = wait_for(lambda: (torso_p_mpa(page) or 0) >= need_mpa, 6)
    time.sleep(0.3)
    return cx, cy, ok


def main():
    page_errors = []
    console_msgs = []

    fresh_dir = tempfile.mkdtemp(prefix="chimera-fresh-")

    with sync_playwright() as p:
        # BRAND-NEW profile (no cache/cookies) + swiftshader so WebGL2 is real.
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

        # ---------- ACCEPTANCE A: full loop via REAL clicks ----------
        # PASS path (fresh name) and RUPTURE/RECOVERY path (a DIFFERENT fresh
        # name -> unpassed lesson 1, which is the only state that can rupture).
        print("\n=== [A1] LOAD (fresh profile, no cache) ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        d = diag(page)
        page.screenshot(path=f"{EV}/07_01_load.png")
        print("startScreenOn:", d['startScreenOn'], "| playScreenOn:", d['playScreenOn'],
              "| glErrorVisible:", d['glErrorVisible'], "| verdict:", d['verdict'])

        print("\n=== [A2] TYPE NAME + CLICK REAL #play-btn ===")
        page.fill("#name-input", "Tiel-Pass")
        page.click("#play-btn")   # the actual button element
        time.sleep(1.5)
        d = diag(page)
        page.screenshot(path=f"{EV}/07_02_name_play.png")
        print("startScreenOn:", d['startScreenOn'], "| playScreenOn:", d['playScreenOn'],
              "| lessonTitle:", repr(d['lessonTitle']), "| enteredName:", d['enteredName'],
              "| glErrorVisible:", d['glErrorVisible'])

        print("\n=== [A3] GENTLE BELLY PRESS past 0.02 MPa, release -> PASSED ===")
        cx, cy, ok = press_center_hold(page, 6000, 0.02)
        page.screenshot(path=f"{EV}/07_03_pressed.png")
        print("goal latched:", ok, "| torsoP:", torso_p_mpa(page), "| verdict:", diag(page)['verdict'])
        up(page, cx, cy); time.sleep(0.5)
        passed = wait_for(lambda: 'PASSED' in diag(page)['verdict'], 7)
        d = diag(page); page.screenshot(path=f"{EV}/07_04_passed.png")
        print("PASSED:", passed, "| verdict:", d['verdict'])

        # reset to a fresh start screen for the rupture session (new name).
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.2)

        print("\n=== [A4] MAX PRESS -> RUPTURE + try-again ===")
        # fresh UNPASSED lesson: back to start, new name, PLAY (a passed lesson
        # will not re-rupture).
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.2)
        page.fill("#name-input", "Tiel-Rupt-" + str(int(time.time() * 1000))[-5:])
        page.click("#play-btn"); time.sleep(1.4)
        # dismiss first-run greeting (it owns the keyboard and would swallow a
        # SPACE); a held pointer press applies belly pressure directly.
        page.evaluate("()=>{var o=document.getElementById('intro-overlay'); if(o) o.classList.add('hidden');}")
        set_force(page, 20000); time.sleep(0.2)
        c = center(page); cx, cy = c['x'], c['y']
        down(page, cx, cy)
        rupt = wait_for(lambda: (torso_p_mpa(page) or 0) >= 0.5, 6)
        time.sleep(0.4)
        d = diag(page); page.screenshot(path=f"{EV}/07_05_ruptured.png")
        print("reached>=0.5MPa:", rupt, "| verdict:", d['verdict'],
              "| tryAgainVisible:", d['tryAgainVisible'], "| blood:", d['blood'][:80])
        up(page, cx, cy); time.sleep(0.3)

        print("\n=== [A5] TRY AGAIN -> re-PASSED ===")
        wait_for(lambda: (torso_p_mpa(page) or 0) < 0.05, 5)
        page.click("#try-again-btn"); time.sleep(0.6)
        cx2, cy2, ok2 = press_center_hold(page, 6000, 0.02)
        page.screenshot(path=f"{EV}/07_06_recovery_pressed.png")
        print("re-latched:", ok2, "| torsoP:", torso_p_mpa(page), "| verdict:", diag(page)['verdict'])
        up(page, cx2, cy2); time.sleep(0.5)
        rec = wait_for(lambda: 'PASSED' in diag(page)['verdict'], 7)
        d = diag(page); page.screenshot(path=f"{EV}/07_07_recovery_passed.png")
        print("re-PASSED:", rec, "| verdict:", d['verdict'])

        # ---------- ACCEPTANCE D: PLAY guard audit (fresh start screen) ----------
        print("\n=== [D1] EMPTY NAME -> must prompt visibly (not silent) ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.2)
        d = diag(page)
        print("pre: startScreenOn:", d['startScreenOn'], "| playScreenOn:", d['playScreenOn'])
        page.fill("#name-input", "")
        page.click("#play-btn")
        time.sleep(0.8)
        d = diag(page); page.screenshot(path=f"{EV}/07_08_empty_name.png")
        print("startScreenOn:", d['startScreenOn'], "| nameHintVisible:", d['nameHintVisible'],
              "| playScreenOn:", d['playScreenOn'])

        print("\n=== [D2] NORMAL NAME -> proceeds to lesson card ===")
        page.fill("#name-input", "Tiel-D")
        page.click("#play-btn")
        time.sleep(1.5)
        d = diag(page); page.screenshot(path=f"{EV}/07_09_play_ok.png")
        print("startScreenOn:", d['startScreenOn'], "| playScreenOn:", d['playScreenOn'],
              "| lessonTitle:", repr(d['lessonTitle']), "| enteredName:", d['enteredName'])

        page_errors_summary = list(page_errors)
        print("\n=== PAGE ERRORS (%d) ===" % len(page_errors_summary), page_errors_summary)
        print("=== CONSOLE MESSAGES (%d) ===" % len(console_msgs))
        for m in console_msgs:
            print("   ", m)

        ctx.close()

    # write a machine-readable record alongside the screenshots
    with open(f"{EV}/07_drive_fresh.txt", "w") as f:
        f.write("fresh_profile=%s\n" % fresh_dir)
        f.write("page_errors=%d\n" % len(page_errors))
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write("console_messages=%d\n" % len(console_msgs))
        for m in console_msgs:
            f.write("CONSOLE: %s\n" % m)
    print("\nwrote 07_drive_fresh.txt")


main()
