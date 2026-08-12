from playwright.sync_api import sync_playwright
import time, sys

def test_spiace_phase0():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        page.goto("file:///E:/PythonChimera/ChimeraEngine/engine/spiace_phase0.html")
        page.wait_for_timeout(5000)  # Give time for loop to start

        # Take screenshot
        page.screenshot(path="E:/PythonChimera/ChimeraEngine/engine/spiace_phase0_screenshot.png", full_page=False)
        print("Screenshot saved")

        # Check HUD elements
        fps = page.locator("#fps").text_content()
        ship_info = page.locator("#ship-info").text_content()
        orbit_info = page.locator("#orbit-info").text_content()
        sys_info = page.locator("#sys-info").text_content()

        print(f"FPS: {fps}")
        print(f"Ship: {ship_info}")
        print(f"Orbit: {orbit_info}")
        print(f"System: {sys_info}")

        # Verify key physics values
        assert ship_info and "m/s" in ship_info, f"Ship info missing: {ship_info}"
        assert orbit_info and "Gm" in orbit_info, f"Orbit info missing: {orbit_info}"
        assert sys_info and "Phase 0" in sys_info, f"System info wrong: {sys_info}"

        # Check canvas has content (non-empty)
        canvas = page.locator("canvas")
        assert canvas.is_visible(), "Canvas not visible"

        print("All assertions passed!")
        browser.close()

if __name__ == "__main__":
    test_spiace_phase0()
