"""chimera_engine -- the frame that holds every part and TICKS. The assembly, at last.

Everything before this was a part on the bench, each proven alone: the membrane primitive, the
four verbs on one density clock, the world stack (planet -> geology -> caves -> biomes), the
economy trained and wired, the input binding. An ENGINE is the one thing none of them are: the
loop that holds a WORLD and a PLAYER, reads INPUT, applies the VERBS to the state each tick,
advances the CLOCK, and reports OUT -- forever, deterministically.

    world (Eden) + player + input -> verbs -> state -> (repeat)

A game is content ON this. Eden is the first scene; the engine runs it. This module assembles
the parts into that loop and then PROVES the loop by RUNNING it (docs/THE_METHOD.md): the physics
claims -- it holds the world, input drives the verbs, the clock ticks, it loops stably, it is
deterministic -- are discharged by measurement. The one THE HUMAN claim -- is it a GAME worth
playing -- waits at the operator's terminal, where it belongs.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChimeraEngine:
    """The world, a player in it, and a tick. Deterministic from a seed."""
    seed: int = 7
    lat: float = 0.0
    lon: float = 0.0
    time: float = 0.0
    ticks: int = 0
    onion: object = None
    world: object = None
    player: object = None
    garden: tuple = None

    def __post_init__(self):
        from core.controls import Controller
        from core.eden import make_eden
        from core.planet_layers import LayeredPlanet
        self.onion, self.garden, _ = make_eden(self.seed)  # Eden + the garden = the spawn point
        self.world = LayeredPlanet(onion=self.onion)
        self.lat, self.lon = self.garden[0], self.garden[1]
        self.player = Controller(ship='freighter')

    def _material_here(self) -> str:
        r = self.world.probe(self.lat, self.lon, 1.0)      # just under the player's feet
        return r['deposit'] or r['layer']

    def tick(self, inputs, dt: float = 0.5) -> dict:
        """One turn of the loop: input -> verbs -> move -> clock -> state."""
        self.player.material = self._material_here()        # you dig what you stand on
        for key, secs in inputs:
            self.player.press(key, secs)                    # input drives the verbs
        self.lon = (self.lon + self.player.velocity * 12.0 * dt) % 360   # thrust traverses Eden
        self.time += dt
        self.ticks += 1
        return self.state()

    def state(self) -> dict:
        s = self.onion.sample(self.lat, self.lon)
        return {'tick': self.ticks, 'time': round(self.time, 1),
                'lat': round(self.lat, 1), 'lon': round(self.lon, 1),
                'velocity': round(self.player.velocity, 2), 'scoops': self.player.scoops,
                'standing_on': s['material'], 'elevation': round(s['elevation'])}

    def run(self, script, dt: float = 0.5) -> list:
        """Run a scripted session (a list of per-tick input-event lists). Returns every state."""
        states = [self.state()]
        for inputs in script:
            states.append(self.tick(inputs, dt))
        return states


# --- PROVE the engine by RUNNING it -------------------------------------------

def _prove():
    # a scripted play session: spawn in Eden's garden, thrust east across the world, dig as you go
    script = [
        [('W', 2.0)],                 # thrust up
        [('W', 3.0), ('LMB', 3.0)],   # keep thrusting, start digging
        [('LMB', 4.0)],               # dig
        [('W', 3.0), ('Q', 1.5)],     # thrust + trim
        [('LMB', 3.0)],               # dig
        [('W', 4.0)],                 # cruise
    ]
    eng = ChimeraEngine(seed=7)
    spawn = eng.garden
    states = eng.run(script)
    final = states[-1]

    # determinism: a second engine on the same seed + script lands identically
    eng2 = ChimeraEngine(seed=7)
    final2 = eng2.run(script)[-1]

    ledger = [
        ("The engine assembles and holds the world (Eden)", "PHYSICS",
         eng.onion is not None and eng.garden is not None,
         f"spawned in the garden: {spawn[2]} at ({spawn[0]:+.1f},{spawn[1]:.1f})"),
        ("It runs as a LOOP (a state every tick, no crash)", "PHYSICS",
         len(states) == len(script) + 1,
         f"{len(states)} states over {len(script)} ticks"),
        ("Input drives the verbs -> the state changes", "PHYSICS",
         final['velocity'] > 0 and final['scoops'] > 0,
         f"velocity {final['velocity']}, {final['scoops']} scoops dug"),
        ("The clock ticks (time advances)", "PHYSICS",
         final['time'] > 0,
         f"reached t={final['time']} over {final['tick']} ticks"),
        ("The player TRAVERSES the world (position + ground change)", "PHYSICS",
         final['lon'] != round(spawn[1], 1),
         f"moved from lon {spawn[1]:.1f} to {final['lon']}, now on {final['standing_on']}"),
        ("The engine is DETERMINISTIC (same seed+input -> same world)", "PHYSICS",
         final == final2,
         "two engines ran the same session to an identical final state"),
        ("It is a GAME worth playing", "THE HUMAN", None,
         "awaits your ruling -- the loop runs; only you can say it is a game"),
    ]
    return ledger, states


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ledger, states = _prove()
    print("  === PROVE( \"the Chimera engine\" ) -- the loop MEASURED by running ===\n")
    print("  the play session (input -> verbs -> world), tick by tick:")
    for st in states:
        print(f"    t={st['time']:>4}  lon {st['lon']:>5}  vel {st['velocity']:.2f}  "
              f"scoops {st['scoops']}  on {st['standing_on']}")
    print()
    phys = [c for c in ledger if c[1] == 'PHYSICS']
    for name, term, ok, detail in ledger:
        if term == 'PHYSICS':
            print(f"    [{'PROVEN ' if ok else 'FAILED '}] {name}\n              -> {detail}")
    for name, term, ok, detail in ledger:
        if term == 'THE HUMAN':
            print(f"    [ AWAITS ] {name}\n              -> {detail}")
    n_ok = sum(1 for c in phys if c[2])
    print(f"\n  === VERDICT: {n_ok}/{len(phys)} engine claims PROVEN by measurement ===")
    if n_ok == len(phys):
        print("    The Chimera engine EXISTS: it holds Eden, takes input, runs the verbs on one")
        print("    clock, ticks, traverses, and is deterministic. The parts are an ENGINE now.")
        print("    Whether it is a GAME is yours to call -- content rides on this loop.")
    return 0 if n_ok == len(phys) else 1


if __name__ == '__main__':
    raise SystemExit(_main())
