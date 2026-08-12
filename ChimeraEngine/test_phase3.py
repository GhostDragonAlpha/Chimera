from playwright.sync_api import sync_playwright

def test_spiace_phase3():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        page.goto("file:///E:/PythonChimera/ChimeraEngine/engine/spiace_phase3.html")
        page.wait_for_timeout(4000)

        page.screenshot(path="E:/PythonChimera/ChimeraEngine/engine/spiace_phase3_screenshot.png", full_page=False)
        print("Screenshot saved")

        # Check key elements
        fps = page.locator("#fps").text_content()
        ship_info = page.locator("#ship-info").text_content()
        warp_info = page.locator("#warp-info").text_content()

        print(f"FPS: {fps}")
        print(f"Ship: {ship_info}")
        print(f"Warp: {warp_info}")

        assert ship_info and ("km/s" in ship_info or "Speed" in ship_info), f"Ship info wrong: {ship_info}"
        assert warp_info, f"Warp info missing: {warp_info}"

        # Check system info panel
        star_type = page.locator("#star-type").text_content()
        body_count = page.locator("#body-count").text_content()
        hab_zone = page.locator("#hab-zone").text_content()
        print(f"Star: {star_type}, Bodies: {body_count}, Hab Zone: {hab_zone}")

        assert star_type and "V" in star_type, f"Star type wrong: {star_type}"
        assert body_count and int(body_count) > 0, f"Body count wrong: {body_count}"
        assert hab_zone and "AU" in hab_zone, f"Hab zone wrong: {hab_zone}"

        # Open star map
        page.click("#btn-map")
        page.wait_for_timeout(1000)
        star_list = page.locator("#star-list").text_content()
        print(f"Star map: {star_list[:100]}...")
        assert "Sol" in star_list or "Sirius" in star_list, f"No stars in map: {star_list}"

        # Click warp button
        page.click("#btn-warp")
        page.wait_for_timeout(3000)
        warp_status = page.locator("#warp-status").text_content()
        curr_sys = page.locator("#curr-sys").text_content()
        print(f"Warp status: {warp_status}, Current system: {curr_sys}")

        assert warp_status == "ACTIVE", f"Warp not active: {warp_status}"

        # Wait for warp to complete
        page.wait_for_timeout(2000)
        new_warp = page.locator("#warp-status").text_content()
        print(f"After warp: {new_warp}")

        print("All Phase 3 assertions passed!")
        browser.close()

if __name__ == "__main__":
    test_spiace_phase3()
