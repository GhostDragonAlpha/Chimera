#!/usr/bin/env python3
# Decisive: REAL page.mouse.click at candidate pixels (exercises tryTouch ->
# pickWorld + pickNearMiss WITH grace), watching for a genuine press to land
# (letgo-btn 'hot' class / hand-text update). Test both default and look-down cam.
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210/?debug=1"
W, H = 1200, 800

def press_signals(pg):
    return pg.evaluate("""() => {
        var lb = document.getElementById('letgo-btn');
        var ht = document.getElementById('hand-text');
        return { letgoHot: !!lb && lb.classList.contains('hot'),
                 hand: ht ? ht.textContent : null };
    }""")

def look_down(pg):
    pg.mouse.down()
    y = H - 40
    for _ in range(55):
        y -= 15
        if y < 30: y = 30
        pg.mouse.move(W//2 + 20, y)
        time.sleep(0.02)
    pg.mouse.up()
    time.sleep(0.6)

def try_click(pg, x, y):
    pg.mouse.click(x, y)
    time.sleep(0.7)
    return press_signals(pg)

def main():
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
        ctx = br.new_context(viewport={"width": W, "height": H})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load")
        time.sleep(1.2)
        pg.fill("#name-input", "Tiel-Click")
        pg.click("#play-btn")
        time.sleep(0.5)
        vis = pg.evaluate("() => !document.getElementById('intro-overlay').classList.contains('hidden')")
        if vis:
            time.sleep(0.3); pg.click("#intro-begin"); time.sleep(0.6)
        pg.evaluate("""() => { var s=document.getElementById('force'); s.value=6000; s.dispatchEvent(new Event('input',{bubbles:true})); }""")
        time.sleep(0.4)

        # default camera: click a small cluster around center
        print("DEFAULT cam clicks:")
        for (x, y) in [(600, 400), (620, 420), (580, 380), (640, 440), (560, 400)]:
            r = try_click(pg, x, y)
            print("   click(%d,%d) -> %s" % (x, y, r))

        # look straight down, then cluster
        look_down(pg)
        print("LOOK-DOWN cam clicks:")
        for (x, y) in [(600, 400), (610, 410), (590, 390), (620, 400), (580, 420), (600, 430)]:
            r = try_click(pg, x, y)
            print("   click(%d,%d) -> %s" % (x, y, r))

        pg.screenshot(path="07_realclick_probe.png")
        print("page_errors=%d" % len(errs))
        br.close()

if __name__ == "__main__":
    main()
