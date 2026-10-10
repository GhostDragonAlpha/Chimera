import time, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"
EV = r"E:\PythonChimera\tools\game_shell\evidence"


def main():
    page_errors = []
    with sync_playwright() as p:
        # WebGL REFUSED: --disable-webgl makes getContext('webgl2') return null.
        ctx = p.chromium.launch_persistent_context(
            tempfile.mkdtemp(prefix="chimera-nogl-"), headless=True,
            viewport={'width': 1280, 'height': 900},
            args=['--disable-webgl', '--ignore-gpu-binary', '--skip-gpu-data-loading'])
        page = ctx.pages[0]
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        print("=== LOAD (WebGL disabled) ===")
        page.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        webgl2_avail = page.evaluate(
            "function(){try{var c=document.getElementById('gl');return !!c.getContext('webgl2');}"
            "catch(e){return 'throw';}}")
        print("webgl2_available_at_load:", webgl2_avail)

        print("=== CLICK PLAY ===")
        page.fill("#name-input", "Tiel-NoGL")
        page.click("#play-btn"); time.sleep(1.6)
        # dismiss first-run greeting so the WebGL-failure message is unobstructed
        page.evaluate(
            "function(){var o=document.getElementById('intro-overlay');"
            "if(o)o.classList.add('hidden');}")
        time.sleep(0.4)
        d = page.evaluate(
            "function(){var ps=document.getElementById('screen-play');"
            "var g=document.getElementById('gl-error');"
            "var v=document.getElementById('verdict');"
            "return {playScreenOn:ps&&ps.classList.contains('on'),"
            "glErr:!!g,glVis:g&&g.offsetParent!==null,"
            "glText:g?g.textContent:'',"
            "verdict:v?v.textContent:''};}")
        page.screenshot(path=f"{EV}/07_webgl_refused.png")
        print("playScreenOn:", d['playScreenOn'])
        print("gl-error present:", d['glErr'], "| gl-error VISIBLE:", d['glVis'])
        print("gl-error text:", repr(d['glText']))
        print("verdict:", repr(d['verdict']))
        print("PAGE ERRORS (%d):" % len(page_errors), page_errors)
        ctx.close()


main()
