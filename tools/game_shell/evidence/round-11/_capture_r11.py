"""Round-11 STEP C: the engine's OWN capture mechanism (GET /frame -> PNG)
plus real keystrokes to the scratch engine window (PostMessageW, PID-pinned
to .tmp/cam-engine so the shared stack is never targeted).

Sequence: 11a both toggles OFF -> 'c' -> 11b follow cam -> 'v' -> 11c lighting.
Evidence: the three PNGs + a pixel-difference measurement proving the frames
visibly differ, and the engine's stderr FOLLOWCAM lines.
"""
import ctypes, json, struct, sys, time, urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8119"
OUT = Path(__file__).resolve().parent
LOG = OUT / "11_capture_log.txt"
log = open(LOG, "w", encoding="utf-8")


def say(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    log.write(m + "\n"); log.flush()


def find_hwnd(substring):
    """HWND of the chimera_engine window whose EXE PATH contains `substring`.
    The path filter is the safety: a scratch run can never post keystrokes to
    the shared stack's engine (different build dir) or to any other window."""
    import subprocess
    ps = ("Get-Process chimera_engine -ErrorAction SilentlyContinue | "
          "Where-Object { $_.Path -like '*" + substring + "*' } | "
          "Select-Object -First 1 Id,Path,MainWindowHandle | "
          "ConvertTo-Json -Compress")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=30)
    txt = r.stdout.strip()
    if not txt:
        return {}
    d = json.loads(txt)
    return {"hwnd": int(d["MainWindowHandle"]), "pid": int(d["Id"]),
            "path": d["Path"], "title": ""}


def post_key(hwnd, vk):
    """One real WM_KEYDOWN (+WM_KEYUP) on the engine window's message pump.
    lParam=0 -> bit30 clear -> the engine's edge-trigger law fires once."""
    WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
    pm = ctypes.windll.user32.PostMessageW
    pm.restype = ctypes.c_bool
    pm.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_int]
    ok1 = pm(hwnd, WM_KEYDOWN, vk, 0)
    time.sleep(0.05)
    ok2 = pm(hwnd, WM_KEYUP, vk, 0)
    say(f"  posted VK 0x{vk:02X} keydown={ok1} keyup={ok2}")


def grab(name):
    with urllib.request.urlopen(BASE + "/frame", timeout=60) as r:
        data = r.read()
    p = OUT / name
    p.write_bytes(data)
    from PIL import Image
    im = Image.open(p).convert("RGB")
    say(f"  {name}: {len(data)} bytes, {im.size[0]}x{im.size[1]}")
    return im


def diff(a, b):
    import numpy as np
    A = np.asarray(a, dtype=np.int32); B = np.asarray(b, dtype=np.int32)
    d = np.abs(A - B)
    changed = float((d.max(axis=2) > 12).mean()) * 100.0
    return float(d.mean()), changed


say("== C. engine-native capture (GET /frame) + real keystrokes ==")
w = find_hwnd("cam-engine")   # the scratch build dir; the shared stack builds elsewhere
if not w:
    say("FAIL: no scratch-engine window found (refusing to post to any other window)")
    sys.exit(2)
say(f"window: pid={w['pid']} title='{w['title']}' path={w['path']}")

a = grab("11a_dev_default.png")
say("  (toggles OFF: follow-cam off, pass-1 lighting off)")

post_key(w["hwnd"], 0x43)          # 'C'
time.sleep(2.0)                    # let the smoothing settle (tau ~1/8 s)
b = grab("11b_follow_cam.png")

post_key(w["hwnd"], 0x56)          # 'V'
time.sleep(1.0)
c = grab("11c_lighting.png")

m_ab, p_ab = diff(a, b)
m_bc, p_bc = diff(b, c)
say(f"11a vs 11b (camera): mean |dRGB| {m_ab:.2f}, pixels changed >12: {p_ab:.1f}%")
say(f"11b vs 11c (lighting): mean |dRGB| {m_bc:.2f}, pixels changed >12: {p_bc:.1f}%")

# toggle back OFF and prove the shipped look returns (default-OFF regression)
post_key(w["hwnd"], 0x56); time.sleep(0.8)
post_key(w["hwnd"], 0x43); time.sleep(2.0)
d = grab("11d_toggles_off_restored.png")
m_ad, p_ad = diff(a, d)
say(f"11a vs 11d (both toggles cycled back OFF): mean |dRGB| {m_ad:.2f}, "
    f"pixels changed >12: {p_ad:.1f}%")
say("PASS-C" if (p_ab > 5.0 and p_bc > 5.0) else "CHECK-C")
