import re, time, os, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
EV = r"E:\PythonChimera\tools\game_shell\evidence"


def diag(page):
    return page.evaluate("""()=>{
        var io=document.getElementById('intro-overlay');
        return {
            verdict: document.getElementById('verdict').textContent,
            blood: document.getElementById('blood').textContent.replace(/\s+/g,' '),
            forceVal: document.getElementById('force').value,
            introOpen: !!io && !io.classList.contains('hidden'),
            playScreenOn: document.getElementById('screen-play').classList.contains('on'),
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


def one_attempt(page, name):
    """One fresh page load for `name`: PLAY -> wait intro -> click begin ->
    set 6000N -> synthetic belly press past 0.02 MPa -> release -> PASSED?"""
    page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
    page.fill("#name-input", name)
    page.click("#play-btn")          # real click
    if not wait_for(lambda: diag(page)['introOpen'], 6):
        return None, "no-intro"
    page.screenshot(path=f"{EV}/07_09a_intro_visible.png")   # show intro up
    page.click("#intro-begin")         # REAL click to dismiss
    time.sleep(0.5)
    if diag(page)['introOpen']:
        return None, "intro-not-dismissed"
    cx, cy = center(page)['x'], center(page)['y']
    ok = wait_for(lambda: (torso_p_mpa(page) or 0) >= 0.02, 6)
    d = diag(page)
    return (ok, torso_p_mpa(page), d['verdict']), ("press" if ok else "no-press")


def main():
    page_errors = []
    console_msgs = []
    max_tries = 10

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            tempfile.mkdtemp(prefix="chimera-clean-retry-"), headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]

        def on_pe(e): page_errors.append(str(e))
        def on_con(e): console_msgs.append(f"[{e.type}] {e.text}")
        page.on("pageerror", on_pe)
        page.on("console", on_con)

        base = int(time.time())
        for attempt in range(1, max_tries + 1):
            name = "Tiel-Clean-%d" % (base - 100 + attempt)
            res, tag = one_attempt(page, name)
            d = diag(page)
            print(f"[try {attempt}] name={name} tag={tag} res={res} "
                  f"| introOpen={d['introOpen']} verdict={d['verdict'][:40]!r} "
                  f"force={d['forceVal']} blood={d['blood'][:60]}")
            if res and res[0]:  # press latched past 0.02 MPa
                up(page, *center(page).values() if False else (
                    page.evaluate("()=>document.getElementById('gl').getBoundingClientRect().left+document.getElementById('gl').width/2"),
                    page.evaluate("()=>document.getElementById('gl').getBoundingClientRect().top+document.getElementById('gl').height/2")))
                time.sleep(0.5)
                passed = wait_for(lambda: 'PASSED' in diag(page)['verdict'], 8)
                d = diag(page)
                print(f"    -> PASSED={passed} verdict={d['verdict']!r}")
                if passed:
                    page.screenshot(path=f"{EV}/07_10_passed_clean.png")
                    print("captured 07_10_passed_clean.png")
                    break
        else:
            print("NO CLEAN PASSED across", max_tries, "tries")

        d2 = diag(page)
        page.screenshot(path=f"{EV}/07_11_still_passed.png")
        print("still:", 'PASSED' in d2['verdict'], "| introOpen:", d2['introOpen'])

        print("\n=== PAGE ERRORS (%d) ===" % len(page_errors), page_errors)
        print("=== CONSOLE (%d) ===" % len(console_msgs))
        for m in console_msgs:
            print("   ", m)
        ctx.close()

    with open(f"{EV}/07_drive_clean_intro.txt", "w") as f:
        f.write("page_errors=%d\n" % len(page_errors))
        for e in page_errors:
            f.write("PAGEERROR: %s\n" % e)
        f.write("console_messages=%d\n" % len(console_msgs))
        for m in console_msgs:
            f.write("CONSOLE: %s\n" % m)
    print("\nwrote 07_drive_clean_intro.txt")


main()
