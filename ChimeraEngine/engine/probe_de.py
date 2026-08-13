"""Track D visual-regression probe: default view renders the planet as a
white disc. Gather numbers: __lodInfo, __dbgRender, HDR texel values at
planet center / limb / off-planet, and a mip-level screenshot for contrast.
Headed, --enable-unsafe-webgpu. NOT part of test_phase6.py."""
from playwright.sync_api import sync_playwright
import os

URL = "file:///E:/PythonChimera/ChimeraEngine/engine/spiace_phase6.html"
OUT = "E:/PythonChimera/ChimeraEngine/engine"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_function(
        "document.getElementById('particle-count').textContent === '500'",
        timeout=15000)
    page.wait_for_timeout(1500)

    print("lodInfo:", page.evaluate("window.__lodInfo"))
    dbg = page.evaluate("window.__dbgRender")
    print("dbgRender: n=%s visible=%s countsTotal=%s" % (dbg["n"], dbg["visible"], dbg["countsTotal"]))
    print("starProj:", page.evaluate("window.__starProj"))

    # HDR readback: planet center (640,360), limb (640,170), off-planet (100,100)
    for (x, y, label) in [(640, 360, "planet-center"), (640, 170, "limb"), (100, 100, "off-planet")]:
        v = page.evaluate(f"window.__readHDR({x}, {y})")
        print(f"HDR {label} ({x},{y}):", v)

    page.screenshot(path=os.path.join(OUT, "probe_fracture.png"))

    # Mip-level view (N=19 law radius) for contrast
    R_PL = 6.371e6
    import math
    rpx = math.sqrt(19 / 0.35)
    dist = R_PL * 720 / (2 * rpx * 0.414)
    page.evaluate(f"window.__setCam(1.5e11 + {dist}, 0, 0)")
    page.evaluate("window.__lookAt(1.5e11, 0, 0)")
    page.wait_for_timeout(600)
    print("lodInfo @mip19:", page.evaluate("window.__lodInfo"))
    v = page.evaluate("window.__readHDR(640, 360)")
    print("HDR mip-center:", v)
    page.screenshot(path=os.path.join(OUT, "probe_mip.png"))

    # Base view (N=300 law radius)
    rpx = math.sqrt(300 / 0.35)
    dist = R_PL * 720 / (2 * rpx * 0.414)
    page.evaluate(f"window.__setCam(1.5e11 + {dist}, 0, 0)")
    page.evaluate("window.__lookAt(1.5e11, 0, 0)")
    page.wait_for_timeout(600)
    print("lodInfo @base300:", page.evaluate("window.__lodInfo"))
    v = page.evaluate("window.__readHDR(640, 360)")
    print("HDR base-center:", v)
    page.screenshot(path=os.path.join(OUT, "probe_base.png"))

    if errs:
        print("PAGE ERRORS:", errs)
    browser.close()
