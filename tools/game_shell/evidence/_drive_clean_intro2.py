#!/usr/bin/env python3
# Clean-intro PASSED drive: EXACTLY the proven _drive_fresh pipeline (synthetic
# PointerEvent on #gl, --use-angle=swiftshader, no ?debug), but with a REAL
# click to dismiss the first-run intro before pressing belly -> PASSED.
import re, time, os, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
EV = r"E:\PythonChimera\tools\game_shell\evidence"


def diag(page):
    return page.evaluate("""()=>{
        var g=document.getElementById('gl-error');
        return {
            glErrorVisible: !!g && !g.classList.contains('hidden') && g.offsetParent!==null,
            verdict: document.getElementById('verdict').textContent,
            blood: document.getElementById('blood').textContent.replace(/\s+/g,' '),
            forceVal: document.getElementById('force').value,
            playScreenOn: document.getElementById('screen-play').classList.contains('on'),
            lessonTitle: document.getElementById('lesson-title').textContent,
            introHidden: document.getElementById('intro-overlay').classList.contains('hidden')
        };
    }""")


def torso_p_mpa(page):
    bd = page.evaluate("()=>document.getElementById('blood').textContent")
    m = re.search(r'torso \(cell 1\):.*?P=([0-9.]+)\s*MPa', bd)
    # NOTE: keep this a normal string; \s is fine inside re at runtime (py3.12+ warns only for str literals in source)
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
    fresh_dir = tempfile.mkdtemp(prefix="chimera-clean-intro-")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]

        def on_pe(e): page_errors.append(str(e))
        page.on("pageerror", on_pe)

        print("fresh profile:", fresh_dir)

        # remove any stale progress for this name so seen_intro is definitely unset
        prog = os.path.abspath(os.path.join(os.path.dirname(EV), "progress", "Tiel-Clean.json"))
        if os.path.exists(prog):
            try: os.remove(prog)
            except OSError: pass

        print("=== TYPE NAME + CLICK REAL #play-btn ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        page.fill("#name-input", "Tiel-Clean")
        page.click("#play-btn")
        time.sleep(1.6)
        d = diag(page)
        print("playScreenOn:", d['playScreenOn'], "| lessonTitle:", repr(d['lessonTitle']),
              "| glErrorVisible:", d['glErrorVisible'])

        # WAIT for the first-run intro overlay to actually appear, then DISMISS
        # it with a REAL click on its begin button.
        print("=== WAIT INTRO + REAL-CLICK BEGIN ===")
        intro_seen = wait_for(lambda: (lambda: page.evaluate(
            "()=>!document.getElementById('intro-overlay').classList.contains('hidden')"))(), 8)
        print("intro appeared:", intro_seen)
        time.sleep(0.4)
        page.click("#intro-begin")
        time.sleep(0.8)
        d = diag(page)
        print("after dismiss: introHidden:", d['introHidden'], "| verdict:", d['verdict'])
        page.screenshot(path=f"{EV}/07_09a_intro_visible.png")  # capture the dismissed state

        print("=== SET HAND 6000N + PRESS BELLY PAST 0.02 MPa ===")
        set_force(page, 6000); time.sleep(0.3)
        c = center(page); cx, cy = c['x'], c['y']
        print("center:", cx, cy)
        down(page, cx, cy)
        ok = wait_for(lambda: (torso_p_mpa(page) or 0) >= 0.02, 6)
        time.sleep(0.4)
        print("belly>=0.02MPa:", ok, "| torsoP:", torso_p_mpa(page), "| verdict:", diag(page)['verdict'])
        up(page, cx, cy); time.sleep(0.5)

        passed = wait_for(lambda: 'PASSED' in diag(page)['verdict'], 7)
        d = diag(page)
        page.screenshot(path=f"{EV}/07_10_passed_clean.png")
        print("PASSED:", passed, "| verdict:", d['verdict'], "| introHidden:", d['introHidden'])

        # same session: wait ~5s, prove intro does NOT reappear
        time.sleep(5.0)
        d2 = diag(page)
        page.screenshot(path=f"{EV}/07_11_still_passed.png")
        print("after 5s: PASSED-still:", 'PASSED' in d2['verdict'], "| introHidden:", d2['introHidden'],
              "| verdict:", d2['verdict'])

        print("\n=== PAGE ERRORS (%d) ===" % len(page_errors))
        for e in page_errors:
            print("   ", e)

        ctx.close()

    with open(f"{EV}/07_drive_clean_intro.txt", "w") as f:
        f.write("fresh_profile=%s\n" % fresh_dir)
        f.write("page_errors=%d\n" % len(page_errors))
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        print("\nwrote 07_drive_clean_intro.txt")


main()
