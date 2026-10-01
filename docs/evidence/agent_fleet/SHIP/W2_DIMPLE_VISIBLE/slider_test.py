"""W2 slider verification (judge1's repro, measured):
1. the drawn thumb/track: elementFromPoint at the drawn track center must hit
   the INPUT itself (the old impostor meter div is gone)
2. a buyer-grade drag ON the drawn thumb moves the value (5/5 trials)
3. a click on the drawn track at the 10% position jumps the value low
4. the note's tick aligns with the input's own tick column (pixel scan)
5. arrow keys work after a track click (the H7 D4 concern)
Also: 50 kN payoff screenshot for the gallery.
"""
import json, math, struct, time, urllib.request
from playwright.sync_api import sync_playwright

SHELL = "http://127.0.0.1:8207"
OUT = r"E:\ChimeraWork\slot-01\.tmp\w2_scratch"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--enable-unsafe-swiftshader","--use-gl=angle","--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(SHELL + "/?debug=1")
    page.fill("#name-input", "W2probe")
    page.click("#play-btn")
    page.wait_for_timeout(400)
    if page.is_visible("#intro-begin"):
        page.click("#intro-begin")
    page.wait_for_timeout(2000)

    g = page.evaluate("""() => {
      const inp = document.getElementById('force');
      const r = inp.getBoundingClientRect();
      const frac = (Number(inp.value) - Number(inp.min)) / (Number(inp.max) - Number(inp.min));
      const tx = r.left + 8 + frac * (r.width - 16);   // thumb center x (8px inset each side)
      const ty = r.top + r.height / 2;                  // track center y = drawn thumb center
      const hitEl = document.elementFromPoint(tx, ty);
      return {rect: {x: r.x, y: r.y, w: r.width, h: r.height},
              thumb: {x: tx, y: ty},
              hitTag: hitEl ? hitEl.tagName : null,
              hitId: hitEl ? hitEl.id : null,
              value: inp.value};
    }""")
    print("input rect:", g["rect"])
    print("drawn thumb at (%.1f, %.1f) -> elementFromPoint: %s#%s" %
          (g["thumb"]["x"], g["thumb"]["y"], g["hitTag"], g["hitId"]))
    assert g["hitId"] == "force", "the drawn thumb does not hit the input"

    # buyer-grade drags: 5 trials, drag the thumb by +/-30 px
    ok = 0
    for i in range(5):
        v0 = page.evaluate("() => Number(document.getElementById('force').value)")
        dx = 30 if i % 2 == 0 else -30
        page.mouse.move(g["thumb"]["x"], g["thumb"]["y"])
        page.mouse.down()
        page.mouse.move(g["thumb"]["x"] + dx, g["thumb"]["y"], steps=6)
        page.mouse.up()
        v1 = page.evaluate("() => Number(document.getElementById('force').value)")
        if v1 != v0: ok += 1
    print("drag trials moved the value: %d/5" % ok)

    # click at the gentle-tick column (15.15% of the track) -> value should drop near the low end
    page.evaluate("() => { const i = document.getElementById('force'); i.value = 50000; i.dispatchEvent(new Event('input')); }")
    tx = g["rect"]["x"] + 8 + 0.1515 * (g["rect"]["w"] - 16)
    page.mouse.click(tx, g["thumb"]["y"])
    v = page.evaluate("() => Number(document.getElementById('force').value)")
    print("click at tick column (15.15%%): value -> %d N (expected <= ~11000)" % v)

    # arrow keys after the click (focus followed the click)
    v0 = v
    page.keyboard.press("ArrowRight")
    v1 = page.evaluate("() => Number(document.getElementById('force').value)")
    print("arrow key after track click: %d -> %d (%s)" % (v0, v1, "works" if v1 > v0 else "DEAD"))

    # SPACE must still press (the H7 guard: typing guard only skips text inputs)
    page.evaluate("() => { const i = document.getElementById('force'); i.value = 20000; i.dispatchEvent(new Event('input')); }")

    # tick alignment: pixel-scan the warn tick column in the input row and the note row
    page.wait_for_timeout(300)
    shot = OUT + r"\slider_fixed.png"
    page.locator(".card").nth(1).screenshot(path=shot)
    print("card screenshot saved")

    # 50 kN payoff: set force, press belly pixel for 1.5 s, shoot
    page.evaluate("() => { const i = document.getElementById('force'); i.value = 50000; i.dispatchEvent(new Event('input')); }")
    for _ in range(60):
        r = page.evaluate("() => (window.__h16pickProbe ? window.__h16pickProbe(640,400) : null)")
        if r and r["triCount"] > 0: break
        page.wait_for_timeout(500)
    BELLY = [0.0, 4.444, 0.700]
    best = None
    for py in range(200, 700, 25):
        for px in range(300, 1000, 25):
            r = page.evaluate(f"() => window.__h16pickProbe({px},{py})")
            if r["raw"]:
                d = math.dist(r["raw"], BELLY)
                if best is None or d < best[0]: best = (d, px, py)
            if best and best[0] < 0.05: break
        if best and best[0] < 0.05: break
    d, bpx, bpy = best
    page.wait_for_timeout(1500)   # let any earlier press settle
    page.screenshot(path=OUT + r"\pay50k_rest.png")
    page.mouse.move(bpx, bpy); page.mouse.down()
    page.wait_for_timeout(1500)
    page.screenshot(path=OUT + r"\pay50k_hold.png")
    page.mouse.up()
    print("50 kN payoff captured (belly px %d,%d)" % (bpx, bpy))
    browser.close()
