# N1 — native core end-to-end: C++ ca_core.exe grows the G1 wall, streams
# NDJSON over SSE through relay.py, and spiace_native.html (ZERO simulation
# logic) renders it with the WebGPU splat pipeline.
#
# Falsifiers (named before the run):
#   F-N1a: renderer is webgpu-splat
#   F-N1b: the wire ledger (native_stream.log, read by THIS oracle — not the
#          page's self-report) shows monotonic growth with 0 violations on
#          every frame
#   F-N1c: the final C++ grown set == the blueprint set exactly, recomputed
#          HERE from the genome table (integer (y,i) pairs — no float games)
#   F-N1d: completion at tick <= 200 (reference: 14)
#   F-N1e: the page's cell set matches the wire's final set (the browser
#          believed the wire, faithfully)
import json
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / "native"
LOG = NATIVE / "native_stream.log"
PORT = 8799
fails = []

def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok:
        fails.append(name)

# --- the oracle's own blueprint, recomputed from the genome table ------------
BRICK_LEN, GAP, COURSES, WIDE, SEED_I, MIN_SUPPORT = 0.22, 0.012, 12, 18, 9, 0.30
xp = BRICK_LEN + GAP
blueprint = {}
for y in range(COURSES):
    n = WIDE if y % 2 == 0 else WIDE - 1
    off = 0.0 if y % 2 == 0 else xp / 2
    for i in range(n):
        blueprint[(y, i)] = (i * xp + off, i * xp + off + BRICK_LEN)

def supported(y, i, placed):
    if y == 0:
        return True
    x0, x1 = blueprint[(y, i)]
    for (cy, ci) in placed:
        if cy != y - 1:
            continue
        cx0, cx1 = blueprint[(cy, ci)]
        if min(x1, cx1) - max(x0, cx0) > MIN_SUPPORT * BRICK_LEN:
            return True
    return False

# --- build + launch ------------------------------------------------------------
print("building ca_core.exe …")
subprocess.run(["g++", "-O2", "-std=c++17", "-o", str(NATIVE / "ca_core.exe"),
                str(NATIVE / "ca_core.cpp")], check=True)
relay = subprocess.Popen([sys.executable, str(NATIVE / "relay.py"), "15",
                          str(PORT)], stdout=subprocess.PIPE, text=True)
time.sleep(1.0)  # relay bind

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,
                                    args=["--enable-unsafe-webgpu"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(f"http://127.0.0.1:{PORT}/")
        page.wait_for_function("window.__growthStats !== undefined",
                               timeout=30000)
        page.wait_for_function("window.__renderer !== 'none'", timeout=15000)
        page.screenshot(path="_native_start.png")
        check("F-N1a renderer is webgpu-splat",
              page.evaluate("window.__renderer") == "webgpu-splat",
              page.evaluate("window.__renderer"))
        t0 = time.time()
        st = None
        while time.time() - t0 < 60:
            st = page.evaluate("window.__growthStats")
            if st["done"]:
                break
            time.sleep(0.25)
        check("F-N1d completed, tick <= 200", st["done"] and st["tick"] <= 200,
              f"tick={st['tick']} cells={st['cellCount']}")
        time.sleep(0.5)
        page.screenshot(path="_native_end.png")
        page_cells = {tuple(c) for c in page.evaluate("window.__growthCheck().cells")}
        browser.close()

    # --- oracle reads the WIRE LOG, not the page --------------------------------
    frames = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]
    counts = [len(f["cells"]) for f in frames]
    viols = [f["violations"] for f in frames]
    mono = all(counts[i] >= counts[i - 1] for i in range(1, len(counts)))
    check("F-N1b wire ledger monotonic, 0 violations every frame",
          mono and all(v == 0 for v in viols),
          f"{len(frames)} frames, cells {counts[0]}->{counts[-1]}, "
          f"max viol {max(viols)}")
    final_set = {tuple(c) for c in frames[-1]["cells"]}
    check("F-N1c grown set == blueprint (oracle-recomputed)",
          final_set == set(blueprint),
          f"{len(final_set)} vs {len(blueprint)}, "
          f"diff={len(final_set ^ set(blueprint))}")
    # independent support audit of the final set
    unsupported = sum(1 for k in final_set if not supported(*k, final_set))
    check("F-N1c oracle support audit of the final wall", unsupported == 0,
          f"unsupported={unsupported}")
    check("F-N1e page's wall == wire's wall", page_cells == final_set,
          f"page {len(page_cells)} vs wire {len(final_set)}")
    print(f"N1 MEASURED: frames={len(frames)} final_tick={frames[-1]['tick']} "
          f"cells={counts[-1]} viol_max={max(viols)}")
finally:
    relay.terminate()

print("RESULT:", "ALL GREEN" if not fails else f"FAILED: {fails}")
raise SystemExit(1 if fails else 0)
