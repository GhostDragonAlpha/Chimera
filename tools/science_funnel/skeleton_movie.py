"""skeleton_movie.py -- engine determinism + argc + scorer-repair lane
(agent/engine-determinism-argc, 2026-09-20). Adapted from the proven
agent/skeleton-movie-20260919 harness: the render path is UNCHANGED
(_post_membrane -> /camera orbit -> _settle_capture -> PNG), the orchestration
now serves THIS lane's three membranes (receipt:
tools/science_funnel/validation/engine_determinism_20260920/receipt.json,
pre-registered block banked before any code edit or measurement).

  M1 SORT STABILITY: the same splat buffer posted via 4 SEPARATE uploads to the
     FIXED engine must render byte-identical PNG frames for the whole 24-frame
     orbit. The engine fix (sort.comp) makes the GPU bitonic sort a stable total
     order: depth key ties are broken by the splat index in the permutation.
  M2 ARGC GUARD: `--hidden --no-restore <port>` and `<port>` alone both start
     and serve; a bad arg exits 1 with a stderr usage message (never
     FAST_FAIL_INVALID_ARG through atoi(nullptr) -- the old `argc > 3` guard
     read argv[4]).
  M3 SCORER REPAIR: discrimination scored on the BANKED posture/anatomy token
     vocabulary (vocab_align below, Jaccard over matched terms) instead of raw
     senses.align text similarity, which scored boilerplate 0.9 on the movie
     lane. The vocabulary is read from the receipt's PRE-REGISTERED block at
     run time -- the banked terms are the only terms; nothing is tuned after a
     score is seen. NO MODEL CALLS: the judgments are the movie lane's own
     recorded verbatim texts (copied read-only into this lane's validation dir).

RENDER PATH (unchanged from the movie lane):
  ct_skeleton_layer.layer_splat_buffer(stride) -> (n,14) splat buffer in scene
  metres (ONE rigid registration, scale 3.2315 scene-units/mm pinned to the
  walker HAT length) -> POST /membrane_bin -> orbit via /camera + the
  settle-capture pattern (cpp_bridge._settle_capture, the fix for the stale
  whole-movies-byte-identical bug) -> PNGs.

LAUNCH NOTE (2026-09-20, FIXED on this lane): the engine no longer aborts when
handed more than one CLI argument -- main() parses argv behind true-argc bounds
and rejects unknown flags with a usage message and exit code 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "tools/science_funnel/validation/engine_determinism_20260920"

ENGINE_FOV_Y_DEG = 45.0      # the engine's vertical FOV (render_splat docstring)
CAMERA_MARGIN = 1.35         # fit margin over the exact FOV fit
ELEVATIONS_RAD = (0.0, 0.45, -0.30)   # level (whole arrangement), above (skull top), below (pelvis underside)


def sha256(raw: bytes) -> str:
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── the splat buffers (true mount + the two pre-named probes) ───────────────

def _trunk_midpoint(buf: np.ndarray) -> np.ndarray:
    """The registration's trunk midpoint (the scene point the layer is seated on),
    recomputed from the buffer as the bbox centre along Y of the central mass."""
    pos = buf[:, 0:3]
    return pos.mean(axis=0)


def probe_rot90(buf: np.ndarray) -> np.ndarray:
    """P1: rotate the placed splats 90 deg about the scene Z axis (left) through
    the trunk midpoint: the upright spine lies horizontal."""
    out = buf.copy()
    c = _trunk_midpoint(buf)
    rel = out[:, 0:3] - c
    x, y = rel[:, 0].copy(), rel[:, 1].copy()
    rel[:, 0] = -y          # Rz(90 deg)
    rel[:, 1] = x
    out[:, 0:3] = rel + c
    return out


def probe_scale_x2(buf: np.ndarray) -> np.ndarray:
    """P2: scale the placed splats x2 about the trunk midpoint: every bone twice
    its mounted size -- positions AND grain sigma (a bone enlarged, not a cloud)."""
    out = buf.copy()
    c = _trunk_midpoint(buf)
    out[:, 0:3] = c + 2.0 * (out[:, 0:3] - c)
    out[:, 7:10] = 2.0 * out[:, 7:10]
    return out


def recenter(buf: np.ndarray) -> np.ndarray:
    """Framing normalization, recorded: the engine's orbit camera always looks at
    the ORIGIN, so each condition's buffer is translated so its bounding-box
    centre sits at the origin. The registration itself is untouched (this is a
    render-time framing decision applied IDENTICALLY to the true mount and both
    probes; the camera radius/elevations are identical across conditions)."""
    out = buf.copy()
    pos = out[:, 0:3]
    out[:, 0:3] = pos - (pos.min(axis=0) + pos.max(axis=0)) / 2.0
    return out


# ── the render: one orbit movie through the splat shell ─────────────────────

def derive_camera(buf: np.ndarray) -> dict:
    """Camera radius derived from the TRUE buffer's bounding box and the engine's
    45 deg vertical FOV (no taste): fit the height, apply the fit margin once."""
    pos = buf[:, 0:3]
    lo, hi = pos.min(axis=0), pos.max(axis=0)
    height = float(hi[1] - lo[1])
    half_fov = math.radians(ENGINE_FOV_Y_DEG) / 2.0
    radius = CAMERA_MARGIN * (height / 2.0) / math.tan(half_fov)
    return {
        "bbox_min_m": [round(float(v), 6) for v in lo],
        "bbox_max_m": [round(float(v), 6) for v in hi],
        "bbox_height_m": round(height, 6),
        "fov_y_deg": ENGINE_FOV_Y_DEG,
        "camera_margin": CAMERA_MARGIN,
        "radius_m": round(radius, 6),
        "elevations_rad": list(ELEVATIONS_RAD),
    }


def _retry_urlopen(req, timeout: float, attempts: int = 4):
    """The engine serves HTTP on ONE worker; a STRICTLY FRESH /frame wait blocks
    that worker, so a POST arriving mid-wait can hit a full listen backlog
    (WinError 10061, measured 2026-09-20 while settling). Retry with backoff."""
    last = None
    for i in range(attempts):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            last = e
            time.sleep(0.25 * (i + 1))
    raise last


def _post_membrane(engine_url: str, buf: np.ndarray, radius: float, theta: float,
                   phi: float, timeout: float = 120.0) -> bool:
    """POST the (n,14) float32 buffer to /membrane_bin (the ct_skeleton_layer contract)."""
    n = int(buf.shape[0])
    header = struct.pack("<I3f", n, float(radius), float(theta), float(phi))
    payload = header + np.ascontiguousarray(buf, dtype=np.float32).tobytes()
    req = urllib.request.Request(f"{engine_url.rstrip('/')}/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"},
                                 method="POST")
    with _retry_urlopen(req, timeout=timeout) as resp:
        return resp.status == 200 and b'"ok":true' in resp.read()


def _set_camera(engine_url: str, radius: float, theta: float, phi: float,
                timeout: float = 10.0) -> bool:
    payload = json.dumps({"cam_radius": radius, "cam_theta": theta, "cam_phi": phi}).encode("utf-8")
    req = urllib.request.Request(f"{engine_url.rstrip('/')}/camera", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with _retry_urlopen(req, timeout=timeout) as resp:
        return resp.status == 200


def _fetch_frame(engine_url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(f"{engine_url.rstrip('/')}/frame")
    with _retry_urlopen(req, timeout=timeout) as r:
        return r.read()


def _settle_capture(engine_url: str, prev: bytes | None, timeout: float = 12.0) -> bytes:
    """cpp_bridge._settle_capture, engine-url parameterised and HARDENED for the
    determinism falsifier: /frame is strictly fresh (each GET captures NOW), and
    a /camera change lands on the render loop's NEXT iteration -- but the FIRST
    differing capture can still catch a transitional render (a mid-sort frame
    after a buffer/camera swap: measured 2026-09-20, 2 of 24 frames differed
    between identical runs with a first-differing-frame capture). So: keep
    fetching until TWO CONSECUTIVE fresh captures are byte-equal to each other
    AND (when a reference is given) differ from it -- a quiesced render."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        b = _fetch_frame(engine_url, timeout=timeout)
        if prev is not None and b == prev:
            last = None
            time.sleep(0.08)
            continue
        if last is not None and b == last:
            return b
        last = b
        time.sleep(0.08)
    return _fetch_frame(engine_url, timeout=timeout)


def render_orbit(engine_url: str, buf: np.ndarray, out_dir: Path, tag: str,
                 frames: int, radius: float) -> dict:
    """One orbit of `buf` through the engine -> {pngs, hashes, orbit_seconds}.

    The buffer POST carries the initial camera (radius, theta=0, phi=0) in its
    header; every later stop is a /camera POST + a quiesced settle capture --
    exactly the movie lane's render path. `radius` is passed in: the caller
    derives it ONCE and pins it across uploads (and would pin it across
    conditions), so an orbit never auto-frames its own buffer."""
    buf = recenter(buf)               # framing: bbox centre -> the camera's look-at (origin)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    n_elev = len(ELEVATIONS_RAD)
    per_orbit = max(1, frames // n_elev)
    paths, hashes = [], []
    prev = None
    idx = 0
    t0 = time.time()
    for phi in ELEVATIONS_RAD:
        for i in range(per_orbit):
            theta = 2.0 * math.pi * i / per_orbit
            if idx == 0:
                # the buffer POST carries the initial camera in its header; the
                # settle reference is the PRE-POST frame so frame 0 is always the
                # posted membrane quiesced at theta=0 (not the previous state)
                pre = _fetch_frame(engine_url)
                ok = _post_membrane(engine_url, buf, radius, theta, phi)
                if not ok:
                    raise RuntimeError("membrane_bin POST refused")
                b = _settle_capture(engine_url, pre)
            else:
                if not _set_camera(engine_url, radius, theta, phi):
                    raise RuntimeError("camera POST refused")
                b = _settle_capture(engine_url, prev)
            png = out / f"{tag}_f{idx:03d}.png"
            png.write_bytes(b)
            prev = b
            paths.append(str(png))
            hashes.append(sha256(b))
            idx += 1
    return {"tag": tag, "pngs": paths, "frame_sha256": hashes,
            "orbit_seconds": round(time.time() - t0, 2)}


# ── M3: the banked-vocabulary scorer (no model calls) ───────────────────────

def banked_vocabulary(receipt_path: Path | None = None) -> dict:
    """The vocabulary EXACTLY as banked in the receipt's pre-registered block.

    Reading the terms from the receipt (not from a second list in this file)
    is the point: the banked block is the single source of truth, so the
    instrument cannot drift from what was registered before the measurement."""
    p = Path(receipt_path) if receipt_path else VALIDATION / "receipt.json"
    receipt = json.loads(p.read_text(encoding="utf-8"))
    return receipt["rule0_pre_registered"]["m3_scorer_repair"]["instrument_details"]["vocabulary"]


def match_terms(report: str, vocab: dict) -> set:
    """Vocabulary terms hit by `report`: word-boundary, case-insensitive for
    single words; multiword entries matched literally across whitespace.
    Returns the set of matched TERM STRINGS."""
    text = report or ""
    hits = set()
    for terms in vocab.values():
        for term in terms:
            if " " in term or "-" in term:
                pat = r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"\b"
            else:
                pat = r"\b" + re.escape(term) + r"\b"
            if re.search(pat, text, flags=re.IGNORECASE):
                hits.add(term)
    return hits


def vocab_align(report_a: str, report_b: str, vocab: dict | None = None) -> float:
    """The M3 discrimination instrument: Jaccard over the two reports' matched
    vocabulary term sets (|A and B| / |A or B|). 0.0 when BOTH sides match
    nothing -- no vocabulary evidence of alignment is a score of 0, never a
    NaN. Boilerplate ("a single isolated object on a black background") holds
    no vocabulary terms and cannot contribute. Banked BEFORE any score was
    seen; the discrimination gate (< 0.5 = distinguished) is the movie lane's
    own pre-registered rule."""
    if vocab is None:
        vocab = banked_vocabulary()
    a, b = match_terms(report_a, vocab), match_terms(report_b, vocab)
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def score_recorded_judgments(jdir: Path | None = None) -> dict:
    """M3 measurement: vocab_align(true, P1) and vocab_align(true, P2) on the
    movie lane's OWN RECORDED verbatim judgments (the judgement_*.json copied
    read-only from its validation dir). No model call anywhere."""
    d = Path(jdir) if jdir else VALIDATION
    names = {"true": "judgement_true.json",
             "p1_trunk_rot90": "judgement_p1_trunk_rot90.json",
             "p2_scale_x2": "judgement_p2_scale_x2.json"}
    reports, models = {}, {}
    for key, name in names.items():
        j = json.loads((d / name).read_text(encoding="utf-8"))
        reports[key] = j.get("report")
        models[key] = j.get("model")
        if not reports[key]:
            raise RuntimeError(f"{name} carries no verbatim report -- nothing to score")

    vocab = banked_vocabulary()
    out = {
        "schema": "chimera.scorer_repair.v1",
        "taken_utc": now_utc(),
        "judgment_sources": {"lane": "agent/skeleton-movie-20260919 "
                                     "(verbatim recorded judgments, copied read-only)",
                             "models": models},
        "vocabulary_source": "receipt.json rule0_pre_registered.m3_scorer_repair"
                             ".instrument_details.vocabulary (banked before this run)",
        "instrument": "vocab_align = Jaccard over matched banked-vocabulary term "
                      "sets; 0.0 when both sides match nothing; gate < 0.5 = "
                      "distinguished (the movie lane's own pre-registered rule)",
        "matched_terms": {k: sorted(match_terms(v, vocab)) for k, v in reports.items()},
        "vocab_align_true_vs_p1": vocab_align(reports["true"], reports["p1_trunk_rot90"], vocab),
        "vocab_align_true_vs_p2": vocab_align(reports["true"], reports["p2_scale_x2"], vocab),
    }
    out["p1_distinguished"] = out["vocab_align_true_vs_p1"] < 0.5
    out["p2_distinguished"] = out["vocab_align_true_vs_p2"] < 0.5
    out["pass"] = bool(out["p1_distinguished"] and out["p2_distinguished"])
    return out


# ── M1: the cross-upload determinism measurement ────────────────────────────

def determinism_run(engine_url: str, uploads: int, frames: int, stride: int,
                    scratch: Path) -> dict:
    """The M1 falsifier, measured: the SAME splat buffer (built once, identical
    bytes every POST) is posted via `uploads` SEPARATE /membrane_bin uploads;
    each upload renders the full `frames`-frame orbit; the PNG frames are
    byte-compared across uploads (and, where bytes differ, scored with the
    movie lane's per-pixel delta: int16 abs difference of the decoded RGBs,
    max over channels; pixels_differing = count of pixels with delta > 0)."""
    from PIL import Image

    from tools.science_funnel import ct_skeleton_layer as csl
    buf, record = csl.layer_splat_buffer(stride)
    raw_bytes = np.ascontiguousarray(recenter(buf), dtype=np.float32).tobytes()
    radius = derive_camera(buf)["radius_m"]

    print(f"[determinism] splats: {record['splats']} (stride {stride}), "
          f"buffer bytes: {len(raw_bytes)}, radius: {radius}", flush=True)
    print(f"[determinism] engine: {engine_url}, uploads: {uploads}, frames: {frames}",
          flush=True)

    runs = []
    for u in range(1, uploads + 1):
        print(f"[determinism] upload {u}/{uploads}: orbit...", flush=True)
        run = render_orbit(engine_url, buf, scratch / f"upload{u}", f"u{u}", frames, radius)
        runs.append(run)
        print(f"   {run['orbit_seconds']} s", flush=True)

    ref = runs[0]
    frames_cmp = []
    for k in range(len(ref["pngs"])):
        pa = Path(ref["pngs"][k])
        byte_ref = pa.read_bytes()
        first_diff_upload = None
        worst_pixels, worst_delta = 0, 0
        n_identical = uploads
        for u in range(1, uploads):
            pb = Path(runs[u]["pngs"][k])
            if pb.read_bytes() == byte_ref:
                continue
            n_identical -= 1
            if first_diff_upload is None:
                first_diff_upload = u + 1
            a = np.asarray(Image.open(pa).convert("RGB"), dtype=np.int16)
            b = np.asarray(Image.open(pb).convert("RGB"), dtype=np.int16)
            d = np.abs(a - b).max(axis=2)
            worst_pixels = max(worst_pixels, int((d > 0).sum()))
            worst_delta = max(worst_delta, int(d.max()))
        entry = {"frame": pa.name, "identical_uploads": n_identical}
        if n_identical != uploads:
            entry.update({"pixels_differing_worst_pair": worst_pixels,
                          "max_pixel_delta": worst_delta,
                          "first_differing_vs_upload": first_diff_upload})
        frames_cmp.append(entry)

    return {
        "schema": "chimera.engine_determinism.v1",
        "taken_utc": now_utc(),
        "engine": engine_url,
        "uploads": uploads,
        "frames_per_orbit": frames,
        "splats": record["splats"],
        "buffer_bytes": len(raw_bytes),
        "buffer_sha256": sha256(raw_bytes),
        "layer_record": record,
        "camera_radius_m": radius,
        "upload_orbit_seconds": [r["orbit_seconds"] for r in runs],
        "upload_frame_sha256": [r["frame_sha256"] for r in runs],
        "frames": frames_cmp,
        "all_frames_byte_identical_across_uploads": all(
            f["identical_uploads"] == uploads for f in frames_cmp),
    }


# ── orchestration ────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", default="http://localhost:8129")
    ap.add_argument("--out", type=Path, default=VALIDATION)
    ap.add_argument("--scratch", type=Path, default=ROOT / ".tmp/engine-determinism")
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--stride", type=int, default=3)
    ap.add_argument("--uploads", type=int, default=4)
    ap.add_argument("--determinism", action="store_true",
                    help="M1: post the layer buffer via N separate uploads and "
                         "byte-compare the whole orbit across uploads")
    ap.add_argument("--score-only", action="store_true",
                    help="M3: vocab_align the RECORDED judgments (no engine, "
                         "no model calls)")
    args = ap.parse_args(argv)

    if args.score_only:
        result = score_recorded_judgments(args.out)
        (args.out / "scorer_repair_scores.json").write_text(
            json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({k: result[k] for k in
                          ("vocab_align_true_vs_p1", "vocab_align_true_vs_p2",
                           "p1_distinguished", "p2_distinguished", "pass")}, indent=1))
        return 0

    if args.determinism:
        args.scratch.mkdir(parents=True, exist_ok=True)
        args.out.mkdir(parents=True, exist_ok=True)
        result = determinism_run(args.engine, args.uploads, args.frames,
                                 args.stride, args.scratch)
        (args.out / "determinism_record.json").write_text(
            json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"all_frames_byte_identical_across_uploads":
                          result["all_frames_byte_identical_across_uploads"],
                          "upload_orbit_seconds": result["upload_orbit_seconds"]},
                         indent=1))
        return 0

    print("nothing to do: pass --determinism (M1) and/or --score-only (M3); "
          "M2 is exercised by the launch matrix in the receipt")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
