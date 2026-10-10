import time, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
EV = r"E:\PythonChimera\tools\game_shell\evidence"


def main():
    errs = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            tempfile.mkdtemp(prefix="chimera-nostore-"), headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: errs.append(str(e)))

        print("=== quick recheck after restart: start -> PLAY -> lesson card ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        start_on = page.evaluate("()=>document.getElementById('screen-start').classList.contains('on')")
        page.fill("#name-input", "Tiel-NoStore"); page.click("#play-btn"); time.sleep(1.6)
        playScreenOn = page.evaluate("()=>document.getElementById('screen-play').classList.contains('on')")
        lessonTitle = page.evaluate("()=>document.getElementById('lesson-title').textContent")
        glErrVisible = page.evaluate("()=>document.getElementById('gl-error').offsetParent!==null")
        page.screenshot(path=f"{EV}/07_nostore_recheck.png")
        print("startScreenOn:", start_on, "| playScreenOn:", playScreenOn,
              "| lessonTitle:", repr(lessonTitle), "| glErrVisible:", glErrVisible)
        print("PAGE ERRORS (%d):" % len(errs), errs)
        ctx.close()


main()
