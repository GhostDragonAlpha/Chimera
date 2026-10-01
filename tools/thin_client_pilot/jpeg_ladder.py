"""jpeg_ladder.py -- the PIXEL family's coupled measurement (F1's pixel arm).

At the settled fixed point the scene is bit-stable (the playable-slice
receipt's own bar), so two pulls are the SAME instant and the compressed
candidate can be compared EXACTLY against its same-instant PNG reference:

  reference: /frame (full-res PNG) and /frame?w=<w> (the box-step PNG)
  candidates: /frame?fmt=jpg&q=<q>[&w=<w>]

Metrics per candidate: bytes, MAD vs its same-size PNG reference (0-255
scale, numpy), and bytes/s at each declared rate. The bandwidth table for
the STATE family comes from run_suite's paced puller; this script adds the
pixel family rows and writes pixel_ladder.json.

Usage: python jpeg_ladder.py --base http://127.0.0.1:PORT --out pixel_ladder.json
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import time
import urllib.request

import numpy as np
from PIL import Image

RATES = [60, 30, 15, 10]
BUDGET_BYTES_S = 1_250_000   # BUDGET-BW (prereg): 1.25 MB/s at 30 Hz
BUDGET_MAD = 2.0             # BUDGET-VIS (prereg)
LADDER_Q = [95, 85, 80, 70, 50, 30]


def get(base: str, path: str, timeout: int = 30) -> bytes:
    # pixel pulls go through the slice door (/api/frame -> engine /frame),
    # exactly the path a thin pixel client would take
    if path.startswith("/frame"):
        path = "/api/frame" + path[len("/frame"):]
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def to_array(raw: bytes) -> np.ndarray:
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.asarray(im, dtype=np.int16)


def wait_settled_true(base: str, timeout: float = 150.0) -> None:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        st = json.loads(get(base, "/api/status"))["engine_state"]
        y, vy = float(st["root_y"]), abs(float(st["root_vy"]))
        if vy < 1e-5 and last is not None and abs(y - last) < 1e-9:
            return
        last = y
        time.sleep(0.5)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    base = a.base
    wait_settled_true(base)

    # byte-stability check at the fixed point (the same-instant premise)
    p1 = get(base, "/frame?w=640")
    p2 = get(base, "/frame?w=640")
    stable = (p1 == p2)
    rec: dict = {"fixed_point_byte_stable_frames": bool(stable)}

    refs: dict = {}
    ref_png_full = get(base, "/frame")
    refs["full"] = ref_png_full
    for w, step_dims in (("1280", None), ("960", None), ("640", None)):
        # the engine's ?w= is an integer box STEP: served width = W/floor(W/w)
        refs[w] = get(base, f"/frame?w={w}")

    def dims(raw: bytes) -> tuple:
        im = Image.open(io.BytesIO(raw))
        return im.size

    rows: dict = {}
    # full-res PNG row (today's historical camera path)
    a_ref = to_array(ref_png_full)
    rows["png_full"] = {"bytes": len(ref_png_full), "dims": list(dims(ref_png_full)),
                        "mad_vs_ref": 0.0,
                        "bytes_s_at_30hz": len(ref_png_full) * 30}
    for w, ref in list(refs.items()):
        if w == "full":
            continue
        rows[f"png_w{w}"] = {"bytes": len(ref), "dims": list(dims(ref)),
                             "mad_vs_ref": 0.0,
                             "bytes_s_at_30hz": len(ref) * 30}
    for w in ("1280", "960", "640"):
        a_ref = to_array(refs[w])
        for q in LADDER_Q:
            raw = get(base, f"/frame?w={w}&fmt=jpg&q={q}")
            arr = to_array(raw)
            mad = float(np.abs(arr - a_ref).mean())
            rows[f"jpg_w{w}_q{q}"] = {
                "bytes": len(raw), "dims": list(dims(raw)),
                "mad_vs_png_same_w": round(mad, 3),
                "vis_budget_ok": mad <= BUDGET_MAD,
                "bytes_s_at_30hz": len(raw) * 30,
                "bw_budget_ok_at_30hz": len(raw) * 30 <= BUDGET_BYTES_S}
    raw = get(base, "/frame?fmt=jpg&q=80")
    arr = to_array(raw)
    mad = float(np.abs(arr - to_array(ref_png_full)).mean())
    rows["jpg_full_q80"] = {"bytes": len(raw), "dims": list(dims(raw)),
                            "mad_vs_png_same_w": round(mad, 3),
                            "vis_budget_ok": mad <= BUDGET_MAD,
                            "bytes_s_at_30hz": len(raw) * 30,
                            "bw_budget_ok_at_30hz": len(raw) * 30 <= BUDGET_BYTES_S}

    # derived: P1's >=2x cut check (jpeg q80 w-step-2 vs png same size)
    if "jpg_w1280_q80" in rows and "png_w1280" in rows and rows["png_w1280"]["bytes"]:
        rec["P1_jpg_q80_w1280_cut_factor"] = round(
            rows["png_w1280"]["bytes"] / rows["jpg_w1280_q80"]["bytes"], 1)
    rec["rows"] = rows
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec.get("P1_jpg_q80_w1280_cut_factor", None)),
          "stable:", rec["fixed_point_byte_stable_frames"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
