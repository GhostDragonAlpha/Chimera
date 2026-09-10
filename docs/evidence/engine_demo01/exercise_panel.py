"""Recorded review of the explicitly owned panel/native process pair.

Run-specific handles are deliberately not a reusable launcher interface.
Refuse any target that no longer belongs to the inspected panel PID.
"""
import ctypes
import hashlib
import json
import time
import urllib.request
from ctypes import wintypes as W
from pathlib import Path

OUT = Path(__file__).parent / "panel_controls"
BASE = "http://127.0.0.1:8101"
PANEL_PID = 32024
PANEL_HWND = 12323984
BUTTONS = {"Step": 7736368, "Run": 6754540, "Pause": 7409858,
           "Reset": 6754898, "Status": 5837238,
           "gamma0": 3543742, "gamma1": 6754676, "gamma2": 9376290}
u = ctypes.WinDLL("user32", use_last_error=True)
u.SetForegroundWindow.argtypes = [W.HWND]
u.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
u.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
u.WindowFromPoint.argtypes = [W.POINT]
u.WindowFromPoint.restype = W.HWND


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as response:
        return response.read()


def status():
    return json.loads(get("/membrane_demo"))


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)


def click(name):
    before = status()
    hwnd = BUTTONS[name]
    pid = W.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value != PANEL_PID:
        raise RuntimeError("button no longer belongs to owned panel")
    u.SetForegroundWindow(PANEL_HWND)
    rect = W.RECT()
    if not u.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("button rectangle unavailable")
    x, y = (rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2
    u.SetCursorPos(x, y)
    time.sleep(.15)
    hit = u.WindowFromPoint(W.POINT(x, y))
    if hit != hwnd:
        raise RuntimeError("button is occluded; refuse global click")
    started = time.time()
    u.mouse_event(2, 0, 0, 0, 0)
    time.sleep(.08)
    u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(.15)
    after = status()
    save(f"{time.time_ns()}_{name}.json", {
        "action": name, "panel_pid": PANEL_PID, "widget_hwnd": hwnd,
        "before": before, "after": after,
        "started_unix": started, "finished_unix": time.time(),
    })
    return after


def capture(label):
    before = status()
    raw = get("/frame")
    after = status()
    with (OUT / (label + ".png")).open("xb") as stream:
        stream.write(raw)
    save(label + ".json", {
        "before": before, "after": after, "image_sha256": hashlib.sha256(raw).hexdigest(),
        "exact_render_submission": "INSUFFICIENT_EVIDENCE",
        "camera_bookmark": [3, 0, 0, 0, .5, 0, 0, 0],
    })


def main():
    OUT.mkdir(exist_ok=False)
    checks = {}
    initial = status()
    stepped = click("Step")
    checks["step_advances"] = stepped["iteration"] > initial["iteration"]
    reset = click("Reset")
    checks["reset_restores"] = reset["iteration"] == 0 and reset["centre"] == initial["centre"]
    doubled = click("gamma2")
    # Existing membrane_demo_client gate: doubling.energy absolute tolerance 4e-6.
    checks["gamma_doubles_fixed_energy"] = abs(doubled["energy"] - 2 * reset["energy"]) <= 4e-6
    click("gamma1")
    capture("profile_raised")
    click("Run")
    paused = click("Pause")
    time.sleep(.3)
    settled = status()
    checks["pause_stops_iteration"] = settled["iteration"] == paused["iteration"]
    click("Run")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if status()["terminal_state"]:
            break
        time.sleep(.1)
    capture("profile_after_run")
    checks["run_reaches_terminal"] = bool(status()["terminal_state"])
    click("Reset")
    zero = click("gamma0")
    checks["zero_gamma_energy"] = zero["energy"] == 0
    click("gamma1")
    save("checks.json", checks)
    print(json.dumps(checks, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
