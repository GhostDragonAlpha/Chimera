"""dyad02_coplanarity_control.py -- GLM-DYAD-02 step 1: the controlled test.

The round-3 dyad flagged horizontal banding + a black lens where the flat
membrane lies COPLANAR with the engine floor (both rasterize the y=0 plane).
Source inspection supports the mechanism (engine.cpp builds floor + shadow
pipelines at y=0), but per the task the coplanar-depth-conflict story is a
HYPOTHESIS until this controlled comparison supports it:

  Same uploaded state (the untouched B2 fixture, single-vertex bump),
  same camera (radius 4.0, theta 0.0, phi 1.10), same render mode:
    A) presentation lift 0.0   (rim coplanar with the floor plane)
    B) presentation lift +0.5  (the preregistered rigid lift)

METRIC: inside the projected mesh region (central box of the frame), count
near-black pixels (luminance < 20; background is ~32, mesh fill ~106+).
The banding/lens artifact is near-black INSIDE the fill. Prediction: A
shows the artifact, B does not. Falsifier: both show it, neither does, or
B shows more (the hypothesis then fails as stated and the ambiguity's
cause remains open).

This tool drives ONLY the isolated demo instance recorded in
launch_20260908T183000Z/launch_record.json. It performs its own uploads
(every capture is blob-corroborated at capture time).
"""
from __future__ import annotations

import json
import struct
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zlib import crc32

import numpy as np

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import membrane_window_demo as demo  # noqa: E402

ENGINE_URL = "http://localhost:8091"
CAM = {"radius": 4.0, "theta": 0.0, "phi": 1.10}
OUTDIR = ROOT / "docs" / "evidence" / "membrane_window_demo" / (
    "dyad02_control_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))


def http_post(url: str, body: bytes, ctype: str):
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": ctype}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()


def http_get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.status, r.read(), r.headers.get("Content-Type", "")


def png_rgba(png: bytes) -> np.ndarray:
    """Minimal PNG decode for the engine's captured frames: parse IHDR and
    IDAT, undo zlib and the per-scanline filters. Supports 8-bit RGB/RGBA."""
    import zlib
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w, h, ct = 8, b"", 0, 0, 6
    while pos < len(png):
        ln, typ = struct.unpack_from(">I4s", png, pos)
        chunk = png[pos + 8: pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ct = struct.unpack_from(">IIBB", chunk)
            assert depth == 8, f"unsupported bit depth {depth}"
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    ch = 4 if ct == 6 else (3 if ct == 2 else None)
    assert ch is not None, f"unsupported colour type {ct}"
    raw = zlib.decompress(idat)
    stride = w * ch
    out = np.zeros((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.int32)
    p = 0
    for y in range(h):
        f = raw[p]
        line = np.frombuffer(raw[p + 1: p + 1 + stride], dtype=np.uint8).copy()
        p += 1 + stride
        if f == 0:
            cur = line.astype(np.int32)
        elif f == 1:
            cur = line.astype(np.int32)
            for i in range(ch, stride):
                cur[i] = (cur[i] + cur[i - ch]) & 0xFF
        elif f == 2:
            cur = (line.astype(np.int32) + prev) & 0xFF
        elif f == 3:
            cur = line.astype(np.int32)
            for i in range(stride):
                a = cur[i - ch] if i >= ch else 0
                cur[i] = (cur[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            cur = line.astype(np.int32)
            for i in range(stride):
                a = int(cur[i - ch]) if i >= ch else 0
                b = int(prev[i])
                c = int(prev[i - ch]) if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 0xFF
        else:
            raise ValueError(f"unknown filter {f}")
        out[y] = cur.astype(np.uint8)
        prev = cur
    img = out.reshape(h, w, ch).astype(np.int32)
    return img[:, :, :3]


def mesh_region_metrics(img: np.ndarray) -> dict:
    h, w, _ = img.shape
    y0, y1 = int(h * 0.30), int(h * 0.70)
    x0, x1 = int(w * 0.30), int(w * 0.70)
    box = img[y0:y1, x0:x1]
    lum = box.mean(axis=2)
    near_black = int((lum < 20).sum())
    fill = int(((lum >= 60) & (lum <= 200)).sum())
    return {
        "box": [x0, y0, x1, y1],
        "near_black_px": near_black,
        "fill_px": fill,
        "near_black_fraction_of_fill": (near_black / fill) if fill else None,
        "mean_luminance_box": float(lum.mean()),
    }


def capture(label: str, positions_f64: np.ndarray, faces: np.ndarray,
            lift_m: float) -> dict:
    payload = demo.encode_mesh_bin(positions_f64, faces, CAM["radius"],
                                   CAM["theta"], CAM["phi"], demo.SLOTMODE,
                                   lift_m=lift_m)
    st, body = http_post(f"{ENGINE_URL}/mesh_bin", payload,
                         "application/octet-stream")
    assert st == 200 and b'"ok":true' in body, (st, body[:120])
    cam = json.dumps({"cam_radius": CAM["radius"], "cam_theta": CAM["theta"],
                      "cam_phi": CAM["phi"]}).encode()
    http_post(f"{ENGINE_URL}/camera", cam, "application/json")
    st, png, ctype = http_get(f"{ENGINE_URL}/frame")
    assert st == 200 and "image/png" in ctype, (st, ctype)
    png_path = OUTDIR / f"{label}.png"
    png_path.write_bytes(png)
    upload32 = demo.upload_positions_f32(positions_f64, lift_m=lift_m)
    blob_hash = demo.blob_position_hash()
    assert blob_hash == demo.sha256_bytes(upload32), "blob corroboration failed"
    img = png_rgba(png)
    metrics = mesh_region_metrics(img)
    rec = {
        "label": label, "png": str(png_path.relative_to(ROOT)),
        "png_sha256": demo.sha256_bytes(png),
        "camera": CAM, "presentation_lift_metres": lift_m,
        "upload_positions_f32le_sha256": demo.sha256_bytes(upload32),
        "blob_position_hash_at_capture": blob_hash,
        "blob_corroboration": "MATCH",
        "region_metrics": metrics,
    }
    print(f"{label}: lift={lift_m} near_black={metrics['near_black_px']} "
          f"fill={metrics['fill_px']} "
          f"frac={metrics['near_black_fraction_of_fill']}")
    return rec


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=False)
    b2 = demo.load_b2()
    positions, faces = b2["positions"], b2["faces"]

    # A: the ORIGINAL coplanar presentation (lift 0.0)
    a = capture("lift0_coplanar", positions, faces, lift_m=0.0)
    # B: the preregistered rigid presentation lift
    b = capture("lift1_presented", positions, faces,
                lift_m=demo.PRESENTATION_LIFT_M)

    fa, fb = a["region_metrics"], b["region_metrics"]
    supported = (fa["near_black_px"] > 5 * max(fb["near_black_px"], 1) and
                 fb["near_black_px"] < 0.05 * max(fb["fill_px"], 1))
    record = {
        "schema": "chimera-dyad02-coplanarity-control-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "task": "GLM-DYAD-02",
        "hypothesis": "the round-3 banding/black-lens artifact is the "
                      "coplanar depth conflict between the flat membrane and "
                      "the engine's floor/shadow plane (both rasterize y=0)",
        "control": "identical uploaded state + camera + render mode; only the "
                   "preregistered rigid presentation lift differs (0.0 vs "
                   "+0.5 m along engine y)",
        "metric": "near-black pixels (luminance < 20) inside the projected "
                  "mesh region (central 40% x 40% box); background ~32, "
                  "fill ~106+",
        "captures": [a, b],
        "artifact_supported_by_control": bool(supported),
        "interpretation": ("supported: the coplanar presentation shows the "
                           "artifact and the lifted presentation does not"
                           if supported else
                           "NOT supported by this control: the ambiguity's "
                           "cause remains open; report descriptively"),
        "operator_engine_untouched": True,
    }
    (OUTDIR / "control_record.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    print(f"supported={supported} -> {OUTDIR / 'control_record.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
