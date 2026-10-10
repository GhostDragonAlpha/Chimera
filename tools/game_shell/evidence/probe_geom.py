#!/usr/bin/env python3
# While looking nearly straight down, do a DENSE full-frame pick scan and dump
# vertCount (RG.verts populated?) + screenshot so we can SEE what's rendered vs
# what pickWorld detects.
import time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210/?debug=1"
W, H = 1200, 800

def main():
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
        ctx = br.new_context(viewport={"width": W, "height": H})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: (errs.append(m.text) if m.type == "error" else None))
        pg.goto(URL, wait_until="load")
        time.sleep(1.2)
        pg.fill("#name-input", "Tiel-Geom")
        pg.click("#play-btn")
        time.sleep(0.5)
        vis = pg.evaluate("() => !document.getElementById('intro-overlay').classList.contains('hidden')")
        if vis:
            time.sleep(0.3); pg.click("#intro-begin"); time.sleep(0.6)
        pg.evaluate("""() => { var s=document.getElementById('force'); s.value=6000; s.dispatchEvent(new Event('input',{bubbles:true})); }""")
        time.sleep(0.4)

        # look straight down: drag mouse UP fully
        pg.mouse.down()
        y = H - 40
        for _ in range(55):
            y -= 15
            if y < 30: y = 30
            pg.mouse.move(W//2 + 20, y)
            time.sleep(0.02)
        pg.mouse.up()
        time.sleep(0.8)

        info = pg.evaluate("""() => {
            var c = window.__h16pickProbe(600,400);
            return {fwdY: c.fwd[1], vertCount: c.vertCount, triCount: c.triCount,
                    sum2: c.sum2, centerRaw: c.raw ? true : false};
        }""")
        print("LOOK-DOWN info:", info)

        # dense full-frame scan 15px
        dens = pg.evaluate("""() => {
            var n=0, total=0, xs=[], ys=[];
            for (var py=0; py<800; py+=15) {
              for (var px=0; px<1200; px+=15) {
                total++;
                var r = window.__h16pickProbe(px,py);
                if (r && r.raw) { n++; if (xs.length<8){xs.push([px,py,+r.raw[1].toFixed(2)]);} }
              }
            }
            return {total:total, hits:n, sample:xs};
        }""")
        print("DENSE scan: %d/%d pixels hit" % (dens["hits"], dens["total"]))
        for s in dens["sample"]:
            print("   px=%s py=%s worldY=%s" % (s[0], s[1], s[2]))

        # also: does the page think a body is present? check verdict/hand text
        dom = pg.evaluate("""() => ({
            verdict: document.getElementById('verdict') && document.getElementById('verdict').textContent,
            hand: document.getElementById('hand-text') && document.getElementById('hand-text').textContent,
            lesson: document.querySelector('.lesson-title') && document.querySelector('.lesson-title').textContent
        })""")
        print("DOM:", dom)

        pg.screenshot(path="07_geom_probe.png")
        print("page_errors=%d" % len(errs))
        br.close()

if __name__ == "__main__":
    main()
