"""Diagnostic: after SEVER, what does the judge actually see?

Logs (proxy /api/state q, page readout q, verdict, __tendonState) every
0.4 s for 40 s after clicking the sever button, to find why the q<5 pass
window is missed on some runs. Read-only to the world except lesson 6.
"""
import time, json, re, urllib.request, tempfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8210"


def proxy_get(path):
    with urllib.request.urlopen(URL + path, timeout=10) as r:
        return json.loads(r.read())


def proxy_post(path, obj):
    req = urllib.request.Request(URL + path, data=json.dumps(obj).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main():
    d = tempfile.mkdtemp(prefix="r10diag-")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            d, headless=False, viewport={'width': 1280, 'height': 900},
            args=['--use-gl=angle', '--use-angle=swiftshader'])
        page = ctx.pages[0]
        page.goto(URL + "/?debug=1", wait_until="load", timeout=30000)
        time.sleep(2.0)
        page.fill("#name-input", "R10-DIAG")
        page.click("#play-btn")
        time.sleep(1.5)
        try:
            page.click("#intro-begin", timeout=1500)
        except Exception:
            pass
        page.keyboard.press("q")
        time.sleep(1.0)
        # reset tendon to limp-not-severed, then arm via proxy
        proxy_post("/api/effort", {"joint_index": 15, "u": 1}); time.sleep(1.5)
        proxy_post("/api/sever", {"joint_index": 15}); time.sleep(3.0)
        proxy_post("/api/effort", {"joint_index": 15, "u": -1}); time.sleep(0.5)
        # flex via the real slider
        page.click("#effort-u")
        page.keyboard.press("End")
        t0 = time.time()
        while time.time() - t0 < 15:
            q = proxy_get("/api/state").get("tendon_q_deg") or 0
            if q >= 40:
                break
            time.sleep(0.2)
        print("flexed q=", proxy_get("/api/state").get("tendon_q_deg"), flush=True)
        page.click("#effort-sever-btn")
        t0 = time.time()
        while time.time() - t0 < 40:
            st = proxy_get("/api/state")
            info = page.evaluate("""()=>{
                var ro=document.getElementById('effort-readout');
                var v=document.getElementById('verdict');
                var jd=document.getElementById('judge-debug');
                return {ro: ro?ro.textContent:'', v: v?v.textContent:'',
                        jd: jd?jd.textContent:'',
                        ts: window.__tendonState||null};}""")
            print(f"t={time.time()-t0:5.1f} proxy_q={st.get('tendon_q_deg'):8.2f} "
                  f"sev={st.get('tendon_severed')} | ro={info['ro'][:60]!r} "
                  f"| v={info['v'][:40]!r} | ts={info['ts']}", flush=True)
            if 'PASSED' in info['v']:
                print("PASSED observed", flush=True)
                break
            time.sleep(0.4)
        ctx.close()


main()
