"""Supplementary probe beyond the pre-registered window.

The pre-registered window [11.2125, 22.425] N.m is CLOSED by the sweep
(falsifier fired at 22.425 with combined ratio 1.001086).  This probe does
NOT reopen it: it characterizes the frontier at 3x and 4.5x so the receipt
can distinguish "no admissible cap exists" from "an admissible cap exists
above the window and is musculature-unproducible a fortiori".  The verdict
(CLOSED) is unchanged under either outcome.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from derive_posture_cap_sweep import CAP_BASE, solve_cap  # noqa: E402

OLD = np.array([-0.254, -0.0835, 0.087, 0.2575, 0.3292, 0.2182, 0.1201,
                0.0588, -0.0441, -0.1568, -0.254, -0.0835, 0.087,
                0.2575, 0.3292, 0.2182, 0.1201, 0.0588, -0.0441, -0.1568, -0.254])

if __name__ == "__main__":
    starts = [np.zeros(2 * 21), np.r_[OLD, np.gradient(OLD, 0.71 / 20.0)]]
    out = {}
    for cap in (3.0 * CAP_BASE, 4.5 * CAP_BASE):
        summary, _ = solve_cap(cap, starts)
        out[f"{cap:.4f}"] = summary
        print(f"cap={cap:.4f} ({cap / CAP_BASE:.1f}x): combined={summary['max_combined_ratio']:.6f} "
              f"posture_req={summary['max_required_posture_Nm']:.4f} admissible={summary['admissible']} "
              f"worst_phi={summary['worst_node']['phi']}")
    (HERE / "probe_beyond_window.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("written", HERE / "probe_beyond_window.json")
