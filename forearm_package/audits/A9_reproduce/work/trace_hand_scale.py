"""Trace the hand_r / hand_l axial scale (~7.155) and 157.7 kg fitted mass to their
exact origins: source endpoints, target landmarks, the scale rule, and the mass chain.

Answers:
  - where the ~7.155 number comes from (and why the printed 7.155 does NOT cube to the
    grounded det_scale 344.778 — the fixture coupling ground truth, not a compiler bug),
  - the source bone length s_src and the authored target length TARGET_LENS['hand_r'],
  - the radial-scale rule (uniform -> [ratio, ratio, ratio]),
  - the mass chain: mass_fitted = mass_src * det(scale).

Read-only: loads the REAL chimanoid.xml and the fixtures; changes nothing.

Run:  python trace_hand_scale.py
"""
from __future__ import annotations

import numpy as np

from synthetic_fixtures import (
    REAL_XML,
    TARGET_LENS,
    TARGET_RADIALS,
    load_real,
    make_full_body_correspondence,
    synth_chimanoid,
)
from intake import load_source, global_site_positions

ORIGIN = (0.0, 0.85, 0.0)
BODY = "hand_r"


def resolve(corr, ana, lid):
    kind, _, name = corr.source_landmarks[lid].partition(":")
    site_world = global_site_positions(ana)
    if kind == "body_origin":
        return ana.body_by_name[name].pos_global.copy()
    if kind == "site":
        return site_world[name].copy()
    raise AssertionError(kind)


def main() -> int:
    real = load_real()
    synth = synth_chimanoid()
    site_world_real = global_site_positions(real)

    corr = make_full_body_correspondence(synth, TARGET_LENS, TARGET_RADIALS, origin=ORIGIN)
    seg = next(s for s in corr.segments if s.source_body == BODY)

    # ---- source endpoints -------------------------------------------------
    src_A_real = resolve(corr, real, seg.proximal_landmark)     # body_origin:hand_r
    src_D_real = resolve(corr, real, seg.distal_landmark)       # site:<farthest hand site>
    s_src_real = float(np.linalg.norm(src_D_real - src_A_real))

    src_A_syn = resolve(corr, synth, seg.proximal_landmark)
    src_D_syn = resolve(corr, synth, seg.distal_landmark)
    s_src_syn = float(np.linalg.norm(src_D_syn - src_A_syn))

    src_Q_real = resolve(corr, real, seg.roll_ref)

    # ---- target landmarks -------------------------------------------------
    P = corr.landmarks[seg.proximal_landmark]
    P_d = corr.landmarks[seg.distal_landmark]
    Q = corr.landmarks[seg.roll_ref]
    len_t = float(np.linalg.norm(P_d - P))
    dir_t = (P_d - P) / len_t

    # ---- the scale rule: uniform -> [ratio, ratio, ratio] ------------------
    ratio_real = len_t / s_src_real
    ratio_syn = len_t / s_src_syn
    detS_real = ratio_real ** 3
    detS_syn = ratio_syn ** 3

    # ---- mass chain ---------------------------------------------------------
    body = real.body_by_name[BODY]
    mass_src = body.mass
    mass_fit_real = mass_src * detS_real
    mass_fit_syn = mass_src * detS_syn

    # roll reference geometry (off-axis witness)
    a = src_D_real - src_A_real
    a = a / np.linalg.norm(a)
    perp = np.linalg.norm((src_Q_real - src_A_real) - a * (a @ (src_Q_real - src_A_real)))

    print(f"trace: {BODY} axial scale -> fitted mass chain")
    print(f"  source file                  : {REAL_XML}")
    print(f"  authored target length lens  : TARGET_LENS['{BODY}'] = {TARGET_LENS[BODY]} m")
    print()
    print("source endpoints (grounded, resolved against the REAL xml):")
    print(f"  proximal landmark     : {seg.proximal_landmark}  src = {corr.source_landmarks[seg.proximal_landmark]}")
    print(f"      src_A (hand origin): {np.round(src_A_real, 6)} m")
    print(f"  distal landmark       : {seg.distal_landmark}  src = {corr.source_landmarks[seg.distal_landmark]}")
    print(f"      src_D (farthest referencing hand site): {np.round(src_D_real, 6)} m")
    print(f"  s_src REAL  = |src_D - src_A| = {s_src_real:.6f} m   <- the source bone the print 7.155 derailed from")
    print(f"  s_src SYNTH = |src_D - src_A| = {s_src_syn:.6f} m   <- twin uses proportion 0.98, so it is 0.98 x real")
    print(f"  roll ref    : {seg.roll_ref} = {corr.source_landmarks[seg.roll_ref]}, perpendicular distance {perp:.4f} m")
    print()
    print("target landmarks (authored, generated from the SYNTHETIC twin geometry):")
    print(f"  P   (prox): {np.round(P, 6)} m")
    print(f"  P_d (dist): {np.round(P_d, 6)} m")
    print(f"  Q   (roll): {np.round(Q, 6)} m")
    print(f"  |P_d - P| = {len_t:.6f} m ; target unit dir = {np.round(dir_t, 6)}")
    print()
    print("the scale rule (compiler.py _Segment, uniform policy):")
    print("  ratio = |P_d - P| / s_src ;  scale = [ratio, ratio, ratio]")
    print(f"  ratio (grounded, vs REAL bone) = {ratio_real:.6f}")
    print(f"  ratio (vs SYNTHETIC   bone) = {ratio_syn:.6f}")
    print(f"  det_scale = ratio^3: grounded {detS_real:.6f}   synthetic-twin {detS_syn:.6f}")
    print()
    print("this is the fixture coupling, not a compiler bug:")
    print(f"  the example_whole_body fit grounded against the REAL xml -> scale 7.012, detS {detS_real:.3f}")
    print(f"  the SYNTHETIC-twin fit printed scale {ratio_syn:.3f} (= grounded * 1/0.98), cubed detS {detS_syn:.3f}")
    print(f"  printed 7.155^3 = {7.155**3:.1f}  ;  grounded cube root of 344.778 = {344.778 ** (1.0/3.0):.4f}")
    print()
    print("the mass chain (uniform-density scaling, compiler.py physiology):")
    print(f"  mass_src (real xml hand_r) = {mass_src:.6f} kg")
    print(f"  mass_fitted = mass_src * det_scale = {mass_src * detS_real:.3f} kg (grounded)")
    print(f"  -> the reported 157.74 kg = {mass_src:.4f} * {detS_real:.3f}")
    print()
    print("the inflation is fully explained by the authored target length being ~7 x the")
    print("real hand bone:  {:.3f} m / {:.4f} m = {:.3f}".format(TARGET_LENS[BODY], s_src_real, TARGET_LENS[BODY] / s_src_real))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())