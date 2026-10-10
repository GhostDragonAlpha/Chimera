#!/usr/bin/env python3
# Full-viewport pick scan at DEFAULT camera using the game's own rect-relative NDC.
# If the body renders anywhere, SOME pixel must pick it. Print canvas rect + hits.
import time, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210/?debug=1"


def main():
    fresh = tempfile.mkdtemp(prefix="chimera-full-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh, headless=True, viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        pg = ctx.pages[0]
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        pg.fill("#name-input", "Tiel-Full")
        pg.click("#play-btn"); time.sleep(1.6)
        for _ in range(80):
            if pg.evaluate("()=>!document.getElementById('intro-overlay').classList.contains('hidden')"):
                break
            time.sleep(0.1)
        pg.click("#intro-begin"); time.sleep(0.8)
        pg.evaluate("""()=>{var s=document.getElementById('force');s.value=6000;s.dispatchEvent(new Event('input',{bubbles:true}));}""")
        time.sleep(0.4)

        rect = pg.evaluate("()=>{var r=document.getElementById('gl').getBoundingClientRect();return {l:r.left,t:r.top,w:r.width,h:r.height};}")
        print("canvas #gl rect:", rect)
        out = pg.evaluate("""() => {
            var out=[], n=0;
            for (var py=0; py<900; py+=12)
              for (var px=0; px<1280; px+=12){
                var r=window.__h16pickProbe(px,py);
                if (r&&r.raw){n++; out.push([px,py,+r.raw[1].toFixed(2)]);}
              }
            return {hits:n, sample:out.slice(0,12), vertCount:r?r.vertCount:0};
        }""")
        print("FULL scan hits=%d / ~8500 px" % out['hits'])
        for s in out['sample']:
            print("   px=%s py=%s worldY=%s" % (s[0], s[1], s[2]))
        pg.screenshot(path="07_fullscan_probe.png")
        print("page_errors=%d" % len(errs))
        ctx.close()


main()
