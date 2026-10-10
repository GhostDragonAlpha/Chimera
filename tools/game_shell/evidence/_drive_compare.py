#!/usr/bin/env python3
# A/B: (control) replicate _drive_fresh A3 exactly -- synthetic press, NO intro
# dismissal -- vs (test) REAL-click dismiss then same synthetic press. Both use
# the proven --use-angle=swiftshader + synthetic PointerEvent-on-#gl pipeline.
import re, time, os, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"


def diag(page):
    return page.evaluate("""()=>({
        verdict: document.getElementById('verdict').textContent,
        introHidden: document.getElementById('intro-overlay').classList.contains('hidden'),
        lessonTitle: document.getElementById('lesson-title').textContent
    })""")


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


def fresh_name():
    return "Tiel-" + str(int(time.time() * 1000))[-6:]


def play(page):
    page.fill("#name-input", fresh_name())
    page.click("#play-btn")
    time.sleep(1.5)


def press_belly(page):
    set_force(page, 6000); time.sleep(0.3)
    c = center(page); cx, cy = c['x'], c['y']
    down(page, cx, cy)
    ok = wait_for(lambda: (torso_p_mpa(page) or 0) >= 0.02, 6)
    time.sleep(0.3)
    up(page, cx, cy); time.sleep(0.4)
    return cx, cy, ok


def main():
    page_errors = []
    fresh_dir = tempfile.mkdtemp(prefix="chimera-ab-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        print("=== CONTROL: no intro dismissal (replicate A3) ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.2)
        play(page)
        d = diag(page)
        print("post-play: lesson=%s introHidden=%s" % (d['lessonTitle'], d['introHidden']))
        cx, cy, ok = press_belly(page)
        print("CONTROL belly>=0.02: %s  torsoP=%s  center=(%g,%g)" % (ok, torso_p_mpa(page), cx, cy))
        passed = wait_for(lambda: 'PASSED' in diag(page)['verdict'], 7)
        print("CONTROL PASSED:", passed, "| verdict:", diag(page)['verdict'])

        print("\n=== TEST: REAL-click dismiss then press ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.2)
        play(page)
        d = diag(page)
        intro_seen = wait_for(lambda: not diag(page)['introHidden'], 8)
        print("intro appeared:", intro_seen)
        time.sleep(0.4)
        page.click("#intro-begin")
        time.sleep(0.8)
        print("after real-click dismiss: introHidden=%s" % diag(page)['introHidden'])
        cx2, cy2, ok2 = press_belly(page)
        print("TEST belly>=0.02: %s  torsoP=%s  center=(%g,%g)" % (ok2, torso_p_mpa(page), cx2, cy2))
        passed2 = wait_for(lambda: 'PASSED' in diag(page)['verdict'], 7)
        print("TEST PASSED:", passed2, "| verdict:", diag(page)['verdict'])

        print("\npage_errors=%d" % len(page_errors))
        for e in page_errors: print("   ", e)
        ctx.close()


main()
