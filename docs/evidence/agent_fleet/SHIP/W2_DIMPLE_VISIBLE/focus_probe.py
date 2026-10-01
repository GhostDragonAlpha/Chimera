"""Focused probe: where exactly are the changed pixels, and does the page
buffer track the server export at every step (rest/hold/+2s/+7s)?"""
import json, math, struct, time, urllib.request
from playwright.sync_api import sync_playwright

SHELL = "http://127.0.0.1:8207"
OUT = r"E:\ChimeraWork\slot-01\.tmp\w2_scratch"

def shell_verts():
    with urllib.request.urlopen(SHELL + "/api/verts", timeout=10) as r:
        return r.read()

def w2_checksum(buf):
    n = struct.unpack("<I", buf[:4])[0]
    f = struct.unpack("<" + "f" * (n * 9), buf[4:4 + n * 36])
    s = 0.0
    for i in range(0, n * 9, 3):
        s += f[i] + f[i + 1] + f[i + 2]
    return s, n, f

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--enable-unsafe-swiftshader","--use-gl=angle","--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(SHELL + "/?debug=1")
    page.fill("#name-input", "W2probe")
    page.click("#play-btn")
    page.wait_for_timeout(400)
    if page.is_visible("#intro-begin"):
        page.click("#intro-begin")
    for _ in range(120):
        r = page.evaluate("() => (window.__h16pickProbe ? window.__h16pickProbe(640,400) : null)")
        if r and r["triCount"] > 0:
            break
        page.wait_for_timeout(500)
    # settle guard
    prev = None
    for _ in range(60):
        s, _, _ = w2_checksum(shell_verts())
        if prev is not None and s == prev: break
        prev = s
        page.wait_for_timeout(1500)
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
    ss, n, fv = w2_checksum(shell_verts())
    pr = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    print("REST parity diff=%.4f" % abs(pr["sum1"]-ss))
    page.screenshot(path=OUT + r"\g_rest.png")

    page.mouse.move(bpx, bpy); page.mouse.down()
    page.wait_for_timeout(1500)
    ss2, _, _ = w2_checksum(shell_verts())
    pr2 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    print("HOLD parity diff=%.4f" % abs(pr2["sum1"]-ss2))
    page.screenshot(path=OUT + r"\g_hold.png")
    page.mouse.up()
    page.wait_for_timeout(2000)
    ss3, _, _ = w2_checksum(shell_verts())
    pr3 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    print("+2s   parity diff=%.4f" % abs(pr3["sum1"]-ss3))
    page.screenshot(path=OUT + r"\g_2s.png")
    page.wait_for_timeout(5000)
    ss4, _, _ = w2_checksum(shell_verts())
    pr4 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    print("+7s   parity diff=%.4f" % abs(pr4["sum1"]-ss4))
    page.screenshot(path=OUT + r"\g_7s.png")
    # buffer drift vs REST checksum (page-side and server-side)
    pr5 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    print("REST sum1=%.4f  final page sum1=%.4f  final server sum1=%.4f" % (pr["sum1"], pr5["sum1"], ss4))
    browser.close()
