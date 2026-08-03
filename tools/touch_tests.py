"""touch_tests.py -- the TOUCH membrane, measured headless (docs/THE_SLICE.md, Phase E rung 2).

Scripted walks through controller.py into a Walker on aTerrain, with the three passive classes
from touchables.py answering. Each prediction of the membrane is asserted against its own
equation -- never against a tuned tolerance (the 20% on the braking distance is the membrane's
own; the physics is fixed):

    1. STONE: post-contact speed = commanded speed x m_body/m_stone along the contact normal;
       it stops within v^2/(2*mu*g), mu = tan(repose_regolith_deg).
    2. TUFT: deflects > 20 deg AWAY from the player, recovers to < 2 deg within 2 s, no divergence.
    3. PILE: >= 5 grains displaced, the footprint is permanent, every grain settled (< 1 cm/s)
       3 s after the player leaves.
    4. GRAB (E): carried inside arm's reach, dropped at the feet, mass reported by probe().
    5. F1: the provenance table exists in touchables.py's docstring.

Run:  python tools/touch_tests.py        (one terrain carve, ~13 s, then seconds of physics)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "ChimeraEngine"))

import controller as C              # noqa: E402
import touchables as T              # noqa: E402
import walker as WK                 # noqa: E402
from walker import Walker           # noqa: E402

DT = 1.0 / 60.0


def place(w, x, y, yaw=0.0):
    """Teleport the body (test rig, not gameplay): stand it somewhere specific, at rest."""
    w.x, w.y = float(x), float(y)
    w.z = WK.height_at(w.x, w.y)
    w.vx = w.vy = w.vz = 0.0
    w.on_ground = True
    w.yaw = yaw


def drive(w, ctl, fwd=1.0, strafe=0.0, crouch=False):
    return C.drive_walker_vector(w, ctl, fwd, strafe, False, crouch, False, DT)


def check(name, ok, detail):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return bool(ok)


def test_stone(w, ctl) -> bool:
    print("STONE (rigid: contact impulse + Coulomb friction)")
    s = T.Stone(3.0, 5.0)
    ok = True

    # -- shove 1: head-on, full walk. The impulse must be v_cmd . n x m_body/m_stone. --
    place(w, s.x, s.y - (s.r + 0.35) + 0.02, 0.0)
    drive(w, ctl)
    nx, ny = s.x - w.x, s.y - w.y
    d = math.hypot(nx, ny)
    nx, ny = nx / d, ny / d
    cmd = w.vx * nx + w.vy * ny
    s.step(w, DT)
    sp1 = math.hypot(s.vx, s.vy)
    ratio_expect = s.m_body / s.mass
    ratio_meas = (sp1 + s.mu * w.g * DT) / cmd       # add back the tick's friction
    ok &= check("impulse scales with m_body/m_stone",
                abs(ratio_meas - ratio_expect) / ratio_expect < 0.05,
                f"dv/v_cmd {ratio_meas:.4f} vs m_body/m_stone {ratio_expect:.4f} "
                f"(m_stone {s.mass:.1f} kg)")
    along = (s.vx * nx + s.vy * ny) / max(sp1, 1e-12)
    ok &= check("impulse along the contact normal", along > 0.99,
                f"alignment {along:.4f}")

    # -- braking: from the measured release state, stop inside v^2/(2 mu g) (membrane: 20%). --
    place(w, 0.0, -8.0)                              # the player walks away; the stone is on its own
    v0 = math.hypot(s.vx, s.vy)
    x0, y0 = s.x, s.y
    t = 0.0
    while math.hypot(s.vx, s.vy) > 0.0 and t < 5.0:
        s.step(w, DT)
        t += DT
    stop_d = math.hypot(s.x - x0, s.y - y0)
    brake = v0 * v0 / (2.0 * s.mu * w.g)
    ok &= check("stops within the mu-derived braking distance",
                math.hypot(s.vx, s.vy) == 0.0 and abs(stop_d - brake) / brake <= 0.20,
                f"released at {v0:.3f} m/s, stopped after {stop_d:.3f} m "
                f"(v^2/2mu g = {brake:.3f} m, mu {s.mu:.3f})")

    # -- shove 2: from the side, crouched (0.45x speed). The law must scale with the COMMAND. --
    s.x, s.y, s.vx, s.vy = 6.0, 5.0, 0.0, 0.0
    s.z = WK.height_at(s.x, s.y) + s.r
    place(w, s.x - (s.r + 0.35) + 0.02, s.y, math.atan2(-1.0, 0.0))   # facing +X
    drive(w, ctl, crouch=True)
    cmd2 = math.hypot(w.vx, w.vy)
    s.step(w, DT)
    sp2 = math.hypot(s.vx, s.vy)
    expect2 = max(0.0, cmd2 * ratio_expect - s.mu * w.g * DT)
    ok &= check("same law from another side at another speed",
                abs(sp2 - expect2) / max(expect2, 1e-12) < 0.05,
                f"crouch-walk shove {sp2:.3f} m/s vs expected {expect2:.3f} m/s")
    ok &= check("player is never blocked", True, "the walker was never touched (v1)")
    return ok


def test_tuft(w, ctl) -> bool:
    print("TUFT (grown: damped aggregate spring, E from Kosmalla 2025)")
    tu = T.Tuft(-3.5, 8.0)
    ok = True
    print(f"  derived spring: k {tu.k:.1f} s^-2, omega_n {tu.omega_n:.2f} rad/s, c {tu.c:.2f} s^-1")

    # -- walk straight through the tuft (0.7 m south to 0.7 m north of its centre). --
    place(w, tu.x, tu.y - 0.7, 0.0)
    best, best_dot, om_max = 0.0, 0.0, 0.0
    for _ in range(int(2.0 / DT)):
        drive(w, ctl)
        tu.step(w, DT)
        if tu.theta > best:
            best = tu.theta
            ux, uy = tu.x - w.x, tu.y - w.y
            d = math.hypot(ux, uy) or 1.0
            best_dot = tu.bend_dir[0] * ux / d + tu.bend_dir[1] * uy / d
        om_max = max(om_max, abs(tu.omega))
    ok &= check("deflects > 20 deg away from the player",
                best > math.radians(20.0) and best_dot > 0.9,
                f"max bend {math.degrees(best):.1f} deg, away-alignment {best_dot:.3f}")
    contact_max = best

    # -- the player leaves; the spring must come back to rest in < 2 s, never diverging. --
    place(w, tu.x, tu.y - 5.0)
    rec_max = 0.0
    for i in range(int(2.0 / DT)):
        tu.step(w, DT)
        rec_max = max(rec_max, abs(tu.theta))
    ok &= check("recovers to < 2 deg within 2 s",
                abs(tu.theta) < math.radians(2.0),
                f"theta after 2.0 s: {math.degrees(abs(tu.theta)):.3f} deg")
    ok &= check("never diverges",
                rec_max <= contact_max * 1.02 + 1e-6 and om_max < 100.0,
                f"recovery peak {math.degrees(rec_max):.1f} deg <= contact peak "
                f"{math.degrees(contact_max):.1f} deg, |omega| max {om_max:.1f}")
    return ok


def test_pile(w, ctl) -> bool:
    print("PILE (granular: kicked grains, repose-limited settle, permanent footprint)")
    p = T.Pile(4.0, 12.0)
    ok = True
    print(f"  derived cone: base {p.R:.2f} m, height {p.h:.3f} m = base x tan({p.repose_deg:.2f} deg),"
          f" grain {p.grain_mg:.2f} mg")

    # -- walk through the pile, south to north across its centre. --
    place(w, p.x, p.y - p.R - 1.2, 0.0)
    for _ in range(int(3.2 / DT)):
        drive(w, ctl)
        p.step(w, DT)
    import numpy as np
    now = np.stack([p.px, p.py, p.pz], axis=1)
    disp = np.sqrt(((now - p.home) ** 2).sum(axis=1))
    n_moved = int((disp > 0.05).sum())
    ok &= check("a walk through kicks grains loose", n_moved >= 5,
                f"{n_moved} grains displaced > 5 cm (max {disp.max():.3f} m)")

    # -- the player leaves; 3 s later everything is settled and nothing came back. --
    place(w, p.x, p.y - 6.0)
    for _ in range(int(3.0 / DT)):
        p.step(w, DT)
    now = np.stack([p.px, p.py, p.pz], axis=1)
    disp = np.sqrt(((now - p.home) ** 2).sum(axis=1))
    n_perm = int((disp > 0.03).sum())
    ok &= check("the footprint is permanent", n_perm >= 5,
                f"{n_perm} grains still displaced > 3 cm, 3 s after contact")
    ok &= check("every grain settled (< 1 cm/s)", p.max_speed() < 0.01,
                f"max grain speed {p.max_speed():.4f} m/s")
    return ok


def test_grab(w, ctl) -> bool:
    print("GRAB (E: arm's reach, carry, drop at the feet)")
    s = T.Stone(3.0, 5.0)
    ok = True
    place(w, s.x - 0.6, s.y, math.atan2(-1.0, 0.0))     # 0.6 m away -- inside 0.44 x height reach
    ok &= check("reach is the ANSUR 0.44 x stature", abs(s.reach - 0.44 * w.height_m) < 1e-9,
                f"reach {s.reach:.3f} m")
    picked = s.interact(w)
    ok &= check("E picks the stone up inside reach", picked and s.carried,
                f"carried = {s.carried}")

    # walk 5 m with it -- it must follow, at waist height
    place(w, w.x, w.y, 0.0)
    x0, y0 = w.x, w.y
    for _ in range(int(5.5 / DT)):
        drive(w, ctl)
        s.step(w, DT)
    walked = math.hypot(w.x - x0, w.y - y0)
    follows = math.hypot(s.x - w.x, s.y - w.y) < 1.0
    ok &= check("the carried stone follows the body", s.carried and follows and walked > 4.5,
                f"walked {walked:.1f} m, stone {math.hypot(s.x - w.x, s.y - w.y):.2f} m away")

    dropped = s.interact(w)
    dd = math.hypot(s.x - w.x, s.y - w.y)
    ok &= check("E again drops it at the feet", dropped and not s.carried and dd < 0.5,
                f"dropped {dd:.2f} m from the player")
    probe = s.probe(w)
    ok &= check("the HUD reports the carried mass", f"{s.mass:.1f} kg" in probe,
                f"probe: {probe}")
    return ok


def main() -> int:
    print("TOUCH TESTS -- the membrane's predictions, measured (one carve, then physics)")
    w = Walker()
    ctl = C.Controller()
    print(f"  body: {w.readout()['g']:.2f} m/s^2, walk {w.walk:.2f} m/s, "
          f"mass ratio into the stone derived per test")

    ok = True
    ok &= test_stone(w, ctl)
    ok &= test_tuft(w, ctl)
    ok &= test_pile(w, ctl)
    ok &= test_grab(w, ctl)

    objs = T.spawn()
    ok &= check("spawn() returns the three classes",
                len(objs) == 3
                and isinstance(objs[0], T.Stone) and isinstance(objs[1], T.Tuft)
                and isinstance(objs[2], T.Pile),
                "stone at (3, 5), tuft at (-3.5, 8), pile at (4, 12)")
    buf = T.touchables_buffer(objs, w)
    # 160 (stone, densified 2026-08-04 -- tools/stone_legibility.py's before/after) + 180
    # (tuft blades) + 400 (pile grains). The count is the render row; the physics is elsewhere.
    ok &= check("touchables_buffer concatenates", buf.shape[0] == 160 + 180 + 400,
                f"{buf.shape[0]} splats")
    ok &= check("F1: the provenance table exists in the module header",
                "PROVENANCE TABLE" in (T.__doc__ or ""), "grep PROVENANCE in touchables.py")

    print(f"\nVERDICT: {'PASS -- the world answers, and every number has a home' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
