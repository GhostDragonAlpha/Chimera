# smoke_capture.py -- the browser leg of the real-shape smoke, launched
# THROUGH the fleet supervisor (kind=browser): one bundled-chromium headless
# capture of the slice page. Bundled chromium per MACHINE_FINDINGS 2026-09-20
# (installed Chrome cannot navigate on this host); fresh context, never the
# operator's browser.
import json
import sys
import time

from playwright.sync_api import sync_playwright


def main() -> int:
    url, out_png, out_json = sys.argv[1], sys.argv[2], sys.argv[3]
    t0 = time.time()
    result = {"url": url, "ok": False}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # BUNDLED chromium, no channel
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(2500)  # let the canvas render frames
                result["title"] = page.title()
                page.screenshot(path=out_png)
                result["screenshot"] = out_png
                result["ok"] = True
            finally:
                browser.close()
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    result["elapsed_s"] = round(time.time() - t0, 2)
    with open(out_json, "w") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
