"""End-to-end whole-body example for the anatomy compiler.

Runs three fits with ONE correspondence object (works against both the real intake
and the synthetic twin because every source resolution is by NAME):
  1. grounded  — the verified FreeMusco chimanoid.xml fitted to the synthetic target;
  2. synthetic — the counts-matched synthetic twin fitted to the same target;
  3. mirror    — the same anatomy read left-handed (plane reflection).
Writes the fitted JSON to runs/ and prints the measured tables the membrane promised:
shared-joint closure, per-segment scale/frame twist, mass, specimen muscle paths,
moment arms, and the unsupported-feature ledger.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\.tmp\anatomy_compiler")

from compiler import fit
from correspondence import Refusal
from schema import write_json
from synthetic_fixtures import (
    TARGET_LENS,
    TARGET_RADIALS,
    load_real,
    make_full_body_correspondence,
    synth_chimanoid,
)

RUNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
ORIGIN = (0.0, 0.85, 0.0)
MIRROR_N = np.array([0.0, 1.0, 0.0])


def table_segments(f):
    rows = []
    for s in f.segments:
        sc = ",".join(f"{x:.3f}" for x in s.scale)
        rows.append((s.rank, s.source_body, s.parent, f"{s.scale[0]:.3f}", sc, f"{s.roll_residual_deg:+.1f}deg"))
    return rows


def table_physiology(f):
    rows = []
    for p in sorted(f.physiology, key=lambda p: -p.mass):
        ev = np.linalg.eigvalsh(p.inertia_fitted)
        rows.append((p.body, f"{p.mass:10.2f}", f"{p.det_scale:8.3f}", " ".join(f"{x:.2e}" for x in ev)))
    return rows


def main() -> int:
    os.makedirs(RUNS, exist_ok=True)
    real = load_real()
    syn = synth_chimanoid()
    corr = make_full_body_correspondence(syn, TARGET_LENS, TARGET_RADIALS, origin=ORIGIN)

    print("panAnatomy compiler v1 — whole-body example")
    print(f"  source file   {real.meta.get('source_file')}")
    print(f"  revision      {real.meta.get('revision')}  sha256 {real.meta.get('sha256')[:16]}...")
    print(f"  source counts bodies={len(real.bodies)} coords={len(real.joints)} "
          f"sites={len(real.sites)} tendons={len(real.tendons)} muscles={len(real.muscles)}")
    print(f"  target        {len(corr.landmarks)} landmarks, {len(corr.segments)} segments, origin {ORIGIN}")

    # --- 1. grounded: real chimanoid.xml -> target ---------------------------------
    gr = fit(real, corr, fit_mode="grounded")
    write_json(gr, os.path.join(RUNS, "grounded_chimanoid.json"))

    # --- 2. synthetic twin ----------------------------------------------------------
    sf = fit(syn, corr)
    write_json(sf, os.path.join(RUNS, "synthetic_twin.json"))

    # --- 3. mirror read of the same anatomy ------------------------------------------
    import copy

    cm = copy.deepcopy(corr)
    n = MIRROR_N
    cm.landmarks = {k: p - 2.0 * (p @ n) * n for k, p in corr.landmarks.items()}
    cm.handedness = "mirror"
    cm.mirror_plane_normal = n
    for attempt, expect in [("preserve", Refusal), ("mirror", type(None))]:
        _c = copy.deepcopy(cm) if attempt == "preserve" else cm
        if attempt == "preserve":
            _c.handedness = "preserve"
            try:
                fit(syn, _c)
                print(f"  mirror/preserve   UNEXPECTEDLY ACCEPTED (falsifier F3 lost)")
                return 1
            except Refusal as e:
                print(f"  mirror/preserve   refused [{e.code}]")
        else:
            fm = fit(syn, _c)
            write_json(fm, os.path.join(RUNS, "mirror_read.json"))
            print(f"  mirror/mirror     accepted  chirality_det={fm.residuals['chirality_det']:+.3f} "
                  f"frame_handedness={fm.residuals['frame_handedness']}")

    # --- measured tables --------------------------------------------------------------
    print("\nsegments (rank body parent axial-scale diag(scale) roll-twist)")
    for row in table_segments(sf):
        print("  %4d %-12s %-12s %-7s %-18s %s" % row)

    print(f"\nshared-joint closure        max {gr.residuals['shared_joint_max_separation_m']:.2e} m")
    for k in sorted(k_ for k_ in gr.residuals if k_.startswith("closure.")):
        v = gr.residuals[k]
        if v > 0:
            print(f"    closure.{k}: {v:.2e} m")

    print("\nphysiology (body mass kg detS inertia eigenvalues)")
    for row in table_physiology(gr):
        print("  %-14s %11s %9s  %s" % row)

    print(f"\ntotal fitted mass (grounded) {sum(p.mass for p in gr.physiology):.1f} kg  vs source total "
          f"{sum((p.mass_src or 0.0) for p in gr.physiology):.1f} kg")

    print("\nspecimen muscles (fitted path rest length, force/timeconst ingested unchanged)")
    for m in [x for x in gr.muscles if x.tendon][:6]:
        print("  %-20s tendon=%-24s l0=%.4f status=%s" % (m.name, m.tendon, m.rest_length, m.status))
    no_path = [m.name for m in gr.muscles if m.status == "no_path"]
    print(f"  no-path muscles: {len(no_path)}  ({', '.join((x or '<unnamed>') for x in no_path[:3])}...)")

    print("\nunsupported features (ledger, never invented)")
    for u in gr.unsupported:
        print("  %-22s %s  %s" % (u["feature"], u["status"], u["evidence"]))

    worst = max((abs(m.analytic - m.finite_difference) / (1.0 + abs(m.finite_difference)) for t in gr.tendons for m in t.moment_arms), default=0.0)
    matched_all = all(m.matched for t in gr.tendons for m in t.moment_arms)
    print(f"\nanalytic vs FD moment arms (whole body, {len(gr.tendons)} tendons):"
          f" all matched={matched_all} worst rel dev={worst:.2e}")

    print(f"\nJSON written: {os.path.join(RUNS, 'grounded_chimanoid.json')}")
    print(f"rules: example_whole_body.py exit {0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())