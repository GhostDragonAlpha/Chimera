"""parser_tests.py -- the Phase D parser's three falsifiers, measured (docs/THE_PARSER.md).

The parser cannot be wrong in an interesting way, so its tests are structural:

  1. BIT-IDENTITY  the stand port through the parser == v1's inline lambda, exactly,
                   over a sweep of (z, pitch). The grammar carries semantics; it may
                   not alter them by ANY amount.
  2. TWO BINDINGS  keyboard and gamepad tables map onto the identical verb set, and
                   the formula layer never sees a physical name -- bindings are DATA.
  3. NAMED REFUSAL every held-but-unimplemented verb refuses BY NAME in the trace;
                   nothing drives silently (no zero command, no crash, no default).

Plus the grammar's own rules: exclusivity conflict is named in the trace, and an
unheld world parses to no drive (f3's phase 2 slumps BY the parser, not around it).

    python tools/parser_tests.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import parser as P

THETA = ROOT / "ChimeraEngine" / "output" / "ports" / "stand_theta.npy"
TGT = 0.9201                       # the derived pelvis target (theStance/theHuman) --
                                   # read by f3 from the port; the sweep only needs A value


def check(name, ok, detail):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return bool(ok)


def main() -> int:
    if not THETA.exists():
        raise SystemExit(f"no {THETA} -- run tools/train_stand.py first (rule 20).")
    theta = np.load(THETA)
    nu = theta.size // 3
    ok = True

    # -- FALSIFIER 1: bit-identity with v1 over a sweep -------------------------------------
    # v1's lambda, reconstructed verbatim from tools/f3_stand.py lines 53-57.
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:]
    v1 = lambda z, pitch: np.clip(a0 + kh * (TGT - z) + kp * pitch, 0.0, 1.0)
    par = P.Parser(P.default_registry(theta, TGT, nu))
    par.set_verb("STAND", True)
    worst = 0.0
    for z in np.linspace(0.4, 1.1, 15):
        for pitch in np.linspace(-0.35, 0.35, 9):
            u2, _ = par.command({"z": float(z), "pitch": float(pitch)})
            worst = max(worst, float(np.max(np.abs(u2 - v1(z, pitch)))))
    ok &= check("falsifier 1: parser stand == v1 stand, bit-identical",
                worst == 0.0, f"max |diff| over 135 samples = {worst:.3e}")

    # -- FALSIFIER 2: both bindings are data over the identical verb set --------------------
    kb_verbs = set(P.BIND_KEYBOARD.values())
    gp_verbs = set(P.BIND_GAMEPAD.values())
    same = kb_verbs == gp_verbs == set(P.VERBS)
    ok &= check("falsifier 2: keyboard + gamepad cover the identical verb set",
                same, f"keyboard-only {sorted(kb_verbs - gp_verbs)}, "
                      f"gamepad-only {sorted(gp_verbs - kb_verbs)}, "
                      f"uncovered {sorted(set(P.VERBS) - kb_verbs)}")
    # the formula layer never sees a physical name: set_physical resolves through the
    # table and nothing downstream can tell which surface drove it
    par_k = P.Parser(P.default_registry(theta, TGT, nu), binding=P.BIND_KEYBOARD)
    par_g = P.Parser(P.default_registry(theta, TGT, nu), binding=P.BIND_GAMEPAD)
    ok &= check("falsifier 2b: an unbound physical input is a no-op, not an error",
                par_k.set_physical("F13", True) is None, "F13 -> None")
    ok &= check("falsifier 2c: the gamepad table drives verbs identically",
                par_g.set_physical("X", True) == "GRAB"
                and par_g.state["GRAB"].held, "X -> GRAB held")

    # -- FALSIFIER 3: every held-but-unimplemented verb refuses BY NAME ---------------------
    par2 = P.Parser(P.default_registry(theta, TGT, nu))
    for verb in P.VERBS:
        par2.set_verb(verb, True)
    par2.set_verb("STAND", True)
    u, tr = par2.command({"z": 0.9, "pitch": 0.0})
    named = {v for v, _ in tr.refused}
    ok &= check("falsifier 3: all 12 map verbs refuse by name, the live formula drives",
                named == set(P.VERBS) and u is not None and tr.driver == "STAND",
                f"{len(named)}/12 refused by name, driver {tr.driver}")

    # -- the composition rule, exercised: two exclusive formulas held -----------------------
    f_a = P.Formula("STAND", lambda obs, v: np.ones(4), P.EXCLUSIVE)
    f_b = P.Formula("MOVE", lambda obs, v: np.zeros(4), P.EXCLUSIVE)
    par4 = P.Parser({"STAND": f_a, "MOVE": f_b})
    par4.set_verb("STAND", True)
    par4.set_verb("MOVE", True)
    u4, tr4 = par4.command({})
    ok &= check("composition: registration order wins AND the loser is named",
                tr4.driver == "STAND" and tr4.conflicts == [("STAND", "MOVE")]
                and float(u4[0]) == 1.0,
                f"driver {tr4.driver}, conflicts {tr4.conflicts}")

    # -- the grammar's own rules ------------------------------------------------------------
    par3 = P.Parser(P.default_registry(theta, TGT, nu))
    u0, tr0 = par3.command({"z": 0.9, "pitch": 0.0})
    ok &= check("an unheld world parses to no drive (phase 2 slumps BY the parser)",
                u0 is None and tr0.driver is None, "no verbs held -> (None, empty trace)")
    try:
        par3.set_verb("FLY", True)
        unnamed = True
    except KeyError:
        unnamed = False
    ok &= check("a verb the map does not name is refused by the grammar",
                not unnamed, "FLY -> KeyError naming the verb set")

    print()
    print(f"VERDICT: {'PASS' if ok else 'FAIL'} -- the grammar carries, refuses, and names")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
