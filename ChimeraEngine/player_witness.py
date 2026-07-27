"""player_witness.py — SOMETHING STANDS ON A WORLD.

  P1  UP IS LOCAL           upright at the equator, at 45 deg and at the pole -- and those three
                            "ups" differ by exactly the angles between the places
  P2  IT STANDS             dropped onto a sphere at four latitudes, it settles at the same
                            altitude every time, upright in its OWN local frame
  P3  IT TOPPLES            a hard shove puts it down, a light one does not -- on a SPHERE, where
                            there is no global up to cheat with
  P4  SKIN TEMPERATURE      the suit warms in sunlight and cools past the terminator, from the
                            light field alone -- crossing the terminator is survivable because a
                            body has thermal inertia, and that is a number, not a rule
  P5  THE SENSED REGISTER   one call returns every field, and the readings CHANGE with position
  P6  A DIFFERENT WORLD     Earth / Moon / asteroid: weight, jump height and breathability all
                            move, and nothing was re-authored to make them

Run:  python ChimeraEngine/player_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fields import Star                                                          # noqa: E402
from player import Player, World                                                 # noqa: E402

np.set_printoptions(precision=4, suppress=True)
AU = 1.496e11
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def settle(pl: Player, seconds=1.2, dt=2e-4, extra=None):
    for _ in range(int(seconds / dt)):
        pl.step(dt, extra_forces=extra() if callable(extra) else extra)
    return pl


def main() -> int:
    print("\nWITNESS: a player standing on a world\n" + "=" * 70)
    sun = Star.from_irradiance(center=(0, 0, 0), at_distance=AU, irradiance=1361.0,
                               radius=6.957e8)
    earth = World.earth_like(sun, center=(AU, 0, 0))

    # ── P1 ───────────────────────────────────────────────────────────────────────────────────
    print("\nP1  UP IS LOCAL -- there is no global upright on a sphere")
    ups = {}
    for lat in (0.0, 45.0, 90.0):
        pl = Player.build(earth, lat_deg=lat, lon_deg=0.0)
        ups[lat] = pl.up()
        print(f"      lat {lat:5.1f} deg -> up {np.round(pl.up(), 4)}   tilt from local up "
              f"{pl.tilt_deg():.4f} deg   altitude {pl.altitude():.3f} m")
    ang = lambda a, b: np.degrees(np.arccos(np.clip(float(np.dot(ups[a], ups[b])), -1, 1)))
    print(f"      angle between ups: 0-45 = {ang(0.0,45.0):.2f} deg, 0-90 = {ang(0.0,90.0):.2f}, "
          f"45-90 = {ang(45.0,90.0):.2f}")
    check("up rotates with latitude, by exactly the latitude",
          abs(ang(0.0, 45.0) - 45.0) < 0.01 and abs(ang(0.0, 90.0) - 90.0) < 0.01,
          f"{ang(0.0,45.0):.2f} deg and {ang(0.0,90.0):.2f} deg -- nothing stores an up, it is "
          "derived from the pull wherever you are standing")

    # ── P2 ───────────────────────────────────────────────────────────────────────────────────
    print("\nP2  IT STANDS -- dropped onto the sphere at four latitudes")
    alts, tilts = [], []
    for lat in (0.0, 30.0, 60.0, 89.0):
        pl = Player.build(earth, lat_deg=lat, lon_deg=17.0, altitude=0.15)
        settle(pl, seconds=1.2)
        alts.append(pl.altitude()); tilts.append(pl.tilt_deg())
        s = pl.sense()
        print(f"      lat {lat:5.1f} -> rests at {pl.altitude():6.3f} m, tilt {pl.tilt_deg():6.3f} deg, "
              f"{s['contact']['feet_down']} pads down, load {s['contact']['load_N']:6.1f} N "
              f"(weight {s['gravity']['weight_N']:.1f})")
    spread = max(alts) - min(alts)
    check("it settles the same way everywhere on the sphere",
          spread < 2e-3 and max(tilts) < 0.5,
          f"resting altitude varies by {spread*1000:.2f} mm across 89 degrees of latitude, worst "
          f"tilt {max(tilts):.3f} deg -- one contact rule, no flat-ground special case")

    # ── P3 ───────────────────────────────────────────────────────────────────────────────────
    print("\nP3  IT TOPPLES -- shoved in the LOCAL tangent plane")
    for push in (60.0, 150.0, 400.0):
        pl = Player.build(earth, lat_deg=20.0, lon_deg=0.0)
        settle(pl, seconds=0.4)
        east, north, up = pl.local_frame()
        peak = 0.0
        dt = 2e-4
        for k in range(int(2.2 / dt)):
            ex = None
            if 2000 <= k < 4500:                     # a half-second shove at chest height
                ex = [(-1, pl.body.base_pos + up * 0.22, east * push)]
            pl.step(dt, extra_forces=ex)
            peak = max(peak, pl.tilt_deg())
        print(f"      push {push:5.0f} N -> peak tilt {peak:6.2f} deg, final {pl.tilt_deg():6.2f} deg"
              f"{'   <-- DOWN' if pl.tilt_deg() > 45 else ''}")
        if push == 60.0:
            light_final = pl.tilt_deg()
        if push == 400.0:
            hard_final = pl.tilt_deg()
    check("a hard shove puts it down, a light one does not",
          light_final < 10.0 and hard_final > 45.0,
          f"60 N leaves it {light_final:.1f} deg from local up, 400 N leaves it {hard_final:.0f} deg "
          "-- and 'down' here means away from the planet's centre, not away from world +Z")

    # ── P4 ───────────────────────────────────────────────────────────────────────────────────
    print("\nP4  SKIN TEMPERATURE across a terminator -- on an airless world")
    moon = World.moon_like(sun, center=(AU, 0, 0))
    # ASK the world which way the sun is. I hard-coded lon 0 as "sub-solar", which is backwards --
    # the star is at the origin and the world is at +x, so the sunward face is lon 180. The witness
    # then confidently reported a suit warming in the dark. Derive it, and ASSERT it.
    lon_day = moon.sunlit_longitude(0.0)
    lon_night = (lon_day + 180.0) % 360.0
    print(f"      sunward longitude derived from the light field: {lon_day:.0f} deg "
          f"(antipode {lon_night:.0f})")
    assert moon.is_sunlit(moon.surface_point(0.0, lon_day, 1.0)), "the 'day' point must be lit"
    assert not moon.is_sunlit(moon.surface_point(0.0, lon_night, 1.0)), "the 'night' point must be dark"
    pl = Player.build(moon, lat_deg=0.0, lon_deg=lon_day)     # sub-solar point: full sun
    pl.skin_T = 293.15
    day_T = [pl.step_thermal(60.0) for _ in range(180)][-1]   # 3 hours in the sun
    night = Player.build(moon, lat_deg=0.0, lon_deg=lon_night)   # the far side: no sun at all
    night.skin_T = day_T
    cool = [night.step_thermal(60.0) for _ in range(180)]
    print(f"      sub-solar,  3 h in sunlight -> skin {day_T-273.15:+7.2f} C")
    print(f"      antipode,   3 h in shadow   -> skin {cool[-1]-273.15:+7.2f} C "
          f"(after 1 h {cool[59]-273.15:+.2f})")
    print(f"      ground under the boots: {moon.ground_temperature_at(pl.position()):.1f} K sunlit, "
          f"{moon.ground_temperature_at(night.position()):.1f} K in shadow")
    check("the suit warms in sun and cools in shadow, and does neither instantly",
          day_T > 350.0 and cool[-1] < day_T - 50.0 and cool[-1] > 180.0,
          f"{day_T-273.15:+.1f} C sunlit -> {cool[-1]-273.15:+.1f} C after 3 h of night. Crossing a "
          "terminator is survivable because a body has thermal INERTIA -- a number, not a rule")

    # ── P5 ───────────────────────────────────────────────────────────────────────────────────
    print("\nP5  THE SENSED REGISTER: one call, every field, and it changes with WHERE you are")
    lon_d = earth.sunlit_longitude(0.0)                      # derived, never assumed
    noon = Player.build(earth, lat_deg=0.0, lon_deg=lon_d)
    dark = Player.build(earth, lat_deg=0.0, lon_deg=(lon_d + 180.0) % 360.0)
    settle(noon, seconds=0.3); settle(dark, seconds=0.3)
    sn, sd = noon.sense(), dark.sense()
    for k in ('gravity', 'contact', 'light', 'thermal', 'atmospheric', 'inertial'):
        fmt = lambda d: {kk: (round(vv, 2) if isinstance(vv, float) else vv)
                         for kk, vv in d.items() if kk != 'up'}
        print(f"      {k:14s} day  {fmt(sn[k])}")
        print(f"      {'':14s} night {fmt(sd[k])}")
    print(f"      HONEST GAP: {sn['thermal']['ground_K']:.0f} K day vs "
          f"{sd['thermal']['ground_K']:.0f} K night is BARE-ROCK equilibrium. The real Earth swings")
    print(f"      only ~10-20 K, because A6 measured its air column at 1.04e7 J/m^2/K -- 4.8 m of")
    print(f"      rock equivalent -- and the oceans add far more. Damping that needs the transient")
    print(f"      Column per point, not a constant. The LAW is right; the reservoir is not wired in.")
    check("the same call reads differently on the day and night sides",
          sn['light']['is_day'] and not sd['light']['is_day']
          and sn['thermal']['ground_K'] > sd['thermal']['ground_K'] + 50
          and sd['thermal']['ground_K'] > 0.0
          and sn['contact']['grounded'] and sd['contact']['grounded'],
          f"day irradiance {sn['light']['irradiance']:.0f} W/m^2 and ground "
          f"{sn['thermal']['ground_K']:.0f} K vs night {sd['light']['irradiance']:.0f} and "
          f"{sd['thermal']['ground_K']:.0f} K -- and both are standing on the same planet")

    # ── P6 ───────────────────────────────────────────────────────────────────────────────────
    print("\nP6  A DIFFERENT WORLD -- nothing re-authored, only the membrane changed")
    rock = World.asteroid(sun, center=(AU, 0, 0), radius=500.0, g=0.0028)
    rows = []
    for w in (earth, moon, rock):
        pl = Player.build(w, lat_deg=10.0, lon_deg=0.0)
        s = pl.sense()
        g = s['gravity']['strength']
        # a 2.5 m/s push-off: how high, and how long you hang there
        jump = 2.5 ** 2 / (2 * g)
        hang = 2 * 2.5 / g
        esc = w.gravity().escape_speed(w.radius)
        rows.append((w.name, g, s['gravity']['weight_N'], jump, hang, esc,
                     s['atmospheric']['breathable']))
        print(f"      {w.name:8s} g {g:7.4f} m/s^2   weight {s['gravity']['weight_N']:8.2f} N   "
              f"jump {jump:8.2f} m   hang {hang:7.1f} s   escape {esc:8.1f} m/s   "
              f"breathable {s['atmospheric']['breathable']}")
    print(f"      on the asteroid a 2.5 m/s hop EXCEEDS escape velocity ({rows[2][5]:.2f} m/s) --")
    print(f"      you would jump off the world, and nobody wrote that rule")
    check("one body, three worlds, and the numbers all move together",
          rows[0][1] > rows[1][1] > rows[2][1] and rows[2][3] > 100 * rows[0][3]
          and rows[0][6] and not rows[1][6] and 2.5 > rows[2][5],
          f"g {rows[0][1]:.3f} / {rows[1][1]:.3f} / {rows[2][1]:.4f} m/s^2; jump "
          f"{rows[0][3]:.2f} m / {rows[1][3]:.2f} m / {rows[2][3]:.0f} m; only Earth breathable "
          "-- every one of those is a consequence of the membrane, not a difficulty setting")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 70)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    if not n_fail:
        print("\nHONEST SCOPE: it stands, leans, senses and topples. It does NOT walk -- that is a")
        print("CONTROLLER problem (nervous.py has the machinery), and a gait must be TRAINED")
        print("against this morphology and this gravity, scored from N randomized starts.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
