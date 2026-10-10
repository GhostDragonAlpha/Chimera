#!/usr/bin/env python3
# Sweep the camera in the LOOK-DOWN direction (mouse drag UP) and wheel-zoom,
# recording fwd.y and pickWorld grid hits at each step. Decides if any reachable
# camera sees the floor-level body.
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210/?debug=1"
W, H = 1200, 800
CX = W // 2

def grid_hits(pg):
    return pg.evaluate("""() => {
        var out=[], n=0;
        for (var py=60; py<760; py+=55) {
          for (var px=110; px<1090; px+=55) {
            var r = window.__h16pickProbe(px, py);
            if (r && r.raw) { n++; out.push([px,py,+r.raw[1].toFixed(2)]); }
          }
        }
        var c = window.__h16pickProbe(600, 400);
        return {hits:n, sample:out.slice(0,6), cxHit: !!c.raw};
    }""")

def fwd_y(pg):
    return pg.evaluate("() => window.__h16pickProbe(%d,%d).fwd[1]" % (CX, H//2))

def drag_up(pg):
    # look-DOWN = mouse moves UP (y decreasing), per probe_pitch sign result
    pg.mouse.down()
    y = H - 40
    for _ in range(50):
        y -= 16
        if y < 30: y = 30
        pg.mouse.move(CX + 20, y)
        time.sleep(0.025)
    pg.mouse.up()
    time.sleep(0.8)

def drag_down(pg):
    pg.mouse.down()
    y = 40
    for _ in range(50):
        y += 16
        if y > H - 30: y = H - 30
        pg.mouse.move(CX - 20, y)
        time.sleep(0.025)
    pg.mouse.up()
    time.sleep(0.8)

def zoom_in(pg, times=6):
    for _ in range(times):
        pg.mouse.wheel(0, -300)   # negative dy = scroll up = zoom in (r decreases)
        time.sleep(0.15)

def main():
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
        ctx = br.new_context(viewport={"width": W, "height": H})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load")
        time.sleep(1.2)
        pg.fill("#name-input", "Tiel-Pitch2")
        pg.click("#play-btn")
        time.sleep(0.5)
        # dismiss intro if visible
        vis = pg.evaluate("() => !document.getElementById('intro-overlay').classList.contains('hidden')")
        if vis:
            time.sleep(0.3); pg.click("#intro-begin"); time.sleep(0.6)
        pg.evaluate("""() => { var s=document.getElementById('force'); s.value=6000; s.dispatchEvent(new Event('input',{bubbles:true})); }""")
        time.sleep(0.4)

        print("BASE fwd.y=%.3f grid=%s cxHit=%s" % (fwd_y(pg), grid_hits(pg)["hits"], grid_hits(pg)["cxHit"]))

        drag_down(pg)  # this direction raised fwd.y; do it to establish range both ways
        print("after drag_fwd.y=%.3f grid=%s" % (fwd_y(pg), grid_hits(pg)["hits"]))

        drag_up(pg)    # look-down direction
        print("after drag_UP fwd.y=%.3f grid=%s cxHit=%s" % (fwd_y(pg), grid_hits(pg)["hits"], grid_hits(pg)["cxHit"]))

        zoom_in(pg, 8)
        print("after ZOOM fwd.y=%.3f grid=%s cxHit=%s" % (fwd_y(pg), grid_hits(pg)["hits"], grid_hits(pg)["cxHit"]))

        # combine: zoom then look-down drag
        drag_up(pg)
        print("after zoom+LOOKDOWN fwd.y=%.3f grid=%s cxHit=%s" % (fwd_y(pg), grid_hits(pg)["hits"], grid_hits(pg)["cxHit"]))

        pg.screenshot(path="07_pitch2_probe.png")
        print("page_errors=%d" % len(errs))
        br.close()

if __name__ == "__main__":
    main()
