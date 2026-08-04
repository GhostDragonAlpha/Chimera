"""classify_fall.py -- WHICH WAY DID IT GO DOWN. A fall, labelled from the trajectory alone.

RULE 0, stated before the build, because a classifier is a theory about what falling IS:

    STATEMENT   A fall has exactly two questions in it, and both are answered by the centre of
                mass against the base of support the FEET make -- never by the pelvis alone.
                (1) DID THE CoM LEAVE THE BASE? If it never did, the body did not topple: the
                legs stopped carrying it and it went down inside its own footprint. That is a
                COLLAPSE, and it is a different defect with a different fix.
                (2) IF IT LEFT, WHICH WAY? The axis whose normalised excursion runs away first
                is the direction, and its sign separates forward from backward.

    PREDICTION  On the documented lateral stand fall -- CoM-y reaching -812 mm while CoM-x stays
                under 52 mm -- this returns `lateral` with a confidence above 0.9, because 812/52
                is a 15.6x separation between the two axes and no threshold in that gap can
                change the answer. On a body whose CoM stays inside the polygon the whole way
                down, it returns `collapse`.

    FALSIFIER   Two, named before the run:
                1. If it labels the documented lateral fall anything but `lateral`, it is wrong
                   and this file is the defect.
                2. If EVERY rollout it is shown comes back the same label, the classifier is not
                   discriminating -- it is a constant wearing a function's clothes. So the
                   self-test drives four synthetic trajectories, one per class, and all four must
                   come back distinct or the harness fails.

WHY NOT THRESHOLD ON THE PELVIS. The pelvis drops in every fall, so its trace says a fall
happened and nothing about which one. Worse, thresholding on a quantile of the pelvis's own
trace is the exact move this project has already been caught by (a threshold defined in terms of
the population it measures cannot report anything about that population). The reference here
comes from OUTSIDE the trajectory: the base of support the feet make, measured at that instant.

    python tools/classify_fall.py            # self-test: four synthetic falls, four labels
"""
from __future__ import annotations

import sys

import numpy as np

LABELS = ("lateral", "forward", "backward", "collapse", "no_fall")


def classify_fall(t, z, com_fore, com_lat, half_fore, half_lat, z_target,
                  fall_frac=0.5):
    """Label one rollout. Every argument is a SERIES except the target; nothing is optional.

    t          -- sample times, s
    z          -- pelvis height, m
    com_fore   -- CoM fore-aft position RELATIVE TO THE FOOT POLYGON CENTRE, m (+ = forward)
    com_lat    -- CoM lateral position relative to the same centre, m (+ = the body's left)
    half_fore  -- the polygon's own half-extent fore-aft at each sample, m
    half_lat   -- the polygon's own half-extent laterally at each sample, m
    z_target   -- the DERIVED pelvis target (stand_port), m. The fall bar is `fall_frac` of it,
                  and `fall_frac` is the same 0.5 every harness in this project already uses --
                  passed in rather than re-declared here so the two cannot drift apart.

    Returns a dict: label, confidence, t_fall, and the numbers the label was read off. The
    numbers are returned WITH the label because a label nobody can check is an opinion.
    """
    t = np.asarray(t, float); z = np.asarray(z, float)
    cf = np.asarray(com_fore, float); cl = np.asarray(com_lat, float)
    hf = np.maximum(np.asarray(half_fore, float), 1e-9)
    hl = np.maximum(np.asarray(half_lat, float), 1e-9)
    if t.size == 0:
        return dict(label="no_fall", confidence=0.0, t_fall=None, reason="empty trajectory")

    bar = fall_frac * z_target
    below = np.flatnonzero(z < bar)
    t_fall = float(t[below[0]]) if below.size else None

    # THE WINDOW IS THE APPROACH TO THE FALL, NOT THE WHOLE RUN. After the pelvis is on the
    # floor the CoM is wherever the heap landed, which says nothing about what tipped it; before
    # the fall begins the body is standing and the excursions are the postural sway the stand
    # port already grades. So the label is read from the samples up to the fall instant.
    end = below[0] + 1 if below.size else t.size
    sl = slice(0, end)
    nf, nl = cf[sl] / hf[sl], cl[sl] / hl[sl]           # excursion in units of the base itself
    pf = float(np.max(np.abs(nf))) if nf.size else 0.0
    pl = float(np.max(np.abs(nl))) if nl.size else 0.0
    # the SIGNED extreme, so forward and backward are separable
    sf = float(nf[np.argmax(np.abs(nf))]) if nf.size else 0.0
    sl_ = float(nl[np.argmax(np.abs(nl))]) if nl.size else 0.0

    if t_fall is None:
        return dict(label="no_fall", confidence=1.0, t_fall=None,
                    peak_fore_frac=pf, peak_lat_frac=pl, z_min=float(z.min()),
                    reason=f"pelvis never reached {bar:.4f} m ({100*fall_frac:.0f}% of target)")

    # (1) DID IT LEAVE THE BASE? theStance's own definition: outside the base of support the body
    # IS a falling inverted pendulum. Inside it, whatever went wrong was not a topple.
    if max(pf, pl) < 1.0:
        return dict(label="collapse", confidence=float(1.0 - max(pf, pl)), t_fall=t_fall,
                    peak_fore_frac=pf, peak_lat_frac=pl, z_min=float(z.min()),
                    reason=f"CoM never left the base (peak {max(pf, pl):.2f} of it) yet the "
                           f"pelvis reached {100*fall_frac:.0f}% of target at {t_fall:.2f} s -- "
                           f"the legs stopped carrying, they did not tip")

    # (2) WHICH AXIS RAN AWAY. Confidence is the SEPARATION between the two axes, not a score:
    # 1 - (loser/winner). Two axes that leave together are a diagonal fall and this says so by
    # returning a low confidence rather than by inventing a fifth label nobody asked for.
    if pl >= pf:
        label, win, lose = "lateral", pl, pf
    else:
        label, win, lose = ("forward" if sf > 0 else "backward"), pf, pl
    return dict(label=label, confidence=float(1.0 - lose / win) if win > 0 else 0.0,
                t_fall=t_fall, peak_fore_frac=pf, peak_lat_frac=pl,
                signed_fore=sf, signed_lat=sl_, z_min=float(z.min()),
                reason=f"{label}: peak excursion {win:.2f} of the base against {lose:.2f} on the "
                       f"other axis, pelvis through {100*fall_frac:.0f}% at {t_fall:.2f} s")


def classify_trace(tr, z_target, fall_frac=0.5):
    """The same call, off the trace dicts f3_stand / train_stand / f4_walk already build.

    Falls back to the PUBLISHED box only when the trace carries no measured polygon, and says so
    in the returned reason -- a silent substitution of one landmark for another is rule 19's
    exact defect (one quantity, two landmarks) and it is what put three leg lengths in one leg.
    """
    n = len(tr.get("t", []))
    if "polx" in tr and "poly" in tr and len(tr["polx"]) == n:
        hf, hl, src = tr["polx"], tr["poly"], "measured foot polygon"
    elif "bos_half_fore" in tr:
        hf = [tr["bos_half_fore"]] * n; hl = [tr["bos_half_lat"]] * n
        src = "PUBLISHED theStance box (no measured polygon in this trace)"
    else:
        raise SystemExit("this trace carries neither a measured foot polygon nor a published "
                         "box -- refusing to classify a fall against a base of support that was "
                         "never recorded (rule 20).")
    out = classify_fall(tr["t"], tr["z"], tr["comx"], tr["comy"], hf, hl, z_target, fall_frac)
    out["base_source"] = src
    return out


# ── THE SELF-TEST: four synthetic falls, and they must come back four different labels ─────────
def _synth(kind, n=200, dur=8.0, ztgt=0.9201):
    t = np.linspace(0, dur, n)
    z = np.full(n, 0.95 * ztgt)
    cf = np.zeros(n); cl = np.zeros(n)
    hf = np.full(n, 0.1272); hl = np.full(n, 0.0961)     # this body's own measured polygon
    go = t > 4.0
    ramp = np.clip((t - 4.0) / 3.0, 0, 1)
    if kind == "lateral":
        cl = -0.812 * ramp; cf = 0.052 * ramp             # THE DOCUMENTED FALL, verbatim
        z = np.where(go, 0.95 * ztgt - 0.9 * ztgt * ramp, z)
    elif kind == "forward":
        cf = +0.60 * ramp; cl = 0.03 * ramp
        z = np.where(go, 0.95 * ztgt - 0.9 * ztgt * ramp, z)
    elif kind == "backward":
        cf = -0.60 * ramp; cl = 0.03 * ramp
        z = np.where(go, 0.95 * ztgt - 0.9 * ztgt * ramp, z)
    elif kind == "collapse":
        cf = 0.02 * ramp; cl = 0.02 * ramp                # stays well inside the polygon
        z = np.where(go, 0.95 * ztgt - 0.9 * ztgt * ramp, z)
    elif kind == "no_fall":
        cf = 0.03 * np.sin(t); cl = 0.02 * np.cos(t)
    return t, z, cf, cl, hf, hl, ztgt


def main() -> int:
    print("\nFALL CLASSIFIER -- self-test on five synthetic trajectories")
    print("=" * 92)
    print(f"{'expected':12}{'got':12}{'conf':>7}{'t_fall':>9}{'fore':>8}{'lat':>8}  reason")
    ok = True
    got_labels = []
    for kind in ("lateral", "forward", "backward", "collapse", "no_fall"):
        r = classify_fall(*_synth(kind))
        got_labels.append(r["label"])
        hit = r["label"] == kind
        ok &= hit
        tf = f"{r['t_fall']:.2f}" if r["t_fall"] is not None else "-"
        print(f"{kind:12}{r['label']:12}{r['confidence']:>7.2f}{tf:>9}"
              f"{r.get('peak_fore_frac', 0):>8.2f}{r.get('peak_lat_frac', 0):>8.2f}  "
              f"{'' if hit else 'MISLABELLED -- '}{r['reason'][:60]}")
    print("-" * 92)
    # FALSIFIER 1: the documented lateral fall must come back lateral.
    lat = classify_fall(*_synth("lateral"))
    print(f"  FALSIFIER 1 (the documented lateral stand fall, CoM-y -812 mm vs CoM-x 52 mm): "
          f"{'PASS' if lat['label'] == 'lateral' else 'FAIL'} -- got {lat['label']!r}, "
          f"confidence {lat['confidence']:.2f}")
    # FALSIFIER 2: the labels must be DISTINCT, or this is a constant wearing a function's coat.
    distinct = len(set(got_labels)) == len(got_labels)
    print(f"  FALSIFIER 2 (does it discriminate?): {len(set(got_labels))} distinct labels over "
          f"5 trajectories -> {'PASS' if distinct else 'FAIL -- it is not classifying'}")
    print("=" * 92)
    print(f"  VERDICT: {'PASS' if (ok and distinct) else 'FAIL'}")
    return 0 if (ok and distinct) else 1


if __name__ == "__main__":
    sys.exit(main())
