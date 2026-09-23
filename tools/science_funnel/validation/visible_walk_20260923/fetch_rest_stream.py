"""fetch_rest_stream.py -- boot the REAL slice server (its own engine), wait
for the settle, fetch ONE settled /api/verts frame (the engine's own bytes:
pos3+nrm3+col3 per vertex), save raw + stats, kill. The walk capture later
rides these exact colors/normals (F-SOURCE-IS-ENGINE clause d).
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
ROOT = SLICE.parents[1]
EXE = ROOT / ".tmp" / "slice_build" / "Release" / "chimera_engine.exe"
OUT = HERE / "rest_stream.bin"
REC = HERE / "rest_stream_record.json"


def get(base, path, timeout=10):
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def main() -> int:
    port = 8231
    base = f"http://127.0.0.1:{port}"
    rec = {"port": port, "exe": str(EXE)}
    server = subprocess.Popen(
        [sys.executable, str(SLICE / "slice_server.py"), "--port", str(port),
         "--engine-exe", str(EXE)],
        cwd=str(ROOT),
        stdout=open(HERE / "rest_boot_server_log.txt", "w", encoding="utf-8"),
        stderr=subprocess.STDOUT)
    t0 = time.perf_counter()
    try:
        booted = False
        while time.perf_counter() - t0 < 240:
            try:
                if json.loads(get(base, "/api/health")).get("world_booted"):
                    booted = True
                    rec["t_world_up_s"] = round(time.perf_counter() - t0, 2)
                    break
            except OSError:
                time.sleep(0.25)
        if not booted:
            raise RuntimeError("server never booted")
        # wait for the settle (the page readiness gate uses the same flag)
        settled = False
        while time.perf_counter() - t0 < 300:
            try:
                st = json.loads(get(base, "/api/status"))
                if (st.get("scene") or {}).get("settled"):
                    settled = True
                    rec["t_settled_s"] = round(time.perf_counter() - t0, 2)
                    rec["root_y"] = (st.get("engine_state") or {}).get("root_y")
                    break
            except OSError:
                time.sleep(0.5)
        rec["settled"] = settled
        raw = get(base, "/api/verts", timeout=60)
        OUT.write_bytes(raw)
        rec["bytes"] = len(raw)
        rec["sha256"] = __import__("hashlib").sha256(raw).hexdigest()
        import struct
        n = int.from_bytes(raw[:4], "little")
        rec["n_verts"] = n
        print(json.dumps(rec, indent=1))
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        time.sleep(1.0)
    REC.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
