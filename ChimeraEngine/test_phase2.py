from playwright.sync_api import sync_playwright

def test_spiace_phase2():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        page.goto("file:///E:/PythonChimera/ChimeraEngine/engine/spiace_phase2.html")
        page.wait_for_timeout(5000)

        page.screenshot(path="E:/PythonChimera/ChimeraEngine/engine/spiace_phase2_screenshot.png", full_page=False)
        print("Screenshot saved")

        # Check key elements
        fps = page.locator("#fps").text_content()
        ship_info = page.locator("#ship-info").text_content()
        surface_info = page.locator("#surface-info").text_content()
        atmo_info = page.locator("#atmo-info").text_content()

        print(f"FPS: {fps}")
        print(f"Ship: {ship_info}")
        print(f"Surface: {surface_info}")
        print(f"Atmosphere: {atmo_info}")

        # Verify physics elements exist
        assert ship_info and ("km" in ship_info or "m/s" in ship_info), f"Ship info wrong: {ship_info}"
        assert surface_info and len(surface_info) > 5, f"Surface info missing: {surface_info}"
        assert atmo_info and "%" in atmo_info, f"Atmosphere missing: {atmo_info}"

        # Check telemetry panel
        alt = page.locator("#alt").text_content()
        vspeed = page.locator("#vspeed").text_content()
        fuel = page.locator("#fuel-pct").text_content()
        print(f"Alt: {alt}, VSPEED: {vspeed}, Fuel: {fuel}")

        assert alt and "m" in alt, f"Altitude missing: {alt}"
        assert fuel and "%" in fuel, f"Fuel missing: {fuel}"

        # Test thrust button
        page.click("#btn-thrust")
        page.wait_for_timeout(2000)
        new_alt = page.locator("#alt").text_content()
        print(f"After thrust: {new_alt}")

        # Test time scale
        page.locator("#tslider").fill("75")
        page.wait_for_timeout(500)
        ts = page.locator("#time-scale").text_content()
        print(f"Time scale: {ts}")

        print("All Phase 2 assertions passed!")
        browser.close()

if __name__ == "__main__":
    test_spiace_phase2()
