"""climb_intent_amr_tests.py -- M-U05b: R4's four BINDING amendments, measured.

Each check is R4's measurement (agents/R4_intent_review/report.md section 4,
probes A1.g, A5.e, A5.b-d, A5.f) converted to the DEMANDED behavior. These four
run AGAINST THE UNEDITED MODULE FIRST (failing-first evidence:
agents/U05b_amendments_U06/receipts/amr_failing_first_20260924.txt), then the
minimal fixes land in climb_intent.py and this file plus U05's 73-check suite
are green: 77/77. No version bump: the wire format, the delivered event set,
and every valid-path behavior are unchanged (R4's ruling).

  AMR-1  the validator refuses intent_version=True (bool; True == 1 smuggled)
  AMR-2  the validator refuses a forged source (provenance a constructor can
         forge is not provenance)
  AMR-3  validate-then-arm: a press whose stamp fails validation NEVER arms
         the edge (no silent consumption of a physical press)
  AMR-4  press()'s docstring states the measured two-case return contract

Prereg: agents/U05b_amendments_U06/PREREGISTRATION.md section 1.

    python tools/monkey_campaign/product/climb_intent_amr_tests.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import climb_intent as CI                                  # noqa: E402

FAILURES = []


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def raises(fn):
    try:
        fn()
        return False
    except CI.IntentEventError:
        return True
    except Exception:
        return False


def amendment_1():
    print("AMR-1: the validator refuses intent_version=True (R4 A1.g/A1.g')")
    ok_true = raises(lambda: CI.IntentEvent("climb_request", 0, 0,
                                            intent_version=True))
    ok_str = raises(lambda: CI.IntentEvent("climb_request", 0, 0,
                                           intent_version="1"))
    ok_float = raises(lambda: CI.IntentEvent("climb_request", 0, 0,
                                             intent_version=1.0))
    ok_two = raises(lambda: CI.IntentEvent("climb_request", 0, 0,
                                           intent_version=2))
    v1_still_constructs = CI.IntentEvent("let_go", 5, 5).intent_version == 1
    check("AMR-1 intent_version=True / '1' / 1.0 / 2 REFUSED; plain 1 still "
          "constructs (bool is not a version: True == 1 smuggled a wire value)",
          ok_true and ok_str and ok_float and ok_two and v1_still_constructs,
          f"True->{ok_true}, '1'->{ok_str}, 1.0->{ok_float}, 2->{ok_two}")


def amendment_2():
    print("AMR-2: the validator refuses a forged source (R4 A5.e)")
    ok_forged = raises(lambda: CI.IntentEvent("let_go", 1, 1,
                                              source="not_the_channel"))
    ok_empty = raises(lambda: CI.IntentEvent("let_go", 1, 1, source=""))
    ev = CI.IntentEvent("climb_request", 3, 3)
    check("AMR-2 a forged/empty source REFUSED; the default still stamps the "
          "fixed SOURCE_ID (provenance a constructor can forge is not "
          "provenance; wire format unchanged)",
          ok_forged and ok_empty
          and ev.source == CI.SOURCE_ID == "u05_climb_intent",
          f"forged->{ok_forged}, empty->{ok_empty}, default={ev.source!r}")


def amendment_3():
    print("AMR-3: validate-then-arm -- a bad stamp NEVER arms the edge (R4 A5.b-d)")
    sink = CI.MockIntentSink()
    chan = CI.ClimbIntentChannel(sink)
    raised = False
    try:
        chan.press("Space", -5)           # invalid stamp (negative now_ms)
    except CI.IntentEventError:
        raised = True
    not_armed = "Space" not in chan.held
    nothing_delivered = len(sink) == 0
    r = chan.press("Space", 100)          # the NEXT valid press
    delivered_after = (r == "climb_request" and len(sink) == 1
                       and sink.events[-1].now_ms == 100)

    sink2 = CI.MockIntentSink()

    def bad_tick():
        raise RuntimeError("broken tick source")
    chan2 = CI.ClimbIntentChannel(sink2, tick_source=bad_tick)
    raised2 = False
    try:
        chan2.press("Space", 100)
    except (CI.IntentEventError, RuntimeError):
        raised2 = True                    # the point: whichever raises, the
    not_armed2 = "Space" not in chan2.held and len(sink2) == 0
    check("AMR-3 a bad-stamp press (negative now_ms OR a raising tick_source) "
          "RAISES without arming the edge; the NEXT valid press DELIVERS (no "
          "silent consumption of a physical press)",
          raised and not_armed and nothing_delivered and delivered_after
          and raised2 and not_armed2,
          f"neg: raised={raised}, held={sorted(chan.held)}, events={len(sink)}, "
          f"redeliver={delivered_after}; tick_src: raised={raised2}, "
          f"held={sorted(chan2.held)}, events={len(sink2)}")


def amendment_4():
    print("AMR-4: press()'s docstring states the measured return contract (R4 A5.f)")
    sink = CI.MockIntentSink()
    chan = CI.ClimbIntentChannel(sink)
    r1 = chan.press("Space", 1000)        # fresh: ONE event
    r2 = chan.press("Space", 1010)        # repeat (held): ZERO events
    measured = (r1 == "climb_request" and len(sink) == 1
                and r2 == "climb_request" and len(sink) == 1
                and chan.last_trace.get("repeat_press") == [("Space", 1010)])
    doc = CI.ClimbIntentChannel.press.__doc__ or ""
    false_claim_gone = ("if ONE event was emitted" not in doc
                        and "else None" not in doc)
    repeat_named = "repeat" in doc
    check("AMR-4 the docstring no longer claims 'returns ... if ONE event was "
          "emitted, else None' (the repeat press returns the bound action with "
          "ZERO events -- R4 A5.f) and names the repeat case",
          measured and false_claim_gone and repeat_named,
          f"measured={measured}, false_claim_gone={false_claim_gone}, "
          f"repeat_named={repeat_named}")


def main():
    print("climb_intent_amr_tests -- M-U05b: R4's four BINDING amendments "
          "(prereg: agents/U05b_amendments_U06/PREREGISTRATION.md)")
    amendment_1()
    amendment_2()
    amendment_3()
    amendment_4()
    print()
    if FAILURES:
        print(f"RESULT: FAIL ({len(FAILURES)} amendment checks fired)")
        for f in FAILURES:
            print(f"  FIRED: {f}")
        return 1
    print("RESULT: GREEN -- all 4 amendment checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
