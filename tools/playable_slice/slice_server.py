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
MARKER_DIST_M = 1.2               # ~2 body lengths (the stand-in body is 0.53 m long)
CARRY_SPEED_MPS = 0.4
ARRIVE_RADIUS_M = 0.15
SETTLE_VY = 0.05                  # the engine's own "settled means settled" bar

# ── THE THIN-CLIENT SNAPSHOT TRANSPORT (lane/thin-client-pilot-20260920) ────
# Astra round-5 Decision 2, camera clause: timestamped snapshots -> client
# interpolation -> local rendering. The engine (frozen core) serves /verts and
# /tick_state but stamps NEITHER into the vertex payload (engine-service gap
# E1, prereg thin_client_pilot_20260920/record.md) -- so THIS server composes
# the two engine pulls into one framed snapshot. The authoritative timestamp is
# the engine's OWN monotonic ts_us (steady clock, read under the same tick lock
# as the state fields); the verts pull precedes the state pull, so ts postdates
# the geometry by the measured inter-pull gap (gap_us travels in every header:
# the E1 ambiguity is measured per snapshot, never hidden).
#
# Header (52 B, little-endian):
#   u32 magic 'THS1' | u64 ts_us | u32 ticks | f32 root_y | f32 root_vy
#   f32 P_lower | f32 P_upper | f32 dimple_m | u64 gap_us | u32 fmt | u32 n
# Payload fmt codes: 0 FULL36 (legacy [36 B/vert], pos+nrm+col), 1 POS12
# (positions f32x3; normals recomputed client-side), 2 POS16 (f16 pos+nrm,
# 12 B/vert), 3 Z12 (zlib-9 of the POS12 payload), 4 DELTA (the engine's own
# C3 run-compressed chain frame, engine-space: the carry mock's XY offset is
# NOT applied -- named here, and in the receipt).
SNAP_MAGIC = 0x31534854           # 'THS1' little-endian
SNAP_HDR = "<IQIfffffQII"         # 4+8+4+5*4+8+4+4 = 52 B
SNAP_FMT = {"FULL36": 0, "POS12": 1, "POS16": 2, "Z12": 3, "DELTA": 4}


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
            body_obj, self.body_rec = sb.build_stand_in_body()
            rec = sb.boot_standing_start(self.url)
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
        measured attractor: 0.25529300 constant, /verts sha constant)."""
        st = sb.wait_settled(self.url, timeout=30)
        prev = None
        deadline = time.time() + 90.0
        while time.time() < deadline:
            cur = sb.http_get_json(self.url, "/tick_state")
            ry, vy = float(cur.get("root_y", 0.0)), abs(float(cur.get("root_vy", 1.0)))
            if prev is not None and abs(ry - prev) < 1e-7 and vy < 1e-5:
                break
            prev = ry
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
        # the engine's real root is never edited here.
        import struct as _s
        n = int.from_bytes(raw[:4], "little")
        buf = bytearray(raw)
        for i in range(n):
            off = 4 + i * 36
            x, y, z = _s.unpack_from("<3f", buf, off)
            _s.pack_into("<3f", buf, off, x + carry["x"], y, z + carry["z"])
        return bytes(buf)

    # ── thin-client snapshot composition (the pilot's transport) ─────────
    def snapshot(self, fmt: str = "FULL36", delta_key: bool = False) -> tuple:
        """One timestamped snapshot: engine /verts (carry-applied) then engine
        /tick_state, framed under SNAP_HDR. Returns (bytes, fmt, n). The
        measured verts->state gap rides every header (E1 ambiguity, honest)."""
        import struct as _s
        t0 = time.perf_counter()
        if fmt == "DELTA":
            path = "/verts?delta=key" if delta_key else "/verts?delta=1"
            vraw = sb.http_get_raw(self.url, path)
            n = _s.unpack_from("<I", vraw, 4)[0] if len(vraw) >= 8 else 0
        else:
            vraw = self.verts()
            n = int.from_bytes(vraw[:4], "little")
        t1 = time.perf_counter()
        state = sb.http_get_json(self.url, "/tick_state")
        t2 = time.perf_counter()
        gap_us = int((t2 - t1) * 1e6)
        # verts arrived before state: ts postdates the geometry by gap_us.
        # A second smaller ambiguity (the verts pull's own transit) is bounded
        # by gap_us too -- both live inside one measured number.
        if fmt == "POS12":
            payload = bytearray(12 * n)
            for i in range(n):
                payload[12 * i:12 * i + 12] = vraw[4 + 36 * i:4 + 36 * i + 12]
            payload = bytes(payload)
        elif fmt == "POS16":
            import numpy as _np
            V = _np.frombuffer(vraw, dtype=_np.float32, count=9 * n,
                               offset=4).reshape(n, 9)
            half = _np.empty((n, 6), dtype=_np.float16)
            half[:, 0:3] = V[:, 0:3]
            half[:, 3:6] = V[:, 3:6]
            payload = half.tobytes()
        elif fmt == "Z12":
            import zlib as _z
            pos = bytearray(12 * n)
            for i in range(n):
                pos[12 * i:12 * i + 12] = vraw[4 + 36 * i:4 + 36 * i + 12]
            payload = _z.compress(bytes(pos), 9)
        else:
            fmt = "FULL36"
            payload = vraw[4:] if n else vraw
        hdr = _s.pack(SNAP_HDR, SNAP_MAGIC,
                      int(state.get("ts_us", 0)), int(state.get("ticks", 0)),
                      float(state.get("root_y", 0.0)),
                      float(state.get("root_vy", 0.0)),
                      float(state.get("P_lower", 0.0)),
                      float(state.get("P_upper", 0.0)),
                      float(state.get("dimple_m", 0.0)),
                      gap_us, SNAP_FMT[fmt], n)
        return hdr + payload, fmt, n

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

    def carry_reset(self) -> dict:
        """MOCK[mock_carry] home: the slide's persisted XY offset returns to
        zero (stop does not reset it -- arrival parks the body at the marker).
        The pilot's CARRY scenario needs a fresh slide from the start pose."""
        with self.lock:
            self.mock_carry = {"active": False, "x": 0.0, "z": 0.0,
                               "arrived": False}
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

# wire-truth counters (the pilot's bandwidth table cross-check): bytes OUT per
# route family, requests, and the running gap_us distribution (E1).
STATS_LOCK = threading.Lock()
STATS: dict = {"snapshot_req": 0, "snapshot_bytes": 0, "frame_req": 0,
               "frame_bytes": 0, "verts_req": 0, "verts_bytes": 0,
               "gap_us_max": 0, "gap_us_hist": []}


def stat(route: str, nbytes: int, gap_us: int | None = None) -> None:
    with STATS_LOCK:
        STATS[route + "_req"] += 1
        STATS[route + "_bytes"] += nbytes
        if gap_us is not None:
            STATS["gap_us_max"] = max(STATS["gap_us_max"], gap_us)
            h = STATS["gap_us_hist"]
            h.append(gap_us)
            if len(h) > 4096:
                del h[:len(h) - 4096]


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
        elif p == "/api/snapshot":
            # THE THIN-CLIENT SNAPSHOT (timestamped, composed server-side; see
            # SNAP_HDR above). fmt via query; DELTA resync via &key=1.
            q = self.path.split("?", 1)
            query = q[1] if len(q) > 1 else ""
            fmt = "FULL36"
            for tok in query.split("&"):
                if tok.upper().startswith("FMT="):
                    fmt = tok[4:].upper()
            if fmt not in SNAP_FMT:
                self._json({"error": "unknown fmt: %s" % fmt}, 400)
                return
            try:
                body, f, n = WORLD.snapshot(fmt, delta_key="key=1" in query)
                stat("snapshot", len(body), gap_us=int.from_bytes(
                    body[36:44], "little"))
                self._send(200, body, "application/octet-stream")
            except OSError as e:
                self._json({"error": str(e)}, 502)
        elif p == "/api/frame":
            # the pixel family through the slice door (engine /frame passthru)
            q = self.path.split("?", 1)
            eng_path = "/frame?" + (q[1] if len(q) > 1 else "")
            try:
                body = sb.http_get_raw(WORLD.url, eng_path)
                stat("frame", len(body))
                ctype = ("image/jpeg" if body[:3] == b"\xff\xd8\xff"
                         else "image/png" if body[:4] == b"\x89PNG"
                         else "application/json")
                self._send(200, body, ctype)
            except OSError as e:
                self._json({"error": str(e)}, 502)
        elif p == "/api/stats":
            with STATS_LOCK:
                out = dict(STATS)
                h = sorted(out.pop("gap_us_hist") or [0])
                out["gap_us_median"] = h[len(h) // 2]
                out["gap_us_p95"] = h[min(len(h) - 1, int(0.95 * len(h)))]
                out["gap_us_n"] = len(h)
                out["gap_us_hist_tail"] = h[-64:]
            self._json(out)
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
        elif p == "/api/carry_reset":
            self._json(WORLD.carry_reset())
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
