"""R4 adversarial probes -- RUN FROM /tmp, imports the repo read-only, writes nothing.
Declared in PREREGISTERED_CHECKS.md as C5 probes A1-A5."""
import io
import json
import sys
from pathlib import Path

ROOT = Path("E:/ChimeraWork/monkey-play-20260924")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "monkey_campaign" / "product"))

import climb_intent as CI  # noqa: E402

RESULTS = []


def probe(name, ok, detail=""):
    tag = "REPRO" if ok else "FINDING"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    RESULTS.append((name, ok, detail))


def raises(exc, fn):
    try:
        fn()
        return False
    except exc:
        return True
    except Exception as e:  # wrong exception class
        print(f"      (wrong exception: {type(e).__name__}: {e})")
        return False


print("== A1: float/bool/NaN/Inf smuggling into IntentEvent ==")
probe("A1.a float issued_tick refused",
      raises(CI.IntentEventError, lambda: CI.IntentEvent("climb_request", 1.5, 0)))
probe("A1.b float now_ms refused",
      raises(CI.IntentEventError, lambda: CI.IntentEvent("climb_request", 0, 1000.5)))
probe("A1.c NaN stamp refused",
      raises(CI.IntentEventError, lambda: CI.IntentEvent("let_go", float("nan"), 0)))
probe("A1.d Inf stamp refused",
      raises(CI.IntentEventError, lambda: CI.IntentEvent("let_go", float("inf"), 0)))
probe("A1.e bool stamp refused",
      raises(CI.IntentEventError, lambda: CI.IntentEvent("let_go", True, 0)))
big = CI.IntentEvent("let_go", 10**400, 10**400)
probe("A1.f huge (unbounded) int accepted -- spec has no upper bound",
      big.issued_tick == 10**400)
ev_bool_ver = None
try:
    ev_bool_ver = CI.IntentEvent("climb_request", 0, 0, intent_version=True)
except CI.IntentEventError:
    pass
probe("A1.g FINDING-CHECK: intent_version=True (bool) ACCEPTED by the validator "
      "(True == 1)", ev_bool_ver is not None,
      f"canonical={ev_bool_ver.canonical_fields() if ev_bool_ver else 'refused'}")
if ev_bool_ver is not None:
    probe("A1.g' and it JSON-encodes as TRUE on the wire",
          json.dumps(ev_bool_ver.canonical_fields()).count("true") == 1)
probe("A1.h string version '1' refused (1 != '1')",
      raises(CI.IntentEventError, lambda: CI.IntentEvent("climb_request", 0, 0,
                                                         intent_version="1")))
probe("A1.i extra kwargs refused (dataclass: no field smuggling)",
      raises(TypeError, lambda: CI.IntentEvent("climb_request", 0, 0, magnitude=2.5)))
ev = CI.IntentEvent("climb_request", 5, 5)
probe("A1.j frozen event cannot be mutated",
      raises(Exception, lambda: setattr(ev, "intent", "let_go")))

print("== A2: version confusion (v1 presented as v2 / foreign shapes) ==")
v2 = {"intent_version": 2, "intent": "climb_request", "issued_tick": 1,
      "now_ms": 1, "source": "u05_climb_intent"}
probe("A2.a a v2 wire dict refused by the v1 constructor",
      raises(CI.IntentEventError, lambda: CI.IntentEvent(**v2)))
probe("A2.b a v3 dict refused too",
      raises(CI.IntentEventError, lambda: CI.IntentEvent(
          **{**v2, "intent_version": 3})))
probe("A2.c an unknown intent name at version 1 refused",
      raises(CI.IntentEventError, lambda: CI.IntentEvent("climb_grab", 0, 0)))
probe("A2.d INTENT_VERSION is the module constant the validator compares to",
      CI.INTENT_VERSION == 1 and CI.IntentEvent("let_go", 0, 0).intent_version == 1)

print("== A3: press on the exact gate-transition tick (same now_ms) ==")


def transition_probe(order):
    sink = CI.MockIntentSink()
    ch = CI.ClimbIntentChannel(sink)
    if order == "press_first":
        r1, r2 = ch.press("Space", 1000), ch.on_pause(1000)
    else:
        r1, r2 = ch.on_pause(1000), ch.press("Space", 1000)
    return len(sink), r1, r2, ch.state


lens = set()
for _ in range(100):
    lens.add(transition_probe("press_first")[0])
probe("A3.a press-then-pause AT THE SAME ms: DELIVERED (call order decides), "
      "deterministic 100/100", lens == {1}, f"delivery_counts={sorted(lens)}")
lens2 = set()
for _ in range(100):
    lens2.add(transition_probe("pause_first")[0])
probe("A3.b pause-then-press AT THE SAME ms: DROPPED_BY_NAME, deterministic "
      "100/100", lens2 == {0} and transition_probe("pause_first")[3] == "paused",
      f"delivery_counts={sorted(lens2)}")

print("== A4: second listener / two sinks ==")
shared = CI.MockIntentSink()
c1 = CI.ClimbIntentChannel(shared)
c2 = CI.ClimbIntentChannel(shared)
c1.press("Space", 1000)
c2.press("Space", 1000)
probe("A4.a FINDING-CHECK: two channels wired to one sink DOUBLE-deliver "
      "(no exclusivity guard; the seam has no add_listener API)",
      len(shared) == 2, f"events={len(shared)}")
solo = CI.MockIntentSink()
ch = CI.ClimbIntentChannel(solo)
probe("A4.b the channel exposes no add_listener/attach -- second-listener race "
      "cannot occur through the declared surface",
      not any(hasattr(ch, a) for a in ("add_listener", "attach", "subscribe")))
ch.bindings["Space"] = "let_go"          # harness mutates its copy
probe("A4.c chan.bindings is a COPY: the module default is untouched",
      CI.DEFAULT_INTENT_BINDINGS["Space"] == "climb_request")

print("== A5: boundary values and failure ordering ==")
s = CI.MockIntentSink()
ch = CI.ClimbIntentChannel(s)
exc = None
try:
    ch.press("Space", -5)                # invalid stamp AFTER the gate/arm logic
except CI.IntentEventError as e:
    exc = e
probe("A5.a negative now_ms press RAISES (validator fires)",
      exc is not None, f"{type(exc).__name__}" if exc else "no raise")
probe("A5.b FINDING-CHECK: but the edge was ARMED BEFORE the validation raised "
      "-- held={'Space'}, zero events (held-but-never-delivered)",
      "Space" in ch.held and len(s) == 0, f"held={sorted(ch.held)}, events={len(s)}")
r = ch.press("Space", 100)
probe("A5.c ...and the NEXT VALID press is then a silent-delivery no-op "
      "(the physical press was consumed)",
      len(s) == 0 and r == "climb_request", f"events={len(s)}, ret={r!r}")
ch.release("Space", 200)
s2 = CI.MockIntentSink()
ch2 = CI.ClimbIntentChannel(s2, tick_source=lambda: -1)
exc2 = None
try:
    ch2.press("Space", 100)
except CI.IntentEventError as e:
    exc2 = e
probe("A5.d a raising tick_source hits the same arm-before-validate path",
      exc2 is not None and "Space" in ch2.held and len(s2) == 0,
      f"held={sorted(ch2.held)}, events={len(s2)}")

s3 = CI.MockIntentSink()
ch3 = CI.ClimbIntentChannel(s3)
forged = CI.IntentEvent("let_go", 1, 1, source="not_the_channel")
probe("A5.e FINDING-CHECK: source is NOT validated -- a forged source "
      "constructs cleanly (spec says source is FIXED)", forged.source == "not_the_channel")

s4 = CI.MockIntentSink()
ch4 = CI.ClimbIntentChannel(s4)
probe("A5.f FINDING-CHECK: press() returns the intent name on a REPEAT (held) "
      "press -- indistinguishable from a delivered press by return value, "
      "contra the docstring's 'else None'",
      ch4.press("Space", 1000) == "climb_request"
      and ch4.press("Space", 1010) == "climb_request" and len(s4) == 1,
      f"ret2={ch4.press('Space', 1010)!r}, events={len(s4)}")

s5 = CI.MockIntentSink()
ch5 = CI.ClimbIntentChannel(s5)
probe("A5.g unbound press ignored-but-recorded; release of never-pressed key safe",
      ch5.press("X", 100) is None and ch5.release("Q", 110) is None and len(s5) == 0)
probe("A5.h bool intent at construction refused",
      raises(CI.IntentEventError, lambda: CI.IntentEvent(True, 0, 0)))

print()
n_repro = sum(1 for _, ok, _ in RESULTS if ok)
n_finding = sum(1 for _, ok, _ in RESULTS if not ok)
print(f"PROBE RESULT: {n_repro} expectations reproduced as expected, "
      f"{n_finding} adversarial FINDINGS (probe checks whose ok=False mark a "
      f"claimed-safe behavior that broke)")
