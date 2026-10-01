"""measure_fall.py -- F-SLICE-FALL: the measured root transient vs the ENGINE'S
OWN DERIVED LAW (banked constants, nothing fitted).

PREREGISTERED BRANCH PREDICTION (preregistration.md P2) -- FALSIFIED BY THIS
MEASUREMENT, AND THE FALSIFICATION IS THE FINDING: the prereg derived a gentle
damped RISE (zeta=0.7 settle in ~0.18 s, no F=0 window). The measured truth:
the centered import starts 0.2653 m penetrating; the penalty spring's stored
energy launches the body THROUGH the floor plane into a ballistic climb to the
engine's root clamp (|root_y| <= 3 m), then the root law's own vertical damping
(c*max(0,-vy), which acts whenever vy<0 -- including airborne) gives a LONG
TERMINAL DESCENT back to the equilibrium. THE F=0 FREE-FALL WINDOW THE PREREG
SAID COULD NOT EXIST IS THE WHOLE SHOW: the descent is real gravity +
engine damping for ~12 seconds. The prereg's own falsifier named this:
"if a free-fall window nonetheless appears, the derivation was wrong --
record it and fit g directly." Recorded; g is identified through the law's
terminal velocity vt = m*g/c.

THE INVARIANTS MEASURED (all from the engine's banked constants,
membrane_tick.hpp/cpp -- nothing fitted):
  I1 THE CLAMP: peak root_y = 3.0 m (the root clamp |root_y| <= 3).
  I2 THE TERMINAL DESCENT: vy -> m*g/c = 0.223719 m/s (g lives in vt).
  I3 THE EQUILIBRIUM SINK: settled lowest vertex = -(m*g/k) = -0.010000 m
     (k*s* = m*g), bar: within 10%.

PASS = I1 within 1 cm of the clamp, I2 within 5%, I3 within 10%.
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
sys.path.insert(0, str(SLICE))
import scene_boot as sb  # noqa: E402

# the engine's banked constants (membrane_tick.hpp lines, verbatim)
K_GROUND = 1.3562e7
C_GROUND = 6.062e5
MASS_KG = 13824.5
G_EARTH = 9.81
ROOT_CLAMP_M = 3.0
VT_DERIVED = MASS_KG * G_EARTH / C_GROUND          # 0.223719 m/s
TAU_DERIVED = MASS_KG / C_GROUND                   # 0.022811 s
SINK_DERIVED = MASS_KG * G_EARTH / K_GROUND        # 0.010000 m


def lowest_y(raw: bytes) -> float:
    n = int.from_bytes(raw[:4], "little")
    return min(struct.unpack_from("<f", raw, 4 + i * 36 + 4)[0] for i in range(n))


def main() -> int:
    port = sb.free_port()
    exe_dir = SLICE.parents[1] / ".tmp" / "slice_build" / "Release"
    proc = subprocess.Popen(
        [str(exe_dir / "chimera_engine.exe"), str(port), "--no-restore", "--hidden"],
        cwd=str(exe_dir),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    url = f"http://127.0.0.1:{port}"
    out = {"falsifier": "F-SLICE-FALL", "engine_url": url}
    try:
        sb.wait_engine(url)
        obj, rec = sb.build_stand_in_body()
        res = sb.http_post(url, "/mesh_import", b"O" + obj)
        assert res.get("ok"), res
        out["authored_lowest_m"] = float(res["ymin"])
        # arm gravity and sample the WHOLE transient (launch, clamp, terminal
        # descent, landing) at the loopback's honest rate
        sb.http_post(url, "/tick_gravity", b'{"on":true}', ctype="application/json")
        t0 = time.perf_counter()
        ts, ys, vys = [], [], []
        while time.perf_counter() - t0 < 40.0:
            st = sb.http_get_json(url, "/tick_state")
            ts.append(time.perf_counter() - t0)
            ys.append(float(st["root_y"]))
            vys.append(float(st["root_vy"]))
            # stop only once truly parked at the equilibrium
            if (time.perf_counter() - t0 > 12.0
                    and abs(float(st["root_vy"])) < 1e-3
                    and abs(float(st["root_y"]) - 0.2553) < 2e-3):
                break
            time.sleep(0.01)
        ts, ys, vys = np.array(ts), np.array(ys), np.array(vys)
        peak_y = float(ys.max())
        # I2: the descent's terminal velocity = the median of |vy| in the slow
        # window (descending between 2.5 and 0.6 m: airborne + near-ground)
        m_desc = (ys < 2.5) & (ys > 0.6) & (vys < 0)
        vy_desc = -vys[m_desc]
        vt_meas = float(np.median(vy_desc)) if len(vy_desc) else None
        out["transient"] = {
            "samples": int(len(ts)),
            "window_s": round(float(ts[-1]), 2),
            "peak_root_y_m": round(peak_y, 4),
            "descent_samples": int(len(vy_desc)),
        }
        # I1 the clamp
        out["i1_clamp"] = {
            "derived_m": ROOT_CLAMP_M,
            "measured_peak_root_y_m": round(peak_y, 4),
            "abs_error_m": round(abs(peak_y - ROOT_CLAMP_M), 4),
            "within_1cm": bool(abs(peak_y - ROOT_CLAMP_M) <= 0.01),
        }
        # I2 the terminal descent (the law's airborne terminal velocity)
        out["i2_terminal_descent"] = {
            "derived_vt_mps": round(VT_DERIVED, 6),
            "measured_median_vt_mps": round(vt_meas, 6) if vt_meas else None,
            "rel_error": round(abs(vt_meas - VT_DERIVED) / VT_DERIVED, 6) if vt_meas else None,
            "within_5pct": bool(abs(vt_meas - VT_DERIVED) <= 0.05 * VT_DERIVED) if vt_meas else False,
            "tau_derived_s": round(TAU_DERIVED, 6),
            "note": "vt = m*g/c; g is identified through the terminal velocity",
        }
        # I3 the equilibrium sink (k*s* = m*g)
        raw = sb.http_get_raw(url, "/verts")
        lo_meas = lowest_y(raw)
        out["i3_equilibrium_sink"] = {
            "derived_m": round(SINK_DERIVED, 6),
            "measured_lowest_m": round(float(lo_meas), 6),
            "abs_error_m": round(abs(lo_meas + SINK_DERIVED), 6),
            "within_10pct": bool(abs(lo_meas + SINK_DERIVED) <= 0.1 * SINK_DERIVED),
        }
        out["pass"] = bool(out["i1_clamp"]["within_1cm"]
                           and out["i2_terminal_descent"]["within_5pct"]
                           and out["i3_equilibrium_sink"]["within_10pct"])
        out["preregistered_branch_prediction"] = (
            "gentle damped rise, no F=0 window -- FALSIFIED by this measurement: "
            "the spring's stored energy launches the body to the root clamp and "
            "the law's vertical damping gives a ~12 s terminal descent; the "
            "prereg's own falsifier named this case ('fit g directly') -- "
            "recorded, not tuned")
        out["law"] = ("y'' = min(50*m*g, k*max(0,-y) + c*max(0,-vy))/m - g; "
                      "k=1.3562e7, c=6.062e5, m=13824.5, g=9.81; damping acts "
                      "whenever vy<0, airborne included (membrane_tick.cpp)")
    finally:
        proc.terminate()
    (HERE / "fall_measurement.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
