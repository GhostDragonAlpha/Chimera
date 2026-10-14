"""measure_fall_realbody.py -- F-SLICE-FALL on the REAL BODY (lane
slice_real_body_20260920; adapted from playable_slice_20260921/measure_fall.py,
whose build_stand_in_body no longer exists: the tick body is
scene_boot.build_real_body now).

The engine's own root law (banked constants, membrane_tick.hpp/cpp, nothing
fitted): y'' = min(50*m*g, k*max(0,-y) + c*max(0,-vy))/m - g,
k=1.3562e7, c=6.062e5, m=13824.5, g=9.81. The 0921 capsule receipt measured
the shape: the centered import starts penetrating, the spring's stored energy
launches the body to the root clamp, then the law's vertical damping gives a
long terminal descent at the law's own terminal velocity.

INVARIANTS (all derived from the banked constants + the import's own stats):
  I0 THE IMPORT: /mesh_import answers ok on the real payload (F-BODY-CAP's
     engine half) and reports the authored lowest vertex ymin.
  I1 THE CLAMP: peak root_y = 3.0 m within 1 cm.
  I2 THE TERMINAL DESCENT: median |vy| over the airborne+near-ground descent
     window == m*g/c = 0.223719 m/s to <= 1e-6 RELATIVE (the carried prereg's
     bar: the identity is geometry-independent; tau = m/c = 0.0228 s means the
     window is fully converged to float precision).
  I3 THE EQUILIBRIUM SINK: settled lowest vertex == -(m*g/k) = -0.010000 m
     within 10%; the settled ROOT is predicted (not fitted) as
     root_eq = -0.010000 - ymin and only used for the stop condition.

PASS = I0 ok AND I1 within 1 cm AND I2 within 1e-6 relative AND I3 within 10%.
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
    arr = np.frombuffer(raw[4:4 + n * 36], dtype=np.float32)
    return float(arr[1::9].min())


def main() -> int:
    port = sb.free_port()
    exe_dir = SLICE.parents[1] / ".tmp" / "slice_build" / "Release"
    proc = subprocess.Popen(
        [str(exe_dir / "chimera_engine.exe"), str(port), "--no-restore", "--hidden"],
        cwd=str(exe_dir),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    url = f"http://127.0.0.1:{port}"
    out = {"falsifier": "F-SLICE-FALL", "body": "the real skeleton "
           "(standing_body.obj, sha-pinned)", "engine_url": url}
    try:
        sb.wait_engine(url)
        obj, rec = sb.build_real_body()
        res = sb.http_post(url, "/mesh_import", b"O" + obj)
        out["i0_import"] = {
            "ok": bool(res.get("ok")),
            "authored_lowest_ymin_m": float(res.get("ymin", "nan")),
            "import_stats": {k: res[k] for k in res if k != "ok"},
        }
        assert res.get("ok"), res
        ymin = float(res["ymin"])
        root_eq_pred = -SINK_DERIVED - ymin
        # arm gravity and sample the WHOLE transient at the loopback's rate
        sb.http_post(url, "/tick_gravity", b'{"on":true}',
                     ctype="application/json")
        t0 = time.perf_counter()
        ys, vys = [], []
        calm = 0
        while time.perf_counter() - t0 < 60.0:
            st = sb.http_get_json(url, "/tick_state")
            t = time.perf_counter() - t0
            ys.append(float(st["root_y"]))
            vys.append(float(st["root_vy"]))
            # stop once parked at the derived equilibrium (body-agnostic:
            # the equilibrium follows from the banked constants + ymin)
            if (t > 12.0 and abs(float(st["root_vy"])) < 1e-3
                    and abs(float(st["root_y"]) - root_eq_pred) < 2e-3):
                calm += 1
                if calm >= 20:
                    break
            else:
                calm = 0
            time.sleep(0.01)
        ys, vys = np.array(ys), np.array(vys)
        peak_y = float(ys.max())
        m_desc = (ys < 2.5) & (ys > 0.6) & (vys < 0)
        vy_desc = -vys[m_desc]
        vt_meas = float(np.median(vy_desc)) if len(vy_desc) else None
        out["transient"] = {
            "samples": int(len(ys)),
            "peak_root_y_m": round(peak_y, 4),
            "descent_samples": int(len(vy_desc)),
            "settled_root_y_m": round(float(ys[-1]), 6),
            "root_eq_predicted_m": round(root_eq_pred, 6),
        }
        out["i1_clamp"] = {
            "derived_m": ROOT_CLAMP_M,
            "measured_peak_root_y_m": round(peak_y, 4),
            "abs_error_m": round(abs(peak_y - ROOT_CLAMP_M), 4),
            "within_1cm": bool(abs(peak_y - ROOT_CLAMP_M) <= 0.01),
        }
        out["i2_terminal_descent"] = {
            "derived_vt_mps": round(VT_DERIVED, 9),
            "measured_median_vt_mps": round(vt_meas, 9) if vt_meas else None,
            "rel_error": round(abs(vt_meas - VT_DERIVED) / VT_DERIVED, 12)
            if vt_meas else None,
            "within_1e-6_relative": bool(abs(vt_meas - VT_DERIVED)
                                         <= 1e-6 * VT_DERIVED) if vt_meas else False,
            "tau_derived_s": round(TAU_DERIVED, 6),
            "note": "vt = m*g/c; the descent window (root_y in (2.5, 0.6)) "
                    "is fully converged: tau = m/c = 0.0228 s",
        }
        raw = sb.http_get_raw(url, "/verts")
        lo_meas = lowest_y(raw)
        out["i3_equilibrium_sink"] = {
            "derived_m": round(SINK_DERIVED, 6),
            "measured_lowest_m": round(lo_meas, 6),
            "abs_error_m": round(abs(lo_meas + SINK_DERIVED), 6),
            "within_10pct": bool(abs(lo_meas + SINK_DERIVED)
                                 <= 0.1 * SINK_DERIVED),
        }
        out["pass"] = bool(out["i0_import"]["ok"]
                           and out["i1_clamp"]["within_1cm"]
                           and out["i2_terminal_descent"]["within_1e-6_relative"]
                           and out["i3_equilibrium_sink"]["within_10pct"])
        out["law"] = ("y'' = min(50*m*g, k*max(0,-y) + c*max(0,-vy))/m - g; "
                      "k=1.3562e7, c=6.062e5, m=13824.5, g=9.81; damping acts "
                      "whenever vy<0, airborne included (membrane_tick.cpp); "
                      "the constants are banked and geometry-independent")
    finally:
        proc.terminate()
    (HERE / "fall_measurement_realbody.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "i0_import"
                      or True}, indent=1)[:2400])
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
