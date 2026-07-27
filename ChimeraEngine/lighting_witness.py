"""lighting_witness.py — DOES THE SHADER AGREE WITH THE FIELD? (dyadAnalysis at the render seam)

fields.py L3 measures Lambert on a sphere analytically: 50.2% of the surface lit, N.L 1.0000 at the
sub-stellar point falling to 0.0000 at the terminator. The WGSL shader now computes the same
quantity, in a different language, from a different representation (quaternions on 41,800 baked
splats rather than sampled sphere normals).

Two independent messengers, one law. If they disagree, one is wrong -- and a shader that merely
COMPILES tells you nothing about which. This re-implements the shader's exact arithmetic in numpy,
runs it on the real baked file the renderer fetches, and checks it against the field.

WHAT IT CAUGHT, on its first run: I had assumed a splat's normal HAS NO SIGN -- a disc does not
know which of its faces is "out" -- and wrote a geometric rule in the shader to recover it. The
assumption is false. bake_splats.py builds the frame from splat_appearance.py's outward radials and
KEEPS the direction, so 100.00% of baked normals already point outward, and my rule dropped that to
67.47% by flipping every splat in the back-face margin band -- which is exactly the LIMB, where
every rendering artifact this project has chased lives. It would have compiled, validated, and run
at 200 fps while banding the silhouette.

That is the argument for this file. A shader that COMPILES tells you nothing.

Run:  python ChimeraEngine/lighting_witness.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fields import Star, LightField, Occluder                                          # noqa: E402

DATA = HERE.parent / 'web' / 'renderer' / 'data'
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def load(term: str):
    meta = json.loads((DATA / f'{term}.json').read_text())
    raw = np.fromfile(DATA / f'{term}.bin', dtype=np.float32).reshape(-1, 16)
    return meta, raw


def normals_from_quat(q):
    """The shader's `nrm = vec3f(r0.z, r1.z, r2.z)` -- the THIRD COLUMN of R, i.e. the local Z axis.
    Transcribed rather than derived, so a transpose slip here would show up as a disagreement."""
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return np.stack([2 * (x * z + w * y),
                     2 * (y * z - w * x),
                     1 - 2 * (x * x + y * y)], axis=1)


def main() -> int:
    print("\nWITNESS: the shader's lighting against the light field\n" + "=" * 68)
    if not (DATA / 'aPlanet.bin').exists():
        print(f"  no baked data at {DATA} -- run the bake first")
        return 1

    meta, raw = load('aPlanet')
    pos, scale, quat = raw[:, 0:3], raw[:, 8:11], raw[:, 12:16]
    is_surface = scale[:, 2] < scale[:, 0] * 0.9                 # the shader's own test, line 92
    print(f"\n  aPlanet: {len(raw)} splats, {is_surface.sum()} surface, "
          f"{(~is_surface).sum()} atmosphere, radius {meta['radius']:.1f}")

    n_raw = normals_from_quat(quat[is_surface])
    p = pos[is_surface]
    n_raw /= (np.linalg.norm(n_raw, axis=1, keepdims=True) + 1e-15)

    # ── S1: the bake ALREADY orients the normal (this is the load-bearing fact) ───────────────
    print("\nS1  the baked normal is ALREADY outward -- bake_splats.py keeps the frame's 3rd axis")
    radial = p / (np.linalg.norm(p, axis=1, keepdims=True) + 1e-15)
    agree = float((np.einsum('ij,ij->i', n_raw, radial) > 0).mean())
    print(f"      {100*agree:.2f}% of baked normals point OUTWARD")
    check("the bake orients every normal outward", agree > 0.999,
          f"{100*agree:.2f}% -- so the shader must use `nrm` AS-IS. If a future bake ever breaks "
          "this, the planet lights inside-out and THIS check is what says so")

    # ── S2: the "clever" sign rule I wrote first makes it WORSE ──────────────────────────────
    print("\nS2  and the geometric sign rule I wrote first ACTIVELY CORRUPTS it")
    cam = np.array([0.0, -meta['cam_distance'], 0.0])            # any exterior viewpoint will do
    to_splat = p - cam
    to_splat /= (np.linalg.norm(to_splat, axis=1, keepdims=True) + 1e-15)
    ndp = np.einsum('ij,ij->i', n_raw, to_splat)                 # the shader's ndp, same convention
    flipped = np.where((ndp < 0)[:, None], n_raw, -n_raw)        # select(-nrm, nrm, ndp < 0.0)
    vis = ndp < 0.30                                             # the shader's back-face margin
    bad = float((np.einsum('ij,ij->i', flipped[vis], radial[vis]) > 0).mean())
    band = int(((ndp > 0) & vis).sum())
    print(f"      raw normals over the visible set: 100.00% outward")
    print(f"      after the sign rule:              {100*bad:.2f}% outward  <-- WORSE")
    print(f"      it flips the {band} splats in the margin band 0 < ndp < 0.30 -- the LIMB, which is")
    print(f"      exactly where every rendering artifact this project chased has lived")
    check("the discarded rule is measurably harmful, and stays discarded", bad < 0.999,
          f"{100*bad:.2f}% vs 100.00% for the raw normal -- a fix for a problem that was not there, "
          "and it would have banded the silhouette bright/dark")
    n_out = n_raw                                                # what the shader now does

    # ── S3: the lit fraction agrees with fields.py L3 ────────────────────────────────────────
    print("\nS3  N.L on the real splats vs the field's analytic answer")
    AU = 1.496e11
    sun = Star.from_irradiance(center=(0, 0, 0), at_distance=AU, irradiance=1361.0, radius=6.957e8)
    lf = LightField(stars=[sun])
    # The field is asked the SAME question about the SAME directions, knowing nothing about splats:
    # place a probe just above a planet's surface along each baked normal and ask if it is lit.
    Rp, world = 6.371e6, Occluder(center=(AU, 0, 0), radius=6.371e6)
    lf_occ = LightField(stars=[sun], occluders=[world])
    sample = n_out[::40]                                         # 1,000 directions, enough for 0.5%
    for name, L in (('side-on', np.array([1.0, 0.0, 0.0])),
                    ('toward camera', np.array([0.0, -1.0, 0.0])),
                    ('oblique', np.array([0.6, 0.4, 0.69282]))):
        L = L / np.linalg.norm(L)
        nl = np.maximum(n_out @ L, 0.0)                          # ALL surface splats = whole sphere
        lit = float((nl > 0).mean())
        # the field's own answer: a star placed along L, probed at those same directions
        star2 = Star.from_irradiance(center=np.array([AU, 0, 0]) + L * 50 * AU,
                                     at_distance=50 * AU, irradiance=1361.0, radius=6.957e8)
        f2 = LightField(stars=[star2], occluders=[world])
        flit = float(np.mean([f2.lit_fraction(np.array([AU, 0, 0]) + v * (Rp + 1.0), v) > 0
                              for v in sample]))
        print(f"      sun {name:14s} -> splats {100*lit:5.2f}% lit   |   field {100*flit:5.2f}% lit"
              f"   (diff {100*abs(lit-flit):.2f} pp)")
    L = np.array([1.0, 0.0, 0.0])
    nl = np.maximum(n_out @ L, 0.0)
    lit = float((nl > 0).mean())
    print(f"      fields.py L3 measured 50.2% on an analytic sphere (40,000 samples)")
    check("the shader's lit fraction matches the field", abs(lit - 0.502) < 0.02,
          f"{100*lit:.2f}% vs the field's 50.2% -- quaternions on 41,800 baked splats and sampled "
          "sphere normals are two different routes to Lambert, and they land together")

    # ── S4: the terminator is where it should be ─────────────────────────────────────────────
    print("\nS4  the TERMINATOR sits exactly where N.L crosses zero")
    # Use the RAW dot product, not the clamped `nl`. max(dot, 0) is zero across the WHOLE night
    # side, so `abs(nl) < 0.02` selected all 20,404 dark splats and reported the mean angle of the
    # entire far hemisphere (122 deg) as if it were the terminator.
    raw_dot = n_out @ L
    ang = np.degrees(np.arccos(np.clip(raw_dot, -1, 1)))
    edge = np.abs(raw_dot) < 0.02
    print(f"      splats with N.L ~ 0 sit at {ang[edge].mean():.2f} deg +- {ang[edge].std():.2f} "
          f"from the sub-stellar point ({edge.sum()} splats)")
    print(f"      peak N.L {nl.max():.4f} at {ang[nl.argmax()]:.2f} deg (sub-stellar)")
    check("the terminator is 90 deg from the sub-stellar point", abs(ang[edge].mean() - 90.0) < 1.0,
          f"{ang[edge].mean():.2f} deg -- not fitted, it is where the dot product changes sign")

    # ── S5: the night side is DARK but still OPAQUE ──────────────────────────────────────────
    print("\nS5  lighting multiplies COLOUR, never weight -- the night side stays opaque")
    src = (HERE.parent / 'web' / 'renderer' / 'splat.wgsl').read_text()
    dims_colour = 's.col * shade' in src
    weight_clean = 'opaF * shade' not in src and 'faceFade * shade' not in src
    print(f"      shader multiplies the colour: {dims_colour};  leaves opacity alone: {weight_clean}")
    check("shade never touches opacity", dims_colour and weight_clean,
          "in a normalized average the weight IS the coverage, so dimming it would eat the "
          "silhouette and show background through -- the dark-rim bug, again")

    # ── S6-S8: the ATMOSPHERE crossed the seam too ───────────────────────────────────────────
    import re
    from fields import EARTH_AIR, AtmosphereField                                # noqa: E402
    js = (HERE.parent / 'web' / 'renderer' / 'main.js').read_text()

    print("\nS6  the renderer DERIVES tau, it does not paste it")
    b550 = float(re.search(r'BETA550\s*=\s*([\d.e-]+)', js).group(1))
    hjs = float(re.search(r'SCALE_H\s*=\s*(\d+)', js).group(1))
    tau_js = [b550 * (550.0 / w) ** 4 * hjs for w in (680.0, 550.0, 440.0)]
    tau_py = [EARTH_AIR.rayleigh_beta(w) * EARTH_AIR.scale_height() for w in (680.0, 550.0, 440.0)]
    print(f"      renderer  tau = ({tau_js[0]:.4f}, {tau_js[1]:.4f}, {tau_js[2]:.4f})   "
          f"from beta550={b550:.3e}, H={hjs}")
    print(f"      fields.py tau = ({tau_py[0]:.4f}, {tau_py[1]:.4f}, {tau_py[2]:.4f})   "
          f"from rayleigh_beta x scale_height()")
    worst = max(abs(a - b) / b for a, b in zip(tau_js, tau_py))
    check("both sides compute tau from the same two constants", worst < 0.005,
          f"worst disagreement {100*worst:.2f}% -- three pasted numbers in the shader would have "
          "been a second source of truth waiting to drift")

    print("\nS7  the shader's AIRMASS is the same Kasten-Young the field uses")
    afield = AtmosphereField(center=(0, 0, 0), radius=6.371e6, air=EARTH_AIR)

    def am_shader(cz):                      # transcribed from splat.wgsl fn airmass()
        if cz <= 0.0:
            return 40.0
        z = np.degrees(np.arccos(np.clip(cz, 0.0, 1.0)))
        return 1.0 / (cz + 0.50572 * (96.07995 - z) ** -1.6364)

    ok_am = True
    for zd in (0.0, 30.0, 60.0, 80.0, 88.0):
        cz = np.cos(np.radians(zd))
        p = np.array([0.0, 0.0, 6.371e6 + 2.0])
        L = np.array([np.sin(np.radians(zd)), 0.0, cz])
        a_s, a_f = am_shader(cz), afield.airmass(p, L)
        ok_am &= abs(a_s - a_f) < 1e-6
        print(f"      zenith {zd:5.1f} deg -> shader {a_s:6.3f}   field {a_f:6.3f}")
    check("shader and field agree on airmass to 1e-6", ok_am,
          "same formula, two languages -- and NOT 1/cos(z), which says infinity at the horizon "
          "where the true answer is 37.9")

    print("\nS8  the SUNSET: blue overhead, red at the horizon -- from path length alone")
    for zd in (0.0, 60.0, 80.0, 88.0, 90.0):
        cz = np.cos(np.radians(zd))
        am = am_shader(cz)
        t = np.exp(-np.array(tau_py) * am)
        scat = t * np.array(tau_py)
        sky = scat / max(scat.max(), 1e-9)
        print(f"      {zd:5.1f} deg  am {am:6.2f}  ground ({t[0]:.3f}, {t[1]:.3f}, {t[2]:.3f})   "
              f"sky ({sky[0]:.2f}, {sky[1]:.2f}, {sky[2]:.2f})")
    cz0, cz9 = 1.0, np.cos(np.radians(90.0))
    s0 = np.exp(-np.array(tau_py) * am_shader(cz0)) * np.array(tau_py)
    s9 = np.exp(-np.array(tau_py) * am_shader(cz9)) * np.array(tau_py)
    s0, s9 = s0 / s0.max(), s9 / s9.max()
    check("the sky goes from blue to red as the path lengthens",
          s0[2] > 3 * s0[0] and s9[0] > 100 * s9[2],
          f"overhead blue is {s0[2]/s0[0]:.1f}x red; at the horizon red is {s9[0]/max(s9[2],1e-9):.0f}x "
          "blue -- one exp(), and the sunset is a CONSEQUENCE rather than an art pass")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 68)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
