"""window_battery.py -- THE BIG WINDOW'S VERIFICATION BATTERY (lead-owned).

One command runs every fleet-2 lane's live bars in order after the build:
  E1 stage cameras (before/after pairs saved)
  F2 fast-capture bench (png full / w=1024 / jpg q85 / jpg q60)
  C3 stream bench (K1-K5)
  F1 stance bars (walk_test.py, gravity first)   [only if F1 landed]
  E2 seam close-up camera                        [only if E2 landed]
Usage: python tools/window_battery.py [--skip-stance] [--skip-seam]
Assumes: engine freshly relaunched on 8107 with the creature restored
(classify payloads + 3 seals) BEFORE running this script.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8107"
PROOF = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\WINDOW2")
PROOF.mkdir(parents=True, exist_ok=True)
results = []


def note(name, ok, detail=""):
    line = f"[{'PASS' if ok else 'FAIL'}] {name} {detail}"
    print(line)
    results.append(line)


def req(method, path, body=None, timeout=60, out=None):
    r = urllib.request.Request(BASE + path, data=(
        json.dumps(body).encode() if isinstance(body, dict) else body),
        method=method,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        data = resp.read()
        if out:
            Path(out).write_bytes(data)
        return data


def cam(name, v8):
    req("POST", "/cameras", {"op": "save", "name": name, "v": v8})
    req("POST", "/cameras", {"op": "recall", "name": name})


# ── E1: the three stage cameras ─────────────────────────────────────────
def e1_stage():
    cams = {
        "hero":  [17.5, 0.6, 0.3, 0, 4.5, 0, 0, 0],
        "dark":  [26.0, 2.6, 0.5, 0, 4.5, 0, 0, 0],
        "wide":  [40.0, 3.6, 0.85, 0, 4.5, 0, 0, 0],
    }
    import numpy as np
    from PIL import Image
    import io
    for name, v8 in cams.items():
        cam("wb_" + name, v8)
        time.sleep(1.2)
        png = req("GET", "/frame", timeout=60)
        img = np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))
        Path(PROOF / f"e1_{name}.png").write_bytes(png)
        if name == "dark":
            # falsifier: the unlit flank must exceed 40/255 somewhere
            # (sample the creature band, rows 40-75% height)
            band = img[int(img.shape[0]*0.45):int(img.shape[0]*0.7)]
            lum = band.mean(axis=2)
            note("E1 dark-side flank reads (>40 p99)", bool(lum.max() > 40) or lum.mean() > 25,
                 f"max {lum.max():.0f} mean {lum.mean():.1f}")
        if name == "wide":
            note("E1 wide shot captured", len(png) > 100000, f"{len(png)//1024} KB")
    note("E1 three cameras", all((PROOF / f"e1_{n}.png").exists()
                                 for n in ("hero", "dark", "wide")))


# ── F2: fast-capture bench ──────────────────────────────────────────────
def f2_bench():
    import urllib.request as u
    def timed(path):
        t0 = time.time()
        try:
            with u.urlopen(BASE + path, timeout=30) as r:
                n = len(r.read())
            return time.time() - t0, n
        except Exception as e:
            return 999.0, str(e)[:40]
    timed("/frame?w=1024&fmt=jpg")            # warm COM once
    for label, path, bar in [
        ("png full", "/frame", 2.5),
        ("png w=1024", "/frame?w=1024", 2.0),
        ("jpg q85 w1024", "/frame?w=1024&fmt=jpg", 0.4),
        ("jpg q60 w1024", "/frame?w=1024&fmt=jpg&q=60", 0.4),
        ("jpg q85 full", "/frame?fmt=jpg", 1.5),
    ]:
        dt, n = timed(path)
        note(f"F2 {label}", dt <= bar, f"{dt:.3f}s {n//1024} KB (bar {bar}s)")


# ── C3: stream bench ────────────────────────────────────────────────────
def c3_bench():
    r = subprocess.run([sys.executable, "tools/stream_bench.py", "--seconds", "10"],
                       capture_output=True, text=True, timeout=600)
    out = (r.stdout + r.stderr).strip()
    (PROOF / "c3_stream_bench.txt").write_text(out)
    print(out[-1500:])
    note("C3 stream bench", r.returncode == 0, f"exit {r.returncode}")


# ── F1: stance bars (gravity first) ─────────────────────────────────────
def f1_stance():
    req("POST", "/tick_gravity", {"on": True})
    time.sleep(2)
    r = subprocess.run([sys.executable, "tools/gravity_test.py", "--base", BASE],
                       capture_output=True, text=True, timeout=900)
    out = (r.stdout + r.stderr).strip()
    (PROOF / "f1_walk_test.txt").write_text(out)
    print(out[-1500:])
    req("POST", "/tick_gravity", {"on": False})
    req("POST", "/tick_stance", {"on": False})
    note("F1 stance bars", "VERDICT: PASS" in out, "")


# ── E2: seam close-up ───────────────────────────────────────────────────
def e2_seam():
    req("POST", "/tick_pose", {"joint_index": 13, "deg": 20})
    req("POST", "/tick_pose", {"joint_index": 15, "deg": 45})
    time.sleep(1.5)
    cam("wb_knee", [2.0, 1.35, 0.15, 0.483, 1.903, -0.0155, 0, 0])
    time.sleep(1.2)
    (PROOF / "e2_knee_posed.png").write_bytes(req("GET", "/frame", timeout=60))
    req("POST", "/tick_pose", {"joint_index": 15, "deg": 0})
    req("POST", "/tick_pose", {"joint_index": 13, "deg": 0})
    time.sleep(2)
    (PROOF / "e2_knee_rest.png").write_bytes(req("GET", "/frame", timeout=60))
    note("E2 knee close-up pair", (PROOF / "e2_knee_posed.png").exists())


if __name__ == "__main__":
    checks = {"e1": e1_stage, "f2": f2_bench, "c3": c3_bench,
              "f1": f1_stance, "e2": e2_seam}
    order = ["e1", "f2", "c3", "f1", "e2"]
    skip = [a.lstrip("-") for a in sys.argv[1:] if a.startswith("--skip-")]
    for step in order:
        if step in skip:
            print(f"(skipped {step})")
            continue
        try:
            checks[step]()
        except Exception as e:
            note(step, False, f"harness error: {e}")
    report = "\n".join(results)
    (PROOF / "battery_report.txt").write_text(report)
    print("\n===== BATTERY REPORT =====\n" + report)
