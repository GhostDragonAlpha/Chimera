"""lesson_server.py -- LESSON ONE "THE FALL"'s front door (the game_shell shape).

One stdlib server: serves the lesson page, starts and owns its OWN engine on a
bind-tested free port (8127 refused by code -- the port law), boots THE REAL
CT-DERIVED BODY through tools/playable_slice/scene_boot.py REUSED AS A MODULE
(no slice-page edits; that page is another lane's), and fronts the lesson:

  REALITY (the engine does it): the mesh stream (/verts, /topology), gravity,
  floor contact (g_contact_n), THE FALL (the root law y'' = F_contact/m - g),
  the settle at the derived attractor -(m*g/k) - ymin.
  TEACHING SURFACES (fed by engine bytes): height = root_y; speed = root_vy;
  floor hold = g_contact_n (the engine's own ground force); weight = m*g from
  the BANKED membrane_tick constants -- the lesson introduces no new constant.
  The lesson's own state machine only NAMES the phases; the engine decides them.

Run:  python tools/lesson_shell/lesson_server.py [--port N] [--engine-exe P]
      default port 8912 (bind-checked; 8127 refused); --no-browser is the
      default and the only behavior (a shared desktop is never touched).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "playable_slice"))
import scene_boot as sb  # noqa: E402  (the real-body boot, reused unchanged)

NEVER_PORT = 8127
DEFAULT_PORT = 8912
DEFAULT_EXE = ROOT / ".tmp/lesson_build/Release/chimera_engine.exe"

# THE BANKED CONSTANTS (membrane_tick.hpp/cpp; pinned in slice_server.py and
# the realbody receipts -- copied here WITH their source, never re-derived):
MASS_KG = 13824.5
G_EARTH = 9.81
K_GROUND = 1.3562e7
C_GROUND = 6.062e5
WEIGHT_N = MASS_KG * G_EARTH          # 135,614.245 N
SETTLE_VY = 0.05                      # the engine's own "settled means settled" bar
GRAVITY_SEAT_S = 0.35                 # the re-seat pause (the slice drop_test's own)


class World:
    """The lesson's world state. The engine stays the frozen world."""

    def __init__(self, engine_exe: Path):
        self.engine_exe = engine_exe
        self.lock = threading.RLock()
        self.port: int | None = None
        self.proc = None
        self.url: str | None = None
        self.boot_info: dict | None = None    # scene sha, import route, ymin
        self.ghost_obj: bytes | None = None
        self.ghost_rec: dict | None = None
        self.fall: dict = {"phase": "booting", "samples": []}
        self.boot_count = 0                   # cumulative, across reboots
        self.events: list[dict] = []

    # ── boot (the real body, through the slice's own boot machinery) ─────
    def boot(self) -> None:
        with self.lock:
            self.shutdown_engine()
            self.port = sb.free_port(avoid=(NEVER_PORT,))
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.proc = subprocess.Popen(
                [str(self.engine_exe), str(self.port), "--no-restore", "--hidden"],
                cwd=str(self.engine_exe.parent),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags)
            self.url = f"http://127.0.0.1:{self.port}"
            self.fall = {"phase": "booting", "samples": []}
        sb.wait_engine(self.url)
        rec = sb.boot_standing_start(self.url)   # THE REAL BODY, cached ~2 s
        ymin = float(rec.get("import_stats", {}).get("ymin", 0.0))
        if self.ghost_obj is None:
            # build_ghost_obj returns (bytes, record) -- unpack BOTH (run-4
            # lesson: assigning the tuple made /api/ghost answer a 2-byte
            # Content-Length with zero body bytes = ERR_CONTENT_LENGTH_MISMATCH)
            self.ghost_obj, self.ghost_rec = sb.build_ghost_obj()
        with self.lock:
            self.boot_count += 1
            self.boot_info = {
                "scene_sha256": rec["scene_sha256"],
                "route": rec.get("route", "unknown"),
                "ymin": ymin,
                "attractor_y": -(MASS_KG * G_EARTH / K_GROUND) - ymin,
                "weight_n": WEIGHT_N,
                "boot_count": self.boot_count,
            }
            self.events.append({"t": time.time(), "event": "boot",
                                "boot_seq": self.boot_count,
                                "scene_sha256": rec["scene_sha256"]})
            self.fall = {"phase": "idle", "samples": []}
        threading.Thread(target=self._finish_settle, daemon=True).start()

    def _finish_settle(self):
        try:
            st = sb.wait_settled(self.url, timeout=60)
            with self.lock:
                self.boot_info["settled_root_y"] = float(st.get("root_y", 0.0))
                self.boot_info["settled"] = True
                self.events.append({"t": time.time(), "event": "standing_start",
                                    "settled_root_y": float(st.get("root_y", 0.0))})
        except Exception:                     # noqa: BLE001 -- the lesson still runs
            with self.lock:
                self.boot_info["settled"] = False

    # ── the lesson's one move: THE FALL (the engine's own law) ───────────
    def drop(self) -> dict:
        with self.lock:
            if self.fall["phase"] in ("booting", "running"):
                return {"ok": False, "error": f"world is {self.fall['phase']}"}
            self.fall = {"phase": "running", "samples": [],
                         "started": time.time()}
        threading.Thread(target=self._run_fall, daemon=True).start()
        return {"ok": True, "phase": "running"}

    def _run_fall(self):
        url = self.url
        try:
            # 1. the re-seat: gravity OFF returns the body to its authored
            #    rest exactly (the engine's own switch; deterministic)
            sb.http_post(url, "/tick_gravity", b'{"on":false}',
                         ctype="application/json")
            with self.lock:
                self.fall["phase"] = "seated"
                self.events.append({"t": time.time(), "event": "reseat"})
            time.sleep(GRAVITY_SEAT_S)
            t_on = time.time()
            # 2. gravity ON: the law takes over -- contact launches the body
            #    out of the floor, gravity pulls it down, contact catches it
            sb.http_post(url, "/tick_gravity", b'{"on":true}',
                         ctype="application/json")
            with self.lock:
                self.fall["phase"] = "running"   # the law owns the world now
                self.fall["gravity_on_at"] = t_on
                self.events.append({"t": t_on, "event": "gravity_on"})
            peak_y, peak_vy = -99.0, 0.0
            contact_at = None
            landed_at = None
            samples: list[dict] = []
            while time.time() - t_on < 40.0:
                try:
                    st = sb.http_get_json(url, "/tick_state", timeout=4)
                except OSError:
                    time.sleep(0.05)
                    continue
                now = time.time()
                ry, vy = float(st.get("root_y", 0.0)), float(st.get("root_vy", 0.0))
                cn = float(st.get("g_contact_n", 0.0))
                if len(samples) < 1200:
                    samples.append({"t": round(now - t_on, 4), "root_y": ry,
                                    "root_vy": vy, "g_contact_n": cn,
                                    "gravity_on": bool(st.get("gravity_on"))})
                peak_y = max(peak_y, ry)
                peak_vy = max(peak_vy, abs(vy))
                if contact_at is None and cn > 1.0:
                    contact_at = now - t_on
                if abs(vy) <= SETTLE_VY and ry < 0.5:
                    landed_at = now - t_on
                    break
                time.sleep(0.05)
            with self.lock:
                self.fall["phase"] = "settling"
            st = sb.wait_settled(url, timeout=30)
            verdict = {
                "phase": "done",
                "max_root_y": round(peak_y, 4),
                "max_abs_vy": round(peak_vy, 4),
                "landed_root_y": round(float(st.get("root_y", 0.0)), 4),
                "contact_first_s": round(contact_at, 3) if contact_at is not None else None,
                "fall_span_s": round(landed_at, 3) if landed_at is not None else None,
                "samples_n": len(samples),
                "law": "engine root law: y'' = F_contact/m - g "
                       "(membrane_tick banked constants: m=13824.5 kg, g=9.81, "
                       "k=1.3562e7 N/m, c=6.062e5 N s/m)",
            }
            with self.lock:
                self.fall.update(verdict)
                self.fall["samples"] = samples
                self.events.append({"t": time.time(), "event": "fall_verdict",
                                    **{k: verdict[k] for k in
                                       ("max_root_y", "max_abs_vy", "landed_root_y")}})
        except Exception as e:                # noqa: BLE001 -- recorded, never hidden
            with self.lock:
                self.fall = {"phase": "error", "error": str(e), "samples": []}
            self.events.append({"t": time.time(), "event": "fall_error",
                                "error": str(e)})

    def reset(self) -> dict:
        with self.lock:
            if self.fall["phase"] in ("booting", "running"):
                return {"ok": False, "error": f"world is {self.fall['phase']}"}
            self.fall = {"phase": "idle", "samples": []}
            self.events.append({"t": time.time(), "event": "lesson_reset"})
            return {"ok": True, "phase": "idle"}

    # ── reads ────────────────────────────────────────────────────────────
    def status(self) -> dict:
        with self.lock:
            booting = self.fall["phase"] == "booting" or self.boot_info is None
            boot_info = dict(self.boot_info) if self.boot_info else None
            fall = {k: v for k, v in self.fall.items() if k != "samples"}
            n_samples = len(self.fall.get("samples", []))
            events_tail = self.events[-12:]
        out = {
            "lesson": "LESSON ONE -- THE FALL",
            "phase": fall.get("phase", "booting"),
            "fall": fall,
            "boot_count": self.boot_count,
            "trace_samples_server": n_samples,
            "events_tail": events_tail,
            "constants": {"mass_kg": MASS_KG, "g": G_EARTH,
                          "k_ground": K_GROUND, "c_ground": C_GROUND,
                          "weight_n": WEIGHT_N,
                          "source": "membrane_tick.hpp/cpp (banked)"},
        }
        if booting:
            out["engine"] = None
            return out
        try:
            st = sb.http_get_json(self.url, "/tick_state", timeout=4)
        except OSError:
            st = None
        out["engine"] = st   # THE ENGINE'S OWN BYTES: root_y, root_vy, g_contact_n, gravity_on
        if boot_info:
            out["boot"] = boot_info
        return out

    def save(self) -> dict:
        with self.lock:
            rec = {"schema": "chimera.lesson_one_fall.session.v1",
                   "saved_at": time.time(),
                   "boot": self.boot_info, "events": self.events,
                   "fall_samples": self.fall.get("samples", [])[-400:]}
        out = HERE / "progress"
        out.mkdir(exist_ok=True)
        p = out / ("session_%d.json" % int(time.time()))
        p.write_text(json.dumps(rec, indent=1), encoding="utf-8")
        return {"ok": True, "saved": str(p)}

    def shutdown_engine(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None


WORLD: World | None = None
INDEX_HTML = (HERE / "index.html").read_bytes() if (HERE / "index.html").exists() \
    else b"lesson page missing"


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
        self._send(code, json.dumps(obj).encode("utf-8"),
                   "application/json")

    def do_GET(self):                       # noqa: N802 (stdlib name)
        p = self.path.split("?")[0]
        if p == "/" or p == "/index.html":
            self._send(200, INDEX_HTML, "text/html; charset=utf-8")
        elif p == "/api/health":
            self._json({"ok": True, "lesson": "one-fall"})
        elif p == "/api/status":
            self._json(WORLD.status())
        elif p == "/api/verts":
            if WORLD.proc is None:
                self._json({"error": "booting"})
                return
            try:
                self._send(200, sb.http_get_raw(WORLD.url, "/verts"),
                           "application/octet-stream")
            except OSError:
                self._json({"error": "booting"})
        elif p == "/api/topology":
            if WORLD.proc is None:
                self._json({"error": "booting"})
                return
            try:
                self._send(200, sb.http_get_raw(WORLD.url, "/topology"),
                           "application/octet-stream")
            except OSError:
                self._json({"error": "booting"})
        elif p == "/api/ghost":
            body = WORLD.ghost_obj or b""
            self._send(200, body, "text/plain; charset=utf-8")
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):                      # noqa: N802 (stdlib name)
        p = self.path.split("?")[0]
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        if p == "/api/fall":
            self._json(WORLD.drop())
        elif p == "/api/reset":
            self._json(WORLD.reset())
        elif p == "/api/save":
            self._json(WORLD.save())
        else:
            self._json({"error": "not found"}, 404)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--engine-exe", type=Path, default=DEFAULT_EXE)
    args = ap.parse_args()
    if args.port == NEVER_PORT:
        print("port 8127 is refused by code (the port law)", flush=True)
        return 2
    if not args.engine_exe.exists():
        print(f"engine missing at {args.engine_exe} -- build it first "
              f"(cmake -S ChimeraEngine/engine -B .tmp/lesson_build && "
              f"cmake --build .tmp/lesson_build --config Release)", flush=True)
        return 2
    global WORLD
    WORLD = World(args.engine_exe)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    threading.Thread(target=WORLD.boot, daemon=True).start()
    print(f"lesson answers on port {srv.server_address[1]}", flush=True)
    print(f"engine exe {args.engine_exe}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        WORLD.shutdown_engine()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
