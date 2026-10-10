#!/usr/bin/env python3
# Focused: DEFAULT camera (no orbit), scan grid around predicted body spot
# (ndc ~0.02,-0.34 -> screen ~(600,603)) with __h16pickProbe; then real-click it.
import time, re, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210/?debug=1"


def diag(pg):
    return pg.evaluate("""()=>({verdict:document.getElementById('verdict').textContent})""")


def torso_p_mpa(pg):
    bd = pg.evaluate("()=>document.getElementById('blood').textContent")
    m = re.search(r'torso \(cell 1\):.*?P=([0-9.]+)\s*MPa', bd)
    return float(m.group(1)) if m else None


def scan(pg, x0, y0, x1, y1, step=15):
    return pg.evaluate("""(a)=>{
        var [x0,y0,x1,y1,st]=a, out=[], n=0;
        for (var py=y0; py<=y1; py+=st)
          for (var px=x0; px<=x1; px+=st){
            var r=window.__h16pickProbe(px,py);
            if (r&&r.raw){n++; out.push([px,py,+r.raw[1].toFixed(2)]);}
          }
        return {hits:n, sample:out.slice(0,8)};
    }""", [x0, y0, x1, y1, step])


def main():
    fresh = tempfile.mkdtemp(prefix="chimera-spot-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            fresh, headless=True, viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        pg = ctx.pages[0]
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load", timeout=30000); time.sleep(1.5)
        pg.fill("#name-input", "Tiel-Spot")
        pg.click("#play-btn"); time.sleep(1.6)
        for _ in range(80):
            if pg.evaluate("()=>!document.getElementById('intro-overlay').classList.contains('hidden')"):
                break
            time.sleep(0.1)
        pg.click("#intro-begin"); time.sleep(0.8)
        pg.evaluate("""()=>{var s=document.getElementById('force');s.value=6000;s.dispatchEvent(new Event('input',{bubbles:true}));}""")
        time.sleep(0.4)

        # default camera: scan lower-middle where sweep predicts body center
        print("DEFAULT cam scan around (600,603):")
        r = scan(pg, 520, 520, 680, 690)
        print("   hits=%d" % r['hits'])
        for s in r['sample']:
            print("   px=%s py=%s worldY=%s" % (s[0], s[1], s[2]))
        # broader scan to locate any hit row
        r2 = scan(pg, 400, 480, 880, 720, step=30)
        print("   broad(400-880,480-720) hits=%d" % r2['hits'])

        # real click at predicted spot
        pg.mouse.click(600, 603); time.sleep(0.8)
        print("click(600,603): torsoP=%s verdict=%r" % (torso_p_mpa(pg), diag(pg)['verdict']))
        r3 = scan(pg, 520, 520, 680, 690)
        print("   post-click lower-mid hits=%d" % r3['hits'])

        # if still nothing, click a vertical column at x=600 across y to find hit
        for yy in [540, 560, 580, 600, 620, 640, 660]:
            pg.mouse.click(600, yy); time.sleep(0.35)
            tp = torso_p_mpa(pg)
            print("   click(600,%d): torsoP=%s" % (yy, tp))
            if tp and tp >= 0.02:
                print("   *** PRESS LANDED at y=%d ***" % yy)
                break

        pg.screenshot(path="07_spot_probe.png")
        print("page_errors=%d" % len(errs))
        for e in errs:
            print("   ", e)
        ctx.close()


main()
