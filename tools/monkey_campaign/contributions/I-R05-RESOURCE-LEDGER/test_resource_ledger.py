"""test_resource_ledger.py -- I-R05 tests (stdlib unittest, bounded).

Card I-R05-RESOURCE-LEDGER, attempt 080ba14585ce405e9b7d0ae87632a8af,
branch-6, pinned base 9afbddcd90164b5544a16fd0bc72278d985eb6e3.

Every scenario here drives the ResourceLedger with INJECTED integer times
and caller-provided data only: no OS processes, no memory probing, no wall
clock, no I/O beyond stdout.  These traces are TEST FIXTURES -- evidence of
what the module does, never runtime proof about a live session.

Run:  python -B test_resource_ledger.py        (well under 120 s; measured
runtime is printed by main and recorded in receipt.json)
"""
from __future__ import annotations

import time
import unittest

from resource_ledger import (
    SCHEMA,
    DUPLICATE_ACQUIRE, UNKNOWN_RELEASE, WRONG_GENERATION, WRONG_OWNER,
    LIVE_AT_CLOSE, FAILURE_CODES,
    CEILING_KEYS,
    LedgerRefusal,
    ResourceLedger,
    canonical_json,
)


class ResourceLedgerTestBase(unittest.TestCase):
    """A fresh ledger per test; injected times only."""

    def setUp(self):
        self.led = ResourceLedger()


class CleanCyclesTests(ResourceLedgerTestBase):
    """The repeated session/restart shape: clean cycles must pass."""

    def test_repeated_clean_cycles_pass(self):
        """Three full generations, every acquire released by name: each
        close_generation passes and the ledger carries zero failures."""
        for gen in range(3):
            self.led.acquire("engine:port", "session", gen, now_ms=gen * 10)
            self.led.acquire("scene:forest", "session", gen, now_ms=gen * 10 + 1)
            self.led.release("scene:forest", "session", gen,
                             now_ms=gen * 10 + 2)
            self.led.release("engine:port", "session", gen,
                             now_ms=gen * 10 + 3)
            doc = self.led.close_generation(gen, now_ms=gen * 10 + 4)
            self.assertTrue(doc["passed"], doc)
            self.assertEqual(doc["live_now"], 0)
            self.assertEqual(doc["failures_total"], 0)
            self.assertEqual(doc["acquires"], 2)
            self.assertEqual(doc["releases"], 2)
        self.assertEqual(self.led.failures(), ())

    def test_empty_ledger_summary_and_close(self):
        """An empty ledger is a valid clean cycle: zero counts, passing."""
        doc = self.led.summary()
        self.assertTrue(doc["passed"])
        self.assertEqual(doc["acquires"], 0)
        self.assertEqual(doc["releases"], 0)
        self.assertEqual(doc["live_now"], 0)
        self.assertEqual(doc["failures_total"], 0)
        self.assertEqual(doc["schema"], SCHEMA)
        closed = self.led.close(now_ms=0)
        self.assertTrue(closed["passed"])
        self.assertTrue(self.led.closed)

    def test_reused_resource_ids_across_generations_are_legal(self):
        """The SAME id released in gen 0 may be re-acquired in gen 1 -- the
        repeated-restart case.  No duplicate, no failure."""
        self.led.acquire("engine:9347", "session", 0, now_ms=0)
        self.led.release("engine:9347", "session", 0, now_ms=1)
        self.led.close_generation(0, now_ms=2)
        self.led.acquire("engine:9347", "session", 1, now_ms=3)
        self.assertEqual(len(self.led.live(1)), 1)
        self.led.release("engine:9347", "session", 1, now_ms=4)
        doc = self.led.close_generation(1, now_ms=5)
        self.assertTrue(doc["passed"], doc)
        self.assertEqual(doc["failures_by_code"][DUPLICATE_ACQUIRE], 0)


class LeakTests(ResourceLedgerTestBase):
    """F3: a leaked resource can never pass a cycle."""

    def test_leak_fails_generation_close(self):
        self.led.acquire("engine:9347", "session", 0, now_ms=0)
        self.led.acquire("scene:forest", "session", 0, now_ms=1)
        self.led.release("scene:forest", "session", 0, now_ms=2)
        doc = self.led.close_generation(0, now_ms=3)
        self.assertFalse(doc["passed"])
        self.assertEqual(doc["failures_by_code"][LIVE_AT_CLOSE], 1)
        self.assertEqual(doc["live_ids"], [])
        self.assertEqual(doc["failure_details"][0]["resource_id"],
                         "engine:9347")
        # the leak stays in the ledger permanently, even though abandoned
        self.assertEqual(self.led.failures()[0]["code"], LIVE_AT_CLOSE)

    def test_leak_fails_whole_ledger_summary_too(self):
        """The leak is visible from the whole-ledger scope, not just its
        generation scope."""
        self.led.acquire("engine:1", "session", 0, now_ms=0)
        self.led.close_generation(0, now_ms=1)
        whole = self.led.summary()
        self.assertFalse(whole["passed"])
        self.assertEqual(whole["failures_by_code"][LIVE_AT_CLOSE], 1)

    def test_leak_cannot_be_laundered_by_a_failure_budget(self):
        """A caller-provided max_failures budget may admit accounting
        failures, but live_at_close is NEVER tolerable: a leaking cycle
        still fails with a generous budget."""
        self.led.acquire("engine:1", "session", 0, now_ms=0)
        doc = self.led.close_generation(0, ceilings={"max_failures": 99},
                                        now_ms=1)
        self.assertFalse(doc["passed"])
        self.assertEqual(doc["failures_by_code"][LIVE_AT_CLOSE], 1)

    def test_final_close_reports_every_open_generation_leak(self):
        self.led.acquire("engine:1", "session", 0, now_ms=0)
        self.led.acquire("engine:2", "session", 1, now_ms=1)
        self.led.acquire("engine:3", "session", 2, now_ms=2)
        self.led.release("engine:2", "session", 1, now_ms=3)
        doc = self.led.close(now_ms=4)
        self.assertFalse(doc["passed"])
        self.assertEqual(doc["failures_by_code"][LIVE_AT_CLOSE], 2)
        leaked = sorted(e["resource_id"]
                        for e in doc["failure_details"])
        self.assertEqual(leaked, ["engine:1", "engine:3"])
        self.assertTrue(self.led.closed)

    def test_generation_close_is_idempotent_guarded(self):
        """Closing the same generation twice is a loud refusal (a second
        teardown is never claimed twice -- session_flow's terminal law)."""
        self.led.close_generation(0, now_ms=0)
        with self.assertRaises(LedgerRefusal) as ctx:
            self.led.close_generation(0, now_ms=1)
        self.assertEqual(ctx.exception.code, "ledger_generation_closed")


class DuplicateAcquireTests(ResourceLedgerTestBase):
    def test_duplicate_acquire_refused_and_named(self):
        self.led.acquire("engine:9347", "session", 0, now_ms=0)
        event = self.led.acquire("engine:9347", "session", 0, now_ms=1)
        self.assertEqual(event["kind"], "failure")
        self.assertEqual(event["code"], DUPLICATE_ACQUIRE)
        # exactly ONE live record survives -- the first owner keeps the slot
        self.assertEqual(len(self.led.live(0)), 1)
        self.assertEqual(self.led.live(0)[0].owner, "session")
        doc = self.led.summary()
        self.assertFalse(doc["passed"])
        # one release closes the slot; the duplicate attempt created nothing
        self.led.release("engine:9347", "session", 0, now_ms=2)
        self.assertEqual(self.led.live(0), [])

    def test_duplicate_by_a_different_owner_is_still_duplicate(self):
        """The uniqueness law does not depend on who attempts the second
        acquire: one id, one live record."""
        self.led.acquire("gpu:solo", "session", 0, now_ms=0)
        event = self.led.acquire("gpu:solo", "operator", 0, now_ms=1)
        self.assertEqual(event["code"], DUPLICATE_ACQUIRE)
        self.assertEqual(self.led.live(0)[0].owner, "session")


class UnknownReleaseTests(ResourceLedgerTestBase):
    def test_unknown_release_named_and_stateless(self):
        event = self.led.release("engine:never", "session", 0, now_ms=0)
        self.assertEqual(event["code"], UNKNOWN_RELEASE)
        self.assertEqual(self.led.live(0), [])

    def test_release_after_abandon_is_unknown(self):
        """A leak abandoned at generation close is gone: a later release
        claim on it is unknown-release, not a resurrection."""
        self.led.acquire("engine:1", "session", 0, now_ms=0)
        self.led.close_generation(0, now_ms=1)
        event = self.led.release("engine:1", "session", 0, now_ms=2)
        self.assertEqual(event["code"], UNKNOWN_RELEASE)

    def test_release_on_empty_ledger_is_unknown(self):
        event = self.led.release("anything", "session", 0, now_ms=0)
        self.assertEqual(event["code"], UNKNOWN_RELEASE)


class GenerationTests(ResourceLedgerTestBase):
    """F2: stale generations must not close current resources."""

    def test_wrong_generation_release_refused(self):
        self.led.acquire("engine:9347", "session", 2, now_ms=0)
        event = self.led.release("engine:9347", "session", 1, now_ms=1)
        self.assertEqual(event["code"], WRONG_GENERATION)
        # THE RESOURCE STAYS LIVE -- the stale claim touched nothing
        self.assertEqual(len(self.led.live(2)), 1)
        doc = self.led.summary()
        self.assertFalse(doc["passed"])
        self.assertEqual(doc["failures_by_code"][WRONG_GENERATION], 1)

    def test_stale_claim_cannot_close_a_reacquired_current_resource(self):
        """The exact falsifier shape: 'engine' lived in gen 0, was re-acquired
        in gen 1, and a gen-0 claim arrives -- gen 1's record must survive."""
        self.led.acquire("engine", "session", 0, now_ms=0)
        self.led.release("engine", "session", 0, now_ms=1)
        self.led.close_generation(0, now_ms=2)
        self.led.acquire("engine", "session", 1, now_ms=3)
        stale = self.led.release("engine", "session", 0, now_ms=4)
        self.assertEqual(stale["code"], WRONG_GENERATION)
        self.assertEqual(len(self.led.live(1)), 1)
        # and the honest claim still works
        ok = self.led.release("engine", "session", 1, now_ms=5)
        self.assertEqual(ok["kind"], "release")
        self.assertEqual(self.led.live(1), [])

    def test_old_record_released_by_its_true_generation_is_legal(self):
        """A genuinely old record (its generation never closed) released by
        its TRUE generation is a legal late release, not an offense."""
        self.led.acquire("engine:old", "session", 0, now_ms=0)
        self.led.acquire("engine:new", "session", 1, now_ms=1)
        event = self.led.release("engine:old", "session", 0, now_ms=2)
        self.assertEqual(event["kind"], "release")
        self.assertEqual(len(self.led.live()), 1)


class OwnerTests(ResourceLedgerTestBase):
    """F1: an unrelated owner cannot release another owner's resource."""

    def test_operator_resource_not_releasable_by_session(self):
        self.led.acquire("operator:notebook", "operator", 0, now_ms=0)
        event = self.led.release("operator:notebook", "session", 0,
                                 now_ms=1)
        self.assertEqual(event["code"], WRONG_OWNER)
        # the operator's resource STAYS LIVE and OWNED
        live = self.led.live(0)
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0].owner, "operator")
        doc = self.led.summary()
        self.assertFalse(doc["passed"])
        self.assertEqual(doc["failures_by_code"][WRONG_OWNER], 1)

    def test_owner_still_releases_their_own_resource(self):
        self.led.acquire("operator:notebook", "operator", 0, now_ms=0)
        ok = self.led.release("operator:notebook", "operator", 0, now_ms=1)
        self.assertEqual(ok["kind"], "release")
        self.assertEqual(self.led.live(0), [])

    def test_wrong_owner_and_wrong_generation_precedence(self):
        """Precedence is fixed and documented: wrong-generation is reported
        when BOTH the generation and the owner of the claim are wrong."""
        self.led.acquire("engine:1", "session", 1, now_ms=0)
        event = self.led.release("engine:1", "operator", 0, now_ms=1)
        self.assertEqual(event["code"], WRONG_GENERATION)


class CeilingTests(ResourceLedgerTestBase):
    """Ceilings are caller data ONLY; the ledger probes nothing."""

    def test_max_live_ceiling_from_caller_data(self):
        self.led.acquire("engine:1", "session", 0, now_ms=0)
        within = self.led.summary(ceilings={"max_live": 1})
        self.assertTrue(within["passed"])
        self.led.acquire("engine:2", "session", 0, now_ms=1)
        over = self.led.summary(ceilings={"max_live": 1})
        self.assertFalse(over["passed"])
        self.assertEqual(over["ceiling_violations"],
                         [{"ceiling": "max_live", "measured": 2, "limit": 1}])
        # zero accounting failures -- the failure is PURELY the ceiling
        self.assertEqual(over["failures_total"], 0)

    def test_max_acquires_and_max_releases_ceilings(self):
        self.led.acquire("a", "session", 0, now_ms=0)
        self.led.acquire("b", "session", 0, now_ms=1)
        self.led.release("b", "session", 0, now_ms=2)
        doc = self.led.summary(ceilings={"max_acquires": 1,
                                         "max_releases": 5})
        self.assertFalse(doc["passed"])
        codes = [v["ceiling"] for v in doc["ceiling_violations"]]
        self.assertEqual(codes, ["max_acquires"])
        doc = self.led.summary(ceilings={"max_acquires": 9,
                                         "max_releases": 0})
        self.assertFalse(doc["passed"])
        self.assertEqual([v["ceiling"] for v in doc["ceiling_violations"]],
                         ["max_releases"])

    def test_max_failures_budget_admits_only_non_leak_failures(self):
        self.led.acquire("x", "session", 0, now_ms=0)
        self.led.release("ghost", "session", 0, now_ms=1)   # one unknown
        doc = self.led.summary(ceilings={"max_failures": 1})
        self.assertTrue(doc["passed"], doc)
        tight = self.led.summary(ceilings={"max_failures": 0})
        self.assertFalse(tight["passed"])

    def test_generation_scoped_summary_ignores_other_generations(self):
        self.led.acquire("engine:1", "session", 0, now_ms=0)
        self.led.release("engine:1", "session", 0, now_ms=1)
        self.led.close_generation(0, now_ms=2)
        self.led.acquire("engine:2", "session", 1, now_ms=3)
        gen0 = self.led.summary(ceilings={"max_live": 0}, generation=0)
        self.assertTrue(gen0["passed"], gen0)
        gen1 = self.led.summary(ceilings={"max_live": 0}, generation=1)
        self.assertFalse(gen1["passed"])
        self.assertEqual(gen1["ceiling_violations"][0]["measured"], 1)

    def test_unknown_ceiling_key_is_refused_not_ignored(self):
        with self.assertRaises(LedgerRefusal) as ctx:
            self.led.summary(ceilings={"max_liv": 1})   # a typo must be loud
        self.assertEqual(ctx.exception.code, "ledger_bad_ceiling")

    def test_bad_ceiling_values_are_refused(self):
        for bad in (-1, True, 1.5, "3"):
            with self.assertRaises(LedgerRefusal) as ctx:
                self.led.summary(ceilings={"max_live": bad})
            self.assertEqual(ctx.exception.code, "ledger_bad_ceiling")

    def test_ceilings_none_judges_failures_only(self):
        """With NO ceilings the zero-failure law still holds: ceilings add
        resource limits; they are never required to catch a failure."""
        self.led.acquire("engine:1", "session", 0, now_ms=0)
        self.led.release("engine:1", "session", 0, now_ms=1)
        self.led.release("engine:1", "session", 0, now_ms=2)  # unknown
        self.assertTrue(self.led.summary(ceilings=None)["passed"] is False)


class RefusalTests(ResourceLedgerTestBase):
    """Loud refusals for programmer errors (never silent acceptance)."""

    def test_bad_identifiers(self):
        for kwargs in ({"resource_id": "", "owner": "s", "generation": 0},
                       {"resource_id": "e", "owner": "", "generation": 0},
                       {"resource_id": 7, "owner": "s", "generation": 0},
                       {"resource_id": "e", "owner": None, "generation": 0}):
            with self.assertRaises(LedgerRefusal) as ctx:
                self.led.acquire(now_ms=0, **kwargs)
            self.assertEqual(ctx.exception.code, "ledger_bad_id")

    def test_bad_generation(self):
        for bad in (-1, True, 0.0, "0", None):
            with self.assertRaises(LedgerRefusal) as ctx:
                self.led.acquire("e", "s", bad, now_ms=0)
            self.assertEqual(ctx.exception.code, "ledger_bad_generation")

    def test_bad_injected_time(self):
        """now_ms is INJECTED data: a wall clock, float or bool is refused."""
        for bad in (-1, 1.5, True, "0"):
            with self.assertRaises(LedgerRefusal) as ctx:
                self.led.acquire("e", "s", 0, now_ms=bad)
            self.assertEqual(ctx.exception.code, "ledger_bad_time")

    def test_use_after_close_raises(self):
        self.led.close(now_ms=0)
        with self.assertRaises(LedgerRefusal) as ctx:
            self.led.acquire("e", "s", 0, now_ms=1)
        self.assertEqual(ctx.exception.code, "ledger_closed")
        with self.assertRaises(LedgerRefusal):
            self.led.release("e", "s", 0, now_ms=1)

    def test_event_bound_is_loud(self):
        led = ResourceLedger(max_events=2)
        led.acquire("a", "s", 0, now_ms=0)
        led.acquire("b", "s", 0, now_ms=1)
        with self.assertRaises(LedgerRefusal) as ctx:
            led.acquire("c", "s", 0, now_ms=2)
        self.assertEqual(ctx.exception.code, "ledger_full")

    def test_bad_ledger_bound(self):
        for bad in (0, -1, True, 2.0, "2", None):
            with self.assertRaises(LedgerRefusal):
                ResourceLedger(max_events=bad)


class DeterminismTests(ResourceLedgerTestBase):
    def test_identical_histories_produce_identical_canonical_bytes(self):
        def build():
            led = ResourceLedger()
            led.acquire("engine:1", "session", 0, now_ms=0)
            led.release("engine:1", "session", 0, now_ms=1)
            led.acquire("engine:1", "session", 1, now_ms=2)
            led.release("engine:2", "session", 1, now_ms=3)  # unknown
            led.close_generation(1, now_ms=4)
            return led
        a, b = build(), build()
        ceilings = {"max_live": 4, "max_acquires": 8, "max_releases": 8,
                    "max_failures": 1}
        self.assertEqual(a.to_json(ceilings=ceilings),
                         b.to_json(ceilings=ceilings))
        self.assertEqual(a.events(), b.events())
        # and the ceiling arguments are echoed verbatim in the document
        doc = a.summary(ceilings=ceilings)
        self.assertEqual(doc["ceilings"], ceilings)

    def test_all_five_codes_form_the_named_vocabulary(self):
        self.assertEqual(len(FAILURE_CODES), 5)
        self.assertIn(LIVE_AT_CLOSE, FAILURE_CODES)
        self.assertEqual(set(CEILING_KEYS),
                         {"max_live", "max_acquires", "max_releases",
                          "max_failures"})

    def test_no_memory_or_process_surface_exists(self):
        """The ledger's public surface contains no memory probe, no process
        discovery, no kill: the only success inputs are events + caller
        ceilings.  (A structural check that the card's 'no psutil' law
        cannot regress silently.)"""
        import resource_ledger as mod
        import inspect
        source = inspect.getsource(mod)
        for forbidden in ("psutil", "popen", "Popen", "terminate", "kill(",
                          "virtual_memory", "time.time", "os.listdir",
                          "subprocess"):
            self.assertNotIn(forbidden, source)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(
        __import__("test_resource_ledger"))
    runner = unittest.TextTestRunner(verbosity=2)
    started = time.perf_counter()
    result = runner.run(suite)
    elapsed = time.perf_counter() - started
    print("runtime_seconds=%.3f" % elapsed)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
