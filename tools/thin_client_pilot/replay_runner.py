"""replay_runner.py -- drive the replay instrument for one recorded run.

Builds data.json from (client pilot samples, twin truth log, topology),
serves replay.html + data.json on a private loopback port, collects the
result POST, and optionally runs the WHOLE pipeline twice on identical bytes
(F5: the two result sets must agree bit-stably).

Usage:
  python replay_runner.py --dump client_dump.json --truth truth.bin \
      --topo topology.bin --out result.json [--stills-dir DIR] [--rerun]
"""
from __future__ import annotations

import argparse
import base64
import json
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_truth(path: str) -> list[dict]:
    frames = []
    with open(path, "rb") as f:
        while True:
            hdr = f.read(40)
            if len(hdr) < 40:
                break
            magic, ts, ticks, ry, rvy, dim, wall, n = struct.unpack("<IQIfffQI", hdr)
            if magic != 0x31524831:
                break            # torn tail (recorder terminated mid-run)
            payload = f.read(36 * n)
            if len(payload) < 36 * n:
                break            # torn tail: keep the intact prefix
            frames.append({"ts": ts, "ticks": ticks, "root_y": ry,
                           "root_vy": rvy, "dimple": dim, "wall": wall,
                           "pos": np.frombuffer(payload, dtype=np.float32,
                                                count=3 * n).copy(),
                           "nrm": np.frombuffer(payload, dtype=np.float32,
                                                count=3 * n, offset=12 * n).copy(),
                           "col": np.frombuffer(payload, dtype=np.float32,
                                                count=3 * n, offset=24 * n).copy()})
    return frames


def truth_at(frames: list[dict], ts_us: int) -> dict | None:
    """linear interpolation between the twin truth frames bracketing ts_us."""
    import numpy as np
    lo, hi = None, None
    for f in frames:
        if f["ts"] <= ts_us:
            lo = f
        if f["ts"] > ts_us and hi is None:
            hi = f
            break
    if lo is None:
        return None if hi is None else hi
    if hi is None:
        return lo
    if hi["ts"] == lo["ts"]:
        return lo
    a = (ts_us - lo["ts"]) / (hi["ts"] - lo["ts"])
    return {"ts": ts_us,
            "pos": (1 - a) * lo["pos"] + a * hi["pos"],
            "nrm": (1 - a) * lo["nrm"] + a * hi["nrm"],
            "col": (1 - a) * lo["col"] + a * hi["col"],
            "interp": True}


def b64(arr) -> str:
    return base64.b64encode(np.ascontiguousarray(arr).tobytes()).decode("ascii")


def build_data(dump: dict, frames: list[dict], topo: bytes, shift_us: int,
               phases: dict[int, str], still_indices: list[int]) -> dict:
    pairs = []
    for s in dump["samples"]:
        r = s["r"] + shift_us if s["r"] else s["a"]   # direct mode: at A
        t = truth_at(frames, r)
        if t is None:
            continue
        pairs.append({"i": len(pairs), "t": s["t"], "r": r,
                      "phase": phases.get(len(pairs), ""),
                      "a": s["frame"],
                      "b": b64(np.concatenate([t["pos"], t["nrm"], t["col"]]))})
    return {"camera": dump["cam"], "target": [0, 0.25, 0],
            "marker": MARKER, "w": 960, "h": 540,
            "topoB64": base64.b64encode(topo).decode("ascii"),
            "pairs": pairs, "still_indices": still_indices}


RESULT: dict | None = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, (HERE / "replay.html").read_bytes(), "text/html")
        elif self.path == "/data.json":
            self._send(200, json.dumps(DATA).encode(), "application/json")
        else:
            self._send(404, b"{}", "application/json")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        global RESULT
        RESULT = json.loads(self.rfile.read(n))
        self._send(200, b'{"ok":true}', "application/json")


import numpy as np  # noqa: E402  (after the functions that lazily need it)

MARKER = {"x": 0.6780143423198108, "z": 0.9660073396941439, "radius": 0.15}
DATA: dict = {}


def run_replay(data: dict, secs: float = 120.0) -> dict:
    global RESULT, DATA
    RESULT = None
    DATA = data
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1000, "height": 600})
        page.goto(f"http://127.0.0.1:{port}/")
        deadline = time.time() + secs
        while RESULT is None and time.time() < deadline:
            time.sleep(0.2)
        browser.close()
    httpd.shutdown()
    if RESULT is None:
        raise RuntimeError("replay did not finish")
    return RESULT


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--topo", required=True)
    ap.add_argument("--shift-us", type=int, default=0,
                    help="twin phase offset (from the suite's curve estimate)")
    ap.add_argument("--phases", default=None,
                    help="JSON {pairIndex: phaseName}")
    ap.add_argument("--stills", default="0,1,2",
                    help="comma-separated pair indices for side-by-side stills")
    ap.add_argument("--stills-dir", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rerun", action="store_true",
                    help="run the whole replay twice (F5 determinism)")
    a = ap.parse_args()

    dump = json.loads(Path(a.dump).read_text(encoding="utf-8"))
    frames = load_truth(a.truth)
    topo = Path(a.topo).read_bytes()
    still_idx = [int(x) for x in a.stills.split(",") if x != ""]
    phases = json.loads(a.phases) if a.phases else {}

    data = build_data(dump, frames, topo, a.shift_us, phases, still_idx)
    res1 = run_replay(data)
    out = {"n_pairs": len(res1["pairs"]), "result": res1}
    if a.rerun:
        res2 = run_replay(data)
        same = (res1["firstCanvasHash"] == res2["firstCanvasHash"]
                and all(p1["mad"] == p2["mad"]
                        for p1, p2 in zip(res1["pairs"], res2["pairs"])))
        out["rerun"] = {"identical": bool(same),
                        "hash1": res1["firstCanvasHash"],
                        "hash2": res2["firstCanvasHash"]}
    mads = [p["mad"] for p in res1["pairs"]]
    if mads:
        out["summary"] = {"median_mad": sorted(mads)[len(mads) // 2],
                          "p95_mad": sorted(mads)[int(0.95 * len(mads))],
                          "max_mad": max(mads)}
    Path(a.out).write_text(json.dumps(out), encoding="utf-8")
    if a.stills_dir:
        import pathlib
        pathlib.Path(a.stills_dir).mkdir(parents=True, exist_ok=True)
        for st in res1["stills"]:
            (pathlib.Path(a.stills_dir) / f"pair_{st['i']:04d}.png").write_bytes(
                base64.b64decode(st["pngB64"]))
    print(json.dumps(out.get("summary", {})), "rerun:",
          out.get("rerun", {}).get("identical"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
