"""smoke_thin.py -- drive the thin client headless and dump its live state.

Usage: python smoke_thin.py --url http://127.0.0.1:PORT [--out state.json]
"""
from __future__ import annotations

import argparse
import json


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--secs", type=float, default=6.0)
    a = ap.parse_args()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 960, "height": 540})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(a.url + "/?thin=1&rate=30&pilot=1")
        page.wait_for_timeout(int(a.secs * 1000))
        state = page.evaluate("window.__thin_state()")
        dump = json.loads(page.evaluate("window.__pilot_dump()"))
        shot = page.screenshot(path=(a.out or "thin_state.json").replace(".json", ".png"))
        del shot
        browser.close()

    rec = {"url": a.url, "thin_state": state,
           "pilot_head": {"params": dump["params"], "mode": dump["mode"],
                          "achieved_hz": dump["achieved_hz"], "bps": dump["bps"],
                          "underruns": dump["underruns"], "pullErrs": dump["pullErrs"],
                          "n_raf": len(dump["raf"]), "n_snaps": len(dump["snaps"]),
                          "cam": dump["cam"]},
           "console_errors": errors[:10]}
    print(json.dumps(rec, indent=1))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
