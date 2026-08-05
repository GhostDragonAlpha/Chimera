"""benchmark_pipeline.py -- what a frame costs, and WHICH quantity predicts it.

`docs/MEASURED_RENDER_BUDGETS.md` established that `MAX_GRAINS_PER_FRAME` was derived 3.64x wrong
and that a 64x increase in grains buys only 1.94x the time. That measurement was three zoom levels
on one body. This is the full sweep, and it also settles the follow-up question: if grain count is
not the predictor, what is?

TWO MODELS ARE FITTED AND BOTH ARE REPORTED, because "coverage is the real driver" was a
hypothesis formed from two data points and hypotheses formed that way are usually half right:

    render_ms ~ a*coverage + b        the proposed model
    render_ms ~ a*grains   + b        the model currently in perf_guard

R^2 for each, on the same rows, so the comparison is not between a fresh fit and a remembered one.

WHAT COVERAGE MEANS HERE: the fraction of frame pixels that are not background. It is measured off
the rendered image rather than predicted from the geometry, so it costs nothing extra and cannot
disagree with what was actually drawn.

    python ChimeraEngine/benchmark_pipeline.py            # full sweep -> docs/pipeline_benchmark.csv
    python ChimeraEngine/benchmark_pipeline.py --quick    # 3 classes, for a smoke check
"""
from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa
import lod as LOD
import perf_guard as pg

W, H = 1920, 1080
FOV = 1.047
ZOOMS = (0.25, 0.5, 1.0, 2.0, 5.0)
N_FRAMES = 5          # 2 discarded as warm-up, 3 timed -- the task asks for 3
_BG = np.array([0.015, 0.015, 0.04], dtype=np.float32) * 255.0


def gpu_state() -> dict:
    """What else was using the card when this sweep ran.

    THIS EXISTS BECAUSE THE COEFFICIENTS MOVED AND NOBODY COULD SAY WHY. Across four sweeps the
    fitted slope went 2.91e-05 -> 3.83e-05 -> 3.15e-05 -> 3.61e-05 and the empty-frame floor read
    9.4-9.8, then 7.7-7.9, then 8.7-9.1 ms -- with ZERO expansions every time, so the renderer
    cannot have moved it. One sweep even reported aTerrain as an 18% regression that measured
    -3.7% when re-run interleaved. The cause was always the same: this box shares one 4090 with
    LM Studio, and nothing recorded what the card was doing.

        A MEASUREMENT THAT DOES NOT RECORD ITS CONDITIONS CANNOT BE COMPARED TO ANOTHER ONE.

    So every row now carries the machine state it was taken under. It does not make the noise go
    away -- it makes two sweeps comparable, and it makes "why did this move" answerable instead of
    a shrug. Best-effort: a missing nvidia-smi or a stopped LM Studio must never fail a benchmark.
    """
    import json as _json
    import subprocess
    import urllib.request
    st = {"vram_used_mb": None, "vram_total_mb": None, "gpu_util_pct": None,
          "sm_clock_mhz": None, "temp_c": None, "lm_model": None}
    try:
        q = ("utilization.gpu,memory.used,memory.total,temperature.gpu,clocks.current.sm")
        out = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=15).stdout.strip()
        u, mu, mt, t, c = [x.strip() for x in out.splitlines()[0].split(",")]
        st.update(gpu_util_pct=int(u), vram_used_mb=int(mu), vram_total_mb=int(mt),
                  temp_c=int(t), sm_clock_mhz=int(c))
    except Exception:
        pass
    try:
        # WHICH MODEL IS RESIDENT, not whether one "should" be. The gateway ADOPTS whatever
        # LM Studio has loaded, so the only honest way to record it is to ask LM Studio.
        with urllib.request.urlopen("http://127.0.0.1:1234/api/v0/models", timeout=10) as r:
            for m in _json.loads(r.read().decode()).get("data", []):
                if m.get("state") == "loaded":
                    st["lm_model"] = f"{m.get('id')}@{m.get('loaded_context_length')}"
                    break
    except Exception:
        pass
    return st


def _fmt_gpu(st: dict) -> str:
    vu, vt = st.get("vram_used_mb"), st.get("vram_total_mb")
    frac = f"{vu:,}/{vt:,} MiB ({100*vu/vt:.0f}%)" if vu and vt else "VRAM unknown"
    return (f"GPU: {frac} | util {st.get('gpu_util_pct')}% | sm {st.get('sm_clock_mhz')} MHz "
            f"| {st.get('temp_c')} C | LM Studio: {st.get('lm_model') or 'nothing loaded'}")


def _aim(cam, dist):
    """Place the camera at `dist` on -y and point it at the origin.

    The aim-at-origin formula, not `atan2(-pos[1], pos[0])`. That expression is correct only where
    pos[0] == 0 and renders bare background elsewhere -- it cost this project two files' worth of
    silent empty frames, and a benchmark that times an empty frame reports the clear-screen cost
    as the render cost.
    """
    pos = (0.0, -dist, 0.0)
    cam.position = np.array(pos, dtype=np.float32)
    n = math.sqrt(sum(p * p for p in pos)) or 1.0
    fx, fy, fz = -pos[0] / n, -pos[1] / n, -pos[2] / n
    cam.yaw = math.atan2(fy, fx)
    cam.pitch = math.atan2(fz, math.hypot(fx, fy))


def coverage_of(img) -> float:
    """Fraction of pixels that are not background. Measured off the frame, not predicted."""
    a = img.astype(np.float32)
    return float(((a > _BG + 2.0).any(-1)).mean())


def heaviest_per_class() -> dict:
    """One representative per surface class: the term with the most grains in it.

    THE HEAVIEST, not a random member, because the budget question is about the worst case. A
    class represented by its median member would produce a benchmark that says everything is fine
    and tell you nothing about the frame that drops.
    """
    best: dict[str, tuple[int, str]] = {}
    for t in sa.scene_terms():
        b = sa.scene_buffer(t)
        if b is None or b.shape[0] == 0:
            continue
        k = pg._classify_type(t)
        if k not in best or b.shape[0] > best[k][0]:
            best[k] = (int(b.shape[0]), t)
    return {k: v[1] for k, v in best.items()}


def bench(quick: bool = False) -> list[dict]:
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, -3.0, 0.0))

    _g0 = gpu_state()
    print("  " + _fmt_gpu(_g0), flush=True)
    reps = heaviest_per_class()
    if quick:
        reps = dict(list(reps.items())[:3])
    rows = []
    for kind, term in sorted(reps.items()):
        buf = sa.scene_buffer(term)
        R = LOD.body_radius(buf)
        mips = LOD.build_mips(buf, R) if LOD.should_lod(buf) else None
        for z in ZOOMS:
            dist = 2.8 * R * z
            _aim(cam, dist)
            draw = buf
            if mips and len(mips) > 1:
                draw = LOD.select(mips, LOD.projected_radius_px(R, dist, H, FOV))
            pipe.upload(np.ascontiguousarray(draw, dtype=np.float32))
            params = cam.params(W, H)
            ts, img = [], None
            for i in range(N_FRAMES):
                t0 = time.perf_counter()
                img = pipe.render_from_gpu(cam, params)
                ts.append((time.perf_counter() - t0) * 1000.0)
            ts = ts[2:]                          # discard JIT warm-up
            ms, sd = float(np.mean(ts)), float(np.std(ts))
            cov = coverage_of(img)
            # THE EXPANSION COUNT IS READ OFF THE FRAME THAT WAS JUST TIMED, not recomputed. It
            # is the same tuple `_build_tiles_gpu` used to bin that frame, so the predictor and
            # the thing it predicts cannot come from two different renders.
            st = pipe.tile_stats()
            nvis = int(st["nv"])
            exp = int(st["expansions"])
            eps = exp / nvis if nvis else 0.0
            rows.append({"class": kind, "term": term, "zoom": z,
                         "n_base": int(buf.shape[0]), "n_lod": int(draw.shape[0]),
                         "n_vis": nvis,
                         "coverage_frac": round(cov, 6), "render_ms": round(ms, 3),
                         "render_ms_std": round(sd, 3), "fps": round(1000.0 / ms, 2),
                         "expansions": exp, "expansions_per_splat": round(eps, 2),
                         "gpu_vram_mb": _g0["vram_used_mb"], "gpu_util_pct": _g0["gpu_util_pct"],
                         "lm_model": _g0["lm_model"] or ""})
            print(f"  {term:22s} {z:5.2f}x  base={buf.shape[0]:>7d} lod={draw.shape[0]:>7d} "
                  f"vis={nvis:>7d} cover={100*cov:6.2f}%  exp={exp:>10,d} eps={eps:>7.1f}  "
                  f"{ms:7.2f} +- {sd:5.2f} ms  {1000.0/ms:6.1f} fps", flush=True)
    return rows


def _fit(x, y):
    """Least squares y = a*x + b, returning (a, b, R^2). R^2 against the mean, the usual sense."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0:
        return 0.0, float(np.mean(y)), 0.0
    a, b = np.polyfit(x, y, 1)
    pred = a * x + b
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return float(a), float(b), (1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0


def _corr(x, y) -> float:
    """Pearson r. Returns 0.0 for a degenerate column rather than a nan, so the matrix prints."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


# THE CANDIDATE PREDICTORS, all fitted on the SAME rows. `expansions` was proposed off a 4-point
# sample; `n_lod` is what MAX_GRAINS_PER_FRAME assumes; `coverage_frac` was an earlier hypothesis
# formed from two points. Naming them in one list is the point -- a model that only ever gets
# compared against the one it replaced is a model nobody tried to beat.
_PREDICTORS = ("n_lod", "n_vis", "coverage_frac", "expansions", "expansions_per_splat")


def model_report(rows) -> dict:
    ms = [r["render_ms"] for r in rows]
    cols = {k: [r[k] for r in rows] for k in _PREDICTORS}
    cols["render_ms"] = ms
    names = list(_PREDICTORS) + ["render_ms"]

    print("\n" + "=" * 100)
    print("  WHICH QUANTITY PREDICTS THE FRAME TIME?   (n = %d rows, every fit on the same rows)"
          % len(rows))
    print("=" * 100)
    fits = {}
    for k in _PREDICTORS:
        a, b, r2 = _fit(cols[k], ms)
        fits[k] = {"a": a, "b": b, "r2": r2}
        print(f"  {k:22s}  render_ms = {a:11.4e} * x + {b:7.3f}    R^2 = {r2:.4f}")
    win = max(_PREDICTORS, key=lambda k: fits[k]["r2"])
    print(f"  -> best single predictor: {win}  (R^2 = {fits[win]['r2']:.4f})")

    print("\n  CORRELATION MATRIX (Pearson r)")
    hdr = "  " + " " * 22 + "".join(f"{n[:12]:>14s}" for n in names)
    print(hdr)
    for a_ in names:
        row = "".join(f"{_corr(cols[a_], cols[b_]):>14.3f}" for b_ in names)
        print(f"  {a_:22s}{row}")

    # THE FIXED FLOOR IS ITS OWN FINDING: if b dominates over the whole measured range, the frame
    # cost is mostly NOT a function of the scene at all, and no scene-derived budget can control it.
    b_win = fits[win]["b"]
    span = max(ms) - min(ms)
    print(f"\n  intercept {b_win:.2f} ms against a measured span of {span:.2f} ms "
          f"({100*b_win/max(max(ms),1e-9):.0f}% of the worst frame is fixed cost)")

    # WHAT AN EXPANSION BUDGET WOULD BE, derived from the wall rather than from one scene. The
    # budget has to answer "how many pairs fit inside MAX_RENDER_MS", and that is the fit inverted
    # -- not a measured scene multiplied by a chosen headroom, which would make the cap a property
    # of whichever membrane happened to be measured.
    fe = fits["expansions"]
    if fe["a"] > 0:
        cap = (pg.MAX_RENDER_MS - fe["b"]) / fe["a"]
        print(f"  expansion cap implied by MAX_RENDER_MS={pg.MAX_RENDER_MS}: "
              f"({pg.MAX_RENDER_MS} - {fe['b']:.3f}) / {fe['a']:.4e} = {cap:,.0f} expansions")
        fits["expansions"]["implied_cap"] = cap
    return {**fits, "winner": win, "ms_min": min(ms), "ms_max": max(ms), "n": len(rows)}


def audit_terms(limit: int = 0) -> list[dict]:
    """Every renderable term at DEFAULT framing: what it costs and what its grains look like.

    The class sweep above answers "how does cost move with zoom"; this answers "which membranes
    are expensive to begin with", which is the question a person editing an emit() has. Default
    framing only -- one row per term, so the list can be ranked.
    """
    from ParticleEngine.gpu_pipeline import FullGPUPipeline, TILE_SIZE, SIZE
    from ParticleEngine.camera import FirstPersonCamera
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, -3.0, 0.0))
    terms = sa.scene_terms()
    if limit:
        terms = terms[:limit]
    half_screen = 0.5 * ((W + TILE_SIZE - 1) // TILE_SIZE) * ((H + TILE_SIZE - 1) // TILE_SIZE)
    rows = []
    for t in terms:
        buf = sa.scene_buffer(t)
        if buf is None or buf.ndim != 2 or buf.shape[0] == 0:
            continue
        R = LOD.body_radius(buf)
        dist = 2.8 * max(R, 1e-6)
        draw = LOD.lod_switch(buf, dist, H, FOV) if LOD.should_lod(buf) else buf
        _aim(cam, dist)
        pipe.upload(np.ascontiguousarray(draw, dtype=np.float32))
        params = cam.params(W, H)
        ts = []
        for i in range(4):
            t0 = time.perf_counter()
            img = pipe.render_from_gpu(cam, params)
            ts.append((time.perf_counter() - t0) * 1000.0)
        st = pipe.tile_stats()
        col = np.asarray(draw[:, SIZE], dtype=np.float64)
        col = col[np.isfinite(col)]
        rows.append({
            "term": t, "class": pg._classify_type(t),
            "n_lod": int(draw.shape[0]), "n_vis": int(st["nv"]),
            "size_mean": float(col.mean()) if col.size else 0.0,
            "size_std": float(col.std()) if col.size else 0.0,
            "size_max": float(col.max()) if col.size else 0.0,
            "expansions": int(st["expansions"]),
            "expansions_per_splat": round(pipe.expansions_per_splat(), 2),
            "render_ms": round(float(np.median(ts[2:])), 3),
            "over_half_screen": bool(pipe.expansions_per_splat() > half_screen),
        })
    return rows


def audit_report(rows) -> None:
    """Rank terms by expansion cost, then ask whether the GRAIN budgets rank them the same way.

    TASK 10'S QUESTION, AND IT IS A RANK QUESTION ON PURPOSE. Whether a grain budget is
    numerically right cannot be settled by comparing it to an expansion count -- they are
    different units. What CAN be settled is whether the two orderings agree: if the class with the
    biggest grain allowance is not the class that actually costs the most, then the budget is
    protecting the wrong thing regardless of what its number is.
    """
    print("\n" + "=" * 118)
    print("  EVERY RENDERABLE TERM AT DEFAULT FRAMING, ranked by tile expansions")
    print("=" * 118)
    print(f"  {'term':<22s} {'class':<11s} {'n_lod':>7s} {'n_vis':>7s} {'expansions':>11s} "
          f"{'/splat':>8s} {'size_mean':>10s} {'size_max':>10s} {'ms':>7s}")
    print("-" * 118)
    for r in sorted(rows, key=lambda r: -r["expansions"]):
        flag = "  <-- OVER HALF-SCREEN" if r["over_half_screen"] else ""
        print(f"  {r['term']:<22s} {r['class']:<11s} {r['n_lod']:>7d} {r['n_vis']:>7d} "
              f"{r['expansions']:>11,d} {r['expansions_per_splat']:>8.1f} "
              f"{r['size_mean']:>10.4g} {r['size_max']:>10.4g} {r['render_ms']:>7.1f}{flag}")

    print("\n" + "=" * 118)
    print("  BUDGET AUDIT -- does the grain budget rank the classes the way the cost does?")
    print("=" * 118)
    by_class: dict[str, list] = {}
    for r in rows:
        by_class.setdefault(r["class"], []).append(r)
    per = []
    for k, rs in by_class.items():
        worst = max(rs, key=lambda r: r["expansions"])
        tot_g = sum(r["n_lod"] for r in rs)
        tot_e = sum(r["expansions"] for r in rs)
        per.append({"class": k, "budget": pg._classify_budget(k if k != "general" else "xx"),
                    "worst_term": worst["term"], "worst_exp": worst["expansions"],
                    "exp_per_grain": (tot_e / tot_g) if tot_g else 0.0,
                    "n_terms": len(rs)})
    # `_classify_budget` takes a TERM, not a class, so it is fed a term from the class instead of
    # the class name -- feeding it the word "terrain" happens to work and feeding it "general"
    # does not, and a lookup that is right by coincidence is a lookup waiting to be wrong.
    for p in per:
        p["budget"] = pg._classify_budget(by_class[p["class"]][0]["term"])
    rank_budget = {p["class"]: i for i, p in
                   enumerate(sorted(per, key=lambda p: -p["budget"]))}
    rank_exp = {p["class"]: i for i, p in
                enumerate(sorted(per, key=lambda p: -p["worst_exp"]))}
    n_mismatch = 0
    for p in sorted(per, key=lambda p: -p["worst_exp"]):
        rb, re_ = rank_budget[p["class"]], rank_exp[p["class"]]
        ok = "OK" if rb == re_ else "MISMATCHED"
        n_mismatch += (rb != re_)
        print(f"  CLASS: {p['class']:<11s} grains={p['budget']:>7,d} "
              f"worst_expansions={p['worst_exp']:>10,d} ({p['worst_term']}) "
              f"exp_per_grain={p['exp_per_grain']:>6.2f} -- budget rank #{rb+1} vs cost rank "
              f"#{re_+1}  {ok}")
    print(f"\n  {n_mismatch} of {len(per)} classes rank differently under the two metrics.")
    if n_mismatch:
        print("  A class whose ranks disagree has a grain budget that is not protecting the thing")
        print("  that costs. Rescaling it by exp_per_grain is the mechanical fix; the honest one is")
        print("  that a GRAIN budget answers a density question and cannot be made into a cost one.")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    quick = "--quick" in argv
    if "--audit" in argv:
        print("PER-TERM EXPANSION AUDIT -- every renderable term at default framing")
        print("=" * 118)
        rows = audit_terms(8 if quick else 0)
        audit_report(rows)
        out = _HERE.parent / "docs" / "pipeline_terms.csv"
        with open(out, "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"\n  wrote {out}  ({len(rows)} rows)")
        return 0
    print("PIPELINE BENCHMARK -- heaviest term per surface class, 5 zoom levels")
    print("=" * 92)
    rows = bench(quick)
    m = model_report(rows)
    # PRINTED AT BOTH ENDS. If the card's state changed DURING the sweep, the early rows and the
    # late rows were measured under different machines and the fit spans two populations -- which
    # is exactly the failure this probe exists to make visible rather than mysterious.
    _g1 = gpu_state()
    print("\n  conditions at end:   " + _fmt_gpu(_g1))
    if rows and rows[0].get("gpu_vram_mb") and _g1.get("vram_used_mb"):
        _d = abs(_g1["vram_used_mb"] - rows[0]["gpu_vram_mb"])
        if _d > 512:
            print(f"  *** VRAM MOVED {_d:,} MiB DURING THIS SWEEP -- the early and late rows were "
                  f"measured under different machines and the fit spans two populations. ***")
    out = _HERE.parent / "docs" / "pipeline_benchmark.csv"
    with open(out, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n  wrote {out}  ({len(rows)} rows)")
    return 0 if len(rows) >= 30 or quick else 1


if __name__ == "__main__":
    sys.exit(main())
