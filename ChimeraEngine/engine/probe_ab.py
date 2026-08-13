"""Track D A/B probe: at the DEFAULT camera, force LOD mode base / mip:1 /
fracture and screenshot each + HDR center readback. Decides whether the
white-out is fracture-specific or inherited. Headed, --enable-unsafe-webgpu.
NOT part of test_phase6.py."""
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

    for mode in ["base", "mip:1", "fracture"]:
        page.evaluate(f"window.__lodForce = '{mode}'")
        page.wait_for_timeout(400)
        info = page.evaluate("window.__lodInfo")
        hdr = page.evaluate("window.__readHDR(640, 360)")
        hdr_limb = page.evaluate("window.__readHDR(640, 175)")
        print(f"{mode}: lodInfo={info}")
        print(f"  HDR center={hdr['hdrPixel']}  limb={hdr_limb['hdrPixel']}")
        page.screenshot(path=os.path.join(OUT, f"probe_ab_{mode.replace(':', '')}.png"))

    page.evaluate("window.__lodForce = null")
    if errs:
        print("PAGE ERRORS:", errs)
    browser.close()
