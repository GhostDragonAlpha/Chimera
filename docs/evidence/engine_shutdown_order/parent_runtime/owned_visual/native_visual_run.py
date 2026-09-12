"""Quiet-close visual follow-up using only test-owned window captures.

No engine is built or reconfigured here. The supplied executable and its shaders
are copied into an isolated runtime directory and invoked unchanged.
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
import subprocess
import time
import urllib.request
from datetime import datetime, timezone

from owned_backdrop import (OwnedBackdrop, capture_client, hwnd_owner,
                            post_owned_close, require_owned_hwnd, sha256_file,
                            window_rect)


LAYOUT_RECT = (64, 64, 1280, 720)  # inherited from parent_runtime/native_run.py
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
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.SetWindowPos.argtypes = [w.HWND, w.HWND, c.c_int, c.c_int,
                              c.c_int, c.c_int, w.UINT]
user.ShowWindow.argtypes = [w.HWND, c.c_int]
callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def request_json(port: int, path: str, timeout: float = 1.0) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as response:
        return json.load(response)


def ordered_shutdown(log: str) -> tuple[bool, list[int]]:
    positions = [log.find(marker) for marker in SHUTDOWN_MARKERS]
    return all(position >= 0 for position in positions) and positions == sorted(positions), positions


def bind_capture(capture: dict, *, role: str, source: dict, engine: dict,
                 backdrop: dict) -> dict:
    """Bind an image to the identities needed to interpret it later."""
    return {
        **capture,
        "role": role,
        "source": source,
        "engine": {key: engine[key] for key in ("pid", "hwnd", "exe_sha256")},
        "backdrop": {key: backdrop[key] for key in
                     ("pid", "hwnd", "title", "class_name", "paint_revision")},
    }


def _listener_pid(port: int) -> int:
    command = f"(Get-NetTCPConnection -LocalPort {port} -State Listen).OwningProcess"
    value = subprocess.check_output(["powershell", "-NoProfile", "-Command", command],
                                    text=True).strip()
    rows = {int(row) for row in value.splitlines() if row.strip()}
    if len(rows) != 1:
        raise AssertionError(f"listener identity is ambiguous: {sorted(rows)!r}")
    return rows.pop()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-name", required=True)
    parser.add_argument("--port", type=int, default=8102)
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
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "helper_sha256": sha256_file(Path(__file__).with_name("owned_backdrop.py")),
        "shader_hashes": shader_hashes,
        "shader_manifest_sha256": sha256_bytes(
            json.dumps(shader_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ),
    }
    result = {
        "schema": "chimera-owned-backdrop-shutdown-v1",
        "declared_layout_xywh": LAYOUT_RECT,
        "watchdog_seconds": WATCHDOG_SECONDS,
        "source": source,
        "command": [str(staged), str(args.port), "--no-restore"],
        "capture_scope": "specified HWND client only; never desktop",
    }
    backdrop = None
    proc = None
    try:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(("127.0.0.1", args.port))

        backdrop = OwnedBackdrop(LAYOUT_RECT).start()
        backdrop_identity = backdrop.identity()
        result["backdrop"] = backdrop_identity
        reference = capture_client(backdrop.hwnd, backdrop.pid,
                                   output / "backdrop_reference.png", "backdrop reference")

        env = os.environ.copy()
        env.pop("CHIMERA_SHUTDOWN_TEST_HOLD", None)
        stdout_path = output / "engine.stdout.log"
        stderr_path = output / "engine.stderr.log"
        stdout = stdout_path.open("wb")
        stderr = stderr_path.open("wb")
        try:
            proc = subprocess.Popen(result["command"], cwd=runtime, env=env,
                                    stdout=stdout, stderr=stderr,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        finally:
            stdout.close()
            stderr.close()
        engine = {
            "pid": proc.pid,
            "exe_sha256": sha256_file(staged),
            "staged_exe": str(staged),
        }
        result["engine"] = engine

        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise AssertionError("native process exited during startup")
            visible = windows(proc.pid)
            if visible:
                try:
                    result["state"] = request_json(args.port, "/state")
                    break
                except Exception:
                    pass
            time.sleep(0.05)
        else:
            raise AssertionError("startup did not produce an owned window and HTTP readiness")

        hwnd = visible[0][0]
        engine["hwnd"] = hwnd
        engine["initial_window_rect_ltrb"] = window_rect(hwnd)
        require_owned_hwnd(hwnd, proc.pid, "engine")
        result["listener_pid"] = _listener_pid(args.port)
        if result["listener_pid"] != proc.pid:
            raise AssertionError("loopback listener belongs to another process")

        # Only the verified engine HWND is positioned. No unrelated HWND is queried,
        # moved, hidden, closed, or captured.
        user.ShowWindow(w.HWND(hwnd), 9)
        result["engine_show_called_utc"] = utc_now()
        x, y, width, height = LAYOUT_RECT
        if not user.SetWindowPos(w.HWND(hwnd), w.HWND(-1), x, y, width, height, 0x0040):
            raise c.WinError(c.get_last_error(), "SetWindowPos(owned engine)")
        engine["capture_window_rect_ltrb"] = window_rect(hwnd)

        # /glass is the before-close image. It is produced by the engine's
        # swapchain readback and cannot contain pixels from foreign windows.
        deadline = time.monotonic() + 5
        glass = b""
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{args.port}/glass", timeout=1) as response:
                    glass = response.read()
                if glass.startswith(b"\x89PNG\r\n\x1a\n"):
                    break
            except Exception:
                pass
            time.sleep(0.05)
        if not glass.startswith(b"\x89PNG\r\n\x1a\n"):
            raise AssertionError("owned engine did not produce a presented /glass PNG")
        before_path = output / "engine_before_glass.png"
        before_path.write_bytes(glass)
        before_raw = {
            "path": str(before_path),
            "sha256": sha256_bytes(glass),
            "capture_api": "engine GET /glass swapchain readback",
            "producer_pid": proc.pid,
            "associated_visible_hwnd": hwnd,
            "window_visible_at_capture": bool(user.IsWindowVisible(w.HWND(hwnd))),
            "window_rect_ltrb": window_rect(hwnd),
            "captured_utc": utc_now(),
            "identity_limit": (
                "PID-owned listener and visible HWND bind this engine-produced readback; "
                "the image alone is not process or window identity proof"
            ),
        }
        if not before_raw["window_visible_at_capture"]:
            raise AssertionError("owned engine HWND was not visible at /glass capture")
        result["before"] = bind_capture(before_raw, role="engine-before-WM_CLOSE",
                                         source=source, engine=engine,
                                         backdrop=backdrop_identity)

        result["window_before_close"] = bool(user.IsWindow(w.HWND(hwnd)))
        if not result["window_before_close"]:
            raise AssertionError("engine HWND disappeared before WM_CLOSE")
        result["wm_close_posted_utc"] = utc_now()
        post_owned_close(hwnd, proc.pid, "engine")
        try:
            result["exit_code"] = proc.wait(timeout=WATCHDOG_SECONDS)
        except subprocess.TimeoutExpired:
            result["watchdog"] = True
            proc.kill()  # exact owned process handle only; retained as a failure
            result["exit_code"] = proc.wait()

        result["process_exit_observed_utc"] = utc_now()
        result["window_after_close"] = bool(user.IsWindow(w.HWND(hwnd)))
        result["process_after_close"] = proc.poll()
        log = stdout_path.read_text(encoding="utf-8", errors="replace")
        result["ordered_markers"], result["marker_positions"] = ordered_shutdown(log)
        if result["exit_code"] != 0 or result.get("watchdog"):
            raise AssertionError("native process did not exit normally before watchdog")
        if result["window_after_close"]:
            raise AssertionError("engine HWND survived process exit")
        if not result["ordered_markers"]:
            raise AssertionError("shutdown markers are absent or out of order")

        require_owned_hwnd(backdrop.hwnd, backdrop.pid, "backdrop after close")
        after_raw = capture_client(backdrop.hwnd, backdrop.pid,
                                   output / "backdrop_after.png", "backdrop after close")
        after_raw["captured_utc"] = utc_now()
        result["after"] = bind_capture(after_raw, role="owned-backdrop-after-engine-exit",
                                        source=source, engine=engine,
                                        backdrop=backdrop_identity)
        result["backdrop_reference"] = reference
        result["backdrop_unchanged"] = after_raw["sha256"] == reference["sha256"]
        if not result["backdrop_unchanged"]:
            raise AssertionError("owned backdrop changed between reference and post-close capture")
        result["passed"] = True
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["passed"] = False
    finally:
        if proc is not None and proc.poll() is None:
            owned = windows(proc.pid)
            for hwnd, _ in owned:
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

    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("state", "source")}, indent=2))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
