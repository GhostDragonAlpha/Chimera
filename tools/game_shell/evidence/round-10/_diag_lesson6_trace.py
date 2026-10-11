"""Diagnostic 2: trace verdict + tendon state at EVERY step of the lesson-6
flow, to find where 'the muscle pulls' appears before the real drag."""
import time, json, tempfile, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"


def pg(path):
    with urllib.request.urlopen(URL + path, timeout=10) as r:
        return json.loads(r.read())


def pp(path, obj):
    req = urllib.request.Request(URL + path, data=json.dumps(obj).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main():
    d = tempfile.mkdtemp(prefix="r10trace-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            d, headless=False, viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.goto(URL + "/?debug=1", wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "R10-TRACE")
        page.click("#play-btn")
        time.sleep(1.5)
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            pass

        def snap(tag):
            info = page.evaluate("""()=>({
                v:(document.getElementById('verdict')||{textContent:''}).textContent,
                li:(document.getElementById('lesson-index')||{textContent:''}).textContent,
                ro:(document.getElementById('effort-readout')||{textContent:''}).textContent})""")
            s = pg("/api/state")
            print(f"[{tag}] lesson={info['li']} q={s.get('tendon_q_deg'):.1f} "
                  f"sev={s.get('tendon_severed')} armed={s.get('tendon_armed')} "
                  f"batt={s.get('tendon_battery_J'):.1f} | ro={info['ro'][:52]!r} "
                  f"| v={info['v'][:60]!r}", flush=True)

        snap("boot")
        page.keyboard.press("q"); time.sleep(1.0); snap("after q (lesson 6)")
        # preset under lesson 1
        page.keyboard.press("1"); time.sleep(0.8); snap("after 1 (lesson 1)")
        pp("/api/effort", {"joint_index": 15, "u": 1}); time.sleep(1.5)
        snap("preset arm u=1")
        pp("/api/sever", {"joint_index": 15}); time.sleep(3.0)
        snap("preset sever")
        pp("/api/effort", {"joint_index": 15, "u": -1}); time.sleep(0.4)
        pp("/api/effort", {"joint_index": 15, "u": 0.05}); time.sleep(0.35)
        pp("/api/effort", {"joint_index": 15, "u": -1}); time.sleep(0.5)
        snap("preset done")
        for i in range(5):
            page.click("#lesson-next"); time.sleep(0.45)
        snap("nav to 6")
        time.sleep(1.2); snap("before-shot moment")
        # real drag: click+End (same as driver's pin)
        page.click("#effort-u"); page.keyboard.press("End"); time.sleep(0.5)
        snap("after drag End")
        t0 = time.time()
        while time.time() - t0 < 10:
            if (pg("/api/state").get("tendon_q_deg") or 0) >= 40:
                break
            time.sleep(0.2)
        snap("flexed")
        page.click("#effort-sever-btn")
        t0 = time.time()
        while time.time() - t0 < 25:
            snap(f"post-sever {time.time()-t0:.1f}s")
            info = page.evaluate("()=>document.getElementById('verdict').textContent")
            if 'PASSED' in info:
                break
            time.sleep(0.5)
        ctx.close()


main()
