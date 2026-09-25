"""resource_ledger.py -- I-R05: ownership-scoped resource accounting for
repeated session / restart teardown.

Card I-R05-RESOURCE-LEDGER (planning id R05), attempt
080ba14585ce405e9b7d0ae87632a8af, branch-6, pinned base
9afbddcd90164b5544a16fd0bc72278d985eb6e3.  PREREGISTRATION.md (Rule 0:
statement / prediction / falsifier) was frozen BEFORE this file was written.

THE GAP THIS FILLS (derived from the pinned sources, read-only):

  * session_flow.py (_transition, :310-360) fires ONE teardown callable on
    exit (:343-349) and restarts through World.boot() (:327-340) -- neither
    transition carries any per-resource ownership record, so a leak or an
    owner collision can pass silently.
  * forest_loader.py ForestScene (the existing teardown ownership API) keeps
    a NAME-keyed registry ``self._resources`` (:358-362) with no owner and no
    session generation; teardown() (:380-405) releases in reverse-load order
    and refuses f08_teardown_leak only when a release RAISES -- a resource
    nobody releases is invisible.

This module adds the missing accounting as a CHECKER, not a rewriter:
acquire/release events are recorded against a (SESSION GENERATION, OWNER,
RESOURCE ID) key and every violation is a NAMED failure.  It discovers no OS
processes, ends nothing, launches nothing and probes no memory: the
only success criterion for a cycle is zero accounting failures plus the
EXPLICIT ceilings the caller passes in.  High free RAM is not consulted --
it does not exist as an input.

THE LAW (each falsifier from PREREGISTRATION.md enforced by construction):

  F1  an unrelated owner cannot release another owner's resource
      (ledger_wrong_owner: the claim's owner must equal the live record's
      owner; the resource STAYS LIVE after a refused release).
  F2  a stale generation cannot close a current resource
      (ledger_wrong_generation: the claim's generation must equal the live
      record's generation; a stale claim never touches the live record).
  F3  a leaked resource can never pass a cycle
      (ledger_live_at_close is recorded at generation close for every still
      live record of that generation; a summary containing a
      live_at_close failure can NEVER pass, regardless of ceilings).

Named failure classes (the five of the card, plus loud refusals):

  ledger_duplicate_acquire  an id acquired while already live
  ledger_unknown_release    a release claim for an id that is not live
  ledger_wrong_generation   a release claim whose generation is not the
                            live record's generation
  ledger_wrong_owner        a release claim whose owner is not the live
                            record's owner
  ledger_live_at_close      a record of a closed generation still live

Release-claim refusal precedence is FIXED (checked in this order):
unknown-release, then wrong-generation, then wrong-owner -- so every refusal
is deterministic even when a claim is wrong in several ways at once.  A
refused release changes NO state except the failure event itself.

Identity and generations: a resource_id is UNIQUE among LIVE records.  The
same id may be re-acquired in a later generation once it is no longer live
(the repeated session/restart case).  A still-live id re-acquired in any
generation is a duplicate-acquire -- two live things answering to one id is
exactly what this ledger exists to catch.  close_generation(g) ABANDONS the
generation's leaks (named live_at_close each) so a later generation may
reuse the ids honestly; the failures remain in the ledger permanently.
close() closes ALL generations at once.  Releasing a genuinely old record
by its TRUE generation is legal; only mismatched claims are failures.

Ceilings (caller data ONLY -- never probed, never defaulted from the
machine): a dict with any subset of

  max_live        max simultaneously-live records in scope
  max_acquires    max successful acquires recorded in scope
  max_releases    max successful releases recorded in scope
  max_failures    max NON-leak accounting failures tolerated in scope
                  (live_at_close is never tolerable and sits outside this
                  budget; unknown keys are refused, not ignored)

A cycle summary passes iff: zero ceiling violations AND zero live_at_close
failures in scope AND non-leak failures within the failure budget (zero when
no budget is given).  Every count is computed from the ledger's own events.

Determinism: all times are INJECTED integer milliseconds (now_ms) or None --
never a wall clock, matching session_flow's injected-time law.  Iteration
orders are fixed (events by sequence, live and failures sorted), so two
ledgers fed the same sequence produce byte-identical canonical JSON.

Bounded: the event log holds at most max_events events (default 10000);
overflow raises ledger_full rather than growing without bound.  Stdlib only,
headless, CPU-only, Python 3.11+.

Selftest:  python resource_ledger.py selftest
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass

__all__ = [
    "SCHEMA",
    "DUPLICATE_ACQUIRE", "UNKNOWN_RELEASE", "WRONG_GENERATION",
    "WRONG_OWNER", "LIVE_AT_CLOSE", "FAILURE_CODES",
    "CEILING_KEYS", "LedgerRefusal", "AcquireRecord", "ResourceLedger",
    "canonical_json",
]

SCHEMA = "chimera.monkey_campaign.resource_ledger.v1"

# ── the five named failure classes (the card's vocabulary) ──────────────────────
DUPLICATE_ACQUIRE = "ledger_duplicate_acquire"
UNKNOWN_RELEASE = "ledger_unknown_release"
WRONG_GENERATION = "ledger_wrong_generation"
WRONG_OWNER = "ledger_wrong_owner"
LIVE_AT_CLOSE = "ledger_live_at_close"
FAILURE_CODES = (DUPLICATE_ACQUIRE, UNKNOWN_RELEASE, WRONG_GENERATION,
                 WRONG_OWNER, LIVE_AT_CLOSE)

# caller-provided ceiling vocabulary (ANY other key is refused, not ignored)
CEILING_KEYS = ("max_live", "max_acquires", "max_releases", "max_failures")

DEFAULT_MAX_EVENTS = 10000


class LedgerRefusal(ValueError):
    """A loud, named refusal (house style, forest_loader.Refusal shape).

    ``code`` names the refusal, ``detail`` carries the specifics, ``identity``
    holds the exact offending inputs.  Refusals are PROGRAMMER errors (bad
    argument shapes, full ledger, use after close); the five accounting
    failure classes above are not refusals -- they are recorded evidence.
    """

    def __init__(self, code, detail="", **identity):
        self.code, self.detail = code, str(detail)
        self.identity = dict(identity)
        super().__init__(code + (": " + self.detail if detail else ""))


@dataclass(frozen=True)
class AcquireRecord:
    """The live identity of one acquired resource."""
    resource_id: str
    owner: str
    generation: int
    seq: int                 # ledger sequence of the acquiring event
    now_ms: int | None       # INJECTED time, never a wall clock


def _check_name(kind, value):
    if not isinstance(value, str) or not value:
        raise LedgerRefusal("ledger_bad_id", "%s must be a non-empty str"
                            % kind, field=kind, got=repr(value))
    return value


def _check_generation(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LedgerRefusal("ledger_bad_generation",
                            "generation must be an int >= 0",
                            got=repr(value))
    return value


def _check_now_ms(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LedgerRefusal("ledger_bad_time",
                            "now_ms must be None or an injected int >= 0 "
                            "(never a wall clock)", got=repr(value))
    return value


class ResourceLedger:
    """A bounded event ledger for repeated session/restart teardown.

    Usage (the repeated-cycle shape the card demands -- all times injected):

        led = ResourceLedger()
        led.acquire("engine:9347", owner="session", generation=0, now_ms=0)
        led.release("engine:9347", owner="session", generation=0, now_ms=10)
        led.close_generation(0, now_ms=11)          # clean: zero live
        led.acquire("engine:9348", owner="session", generation=1, now_ms=12)
        doc = led.close_generation(1, ceilings={"max_live": 4}, now_ms=20)
        assert doc["passed"]

    The public mutators are exactly acquire/release/close_generation/close;
    reads are live()/events()/failures()/summary().  The ledger never
    touches the world: it records and judges claims, nothing else.
    """

    def __init__(self, max_events=DEFAULT_MAX_EVENTS):
        if (isinstance(max_events, bool) or not isinstance(max_events, int)
                or max_events < 1):
            raise LedgerRefusal("ledger_bad_bound",
                                "max_events must be an int >= 1",
                                got=repr(max_events))
        self._max_events = max_events
        self._events = []            # bounded event log, seq order
        self._live = {}              # resource_id -> AcquireRecord
        self._failures = []          # subset of events, seq order
        self._closed_generations = set()
        self._closed = False

    # ── shape checks ─────────────────────────────────────────────────────────
    def _check_open(self):
        if self._closed:
            raise LedgerRefusal("ledger_closed",
                                "the ledger is finally closed; open a new one")

    def _record(self, event):
        if len(self._events) >= self._max_events:
            raise LedgerRefusal("ledger_full",
                                "event bound reached (%d); a full ledger is "
                                "a loud stop, never a silent roll"
                                % self._max_events)
        event["seq"] = len(self._events)
        self._events.append(event)
        if event.get("is_failure"):
            self._failures.append(event)
        return event

    @staticmethod
    def _failure(kind, resource_id, owner, generation, now_ms, detail):
        return {"kind": "failure", "code": kind, "resource_id": resource_id,
                "owner": owner, "generation": generation, "now_ms": now_ms,
                "detail": detail, "is_failure": True}

    # ── the mutators ─────────────────────────────────────────────────────────
    def acquire(self, resource_id, owner, generation, now_ms=None):
        """Record an acquire claim.  Refused (named) when the id is already
        live -- the FIRST record keeps the slot; the duplicate attempt is
        evidence only."""
        self._check_open()
        resource_id = _check_name("resource_id", resource_id)
        owner = _check_name("owner", owner)
        generation = _check_generation(generation)
        now_ms = _check_now_ms(now_ms)
        live = self._live.get(resource_id)
        if live is not None:
            event = self._failure(
                DUPLICATE_ACQUIRE, resource_id, owner, generation, now_ms,
                "already live as gen %d owner %r (seq %d)"
                % (live.generation, live.owner, live.seq))
            return self._record(event)
        record = AcquireRecord(resource_id, owner, generation,
                               len(self._events), now_ms)
        self._record({"kind": "acquire", "resource_id": resource_id,
                      "owner": owner, "generation": generation,
                      "now_ms": now_ms, "is_failure": False})
        self._live[resource_id] = record
        return dict(self._events[-1])

    def release(self, resource_id, owner, generation, now_ms=None):
        """Record a release claim.  Refusal precedence (fixed, documented in
        the module docstring): unknown-release, wrong-generation,
        wrong-owner.  A refused release leaves the live record UNTOUCHED."""
        self._check_open()
        resource_id = _check_name("resource_id", resource_id)
        owner = _check_name("owner", owner)
        generation = _check_generation(generation)
        now_ms = _check_now_ms(now_ms)
        live = self._live.get(resource_id)
        if live is None:
            return self._record(self._failure(
                UNKNOWN_RELEASE, resource_id, owner, generation, now_ms,
                "no live record for this id"))
        if live.generation != generation:
            return self._record(self._failure(
                WRONG_GENERATION, resource_id, owner, generation, now_ms,
                "live record is generation %d (owner %r); a stale "
                "generation never closes a current resource"
                % (live.generation, live.owner)))
        if live.owner != owner:
            return self._record(self._failure(
                WRONG_OWNER, resource_id, owner, generation, now_ms,
                "owned by %r; an unrelated owner cannot release it"
                % (live.owner,)))
        self._record({"kind": "release", "resource_id": resource_id,
                      "owner": owner, "generation": generation,
                      "now_ms": now_ms, "is_failure": False})
        del self._live[resource_id]
        return dict(self._events[-1])

    def close_generation(self, generation, ceilings=None, now_ms=None):
        """Close one session generation: every still-live record OF THAT
        generation is a named live_at_close leak and is ABANDONED (the
        session that owned it has ended; the failure is permanent).  Other
        generations' live records are untouched.  Returns the generation's
        cycle summary, judged against the caller-provided ``ceilings``."""
        self._check_open()
        generation = _check_generation(generation)
        now_ms = _check_now_ms(now_ms)
        if generation in self._closed_generations:
            raise LedgerRefusal("ledger_generation_closed",
                                "generation %d already closed" % generation,
                                generation=generation)
        self._closed_generations.add(generation)
        leaked = sorted((rec for rec in self._live.values()
                         if rec.generation == generation),
                        key=lambda r: (r.resource_id,))
        for rec in leaked:
            self._record(self._failure(
                LIVE_AT_CLOSE, rec.resource_id, rec.owner, generation,
                now_ms, "still live at generation close (acquired seq %d)"
                % rec.seq))
            del self._live[rec.resource_id]
        self._record({"kind": "generation_close", "resource_id": None,
                      "owner": None, "generation": generation,
                      "now_ms": now_ms, "is_failure": False,
                      "leaked": [r.resource_id for r in leaked]})
        return self.summary(ceilings=ceilings, generation=generation)

    def close(self, ceilings=None, now_ms=None):
        """Final close: abandons every still-live record of EVERY open
        generation (each a named live_at_close) and seals the ledger.
        Further acquire/release raise ledger_closed.  Returns the
        whole-ledger summary, judged against ``ceilings``."""
        self._check_open()
        now_ms = _check_now_ms(now_ms)
        for generation in sorted(self._closed_generations
                                 | {r.generation for r in
                                    self._live.values()}):
            if generation not in self._closed_generations:
                self.close_generation(generation, now_ms=now_ms)
        self._closed = True
        self._record({"kind": "close", "resource_id": None, "owner": None,
                      "generation": None, "now_ms": now_ms,
                      "is_failure": False})
        return self.summary(ceilings=ceilings)

    # ── reads ────────────────────────────────────────────────────────────────
    def live(self, generation=None):
        """The live records, sorted (deterministic); optionally scoped to
        one generation."""
        recs = sorted(self._live.values(),
                      key=lambda r: (r.generation, r.resource_id))
        if generation is None:
            return list(recs)
        return [r for r in recs if r.generation == generation]

    def events(self):
        return tuple(self._events)

    def failures(self):
        return tuple(self._failures)

    @property
    def closed(self):
        return self._closed

    # ── the judge ────────────────────────────────────────────────────────────
    def summary(self, ceilings=None, generation=None):
        """Judge a cycle against EXPLICIT caller-provided ceilings.

        Scope: generation=None judges the whole ledger; an int judges only
        that generation's events.  ``ceilings`` (caller data ONLY) may carry
        any subset of CEILING_KEYS; an unknown key is refused (a typo must
        never silently disable a limit).  passed = no ceiling violation AND
        no live_at_close in scope AND non-leak failures within the failure
        budget (zero when no budget given).  No field of this document is
        derived from the machine: there is no memory probe anywhere.
        """
        if ceilings is None:
            ceilings = {}
        if not isinstance(ceilings, dict):
            raise LedgerRefusal("ledger_bad_ceiling",
                                "ceilings must be a dict keyed from "
                                "CEILING_KEYS", got=repr(ceilings))
        limits = {}
        for key, value in ceilings.items():
            if key not in CEILING_KEYS:
                raise LedgerRefusal("ledger_bad_ceiling",
                                    "%r is not a ceiling key (known: %s)"
                                    % (key, ", ".join(CEILING_KEYS)),
                                    key=key)
            if isinstance(value, bool) or not isinstance(value, int) \
                    or value < 0:
                raise LedgerRefusal("ledger_bad_ceiling",
                                    "ceiling %r must be an int >= 0" % key,
                                    key=key, got=repr(value))
            limits[key] = value

        evs = [e for e in self._events
               if generation is None or e["generation"] == generation]
        scope_failures = [e for e in evs if e["is_failure"]]
        leak_failures = [e for e in scope_failures
                         if e["code"] == LIVE_AT_CLOSE]
        other_failures = [e for e in scope_failures
                          if e["code"] != LIVE_AT_CLOSE]
        acquires = sum(1 for e in evs if e["kind"] == "acquire")
        releases = sum(1 for e in evs if e["kind"] == "release")
        live_now = len(self.live(generation=generation))

        violations = []
        for key, measured in (("max_live", live_now),
                              ("max_acquires", acquires),
                              ("max_releases", releases),
                              ("max_failures", len(other_failures))):
            if key in limits and measured > limits[key]:
                violations.append({"ceiling": key, "measured": measured,
                                   "limit": limits[key]})

        failure_budget = limits.get("max_failures", 0)
        passed = (not violations
                  and not leak_failures
                  and len(other_failures) <= failure_budget)
        return {
            "schema": SCHEMA,
            "scope_generation": generation,
            "ledger_closed": self._closed,
            "acquires": acquires,
            "releases": releases,
            "live_now": live_now,
            "live_ids": [r.resource_id for r in self.live(generation)],
            "failures_total": len(scope_failures),
            "failures_by_code": {code: sum(1 for e in scope_failures
                                           if e["code"] == code)
                                 for code in FAILURE_CODES},
            "failure_details": [{k: e[k] for k in
                                 ("seq", "code", "resource_id", "owner",
                                  "generation", "detail")} for e in
                                scope_failures],
            "ceilings": dict(limits),
            "ceiling_violations": violations,
            "passed": passed,
        }

    def to_json(self, ceilings=None, generation=None):
        """The canonical JSON bytes of a summary (house canonical form:
        sorted keys, tight separators) -- byte-identical for identical
        histories."""
        return canonical_json(self.summary(ceilings=ceilings,
                                           generation=generation))


def canonical_json(value):
    """House canonical bytes (forest_loader.canonical shape, stdlib only)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


# ── the built-in selftest (deterministic, bounded, no I/O beyond stdout) ────────
def _selftest():
    led = ResourceLedger()
    ok = True
    # clean cycle 0
    led.acquire("engine:9347", "session", 0, now_ms=0)
    led.acquire("scene:forest", "session", 0, now_ms=1)
    led.release("scene:forest", "session", 0, now_ms=2)
    led.release("engine:9347", "session", 0, now_ms=3)
    ok &= led.close_generation(0, now_ms=4)["passed"]
    # clean cycle 1: same ids, new generation -- reuse is legal
    led.acquire("engine:9350", "session", 1, now_ms=5)
    led.release("engine:9350", "session", 1, now_ms=6)
    ok &= led.close_generation(1, now_ms=7)["passed"]
    # leak cycle 2: F3 -- a leak must fail the cycle
    led.acquire("engine:9351", "session", 2, now_ms=8)
    leak_doc = led.close_generation(2, now_ms=9)
    ok &= not leak_doc["passed"]
    ok &= leak_doc["failures_by_code"][LIVE_AT_CLOSE] == 1
    # owner isolation: F1 -- the session cannot release the operator's id
    led.acquire("operator:notebook", "operator", 3, now_ms=10)
    bad = led.release("operator:notebook", "session", 3, now_ms=11)
    ok &= bad["code"] == WRONG_OWNER
    ok &= len(led.live(3)) == 1
    # stale generation: F2 -- gen 2's claim cannot close gen 3's resource
    led.acquire("engine:9352", "session", 3, now_ms=12)
    stale = led.release("engine:9352", "session", 2, now_ms=13)
    ok &= stale["code"] == WRONG_GENERATION
    ok &= len(led.live(3)) == 2
    final = led.close(now_ms=14)
    ok &= not final["passed"]          # the gen-3 resources die live_at_close
    print(canonical_json({"schema": SCHEMA, "selftest": "pass" if ok
                          else "FAIL"}).decode("ascii"))
    return 0 if ok else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "selftest":
        return _selftest()
    raise LedgerRefusal("ledger_cli_verb", argv)


if __name__ == "__main__":
    sys.exit(main())
