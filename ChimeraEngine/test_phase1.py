from playwright.sync_api import sync_playwright
import time

def test_spiace_phase1():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        page.goto("file:///E:/PythonChimera/ChimeraEngine/engine/spiace_phase1.html")
        page.wait_for_timeout(5000)

        # Screenshot
        page.screenshot(path="E:/PythonChimera/ChimeraEngine/engine/spiace_phase1_screenshot.png", full_page=False)
        print("Screenshot saved")

        # Check key elements
        fps = page.locator("#fps").text_content()
        ship_info = page.locator("#ship-info").text_content()
        orbit_info = page.locator("#orbit-info").text_content()
        nbody_info = page.locator("#nbody-info").text_content()

        print(f"FPS: {fps}")
        print(f"Ship: {ship_info}")
        print(f"Orbit: {orbit_info}")
        print(f"N-body: {nbody_info}")

        # Verify physics
        assert ship_info and "m/s" in ship_info, f"Ship info missing: {ship_info}"
        assert orbit_info and ("Gm" in orbit_info or "Dist" in orbit_info), f"Orbit missing: {orbit_info}"
        assert nbody_info and "Bodies:" in nbody_info, f"N-body missing: {nbody_info}"

        # Test Hohmann transfer button
        page.click("#btn-hohmann")
        page.wait_for_timeout(1000)
        hohmann_info = page.locator("#nbody-info").text_content()
        print(f"After Hohmann: {hohmann_info}")
        assert "Hohmann" in hohmann_info or "dV" in hohmann_info, f"Hohmann not triggered: {hohmann_info}"

        # Test time scale slider
        page.locator("#tslider").fill("75")
        page.wait_for_timeout(500)
        ts = page.locator("#time-scale").text_content()
        print(f"Time scale: {ts}")

        print("All Phase 1 assertions passed!")
        browser.close()

if __name__ == "__main__":
    test_spiace_phase1()
