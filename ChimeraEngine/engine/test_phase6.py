"""
SPIACE Phase 6 — Universal Kernel Translation + EM Playwright Test (headed)

Tests:
1. kernel_dsl.py --verify spiace_phase6.html exits 0 (the GENERATED
   regions in the HTML match the DSL declarations — no hand edits)
2. Page loads; particle count shows exactly 500 (polled, not fixed-slept)
3. Tree stats populate in CPU mode (nodes, leaves, depth > 0)
4. Tree nodes carry EM fields: charge stats report 499 charged orbitals,
   non-zero std, and the WGSL struct has the electromagnetism fields
5. FALSIFIER 1: total energy drift (KE + grav PE + EM PE) < 1% over
   60 frames in CPU BH+EM mode (two post-reset 60-frame samples)
6. FALSIFIER 2: the 1 AU temperature bin holds radiative equilibrium
   within 15% (the tree's light transport is not broken by the refactor)
7. FALSIFIER 3: a charged test particle's trajectory differs measurably
   from a neutral one (window.__deflectionCheck, delta > 10 m)
8. All three modes switch correctly (CPU BH -> CPU BH+EM -> GPU BH+EM
   -> CPU BH), active class, no #err; GPU skipped gracefully if no WebGPU
9. Renderer is WebGPU: window.__renderer === 'webgpu-splat' and the main
   canvas refuses a 2d context
10. Screenshots at start and end; console collected; no page errors

Falsifier: If combined energy drift exceeds 1% over 60 frames in CPU
BH+EM mode, the kernel-translated EM force (or its PE accounting) has
a bug.

Run:  python test_phase6.py        (plain script, asserts)
  or: pytest test_phase6.py        (pytest-compatible)
"""

from playwright.sync_api import sync_playwright
import os
import subprocess
import sys

PHASE_URL = "file:///E:/PythonChimera/ChimeraEngine/engine/spiace_phase6.html"
ENGINE_DIR = "E:/PythonChimera/ChimeraEngine/engine"
SCREENSHOT_START = os.path.join(ENGINE_DIR, "spiace_phase6_screenshot.png")
SCREENSHOT_FINAL = os.path.join(ENGINE_DIR, "spiace_phase6_final.png")


def text(page, sel):
    return page.locator(sel).text_content()


def err_visible(page):
    return page.evaluate(
        "(() => { const e = document.getElementById('err');"
        " return e && e.style.display === 'block' ? e.textContent : null; })()")


def test_kernel_dsl_regions_current():
    """The GENERATED code in the HTML matches kernel_dsl.py exactly."""
    r = subprocess.run([sys.executable, "kernel_dsl.py", "--verify", "spiace_phase6.html"],
                       cwd=ENGINE_DIR, capture_output=True, text=True)
    print(r.stdout.strip())
    assert r.returncode == 0, f"kernel_dsl --verify failed:\n{r.stdout}\n{r.stderr}"


def test_spiace_phase6_kernels():
    console_msgs = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.on("console", lambda m: console_msgs.append(f"[{m.type}] {m.text}"))
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        # ---- Load page ----
        print("Loading Phase 6...")
        page.goto(PHASE_URL)

        # ---- 2. Particle count shows 500 on load (poll) ----
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

        # ---- 3. Tree stats populate in CPU mode ----
        page.wait_for_function(
            "parseInt(document.getElementById('stat-nodes').textContent) > 0",
            timeout=10000)
        nodes = int(text(page, "#stat-nodes").split()[0])
        leaves = int(text(page, "#stat-leaves"))
        depth = int(text(page, "#stat-depth"))
        print(f"Tree: {nodes} nodes, {leaves} leaves, depth {depth}")
        assert nodes > 0 and leaves > 0 and depth > 0, "Tree stats not populated"

        # ---- 4. EM fields present: charge stats + WGSL struct ----
        page.wait_for_function("window.__charge && window.__charge.count > 0",
                               timeout=15000)
        charge = page.evaluate("window.__charge")
        print(f"Charge: {charge['count']} orbitals, mean|q|={charge['meanAbs']:.2e} C, "
              f"std={charge['std']:.2e} C, net={charge['net']:.2e} C")
        assert charge["count"] == 499, "every orbital must carry charge"
        assert charge["std"] > 0, "charge distribution is degenerate"
        wgsl = page.evaluate("document.getElementById('sh-grav-bh').textContent")
        assert "electromagnetism_c" in wgsl and "electromagnetism_q" in wgsl, \
            "WGSL TreeNode missing EM fields (kernel DSL not injected?)"
        print("WGSL TreeNode carries electromagnetism_c/_q OK")

        # ---- 6. FALSIFIER 2: thermal equilibrium still holds (CPU mode) ----
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
            f"predicted {thermal['predicted']:.1f} K"

        # ---- 5. FALSIFIER 1: combined energy drift < 1% (CPU BH+EM) ----
        # Switch to EM mode and reset: btn-reset nulls prevEnergy, so the
        # first post-reset sample is the baseline and the second is the
        # drift — both computed with EM PE included.
        page.click("#btn-cpuem")
        assert "active" in page.locator("#btn-cpuem").get_attribute("class")
        page.click("#btn-reset")
        page.wait_for_function(
            "document.getElementById('particle-count').textContent === '500'",
            timeout=15000)
        f0 = page.evaluate("window.__frames || 0")
        page.wait_for_function(
            f"(window.__frames || 0) >= {f0 + 125}", timeout=60000)
        energy = page.evaluate("window.__energy")
        drift = page.evaluate("window.__energyDrift")
        print(f"CPU BH+EM energy: KE={energy['KE']:.3e} J, "
              f"PE_grav={energy['peGravity']:.3e} J, PE_em={energy['peEM']:.3e} J, "
              f"total={energy['total']:.3e} J; drift={drift:.4f}%")
        assert energy["peEM"] != 0, "EM PE is zero in CPU BH+EM mode — EM kernel dead?"
        assert drift < 1.0, f"FALSIFIER 1 TRIPPED: combined energy drift {drift}% >= 1%"

        # ---- 7. FALSIFIER 3: charge deflects trajectories ----
        defl = page.evaluate("window.__deflectionCheck()")
        print(f"Deflection: particle #{defl['index']} (q={defl['charge']:.2e} C, "
              f"|a_EM|0={defl['aEM0']:.2e} m/s^2) charged-vs-neutral "
              f"delta = {defl['delta']:.3e} m after 2e7 s")
        assert defl["aEM0"] > 0, "no EM acceleration anywhere — EM kernel dead?"
        assert defl["delta"] > 10.0, \
            f"FALSIFIER 3 TRIPPED: charged-vs-neutral delta {defl['delta']} m <= 10 m — " \
            f"EM force does not measurably deflect trajectories"

        # ---- 8a. Back to CPU BH (gravity only) ----
        page.click("#btn-cpu")
        page.wait_for_timeout(500)
        assert "active" in page.locator("#btn-cpu").get_attribute("class")
        assert "active" not in page.locator("#btn-cpuem").get_attribute("class")
        assert text(page, "#stat-grav") != "--", "gravity ms not updating in CPU mode"
        assert err_visible(page) is None, f"#err shown in CPU mode: {err_visible(page)}"
        print(f"CPU BH gravity time: {text(page, '#stat-grav')}")

        # ---- 8b. CPU BH+EM again, then GPU BH+EM ----
        page.click("#btn-cpuem")
        page.wait_for_timeout(500)
        assert "active" in page.locator("#btn-cpuem").get_attribute("class")
        assert text(page, "#stat-grav") != "--"
        print(f"CPU BH+EM gravity time: {text(page, '#stat-grav')}")

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
            print(f"GPU BH+EM gravity time: {text(page, '#stat-grav')} "
                  f"(frames {f0} -> {f1}, fps: {text(page, '#fps')})")
            page.click("#btn-cpu")  # back to reference mode
            page.wait_for_timeout(500)
            # GPU mode must not corrupt the CPU-side particle array:
            # the CPU tree built afterwards must be non-degenerate.
            page.wait_for_function(
                "parseInt(document.getElementById('stat-depth').textContent) > 0",
                timeout=5000)
            nodes_after = int(text(page, "#stat-nodes").split()[0])
            assert nodes_after > 1, \
                f"tree degenerate after GPU mode ({nodes_after} nodes)"
            print(f"After GPU mode: tree healthy ({nodes_after} nodes)")
        else:
            print("WebGPU not available — GPU mode test skipped gracefully")

        # ---- 9. Renderer is WebGPU, not Canvas 2D ----
        renderer = page.evaluate("window.__renderer")
        assert renderer == "webgpu-splat", f"window.__renderer = {renderer!r}"
        ctx2d = page.evaluate("document.getElementById('c').getContext('2d')")
        assert ctx2d is None, "main canvas handed out a 2d context — not a WebGPU canvas"
        print("Renderer check: window.__renderer='webgpu-splat', no 2d context on #c")

        # ---- Final screenshot ----
        page.screenshot(path=SCREENSHOT_FINAL, full_page=False)
        assert os.path.exists(SCREENSHOT_FINAL), "Final screenshot not saved"
        print(f"Screenshot saved: {SCREENSHOT_FINAL}")

        # ---- 10. Console + page errors ----
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

        print("\n=== All Phase 6 assertions passed! ===")
        browser.close()


if __name__ == "__main__":
    test_kernel_dsl_regions_current()
    test_spiace_phase6_kernels()
