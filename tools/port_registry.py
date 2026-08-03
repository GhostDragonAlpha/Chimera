"""port_registry.py -- the ONE registry every port test registers into.

WHY THIS MODULE EXISTS, and it is a defect worth the extra file. `port_tests.py` runs as
`__main__`; `port_tests_more.py` did `from port_tests import port_test`, which imports a SECOND
copy of the module with its OWN empty TESTS dict. Ports 5-12 registered into a dictionary nobody
read, and the harness printed:

    4/4 ports validated

A clean, confident success, with two-thirds of the instruction set missing. Nothing in the output
said so. The harness built to catch silent successes SILENTLY SUCCEEDED.

    A SHARED REGISTRY MUST NOT LIVE IN A MODULE THAT IS ALSO AN ENTRY POINT.

So the registry lives here, imported by everything and run by nothing. And `expect()` makes the
count itself an assertion: a test file that fails to load is a REFUSAL, not a smaller number.
"""
from __future__ import annotations

from pathlib import Path

# SHARED CONFIG LIVES HERE TOO, for the same reason the registry does. `port_tests_more` importing
# MYOBODY from `port_tests` re-executed that module and re-registered every test in it -- caught
# by the duplicate-name guard below, thirty seconds after it was written. Anything two test files
# both need belongs in the module that neither of them runs.
ROOT = Path(__file__).resolve().parent.parent
MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"

TESTS = {}


def port_test(name, statement, falsifier):
    """Register a port test. All three parts required -- no falsifier, no test (Rule 0)."""
    if not statement or not falsifier:
        raise ValueError(f"port test {name!r} needs a STATEMENT and a FALSIFIER. A claim without "
                         f"a named refutation is a description, and a description cannot be wrong.")
    if name in TESTS:
        raise ValueError(f"port test {name!r} registered twice -- two instructions cannot share "
                         f"a name, and a silent overwrite would hide one of them")

    def deco(fn):
        TESTS[name] = dict(fn=fn, statement=statement, falsifier=falsifier, name=name)
        return fn
    return deco


PRIMITIVES = {}


def primitive_test(name, ports, statement, falsifier):
    """Register a PRIMITIVE -- a composition of validated ports that does something none of them
    does alone.

    TWO GUARDS BEYOND THE PORT'S. A primitive must NAME the ports it composes, and every named one
    must already be registered: you cannot declare a composition over an instruction that does not
    exist. And it must ABLATE -- the test has to show the primitive FAILING when one port's
    contribution is removed. Without an ablation a primitive is a port wearing a longer name, and
    the whole layer would be relabelling rather than composing. Port 12 already worked this way
    (coupled converges, uncoupled does not); this makes it the rule instead of one test's trick.
    """
    if not statement or not falsifier:
        raise ValueError(f"primitive {name!r} needs a STATEMENT and a FALSIFIER (Rule 0).")
    if not ports:
        raise ValueError(f"primitive {name!r} names no ports. A composition of nothing is a port; "
                         f"register it as one or name what it is built from.")
    missing = [p for p in ports if p not in TESTS]
    if missing:
        raise ValueError(f"primitive {name!r} composes {missing}, which are not registered ports. "
                         f"Import the port tests first -- a primitive over an unvalidated "
                         f"instruction is exactly the thing this layer exists to prevent.")
    if name in PRIMITIVES:
        raise ValueError(f"primitive {name!r} registered twice -- a silent overwrite hides one.")

    def deco(fn):
        PRIMITIVES[name] = dict(fn=fn, statement=statement, falsifier=falsifier, name=name,
                                ports=list(ports))
        return fn
    return deco


ACTIONS = {}


def action_test(name, rests_on, statement, prediction, falsifier):
    """Register an ACTION PRIMITIVE -- one thing the body DOES, as a program over validated ports.

    RULE 0 HAS THREE PARTS AND THIS REGISTRY ONLY ENFORCED TWO. `port_test` and `primitive_test`
    demand a STATEMENT and a FALSIFIER and let the PREDICTION live wherever the test author felt
    like putting it -- which means the number could be written after the run and nobody would know.
    A prediction produced after the measurement is a description, and the whole of Rule 0 is that a
    description survives any result. It is a required field here.

        THE PREDICTION IS DECLARED AT REGISTRATION, WHICH IS BEFORE THE TEST CAN HAVE RUN.

    `rests_on` names ports and mechanism primitives; every name must already be registered.
    """
    if not statement or not prediction or not falsifier:
        missing = [n for n, v in (("STATEMENT", statement), ("PREDICTION", prediction),
                                  ("FALSIFIER", falsifier)) if not v]
        raise ValueError(f"action {name!r} is missing {' and '.join(missing)}. Rule 0 has three "
                         f"parts and all three are required before the test may exist.")
    if not rests_on:
        raise ValueError(f"action {name!r} rests on nothing. An action is a PROGRAM over an "
                         f"instruction set; name the instructions.")
    unknown = [p for p in rests_on if p not in TESTS and p not in PRIMITIVES]
    if unknown:
        raise ValueError(f"action {name!r} rests on {unknown}, which are neither validated ports "
                         f"nor registered primitives. Import them first.")
    if name in ACTIONS:
        raise ValueError(f"action {name!r} registered twice -- a silent overwrite hides one.")

    def deco(fn):
        ACTIONS[name] = dict(fn=fn, statement=statement, prediction=prediction,
                             falsifier=falsifier, name=name, rests_on=list(rests_on))
        return fn
    return deco


def expect_actions(n: int) -> None:
    if len(ACTIONS) != n:
        raise SystemExit(
            f"REFUSING TO RUN: {len(ACTIONS)} actions registered, expected {n}.\n"
            f"  registered: {sorted(ACTIONS)}")


def expect_primitives(n: int) -> None:
    if len(PRIMITIVES) != n:
        raise SystemExit(
            f"REFUSING TO RUN: {len(PRIMITIVES)} primitives registered, expected {n}.\n"
            f"  registered: {sorted(PRIMITIVES)}")


def port_coverage() -> dict:
    """Which validated ports no primitive rests on. An instruction nothing composes is either
    unnecessary or a layer that was never built -- and the difference should be visible."""
    used = {p for v in PRIMITIVES.values() for p in v["ports"]}
    return {"used": sorted(used), "unused": sorted(set(TESTS) - used)}


def expect(n: int) -> None:
    """Refuse to run a partial instruction set.

    The count is an assertion because the alternative already happened: 8 of 12 tests failed to
    register and the harness reported total success on the 4 that had.
    """
    if len(TESTS) != n:
        raise SystemExit(
            f"REFUSING TO RUN: {len(TESTS)} port tests registered, expected {n}.\n"
            f"  registered: {sorted(TESTS)}\n"
            f"  A missing test is not a smaller test suite -- it is an untested instruction that "
            f"a composition will later be blamed for.")
