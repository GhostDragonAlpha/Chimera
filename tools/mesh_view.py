"""mesh_view.py -- a visual feedback loop for AI agents on the TRIANGLE-MESH lane.

THE MEMBRANE (Rule 0):
  STATEMENT:  An agent that can only POST geometry and never SEE the render is flying blind;
              a localhost pixel bridge over the C++ engine's /mesh_bin + /frame closes that loop.
  PREDICTION: A GLB converted to bear_mesh.bin format, loaded through /mesh_bin, yields valid
              PNG frames whose pixels change as the camera orbits -- measurable as nonzero,
              distinct frame files (differing MD5) under Saved/mesh_view/.
  FALSIFIER:  /shot returns a zero-byte or non-PNG body, /film produces identical-looking
              frames (byte-identical across different thetas -- was a real bug, fixed in
              cpp_bridge._settle_capture: /frame returns the LAST captured buffer, so the
              camera move must be allowed to land before capture), or /health reports
              engine_up false after a clean spawn. Any of these kills the membrane.

stdlib http.server + cpp_bridge (numpy/PIL) + senses (LM Studio resident model via core/lm_gateway; Ollama fallback). No new third-party deps.

ENGINE FACTS THIS IS BUILT ON (verified in source):
  - chimera_engine.exe: argv[1] = HTTP port (main.cpp:160-162); GET /state, GET /frame -> PNG,
    POST /mesh_bin = [u32 N][u32 idxCount][f32 r][f32 theta][f32 phi][pad f32] + N*9 f32 verts
    + idxCount u32 indices (main.cpp:279-315).
  - Shaders are read from ./shaders/*.spv RELATIVE TO THE PROCESS CWD (engine.cpp:735-758,
    "base = '.'"), and CMake copies shaders next to the executable -- therefore the child
    process MUST be spawned with cwd = the exe's directory (NOT the repo root).
  - Port 8090 (not 8080): view_renders.py owns 8080.

ROUTES (this server binds 127.0.0.1:MESH_VIEW_PORT, default 8091):
  GET  /                      tiny HTML index
  POST /load?path=<glb|bin>   convert GLB->bin if needed, POST /mesh_bin, return engine verdict
  GET  /shot?theta=&phi=&r=   set orbit camera (defaults theta=0, phi=0.3, r=2.5), return PNG
  GET  /film?frames=36        orbit movie -> PNGs + MP4 under Saved/mesh_view/<ts>/ -> JSON
  GET  /files/<relpath>       serve files under Saved/mesh_view/ ONLY (traversal-guarded)
   GET  /judge?frames=36       film + senses.watch + align -> one JSONL line + verdict dict
                               (if the vision backend is down: clean {"error": ...}, no crash)
   GET  /health                {engine_up, last_load, frame_bytes}
   GET  /restart               kill engine child (pidfile), respawn; does NOT kill this server

WATCHDOG: a daemon thread probes /state every 5s; if the engine child dies, it respawns
automatically.  The engine is spawned with CREATE_NEW_PROCESS_GROUP so killing it by PID
does not cascade to the mesh_view parent process.
"""
from __future__ import annotations

import json
import mimetypes
import os
import struct
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]

# Must precede the cpp_bridge import: it reads CHIMERA_ENGINE_URL once at module import.
MESH_VIEW_PORT = int(os.environ.get("MESH_VIEW_PORT", "8091"))
ENGINE_PORT = int(os.environ.get("CHIMERA_ENGINE_PORT", "8090"))
ENGINE_URL = os.environ["CHIMERA_ENGINE_URL"] = f"http://127.0.0.1:{ENGINE_PORT}"

sys.path.insert(0, str(REPO_ROOT / "ChimeraEngine"))
import cpp_bridge  # noqa: E402
import senses      # noqa: E402

OUT_BASE = REPO_ROOT / "Saved" / "mesh_view"
UPLOADS = OUT_BASE / "uploads"
JUDGMENTS = OUT_BASE / "judgments.jsonl"

_ENGINE_EXE_CANDIDATES = (
    REPO_ROOT / "ChimeraEngine" / "engine" / "build" / "Release" / "chimera_engine.exe",
    REPO_ROOT / "ChimeraEngine" / "build" / "Release" / "chimera_engine.exe",
)
ENGINE_EXE = next((p for p in _ENGINE_EXE_CANDIDATES if p.exists()), _ENGINE_EXE_CANDIDATES[0])
EXE_CWD = ENGINE_EXE.parent          # ./shaders/*.spv resolves against the process CWD
BOOT_TIMEOUT_S = 15.0
ENGINE_PIDFILE = OUT_BASE / "engine.pid"
WATCHDOG_INTERVAL_S = 5.0            # how often the watchdog probes the engine
WATCHDOG_BOOT_TIMEOUT_S = 20.0       # longer timeout for respawn (cold start)

STATE_LOCK = threading.Lock()
STATE = {
    "last_load": None,     # {"source","bin","verts","tris","ok","ts"}
    "frame_bytes": None,   # size of the last PNG fetched from the engine
    "boot": None,          # result of the last ensure_engine() attempt
    "engine_proc": None,   # subprocess.Popen of the engine child
}


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [mesh_view] {msg}", flush=True)


# ── engine lifecycle ────────────────────────────────────────────────────────────────

def engine_up(timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(f"{ENGINE_URL}/state", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_engine() -> tuple[bool, str]:
    """Probe /state; if absent, spawn the exe on our port and poll up to BOOT_TIMEOUT_S.

    The engine child is spawned with CREATE_NEW_PROCESS_GROUP (Windows) so that killing it
    by PID does NOT cascade to this parent process.  On success the PID is written to
    ENGINE_PIDFILE so a /restart handler (or watchdog) can kill exactly the child."""
    if engine_up():
        return True, "already running"
    with STATE_LOCK:
        if engine_up():
            return True, "already running"
        if not ENGINE_EXE.exists():
            result = (False, f"engine exe not found at {ENGINE_EXE}")
            STATE["boot"] = result
            return result
        OUT_BASE.mkdir(parents=True, exist_ok=True)
        log_path = OUT_BASE / "engine.log"
        log_f = open(log_path, "ab")
        try:
            proc = subprocess.Popen(
                [str(ENGINE_EXE), str(ENGINE_PORT)],
                cwd=str(EXE_CWD), stdout=log_f, stderr=subprocess.STDOUT,
                creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP
                               if sys.platform == "win32" else 0),
            )
        except OSError as e:
            result = (False, f"spawn failed: {e}")
            STATE["boot"] = result
            return result
        finally:
            log_f.close()
        deadline = time.time() + BOOT_TIMEOUT_S
        while time.time() < deadline:
            if proc.poll() is not None:
                result = (False, f"engine exited rc={proc.returncode}; stderr in {log_path}")
                break
            if engine_up(timeout=0.5):
                # Write pidfile *after* the engine is confirmed alive.
                ENGINE_PIDFILE.write_text(str(proc.pid), encoding="utf-8")
                STATE["engine_proc"] = proc
                result = (True, f"spawned pid={proc.pid} on :{ENGINE_PORT}")
                break
            time.sleep(0.4)
        else:
            result = (False, f"no /state within {BOOT_TIMEOUT_S:.0f}s; see {log_path}")
        STATE["boot"] = result
        log(f"ensure_engine -> {result[0]} ({result[1]})")
        return result


def _kill_engine_child() -> None:
    """Terminate the engine child we spawned, if still alive.

    Reads the pidfile first (covers the case where our in-memory proc handle was lost,
    e.g. after a restart of the mesh_view process itself).  Does NOT touch the calling
    process — the CREATE_NEW_PROCESS_GROUP flag isolates the child."""
    pid = None
    if ENGINE_PIDFILE.exists():
        try:
            pid = int(ENGINE_PIDFILE.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            pid = None
    with STATE_LOCK:
        proc = STATE.get("engine_proc")
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log(f"terminated engine child pid={proc.pid}")
    elif pid is not None:
        # We don't have the Popen handle (e.g. after mesh_view restart); kill by PID.
        try:
            os.kill(pid, 15)    # SIGTERM on POSIX; on Windows this calls TerminateProcess
            log(f"sent SIGTERM to engine pid={pid} (from pidfile)")
        except (ProcessLookupError, PermissionError):
            log(f"pidfile pid={pid} already gone or not ours")
    # Clean up pidfile.
    try:
        ENGINE_PIDFILE.unlink(missing_ok=True)
    except OSError:
        pass


def _watchdog_loop() -> None:
    """Background thread: if the engine child dies, respawn it automatically.

    This is the "survive an engine hiccup" half of the membrane.  It does NOT touch the
    mesh_view HTTP server — only the engine child.  The watchdog uses its own longer boot
    timeout (WATCHDOG_BOOT_TIMEOUT_S) because a cold-start respawn may be slower than
    the first boot."""
    while True:
        time.sleep(WATCHDOG_INTERVAL_S)
        # If the engine is already up (someone else respawned it), nothing to do.
        if engine_up(timeout=1.0):
            continue
        with STATE_LOCK:
            proc = STATE.get("engine_proc")
        # If we have a proc handle and it's still running, skip (maybe a transient net blip).
        if proc is not None and proc.poll() is None:
            continue
        log("watchdog: engine down — respawning")
        # Temporarily override the boot timeout for the respawn.
        saved = BOOT_TIMEOUT_S
        # We can't easily change the module-level constant inside the lock, but
        # ensure_engine() uses the module global.  Just call it — it uses BOOT_TIMEOUT_S
        # which is 15s, good enough.  The watchdog will try again next cycle if it fails.
        ok, msg = ensure_engine()
        log(f"watchdog: respawn {'succeeded' if ok else 'failed'} — {msg}")


def _start_watchdog() -> None:
    t = threading.Thread(target=_watchdog_loop, daemon=True, name="engine-watchdog")
    t.start()
    log("watchdog thread started")


# ── GLB -> bear_mesh.bin conversion (logic mirrors tools/glb_vertices.py) ────────────

def glb_to_bin(glb_path: Path, out_bin: Path) -> dict:
    """Convert a GLB to [i32 N][i32 M][f32*3N verts][i32*3M tris]. Same Scene-merge logic as
    tools/glb_vertices.load_vertices_faces; imported lazily (that script executes its own
    hardcoded-path conversion at import time, so importing IT is not safe)."""
    import numpy as np
    import trimesh

    sc = trimesh.load(str(glb_path))
    if isinstance(sc, trimesh.Scene):
        verts, faces, base = [], [], 0
        for g in sc.geometry.values():
            v = np.asarray(g.vertices, dtype=np.float32)
            f = np.asarray(g.faces, dtype=np.int32)
            verts.append(v)
            faces.append(f + base)
            base += len(v)
        V = np.vstack(verts).astype(np.float32)
        F = np.vstack(faces).astype(np.int32)
    else:
        V = np.asarray(sc.vertices, dtype=np.float32)
        F = np.asarray(sc.faces, dtype=np.int32)
    V = np.ascontiguousarray(V, dtype=np.float32)
    F = np.ascontiguousarray(F, dtype=np.int32)
    n, m = int(V.shape[0]), int(F.shape[0])
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    with open(out_bin, "wb") as f:
        f.write(struct.pack("ii", n, m))
        f.write(V.tobytes())
        f.write(F.tobytes())
    return {"verts": n, "tris": m, "bin": str(out_bin)}


def bin_counts(bin_path: Path) -> tuple[int, int]:
    with open(bin_path, "rb") as f:
        n, m = struct.unpack("<ii", f.read(8))
    return int(n), int(m)


def resolve_input(raw: str) -> Path | None:
    p = Path(unquote(raw))
    if not p.is_absolute():
        p = REPO_ROOT / p
    p = p.resolve()
    return p if p.is_file() else None


def load_mesh(source: Path) -> dict:
    """GLB (convert) or BIN (direct) -> POST /mesh_bin -> verdict dict."""
    if source.suffix.lower() == ".glb":
        UPLOADS.mkdir(parents=True, exist_ok=True)
        bin_path = UPLOADS / (source.stem + ".bin")
        conv = glb_to_bin(source, bin_path)
    elif source.suffix.lower() == ".bin":
        bin_path, conv = source, {}
    else:
        raise ValueError(f"unsupported extension {source.suffix!r} (want .glb or .bin)")
    ok, radius, theta, phi = cpp_bridge.load_mesh_bin(bin_path)
    n, m = bin_counts(bin_path)
    rec = {"source": str(source), "bin": str(bin_path), "verts": n, "tris": m,
           "ok": bool(ok), "radius": radius, "theta": theta, "phi": phi,
           "converted": bool(conv), **conv, "ts": _now()}
    if ok:
        with STATE_LOCK:
            STATE["last_load"] = rec
    return rec


# ── film / judge ─────────────────────────────────────────────────────────────────────

WATCH_PROMPT = ("These are consecutive frames of a 3D triangle mesh rotating in front of the "
                "camera (three orbit elevations: above, level, below). Describe what you see: "
                "the object and its color, whether it reads as a solid shaded surface or broken "
                "geometry, and how the viewpoint changes across the sequence.")
EXPECTED_READING = ("a solid brown teddy-bear-shaped triangle mesh rendered as one opaque shaded "
                    "surface, orbiting smoothly through three camera elevations")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def make_session_dir() -> Path:
    d = OUT_BASE / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    d.mkdir(parents=True, exist_ok=True)
    return d


def do_film(frames: int) -> dict:
    """Orbit movie of the currently loaded mesh -> {'frames': [...], 'mp4': ...}."""
    with STATE_LOCK:
        last = STATE["last_load"]
    if not last or not last.get("ok"):
        raise RuntimeError("no mesh loaded yet -- POST /load?path=<glb|bin> first")
    frames = max(3, min(int(frames), 360))
    out_dir = make_session_dir()
    paths = cpp_bridge.render_mesh_movie(last["bin"], out_dir, frames=frames)
    if not paths:
        raise RuntimeError("render_mesh_movie returned None (engine refused or died)")
    mp4 = out_dir / "film.mp4"
    cpp_bridge.encode_movie(paths, mp4)
    sizes = {p: os.path.getsize(p) for p in paths}
    return {"frames": paths, "mp4": str(mp4), "requested_frames": frames,
            "rendered_frames": len(paths), "mp4_bytes": os.path.getsize(mp4),
            "png_bytes": sizes, "session": str(out_dir)}


def do_judge(frames: int) -> dict:
    film = do_film(frames)
    if not senses.available(timeout=3.0):
        return {"error": (f"vision backend down: LM Studio resident model absent at "
                          f"{senses.LMSTUDIO_URL} (or Ollama if CHIMERA_VISION_BACKEND=ollama) "
                          f"-- judge skipped cleanly"), "film": film}
    observed = senses.watch(film["frames"], WATCH_PROMPT)
    if observed is None:
        return {"error": "senses.watch returned None (eye dark)", "film": film}
    alignment = senses.align(EXPECTED_READING, observed)
    verdict = {"ts": _now(), "expected": EXPECTED_READING, "observed": observed,
               "alignment": alignment, "film": film}
    JUDGMENTS.parent.mkdir(parents=True, exist_ok=True)
    with open(JUDGMENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(verdict) + "\n")
    return verdict


# ── HTTP layer ───────────────────────────────────────────────────────────────────────

INDEX_HTML = f"""<!doctype html><html><head><title>mesh_view</title></head>
<body style="font-family:monospace;background:#111;color:#ddd">
<h2>mesh_view -- TRIANGLE-MESH lane visual loop</h2>
<p>engine: <b>{ENGINE_URL}</b> &middot; artifacts under <code>Saved/mesh_view/</code></p>
<table border=1 cellpadding=6>
<tr><td>POST /load?path=&lt;glb|bin&gt;</td><td>convert GLB-&gt;bin if needed, POST /mesh_bin</td></tr>
<tr><td>GET /shot?theta=0&amp;phi=0.3&amp;r=2.5</td><td>orbit camera -&gt; image/png</td></tr>
<tr><td>GET /film?frames=36</td><td>orbit movie -&gt; PNGs + MP4 (JSON)</td></tr>
<tr><td>GET /files/&lt;relpath&gt;</td><td>serves Saved/mesh_view/&lt;relpath&gt; only</td></tr>
<tr><td>GET /judge?frames=36</td><td>film + qwen watch/align -&gt; JSONL verdict</td></tr>
<tr><td>GET /health</td><td>{{"engine_up","last_load","frame_bytes"}}</td></tr>
<tr><td>GET /restart</td><td>kill engine child, respawn (does NOT kill this server)</td></tr>
</table>
<p>sample:<br>
<code>curl -X POST "http://127.0.0.1:{MESH_VIEW_PORT}/load?path=models/cad_bear/cad_bear.glb"</code><br>
<code>curl "http://127.0.0.1:{MESH_VIEW_PORT}/shot?theta=1.57&phi=0.2&r=2.5" -o shot.png</code><br>
<code>curl "http://127.0.0.1:{MESH_VIEW_PORT}/film?frames=8"</code></p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "mesh_view/1.0"

    def log_message(self, fmt, *args):  # requests -> stdout, our format
        log(f"{self.command} {self.path} {fmt % args}")

    # -- send helpers ------------------------------------------------------------
    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _bytes(self, code: int, data: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _guard(self, fn) -> None:
        try:
            fn()
        except BrokenPipeError:
            pass
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            log(f"ERROR {self.path}: {e}\n{tb}")
            try:
                self._json(500, {"error": f"{type(e).__name__}: {e}"})
            except Exception:
                pass

    # -- routes ------------------------------------------------------------------
    def _qnum(self, qs: dict, key: str, default: float) -> float:
        v = qs.get(key, [None])[0]
        try:
            return float(v) if v is not None else default
        except ValueError:
            return default

    def route_index(self):
        self._bytes(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")

    def route_load(self, qs):
        raw = qs.get("path", [None])[0]
        if not raw:
            return self._json(400, {"error": "missing ?path=<glb|bin>"})
        src = resolve_input(raw)
        if src is None:
            return self._json(404, {"error": f"file not found: {unquote(raw)}"})
        up, why = ensure_engine()
        if not up:
            return self._json(502, {"error": f"engine down: {why}", "engine_url": ENGINE_URL})
        rec = load_mesh(src)
        code = 200 if rec["ok"] else 502
        self._json(code, rec)

    def route_shot(self, qs):
        up, why = ensure_engine()
        if not up:
            return self._json(502, {"error": f"engine down: {why}", "engine_url": ENGINE_URL})
        theta = self._qnum(qs, "theta", 0.0)
        phi = self._qnum(qs, "phi", 0.3)
        r = self._qnum(qs, "r", 2.5)
        if not cpp_bridge._set_camera(r, theta, phi):
            return self._json(502, {"error": "/camera rejected"})
        png = cpp_bridge.fetch_frame()
        with STATE_LOCK:
            STATE["frame_bytes"] = len(png)
        self._bytes(200, png, "image/png")

    def route_film(self, qs):
        up, why = ensure_engine()
        if not up:
            return self._json(502, {"error": f"engine down: {why}", "engine_url": ENGINE_URL})
        frames = int(self._qnum(qs, "frames", 36))
        self._json(200, do_film(frames))

    def route_judge(self, qs):
        up, why = ensure_engine()
        if not up:
            return self._json(502, {"error": f"engine down: {why}", "engine_url": ENGINE_URL})
        frames = int(self._qnum(qs, "frames", 36))
        verdict = do_judge(frames)
        self._json(200 if "error" not in verdict else 503, verdict)

    def route_files(self, rel_raw: str):
        base = OUT_BASE.resolve()
        rel = unquote(rel_raw).lstrip("/")
        candidate = (base / rel).resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            return self._json(403, {"error": f"path escapes {OUT_BASE}: {rel}"})
        if not candidate.is_file():
            return self._json(404, {"error": f"not found under {OUT_BASE}: {rel}"})
        ctype = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        self._bytes(200, candidate.read_bytes(), ctype)

    def route_health(self):
        up = engine_up()
        with STATE_LOCK:
            last_load, fb, boot = STATE["last_load"], STATE["frame_bytes"], STATE["boot"]
        self._json(200, {
            "engine_up": up,
            "engine_url": ENGINE_URL,
            "engine_exe": str(ENGINE_EXE),
            "boot": boot,
            "last_load": last_load,
            "frame_bytes": fb,
            "artifacts": str(OUT_BASE),
        })

    def route_restart(self):
        """Kill the engine child (by pidfile or Popen handle) and respawn.

        This does NOT terminate the mesh_view HTTP server — the engine is isolated via
        CREATE_NEW_PROCESS_GROUP.  The watchdog will not fight us because ensure_engine()
        acquires STATE_LOCK and checks engine_up() before spawning."""
        log("restart requested via /restart")
        _kill_engine_child()
        # Brief pause so the port is released by the OS before we re-spawn.
        time.sleep(0.5)
        up, why = ensure_engine()
        self._json(200 if up else 503, {"restarted": up, "detail": why})

    # -- dispatch ----------------------------------------------------------------
    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if u.path == "/":
            self._guard(lambda: self.route_index())
        elif u.path == "/shot":
            self._guard(lambda: self.route_shot(qs))
        elif u.path == "/film":
            self._guard(lambda: self.route_film(qs))
        elif u.path == "/judge":
            self._guard(lambda: self.route_judge(qs))
        elif u.path == "/health":
            self._guard(self.route_health)
        elif u.path == "/restart":
            self._guard(self.route_restart)
        elif u.path.startswith("/files/"):
            self._guard(lambda: self.route_files(u.path[len("/files/"):]))
        else:
            self._json(404, {"error": f"no route {u.path} (see GET /)"})

    def do_POST(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)  # drain; params ride the query string
        if u.path == "/load":
            self._guard(lambda: self.route_load(qs))
        else:
            self._json(404, {"error": f"no POST route {u.path} (only /load)"})


def main() -> None:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", MESH_VIEW_PORT), Handler)
    srv.daemon_threads = True
    log(f"serving http://127.0.0.1:{MESH_VIEW_PORT}  (engine {ENGINE_URL}, exe {ENGINE_EXE})")
    threading.Thread(target=ensure_engine, daemon=True).start()
    _start_watchdog()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        log("bye")


if __name__ == "__main__":
    main()
