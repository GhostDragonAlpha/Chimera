"""W2 e2e probe: press the creature in a headless browser and measure the dent
at every link of the chain:
  server  — GET /api/verts (legacy framing) through the shell during the hold
  page    — window.__h16pickProbe(bellyPx).raw at rest vs during the hold
            (raw = first-hit world point of the page's own raycast against
            RG.verts: it moves iff the page's buffer carries the dent)
  pixels  — before/during/after PNGs of the same camera
"""
import json, math, struct, sys, time, urllib.request
from playwright.sync_api import sync_playwright

SHELL = "http://127.0.0.1:8207"
OUT = r"E:\ChimeraWork\slot-01\.tmp\w2_scratch"

def shell_verts():
    with urllib.request.urlopen(SHELL + "/api/verts", timeout=10) as r:
        return r.read()

def probe_dent(buf, hit_idx, base_at):
    n = struct.unpack("<I", buf[:4])[0]
    f = struct.unpack("<" + "f" * (n * 9), buf[4:4 + n * 36])
    return math.dist(f[hit_idx*9:hit_idx*9+3], base_at), n

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(SHELL + "/?debug=1")
    page.fill("#name-input", "W2probe")
    page.click("#play-btn")
    page.wait_for_timeout(500)
    if page.is_visible("#intro-begin"):
        page.click("#intro-begin")
    # wait for the mesh stream to land
    for _ in range(40):
        ready = page.evaluate("() => (window.__h16pickProbe ? 1 : 0)")
        if ready:
            r = page.evaluate("() => window.__h16pickProbe(640,400)")
            if r["triCount"] > 0 and r["vertCount"] > 0:
                break
        page.wait_for_timeout(250)
    print("mesh ready: triCount=%d vertCount=%d" % (r["triCount"], r["vertCount"]))

    # find the belly pixel: scan the canvas for a pick near world [0,4.444,0.700]
    BELLY = [0.0, 4.444, 0.700]
    best = None
    for py in range(200, 700, 25):
        for px in range(300, 1000, 25):
            r = page.evaluate(f"() => window.__h16pickProbe({px},{py})")
            if r["raw"]:
                d = math.dist(r["raw"], BELLY)
                if best is None or d < best[0]:
                    best = (d, px, py, r["raw"])
            if best and best[0] < 0.05:
                break
        if best and best[0] < 0.05:
            break
    d, bpx, bpy, raw = best
    print(f"belly pixel: ({bpx},{bpy}) raw=({raw[0]:.3f},{raw[1]:.3f},{raw[2]:.3f}) d={d:.3f} m")

    # index of the hit vertex server-side for the shell-side dent measure
    buf = shell_verts()
    n = struct.unpack("<I", buf[:4])[0]
    f = struct.unpack("<" + "f" * (n * 9), buf[4:4 + n * 36])
    hit_idx, bd = -1, 1e30
    for i in range(n):
        dx = f[i*9]-raw[0]; dy = f[i*9+1]-raw[1]; dz = f[i*9+2]-raw[2]
        d2 = dx*dx+dy*dy+dz*dz
        if d2 < bd: bd, hit_idx = d2, i
    base_at = f[hit_idx*9:hit_idx*9+3]
    print(f"server hit vert idx={hit_idx} d={bd**0.5:.4f} m")

    r0 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    page.screenshot(path=OUT + r"\before.png")
    sv0, _ = probe_dent(shell_verts(), hit_idx, base_at)
    print(f"REST:   server dent={sv0:.4f} m  page raw=({r0['raw'][0]:.3f},{r0['raw'][1]:.3f},{r0['raw'][2]:.3f}) sum1={r0['sum1']:.1f}")

    # THE PRESS: pointer down, hold 2 s
    page.mouse.move(bpx, bpy)
    page.mouse.down()
    page.wait_for_timeout(600)
    hand = page.text_content("#hand-state")
    sv1, _ = probe_dent(shell_verts(), hit_idx, base_at)
    r1 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    page.screenshot(path=OUT + r"\during.png")
    print(f"HOLD:   hand='{hand}' server dent={sv1:.4f} m  page raw=({r1['raw'][0]:.3f},{r1['raw'][1]:.3f},{r1['raw'][2]:.3f}) sum1={r1['sum1']:.1f}")
    page.wait_for_timeout(1400)
    sv2, _ = probe_dent(shell_verts(), hit_idx, base_at)
    r2 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    page.screenshot(path=OUT + r"\during2.png")
    print(f"HOLD2s: server dent={sv2:.4f} m  page raw=({r2['raw'][0]:.3f},{r2['raw'][1]:.3f},{r2['raw'][2]:.3f}) sum1={r2['sum1']:.1f}")
    page.mouse.up()
    page.wait_for_timeout(1500)
    sv3, _ = probe_dent(shell_verts(), hit_idx, base_at)
    r3 = page.evaluate(f"() => window.__h16pickProbe({bpx},{bpy})")
    page.screenshot(path=OUT + r"\after.png")
    print(f"AFTER:  server dent={sv3:.4f} m  page raw=({r3['raw'][0]:.3f},{r3['raw'][1]:.3f},{r3['raw'][2]:.3f}) sum1={r3['sum1']:.1f}")

    # the judge's debug line + any console errors
    print("judge line:", page.text_content("#judge-debug"))
    browser.close()
