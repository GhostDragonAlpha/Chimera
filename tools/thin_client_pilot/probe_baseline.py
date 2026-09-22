"""probe_baseline.py -- measure TODAY's snapshot path on the declared scene,
before any thin-client code exists. The numbers this prints are the prereg's
"what the current path emits" baseline:
  - /api/verts payload bytes (today's page polls this at 10 Hz, untimed swap)
  - /api/topology one-time bytes
  - /tick_state authoritative ts_us + ticks (the timestamp the client lacks)
  - /frame pixel family: full PNG, ?w=960 PNG, JPEG ladder (?fmt=jpg&q=)
  - /verts?delta=1 C3 chain: key + delta frame sizes at rest
  - engine tick rate: idle vs under the page's 10 Hz /api/verts poll

Usage: python probe_baseline.py --base http://127.0.0.1:PORT --out OUT.json
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import struct
import threading
import time
import urllib.request


def get_raw(base: str, path: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def get_json(base: str, path: str, timeout: int = 30) -> dict:
    return json.loads(get_raw(base, path, timeout))


def frame_dims(raw: bytes) -> list[int]:
    from PIL import Image
    im = Image.open(io.BytesIO(raw))
    return list(im.size)


def median(vals: list[float]) -> float:
    return statistics.median(vals)


def pct95(vals: list[float]) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(0.95 * len(s)))]


def tick_rate(eng: str, seconds: float, poll_hz: float = 20.0) -> dict:
    """engine ticks/s from the engine's OWN ticks field (not a wall guess)."""
    t0 = None
    ticks0 = None
    n = max(2, int(seconds * poll_hz))
    for _ in range(n):
        st = get_json(eng, "/tick_state")
        if t0 is None:
            t0 = time.perf_counter()
            ticks0 = int(st["ticks"])
        time.sleep(1.0 / poll_hz)
    t1 = time.perf_counter()
    ticks1 = int(get_json(eng, "/tick_state")["ticks"])
    return {"window_s": round(t1 - t0, 3), "ticks": ticks1 - ticks0,
            "ticks_per_s": round((ticks1 - ticks0) / (t1 - t0), 1)}


def poller_load(slice_base: str, stop: threading.Event, interval: float,
                sink: list) -> None:
    """the page's poll loop: /api/verts every `interval` s (sizes sunk)."""
    while not stop.is_set():
        t0 = time.perf_counter()
        try:
            b = get_raw(slice_base, "/api/verts")
            sink.append((time.perf_counter() - t0, len(b)))
        except OSError:
            pass
        stop.wait(interval)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True,
                    help="slice server base (state family: /api/*)")
    ap.add_argument("--engine", required=True,
                    help="engine base (raw contract: /verts /frame /tick_state)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    base = a.base
    eng = a.engine
    rec: dict = {"base": base, "engine": eng, "measured_at_unix": time.time()}

    # ── state family today ────────────────────────────────────────────
    verts_sizes = []
    for _ in range(50):
        verts_sizes.append(len(get_raw(base, "/api/verts")))
    rec["api_verts"] = {
        "n": len(verts_sizes),
        "median_B": int(median(verts_sizes)),
        "p95_B": int(pct95(verts_sizes)),
        "derived_framing_B": "4 + nverts*36",
    }
    topo = get_raw(base, "/api/topology")
    tris = struct.unpack_from("<I", topo, 0)[0] if len(topo) >= 4 else 0
    nverts = struct.unpack_from("<I", get_raw(base, "/api/verts"), 0)[0]
    rec["topology"] = {"bytes": len(topo), "triangles": int(tris)}
    rec["verts_count"] = int(nverts)

    st = get_json(eng, "/tick_state")
    rec["tick_state_fields_present"] = sorted(
        k for k in ("ts_us", "ts_ms", "ticks", "root_y", "root_vy",
                    "dimple_m", "P_lower", "P_upper") if k in st)
    rec["tick_state_snapshot"] = {k: st.get(k) for k in
                                  ("ts_us", "ticks", "root_y", "root_vy",
                                   "dimple_m", "gravity_on")}
    rec["verts_carries_timestamp"] = False   # measured structurally: framing is
    # [u32 n][36B*vert] only -- no ts field exists anywhere in the payload

    # ── C3 delta chain at rest ────────────────────────────────────────
    key = get_raw(eng, "/verts?delta=key")
    d1 = get_raw(eng, "/verts?delta=1")
    d2 = get_raw(eng, "/verts?delta=1")
    def framing(raw: bytes) -> dict:
        if len(raw) < 16 or raw[0] != 0xD1:
            return {"framing": "legacy_full", "bytes": len(raw)}
        flags = raw[1]
        seq = struct.unpack_from("<I", raw, 8)[0]
        runs = struct.unpack_from("<I", raw, 12)[0]
        return {"framing": "C3_delta", "flags": flags, "seq": seq,
                "runs": runs, "bytes": len(raw)}
    rec["c3_delta_at_rest"] = {"key_pull": framing(key),
                               "delta_pull_1": framing(d1),
                               "delta_pull_2": framing(d2)}

    # ── engine tick rate: idle vs today's 10 Hz page poll ─────────────
    rec["ticks_idle"] = tick_rate(eng, 5.0)
    stop = threading.Event()
    sink: list = []
    th = threading.Thread(target=poller_load, args=(base, stop, 0.10, sink),
                          daemon=True)
    th.start()
    time.sleep(0.5)
    rec["ticks_under_10hz_verts_poll"] = tick_rate(eng, 10.0)
    stop.set()
    th.join(timeout=5)
    if sink:
        rec["poll_roundtrip_s_under_load"] = {
            "n": len(sink), "median_s": round(median([x[0] for x in sink]), 5),
            "p95_s": round(pct95([x[0] for x in sink]), 5)}
        wire = [x[1] for x in sink]
        rec["today_path_bandwidth"] = {
            "rate_hz": 10.0,
            "median_payload_B": int(median(wire)),
            "bytes_per_s": int(median(wire) * 10.0),
            "MB_per_s": round(median(wire) * 10.0 / 1e6, 3)}

    # ── pixel family (PNG today + JPEG ladder) ────────────────────────
    px: dict = {}
    pulls = [
        ("png_full", "/frame"),
        ("png_w960", "/frame?w=960"),
        ("png_w640", "/frame?w=640"),
    ]
    for q in (95, 85, 80, 70, 50, 30):
        pulls.append((f"jpg_w960_q{q}", f"/frame?w=960&fmt=jpg&q={q}"))
    pulls.append(("jpg_full_q80", "/frame?fmt=jpg&q=80"))
    for name, path in pulls:
        t0 = time.perf_counter()
        raw = get_raw(eng, path)
        dt = time.perf_counter() - t0
        entry = {"bytes": len(raw), "pull_s": round(dt, 4)}
        if raw[:4] == b"\x89PNG":
            entry["fmt"] = "png"
            entry["dims"] = frame_dims(raw)
        elif raw[:3] == b"\xff\xd8\xff":
            entry["fmt"] = "jpeg"
            entry["dims"] = frame_dims(raw)
        else:
            entry["fmt"] = raw[:40].decode("utf-8", "replace")
        px[name] = entry
        time.sleep(0.05)
    rec["pixel_family"] = px

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: rec[k] for k in (
        "api_verts", "verts_count", "topology", "today_path_bandwidth",
        "ticks_idle", "ticks_under_10hz_verts_poll")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
