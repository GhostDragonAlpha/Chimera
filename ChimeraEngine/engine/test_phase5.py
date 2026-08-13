"""
SPIACE Phase 5 — GPU Barnes-Hut N-Body Playwright Test (headed mode)

Tests:
1. Page loads; particle count shows exactly 500 (polled, not fixed-slept)
2. Tree stats populate in CPU mode (nodes, leaves, depth > 0)
3. Energy drift < 5% over 60 frames in CPU mode (FALSIFIER 1)
3b. Light/heat in the tree: the 1 AU temperature bin holds its
    radiative equilibrium within 15% (FALSIFIER 2); membrane panel
    reports contained light (W) and heat (J)
4. All three mode buttons switch correctly (active class, no #err,
   gravity ms updates); GPU mode skipped gracefully if WebGPU unavailable
5. Renderer is WebGPU: window.__renderer === 'webgpu-splat' and the main
   canvas refuses a 2d context (a canvas with a webgpu context returns null)
6. Screenshots at start and end
7. Browser console collected; fails on uncaught page errors

Falsifier: If energy drift exceeds 5% over 60 frames in CPU mode,
the Barnes-Hut implementation has a bug (either tree construction
or traversal).

Run:  python test_phase5.py        (plain script, asserts)
  or: pytest test_phase5.py        (pytest-compatible)
"""

from playwright.sync_api import sync_playwright
import os

PHASE_URL = "file:///E:/PythonChimera/ChimeraEngine/engine/spiace_phase5.html"
ENGINE_DIR = "E:/PythonChimera/ChimeraEngine/engine"
SCREENSHOT_START = os.path.join(ENGINE_DIR, "spiace_phase5_screenshot.png")
SCREENSHOT_FINAL = os.path.join(ENGINE_DIR, "spiace_phase5_final.png")


def text(page, sel):
    return page.locator(sel).text_content()


def err_visible(page):
    return page.evaluate(
        "(() => { const e = document.getElementById('err');"
        " return e && e.style.display === 'block' ? e.textContent : null; })()")


def test_spiace_phase5_barnes_hut():
    console_msgs = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.on("console", lambda m: console_msgs.append(f"[{m.type}] {m.text}"))
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        # ---- Load page ----
        print("Loading Phase 5...")
        page.goto(PHASE_URL)

        # ---- 1. Particle count shows 500 on load (poll) ----
        page.wait_for_function(
            "document.getElementById('particle-count').textContent === '500'",
            timeout=15000)
        assert text(page, "#particle-count") == "500"
        assert text(page, "#stat-n") == "500"
        print("Particle count: 500 OK")

        # ---- Start screenshot ----
        page.screenshot(path=SCREENSHOT_START, full_page=False)
        assert os.path.exists(SCREENSHOT_START), "Start screenshot not saved"
        print(f"Screenshot saved: {SCREENSHOT_START}")

        # ---- 2. Tree stats populate in CPU mode ----
        page.wait_for_function(
            "parseInt(document.getElementById('stat-nodes').textContent) > 0",
            timeout=10000)
        nodes = int(text(page, "#stat-nodes").split()[0])
        leaves = int(text(page, "#stat-leaves"))
        depth = int(text(page, "#stat-depth"))
        print(f"Tree: {nodes} nodes, {leaves} leaves, depth {depth}")
        assert nodes > 0 and leaves > 0 and depth > 0, "Tree stats not populated"

        # ---- 3. Energy drift < 5% over 60 frames (CPU mode, falsifier) ----
        page.wait_for_function(
            "document.getElementById('stat-energy').textContent.endsWith('%')",
            timeout=30000)
        energy_text = text(page, "#stat-energy")
        drift = float(energy_text.replace("%", ""))
        print(f"Energy drift over 60 frames (CPU BH): {drift}%")
        assert drift < 5.0, f"FALSIFIER TRIPPED: energy drift {drift}% >= 5%"

        # ---- 3b. Light/heat in the tree: radiative equilibrium holds ----
        # FALSIFIER 2: particles were initialized at T_eq from analytic
        # starlight; if the BH tree's light transport were wrong, the
        # delivered flux would walk the 1 AU bin off equilibrium.
        page.wait_for_function(
            "window.__thermal && window.__thermal.count > 0",
            timeout=15000)
        thermal = page.evaluate("window.__thermal")
        rel_err = abs(thermal["meanT"] - thermal["predicted"]) / thermal["predicted"]
        print(f"Thermal: mean T @1AU = {thermal['meanT']:.1f} K over "
              f"{thermal['count']} bodies (predicted {thermal['predicted']:.1f} K, "
              f"rel err {rel_err*100:.1f}%)")
        assert rel_err < 0.15, \
            f"FALSIFIER 2 TRIPPED: 1AU bin mean T {thermal['meanT']:.1f} K vs " \
            f"predicted {thermal['predicted']:.1f} K ({rel_err*100:.1f}% off) — " \
            f"the tree's light transport is wrong"
        mem_light = text(page, "#mem-light")
        mem_heat = text(page, "#mem-heat")
        assert mem_light.endswith("W") and "--" not in mem_light, f"mem-light wrong: {mem_light}"
        assert mem_heat.endswith("J") and "--" not in mem_heat, f"mem-heat wrong: {mem_heat}"
        print(f"Membrane contains: light {mem_light}, heat {mem_heat}")

        # ---- 4a. O(n^2) direct mode ----
        page.click("#btn-direct")
        page.wait_for_timeout(500)
        assert "active" in page.locator("#btn-direct").get_attribute("class")
        assert "active" not in page.locator("#btn-cpu").get_attribute("class")
        assert text(page, "#stat-grav") != "--", "gravity ms not updating in direct mode"
        assert err_visible(page) is None, f"#err shown in direct mode: {err_visible(page)}"
        print(f"Direct O(n^2) gravity time: {text(page, '#stat-grav')}")

        # ---- 4b. Back to CPU BH ----
        page.click("#btn-cpu")
        page.wait_for_timeout(500)
        assert "active" in page.locator("#btn-cpu").get_attribute("class")
        assert text(page, "#stat-grav") != "--"
        print(f"CPU BH gravity time: {text(page, '#stat-grav')}")

        # ---- 4c. GPU BH mode (skip gracefully if WebGPU unavailable) ----
        gpu_info = text(page, "#gpu-info") or ""
        print(f"gpu-info: {gpu_info}")
        if "OK" in gpu_info:
            page.click("#btn-gpu")
            assert "active" in page.locator("#btn-gpu").get_attribute("class")
            f0 = page.evaluate("window.__frames || 0")
            page.wait_for_timeout(1500)
            f1 = page.evaluate("window.__frames || 0")
            assert f1 > f0, f"frames not advancing in GPU mode ({f0} -> {f1})"
            assert err_visible(page) is None, f"#err shown in GPU mode: {err_visible(page)}"
            page.wait_for_function(
                "document.getElementById('stat-grav').textContent !== '--'",
                timeout=10000)
            print(f"GPU BH gravity time: {text(page, '#stat-grav')} "
                  f"(frames {f0} -> {f1}, fps: {text(page, '#fps')})")
            page.click("#btn-cpu")  # back to reference mode
            page.wait_for_timeout(500)
            # GPU mode must not corrupt the CPU-side particle array:
            # the CPU tree built afterwards must be non-degenerate.
            page.wait_for_function(
                "parseInt(document.getElementById('stat-depth').textContent) > 0",
                timeout=5000)
            depth_after = int(text(page, "#stat-depth"))
            nodes_after = int(text(page, "#stat-nodes").split()[0])
            assert nodes_after > 1, \
                f"tree degenerate after GPU mode ({nodes_after} nodes) — GPU BH corrupted the CPU particle array"
            print(f"After GPU mode: tree healthy ({nodes_after} nodes, depth {depth_after})")
        else:
            print("WebGPU not available — GPU mode test skipped gracefully")

        # ---- 5. Renderer is WebGPU, not Canvas 2D ----
        renderer = page.evaluate("window.__renderer")
        assert renderer == "webgpu-splat", f"window.__renderer = {renderer!r}"
        ctx2d = page.evaluate("document.getElementById('c').getContext('2d')")
        assert ctx2d is None, "main canvas handed out a 2d context — not a WebGPU canvas"
        print("Renderer check: window.__renderer='webgpu-splat', no 2d context on #c")

        # ---- Final screenshot ----
        page.screenshot(path=SCREENSHOT_FINAL, full_page=False)
        assert os.path.exists(SCREENSHOT_FINAL), "Final screenshot not saved"
        print(f"Screenshot saved: {SCREENSHOT_FINAL}")

        # ---- 7. Console + page errors ----
        print("\n--- browser console ---")
        for m in console_msgs[:50]:
            print(" ", m)
        if len(console_msgs) > 50:
            print(f"  ... and {len(console_msgs) - 50} more")
        assert not page_errors, "Uncaught page errors:\n" + "\n".join(page_errors)
        bad_console = [m for m in console_msgs
                       if "Invalid CommandBuffer" in m or "too small" in m]
        assert not bad_console, \
            "WebGPU validation failures in console:\n" + "\n".join(bad_console[:5])

        print("\n=== All Phase 5 assertions passed! ===")
        browser.close()


if __name__ == "__main__":
    test_spiace_phase5_barnes_hut()
