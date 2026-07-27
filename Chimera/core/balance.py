"""balance — the BALANCE verb: centre-of-mass vs centre-of-thrust, on the same clock.

Thrust's rotational partner, and the third proof that one clock runs everything. When the line
of thrust does not pass through the centre of mass, the offset is a LEVER: torque = thrust x
offset, and the ship tips. BALANCE is the verb that trims it -- shift ballast or gimbal the
thruster until the centre of thrust lines up with the centre of mass and the torque goes to
zero.

  IT IS A VERB          a membranes.Verb -- two states (toppling, trimmed) + a dial the player's
                        trim input drives. Toppling = offset lever, max torque; trimmed = aligned,
                        zero torque. The between is derived.
  ITS CLOCK IS INERTIA  how fast the ship tips (or rights itself) runs on the SAME relative-mass
                        clock as dig and thrust -- but rotationally, where the "mass" is the
                        MOMENT OF INERTIA I ~ m*r^2. A rig membrane carries its relative inertia
                        as density, so rig.clock_rate() = sqrt(relative inertia): a heavy or wide
                        hull tips slowly and rights slowly; a small light one snaps. For same-size
                        hulls relative inertia = relative mass, so it is literally the thrust clock
                        turned on its side.
  CoM vs CoT            torque = thrust x (centre_of_thrust - centre_of_mass). Zero offset = no
                        torque = stable. This is the operator's "adjusting Center of Gravity vs
                        Center of Thrust to stabilize torque", made a verb.

density = relative mass = relative scale = (here) relative inertia -- one term, pointed now at
rotation. Dig, thrust, balance: three mechanics, one clock.
"""
from __future__ import annotations

import math

import numpy as np

from core.membranes import Membrane
from core.thrust import relative_mass

REF_RADIUS = 10.0                # m, the reference hull's size (sets the moment of inertia)


def relative_inertia(mass_class: str, radius: float = REF_RADIUS) -> float:
    """Moment of inertia relative to the reference hull: I ~ m*r^2. Relative mass AND relative
    size both feed it -- the density term, now rotational. Same-size hulls: = relative mass."""
    return relative_mass(mass_class) * (radius / REF_RADIUS) ** 2


def rig_membrane(mass_class: str, radius: float = REF_RADIUS) -> Membrane:
    """A ship's rotational rig, MADE OF its relative inertia (carried as density) so that
    rig.clock_rate() is the rotational relative-mass clock -- and a balance verb on it."""
    m = Membrane(f'rig-{mass_class}', scale=radius, serial=f'RIG-{mass_class}')
    m.prop(density=relative_inertia(mass_class, radius), mass_class=mass_class, radius=radius)
    m.state('toppling', torque=1.0, tip_rate=1.0, offset=1.0)
    m.state('trimmed', torque=0.0, tip_rate=0.0, offset=0.0)
    m.verb('balance', 'toppling', 'trimmed')       # the ACTION runs toppling -> trimmed (you correct it)
    return m


def torque(thrust: float, offset_m: float) -> float:
    """The lever: thrust force times the centre-of-thrust / centre-of-mass offset."""
    return thrust * offset_m


def stability(mass_class: str, thrust: float, offset_m: float, radius: float = REF_RADIUS) -> dict:
    """Given a hull, a thrust, and a CoT-CoM offset: the torque, the angular response, how long
    until it topples 90 degrees, and the rotational clock (sqrt relative inertia)."""
    rig = rig_membrane(mass_class, radius)
    I = relative_inertia(mass_class, radius)
    tau = torque(thrust, offset_m)
    alpha = tau / max(I, 1e-9)                      # angular acceleration (relative units)
    t_topple = math.sqrt(2 * (math.pi / 2) / alpha) if alpha > 1e-9 else float('inf')
    return {
        'mass_class': mass_class, 'offset_m': offset_m, 'thrust': thrust,
        'relative_inertia': I,
        'clock_rate': rig.clock_rate(),             # sqrt(relative inertia) -- the membrane's own
        'torque': tau,
        'angular_accel': alpha,
        'seconds_to_topple': t_topple,
        'stable': offset_m < 1e-6,
    }


def trim(mass_class: str, thrust: float, offset_m: float, dial: float,
         radius: float = REF_RADIUS) -> dict:
    """The BALANCE action: the trim dial runs from toppling (full offset) to trimmed (aligned).
    dial=0 leaves the offset; dial=1 zeroes it. Torque follows -- this is the player stabilising."""
    rig = rig_membrane(mass_class, radius)
    residual_offset = offset_m * (1.0 - float(np.clip(dial, 0.0, 1.0)))
    st = rig.apply('balance', float(np.clip(dial, 0.0, 1.0)))     # verb state at the trim dial
    return {'dial': dial, 'residual_offset_m': residual_offset,
            'torque': torque(thrust, residual_offset),
            'verb_state': st, **{k: stability(mass_class, thrust, residual_offset, radius)[k]
                                 for k in ('seconds_to_topple', 'stable')}}


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='the balance verb: CoM vs CoT on the inertia clock')
    ap.add_argument('--thrust', type=float, default=1.0)
    a = ap.parse_args()

    print("  === the balance verb: two states + a dial (membranes.Verb) ===")
    rig = rig_membrane('freighter')
    print(f"    verb 'balance' moves: {rig.verbs['balance'].differs_in()}   lo=toppling hi=trimmed")
    for t in (0.0, 0.5, 1.0):
        st = rig.apply('balance', t)
        print(f"    trim {t:>3} -> torque {st['torque']:.2f} offset {st['offset']:.2f}")

    print(f"\n  === CoM vs CoT: an offset is a lever -> torque -> the ship tips ===")
    print(f"  {'offset (m)':>10} {'torque':>8} {'ang.accel':>10} {'s to topple':>12}")
    for off in (0.0, 0.25, 1.0, 3.0):
        s = stability('freighter', a.thrust, off)
        tt = 'stable' if s['seconds_to_topple'] == float('inf') else f"{s['seconds_to_topple']:.1f}s"
        print(f"  {off:>10.2f} {s['torque']:>8.2f} {s['angular_accel']:>10.3f} {tt:>12}")

    print("\n  === the inertia clock: same offset, heavier/wider hull tips SLOWER ===")
    print(f"  {'hull':10} {'rel.inertia':>11} {'clock=√I':>9} {'s to topple @off=1m':>20}")
    for ship in ('scout', 'shuttle', 'freighter', 'hauler', 'capital'):
        s = stability(ship, a.thrust, 1.0)
        print(f"    {ship:10} {s['relative_inertia']:>11.0f} {s['clock_rate']:>9.2f} "
              f"{s['seconds_to_topple']:>18.1f}s")
    print("    ^ the rotational relative-mass clock -- the thrust clock turned on its side")

    print("\n  === BALANCE the verb: trim the offset -> torque falls -> stable ===")
    for dial in (0.0, 0.5, 0.9, 1.0):
        r = trim('freighter', a.thrust, 2.0, dial)
        tt = 'STABLE' if r['stable'] else f"topples in {r['seconds_to_topple']:.1f}s"
        print(f"    trim dial {dial:>3} -> residual offset {r['residual_offset_m']:.2f} m, "
              f"torque {r['torque']:.2f} -> {tt}")
    print("\n    dig | thrust | balance -- three verbs, one clock (density = relative mass =")
    print("    relative scale = relative inertia), pointed at material, motion, and rotation.")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
