#!/usr/bin/env python3
# Verify the framing recipe end-to-end: fresh -> real-click dismiss intro ->
# force 6000 -> drag mouse DOWN fully (phi -> -1.45, camera below body) -> confirm
# pickWorld hits at center + body renders -> REAL-click to press -> PASSED.
import time, re, os, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210/?debug=1"
W, H = 1280, 900


def diag(pg):
    return pg.evaluate("""()=>({
        verdict: document.getElementById('verdict').textContent,
        introHidden: document.getElementById('intro-overlay').classList.contains('hidden'),
        blood: document.getElementById('blood').textContent.replace(/\s+/g,' ')
    })""")


def torso_p_mpa(pg):
    bd = pg.evaluate("()=>document.getElementById('blood').textContent")
    m = re.search(r'torso \(cell 1\):.*?P=([0-9.]+)\s*MPa', bd)
    return float(m.group(1)) if m else None


def probe(pg):
    return pg.evaluate("""() => {
        var out=[], n=0;
        for (var dy=-40; dy<=40; dy+=10) {
          for (var dx=-40; dx<=40; dx+=10) {
            var r = window.__h16pickProbe(600+dx, 450+dy);
            if (r && r.raw) { n++; out.push([600+dx,450+dy,+r.raw[1].toFixed(2)]); }
          }
        }
        var c = window.__h16pickProbe(600,450);
        return {hits:n, sample:out.slice(0,6), centerRaw: !!c.raw, fwdY: c.fwd[1]};
    }""")


def drag_down(pg):
    # rig sign: mouse DOWN -> cam.phi decreases -> -1.45 (camera below body)
    pg.mouse.down()
    y = H - 60
    for _ in range(60):
        y -= 11
        if y < 30: y = 30
        pg.mouse.move(W//2 + 15, y)
        time.sleep(0.02)
    pg.mouse.up()
    time.sleep(0.8)


def main():
    fresh_dir = tempfile.mkdtemp(prefix="chimera-final-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh_dir, headless=True, viewport={'width': W, 'height': H},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        pg = ctx.pages[0]
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        pg.fill("#name-input", "Tiel-Final")
        pg.click("#play-btn"); time.sleep(1.6)
        # real-click dismiss intro
        for _ in range(80):
            if pg.evaluate("()=>!document.getElementById('intro-overlay').classList.contains('hidden')"):
                break
            time.sleep(0.1)
        pg.click("#intro-begin"); time.sleep(0.8)
        pg.evaluate("""()=>{var s=document.getElementById('force');s.value=6000;s.dispatchEvent(new Event('input',{bubbles:true}));}""")
        time.sleep(0.4)

        print("post: introHidden=%s verdict=%r" % (diag(pg)['introHidden'], diag(pg)['verdict']))
        # frame body from below
        drag_down(pg)
        pr = probe(pg)
        print("after drag DOWN: centerRaw=%s gridHits(81px)=%s fwdY=%.3f" % (pr['centerRaw'], pr['hits'], pr['fwdY']))
        for s in pr['sample']:
            print("   px=%s py=%s worldY=%s" % (s[0], s[1], s[2]))
        pg.screenshot(path="07_final_frame.png")

        # try a REAL click at center to press
        pg.mouse.click(600, 450); time.sleep(0.8)
        print("after real-click: torsoP=%s verdict=%r" % (torso_p_mpa(pg), diag(pg)['verdict']))
        pr2 = probe(pg)
        print("post-click gridHits=%s centerRaw=%s" % (pr2['hits'], pr2['centerRaw']))

        # if still no framing, try dragging down again then click
        if not pr2['centerRaw']:
            drag_down(pg)
            pr3 = probe(pg)
            print("after 2nd drag: centerRaw=%s gridHits=%s fwdY=%.3f" % (pr3['centerRaw'], pr3['hits'], pr3['fwdY']))
            pg.mouse.click(600, 450); time.sleep(0.8)
            print("after 2nd click: torsoP=%s verdict=%r" % (torso_p_mpa(pg), diag(pg)['verdict']))

        pg.screenshot(path="07_final_click.png")
        print("page_errors=%d" % len(errs))
        for e in errs: print("   ", e)
        ctx.close()


main()
