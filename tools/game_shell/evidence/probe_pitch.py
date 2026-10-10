#!/usr/bin/env python3
# Probe: pitch the camera DOWN via a REAL held-mouse vertical drag (the only
# way orbit responds, since pointermove returns early unless pressed). Then
# probe pickWorld at center + grid to see if the body is now visible.
import sys, json, time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210/?debug=1"

def main():
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--webgl=swiftshader", "--use-gl=angle",
                                      "--enable-unsafe-swiftshader"])
        ctx = br.new_context(viewport={"width": 1200, "height": 800})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: (errs.append(m.text) if m.type == "error" else None))

        pg.goto(URL, wait_until="load")
        time.sleep(1.5)
        # fresh name so intro appears; type + play
        pg.fill("#name-input", "Tiel-Pitch")
        pg.click("#play-btn")
        time.sleep(0.6)
        st = pg.evaluate("""() => ({
            play: document.getElementById('screen-play').classList.contains('on'),
            overlayHidden: document.getElementById('intro-overlay').classList.contains('hidden'),
            beginVisible: !!document.getElementById('intro-begin')
        })""")
        print("post-play state:", st)
        # dismiss intro only if it is actually visible (not hidden)
        if (not st["overlayHidden"] and st["play"]):
            time.sleep(0.3)
            try: pg.click("#intro-begin")
            except Exception as e: print("dismiss err:", str(e)[:50])
            time.sleep(0.8)
        # set force to 6000 N (range input: set value + dispatch input)
        pg.evaluate("""() => { var s=document.getElementById('force'); s.value=6000; s.dispatchEvent(new Event('input',{bubbles:true})); }""")
        time.sleep(0.5)

        def probe_grid():
            return pg.evaluate("""() => {
                var out=[]; var n=0;
                for (var py=80; py<720; py+=60) {
                  for (var px=120; px<1080; px+=60) {
                    var r = window.__h16pickProbe(px, py);
                    if (r && r.raw) { n++; out.push([px,py, +r.raw[1].toFixed(2)]); }
                  }
                }
                return {hits:n, sample:out.slice(0,8),
                        center: window.__h16pickProbe(600,400)};
            }""")

        # baseline (no pitch) at center
        base = pg.evaluate("""() => { var c=window.__h16pickProbe(600,400); return {fwd: c.fwd, dir: c.dir, hit: !!c.raw}; }""")
        print("BASELINE fwd.y=%.3f dir.y=%.3f hit=%s" % (base["fwd"][1], base["dir"][1], base["hit"]))

        # REAL vertical drag DOWN to pitch camera down: press at top-center, move down in steps
        W, H = 1200, 800
        cx = W // 2
        pg.mouse.down()
        y = 60
        for _ in range(40):
            y += 18
            if y > H - 40: y = H - 40
            # also tiny horizontal nudge so it clears the 6px orbit threshold
            pg.mouse.move(cx + 20, y)
            time.sleep(0.03)
        pg.mouse.up()
        time.sleep(1.0)

        after = pg.evaluate("() => ({fwd: window.__h16pickProbe(600,400).fwd})")
        print("AFTER pitch fwd.y=%.3f" % (after["fwd"][1],))

        g = probe_grid()
        print("GRID hits after pitch=%d" % g["hits"])
        if g["sample"]:
            for s in g["sample"]:
                print("   px=%s py=%s worldY=%s" % (s[0], s[1], s[2]))
        c = g["center"]
        print("CENTER raw=%s" % ("HIT y=%.3f"%c["raw"][1] if c and c["raw"] else "null"))

        # try a second, steeper drag from very top to very bottom
        pg.mouse.down()
        y = 40
        for _ in range(45):
            y += 16
            if y > H - 30: y = H - 30
            pg.mouse.move(cx - 15, y)
            time.sleep(0.03)
        pg.mouse.up()
        time.sleep(1.0)
        g2 = probe_grid()
        print("GRID hits after 2nd pitch=%d" % g2["hits"])
        c2 = g2["center"]
        print("CENTER raw=%s" % ("HIT y=%.3f"%c2["raw"][1] if c2 and c2["raw"] else "null"))

        pg.screenshot(path="07_pitch_probe.png")
        print("page_errors=%d" % len(errs))
        br.close()

if __name__ == "__main__":
    main()
