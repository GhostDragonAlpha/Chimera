"""Owned-engine lifecycle runner for engine-vulkan-cleanup-02 (cases V0-V4).

Adapted from the PR27 lane's native_visual_run.py (same owned-window discipline:
only test-owned HWNDs are queried, moved, closed, or captured). Extended with the
preregistered resize generations, /glass capture, membrane-demo reset/step, and
ordered WM_CLOSE shutdown. stderr is retained verbatim — validation errors in it
are the decisive measurement, never filtered here.

The executable is staged unchanged with its shaders into an isolated runtime dir.
"""
from __future__ import annotations

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
import time
import urllib.request
from datetime import datetime, timezone

_PARENT = Path(__file__).resolve().parent.parent / "engine_shutdown_order" / "parent_runtime" / "owned_visual"
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("owned_backdrop", _PARENT / "owned_backdrop.py")
ob = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(ob)
OwnedBackdrop, capture_client = ob.OwnedBackdrop, ob.capture_client
hwnd_owner, post_owned_close = ob.hwnd_owner, ob.post_owned_close
require_owned_hwnd, window_rect, sha256_file = ob.require_owned_hwnd, ob.window_rect, ob.sha256_file

LAYOUTS = [(64, 64, 1280, 720), (64, 64, 1000, 640), (64, 64, 1180, 680)]  # placement + 2 resize generations
SHUTDOWN_MARKERS = [
    "shutdown: admission_closed",
    "shutdown: boot_joined",
    "shutdown: http_stopped",
    "shutdown: engine_shutdown",
]
WATCHDOG_SECONDS = 10
user = c.WinDLL("user32", use_last_error=True)
user.SetProcessDPIAware()
user.IsWindowVisible.argtypes = [w.HWND]
user.IsWindow.argtypes = [w.HWND]
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.SetWindowPos.argtypes = [w.HWND, w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.UINT]
user.ShowWindow.argtypes = [w.HWND, c.c_int]
WM_CLOSE = 0x0010
callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def windows(pid: int) -> list[tuple[int, tuple[int, int, int, int]]]:
    found = []

    @callback_type
    def visit(hwnd, _):
        if hwnd_owner(int(hwnd)) == pid and user.IsWindowVisible(hwnd):
            rect = window_rect(int(hwnd))
            if rect[2] > rect[0] and rect[3] > rect[1]:
                found.append((int(hwnd), rect))
        return True

    user.EnumWindows(visit, 0)
    return sorted(found, key=lambda item: ((item[1][2] - item[1][0]) *
                                           (item[1][3] - item[1][1])), reverse=True)


def http_json(port: int, method: str, path: str, body=None, timeout: float = 35.0):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def http_bytes(port: int, path: str, timeout: float = 15.0) -> bytes:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as response:
        return response.read()


def tetrahedron_demo() -> bytes:
    """Synthetic membrane demo upload: magic u32, nv, nf, centre, gamma f64, lift f32, reserved u32,
    then pos f32[nv*3], idx u32[nf*3], csr_offsets u32[nv+1], csr_corners u32[nf*3], gamma f32[nf]."""
    nv, nf, centre = 4, 4, 0
    gamma_f64, lift = 0.05, 0.0
    positions = [(0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (0.5, -0.5, -0.5)]
    faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    offsets = [0, 3, 6, 9, 12]
    corners = [v for f in faces for v in f]
    head = struct.pack("<IIIIdfI", 0x3130444D, nv, nf, centre, gamma_f64, lift, 0)
    payload = struct.pack(f"<{nv*3}f", *[x for p in positions for x in p])
    payload += struct.pack(f"<{nf*3}I", *[v for f in faces for v in f])
    payload += struct.pack(f"<{nv+1}I", *offsets)
    payload += struct.pack(f"<{nf*3}I", *corners)
    payload += struct.pack(f"<{nf}f", *([gamma_f64] * nf))
    return head + payload


def ordered_shutdown(log: str) -> tuple[bool, list[int]]:
    positions = [log.find(marker) for marker in SHUTDOWN_MARKERS]
    return all(position >= 0 for position in positions) and positions == sorted(positions), positions


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-name", required=True)
    parser.add_argument("--port", type=int, default=8104)
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    exe = args.exe.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing existing evidence directory: {output}")
    if not exe.is_file() or not (exe.parent / "shaders").is_dir():
        raise FileNotFoundError("supplied executable or adjacent shaders are missing")
    if Path(args.runtime_name).name != args.runtime_name:
        raise ValueError("runtime-name must be one path component")
    output.mkdir(parents=True)
    runtime = repo / ".tmp" / "engine_runtime" / args.runtime_name
    runtime.mkdir(parents=True, exist_ok=False)
    staged = runtime / exe.name
    shutil.copy2(exe, staged)
    shutil.copytree(exe.parent / "shaders", runtime / "shaders")

    shader_hashes = {
        str(path.relative_to(runtime)): sha256_file(path)
        for path in sorted((runtime / "shaders").glob("*.spv"))
    }
    source = {
        "main_cpp_sha256": sha256_file(repo / "ChimeraEngine/engine/main.cpp"),
        "engine_cpp_sha256": sha256_file(repo / "ChimeraEngine/engine/engine.cpp"),
        "engine_hpp_sha256": sha256_file(repo / "ChimeraEngine/engine/engine.hpp"),
        "ui_cpp_sha256": sha256_file(repo / "ChimeraEngine/engine/ui.cpp"),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "shader_hashes": shader_hashes,
        "shader_manifest_sha256": hashlib.sha256(
            json.dumps(shader_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    result = {
        "schema": "chimera-vulkan-resource-lifetime-case-v1",
        "declared_layouts_xywh": LAYOUTS,
        "watchdog_seconds": WATCHDOG_SECONDS,
        "source": source,
        "command": [str(staged), str(args.port), "--no-restore"],
        "validation": {
            "layer": "VK_LAYER_KHRONOS_validation (engine-enabled when present, engine.cpp:474-500)",
            "stderr_is_verbatim": True,
            "suppression": "none",
        },
        "cases": {},
    }
    backdrop = None
    proc = None
    try:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(("127.0.0.1", args.port))

        backdrop = OwnedBackdrop(LAYOUTS[0]).start()
        backdrop_identity = backdrop.identity()
        result["backdrop"] = backdrop_identity
        result["backdrop_reference"] = capture_client(
            backdrop.hwnd, backdrop.pid, output / "backdrop_reference.png", "backdrop reference")

        env = os.environ.copy()
        env.pop("CHIMERA_SHUTDOWN_TEST_HOLD", None)
        stdout_path = output / "engine.stdout.log"
        stderr_path = output / "engine.stderr.log"
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            proc = subprocess.Popen(result["command"], cwd=runtime, env=env,
                                    stdout=stdout, stderr=stderr,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        engine = {"pid": proc.pid, "exe_sha256": sha256_file(staged), "staged_exe": str(staged)}
        result["engine"] = engine

        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise AssertionError("native process exited during startup")
            visible = windows(proc.pid)
            if visible:
                try:
                    state = http_json(args.port, "GET", "/state", timeout=1.0)
                    break
                except Exception:
                    pass
            time.sleep(0.05)
        else:
            raise AssertionError("startup did not produce an owned window and HTTP readiness")
        result["cases"]["V0_startup"] = {"passed": True, "state_keys": sorted(state.keys()),
                                         "state_sha256": hashlib.sha256(
                                             json.dumps(state, sort_keys=True).encode()).hexdigest()}

        hwnd = visible[0][0]
        engine["hwnd"] = hwnd
        require_owned_hwnd(hwnd, proc.pid, "engine")
        with socket.socket() as probe2:
            probe2.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            try:
                probe2.bind(("127.0.0.1", args.port))
                raise AssertionError("listener is not the engine process")
            except OSError:
                pass  # bind refused because the engine owns the port
        user.ShowWindow(w.HWND(hwnd), 9)

        rects = []
        for (x, y, wd, ht) in LAYOUTS:
            if not user.SetWindowPos(w.HWND(hwnd), w.HWND(-1), x, y, wd, ht, 0x0040):
                raise c.WinError(c.get_last_error(), "SetWindowPos(owned engine)")
            rects.append(window_rect(hwnd))
            time.sleep(1.2)  # let WM_SIZE -> Engine::resize complete a presented frame
        engine["resize_rects_ltrb"] = rects
        result["cases"]["V1_resize"] = {"passed": True, "generations": len(LAYOUTS),
                                        "rects_ltrb": rects,
                                        "window_visible": bool(user.IsWindowVisible(w.HWND(hwnd)))}

        deadline = time.monotonic() + 10
        glass = b""
        while time.monotonic() < deadline:
            try:
                glass = http_bytes(args.port, "/glass")
                if glass.startswith(b"\x89PNG\r\n\x1a\n"):
                    break
            except Exception:
                pass
            time.sleep(0.1)
        if not glass.startswith(b"\x89PNG\r\n\x1a\n"):
            raise AssertionError("owned engine did not produce a presented /glass PNG")
        (output / "engine_before_glass.png").write_bytes(glass)
        result["cases"]["V2_capture"] = {
            "passed": True, "png_bytes": len(glass),
            "sha256": hashlib.sha256(glass).hexdigest(),
            "window_visible_at_capture": bool(user.IsWindowVisible(w.HWND(hwnd))),
            "captured_utc": utc_now()}

        demo_bytes = tetrahedron_demo()
        req = urllib.request.Request(f"http://127.0.0.1:{args.port}/membrane_demo_bin",
                                     data=demo_bytes, method="POST",
                                     headers={"Content-Type": "application/octet-stream"})
        with urllib.request.urlopen(req, timeout=35.0) as response:
            init_body = json.load(response)
        reset = http_json(args.port, "POST", "/membrane_demo", body={"op": "reset"})
        step = http_json(args.port, "POST", "/membrane_demo", body={"op": "step"})
        status = http_json(args.port, "GET", "/membrane_demo")
        glass_demo = http_bytes(args.port, "/glass")
        (output / "engine_after_demo.png").write_bytes(glass_demo)
        v3_ok = bool(init_body.get("ok") and reset.get("ok") and step.get("ok") and status.get("ok"))
        result["cases"]["V3_membrane_demo"] = {
            "passed": v3_ok,
            "upload_bytes": len(demo_bytes),
            "init_ok": bool(init_body.get("ok")), "reset_ok": bool(reset.get("ok")),
            "step_ok": bool(step.get("ok")), "status_ok": bool(status.get("ok")),
            "post_demo_png_bytes": len(glass_demo),
            "post_demo_png_sha256": hashlib.sha256(glass_demo).hexdigest(),
            "window_visible": bool(user.IsWindowVisible(w.HWND(hwnd)))}
        if not v3_ok:
            raise AssertionError(f"membrane demo case failed: {init_body} {reset} {step} {status}")

        result["window_before_close"] = bool(user.IsWindow(w.HWND(hwnd)))
        if not result["window_before_close"]:
            raise AssertionError("engine HWND disappeared before WM_CLOSE")
        post_owned_close(hwnd, proc.pid, "engine")
        try:
            result["exit_code"] = proc.wait(timeout=WATCHDOG_SECONDS)
        except subprocess.TimeoutExpired:
            result["watchdog"] = True
            proc.kill()  # exact owned process handle only; retained as a failure
            result["exit_code"] = proc.wait()
        result["window_after_close"] = bool(user.IsWindow(w.HWND(hwnd)))
        log = stdout_path.read_text(encoding="utf-8", errors="replace")
        result["ordered_markers"], result["marker_positions"] = ordered_shutdown(log)
        v4 = {"passed": result["exit_code"] == 0 and not result.get("watchdog")
              and not result["window_after_close"] and result["ordered_markers"],
              "exit_code": result["exit_code"], "watchdog": bool(result.get("watchdog")),
              "window_after_close": result["window_after_close"],
              "ordered_markers": result["ordered_markers"],
              "marker_positions": result["marker_positions"]}
        result["cases"]["V4_ordered_shutdown"] = v4

        require_owned_hwnd(backdrop.hwnd, backdrop.pid, "backdrop after close")
        after_raw = capture_client(backdrop.hwnd, backdrop.pid,
                                   output / "backdrop_after.png", "backdrop after close")
        result["backdrop_unchanged"] = after_raw["sha256"] == result["backdrop_reference"]["sha256"]
        if not result["backdrop_unchanged"]:
            raise AssertionError("owned backdrop changed between reference and post-close capture")

        err = stderr_path.read_text(encoding="utf-8", errors="replace")
        result["validation_vuid_vkDestroyDevice_05137_count"] = err.count("VUID-vkDestroyDevice-device-05137")
        result["validation_error_lines"] = sum(1 for line in err.splitlines() if "[VK ERROR]" in line)
        result["passed"] = all(case.get("passed") for case in result["cases"].values())
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["passed"] = False
    finally:
        if proc is not None and proc.poll() is None:
            for hwnd, _ in windows(proc.pid):
                try:
                    post_owned_close(hwnd, proc.pid, "engine cleanup")
                except Exception:
                    pass
            try:
                proc.wait(timeout=WATCHDOG_SECONDS)
            except subprocess.TimeoutExpired:
                result["cleanup_watchdog"] = True
                proc.kill()
                proc.wait()
        if backdrop is not None:
            try:
                backdrop.close()
            except Exception as exc:
                result["backdrop_cleanup_error"] = f"{type(exc).__name__}: {exc}"
                result["passed"] = False
        (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps({k: v for k, v in result.items() if k not in ("state", "source")},
                     indent=2))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
