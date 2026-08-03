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
