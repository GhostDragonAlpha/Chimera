"""thrust — the THRUST verb, on the same relative-mass clock as dig.

The dig verb's twin, and the point is that it is the SAME construct with the density term
pointed at motion instead of material:

  IT IS A VERB          a membranes.Verb -- two states (at_rest, full_burn) + a dial that INPUT
                        drives (the throttle). You exhibit the two ends; the world computes the
                        spin-up between them.
  ITS CLOCK IS MASS     a ship membrane is MADE OF a mass and carries its relative mass as its
                        density, so ship.clock_rate() = sqrt(relative mass) -- the SAME clock the
                        membrane and the dig verb use. A ship on its controls answers the helm
                        like a mass on a spring, whose natural frequency is omega = sqrt(k/m), so
                        its response rate goes as 1/sqrt(mass): a light scout snaps to full burn,
                        a capital ship lumbers up to it. thrust_rate = power / ship.clock_rate().
  RELATIVE MASS         is relative scale is density -- one term (the operator's identity). A
                        scout is the reference (1); a hauler is 40x, so it answers sqrt(40) ~ 6.3x
                        slower. Read from OUTSIDE, relative to the reference.

Honest note on the physics: the STEADY-STATE acceleration under a fixed thrust is a = F/m --
LINEAR in mass (Newton). The sqrt(m) clock here is the RESPONSE / manoeuvre frequency (how fast
the ship answers the throttle), which is the spring-mass result and the same clock the rest of
the system runs on. Both are true and both are reported; the CLOCK is the responsiveness one.
"""
from __future__ import annotations

import numpy as np

from core.membranes import Membrane

# Ship masses RELATIVE to the reference scout (dimensionless -- relative mass = relative scale =
# density, the operator's one term). Read from outside, root at the lightest hull.
REF_SHIP = 'scout'
SHIP_MASS = {
    'scout': 1.0, 'shuttle': 3.0, 'fighter': 2.0, 'freighter': 12.0, 'hauler': 40.0,
    'capital': 200.0,
}
BASE_SPINUP_SECONDS = 2.0        # time for the reference scout to reach full burn at power 1


def relative_mass(mass_class: str) -> float:
    return SHIP_MASS.get(mass_class, 1.0)


def ship_membrane(mass_class: str, scale: float = 20.0) -> Membrane:
    """A ship membrane MADE OF a mass class, carrying its relative mass as density so that
    ship.clock_rate() is the relative-mass clock -- and a thrust verb on it (at_rest -> full_burn)."""
    m = Membrane(mass_class, scale=scale, serial=f'SHIP-{mass_class}')
    m.prop(density=relative_mass(mass_class), mass_class=mass_class)
    m.state('at_rest', velocity=0.0, throttle=0.0, thrust=0.0)
    m.state('full_burn', velocity=1.0, throttle=1.0, thrust=1.0)
    m.verb('thrust', 'at_rest', 'full_burn')
    return m


def thrust_rate(ship: Membrane, power: float = 1.0) -> float:
    """Dial advance per second: power / clock_rate. Uses the membrane's OWN clock_rate()
    (= sqrt(relative mass)) -- the same clock as dig, inverted because a heavier hull answers
    the helm slower. Light = fast, heavy = slow."""
    return power / (ship.clock_rate() * BASE_SPINUP_SECONDS)


def hold(mass_class: str, seconds: float, power: float = 1.0) -> dict:
    """Simulate holding the throttle for `seconds` on a ship of `mass_class`. Returns how far the
    thrust dial got (velocity as a fraction of full burn), the time to reach full, and -- for
    honesty -- the steady-state F/m acceleration alongside the sqrt(m) response clock."""
    ship = ship_membrane(mass_class)
    rate = thrust_rate(ship, power)                    # dial per second
    dial = float(min(rate * seconds, 1.0))
    return {
        'mass_class': mass_class,
        'relative_mass': relative_mass(mass_class),
        'clock_rate': ship.clock_rate(),               # sqrt(relative mass) -- the membrane's own
        'seconds_to_full_burn': BASE_SPINUP_SECONDS * ship.clock_rate() / max(power, 1e-9),
        'dial': dial,
        'velocity_frac': dial,
        'steady_accel_rel': power / relative_mass(mass_class),   # a = F/m, LINEAR (Newton)
        'verb_state_at_dial': ship.apply('thrust', dial),
    }


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='the thrust verb on the relative-mass clock')
    ap.add_argument('--seconds', type=float, default=3.0)
    a = ap.parse_args()

    print("  === the thrust verb: two states + a dial (membranes.Verb) ===")
    s = ship_membrane('freighter')
    print(f"    verb 'thrust' moves: {s.verbs['thrust'].differs_in()}   lo=at_rest hi=full_burn")
    for t in (0.0, 0.5, 1.0):
        st = s.apply('thrust', t)
        print(f"    throttle {t:>3} -> velocity {st['velocity']:.2f} thrust {st['thrust']:.2f}")

    print(f"\n  === same relative-mass clock as dig: hold the throttle {a.seconds:.0f}s on each hull ===")
    print(f"  {'ship':10} {'rel.mass':>9} {'clock=√m':>9} {'s to full':>10} "
          f"{'vel after '+str(int(a.seconds))+'s':>13} {'a=F/m':>7}")
    for ship in ('scout', 'fighter', 'shuttle', 'freighter', 'hauler', 'capital'):
        h = hold(ship, a.seconds)
        print(f"    {ship:10} {h['relative_mass']:>9.0f} {h['clock_rate']:>9.2f} "
              f"{h['seconds_to_full_burn']:>10.1f} {h['velocity_frac']:>12.2f} "
              f"{h['steady_accel_rel']:>7.3f}")
    print("    ^ the light scout snaps to full burn; the capital lumbers -- the √(relative mass)")
    print("      clock (responsiveness). a=F/m is the linear steady-state, shown for honesty.")
    print("\n    dig and thrust are ONE verb pattern on ONE clock: density = relative mass =")
    print("    relative scale, pointed at material (dig) or at motion (thrust).")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
