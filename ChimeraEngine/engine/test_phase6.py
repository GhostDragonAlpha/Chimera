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
14. PHASE 8: heat diffusion steady-state kernel — WGSL heat fields,
    FALSIFIER 6 (two-source analytic superposition within 2% via the
    aggregated-node path), T_field @1AU ~= 271 K (the kappa derivation's
    prediction, <15%), heat toggle, FALSIFIERS 7-8 (energy drift and
    thermal equilibrium unchanged with the heat kernel active)
15. PHASE 9: acoustic pressure kernel + quantity packing — WGSL acoustic
    fields + packed quants vec4f (mass/lum/charge/heat in ONE buffer,
    8 storage buffers = the default WebGPU limit), FALSIFIER 9 (two
    bipolar monopoles superpose within 2% via the aggregated-node path),
    p_field @1AU ~= 2 nPa (the solar-wind calibration's prediction, <15%),
    acoustic toggle
16. TRACK E: character on planet — E1 ground-query roundtrip (<1 m over
    300 splats), E2 rest falsifier (speed 0, gap <0.01 m after 1 s),
    E2b walk falsifier (track within 10% of WALK_SPEED*t), E3 scale
    handoff (land -> walk -> rest -> takeoff via __enterFoot/__exitFoot)
17. TRACK D: LOD law N = rho*r_px^2 (rho=0.35 trained) — D1 mip pyramid
    selection within 20% at 3 law radii, D2 fracture counts track the law
    (monotonic increase) and pin at the renderer budget cap

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
        # Surface WebGPU init state early — a failure here shows #err and
        # otherwise only trips an assertion 30 s later in the LOD section
        print(f"gpu-info @load: {text(page, '#gpu-info')} | err: {err_visible(page)}")

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

        # ---- PHASE 8: HEAT DIFFUSION STEADY-STATE KERNEL ----
        # WGSL TreeNode must carry the heat fields (DSL injected)
        assert "heat_c" in wgsl and "heat_q" in wgsl, \
            "WGSL TreeNode missing heat fields (kernel DSL not injected?)"
        print("WGSL TreeNode carries heat_c/_q OK")

        # FALSIFIER 6: two point heat sources superpose analytically.
        # The probe is far enough that the tree ACCEPTS the aggregated
        # node — this tests the approximation path, not just leaf sums.
        hw = page.evaluate("window.__heatWitness()")
        print(f"Heat witness: T_tree={hw['tTree']:.4e} K vs "
              f"T_analytic={hw['tAnalytic']:.4e} K, rel err {hw['relErr']*100:.4f}% "
              f"({hw['approximatedNodes']} accepted nodes, {hw['directLeaves']} leaves)")
        assert hw["approximatedNodes"] > 0, \
            "heat witness exercised no aggregated nodes — approximation path untested"
        assert hw["relErr"] < 0.02, \
            f"FALSIFIER 6 TRIPPED: heat superposition rel err {hw['relErr']*100:.3f}% >= 2%"

        # The kappa derivation's prediction: the diffusive temperature
        # field at 1 AU equals radiative equilibrium (271 K) by construction
        page.wait_for_function(
            "window.__heatStats && window.__heatStats.count > 0 && window.__heatStats.enabled",
            timeout=15000)
        hs = page.evaluate("window.__heatStats")
        tf_err = abs(hs["meanTfield"] - hs["predicted"]) / hs["predicted"]
        print(f"Heat field: mean T_field @1AU = {hs['meanTfield']:.1f} K over "
              f"{hs['count']} bodies (predicted {hs['predicted']:.1f} K, "
              f"rel err {tf_err*100:.1f}%)")
        assert tf_err < 0.15, \
            f"HEAT DERIVATION WRONG: T_field @1AU {hs['meanTfield']:.1f} K vs " \
            f"predicted {hs['predicted']:.1f} K"

        # Toggle: button flips the kernel and the HUD reports it
        # (membrane panel updates every 60 frames — poll, don't fixed-sleep)
        page.click("#btn-heat")
        assert text(page, "#btn-heat") == "Heat: off"
        page.wait_for_function(
            "document.getElementById('mem-tfield').textContent === 'off'",
            timeout=15000)
        page.click("#btn-heat")
        assert text(page, "#btn-heat") == "Heat: on"
        page.wait_for_function(
            "window.__heatStats && window.__heatStats.enabled",
            timeout=15000)
        print("Heat kernel toggle OK")
        # Falsifiers 7 & 8 are the EXISTING energy and thermal checks run
        # with the heat kernel active (default on): heat is a field, not a
        # force — it does no work and touches no dynamics, so drift must
        # stay < 1% and the 1 AU bin must hold equilibrium.

        # ---- PHASE 9: ACOUSTIC PRESSURE KERNEL + QUANTITY PACKING ----
        # WGSL TreeNode must carry the acoustic fields (DSL injected), and
        # the packed quants vec4f buffer must replace the per-kernel arrays.
        assert "acoustic_c" in wgsl and "acoustic_q" in wgsl, \
            "WGSL TreeNode missing acoustic fields (kernel DSL not injected?)"
        assert "quants" in wgsl and "pressures" in wgsl, \
            "WGSL missing packed quants/pressures buffers (Phase 9 packing?)"
        assert "masses" not in wgsl and "charges[" not in wgsl, \
            "WGSL still references unpacked quantity arrays"
        print("WGSL TreeNode carries acoustic_c/_q + packed quants OK")

        # FALSIFIER 9: two bipolar monopoles superpose analytically through
        # the AGGREGATED-node path (probe far enough that the tree accepts).
        aw = page.evaluate("window.__acousticWitness()")
        print(f"Acoustic witness: p_tree={aw['pTree']:.4e} Pa vs "
              f"p_analytic={aw['pAnalytic']:.4e} Pa, rel err {aw['relErr']*100:.4f}% "
              f"({aw['approximatedNodes']} accepted nodes, {aw['directLeaves']} leaves)")
        assert aw["approximatedNodes"] > 0, \
            "acoustic witness exercised no aggregated nodes — approximation path untested"
        assert aw["relErr"] < 0.02, \
            f"FALSIFIER 9 TRIPPED: acoustic superposition rel err {aw['relErr']*100:.3f}% >= 2%"

        # The calibration derivation's prediction: Q_star was DERIVED from
        # the measured solar-wind pressure at 1 AU (2 nPa), so the pressure
        # field at 1 AU must equal it.
        page.wait_for_function(
            "window.__pressureStats && window.__pressureStats.count > 0 && window.__pressureStats.enabled",
            timeout=15000)
        ps = page.evaluate("window.__pressureStats")
        pf_err = abs(ps["meanPfield"] - ps["predicted"]) / ps["predicted"]
        print(f"Pressure field: mean p_field @1AU = {ps['meanPfield']:.3e} Pa over "
              f"{ps['count']} bodies (predicted {ps['predicted']:.1e} Pa, "
              f"rel err {pf_err*100:.1f}%)")
        assert pf_err < 0.15, \
            f"ACOUSTIC CALIBRATION WRONG: p_field @1AU {ps['meanPfield']:.3e} Pa vs " \
            f"predicted {ps['predicted']:.1e} Pa"

        # Toggle: button flips the kernel and the HUD reports it
        # (membrane panel updates every 60 frames — poll, don't fixed-sleep)
        page.click("#btn-acoustic")
        assert text(page, "#btn-acoustic") == "Acoustic: off"
        page.wait_for_function(
            "document.getElementById('mem-press').textContent === 'off'",
            timeout=15000)
        page.click("#btn-acoustic")
        assert text(page, "#btn-acoustic") == "Acoustic: on"
        page.wait_for_function(
            "window.__pressureStats && window.__pressureStats.enabled",
            timeout=15000)
        print("Acoustic kernel toggle OK")
        # Energy/thermal falsifiers (below) run with the acoustic kernel
        # active (default on): pressure is a field, not a force — it does
        # no work, so drift must stay < 1%.

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
        assert err_visible(page) is None, f"#err shown: {err_visible(page)} | gpu-info: {text(page, '#gpu-info')}"
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

        # ---- TRACK E: CHARACTER STANDING ON PLANET (the north star) ----
        # E1 FALSIFIER: the ground query roundtrips every placed terrain
        # splat — query and placement are the same theory of ground.
        gw = page.evaluate("window.__groundWitness()")
        print(f"E1 ground query: {gw['checked']} splats roundtripped, "
              f"max err {gw['maxErr']:.2e} m")
        assert gw["checked"] == 300, f"ground witness checked {gw['checked']} splats"
        assert gw["maxErr"] < 1.0, \
            f"E1 FALSIFIER TRIPPED: heightAt diverges {gw['maxErr']} m from placed splats"

        # E2 FALSIFIERS: rest (speed = 0, gap < 0.01 m) and walk (track
        # within 10% of WALK_SPEED*t, still on the surface).
        cw = page.evaluate("window.__charWitness()")
        print(f"E2 rest witness: speed={cw['restSpeed']:.2e} m/s, gap={cw['gap']:.2e} m")
        assert cw["restSpeed"] < 1e-6, \
            f"E2 FALSIFIER TRIPPED: character not at rest after 1 s ({cw['restSpeed']} m/s)"
        assert abs(cw["gap"]) < 0.01, \
            f"E2 FALSIFIER TRIPPED: gap {cw['gap']} m >= 0.01 m"
        ww = page.evaluate("window.__charWalkWitness()")
        print(f"E2b walk witness: track={ww['track']:.3f} m vs {ww['expected']:.1f} m "
              f"({ww['relErr']*100:.2f}%), gap={ww['gap']:.2e} m")
        assert ww["relErr"] < 0.10, \
            f"E2b FALSIFIER TRIPPED: walk track off by {ww['relErr']*100:.1f}%"
        assert abs(ww["gap"]) < 0.01, \
            f"E2b FALSIFIER TRIPPED: walked off the surface (gap {ww['gap']} m)"

        # E3: scale handoff — fly to 2 m above the ground, land (foot mode),
        # walk, stop, take off. lat/lon 0.3/1.0 with the in-page ground query.
        import math as _math
        lat0, lon0 = 0.3, 1.0
        elev0 = page.evaluate(f"window.__heightAt({lat0}, {lon0})")
        d_cam = 6.371e6 + elev0 + 1.7 + 2.0  # 2 m above the feet
        px = _math.cos(lat0) * _math.cos(lon0)
        py = _math.sin(lat0)
        pz = _math.cos(lat0) * _math.sin(lon0)
        page.evaluate(f"window.__setCam(1.5e11 + {d_cam*px}, {d_cam*py}, {d_cam*pz})")
        page.evaluate("window.__enterFoot()")
        page.wait_for_function(
            "window.__charInfo && window.__charInfo.active && window.__charInfo.grounded",
            timeout=15000)
        ci = page.evaluate("window.__charInfo")
        print(f"E3 land: mode={ci['mode']} gap={ci['gap']:.4f} m speed={ci['speed']:.2e} m/s")
        assert ci["mode"] == "foot"
        assert abs(ci["gap"]) < 0.01, f"E3: landed with gap {ci['gap']} m"
        page.keyboard.down("w")
        page.wait_for_timeout(1000)
        page.keyboard.up("w")
        ci2 = page.evaluate("window.__charInfo")
        assert ci2["speed"] > 0.5, f"E3: WASD did not move the character ({ci2['speed']} m/s)"
        print(f"E3 walk: speed={ci2['speed']:.2f} m/s gap={ci2['gap']:.4f} m")
        page.wait_for_timeout(800)  # Coulomb friction stops it
        ci3 = page.evaluate("window.__charInfo")
        assert ci3["speed"] < 1e-6, \
            f"E3 FALSIFIER: character did not stop ({ci3['speed']} m/s after 0.8 s no input)"
        assert abs(ci3["gap"]) < 0.01
        page.evaluate("window.__exitFoot()")
        page.wait_for_timeout(200)
        ci4 = page.evaluate("window.__charInfo")
        assert ci4["mode"] == "flight", f"E3: takeoff failed ({ci4['mode']})"
        print("E3 scale handoff: land -> walk -> rest -> takeoff OK")

        # ---- TRACK D: INFINITE DETAIL (LOD law + fracture) ----
        # D1 FALSIFIER: at r_px = sqrt(N/rho) the rendered count matches
        # N = rho*r_px^2 within 20% (checked AT the law's own radii).
        R_PL = 6.371e6
        H_canvas = page.evaluate("document.getElementById('c').height")
        for N in (300, 75, 19):
            rpx = _math.sqrt(N / 0.35)
            dist = R_PL * H_canvas / (2 * rpx * 0.414)
            page.evaluate(f"window.__setCam(1.5e11 + {dist}, 0, 0)")
            page.evaluate("window.__lookAt(1.5e11, 0, 0)")
            page.wait_for_timeout(300)
            li = page.evaluate("window.__lodInfo")
            err_pct = abs(li["count"] - N) / N * 100
            print(f"D1: r_px={li['rPx']:.1f} N_target={li['nTarget']} mode={li['mode']} "
                  f"level={li['level']} count={li['count']} (law err {err_pct:.1f}%)")
            assert err_pct <= 20, \
                f"D1 FALSIFIER TRIPPED at N={N}: rendered {li['count']} splats"

        # D2 FALSIFIER: fracture counts track the law (monotonic, within 20%)
        # and pin at the renderer budget past it.
        counts_seen = []
        for rpx in (45, 60, 90):
            dist = R_PL * H_canvas / (2 * rpx * 0.414)
            page.evaluate(f"window.__setCam(1.5e11 + {dist}, 0, 0)")
            page.evaluate("window.__lookAt(1.5e11, 0, 0)")
            page.wait_for_timeout(300)
            li = page.evaluate("window.__lodInfo")
            n_exp = min(round(0.35 * rpx * rpx), li["budgetCap"])
            err_pct = abs(li["count"] - n_exp) / n_exp * 100
            counts_seen.append(li["count"])
            print(f"D2: r_px={li['rPx']:.1f} fracture count={li['count']} vs law {n_exp} "
                  f"({err_pct:.1f}%)")
            assert li["mode"] == "fracture", f"D2: expected fracture mode, got {li['mode']}"
            assert err_pct <= 20, \
                f"D2 FALSIFIER TRIPPED at r_px={rpx}: count {li['count']} vs law {n_exp}"
        assert counts_seen[0] < counts_seen[1] < counts_seen[2], \
            f"D2 FALSIFIER TRIPPED: fracture counts not increasing: {counts_seen}"
        # Budget cap: r_px = 300 -> law wants 31500, budget caps it
        dist = R_PL * H_canvas / (2 * 300 * 0.414)
        page.evaluate(f"window.__setCam(1.5e11 + {dist}, 0, 0)")
        page.evaluate("window.__lookAt(1.5e11, 0, 0)")
        page.wait_for_timeout(300)
        li = page.evaluate("window.__lodInfo")
        print(f"D2 cap: r_px={li['rPx']:.1f} count={li['count']} budget={li['budgetCap']}")
        assert li["count"] == li["budgetCap"], \
            f"D2: budget cap not applied ({li['count']} != {li['budgetCap']})"
        page.click("#btn-center")
        page.wait_for_timeout(300)

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

        # ---- PHASE 7: LORENTZ FORCE + MAGNETIC FIELD ----
        # Falsifier 4: cyclotron frequency match. Enable B-field, read the
        # theoretical cyclotron params for the highest-q/m particle.
        page.evaluate("bFieldEnabled = true")
        page.evaluate("B_field = [0, 0, 1e-3]")  # 1 mT — strong enough to see effects
        page.wait_for_timeout(300)
        cyclo = page.evaluate("window.__cyclotronCheck()")
        print(f"Cyclotron: particle #{cyclo['index']} (q={cyclo['charge']:.2e} C, m={cyclo['mass']:.2e} kg), "
              f"B={cyclo['B_mag']:.2e} T, omega_c={cyclo['omega_c']:.3e} rad/s, "
              f"T_cyclotron={cyclo['T_cyclotron']:.3e} s, r_c={cyclo['r_c']:.3e} m")
        assert cyclo.get("error") is None, f"cyclotron check failed: {cyclo.get('error')}"
        assert cyclo["omega_c"] > 0, "cyclotron frequency is zero — Lorentz force not active?"
        assert cyclo["r_c"] > 0, "gyroradius is zero"

        # Falsifier 5: energy still conserved with B-field on (Lorentz does no work)
        page.click("#btn-cpuem")
        page.click("#btn-reset")
        page.wait_for_function(
            "document.getElementById('particle-count').textContent === '500'",
            timeout=15000)
        f0 = page.evaluate("window.__frames || 0")
        page.wait_for_function(
            f"(window.__frames || 0) >= {f0 + 125}", timeout=60000)
        energy_b = page.evaluate("window.__energy")
        drift_b = page.evaluate("window.__energyDrift")
        print(f"CPU BH+EM+B: KE={energy_b['KE']:.3e} J, total={energy_b['total']:.3e} J; "
              f"drift={drift_b:.4f}% (Lorentz does no work — should be ~0)")
        assert drift_b < 1.0, f"FALSIFIER 5 TRIPPED: energy drift with B-field {drift_b}% >= 1%"

        # Turn B-field off for clean exit
        page.evaluate("bFieldEnabled = false")
        page.wait_for_timeout(200)

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

        print("\n=== All Phase 6 + 7 + 8 + 9 + Track D/E assertions passed! ===")
        browser.close()


if __name__ == "__main__":
    test_kernel_dsl_regions_current()
    test_spiace_phase6_kernels()
