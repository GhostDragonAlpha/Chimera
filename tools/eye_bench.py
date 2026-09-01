"""eye_bench.py — MEASURE an eye's ability to do OUR job. Not benchmarks. This job.

    python tools/eye_bench.py [--cases 4] [--model notes]

WHY THIS EXISTS. Picking a vision model off download counts and leaderboard
scores is treating a proxy as a measurement. The job here is specific: find a
hole/tear in a triangle mesh, on the right body part, in a 2560x1440 engine
window full of small UI text. Nothing on a leaderboard measures that.

So we measure it. The engine is the oracle: we INJECT a defect at a known place,
then ask the eye where it is. The answer is either right or it isn't.

THE CASES (a defect at a known body location, plus one NEGATIVE CONTROL):

  clean        nothing removed   -> the eye MUST say none. A model that invents
                                    defects on a clean mesh is worse than useless:
                                    every report becomes unfalsifiable noise.
  chest_hole   triangles near the chest removed
  neck_tear    triangles near the neck removed
  foot_cut     triangles near one foot removed

The negative control is the Triangle Guide's own rule: run a check against a case
that MUST fail (here, must say "none") to prove the check can fail at all. A bench
with no placebo is a bench that can only ever report success.

THE ASK IS BOUNDED ON PURPOSE. Measured: a one-sentence ask costs ~18s, an
open-ended report ~70s, and both find the same defects. Decode dominates, so a
short ask makes the bench cheap enough to run on every candidate.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path("E:/PythonChimera")
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import trimesh

import cpp_bridge
import senses

OUT = ROOT / "Saved" / "eye_bench"

# where the mesh actually is (from tools/mesh_to_bin.py on the B1 birth artifact)
BASE_BIN = ROOT / "Saved" / "meshes" / "monkey_birth.bin"
BASE_GLB = ROOT / ".tmp/monkey_assets/recon/8955fb5b9c9b4e169456ccbae7c465f7_birth.glb"

ASK = ("Look only at the 3D animal body in the centre of this window. Is there a "
       "hole, tear, or missing patch of surface on it? Answer in this exact form:\n"
       "PART: <the body part, one or two words>   or   PART: NONE if the surface is intact.\n"
       "Then one short sentence saying what you see there. Nothing else.")


def load_base():
    """(verts float32 Nx3, tris uint32 Mx3) for the pipeline's monkey."""
    if BASE_BIN.exists():
        raw = BASE_BIN.read_bytes()
        n, m = np.frombuffer(raw[:8], dtype="<i4")
        v = np.frombuffer(raw[8:8 + n * 12], dtype="<f4").reshape(n, 3)
        f = np.frombuffer(raw[8 + n * 12:8 + n * 12 + m * 12], dtype="<u4").reshape(m, 3)
        return v.copy(), f.copy()
    m = trimesh.load(str(BASE_GLB), force="mesh")
    return (np.asarray(m.vertices, dtype=np.float32),
            np.asarray(m.faces, dtype=np.uint32))


def punch(v: np.ndarray, f: np.ndarray, at, radius: float):
    """Remove triangles whose centroid is within `radius` of `at` — a hole with a
    known location. Returns (kept_tris, how_many_removed)."""
    cen = v[f].mean(axis=1)
    d = np.linalg.norm(cen - np.asarray(at, dtype=np.float64), axis=1)
    keep = d > radius
    return f[keep], int((~keep).sum())


def write_bin(path: Path, v: np.ndarray, f: np.ndarray) -> None:
    import struct
    with open(path, "wb") as fh:
        fh.write(struct.pack("<ii", len(v), len(f)))
        fh.write(np.ascontiguousarray(v, dtype="<f4").tobytes())
        fh.write(np.ascontiguousarray(f, dtype="<u4").tobytes())


def grab(times: int = 4, timeout: int = 40):
    for _ in range(times):
        b = urllib.request.urlopen("http://localhost:8090/glass", timeout=timeout).read()
        if b[:4] == b"\x89PNG":
            return b
        time.sleep(0.7)
    raise SystemExit(b[:160])


def jget(p):
    with urllib.request.urlopen("http://localhost:8090" + p, timeout=15) as r:
        return json.loads(r.read())


def visible_change(case_png: Path, clean_png: Path) -> dict:
    """HOW MUCH of the change is actually on screen, inside the viewport?

    A bench that scores "did the eye find the hole" without checking the hole is
    IN VIEW is a bench that can fail a model for a defect that was never visible.
    The whole-frame diff is useless here: the FPS counter, the joint readout and
    the clock all change between two captures, and that swamps a few hundred
    pixels of missing geometry. So: restrict to the viewport, ignore the docks.
    """
    from PIL import Image
    a = np.asarray(Image.open(case_png).convert("RGB")).astype(np.int16)
    b = np.asarray(Image.open(clean_png).convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    vp = (slice(int(h * 0.13), int(h * 0.70)), slice(int(w * 0.17), int(w * 0.83)))
    diff = (np.abs(a - b).max(axis=2) > 12)[vp]
    n = int(diff.sum())
    out = {"viewport_diff_px": n}
    if n:
        ys, xs = np.nonzero(diff)
        out["bbox_w"] = int(xs.max() - xs.min())
        out["bbox_h"] = int(ys.max() - ys.min())
        # a real hole is a LOCALISED cluster, not text scattered across the frame
        out["localised"] = bool(out["bbox_w"] < w * 0.35 and out["bbox_h"] < h * 0.35)
    else:
        out["localised"] = False
    return out


def jpost(p, pl):
    d = json.dumps(pl).encode()
    r = urllib.request.Request("http://localhost:8090" + p, data=d, method="POST",
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=15) as resp:
        return json.loads(resp.read())


def eye_position(radius: float, theta: float, phi: float):
    """Same spherical law the engine uses (target at the origin; set_camera zeroes
    target/pan). Needed so the bench can pick a hole on the side FACING the camera."""
    import math
    c, s = math.cos(phi), math.sin(phi)
    ct, st = math.cos(theta), math.sin(theta)
    return np.array([radius * c * st, radius * s, -radius * c * ct], dtype=np.float64)


def pick_front_point(v: np.ndarray, eye, lo_y: float, hi_y: float):
    """The mesh vertex nearest the camera within a height band — i.e. a point on
    the SIDE FACING US. Nothing is asserted about what body part it is: the part
    is READ BACK from where the point actually is.

    This replaces hand-typed coordinates, which put two of three holes out of
    view and made the bench convict the eye for defects that were never on
    screen. The location is derived; the expected answer is derived from it.
    """
    band = (v[:, 1] >= lo_y) & (v[:, 1] <= hi_y)
    if not band.any():
        return None
    idx = np.nonzero(band)[0]
    d = np.linalg.norm(v[idx].astype(np.float64) - eye, axis=1)
    return idx[int(np.argmin(d))]


# height band on the mesh -> the body part name that band IS.
# Derived from the mesh's own bounds, not from my assumptions.
BANDS = [
    ("foot/ankle", 0.00, 0.22),
    ("lower leg",  0.22, 0.45),
    ("chest",      0.55, 0.72),
    ("neck",       0.80, 0.92),
]


def band_for(v: np.ndarray, i: int) -> str:
    """Name the region a vertex sits in — by fraction of the mesh's height."""
    y0, y1 = float(v[:, 1].min()), float(v[:, 1].max())
    frac = (float(v[i, 1]) - y0) / max(1e-6, (y1 - y0))
    best, bd = None, 9e9
    for name, lo, hi in BANDS:
        d = 0.0 if lo <= frac <= hi else min(abs(frac - lo), abs(frac - hi))
        if d < bd:
            bd, best = d, name
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="clean,leg_hole,chest_hole,neck_hole")
    ap.add_argument("--tag", default="")
    ap.add_argument("--no-ask", action="store_true", help="render only, no vision calls")
    a = ap.parse_args()

    v, f = load_base()
    print(f"base mesh: {len(v)} verts / {len(f)} tris")

    OUT.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y-%m-%d_%H%M%S") + (f"_{a.tag}" if a.tag else "")
    rd = OUT / run_id
    rd.mkdir(parents=True, exist_ok=True)

    # THE SHOW MUST BE OFF for the negative control to mean anything. With the
    # joints driving, the "clean" mesh is ALREADY TORN (spine_upper at ~117deg rips
    # the neck — the eye's own #1 finding). So a clean-case "defect found" would be
    # the eye being RIGHT, not a false alarm. Rest pose = genuinely intact.
    jpost("/joints", {"on": False})
    jpost("/show", {"playing": False})
    jpost("/camera", {"cam_radius": 14.0, "cam_theta": 0.6, "cam_phi": 0.25})
    time.sleep(1.2)
    eye = eye_position(14.0, 0.6, 0.25)

    rows = []
    for name in [c.strip() for c in a.cases.split(",") if c.strip()]:
        removed, want = 0, None
        if name == "clean":
            vf = f
        else:
            lo_frac, hi_frac = dict(
                leg_hole=(0.00, 0.45), chest_hole=(0.55, 0.72),
                neck_hole=(0.80, 0.92))[name]
            y0, y1 = float(v[:, 1].min()), float(v[:, 1].max())
            i = pick_front_point(v, eye, y0 + lo_frac * (y1 - y0), y0 + hi_frac * (y1 - y0))
            if i is None:
                print(f"  {name}: no vertex in that band, skipping")
                continue
            want = band_for(v, i)                      # derived, not asserted
            vf, removed = punch(v, f, v[i], (y1 - y0) * 0.055)
        p = rd / f"{name}.bin"
        write_bin(p, v, vf)
        ok, cr, cth, cph = cpp_bridge.load_mesh_bin(str(p), timeout=90)
        time.sleep(1.6)
        png = grab()
        img = rd / f"{name}.png"
        img.write_bytes(png)

        row = {"case": name, "tris_removed": removed, "tris": int(len(vf)),
               "upload_ok": bool(ok), "png": str(img)}
        print(f"  {name:11s} removed={removed:5d}  tris={len(vf)}")

        if not a.no_ask:
            t0 = time.time()
            try:
                rep = senses.see(str(img), ASK, timeout=900)
            except Exception as e:
                rep = None
                print(f"     FAILED {type(e).__name__}: {str(e)[:80]}")
            dt = time.time() - t0
            low = (rep or "").lower()
            # the expected words come from WHERE the hole actually is
            expect = (["none", "intact", "no hole", "no tear", "no defect",
                       "no missing", "clean"] if name == "clean"
                      else [w for w in want.replace("/", " ").split() if len(w) > 2])
            hits = [w for w in expect if w in low]
            row.update({"seconds": round(dt, 1), "report": rep,
                        "want_part": want, "expect": expect, "matched": hits,
                        "correct": bool(hits),
                        "finish_reason": senses.last_finish_reason(),
                        "served": senses._last_served_model()})
            if name != "clean":
                vis = visible_change(img, rd / "clean.png")
                row["visibility"] = vis
                # NOT VISIBLE != WRONG. Mark the case invalid rather than
                # convicting the eye for a defect that was never on screen.
                if not vis["localised"]:
                    row["correct"] = None          # invalid, not a failure
                    print(f"     INVALID {dt:6.1f}s  hole not localised in view "
                          f"(diff {vis['viewport_diff_px']}px, "
                          f"bbox {vis.get('bbox_w')}x{vis.get('bbox_h')})")
                else:
                    print(f"     {'PASS' if hits else 'FAIL':7s} {dt:6.1f}s  "
                          f"matched={hits or 'NOTHING'}  "
                          f"(hole {vis['viewport_diff_px']}px visible)")
            else:
                flag = "PASS" if hits else "FALSE ALARM"
                print(f"     {flag:11s} {dt:6.1f}s  matched={hits or 'NOTHING'}")
        rows.append(row)

    # restore the intact mesh so the engine is left clean
    write_bin(rd / "_restore.bin", v, f)
    cpp_bridge.load_mesh_bin(str(rd / "_restore.bin"), timeout=90)

    (rd / "results.json").write_text(
        json.dumps({"run_id": run_id, "model": senses.SENSES_MODEL,
                    "served": rows[0].get("served") if rows else None,
                    "context": None, "rows": rows}, indent=1, ensure_ascii=False),
        encoding="utf-8")

    asked = [r for r in rows if "correct" in r]
    if asked:
        valid = [r for r in asked if r["case"] != "clean" and r["correct"] is not None]
        inval = [r for r in asked if r["case"] != "clean" and r["correct"] is None]
        tp = sum(1 for r in valid if r["correct"])
        cl = [r for r in asked if r["case"] == "clean"]
        print(f"\n=== {senses.SENSES_MODEL} "
              f"(as served: {rows[0].get('served')}) ===")
        print(f"  defects found        : {tp}/{len(valid)}"
              + (f"   ({len(inval)} case(s) INVALID — hole not in view)" if inval else ""))
        print(f"  clean false alarms   : "
              f"{sum(1 for r in cl if not r['correct'])}/{len(cl)}")
        print(f"  mean read time       : "
              f"{sum(r['seconds'] for r in asked)/len(asked):.1f}s")
        print(f"  artefacts             : {rd}")
        if inval:
            print("\n  NOTE: invalid cases mean the bench is at fault, not the eye. "
                  "The camera must be aimed so the injected hole faces it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
