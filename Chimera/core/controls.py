"""controls — the last mile: a keystroke drives a verb's dial.

Everything below this was buildable without an engine: verbs, clocks, geology, economy. This is
the ONE place the outside world touches the game -- and it is the floor the operator identified:
reading the physical key from the OS/hardware is programmed ONCE, per platform (SDL, pygame, the
browser, Unreal), reused by every game, and NOT trainable. That read is the engine's; this
module is the two pieces that ARE the game's:

  THE BINDING   key -> verb. A table (W -> thrust, LMB -> dig, Q -> trim). Data, not code --
                a player can rebind it. Below.
  THE DRIVER    a Controller that takes input EVENTS (key, seconds-held) and advances the bound
                verb's dial at that verb's clock, accumulating persistent state (velocity across
                many taps, scoops across many holds, trim toward balance).

Feed it real events from the engine and it is a live control scheme; feed it a script (as the
demo does) and it is reproducible and testable. Input -> binding -> verb -> density clock ->
world state, end to end. grow is NOT here: it is driven by the flow of energy, not a key.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core import balance as _balance
from core import dig as _dig
from core import thrust as _thrust

# THE BINDING: key -> verb. Data. A player rebinds this; the game does not care which key.
BINDINGS = {
    'W': 'thrust',       # hold to accelerate
    'LMB': 'dig',        # hold to dig a scoop
    'Q': 'trim',         # tap/hold to trim the centre of thrust toward centre of mass
}
TRIM_RATE = 1.0          # metres of offset corrected per second of trim


@dataclass
class Controller:
    """The player's live state, driven by input events. Persistent across presses."""
    ship: str = 'freighter'          # what you fly (sets the thrust clock)
    material: str = 'bedrock'        # what you dig (sets the dig clock)
    velocity: float = 0.0            # thrust dial, accumulated 0..1
    dig_dial: float = 0.0            # current scoop progress 0..1
    scoops: int = 0                  # completed scoops
    offset: float = 2.0              # balance: CoT-CoM offset (starts imbalanced)
    log: list = field(default_factory=list)

    def press(self, key: str, seconds: float) -> dict:
        """Process one input event: hold `key` for `seconds`. Advances the bound verb's dial at
        that verb's OWN clock, and returns what changed."""
        verb = BINDINGS.get(key)
        if verb == 'thrust':
            rate = _thrust.thrust_rate(_thrust.ship_membrane(self.ship))     # dial/sec = 1/√mass
            self.velocity = min(self.velocity + rate * seconds, 1.0)
            ev = f"W {seconds:.1f}s -> velocity {self.velocity:.2f}"
        elif verb == 'dig':
            rate = _dig.dig_rate(_dig.scoop_membrane(self.material))          # dial/sec = 1/√density
            self.dig_dial += rate * seconds
            done = 0
            while self.dig_dial >= 1.0:
                self.dig_dial -= 1.0
                self.scoops += 1
                done += 1
            ev = (f"LMB {seconds:.1f}s -> dig {self.dig_dial:.2f}"
                  + (f", +{done} scoop of {self.material}" if done else ""))
        elif verb == 'trim':
            self.offset = max(0.0, self.offset - TRIM_RATE * seconds)
            tau = _balance.torque(1.0, self.offset)
            ev = f"Q {seconds:.1f}s -> offset {self.offset:.2f} m, torque {tau:.2f}"
        else:
            ev = f"{key}: unbound"
        self.log.append(ev)
        return {'event': ev, 'velocity': self.velocity, 'dig_dial': self.dig_dial,
                'scoops': self.scoops, 'offset': self.offset}

    def state(self) -> dict:
        stable = self.offset < 1e-6
        return {'ship': self.ship, 'velocity': round(self.velocity, 3),
                'scoops': self.scoops, 'dig_dial': round(self.dig_dial, 3),
                'offset_m': round(self.offset, 3), 'stable': stable}


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    print("  === the binding: key -> verb (data; the player rebinds it) ===")
    for k, v in BINDINGS.items():
        print(f"    {k:4} -> {v}")
    print("    (grow is not bound to a key -- it runs on the flow of energy, not input)")

    print("\n  === the driver: a SCRIPT of input events drives the verbs (engine feeds real ones) ===")
    c = Controller(ship='freighter', material='bedrock')
    script = [('W', 2.0), ('LMB', 3.0), ('Q', 0.8), ('W', 3.0), ('LMB', 4.0),
              ('Q', 1.2), ('W', 4.0), ('LMB', 2.5)]
    for key, secs in script:
        r = c.press(key, secs)
        print(f"    {r['event']}")

    s = c.state()
    print(f"\n  === final state ===")
    print(f"    flying a {s['ship']}: velocity {s['velocity']} of full burn")
    print(f"    dug {s['scoops']} scoops of bedrock (current scoop {s['dig_dial']})")
    print(f"    trim: offset {s['offset_m']} m -> {'STABLE' if s['stable'] else 'still torquing'}")
    print("\n    keystroke -> binding -> verb -> density clock -> world state. The last mile is the")
    print("    binding + the driver (game logic); reading the key is the engine's floor, once per")
    print("    platform. Everything else -- clocks, geology, economy -- was already here.")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
