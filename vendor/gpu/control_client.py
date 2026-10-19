"""Small control messages; native code retains geometry, physical state and GPU work.

Never retry a mutation: a timeout may follow a successful native application.
A client serializes requests, and callers choose its engine URL explicitly.
"""
from __future__ import annotations
import urllib.request
import urllib.error
import json
import math
import threading
from urllib.parse import urlsplit


class NativeRefusal(RuntimeError):
    pass


def number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be finite in [{low}, {high}]")
    return value


class EngineControl:
    def __init__(self, base: str, timeout: float = 60):
        url = urlsplit(base)
        if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1")
                or url.path not in ("", "/") or url.query or url.fragment or url.username):
            raise ValueError("Use an explicit local native engine URL, e.g. http://127.0.0.1:8813")
        self.base = base.rstrip("/")
        self._timeout = timeout
        self._lock = threading.Lock()
        self.membrane = Membrane(self)
        self.matter = Matter(self)
        self.physics = Physics(self)
        self.assembly = Assembly(self)

    def __enter__(self): return self
    def __exit__(self, *_): self.close()
    def close(self): pass  # Native HTTP server closes each response; no persistent connection.

    def request(self, method, path, payload=None, *, binary=False):
        if not path.startswith("/") or "\r" in path or "\n" in path:
            raise ValueError("Invalid native route")
        data = payload if isinstance(payload, bytes) else (
            json.dumps(payload, allow_nan=False, separators=(",", ":")).encode()
            if payload is not None else None)
        headers = ({"Content-Type": "application/octet-stream" if isinstance(payload, bytes)
                    else "application/json"} if data is not None else {})
        request = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        with self._lock:
            try:
                # Match the existing native client's connection-close request path.
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    raw = response.read()
            except urllib.error.HTTPError as error:
                raise NativeRefusal(f"{method} {path}: HTTP {error.code}: {error.read()[:512]!r}") from error
            if binary: return raw
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise NativeRefusal(f"{path}: native reply must be an object")
            if result.get("ok") is False:
                raise NativeRefusal(f"{path}: {result.get('error', result)}")
            return result

    def frame(self):
        raw = self.request("GET", "/frame", binary=True)
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise NativeRefusal("Native frame response is not PNG")
        return raw

    def telemetry(self): return self.request("GET", "/studio_chrome")


class Membrane:
    def __init__(self, engine): self.engine = engine
    def upload(self, packet: bytes):
        if not isinstance(packet, bytes): raise ValueError("Upload needs immutable MD01 bytes")
        return self.engine.request("POST", "/membrane_demo_bin", packet)
    def load_fixture(self, case="case_gamma1"):
        # Reuse the project's pinned geometry/CSR and binary protocol exactly.
        from tools.membrane_demo_client import load_b2, md01_packet
        if case not in ("case_gamma1", "case_gamma2"):
            raise ValueError("Use a pinned B2 gamma case")
        fixture = load_b2(case)
        return self.upload(md01_packet(fixture, float(case[-1])))
    def state(self): return self.engine.request("GET", "/membrane_demo")
    def reset(self): return self.engine.request("POST", "/membrane_demo", {"op": "reset"})
    def pause(self): return self.engine.request("POST", "/membrane_demo", {"op": "pause"})
    def tension(self, gamma):
        number(gamma, "gamma", 0.000001, 1000000)
        result = self.engine.request("POST", "/membrane_demo", {"op": "gamma", "gamma": gamma})
        state = result.get("status", result)
        if "REJECTED" in str(state.get("last_control", "")):
            raise NativeRefusal("Native material admission rejected gamma")
        return result
    def step(self, count=1):
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 4096:
            raise ValueError("Step count must be an integer in [1, 4096]")
        # Native 'step' ignores n_steps; native 'run' performs a synchronous batch.
        return self.engine.request("POST", "/membrane_demo",
                                   {"op": "step" if count == 1 else "run", "n_steps": count})


class Matter:
    def __init__(self, engine): self.engine = engine
    def state(self): return self.engine.request("GET", "/matter")
    def readback(self): return self.engine.request("GET", "/matter_state")
    def configure(self, *, on, iters=None, k=None):
        if not isinstance(on, bool): raise ValueError("on must be boolean")
        data = {"on": on}
        if iters is not None: data["iters"] = number(iters, "iters", 0, 64)
        if k is not None: data["k"] = number(k, "k", 0, 1)
        return self.engine.request("POST", "/matter", data)


class Physics:
    def __init__(self, engine): self.engine = engine
    def state(self): return self.engine.request("GET", "/earth_state")
    def intent(self, **parameters):
        # The loaded native scene owns units, schema, admission and constraints.
        # Do not expose direct vertex/pose writes as physical integration.
        allowed = {"paused", "reset", "power", "shoulder_drive", "elbow_drive",
                   "shoulder_target_deg", "elbow_target_deg", "hand_force_N"}
        if not parameters or parameters.keys() - allowed:
            raise ValueError("Use native coupled-arm intent controls")
        json.dumps(parameters, allow_nan=False)
        return self.engine.request("POST", "/earth_state", parameters)
    def surface(self, **parameters):
        if not parameters: return self.engine.request("GET", "/science_surface")
        json.dumps(parameters, allow_nan=False)
        return self.engine.request("POST", "/science_surface", parameters)


class Assembly:
    """Existing native B2 Lego-style part/material/connection transactions.

    Native admission remains the authority for mass, inertia, contact and units.
    No mesh positions are updated by this Python adapter.
    """
    def __init__(self, engine): self.engine = engine
    def state(self): return self.engine.request("GET", "/tick_b2_state")
    def clock(self): return self.engine.request("GET", "/tick_b2_clock")
    def state_hash(self): return self.engine.request("GET", "/tick_b2_hash")["state_hash"]
    def command(self, operation, document):
        allowed = {"admit", "place", "remove", "patch", "weld", "weld_remove",
                   "load", "inspect", "render_lod", "gravity", "support", "pause"}
        if operation not in allowed or not isinstance(document, dict):
            raise ValueError("Use a native B2 transaction and an object document")
        json.dumps(document, allow_nan=False)
        return self.engine.request("POST", "/tick_b2_" + operation, document)
    def pause(self, on=True):
        if not isinstance(on, bool): raise ValueError("Pause requires a boolean")
        return self.command("pause", {"on": on})
    def admit(self, scene): return self.command("admit", scene)
    def place(self, part): return self.command("place", part)
    def patch(self, **material): return self.command("patch", material)
    def weld(self, connection): return self.command("weld", connection)
    def remove(self, part_id): return self.command("remove", {"id": part_id})
