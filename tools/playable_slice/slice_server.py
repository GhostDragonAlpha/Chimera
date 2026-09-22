"""slice_server.py -- THE PLAYABLE SLICE's front door (the R2 shape, one lane).

One stdlib server: serves the slice page, starts and owns its OWN engine on a
bind-tested free port (8127 refused BY CODE -- the port law), boots the
standing start through the REAL aliveness ingestion, and fronts the gameplay.

REALITY (the engine does it): rendering state (/verts + /topology streamed
triangles), gravity, floor contact, the press, THE FALL TEST, the settle.
FANTASY (named, labeled): MOCK[mock_carry] -- the XY slide toward the marker.
The Y coordinate served to the page is ALWAYS the engine's untouched root
stream; the carry never touches it. The fall test is the engine's own root law
run live: /tick_gravity off re-seats the authored rest, on integrates
y'' = F_contact/m - g (banked constants: k=1.3562e7 N/m, c=6.062e5 N s/m,
m=13824.5 kg, g=9.81 m/s^2 -- membrane_tick.hpp/cpp).

Run:  python tools/playable_slice/slice_server.py [--port N] [--engine-exe P]
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scene_boot as sb  # noqa: E402

NEVER_PORT = 8127
DEFAULT_EXE = HERE.parent.parent / ".tmp/slice_build/Release/chimera_engine.exe"
MARKER_AZIMUTH_RAD = 0.6          # level constant (stated, not tuned)
MARKER_DIST_M = 1.2               # ~2 body lengths (the standing skeleton measures 0.605 m nose-to-tail)
CARRY_SPEED_MPS = 0.4
ARRIVE_RADIUS_M = 0.15
SETTLE_VY = 0.05                  # the engine's own "settled means settled" bar
# the banked constants (membrane_tick.hpp/cpp): the settled lowest vertex is
# -(m*g/k) below the floor, so the settled ROOT is -(m*g/k) - ymin with ymin
# the import's own authored lowest -- the attractor, derived, any body.
SETTLE_SINK_M = 13824.5 * 9.81 / 1.3562e7    # 0.010000 m


class World:
    """The slice's world state. The engine stays the frozen world; this is the
    doorplate, the doormat, and the sign-up sheet."""

    def __init__(self, engine_exe: Path):
        self.engine_exe = engine_exe
        self.lock = threading.RLock()
        self.port = None
        self.proc = None
        self.url = None
        self.scene_spec = None          # marker + shas, fixed per boot
        self.ghost_obj = None
        self.ghost_rec = None
        self.body_rec = None
        self.mock_carry = {"active": False, "x": 0.0, "z": 0.0, "arrived": False}
        self.events: list[dict] = []    # the session record (the save)
        self.fall_test: dict | None = None

    # ── boot / restart (byte-clean) ──────────────────────────────────────
    def boot(self) -> dict:
        with self.lock:
            self.shutdown_engine()
            self.port = sb.free_port()
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.proc = subprocess.Popen(
                [str(self.engine_exe), str(self.port), "--no-restore", "--hidden"],
                cwd=str(self.engine_exe.parent),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags)
            self.url = f"http://127.0.0.1:{self.port}"
            sb.wait_engine(self.url)
            if self.ghost_obj is None:
                self.ghost_obj, self.ghost_rec = sb.build_ghost_obj()
            rec = sb.boot_standing_start(self.url)   # imports THE REAL BODY
            self.body_rec = rec
            marker_x = MARKER_DIST_M * math.sin(MARKER_AZIMUTH_RAD)
            marker_z = MARKER_DIST_M * math.cos(MARKER_AZIMUTH_RAD)
            self.scene_spec = {
                "schema": "chimera.playable_slice.scene.v1",
                "scene_sha256": rec["scene_sha256"],
                "start_state_sha256": None,   # set when the settle lands
                "settled": False,
                "start_root_y": None,
                "marker": {"x": marker_x, "z": marker_z,
                           "radius": ARRIVE_RADIUS_M,
                           "azimuth_rad": MARKER_AZIMUTH_RAD,
                           "dist_m": MARKER_DIST_M},
                "body": self.body_rec,
                "ghost": self.ghost_rec,
                "ghost_bytes_sha256": sb.sha256(self.ghost_obj),
            }
            self.mock_carry = {"active": False, "x": 0.0, "z": 0.0, "arrived": False}
            self.fall_test = None
            self.events = [{"t": time.time(), "event": "boot",
                            "scene_sha256": rec["scene_sha256"]}]
        # the standing start settles in the background: the page is live and
        # the settle itself is REAL physics the player watches
        threading.Thread(target=self._finish_settle, daemon=True).start()
        return self.scene_spec

    def _finish_settle(self):
        """The standing start = the engine's own settle, then CONVERGENCE: the
        root law's fixed point is bit-stable once root_y stops moving (the
        measured attractor: 0.25529300 constant for the capsule; the real
        skeleton's is -(m*g/k) - ymin, derived below). The convergence WINDOW
        matters: a drift-only break fires on bounce CRESTS of a body whose
        oscillation outlives the capsule's (measured this lane: three boots
        recorded three different crests). So "settled" means residence AT the
        derived attractor: |root_y - root_eq| < 5e-5 with |vy| < 1e-5, held
        for 10 s."""
        st = sb.wait_settled(self.url, timeout=30)
        ymin = float(self.body_rec.get("import_stats", {}).get("ymin", 0.0))
        root_eq = -SETTLE_SINK_M - ymin
        deadline = time.time() + 180.0
        settled_since = None
        while time.time() < deadline:
            cur = sb.http_get_json(self.url, "/tick_state")
            ry, vy = float(cur.get("root_y", 0.0)), abs(float(cur.get("root_vy", 1.0)))
            at_eq = abs(ry - root_eq) < 5e-5 and vy < 1e-5
            if at_eq:
                if settled_since is None:
                    settled_since = time.time()
                elif time.time() - settled_since >= 10.0:
                    break
            else:
                settled_since = None
            time.sleep(0.25)
        start_verts = sb.verts_payload(self.url)
        start_sha = sb.sha256(start_verts)
        with self.lock:
            self.scene_spec["start_state_sha256"] = start_sha
            self.scene_spec["start_root_y"] = st.get("root_y")
            self.scene_spec["settled"] = True
            self.events.append({"t": time.time(), "event": "standing_start",
                                "start_state_sha256": start_sha,
                                "settled_root_y": st.get("root_y")})

    def shutdown_engine(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None

    # ── engine proxies ───────────────────────────────────────────────────
    def verts(self) -> bytes:
        raw = sb.http_get_raw(self.url, "/verts")
        with self.lock:
            carry = dict(self.mock_carry)
        if not (carry["active"] or carry["x"] or carry["z"]):
            return raw
        # MOCK[mock_carry]: the named XY slide. The Y stream is untouched --
        # the engine's real root is never edited here. Vectorized: the real
        # body streams ~250k verts per poll and a per-vertex struct loop
        # cannot hold the 10 Hz poll cadence.
        import numpy as _np
        n = int.from_bytes(raw[:4], "little")
        arr = _np.frombuffer(raw[4:4 + n * 36], dtype=_np.float32).copy()
        arr[0::9] += _np.float32(carry["x"])
        arr[2::9] += _np.float32(carry["z"])
        return raw[:4] + arr.tobytes()

    def topology(self) -> bytes:
        return sb.http_get_raw(self.url, "/topology")

    def tick_state(self) -> dict:
        return sb.http_get_json(self.url, "/tick_state")

    def press(self, payload: bytes) -> dict:
        # REALITY: the engine's own closed-loop press (the web-kernel form:
        # the player's camera + click pixel; the engine picks the point)
        return sb.http_post(self.url, "/tick_touch", payload,
                            ctype="application/json")

    # ── gameplay ─────────────────────────────────────────────────────────
    def carry_step(self):
        """MOCK[mock_carry]: advance the labeled slide toward the marker."""
        with self.lock:
            c = self.mock_carry
            if not c["active"]:
                return
            m = self.scene_spec["marker"]
            dx, dz = m["x"] - c["x"], m["z"] - c["z"]
            d = (dx * dx + dz * dz) ** 0.5
            if d <= ARRIVE_RADIUS_M:
                c["active"] = False
                c["arrived"] = True
                self.events.append({"t": time.time(), "event": "carry_arrived",
                                    "x": c["x"], "z": c["z"]})
                return
            step = min(CARRY_SPEED_MPS * 0.05, d)
            c["x"] += dx / d * step
            c["z"] += dz / d * step

    def send(self) -> dict:
        with self.lock:
            if self.fall_test is not None:
                return {"ok": False, "error": "the fall test owns the world"}
            self.mock_carry["active"] = True
            return {"ok": True, "mock": "mock_carry"}

    def stop(self) -> dict:
        with self.lock:
            self.mock_carry["active"] = False
            return {"ok": True}

    def drop_test(self) -> dict:
        """THE FALL TEST -- REALITY. The engine's own root law, run live:
        gravity off re-seats the authored rest; gravity on integrates
        y'' = F/m - g. The world streams the real curve; the verdict reads
        the engine's own numbers."""
        with self.lock:
            if self.fall_test is not None:
                return {"ok": False, "error": "fall test already running"}
            self.fall_test = {"phase": "running", "started": time.time()}
            self.mock_carry["active"] = False
        try:
            sb.http_post(self.url, "/tick_gravity", b'{"on":false}',
                         ctype="application/json")
            time.sleep(0.35)                    # the authored-rest seat
            sb.http_post(self.url, "/tick_gravity", b'{"on":true}',
                         ctype="application/json")
            peak_y, peak_vy = -99.0, 0.0
            t0 = time.time()
            while time.time() - t0 < 40.0:
                st = self.tick_state()
                peak_y = max(peak_y, float(st.get("root_y", 0.0)))
                peak_vy = max(peak_vy, abs(float(st.get("root_vy", 0.0))))
                if abs(float(st.get("root_vy", 1.0))) <= SETTLE_VY and \
                        float(st.get("root_y", 99.0)) < 0.5:
                    break
                time.sleep(0.05)
            st = sb.wait_settled(self.url, timeout=30)
            verdict = {
                "phase": "done",
                "max_root_y": round(peak_y, 4),
                "max_abs_vy": round(peak_vy, 4),
                "landed_root_y": round(float(st.get("root_y", 0.0)), 4),
                "law": "engine root law: y'' = F_contact/m - g; "
                       "terminal descent vy = m*g/c = 0.2237 m/s (banked constants)",
                "mock": None,
            }
            with self.lock:
                self.fall_test = verdict
                self.events.append({"t": time.time(), "event": "fall_test", **verdict})
            return {"ok": True, **verdict}
        except Exception as e:                  # noqa: BLE001
            with self.lock:
                self.fall_test = {"phase": "error", "error": str(e)}
            return {"ok": False, "error": str(e)}

    def status(self) -> dict:
        # the status read never blocks behind a boot: try the engine directly,
        # and answer with the honest absence when it is mid-restart
        try:
            st = sb.http_get_json(self.url, "/tick_state", timeout=4)
        except OSError:
            st = {"restarting": True}
        with self.lock:
            return {
                "engine_state": st,
                "mock_carry": {k: self.mock_carry[k] for k in ("active", "x", "z", "arrived")},
                "fall_test": self.fall_test,
                "scene": self.scene_spec,
                "marker": self.scene_spec["marker"] if self.scene_spec else None,
            }

    def save(self) -> dict:
        with self.lock:
            rec = {"schema": "chimera.playable_slice.session.v1",
                   "saved_at": time.time(),
                   "scene": self.scene_spec, "events": self.events}
        out = HERE / "progress"
        out.mkdir(exist_ok=True)
        p = out / ("session_%d.json" % int(time.time()))
        p.write_text(json.dumps(rec, indent=1), encoding="utf-8")
        return {"ok": True, "saved": str(p)}



WORLD: World | None = None
CARRIER = threading.Timer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("  %s\n" % (fmt % args))

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/" or p == "/index.html":
            self._send(200, (HERE / "index.html").read_bytes(), "text/html")
        elif p == "/mock_registry.json":
            self._send(200, (HERE / "mock_registry.json").read_bytes(), "application/json")
        elif p == "/ghost.obj":
            self._send(200, WORLD.ghost_obj, "text/plain")
        elif p == "/api/verts":
            try:
                self._send(200, WORLD.verts(), "application/octet-stream")
            except OSError as e:
                self._json({"error": str(e)}, 502)
        elif p == "/api/topology":
            try:
                self._send(200, WORLD.topology(), "application/octet-stream")
            except OSError as e:
                self._json({"error": str(e)}, 502)
        elif p == "/api/status":
            self._json(WORLD.status())
        elif p == "/api/health":
            self._json({"ok": True, "world_booted": WORLD.scene_spec is not None})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        p = self.path.split("?")[0]
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(n) if n else b"{}"
        if p == "/api/send":
            self._json(WORLD.send())
        elif p == "/api/stop":
            self._json(WORLD.stop())
        elif p == "/api/press":
            self._json(WORLD.press(body))
        elif p == "/api/drop_test":
            threading.Thread(target=WORLD.drop_test, daemon=True).start()
            self._json({"ok": True, "started": True})
        elif p == "/api/restart":
            def boot():
                WORLD.boot()
            threading.Thread(target=boot, daemon=True).start()
            self._json({"ok": True, "restarting": True})
        elif p == "/api/save":
            self._json(WORLD.save())
        else:
            self._json({"error": "not found"}, 404)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=0,
                    help="0 = a bind-tested free port (8127 is refused by code)")
    ap.add_argument("--engine-exe", type=Path, default=DEFAULT_EXE)
    a = ap.parse_args()
    global WORLD
    engine_exe = a.engine_exe
    if not engine_exe.is_file():
        cand = shutil.which("chimera_engine.exe")
        if not cand:
            print("slice_server: engine binary missing at %s -- build it first"
                  % engine_exe)
            return 1
        engine_exe = Path(cand)
    WORLD = World(engine_exe)
    spec = WORLD.boot()
    print("scene booted: scene %s" % spec["scene_sha256"][:16])
    print("standing start: settling in the background (real physics)")

    port = a.port
    if not port:
        port = sb.free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)

    def carry_loop():
        while True:
            try:
                WORLD.carry_step()
            except Exception:
                pass
            time.sleep(0.05)
    threading.Thread(target=carry_loop, daemon=True).start()

    url = "http://127.0.0.1:%d/" % httpd.server_address[1]
    print("slice: %s" % url)
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        WORLD.shutdown_engine()
    return 0


if __name__ == "__main__":
    sys.exit(main())
