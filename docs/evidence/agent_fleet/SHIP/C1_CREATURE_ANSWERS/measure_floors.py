"""measure_floors.py -- C1r "creature-answers" prereg measurement battery.

Runs on the CURRENT binary (reflex code does not exist in it yet): measures
the quantities the reflex thresholds must be derived FROM, so no threshold
is a taste number:

  M1  rest pressure floor          max|P| per sealed cell, all rungs off
  M2  touch pressure ladder        per-cell P for held touches at 5 forces
  M3  dP/dt scales                 touch onset rate vs gait-walk swing rate
  M4  walk pmax + conserve_pct     the gait machine's own pressure witness
  M5  /verts rest drift            the zero-motion reference (breathing's
                                   negative control measures against this)

HTTP only: GET /tick_state, GET /verts, POST /tick_touch, /tick_touch_clear,
/tick_gravity, /tick_stance, /tick_gait (compact JSON -- the "on":true
literal-substring parse hazard, R4_GAIT_VERIFY/PROTOCOL.md).

Usage:  python measure_floors.py --base http://127.0.0.1:8163 --json out.json
"""
from __future__ import annotations

import argparse
import array
import json
import struct
import time
import urllib.request

MASS_KG = 13824.5
G_EARTH = 9.81
KAPPA = 4.6e-10          # sealed-cell water compressibility, 1/Pa


def http_get(base: str, path: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_post(base: str, path: str, body: bytes, timeout: int = 60) -> bytes:
    req = urllib.request.Request(base + path, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_state(base: str) -> dict:
    return json.loads(http_get(base, "/tick_state"))


def get_verts(base: str):
    raw = http_get(base, "/verts")
    (n,) = struct.unpack_from("<I", raw, 0)
    flt = array.array("f")
    flt.frombytes(raw[4:4 + n * 36])
    return n, flt


def cell_pressures(st: dict) -> list:
    return [abs(c.get("P", 0.0)) for c in st.get("cells", [])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8163")
    ap.add_argument("--json", default="floors.json")
    ap.add_argument("--walk", action="store_true",
                    help="also arm gravity+stance+gait for the walk scales")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    out: dict = {"base": base, "ts": time.strftime("%Y-%m-%d %H:%M:%S")}

    st = get_state(base)
    out["cells"] = [{"i": i, "v0": c["v0"], "ylo": c["ylo"], "yhi": c["yhi"],
                     "pieces": c["pieces"]}
                    for i, c in enumerate(st.get("cells", []))]
    print(f"== body: {len(out['cells'])} sealed cells, "
          f"V_whole={st.get('V_whole')}")

    # ---- M5 (first, at full rest): /verts zero-motion reference ------------
    n, f0 = get_verts(base)
    ymin0 = min(f0[v * 9 + 1] for v in range(n))
    ymax0 = max(f0[v * 9 + 1] for v in range(n))
    drift = 0.0
    t_end = time.monotonic() + 4.0
    while time.monotonic() < t_end:
        time.sleep(0.1)
        _, f1 = get_verts(base)
        d = max(abs(min(f1[v * 9 + 1] for v in range(n)) - ymin0),
                abs(max(f1[v * 9 + 1] for v in range(n)) - ymax0))
        drift = max(drift, d)
    out["M5_rest_vert_drift_m"] = drift
    print(f"[M5] /verts y-drift at full rest: {drift:.3e} m over 4 s")

    # ---- M1: rest pressure floor -------------------------------------------
    worst = 0.0
    cons = 0.0
    t_end = time.monotonic() + 4.0
    while time.monotonic() < t_end:
        time.sleep(0.05)
        st = get_state(base)
        worst = max(worst, max(cell_pressures(st), default=0.0))
        cons = max(cons, abs(st.get("conserve_pct", 0.0)))
    out["M1_rest_pmax_pa"] = worst
    out["M1_rest_conserve_worst_pct"] = cons
    print(f"[M1] rest max|P| {worst:.3e} Pa; |conserve_pct| worst {cons:.3e}")

    # ---- pick a belly hit: the mid-radius vertex of the torso band ---------
    torso = max(out["cells"], key=lambda c: c["v0"])
    ymid = 0.5 * (torso["ylo"] + torso["yhi"])
    best_v, best_r2 = 0, -1.0
    for v in range(n):
        y = f0[v * 9 + 1]
        if not (torso["ylo"] < y < torso["yhi"]):
            continue
        r2 = f0[v * 9 + 0] ** 2 + f0[v * 9 + 2] ** 2
        if r2 > best_r2:
            best_v, best_r2 = v, r2
    hit = [f0[best_v * 9 + 0], f0[best_v * 9 + 1], f0[best_v * 9 + 2]]
    out["belly_hit"] = hit
    print(f"[M2] belly hit vertex {best_v} at "
          f"({hit[0]:.3f}, {hit[1]:.3f}, {hit[2]:.3f})")

    # ---- M2/M3: the touch ladder with onset-rate capture -------------------
    ladder = []
    for F in (500.0, 2000.0, 10000.0, 20000.0, 50000.0):
        resp = http_post(base, "/tick_touch",
                         json.dumps({"hit": hit, "force_n": F}).encode())
        if b'"ok":true' not in resp:
            print(f"[M2] touch {F} N refused: {resp[:80]}")
            continue
        # onset capture: poll as fast as the server answers for 1.5 s
        series = []
        t0 = time.monotonic()
        while time.monotonic() - t0 < 1.5:
            s2 = get_state(base)
            series.append([s2.get("ts_us", 0), time.monotonic() - t0]
                          + cell_pressures(s2))
        peak = max(max(r[2:]) for r in series)
        # dP/dt from consecutive samples (per-cell max, positive only)
        rates = []
        for a, b in zip(series, series[1:]):
            dt = (b[0] - a[0]) / 1e6
            if dt > 1e-4:
                for pa, pb in zip(a[2:], b[2:]):
                    rates.append((pb - pa) / dt)
        ladder.append({"force_n": F, "peak_pa": peak,
                       "onset_rate_p95_pa_s": sorted(rates)[int(0.95 * len(rates))] if rates else 0.0,
                       "onset_rate_max_pa_s": max(rates) if rates else 0.0,
                       "n_samples": len(series)})
        print(f"[M2] F={F:>7.0f} N: peak|P| {peak:.3e} Pa, "
              f"onset dP/dt p95 {ladder[-1]['onset_rate_p95_pa_s']:.2e} "
              f"max {ladder[-1]['onset_rate_max_pa_s']:.2e} Pa/s")
        http_post(base, "/tick_touch_clear", b"{}")
        time.sleep(1.2)   # 2+ tissue taus: the dimple must fully relax
    out["M2_touch_ladder"] = ladder

    if args.walk:
        # ---- M4: the gait walk's own pressure witness ----------------------
        http_post(base, "/tick_gravity", b'{"on":true}')
        time.sleep(2.5)
        http_post(base, "/tick_stance", b'{"on":true}')
        time.sleep(1.0)
        http_post(base, "/tick_gait", b'{"on":true}')
        st = get_state(base)
        print(f"[M4] gait_on={st.get('gait_on')}")
        series = []
        t0 = time.monotonic()
        stride0 = st.get("gait_stride", 0)
        while time.monotonic() - t0 < 25.0:
            s2 = get_state(base)
            series.append([s2.get("ts_us", 0)]
                          + cell_pressures(s2)
                          + [s2.get("conserve_pct", 0.0)])
            if s2.get("gait_stride", 0) >= stride0 + 3:
                break
            time.sleep(0.03)
        pmax_series = [max(r[1:-1]) for r in series]
        rates = []
        for a, b in zip(series, series[1:]):
            dt = (b[0] - a[0]) / 1e6
            if dt > 1e-4:
                for pa, pb in zip(a[1:-1], b[1:-1]):
                    rates.append(abs(pb - pa) / dt)
        rates.sort()
        out["M4_walk"] = {
            "strides": s2.get("gait_stride", 0) - stride0,
            "pmax_max_pa": max(pmax_series),
            "pmax_typ_pa": sorted(pmax_series)[len(pmax_series) // 2],
            "dPdt_p50_pa_s": rates[len(rates) // 2] if rates else 0.0,
            "dPdt_p95_pa_s": rates[int(0.95 * len(rates))] if rates else 0.0,
            "dPdt_max_pa_s": rates[-1] if rates else 0.0,
            "conserve_worst_pct": max(abs(r[-1]) for r in series),
            "n_polls": len(series)}
        w = out["M4_walk"]
        print(f"[M4] walk: {w['strides']} strides, pmax max "
              f"{w['pmax_max_pa']:.3e} Pa (typ {w['pmax_typ_pa']:.3e}), "
              f"|dP/dt| p95 {w['dPdt_p95_pa_s']:.2e} max "
              f"{w['dPdt_max_pa_s']:.2e} Pa/s, |conserve| worst "
              f"{w['conserve_worst_pct']:.3e}")
        # teardown to rest
        http_post(base, "/tick_gait", b'{"on":false}')
        http_post(base, "/tick_stance", b'{"on":false}')
        http_post(base, "/tick_gravity", b'{"on":false}')
        time.sleep(1.5)
        st = get_state(base)
        out["M4_after_teardown_pmax"] = max(cell_pressures(st), default=0.0)
        print(f"[M4] teardown max|P| {out['M4_after_teardown_pmax']:.3e} Pa")

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"== written {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
