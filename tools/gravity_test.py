"""gravity_test.py -- THE FALL: the F-bar script for the movement law
(prereg appended to docs/evidence/agent_fleet/MATTER_KERNEL/
SEAL_PREREGISTRATION.md, "THE MOVEMENT LAW PREREGISTRATION").

HTTP only, no engine build/run from here:
  GET  /tick_state     baseline + final: gravity_on, root_y, root_vy,
                       every sealed cell's P (bar: exactly 0),
                       conserve_pct (bar: |.| <= 0.01)
  POST /tick_gravity   {"on": true}   -- THE LEAD WIRES THIS ROUTE at the
                       build window (MembraneTick::set_gravity). Until
                       then run with --skip-enable: the script samples
                       and reports the curve without a verdict.
  GET  /verts          [u32 n][f32 x9 per vert] -- the lowest vertex's
                       world y is the fall curve.

Bars (from the prereg):
  F1  the root moves along Y by >= 3 mm within the window (the
      measured authored rest starts 1.95 cm BELOW y=0, so the derived
      branch there is a 9.5 mm RISE to equilibrium; a floor-clear
      start DROPS -- either branch is the law answering).
  F2  settled penetration within [-1.2 cm, +0.2 cm] (W/k = 1.0 cm),
      root_vy -> 0, all pressures exactly 0.
  F3  |conserve_pct| <= 0.01 (the 13.8245 m^3 sum stands).
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import time
import urllib.error
import urllib.request

TOL_PENET_LO = -0.012   # m: 1 cm sink + 2 mm float tolerance
TOL_PENET_HI = 0.002    # m: above-floor rest is not "held"
MIN_MOTION_M = 0.003    # m: measurable root motion (F1)
VY_SETTLE = 0.05        # m/s: settled means settled
CONSERVE_BAR = 0.01     # percent (F3, pre-gravity measured ~1e-4 %)


def http_get(base: str, path: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_post(base: str, path: str, body: bytes, timeout: int = 30) -> bytes:
    req = urllib.request.Request(base + path, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lowest_y(base: str) -> float:
    raw = http_get(base, "/verts")
    (n,) = struct.unpack_from("<I", raw, 0)
    if len(raw) < 4 + n * 36:
        raise RuntimeError(f"/verts short: {len(raw)} bytes for {n} verts")
    # y of vert v sits at offset 4 + v*36 + 4; scan without materializing
    best = float("inf")
    for v in range(n):
        (y,) = struct.unpack_from("<f", raw, 4 + v * 36 + 4)
        if y < best:
            best = y
    return best


def pressures_pa(st: dict) -> list[float]:
    return [abs(c["P"]) for c in st.get("cells", [])] or (
        [abs(st.get("P_lower", 0.0)), abs(st.get("P_upper", 0.0))])


def main() -> int:
    ap = argparse.ArgumentParser(description="THE FALL: gravity F-bar")
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--seconds", type=float, default=3.0,
                    help="sample window after enable (prereg watches 3 s)")
    ap.add_argument("--hz", type=float, default=10.0)
    ap.add_argument("--skip-enable", action="store_true",
                    help="do not POST /tick_gravity (route not wired yet); "
                         "instrument mode, no verdict")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    try:
        st0 = json.loads(http_get(base, "/tick_state"))
    except (urllib.error.URLError, OSError) as e:
        print(f"FAIL unreachable: the engine at {base} is not answering ({e})")
        return 2

    print("== baseline /tick_state")
    print(f"   gravity_on={st0.get('gravity_on')} sealed={st0.get('sealed')} "
          f"n_cells={st0.get('n_cells')} V_whole={st0.get('V_whole'):.6f} "
          f"conserve_pct={st0.get('conserve_pct'):.2e}")
    p0 = pressures_pa(st0)
    print(f"   |P| max={max(p0) if p0 else 0.0:.3e} Pa (bar: 0)")

    if not args.skip_enable:
        try:
            http_post(base, "/tick_gravity", b'{"on": true}')
        except urllib.error.HTTPError as e:
            print(f"FAIL route: POST /tick_gravity -> HTTP {e.code}; the lead "
                  f"must wire it to MembraneTick::set_gravity at the build "
                  f"window. Until then: python tools/gravity_test.py --skip-enable")
            return 2
        print("== gravity ON (POST /tick_gravity {\"on\": true})")
    else:
        print("== --skip-enable: instrument mode (no POST, no verdict)")

    y0 = lowest_y(base)
    print(f"== sampling /verts lowest-y for {args.seconds} s at {args.hz} Hz")
    print(f"   t=0.000  y={y0:+.5f}")
    curve = []
    t_end = time.monotonic() + args.seconds
    period = 1.0 / args.hz
    nxt = time.monotonic() + period
    while time.monotonic() < t_end:
        time.sleep(max(0.0, nxt - time.monotonic()))
        nxt += period
        y = lowest_y(base)
        curve.append((args.seconds - (t_end - time.monotonic()), y))
        print(f"   t={curve[-1][0]:6.3f}  y={y:+.5f}")

    st1 = json.loads(http_get(base, "/tick_state"))
    p1 = pressures_pa(st1)
    y_final = curve[-1][1] if curve else y0
    y_extreme = min(curve, key=lambda p: p[1])[1] if curve else y0
    motion = y_final - y0
    root_y = st1.get("root_y")
    root_vy = st1.get("root_vy")
    print("== final /tick_state")
    print(f"   root_y={root_y} root_vy={root_vy} "
          f"g_contact_n={st1.get('g_contact_n')} "
          f"conserve_pct={st1.get('conserve_pct'):.2e}")
    print(f"   motion={motion * 1000:+.2f} mm  extreme={y_extreme:+.5f}  "
          f"final={y_final:+.5f}")

    if args.skip_enable:
        print("VERDICT: INSTRUMENT-ONLY (no enable sent) -- wire "
              "/tick_gravity, then rerun without --skip-enable")
        return 0

    checks = [
        (f"F1 root moved along Y >= {MIN_MOTION_M * 1000:.0f} mm",
         abs(motion) >= MIN_MOTION_M),
        (f"F2 settled penetration in [{TOL_PENET_LO * 100:.1f}, "
         f"{TOL_PENET_HI * 100:.1f}] cm",
         TOL_PENET_LO <= y_final <= TOL_PENET_HI),
        (f"F2 root_vy settled (|{root_vy}| <= {VY_SETTLE})",
         root_vy is not None and abs(root_vy) <= VY_SETTLE),
        ("F2 all pressures exactly 0 throughout",
         max(p0 + p1) == 0.0 if (p0 or p1) else True),
        (f"F3 |conserve_pct| <= {CONSERVE_BAR}",
         abs(st1.get("conserve_pct", 0.0)) <= CONSERVE_BAR),
    ]
    ok = True
    for name, passed in checks:
        print(f"   [{'PASS' if passed else 'FAIL'}] {name}")
        ok &= passed
    verdict = ("PASS -- the fall law answers" if ok else
               "FAIL -- the falsifier fired; successor audit: contact "
               "sign/depth in step(), then seal translation-invariance, "
               "then boot mesh placement")
    print(f"VERDICT: {verdict}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
