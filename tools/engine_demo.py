"""Persistent Tk companion for the frozen GPU membrane demo.

The native engine remains the renderer. This module owns only its explicitly
launched process and sends the existing membrane demo protocol from worker
threads.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
from queue import Empty, Queue
from pathlib import Path
from typing import Callable

from membrane_demo_client import load_b2, md01_packet


class DemoTransport:
    def __init__(self, base: str, opener=urllib.request.urlopen):
        self.base = base.rstrip("/")
        self._opener = opener

    def request(self, method: str, path: str, body: bytes | None = None,
                content_type: str = "application/json") -> dict:
        req = urllib.request.Request(self.base + path, data=body, method=method)
        if body is not None:
            req.add_header("Content-Type", content_type)
        with self._opener(req, timeout=30) as response:
            raw = response.read()
        return json.loads(raw.decode("utf-8"))

    def ready(self) -> dict:
        return self.request("GET", "/state")

    def initialize(self) -> dict:
        b2 = load_b2("case_gamma1")
        return self.request("POST", "/membrane_demo_bin", md01_packet(b2, 1.0),
                            "application/octet-stream")

    def status(self) -> dict:
        return self.request("GET", "/membrane_demo")

    def control(self, op: str, **values) -> dict:
        payload = {"op": op, **values}
        return self.request("POST", "/membrane_demo",
                            json.dumps(payload).encode("utf-8"))


def _pid_image(pid: int) -> str | None:
    """Read a process image path without sending it a control signal."""
    if pid <= 0:
        return None
    if os.name != "nt":
        try:
            return os.readlink(f"/proc/{pid}/exe")
        except OSError:
            return None
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                  wintypes.LPWSTR,
                                                  ctypes.POINTER(wintypes.DWORD)]
        k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL
        h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return None
        try:
            n = ctypes.c_ulong(32768)
            buf = ctypes.create_unicode_buffer(n.value)
            if not k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                return None
            return buf.value
        finally:
            k.CloseHandle(h)
    except (OSError, AttributeError):
        return None


def _pid_alive(pid: int) -> bool:
    return _pid_image(pid) is not None


def _port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


class DemoSession:
    """Lifecycle and interruptible one-step scheduler, independent of Tk."""
    def __init__(self, transport: DemoTransport, root_dir: Path,
                 process=None,
                 manifest: Path | None = None,
                 callback: Callable[[str], None] | None = None):
        self.transport = transport
        self.root_dir = root_dir
        self.process = process
        self.manifest = manifest
        self.callback = callback or (lambda _msg: None)
        self.running = False
        self._closed = False
        self._lock = threading.Lock()
        self._control_lock = threading.Lock()
        self._run_generation = 0

    def _say(self, message: str) -> None:
        self.callback(message)

    def initialize(self) -> None:
        self._cancel_run()
        self._background("initializing", self.transport.initialize)

    def status(self) -> None:
        self._background("status", self.transport.status)

    def reset(self) -> None:
        self._cancel_run()
        self._background("reset", lambda: self.transport.control("reset"))

    def gamma(self, value: float) -> None:
        self._cancel_run()
        self._background("gamma", lambda: self.transport.control("gamma", gamma=value))

    def _cancel_run(self) -> None:
        with self._lock:
            self.running = False
            self._run_generation += 1

    def pause(self) -> None:
        with self._lock:
            self.running = False
            self._run_generation += 1
        self._background("pause", lambda: self.transport.control("pause"))

    def step(self) -> None:
        self._background("step", lambda: self.transport.control("step", n_steps=1))

    def run(self, steps: int = 126) -> None:
        with self._lock:
            if self._closed or self.running:
                return
            self.running = True
            self._run_generation += 1
            generation = self._run_generation
        self._schedule_step(max(0, int(steps)), generation)

    def _schedule_step(self, remaining: int, generation: int) -> None:
        with self._lock:
            if self._closed or not self.running or generation != self._run_generation:
                return
        if remaining <= 0:
            with self._lock:
                if generation != self._run_generation or self._closed:
                    return
                self.running = False
            self._say("run complete")
            return
        threading.Thread(target=self._step_worker, args=(remaining, generation), daemon=True).start()

    def _step_worker(self, remaining: int, generation: int) -> None:
        try:
            with self._control_lock:
                with self._lock:
                    if self._closed or not self.running or generation != self._run_generation:
                        return
                result = self.transport.control("step", n_steps=1)
            nested = result.get("status") if isinstance(result, dict) else None
            refused = (isinstance(result, dict) and result.get("ok") is False)
            if isinstance(nested, dict) and nested.get("ok") is False:
                refused = True
            if refused:
                raise RuntimeError(str(result.get("error", "step request refused")))
            self._say("step: " + _status_line(result))
            terminal = result.get("terminal_state")
            if not terminal and isinstance(result.get("status"), dict):
                terminal = result["status"].get("terminal_state")
            if terminal:
                with self._lock:
                    if generation == self._run_generation:
                        self.running = False
        except Exception as exc:
            with self._lock:
                if generation == self._run_generation:
                    self.running = False
            self._say("ERROR: " + str(exc))
            return
        with self._lock:
            keep_going = (self.running and not self._closed
                          and generation == self._run_generation)
        if keep_going:
            # Yield between requests so Pause is observed even on a fast engine.
            threading.Timer(0.01, self._schedule_step,
                            args=(remaining - 1, generation)).start()

    def _background(self, label: str, fn) -> None:
        def work():
            try:
                with self._control_lock:
                    with self._lock:
                        if self._closed:
                            return
                    self._say(label + ": " + _status_line(fn()))
            except Exception as exc:
                self._say("ERROR: " + str(exc))
        threading.Thread(target=work, daemon=True).start()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self.running = False
        _stop_owned(self.process)
        if self.manifest is not None and self.manifest.exists():
            try:
                data = json.loads(self.manifest.read_text(encoding="utf-8"))
                data["status"] = "stopped"
                self.manifest.write_text(json.dumps(data, indent=2) + "\n",
                                         encoding="utf-8")
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                pass


def _status_line(payload: dict) -> str:
    if payload.get("ok") is False:
        return "ERROR: " + str(payload.get("error", "request refused"))
    status = payload.get("status", payload)
    if status.get("ok") is False:
        return "ERROR: " + str(status.get("error", "request refused"))
    if status.get("active") is False:
        return "not initialized — click Initialize B2"
    return (f"it={status.get('iteration', '?')} E={status.get('energy', '?')} "
            f"z={status.get('centre', ['?', '?', '?'])[-1]} "
            f"terminal={status.get('terminal_state', '')} "
            f"control={status.get('last_control', '')}")


def _write_manifest(path: Path, exe: Path, port: int, pid: int) -> None:
    path.write_text(json.dumps({"schema": 1, "status": "running",
                                "exe": str(exe), "pid": pid, "port": port,
                                "base": f"http://127.0.0.1:{port}",
                                "cwd": str(path.parent)}, indent=2) + "\n",
                    encoding="utf-8")


def _stop_owned(proc) -> None:
    """Terminate and reap one known Popen; tolerate slow/half-started children."""
    if proc is None:
        return
    try:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
    except (OSError, ProcessLookupError):
        pass


def _launch(exe: Path, port: int, runtime: Path | None) -> tuple[subprocess.Popen, Path]:
    exe = exe.resolve()
    if not exe.is_file():
        raise ValueError(f"executable not found: {exe}")
    if not (1 <= port <= 65535) or _port_busy(port):
        raise ValueError(f"port {port} is unavailable")
    if runtime is None:
        runtime = Path(tempfile.mkdtemp(prefix="chimera_demo_", dir=exe.parent))
    elif runtime.exists() and any(runtime.iterdir()):
        raise ValueError(f"runtime directory must be new and empty: {runtime}")
    runtime.mkdir(parents=True, exist_ok=True)
    manifest = runtime / "manifest.json"
    shaders = exe.parent / "shaders"
    if not shaders.is_dir():
        raise ValueError(f"shaders directory not found beside executable: {shaders}")
    staged_exe = runtime / exe.name
    shutil.copy2(exe, staged_exe)
    shutil.copytree(shaders, runtime / "shaders")
    proc = None
    try:
        with (runtime / "engine.stdout.log").open("ab") as stdout, \
             (runtime / "engine.stderr.log").open("ab") as stderr:
            proc = subprocess.Popen([str(staged_exe), str(port), "--no-restore"], cwd=runtime,
                                    stdout=stdout, stderr=stderr)
        _write_manifest(manifest, staged_exe, port, proc.pid)
    except Exception:
        _stop_owned(proc)
        raise
    return proc, manifest


def _wait_ready(proc: subprocess.Popen, port: int, timeout: float = 60.0) -> None:
    transport = DemoTransport(f"http://127.0.0.1:{port}")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"engine exited during startup (rc={proc.returncode})")
        try:
            transport.ready()
            return
        except Exception:
            time.sleep(0.2)
    raise TimeoutError(f"engine did not answer /state within {timeout:g}s")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--runtime-dir", type=Path)
    ap.add_argument("--steps", type=int, default=126)
    args = ap.parse_args(argv)
    process = None
    runtime = args.runtime_dir.resolve() if args.runtime_dir else None
    try:
        process, manifest_path = _launch(args.exe, args.port, runtime)
        _wait_ready(process, args.port)
    except Exception:
        _stop_owned(process)
        raise
    runtime = manifest_path.parent
    transport = DemoTransport(f"http://127.0.0.1:{args.port}")

    session = None
    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("Chimera membrane demo")
        text = tk.StringVar(value="connecting…")
        tk.Label(root, textvariable=text, width=82, anchor="w").pack(padx=12, pady=10)
        tk.Label(root, text="Optimization iterations are control steps, not physical time.",
                 anchor="w").pack(padx=12, pady=2)
        messages = Queue()
        session = DemoSession(transport, runtime, process=process,
                              manifest=manifest_path,
                              callback=messages.put)
        def pump_messages():
            try:
                while True:
                    text.set(messages.get_nowait())
            except Empty:
                pass
            root.after(50, pump_messages)
        root.after(0, pump_messages)
        buttons = tk.Frame(root); buttons.pack(padx=12, pady=4)
        for label, action in (("Initialize B2", session.initialize), ("Step", session.step),
                              ("Run", lambda: session.run(args.steps)),
                              ("Pause", session.pause), ("Reset", session.reset),
                              ("Status", session.status)):
            tk.Button(buttons, text=label, command=action, width=14).pack(side="left", padx=3)
        gamma_frame = tk.Frame(root); gamma_frame.pack(pady=4)
        tk.Label(gamma_frame, text="gamma (J/m²):").pack(side="left")
        for value in (0.0, 1.0, 2.0):
            tk.Button(gamma_frame, text=f"{value:g}", width=8,
                      command=lambda g=value: session.gamma(g)).pack(side="left", padx=2)
        root.protocol("WM_DELETE_WINDOW", lambda: (session.close(), root.destroy()))
        def probe():
            try:
                transport.ready()
                messages.put("engine ready — click Initialize B2")
            except Exception as exc:
                messages.put("ERROR: " + str(exc))
                session.close()
        threading.Thread(target=probe, daemon=True).start()
        root.mainloop()
    finally:
        if session is not None:
            session.close()
        else:
            _stop_owned(process)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
