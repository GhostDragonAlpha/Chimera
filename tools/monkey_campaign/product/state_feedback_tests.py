"""state_feedback_tests.py -- M-U05b/U06 falsifiers, measured (prereg §2.5).

Headless: injected millisecond clocks, real landed modules (X02 SessionFlow,
U03 FocusPolicy + U01 InputMapper, U05 ClimbIntentChannel) driven through
synthetic scenarios, no window, no desktop input, no engine process, no wall
clock. The display model is measured against the frozen vocabulary in
agents/U05b_amendments_U06/PREREGISTRATION.md section 2:

  V1  DERIVABILITY   every vocabulary row renders from REAL module objects
                     (public attributes only); prompt == the frozen line;
                     sources cite the right modules.
  V2  NO-CAPABILITY-CLAIM FUZZ   20,000 seeded adversarial state combos
                     (incl. cross-source mis-wiring and stale flashes):
                     every rendered prompt+diagnostic scanned for the frozen
                     forbidden claim tokens (ZERO hits); the ladder is
                     model-checked (an independent model recomputes every
                     state_key and prompt); invalid inputs RAISE, never render.
  V3  U05 INTEGRATION    intent events/drops surface correctly: the delivered
                     flash, the held edge, named drops in OPTIONAL
                     diagnostics only (default OFF, empty).
  V4  X02/U03 GATING    real session pause/exit and real focus blur/disconnect
                     each take over the line; recovery returns the ladder to
                     walking/climb_ready WITHOUT the word.
  V5  HONESTY BOUNDARIES    the map's five nouns: falling/recovery/support
                     have NO row and NO token; the no-skill disclaimer is
                     mandatory in climb lines; `held` never renders as a
                     game state; the record JSON round-trips.

    python tools/monkey_campaign/product/state_feedback_tests.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import input_mapper as M                                    # noqa: E402
import focus_policy as FP                                   # noqa: E402
import session_flow as SF                                   # noqa: E402
import climb_intent as CI                                   # noqa: E402
import state_feedback as SFB                                # noqa: E402

FAILURES = []
SEED = 20260924                       # house seed (U01/U03/U05 precedent)
FUZZ_COMBOS = 20000                   # prereg-frozen (never tuned)


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


class Rig:
    """The real module composition: one X02 flow + one U03 policy (carrying
    its U01 mapper) + one U05 channel, all on one injected clock."""

    def __init__(self):
        self.walk_sink = M.MockSink()
        self.fp = FP.FocusPolicy(
            self.walk_sink, mapper_factory=lambda gate: M.InputMapper(gate))
        self.flow_mapper = M.InputMapper(M.MockSink())
        self.flow = SF.SessionFlow(self.flow_mapper,
                                   SF.RecordingRestart().boot,
                                   SF.TeardownDouble().shutdown_engine)
        self.intent_sink = CI.MockIntentSink()
        self.chan = CI.ClimbIntentChannel(self.intent_sink)

    def play(self, t):
        self.flow.key("Return", 1, t)                 # attract -> playing

    def observation(self, *, flash=False, now_ms=None, diagnostics_drop=False):
        return SFB.observe(
            self.flow, self.fp, self.chan, self.fp.mapper,
            flash_event=(self.intent_sink.events[-1]
                         if flash and self.intent_sink.events else None),
            now_ms=now_ms,
            walk_command_live=SFB.walk_record_live(self.walk_sink.records,
                                                   now_ms or 0),
            last_drop=(self.chan.last_trace.get("drops", [{}])[-1]
                       if diagnostics_drop
                       and self.chan.last_trace.get("drops") else None))


def expect(name, fn):
    """The renderer must REFUSE what it cannot name (raise, never render)."""
    try:
        fn()
        return False
    except SFB.UnknownStateError:
        return True
    except Exception:
        return False


# ── V1 DERIVABILITY (falsifier F-c: a row with no real source is dead) ────────
def v1_derivability():
    print("V1 DERIVABILITY: every vocabulary row renders from real modules")
    results = {}

    # rows 1-3: the X02 session states, reached BY KEYS on a real flow
    rig = Rig()
    results["session_menu"] = (rig.observation(now_ms=1000),
                               SFB.render(rig.observation(now_ms=1000)))
    rig.play(1100)
    rig.flow.key("Escape", 1, 1200)                   # playing -> paused
    results["session_paused"] = (None, SFB.render(rig.observation(now_ms=1200)))
    rig.flow.key("Q", 1, 1300)                        # paused -> exited
    results["session_exited"] = (None, SFB.render(rig.observation(now_ms=1300)))

    # row 4-5: the U03 gates on a live session
    rig2 = Rig()
    rig2.play(2000)
    rig2.fp.on_disconnect(2001)
    results["input_disconnected"] = (None, SFB.render(rig2.observation(now_ms=2001)))
    rig2b = Rig()
    rig2b.play(2000)
    rig2b.fp.on_blur(2001)
    results["input_blurred"] = (None, SFB.render(rig2b.observation(now_ms=2001)))

    # row 6: the U05 pause gate alone (session playing, channel gated)
    rig3 = Rig()
    rig3.play(3000)
    rig3.chan.on_pause(3001)
    results["intent_paused"] = (None, SFB.render(rig3.observation(now_ms=3001)))

    # rows 7-8: the delivered intent stream (REAL IntentEvents from a real sink)
    rig4 = Rig()
    rig4.play(4000)
    rig4.chan.press("Space", 4001)                    # ONE climb_request
    results["climb_sent"] = (None,
                             SFB.render(rig4.observation(flash=True,
                                                         now_ms=4001)))
    rig4.chan.release("Space", 4002)
    rig4.chan.press("C", 4003)                        # ONE let_go
    results["let_go_sent"] = (None,
                              SFB.render(rig4.observation(flash=True,
                                                          now_ms=4003)))

    # row 9: the held edge (an INPUT fact), flash NOT surfaced this call
    rig5 = Rig()
    rig5.play(5000)
    rig5.chan.press("Space", 5001)
    results["climb_key_held"] = (None,
                                 SFB.render(rig5.observation(now_ms=5002)))

    # row 10: the U01 walk stream, live per InputMapper.is_expired
    rig6 = Rig()
    rig6.play(6000)
    rig6.fp.press("W", 6001)
    rig6.fp.tick(6001)                                # ONE walk record
    results["walking"] = (None, SFB.render(rig6.observation(now_ms=6001)))

    # row 11: all gates open -- and the key name is DATA (remap, spec §9)
    rig7 = Rig()
    rig7.play(7000)
    obs_ready = rig7.observation(now_ms=7000)
    results["climb_ready"] = (obs_ready, SFB.render(obs_ready))
    rig7r = Rig()
    rig7r.chan.bindings.update({"F": CI.CLIMB_REQUEST, "X": CI.LET_GO})
    rig7r.chan.bindings.pop("Space")
    rig7r.chan.bindings.pop("C")
    rig7r.play(7000)
    fb_r = SFB.render(rig7r.observation(now_ms=7000))

    for key, (obs, fb) in results.items():
        want = SFB.PROMPTS[key]
        if key == "climb_ready":   # the ONE interpolated row (live bindings)
            want = want.format(key=obs.climb_key)
        check(f"V1.{key} renders from real inputs with the FROZEN prompt",
              fb.state_key == key and fb.prompt == want,
              f"{fb.prompt!r}")
    check("V1.sources every row cites its source module(s)",
          all(fb.sources["state_key"] == SFB.SOURCE_MAP[key]
              for key, (_, fb) in results.items()),
          "per-row SOURCE_MAP citations")
    check("V1.remap the ready line interpolates the LIVE bindings table "
          "(data, never semantics)", "F" in fb_r.prompt
          and fb_r.prompt == SFB.PROMPTS["climb_ready"].format(key="F"),
          f"{fb_r.prompt!r}")


# ── V2 NO-CAPABILITY-CLAIM FUZZ (falsifier F-a; model-checked, F-c) ───────────
SESSIONS = SF.STATES
FOCUSES = (FP.FOCUSED, FP.BLURRED, FP.DISCONNECTED)
GATES = ("disconnected", "blurred", "paused")
INTENT_KEYS = ("Space", "C")
WALK_KEYS = ("W", "A")


def model_key(o):
    """An INDEPENDENT restatement of the frozen ladder (prereg §2.3); the fuzz
    compares the renderer against this model after every combo."""
    if o["session_state"] != SF.PLAYING:
        return {SF.ATTRACT: "session_menu", SF.PAUSED: "session_paused",
                SF.EXITED: "session_exited"}[o["session_state"]]
    if o["focus_state"] == FP.DISCONNECTED or "disconnected" in o["intent_gates"]:
        return "input_disconnected"
    if o["focus_state"] == FP.BLURRED or "blurred" in o["intent_gates"]:
        return "input_blurred"
    if "paused" in o["intent_gates"]:
        return "intent_paused"
    if o["flash_intent"] is not None:
        return ("climb_sent" if o["flash_intent"] == CI.CLIMB_REQUEST
                else "let_go_sent")
    if o["intent_held"]:
        return "climb_key_held"
    if o["walk_held"] or o["walk_command_live"]:
        return "walking"
    return "climb_ready"


def v2_fuzz():
    print(f"V2 NO-CAPABILITY-CLAIM FUZZ: {FUZZ_COMBOS} seeded adversarial "
          "combos, every rendered string scanned")
    rng = random.Random(SEED)
    n_strings = 0
    n_token_checks = 0
    hits = []
    model_misses = []
    keys_seen = set()

    def all_subsets(rng, items):
        return frozenset(x for x in items if rng.random() < 0.5)

    for i in range(FUZZ_COMBOS):
        now_ms = rng.randint(1000, 10_000_000)
        flash_intent = rng.choice([None, CI.CLIMB_REQUEST, CI.LET_GO,
                                   CI.CLIMB_REQUEST, CI.LET_GO, None])
        flash_age = rng.choice([0, 0, 1, 7, 999, 123456])   # incl. STALE flashes
        ev = None
        if flash_intent is not None:
            ev = CI.IntentEvent(flash_intent, now_ms, max(0, now_ms - flash_age))
        obs = SFB.Observation(
            session_state=rng.choice(SESSIONS),
            focus_state=rng.choice(FOCUSES),
            intent_gates=all_subsets(rng, GATES),     # incl. mis-wired combos
            intent_held=all_subsets(rng, INTENT_KEYS),
            walk_held=all_subsets(rng, WALK_KEYS),
            walk_command_live=rng.random() < 0.5,
            climb_key=rng.choice(["Space", "F"]),
            let_go_key=rng.choice(["C", "X"]),
            flash_event=ev,
            last_drop=(rng.choice([
                {"what": "Space", "at_ms": now_ms - 5,
                 "reason": "dropped_blurred", "gates": ["blurred"]},
                {"what": "C", "at_ms": now_ms - 9,
                 "reason": "dropped_disconnected",
                 "gates": ["blurred", "disconnected", "paused"]},
            ]) if rng.random() < 0.25 else None),
            now_ms=now_ms,
        )
        want_diag = rng.random() < 0.5
        fb = SFB.render(obs, diagnostics=want_diag)
        n_strings += 2 if want_diag else 1
        # F-a: the forbidden-token scan (prompt + optional diagnostics)
        for text in ((fb.prompt, fb.diagnostics) if want_diag
                     else (fb.prompt,)):
            low = text.lower()
            for tok in SFB.FORBIDDEN_CLAIM_TOKENS:
                n_token_checks += 1
                if tok in low:
                    hits.append((i, tok, text))
        # F-c: model-checked ladder + frozen prompt text + valid keys
        o = {"session_state": obs.session_state,
             "focus_state": obs.focus_state,
             "intent_gates": set(obs.intent_gates),
             "flash_intent": flash_intent,
             "intent_held": bool(obs.intent_held),
             "walk_held": bool(obs.walk_held),
             "walk_command_live": obs.walk_command_live}
        want_key = model_key(o)
        want_prompt = (SFB.PROMPTS[want_key] if want_key != "climb_ready"
                       else SFB.PROMPTS["climb_ready"].format(key=obs.climb_key))
        keys_seen.add(fb.state_key)
        if fb.state_key != want_key or fb.prompt != want_prompt:
            model_misses.append((i, want_key, fb.state_key, fb.prompt))

    check(f"V2.a ZERO forbidden claim tokens in {n_strings} rendered strings "
          f"({n_token_checks} token scans)", not hits, f"hits={hits[:4]}")
    check(f"V2.b the ladder is MODEL-CHECKED: state_key and prompt match the "
          f"independent model on all {FUZZ_COMBOS} combos",
          not model_misses, f"misses={model_misses[:3]}")
    check("V2.c every rendered key is in the FROZEN table, and the full table "
          "is reachable (no dead row, no invented row)",
          keys_seen <= set(SFB.STATE_KEYS)
          and keys_seen == set(SFB.STATE_KEYS),
          f"n_keys={len(keys_seen)} of {len(SFB.STATE_KEYS)}")


def v2_adversarial_inputs():
    print("V2.d-g ADVERSARIAL INPUTS: unknown values RAISE, never render")
    base = dict(session_state=SF.PLAYING, focus_state=FP.FOCUSED,
                intent_gates=frozenset(), intent_held=frozenset(),
                walk_held=frozenset(), walk_command_live=False)
    def bad(**over):
        return lambda: SFB.render(SFB.Observation(**{**base, **over}))
    ok = expect("unknown session", bad(session_state="bananas"))
    ok &= expect("unknown focus", bad(focus_state="moist"))
    ok &= expect("unknown gate", bad(intent_gates=frozenset({"limbo"})))
    check("V2.d unknown session/focus/gate values raise UnknownStateError "
          "(refuse-what-you-cannot-name)", ok)

    from types import SimpleNamespace as NS
    ok2 = expect("foreign version flash", bad(
        flash_event=NS(intent_version=2, intent=CI.CLIMB_REQUEST)))
    ok2 &= expect("bool-version flash", bad(
        flash_event=NS(intent_version=True, intent=CI.CLIMB_REQUEST)))
    ok2 &= expect("foreign intent flash", bad(
        flash_event=NS(intent_version=1, intent="climb_grab")))
    check("V2.e a flash event outside v1 (a foreign version, the AMR-1 bool, "
          "or a foreign intent name) RAISES -- U06 is an IntentEvent consumer "
          "and enforces spec §7.1's check-the-version law", ok2)

    ok3 = expect("non-bool walk_live", bad(walk_command_live=1))
    ok3 &= expect("non-str held", bad(intent_held=frozenset({42})))
    ok3 &= expect("empty climb_key", bad(climb_key=""))
    ok3 &= expect("float now_ms", bad(now_ms=1.5))
    ok3 &= expect("bool now_ms", bad(now_ms=True))
    check("V2.f malformed scalars (walk_live, held members, binding names, "
          "stamps) raise -- a renderer that guesses is a renderer that "
          "fabricates", ok3)
    check("V2.g UnknownStateError is a ValueError (the house refusal class)",
          issubclass(SFB.UnknownStateError, ValueError))


# ── V3 U05 INTEGRATION ────────────────────────────────────────────────────────
def v3_u05_integration():
    print("V3 U05 INTEGRATION: intent events/drops surface correctly")
    rig = Rig()
    rig.play(1000)
    r = rig.chan.press("Space", 1001)                 # delivered (AMR-3 path)
    fb = SFB.render(rig.observation(flash=True, now_ms=1001))
    check("V3.a the DELIVERED climb_request renders the brief's exact line "
          "(capability disclaimed, never 'climbing')",
          r == "climb_request" and fb.state_key == "climb_sent"
          and fb.prompt == "Climb intent sent (no climb skill loaded)",
          f"{fb.prompt!r}")
    ev = rig.intent_sink.events[-1]
    fb2 = SFB.render(rig.observation(flash=False, now_ms=1002))
    check("V3.b the same instant WITHOUT the flash surfaces the held edge "
          "(the input fact), never a game state",
          fb2.state_key == "climb_key_held"
          and "held" in fb2.prompt and "climbing" not in fb2.prompt.lower(),
          f"{fb2.prompt!r}")
    check("V3.c the structured record carries the delivered event's canonical "
          "fields verbatim (the C12 chain: same clocks as CommandRecord)",
          fb2.record()["observed"]["flash_event"] is None
          and SFB.render(rig.observation(flash=True, now_ms=1001))
          .record()["observed"]["flash_event"] == ev.canonical_fields())

    rig.chan.release("Space", 1003)
    rig.fp.on_blur(1004)
    rig.chan.on_blur(1004)
    r = rig.chan.press("Space", 1005)                 # dropped, NAMED
    drop = rig.chan.last_trace["drops"][-1]
    fb3 = SFB.render(rig.observation(now_ms=1005))
    fb3d = SFB.render(rig.observation(now_ms=1005, diagnostics_drop=True),
                      diagnostics=True)
    check("V3.d a gated press shows the INPUT-gate line; the named drop is "
          "DIAGNOSTICS-ONLY (default OFF == empty string)",
          r is None and fb3.state_key == "input_blurred"
          and fb3.diagnostics == ""
          and "last_drop=" in fb3d.diagnostics
          and drop["reason"] in fb3d.diagnostics,
          f"diag={fb3d.diagnostics[:80]}...")
    check("V3.e diagnostics stay OPTIONAL engineering language and still "
          "carry zero claim tokens",
          not any(t in fb3d.diagnostics.lower()
                  for t in SFB.FORBIDDEN_CLAIM_TOKENS))


# ── V4 X02/U03 GATING (real session + real focus policy own the line) ─────────
def v4_gating():
    print("V4 X02/U03 GATING: real flow + real policy take over the line")
    rig = Rig()
    fb0 = SFB.render(rig.observation(now_ms=1000))
    check("V4.a attract: the menu line (X02 owns it)", fb0.state_key ==
          "session_menu" and fb0.prompt == "Menu — controls inactive")
    rig.play(1001)
    rig.chan.press("Space", 1002)
    rig.chan.release("Space", 1003)
    rig.flow.key("Escape", 1, 1004)                   # playing -> paused
    fb1 = SFB.render(rig.observation(now_ms=1004))
    check("V4.b real session pause takes the line (even though the intent "
          "channel was not told)", fb1.state_key == "session_paused",
          f"{fb1.prompt!r}")
    rig.chan.on_pause(1005)                           # the ONE harness line
    fb2 = SFB.render(rig.observation(now_ms=1005))
    check("V4.c with the channel told, the line still reads as paused "
          "(honest: either source suffices to close the gate)",
          fb2.state_key == "session_paused")
    rig.flow.key("Return", 1, 1006)                   # resume
    rig.chan.on_resume(1006)
    rig.fp.press("W", 1007)
    rig.fp.tick(1007)
    fb3 = SFB.render(rig.observation(now_ms=1007))
    check("V4.d resume returns the ladder to the WALKING row (the recovery "
          "word appears NOWHERE)",
          fb3.state_key == "walking"
          and "recover" not in fb3.prompt.lower()
          and "recover" not in SFB.render(
              rig.observation(now_ms=1007), diagnostics=True).diagnostics)
    rig.fp.on_blur(1008)
    rig.chan.on_blur(1008)
    fb4 = SFB.render(rig.observation(now_ms=1008))
    check("V4.e real blur takes the line; on_focus returns to walking",
          fb4.state_key == "input_blurred")
    rig.fp.on_focus(1009)
    rig.chan.on_focus(1009)
    fb5 = SFB.render(rig.observation(now_ms=1009))
    check("V4.f focus regained: back to walking (U01's record still live)",
          fb5.state_key == "walking")
    rig.fp.on_disconnect(1010)
    rig.chan.on_disconnect(1010)
    fb6 = SFB.render(rig.observation(now_ms=1010), diagnostics=True)
    check("V4.g disconnect dominates and is named; the gate clears back to "
          "walking on reconnect",
          fb6.state_key == "input_disconnected"
          and rig.fp.on_reconnect(1011) == "focused"
          and rig.chan.on_reconnect(1011) == "ready"
          and SFB.render(rig.observation(now_ms=1011)).state_key == "walking")
    rig.fp.on_blur(1012)                              # MIS-WIRE: channel not told
    fb7 = SFB.render(rig.observation(now_ms=1012), diagnostics=True)
    check("V4.h a cross-source mis-wire (focus blurred, channel open) still "
          "renders the conservative gate line, and the mismatch goes to "
          "DIAGNOSTICS ONLY",
          fb7.state_key == "input_blurred"
          and "wiring" in fb7.diagnostics)


# ── V5 HONESTY BOUNDARIES (the map's five nouns) ──────────────────────────────
def v5_honesty():
    print("V5 HONESTY BOUNDARIES: falling/recovery/support have NO row")
    check("V5.a the map's non-derivable nouns have NO vocabulary row (no "
          "landed module provides them: F04's L1 is offline geometry, W09 "
          "recovery is future, K-series climb is future)",
          not any(w in k for k in SFB.STATE_KEYS
                  for w in ("fall", "recover", "support", "contact")))
    check("V5.b the no-skill disclaimer is MANDATORY in both climb-capability "
          "lines (the brief's honesty example)",
          "no climb skill loaded" in SFB.PROMPTS["climb_sent"]
          and "no climb skill loaded" in SFB.PROMPTS["climb_ready"])
    check("V5.c the held-edge line is an INPUT fact (never 'holding', never "
          "'climbing')",
          SFB.PROMPTS["climb_key_held"] == "Climb key held (ask already sent)")
    check("V5.d the unavailable-support noun maps to INPUT-gate language "
          "('keys dropped'), never a support/contact claim",
          "keys dropped" in SFB.PROMPTS["input_disconnected"]
          and "keys dropped" in SFB.PROMPTS["input_blurred"]
          and not any(t in SFB.PROMPTS[k].lower()
                      for k in SFB.STATE_KEYS
                      for t in ("support", "contact", "branch", "trunk")))
    rig = Rig()
    rig.play(1000)
    fb = SFB.render(rig.observation(now_ms=1000))
    blob = json.dumps(fb.record())
    back = json.loads(blob)
    check("V5.e the structured record JSON round-trips (state_key, prompt, "
          "sources, observed)",
          back["state_key"] == "climb_ready"
          and back["sources"]["state_key"] == list(SFB.SOURCE_MAP["climb_ready"])
          and back["sources"]["session_state"].startswith("x02:"),
          f"keys={sorted(back)}")


def main():
    print("state_feedback_tests -- M-U05b/U06 falsifiers "
          "(prereg: agents/U05b_amendments_U06/PREREGISTRATION.md §2)")
    v1_derivability()
    v2_fuzz()
    v2_adversarial_inputs()
    v3_u05_integration()
    v4_gating()
    v5_honesty()
    print()
    if FAILURES:
        print(f"RESULT: FAIL ({len(FAILURES)} falsifier checks fired)")
        for f in FAILURES:
            print(f"  FIRED: {f}")
        return 1
    print("RESULT: GREEN -- all U06 falsifier checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
