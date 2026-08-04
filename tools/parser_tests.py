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
    # nu COMES FROM THE MODEL, NOT FROM DIVIDING THE CHECKPOINT BY AN ASSUMED BLOCK COUNT.
    # This line was `nu = theta.size // 3`, and it broke silently the moment the stand formula
    # gained its fourth block (kr, the roll term, 2026-08-04): a 1160-number theta divided by 3
    # gives nu = 386 against a body with 290 actuators, so `a0` was 386 long, `kp` was 388, and
    # falsifier 1 died on a broadcast error instead of measuring anything. IT HAS BEEN
    # UN-RUNNABLE EVER SINCE -- the parser's headline claim, that the grammar carries the
    # identical signal, has gone unchecked across every commit that touched the formula.
    #
    # A block count inferred from a checkpoint's LENGTH is a second landmark for a quantity the
    # model already owns (rule 19). The number of muscles is a property of the body; the number
    # of blocks is then just theta.size / nu, and both are read rather than assumed.
    import mujoco
    from world import load_body
    from stand_port import MYOBODY
    _m, _g = load_body(MYOBODY, mujoco)
    nu = int(_m.nu)
    if theta.size % nu:
        raise SystemExit(f"stand_theta holds {theta.size} numbers, which is not a whole number "
                         f"of {nu}-muscle blocks. Refusing to guess the policy's shape.")
    blocks = theta.size // nu
    ok = True

    # -- FALSIFIER 0: THE SHAPE GUARD, wired into the sweep -----------------------------------
    # RULE 0 for it, stated before it was built (2026-08-04):
    #
    #   STATEMENT   Falsifier 1 below was silently un-runnable from the moment the stand formula
    #               gained its fourth block, because it inferred `nu` from the checkpoint's
    #               length. Reading `nu` from the model fixes THIS file; nothing stops the same
    #               drift recurring at the WRITER, where a short theta becomes a checkpoint every
    #               consumer quietly zero-fills. A shape contract that only the reader enforces
    #               is a contract with one party.
    #   PREDICTION  `parser.check_theta_shape` refuses a 3-block theta against the parser's
    #               declared 4, and accepts the real on-disk checkpoint unchanged.
    #   FALSIFIER   If a 3-block theta passes the guard, the guard is decorative and this test
    #               is the one that says so.
    #
    # The guard is exercised on a SYNTHETIC 3-block theta, never by writing a bad file: an
    # instrument that has to create the defect on disk to detect it is one crash away from
    # leaving it there.
    _short = np.zeros(3 * nu)
    try:
        P.check_theta_shape(_short, nu, where="parser_tests synthetic 3-block")
        _tripped, _why = False, "it PASSED -- the guard is decorative"
    except SystemExit as e:
        _tripped, _why = True, str(e).split(".")[0]
    ok &= check("falsifier 0: the shape guard trips on a 3-block theta", _tripped, _why)
    try:
        _b = P.check_theta_shape(theta, nu, where="parser_tests on-disk stand_theta")
        _live, _lwhy = True, f"{_b} blocks x {nu} = {theta.size}, the declared contract"
    except SystemExit as e:
        _live, _lwhy = False, str(e)
    ok &= check("falsifier 0b: the guard accepts the real checkpoint", _live, _lwhy)

    # -- FALSIFIER 0c: NO CONSUMER REIMPLEMENTS THE STAND FORMULA -----------------------------
    # The guard above protects the CHECKPOINT. It cannot protect a consumer that never asks it:
    # `step_port.step_formula` wrote the arithmetic out again and ended in an OPEN SLICE
    # `theta_stand[2 * nu:]`, correct at three blocks and 580 numbers wide at four. It had been
    # crashing `f5_step` outright with a broadcast error since the roll block landed, in a file
    # the shape guard could not reach BECAUSE it reimplemented the formula instead of calling
    # it. Two copies of a formula agree until one is edited.
    #
    # So the sweep asks the question directly: with no swing active, does the step port's stand
    # half equal the parser's, bit for bit? A consumer that slices its own way will disagree the
    # moment a block is added, and will say so HERE rather than in a harness six files away.
    try:
        import step_port as SP
        _sp_reg = P.default_registry(theta, TGT, nu)
        _idle = {"r": "stance", "l": "stance"}         # no swing -> the stand formula alone
        _w = 0.0
        for z in np.linspace(0.4, 1.1, 9):
            for pitch in np.linspace(-0.35, 0.35, 5):
                for roll in (-0.2, 0.0, 0.2):
                    a = SP.step_formula(theta, np.zeros(64), {}, float(z), float(pitch), nu,
                                        TGT, _idle, {"r": 0.0, "l": 0.0}, gain=0.0,
                                        roll=float(roll))
                    b = _sp_reg["STAND"].command({"z": float(z), "pitch": float(pitch),
                                                  "roll": float(roll)}, 1.0)
                    _w = max(_w, float(np.max(np.abs(a - b))))
        ok &= check("falsifier 0c: step_port's stand half == the parser's, bit-identical",
                    _w == 0.0, f"max |diff| over 135 samples = {_w:.3e}")
    except Exception as e:                              # a CRASH is the failure, not an excuse
        ok &= check("falsifier 0c: step_port's stand half == the parser's, bit-identical",
                    False, f"{type(e).__name__}: {e}")

    # -- FALSIFIER 1: bit-identity with the formula the parser CLAIMS to carry ---------------
    # Reconstructed from tools/parser.py's `stand_formula_fn`, which is what the claim is ABOUT.
    # The roll term is included when the theta carries one, because a reference that omits a
    # block the parser applies does not test the parser -- it tests the reference.
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:3 * nu]
    kr = theta[3 * nu:4 * nu] if blocks >= 4 else np.zeros(nu)
    ref = lambda z, pitch, roll: np.clip(
        a0 + kh * (TGT - z) + kp * pitch + kr * roll, 0.0, 1.0)
    par = P.Parser(P.default_registry(theta, TGT, nu))
    par.set_verb("STAND", True)
    worst, n_s = 0.0, 0
    for z in np.linspace(0.4, 1.1, 15):
        for pitch in np.linspace(-0.35, 0.35, 9):
            for roll in ((0.0,) if blocks < 4 else (-0.2, 0.0, 0.2)):
                u2, _ = par.command({"z": float(z), "pitch": float(pitch), "roll": float(roll)})
                worst = max(worst, float(np.max(np.abs(u2 - ref(z, pitch, roll)))))
                n_s += 1
    ok &= check(f"falsifier 1: parser stand == the {blocks}-block formula, bit-identical",
                worst == 0.0, f"max |diff| over {n_s} samples = {worst:.3e}")

    # -- FALSIFIER 1b: AND it still reduces to v1 when roll is absent ------------------------
    # The original falsifier's meaning, preserved: with no roll in the obs the grammar must
    # produce v1's inline lambda exactly, so the roll block cannot have silently changed what
    # every pre-2026-08-04 result was measured on.
    v1 = lambda z, pitch: np.clip(a0 + kh * (TGT - z) + kp * pitch, 0.0, 1.0)
    worst1 = 0.0
    for z in np.linspace(0.4, 1.1, 15):
        for pitch in np.linspace(-0.35, 0.35, 9):
            u2, _ = par.command({"z": float(z), "pitch": float(pitch)})
            worst1 = max(worst1, float(np.max(np.abs(u2 - v1(z, pitch)))))
    ok &= check("falsifier 1b: with no roll in the obs, the parser == v1 exactly",
                worst1 == 0.0, f"max |diff| over 135 samples = {worst1:.3e}")

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
