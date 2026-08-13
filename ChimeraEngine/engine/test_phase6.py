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
10. Track B: scale-relative flight — walk pace near planet, orbital pace
    in void, speed always within [1 m/s, 10x local escape velocity]
    (B falsifier); membrane depth/path/clock reported per position
11. B4: F-focus flies the camera to framing distance (derived from the
    target's render radius) and Escape releases it
12. Track T: LOD-of-time toggle works; witness falsifier — LOD-gated
    positions within 1% of full-rate over 60 frames
13. Screenshots at start and end; console collected; no page errors

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

        # ---- 5b. FALSIFIER: derived sea level yields Earth-like land fraction ----
        # spawnPlanet() derives the sea threshold at the area-weighted
        # (1 - 0.291) quantile of the normalized noise potential. The 300
        # Fibonacci splats sample correlated continents, so allow |lf-0.291|
        # < 0.12 (measured 0.203 deterministically). The old hardcoded
        # threshold measured 0.000 — 100% abyssal, the "blue wash".
        terra = page.evaluate("window.__terrainStats")
        print(f"Terrain: land fraction {terra['landFraction']:.3f} "
              f"(target {terra['target']}, seaThr {terra['seaThr']:.3f})")
        assert abs(terra["landFraction"] - terra["target"]) < 0.12, \
            f"LAND FRACTION FALSIFIER TRIPPED: {terra['landFraction']:.3f} vs " \
            f"target {terra['target']} — sea level derivation broken"

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

        # ---- Track B: scale-relative flight camera ----
        # B falsifier bounds: speed <= 10x local escape velocity, and
        # speed >= 1 m/s near a surface. Verified at two scales.
        page.wait_for_function("window.__flightInfo !== undefined", timeout=10000)

        # Near the planet (1 radius above surface): walk-pace speed
        # (planet membrane orbits at 1 AU = 1.5e11 m from the star)
        page.evaluate("window.__setCam(1.5e11, 2 * 6.371e6, 0)")
        page.wait_for_timeout(200)
        fl_planet = page.evaluate("window.__flightInfo")
        print(f"Flight @planet: depth={fl_planet['depth']} path={fl_planet['path']} "
              f"alt={fl_planet['alt']:.3e} m speed={fl_planet['speed']:.1f} m/s "
              f"clock={fl_planet['clock']:.2f} vesc={fl_planet['vesc']:.0f} m/s")
        assert fl_planet["depth"] == 1, f"expected planet membrane depth 1, got {fl_planet['depth']}"
        assert "planet" in fl_planet["path"]
        assert fl_planet["speed"] >= 1.0, "B FALSIFIER: speed below 1 m/s near a surface"
        assert fl_planet["speed"] <= 10 * fl_planet["vesc"] * 1.001, \
            "B FALSIFIER: speed exceeds 10x local escape velocity"
        assert 10 < fl_planet["speed"] < 2000, \
            f"walk-pace expectation broken: {fl_planet['speed']} m/s at 1 radius altitude"

        # Deep void: orbital-pace speed, system clock ~0.43
        page.evaluate("window.__setCam(2e11, 0, 5e10)")
        page.wait_for_timeout(200)
        fl_void = page.evaluate("window.__flightInfo")
        print(f"Flight @void:   depth={fl_void['depth']} path={fl_void['path']} "
              f"alt={fl_void['alt']:.3e} m speed={fl_void['speed']:.3e} m/s "
              f"clock={fl_void['clock']:.2f} vesc={fl_void['vesc']:.0f} m/s")
        assert fl_void["depth"] == 0, f"expected system void depth 0, got {fl_void['depth']}"
        assert fl_void["speed"] > fl_planet["speed"] * 10, \
            "scale-relative speed broken: void not much faster than planet surface"
        assert fl_void["speed"] <= 10 * fl_void["vesc"] * 1.001, \
            "B FALSIFIER: void speed exceeds 10x local escape velocity"
        assert 0.3 < fl_void["clock"] < 0.6, \
            f"system membrane clock should be ~0.43, got {fl_void['clock']}"

        # ---- B4: focus/frame flight ----
        page.evaluate("window.__focusOn(5)")  # a terrain splat
        page.wait_for_timeout(3500)
        focus_txt = text(page, "#fly-focus")
        assert focus_txt == "#5", f"focus HUD shows {focus_txt!r}, expected '#5'"
        dist = page.evaluate(
            "(() => { const p = window.__flightInfo.camPos; "
            " return Math.hypot(p[0] - 1.5e11, p[1], p[2]); })()")
        # terrain splat 5 sits on the planet (at 1 AU); frameDist = radius*5 = 6.4e6 m
        # plus the particle's surface offset — assert we framed, not void/overshot
        print(f"Focus flight: camera at {dist:.3e} m from planet center (frame dist ~6.4e6 m target)")
        assert dist < 1.2e8, f"focus flight did not converge (dist {dist:.3e} m)"
        assert dist > 1e6, f"focus flight overshot into the planet (dist {dist:.3e} m)"
        page.keyboard.press("Escape")  # release focus
        page.wait_for_timeout(300)
        assert text(page, "#fly-focus") == "none (F)", \
            f"focus not released by Escape: {text(page, '#fly-focus')!r}"
        page.click("#btn-center")
        page.wait_for_timeout(200)

        # ---- Track T: LOD of time ----
        # Toggle on: button + HUD respond, frames keep advancing, no errors
        page.click("#btn-lod")
        assert text(page, "#btn-lod") == "LOD Time: on"
        f0 = page.evaluate("window.__frames || 0")
        page.wait_for_timeout(400)
        f1 = page.evaluate("window.__frames || 0")
        assert f1 > f0, "frames stalled with LOD time on"
        assert err_visible(page) is None
        page.click("#btn-lod")
        assert text(page, "#btn-lod") == "LOD Time: off"
        print("LOD time toggle OK")

        # T FALSIFIER: LOD-gated positions within 1% of full-rate over 60 frames
        wit = page.evaluate("window.__lodWitness()")
        print(f"LOD witness: {wit['systemTicks']}/{wit['frames']} system ticks "
              f"(clock {wit['clockRate']:.2f}), max divergence {wit['divergence']:.3e} m "
              f"= {wit['relDivergence']*100:.4f}% at particle #{wit['index']}")
        assert 0 < wit["systemTicks"] < wit["frames"], \
            "LOD gating never fired — witness measured nothing"
        assert wit["relDivergence"] < 0.01, \
            f"T FALSIFIER TRIPPED: LOD divergence {wit['relDivergence']*100:.3f}% >= 1%"

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

        # ---- Canvas is not black (regression: the system-scale near-cull
        # culled every splat at planetary altitude and NO assertion noticed) ----
        vis = page.evaluate("window.__dbgRender && window.__dbgRender.visible")
        assert vis and vis > 0, "0 visible splats — canvas would be black"
        print(f"Visible splats: {vis}")

        # ---- Final screenshot ----
        page.screenshot(path=SCREENSHOT_FINAL, full_page=False)
        assert os.path.exists(SCREENSHOT_FINAL), "Final screenshot not saved"
        print(f"Screenshot saved: {SCREENSHOT_FINAL}")

        # ---- 10. Console + page errors ----
        print("\n--- browser console ---")
        for m in console_msgs[:50]:
            print(" ", m.encode("ascii", "replace").decode())  # cp1252-safe
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
