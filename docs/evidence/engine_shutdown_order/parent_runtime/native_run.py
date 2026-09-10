"""Owned native-window lifecycle verification; no foreign process actions."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.request
from PIL import ImageGrab

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
user = c.WinDLL("user32", use_last_error=True)
user.SetProcessDPIAware()
user.IsWindowVisible.argtypes = [w.HWND]
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.ClientToScreen.argtypes = [w.HWND, c.POINTER(w.POINT)]
user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
user.IsWindow.argtypes = [w.HWND]
user.SetWindowPos.argtypes = [w.HWND, w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.UINT]
user.ShowWindow.argtypes = [w.HWND, c.c_int]
user.WindowFromPoint.argtypes = [w.POINT]
user.WindowFromPoint.restype = w.HWND
user.GetAncestor.argtypes = [w.HWND, w.UINT]
user.GetAncestor.restype = w.HWND
callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)


def windows(pid):
    found = []
    @callback_type
    def visit(hwnd, _):
        owner = w.DWORD()
        user.GetWindowThreadProcessId(hwnd, c.byref(owner))
        if owner.value == pid and user.IsWindowVisible(hwnd):
            rect = w.RECT()
            user.GetWindowRect(hwnd, c.byref(rect))
            box = (rect.left, rect.top, rect.right, rect.bottom)
            if box[2] > box[0] and box[3] > box[1]:
                found.append((int(hwnd), box))
        return True
    user.EnumWindows(visit, 0)
    return sorted(found, key=lambda v: (v[1][2]-v[1][0])*(v[1][3]-v[1][1]), reverse=True)


def request(port, path, payload=None, timeout=12):
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path),
                                 data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--case", choices=["quiet", "boot", "pending", "nested"], required=True)
    p.add_argument("--run", required=True)
    p.add_argument("--instrumented", action="store_true")
    p.add_argument("--regression", action="store_true")
    a = p.parse_args()
    assert Path(a.run).name == a.run
    assert a.case not in ("pending", "nested") or a.instrumented
    out = HERE / a.run
    out.mkdir(exist_ok=False)
    runtime = ROOT / ".tmp" / "engine_runtime" / a.run
    runtime.mkdir(parents=True, exist_ok=False)
    exe = a.exe.resolve()
    assert exe.is_file() and (exe.parent / "shaders").is_dir()
    staged = runtime / exe.name
    shutil.copy2(exe, staged)
    shutil.copytree(exe.parent / "shaders", runtime / "shaders")
    if a.case == "nested":
        # Explicit synthetic ABI fixture: one right triangle, +Z normals,
        # white vertices, fill mode. This tests cancellation, not material physics.
        verts = [0,0,0,0,0,1,1,1,1, 1,0,0,0,0,1,1,1,1, 0,1,0,0,0,1,1,1,1]
        blob = struct.pack("<IIffff",3,3,3,0,0,0) + struct.pack("<27f",*verts) + struct.pack("<3I",0,1,2)
        (runtime / "session_snapshot").mkdir()
        (runtime / "session_snapshot" / "mesh_bin.blob").write_bytes(blob)
        (out / "mesh_fixture.sha256").write_text(hashlib.sha256(blob).hexdigest())
    port = 8102
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(("127.0.0.1", port))
    env = os.environ.copy()
    env.pop("CHIMERA_SHUTDOWN_TEST_HOLD", None)
    if a.case in ("pending", "nested"):
        env["CHIMERA_SHUTDOWN_TEST_HOLD"] = "1"
    args = [str(staged), str(port)]
    if a.case != "boot": args.append("--no-restore")
    result = dict(case=a.case, instrumented=a.instrumented, commands=args, port=port,
                  exe_sha256=hashlib.sha256(staged.read_bytes()).hexdigest(),
                  main_sha256=hashlib.sha256((ROOT / "ChimeraEngine/engine/main.cpp").read_bytes()).hexdigest(),
                  shaders={str(f.relative_to(runtime)):hashlib.sha256(f.read_bytes()).hexdigest()
                           for f in (runtime / "shaders").glob("*.spv")})
    client = None
    client_result = {}
    with (out / "engine.stdout.log").open("wb") as stdout, (out / "engine.stderr.log").open("wb") as stderr:
        proc = subprocess.Popen(args, cwd=runtime, env=env, stdout=stdout, stderr=stderr,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    result["pid"] = proc.pid
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            assert proc.poll() is None, "native exited during startup"
            view = windows(proc.pid)
            if view:
                try:
                    result["state"] = request(port, "/state", timeout=1)
                    break
                except Exception: pass
            time.sleep(.05)
        else: raise AssertionError("startup did not produce owned window and HTTP readiness")
        hwnd, box = view[0]
        result["hwnd"] = hwnd
        result["window_box"] = box
        listener = subprocess.check_output(["powershell", "-NoProfile", "-Command",
                    "(Get-NetTCPConnection -LocalPort 8102 -State Listen).OwningProcess"], text=True).strip()
        assert listener == str(proc.pid), "endpoint belongs to another process"
        if a.regression:
            assert a.case == "quiet" and not a.instrumented
            identity = out / "regression_identity.json"
            identity.write_text(json.dumps(result, indent=2), encoding="utf-8")
            check = subprocess.run([sys.executable, str(ROOT / "tools/demo_runtime_verify.py"),
                "--base", "http://127.0.0.1:8102", "--identity", str(identity),
                "--output", str(out / "reset_regression")], capture_output=True)
            (out / "regression.log").write_bytes(check.stdout + check.stderr)
            result["normal_regression_exit"] = check.returncode
            assert check.returncode == 0, "existing runtime reset gates failed"
        # Make only our own native window unobscured before screen capture.
        # A PID-matched HWND alone does not establish visible screen content.
        user.ShowWindow(hwnd, 9)
        assert user.SetWindowPos(hwnd, w.HWND(-1), 64, 64, 1280, 720, 0x0040)
        deadline = time.monotonic() + 5
        while True:
            try:
                with urllib.request.urlopen("http://127.0.0.1:8102/glass", timeout=1) as response:
                    png = response.read()
                if png.startswith(b"\x89PNG\r\n\x1a\n"): break
            except Exception: pass
            assert time.monotonic() < deadline, "owned window has no presented frame"
            time.sleep(.05)
        rect = w.RECT()
        user.GetWindowRect(hwnd, c.byref(rect))
        box = (rect.left, rect.top, rect.right, rect.bottom)
        result["capture_box"] = box
        for x, y in [(box[0]+12,box[1]+40), (box[2]-12,box[1]+40),
                     (box[0]+12,box[3]-12), (box[2]-12,box[3]-12),
                     ((box[0]+box[2])//2,(box[1]+box[3])//2)]:
            hit = user.WindowFromPoint(w.POINT(x, y))
            assert user.GetAncestor(hit, 2) == hwnd, "capture region is occluded"
        (out / "owned_glass.png").write_bytes(png)
        client_rect = w.RECT()
        origin = w.POINT(0, 0)
        user.GetClientRect(hwnd, c.byref(client_rect))
        user.ClientToScreen(hwnd, c.byref(origin))
        client_box = (origin.x, origin.y, origin.x+client_rect.right, origin.y+client_rect.bottom)
        result["client_capture_box"] = client_box
        ImageGrab.grab(bbox=client_box).save(out / "window_before.png")
        if a.case in ("pending", "nested"):
            def call():
                try:
                    client_result["response"] = request(port, "/session" if a.case == "nested" else "/membrane_demo",
                                                          {"op":"restore"} if a.case == "nested" else None)
                except Exception as exc:
                    client_result["transport_error"] = type(exc).__name__ + ": " + str(exc)
            client = threading.Thread(target=call)
            client.start()
            expected = "shutdown_test: mesh_pending_held" if a.case == "nested" else "shutdown_test: md_pending_held"
            deadline = time.monotonic() + 5
            while expected not in (out / "engine.stdout.log").read_text(errors="replace"):
                assert time.monotonic() < deadline, "missing real pending witness: INCONCLUSIVE"
                time.sleep(.01)
            result["pending_witness"] = expected
        result["window_before_close"] = bool(user.IsWindow(hwnd))
        assert result["window_before_close"]
        assert user.PostMessageW(hwnd, 0x0010, 0, 0), "owned WM_CLOSE failed"
        try:
            result["exit_code"] = proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            result["watchdog"] = True
            proc.kill()
            result["exit_code"] = proc.wait()
        if client:
            client.join(timeout=13)
            assert not client.is_alive(), "owned client failed to finish"
            result["client"] = client_result
        result["window_after_close"] = bool(user.IsWindow(hwnd))
        log = (out / "engine.stdout.log").read_text(errors="replace")
        markers = ["shutdown: admission_closed", "shutdown: boot_joined", "shutdown: http_stopped", "shutdown: engine_shutdown"]
        positions = [log.find(m) for m in markers]
        result["ordered_markers"] = all(i >= 0 for i in positions) and positions == sorted(positions)
        assert result["exit_code"] == 0 and not result.get("watchdog")
        assert result["ordered_markers"] and not result["window_after_close"]
        if a.instrumented:
            assert 'shutdown_test: late_api {"ok":false,"error":"shutdown in progress"}' in log
        if a.instrumented and a.case == "boot":
            assert "shutdown_test: boot_wait_entered" in log, "boot wait not witnessed"
            assert "session: boot restore ->" not in log, "boot already passed delay: INCONCLUSIVE"
        if a.case in ("pending", "nested"):
            endpoint = "/mesh_bin" if a.case == "nested" else "/membrane_demo"
            assert "shutdown_test: cancelled " + endpoint in log
            assert not client_result.get("response", {}).get("ok", False)
        if a.case == "nested":
            assert 'shutdown_test: session_result {"ok":false,"replayed":0,"failed":1,' in log
        result["passed"] = True
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        result["passed"] = False
    finally:
        if proc.poll() is None:
            for hwnd, _ in windows(proc.pid): user.PostMessageW(hwnd, 0x0010, 0, 0)
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                result["cleanup_watchdog"] = True
                proc.kill()
                proc.wait()
        if client: client.join(timeout=13)
        (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("shaders", "state")}, indent=2))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
