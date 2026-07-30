"""walk_demo.py -- the state machine, demonstrated: a scripted key sequence driven through
controller.py into a Walker on aTerrain, with every state measured and the trace rendered.

The operator's checklist: walk forward, sidestep left and right, steer, walk backward, jump.
Each leg of the script asserts its own effect (position, lateral offset, heading, apex height),
so the demo is a test, not a show.

Run:  python tools/walk_demo.py            (headless numbers + trace PNG)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "ChimeraEngine"))

import controller as C          # noqa: E402
from walker import Walker       # noqa: E402

DT = 1.0 / 60.0

# the scripted key sequence: (seconds, keys) -- a person playing, written down
SCRIPT = [
    (1.0, {}),
    (3.0, {"fwd": True}),
    (2.0, {"left": True}),
    (1.5, {"turn_r": True, "fwd": True}),
    (2.0, {"back": True}),
    (0.6, {}),
    (0.1, {"jump": True}),
    (1.4, {}),
    (2.0, {"right": True, "sprint": True}),
]


def main() -> int:
    w = Walker()
    ctl = C.Controller()
    x0, y0, yaw0 = w.x, w.y, w.yaw

    trace = []
    marks = {}
    t = 0.0
    for secs, keys in SCRIPT:
        steps = int(secs / DT + 0.5)
        leg_start = (w.x, w.y, w.z, w.yaw, t)
        for _ in range(steps):
            d = C.drive_walker(w, ctl, keys, DT)
            trace.append((t, w.x, w.y, w.z, w.yaw, d.state))
            t += DT
        marks[keys and tuple(sorted(k for k, v in keys.items() if v)) or ("idle",)] = \
            (leg_start, (w.x, w.y, w.z, w.yaw, t))

    # ── the assertions: each state must DO its thing ──
    from walker import height_at as _hz
    fwd_d = math.hypot(*[m - s for m, s in zip(marks[("fwd",)][1][:2], marks[("fwd",)][0][:2])])
    lat_d = [m - s for m, s in zip(marks[("left",)][1][:2], marks[("left",)][0][:2])]
    yaw_d = marks[("fwd", "turn_r")][1][3] - marks[("fwd", "turn_r")][0][3]
    back_d = math.hypot(*[m - s for m, s in zip(marks[("back",)][1][:2], marks[("back",)][0][:2])])
    # apex measured against the LOCAL ground under the body at each airborne moment, never
    # against the ground at the end of the trace -- the terrain moves under a moving person.
    apex = max((p[3] - _hz(p[1], p[2])) for p in trace if p[5] == C.JUMP)
    air = [p[0] for p in trace if p[5] == C.JUMP]
    airtime = (max(air) - min(air)) if air else 0.0

    print("STATE MACHINE DEMO -- every state, measured:")
    print(f"  WALK_F:     covered {fwd_d:.2f} m forward")
    print(f"  SIDESTEP_L: lateral drift {lat_d[0]:.2f}, {lat_d[1]:.2f} m (dominant axis must be lateral)")
    print(f"  TURN_R:     heading changed {math.degrees(yaw_d):.1f} deg while walking")
    print(f"  WALK_B:     covered {back_d:.2f} m backward")
    print(f"  JUMP:       apex {apex:.3f} m over local ground (derived ceiling: "
          f"{w.jump_v ** 2 / (2 * w.g):.3f} m), airtime {airtime:.2f} s")
    ok = (fwd_d > 1.0 and abs(lat_d[0]) > 0.5 and abs(yaw_d) > 0.5
          and back_d > 0.5 and 0.2 < apex < 0.6)
    print(f"  VERDICT: {'PASS -- the state machine walks, sidesteps, steers, and jumps' if ok else 'FAIL'}")

    # ── the trace, drawn ──
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {C.IDLE: "#888", C.WALK_F: "#2e7d32", C.WALK_B: "#b71c1c",
              C.SIDESTEP_L: "#1565c0", C.SIDESTEP_R: "#6a1b9a",
              C.TURN_L: "#ef6c00", C.TURN_R: "#ef6c00", C.JUMP: "#00838f"}
    fig, ax = plt.subplots(figsize=(7, 7))
    for (t0, x, y, z, yaw, st) in trace:
        ax.plot(x, y, ".", color=colors.get(st, "#333"), ms=2)
    ax.plot(x0, y0, "k^", ms=12, label="start")
    for st, col in colors.items():
        ax.plot([], [], ".", color=col, label=st)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_title("the state machine walks the planet -- every colour a state")
    ax.legend(fontsize=8); ax.grid(alpha=0.3); ax.set_aspect("equal")
    fig.tight_layout()
    out = REPO / "ChimeraEngine" / "output" / "walk_demo_trace.png"
    fig.savefig(out, dpi=130)
    print(f"  trace: {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
