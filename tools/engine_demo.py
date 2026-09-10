"""Persistent Tk companion for the frozen GPU membrane demo.

The native engine remains the renderer.  This module owns only its explicitly
launched process (or attaches read-only to an explicit manifest) and sends the
existing membrane demo protocol from worker threads.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import time
import urllib.error
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


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


class DemoSession:
    """Lifecycle and interruptible one-step scheduler, independent of Tk."""
    def __init__(self, transport: DemoTransport, root_dir: Path,
                 process=None, attached: bool = False,
                 manifest: Path | None = None,
                 callback: Callable[[str], None] | None = None):
        self.transport = transport
        self.root_dir = root_dir
        self.process = process
        self.attached = attached
        self.manifest = manifest
        self.callback = callback or (lambda _msg: None)
        self.running = False
        self._closed = False
        self._lock = threading.Lock()

    def _say(self, message: str) -> None:
        self.callback(message)

    def initialize(self) -> None:
        self._background("initializing", self.transport.initialize)

    def status(self) -> None:
        self._background("status", self.transport.status)

    def reset(self) -> None:
        self._background("reset", lambda: self.transport.control("reset"))

    def gamma(self, value: float) -> None:
        self._background("gamma", lambda: self.transport.control("gamma", gamma=value))

    def pause(self) -> None:
        with self._lock:
            self.running = False
        self._background("pause", lambda: self.transport.control("pause"))

    def run(self, steps: int = 126) -> None:
        with self._lock:
            if self._closed or self.running:
                return
            self.running = True
        self._schedule_step(max(0, int(steps)))

    def _schedule_step(self, remaining: int) -> None:
        if remaining <= 0:
            with self._lock:
                self.running = False
            self._say("run complete")
            return
        with self._lock:
            if self._closed or not self.running:
                return
        threading.Thread(target=self._step_worker, args=(remaining,), daemon=True).start()

    def _step_worker(self, remaining: int) -> None:
        try:
            result = self.transport.control("step", n_steps=1)
            self._say("step: " + _status_line(result))
        except Exception as exc:
            with self._lock:
                self.running = False
            self._say("ERROR: " + str(exc))
            return
        with self._lock:
            keep_going = self.running and not self._closed
        if keep_going:
            # Yield between requests so Pause is observed even on a fast engine.
            threading.Timer(0.01, self._schedule_step,
                            args=(remaining - 1,)).start()

    def _background(self, label: str, fn) -> None:
        def work():
            try:
                self._say(label + ": " + _status_line(fn()))
            except Exception as exc:
                self._say("ERROR: " + str(exc))
        threading.Thread(target=work, daemon=True).start()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self.running = False
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if not self.attached and self.manifest is not None and self.manifest.exists():
            try:
                data = json.loads(self.manifest.read_text(encoding="utf-8"))
                data["status"] = "stopped"
                self.manifest.write_text(json.dumps(data, indent=2) + "\n",
                                         encoding="utf-8")
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                pass


def _status_line(payload: dict) -> str:
    status = payload.get("status", payload)
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


def _launch(exe: Path, port: int, runtime: Path) -> tuple[subprocess.Popen, Path]:
    exe = exe.resolve()
    if not exe.is_file():
        raise ValueError(f"executable not found: {exe}")
    runtime.mkdir(parents=True, exist_ok=True)
    manifest = runtime / "manifest.json"
    if manifest.exists():
        try:
            old = json.loads(manifest.read_text(encoding="utf-8"))
            if old.get("status") == "running" and _pid_alive(int(old.get("pid", 0))):
                raise ValueError(f"runtime already owned by pid {old['pid']}: {manifest}")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            if isinstance(exc, ValueError) and "already owned" in str(exc):
                raise
    proc = subprocess.Popen([str(exe), str(port), "--no-restore"], cwd=runtime,
                            stdout=(runtime / "engine.stdout.log").open("ab"),
                            stderr=(runtime / "engine.stderr.log").open("ab"))
    _write_manifest(manifest, exe, port, proc.pid)
    return proc, manifest


def _read_manifest(path: Path) -> tuple[DemoTransport, Path]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not data.get("base"):
        raise ValueError("invalid demo manifest")
    if not str(data["base"]).startswith("http://127.0.0.1:"):
        raise ValueError("manifest base must be loopback")
    if not _pid_alive(int(data.get("pid", 0))):
        raise ValueError("manifest process is not live")
    return DemoTransport(str(data["base"])), path.parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--exe", type=Path)
    group.add_argument("--attach", type=Path)
    ap.add_argument("--port", type=int, required=False)
    ap.add_argument("--runtime-dir", type=Path)
    ap.add_argument("--steps", type=int, default=126)
    args = ap.parse_args(argv)
    if args.exe is not None and args.port is None:
        ap.error("--port is required with --exe")
    if args.attach is not None and args.port is not None:
        ap.error("--port is only valid with --exe")

    process = None
    if args.exe is not None:
        runtime = (args.runtime_dir or args.exe.parent / "demo_runtime").resolve()
        process, manifest = _launch(args.exe, args.port, runtime)
        transport = DemoTransport(f"http://127.0.0.1:{args.port}")
        manifest_path = manifest
    else:
        transport, runtime = _read_manifest(args.attach.resolve())
        manifest_path = args.attach.resolve()

    import tkinter as tk
    root = tk.Tk()
    root.title("Chimera membrane demo")
    text = tk.StringVar(value="connecting…")
    tk.Label(root, textvariable=text, width=82, anchor="w").pack(padx=12, pady=10)
    messages = Queue()
    session = DemoSession(transport, runtime, process=process,
                          attached=args.attach is not None,
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
    for label, action in (("Initialize B2", session.initialize), ("Run", lambda: session.run(args.steps)),
                          ("Pause", session.pause), ("Reset", session.reset),
                          ("Status", session.status)):
        tk.Button(buttons, text=label, command=action, width=14).pack(side="left", padx=3)
    gamma = tk.DoubleVar(value=1.0)
    tk.Scale(root, variable=gamma, from_=0.0, to=2.0, resolution=0.1,
             orient="horizontal", length=380, label="gamma (J/m²)",
             command=lambda _v: None).pack()
    tk.Button(root, text="Apply gamma", command=lambda: session.gamma(gamma.get())).pack(pady=4)
    root.protocol("WM_DELETE_WINDOW", lambda: (session.close(), root.destroy()))
    def probe():
        try:
            transport.ready()
            messages.put("engine ready — click Initialize B2")
        except Exception as exc:
            messages.put("ERROR: " + str(exc))
            if process is not None:
                session.close()
    threading.Thread(target=probe, daemon=True).start()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
