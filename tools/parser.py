"""parser.py -- THE PHASE D PARSER: intent -> program, a grammar over button state.

Membrane: docs/THE_PARSER.md (stated 2026-08-04, before this build). Design:
docs/CONTROLLER_MAP.md (~12 verbs, two binding surfaces, ONE formula layer) and
docs/THE_COMPILER.md layer 4 (the parser is built LAST because it cannot be wrong
in an interesting way).

THE GRAMMAR IS THREE DATA TABLES AND ONE RULE:

    1. BINDING    physical input -> verb. DATA, written twice (keyboard+mouse
                  PRIMARY, gamepad port). Never code.
    2. STATE      verb -> ButtonState(held, value). The button is a fact.
    3. FORMULAS   verb -> Formula. ONE layer, input-agnostic: a Formula sees
                  (obs, button value) and returns a command. A verb with no
                  trained formula is REGISTERED ANYWAY and REFUSES BY NAME --
                  the derive_ligaments discipline: a refusal with a reason,
                  never a silent zero.
    4. COMPOSITION formulas declare EXCLUSIVE or OVERLAY. Overlays add onto the
                  exclusive driver's command. Two exclusive verbs held at once:
                  registration order wins AND the conflict is named in the trace.

The parser is v2: the stand port is the only trained formula, so the registry
ships `stand` live and every other verb as a named refusal pointing at its
milestone. Programs ARRIVE at the registry as the atoms are trained (M3's
STEP+PLANT+BALANCE -> MOVE, M8's REACH+GRIP+BRACE -> GRAB); this file does not
change when they do. That is the point of building it last.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# -- 1. THE VERBS (the controller map's compression, named once, ordered) ---------------------
VERBS = ("MOVE", "SPRINT", "LOOK", "JUMP", "CROUCH", "GRAB",
         "ACTION", "AIM", "USE", "LHAND", "RHAND", "STANCE")

# -- 2. THE BINDINGS, AS DATA, TWICE ----------------------------------------------------------
# physical input name -> verb. Analog channels (stick axes, mouse) bind the verb whole;
# the VALUE travels in the ButtonState, not in this table.
BIND_KEYBOARD = {
    "W": "MOVE", "A": "MOVE", "S": "MOVE", "D": "MOVE",
    "Shift": "SPRINT",
    "Mouse": "LOOK",
    "Space": "JUMP",
    "Ctrl": "CROUCH", "C": "CROUCH",
    "E": "GRAB",
    "MouseL": "ACTION",
    "MouseR": "AIM",
    "R": "USE",
    "Q": "LHAND",
    "F": "RHAND",
    "Wheel": "STANCE", "1": "STANCE", "2": "STANCE", "3": "STANCE",
    "4": "STANCE", "5": "STANCE", "6": "STANCE", "7": "STANCE",
    "8": "STANCE", "9": "STANCE",
}

BIND_GAMEPAD = {
    "LStick": "MOVE",
    "L3": "SPRINT",
    "RStick": "LOOK",
    "A": "JUMP",
    "B": "CROUCH",
    "X": "GRAB",
    "RT": "ACTION",
    "LT": "AIM",
    "Y": "USE",
    "LB": "LHAND",
    "RB": "RHAND",
    "DPad": "STANCE",
}


# -- 3. BUTTON STATE ---------------------------------------------------------------------------
@dataclass
class ButtonState:
    held: bool = False
    value: float = 1.0                 # analog magnitude; 1.0 for a binary button


# -- 4. THE FORMULA LAYER -----------------------------------------------------------------------
EXCLUSIVE = "EXCLUSIVE"                # one driver at a time (stand, move, crouch...)
OVERLAY = "OVERLAY"                    # adds onto the driver (jump mid-walk, per the map)


class Formula:
    """One verb's program. command(obs, value) -> control vector, or None for no drive."""

    def __init__(self, verb, fn, kind=EXCLUSIVE):
        self.verb = verb
        self.fn = fn
        self.kind = kind

    def command(self, obs, value):
        return self.fn(obs, value)


@dataclass
class Refusal:
    """A verb whose formula is not trained yet. It is REGISTERED -- the grammar sees the
    whole controller map -- and it REFUSES BY NAME. Never a silent zero."""
    verb: str
    reason: str


class ParseTrace:
    """Every parse leaves a trace: who drove, who was queued, who refused, what conflicted.
    The parser cannot be wrong in an interesting way, so its honesty is a printed record."""
    def __init__(self):
        self.driver = None             # the exclusive formula that drove (verb name)
        self.overlays = []             # overlay verbs that added
        self.refused = []              # [(verb, reason)] held but unimplemented
        self.conflicts = []            # [(winner, loser)] exclusive conflicts, named


class Parser:
    """The grammar, instantiated. `formulas`: {verb: Formula | Refusal}, in registration
    order -- the order is the stated conflict rule, so it is part of the contract."""

    def __init__(self, formulas, binding=BIND_KEYBOARD):
        self.formulas = dict(formulas)
        self.binding = binding
        # a button exists for every verb of the map AND every registered formula
        # (STAND is registered but is not a map button -- in-game BALANCE is
        # always-on; the harness drives it as a button to prove the path)
        self.state = {v: ButtonState() for v in VERBS}
        for verb in self.formulas:
            self.state.setdefault(verb, ButtonState())

    # -- physical level: inputs arrive as physical names, the binding resolves them --
    def set_physical(self, physical_name, held, value=1.0):
        verb = self.binding.get(physical_name)
        if verb is None:
            return None                            # an unbound physical input is not an error
        self.state[verb] = ButtonState(held, value)
        return verb

    # -- verb level: a harness (f3_stand's phases) or a headless test drives verbs directly --
    def set_verb(self, verb, held, value=1.0):
        if verb not in self.state:
            raise KeyError(f"{verb} is not a verb of the controller map -- "
                           f"the grammar refuses what it cannot name (the verbs are {VERBS})")
        self.state[verb] = ButtonState(held, value)

    def command(self, obs):
        """ONE parse: read the held verbs, pick the driver, add the overlays, name the rest.
        Returns (u, trace): the control vector (None = no drive, the runtime holds its last)
        and the trace. An unheld world parses to (None, empty trace) -- the body slumps,
        which is exactly what f3_stand's phase 2 tests."""
        import numpy as np
        tr = ParseTrace()
        u = None
        for verb, entry in self.formulas.items():
            st = self.state.get(verb, ButtonState())
            if not st.held:
                continue
            if isinstance(entry, Refusal):
                tr.refused.append((verb, entry.reason))
                continue
            if entry.kind == OVERLAY:
                add = entry.command(obs, st.value)
                if add is not None:
                    u = add if u is None else u + add
                    tr.overlays.append(verb)
                continue
            # EXCLUSIVE: registration order wins; the conflict is NAMED
            if tr.driver is None:
                u = entry.command(obs, st.value)
                tr.driver = verb
            else:
                tr.conflicts.append((tr.driver, verb))
        return u, tr


def stand_formula_fn(theta, tgt, nu):
    """The stand port AS A FORMULA REGISTRATION -- the same function v1 bound inline
    (`tools/f3_stand.py`'s stand_formula), moved here so the button's content lives in
    the layer, not in the harness. Bit-identical by construction, and parser_tests
    MEASURES the identity rather than trusting this sentence.

    THE ROLL TERM, 2026-08-04. Until today this formula fed back HEIGHT and PITCH only,
    and the body fell over sideways at 7.6 s -- MEASURED, by watching the fall instead of
    theorising about it: CoM-y ran to -812 mm while CoM-x never exceeded 52 mm, and pitch
    stayed stable at -16 deg for the first 5.5 s. The sagittal plane was controlled and the
    frontal plane had no sense at all, on a body whose own port docstring says "ONE centre
    of mass is carried by TWO hips 0.162 m apart". A 3-D inverted pendulum has two lean
    angles; this formula fed back one.

    IT HAD TO BE TRAINED IN, NOT ADDED ON, and that is a measured result rather than a
    preference. Bolting roll gains onto the frozen theta does NOT work -- searched two ways
    (290 whole-body gains, then 2 gains on the 44 measured hip-abductor/subtalar muscles)
    and BOTH searches converged to ZERO gain, every nonzero value being up to 4x worse. The
    frozen policy was holding a fragile lateral configuration by accident, and any
    perturbation destroyed the accident. Searching a0/kh/kp/kr TOGETHER:

        held 7.60 -> 9.08 s | CoM peak 1.65 -> 0.49 | outside the BoS 16.8% -> 0.0%
        max roll 15.4 -> 10.6 deg | pelvis MIN 102.4% -> 102.9%

    BACKWARD COMPATIBLE BY MEASUREMENT, not by flag: a 3-block theta (3*nu) is the old
    formula exactly, because kr is then zeros and the added term vanishes. So an old
    checkpoint judges identically and cannot silently acquire a term it was never trained
    with -- the defect this project spent the day paying for in the walk port.
    """
    def fn(obs, value):
        import numpy as np
        a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:3 * nu]
        kr = theta[3 * nu:4 * nu] if theta.size >= 4 * nu else np.zeros(nu)
        return np.clip(a0 + kh * (tgt - obs["z"]) + kp * obs["pitch"]
                       + kr * obs.get("roll", 0.0), 0.0, 1.0)
    return fn


def default_registry(theta=None, tgt=None, nu=None):
    """The v2 registry: `STAND` live (given its trained theta), every map verb a named
    refusal pointing at the milestone that trains its atoms. Registration ORDER is the
    conflict rule, so STAND is registered first -- it is the only formula that exists.
    STAND is not a map button: in-game BALANCE is always-on (CONTROLLER_MAP.md), and the
    harness drives it as a button to prove the button -> formula -> muscles path."""
    reg = {}
    if theta is not None:
        reg["STAND"] = Formula("STAND", stand_formula_fn(theta, tgt, nu), EXCLUSIVE)
    for verb, reason in (
        ("MOVE", "no trained formula -- its atoms are M3 (STEP+PLANT+BALANCE)"),
        ("SPRINT", "no trained formula -- STEP(fast)+SWING, after MOVE"),
        ("LOOK", "no trained formula -- ORIENT atom, after MOVE"),
        ("JUMP", "no trained formula -- its atoms are LAUNCH+ABSORB (map order 2)"),
        ("CROUCH", "no trained formula -- SHIFT-down+PLANT, map order 4"),
        ("GRAB", "no trained formula -- its atoms are M8 (REACH+GRIP+BRACE)"),
        ("ACTION", "no trained formula -- SWING/PUSH, map order 4"),
        ("AIM", "no trained formula -- ORIENT+BRACE, map order 4"),
        ("USE", "no trained formula -- item state, after GRAB"),
        ("LHAND", "no trained formula -- REACH+GRIP, after GRAB"),
        ("RHAND", "no trained formula -- REACH+GRIP, after GRAB"),
        ("STANCE", "no trained formula -- pose set, after the atoms"),
    ):
        reg[verb] = Refusal(verb, reason)
    return reg
