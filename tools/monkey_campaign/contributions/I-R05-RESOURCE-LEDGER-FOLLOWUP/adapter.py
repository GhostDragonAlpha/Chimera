"""adapter.py -- I-R05-RESOURCE-LEDGER-FOLLOWUP: connect the ACCEPTED resource
ledger to the EXISTING session teardown hooks and teardown tests.

Card I-R05-RESOURCE-LEDGER-FOLLOWUP (planning id R05), attempt
a4592d4b796542a7ad657d8e2ad7d3ec, branch-3, base c525b82c.  PREREGISTRATION.md
(Rule 0: statement / prediction / falsifier) was frozen BEFORE this file was
written.

WHAT THIS IS (and is not)

This is a WIRING module, not a checker: all accounting law lives in the
accepted `resource_ledger.py` (PR #139 head 47c00f05169fa49ea770c274cfe7f280e6
... merge becdcb27, sha256 05cf62184931d6443188cd9b72aa9e88821cc8a9063a351a7e4
d658d6690da6c).  This module IMPORTS those exact bytes -- verified by sha256
at import time, refusing by name on any drift -- and connects them to the two
pinned teardown hooks the card names, WITHOUT editing any production source
(production_edit_allowed: false):

  * session_flow.py  (9afbddcd, sha256 30e06c04...): SessionFlow._transition
    (:310-360) fires ONE restart callable (:336, declared referent World.boot)
    and ONE teardown callable (:349, declared referent World.shutdown_engine)
    but keeps no per-resource ownership record.
  * forest_loader.py (9afbddcd, sha256 53d7fdde...): ForestScene (:339-412)
    is the existing teardown ownership API -- a NAME-keyed registry
    (:358-362), reverse-load-order teardown (:380-405) -- with no owner axis
    and no session generation.

THE ADAPTERS (the accepted hook-up proposal's sections A and B, as subclasses
instead of edits):

  LedgeredSessionFlow(SessionFlow)
      Owns the SESSION GENERATION integer (mirroring World.boot_count,
      slice_server.py:128).  The session owner records claims through
      acquire()/release(); a successful restart closes exactly the generation
      that ended (AFTER the declared restart callable returned) and bumps the
      generation; a successful exit records the session-owned release claims
      AFTER the one real teardown returned and closes the final generation.
      Every close leaves a named receipt in last_trace ("restart_leaks" /
      "exit_leaks") in the exact style of the existing restart_failed /
      exit_failed records.  The frozen transition table is untouched: teardown
      still fires exactly once, a second Q is still the named drop.

  LedgeredForestScene(ForestScene)
      Mirrors every name the scene registers as a
      (generation, owner="session", "forest:<name>") ledger record, and mirrors
      each successful teardown release; on the f08_teardown_leak path the
      record simply stays live, so the next close names the leak by exact id.
      The scene's own zero-live audit (live_after) and the ledger's live ids
      are two independent counts of one truth.

THE CLAIM-TIMING LAW (deliberate, documented deviation from proposal A's
release-before-teardown ordering): release claims are recorded only AFTER the
declared work actually completed -- a failed teardown claims nothing, the
generation stays open, and the eventual close names every still-live record.
A claim must never precede the observable completion of what it claims.

PINNED SOURCES: `reference/` holds the read-only extraction (git show) of the
pinned hooks, byte-pinned in reference/EXTRACTION_LEDGER.json.  The adapter
re-verifies EVERY pin at import and refuses by name
(adapter_accepted_source_drift / adapter_reference_drift) on the slightest
drift -- a rewritten stand-in cannot pass silently.

NO GOVERNOR POWERS: this module discovers no OS processes, terminates nothing,
launches nothing, probes no memory, reads no wall clock and no network.  The
only success criterion is the accepted ledger's own accounting.

Selftest:  python adapter.py selftest
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

__all__ = [
    "AdapterRefusal",
    "ACCEPTED_LEDGER_HEAD", "ACCEPTED_LEDGER_MERGE", "PINNED_BASE_REVISION",
    "ACCEPTED_RESOURCE_LEDGER_SHA256", "PINNED_HOOK_SHA256",
    "RESOURCE_LEDGER_SOURCE_PATH", "RESOURCE_LEDGER_SHA256",
    "resource_ledger", "ResourceLedger", "session_flow", "forest_loader",
    "REFERENCE_ROOT", "REFERENCE_SCHEMA",
    "LedgeredSessionFlow", "LedgeredForestScene",
]

REFERENCE_SCHEMA = "chimera.monkey_campaign.pinned_reference.v1"

_HERE = Path(__file__).resolve().parent
REFERENCE_ROOT = _HERE / "reference"

# ── the accepted identity (falsifier F1's guard) ────────────────────────────────
ACCEPTED_LEDGER_HEAD = "47c00f05169fa49ea770c274cfe7f280e6710e82"   # PR #139 head
ACCEPTED_LEDGER_MERGE = "becdcb2716ee441cfb2832287a349c8f4b6c7090"
ACCEPTED_RESOURCE_LEDGER_SHA256 = (
    "05cf62184931d6443188cd9b72aa9e88821cc8a9063a351a7e4d658d6690da6c")

# ── the pinned hooks (parent card's pinned base revision) ───────────────────────
PINNED_BASE_REVISION = "9afbddcd90164b5544a16fd0bc72278d985eb6e3"
PINNED_HOOK_SHA256 = {
    "tools/monkey_campaign/product/session_flow.py":
        "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf",
    "tools/monkey_campaign/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "tools/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
    "tools/monkey_campaign/data/monkey_forest/forest_loader.py":
        "53d7fdde7deb6223f6760f4d9d6d8f378f3c4bf3cc5513381bf83e68d8cfbb95",
    "tools/monkey_campaign/product/session_flow_tests.py":
        "b6ce2bba598fcb8119de82f9a06639ee6d2744c1605ac82c8d699b8df75ef49a",
}


class AdapterRefusal(ValueError):
    """A loud, named refusal (house shape: code / detail / identity).

    Refusals are structural: a drifted pinned source, a ledger that is not an
    instance of the ACCEPTED ResourceLedger, a bad ceiling mapping.  Accounting
    failures (leaks, wrong owner/generation) are NEVER refusals -- they are the
    accepted ledger's recorded evidence.
    """

    def __init__(self, code, detail="", **identity):
        self.code, self.detail = code, str(detail)
        self.identity = dict(identity)
        super().__init__(code + (": " + self.detail if detail else ""))


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_file(path, expected, code, **identity):
    got = _sha256_file(path)
    if got != expected:
        raise AdapterRefusal(code, "pinned source drift", path=str(path),
                             expected=expected, got=got, **identity)
    return path


def _module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AdapterRefusal("adapter_load_refused", str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ── load the ACCEPTED ledger (falsifier F1's guard fires here, at import) ───────
def _locate_accepted_ledger():
    """Prefer the merged sibling contribution; fall back to the pinned
    reference extraction.  EITHER WAY the bytes must hash to the accepted
    sha256 or the import refuses."""
    candidates = (
        (_HERE.parent / "I-R05-RESOURCE-LEDGER" / "resource_ledger.py",
         "merged sibling contribution I-R05-RESOURCE-LEDGER"),
        (REFERENCE_ROOT / "resource_ledger.py",
         "pinned reference extraction"),
    )
    for path, origin in candidates:
        if path.is_file():
            return _verify_file(path, ACCEPTED_RESOURCE_LEDGER_SHA256,
                                "adapter_accepted_source_drift",
                                origin=origin), origin
    raise AdapterRefusal("adapter_accepted_source_missing",
                         "the accepted resource_ledger.py was found nowhere",
                         tried=[str(p) for p, _ in candidates])


RESOURCE_LEDGER_SOURCE_PATH, RESOURCE_LEDGER_ORIGIN = _locate_accepted_ledger()
resource_ledger = _module_from_path(
    "adapter_accepted_resource_ledger", RESOURCE_LEDGER_SOURCE_PATH)
ResourceLedger = resource_ledger.ResourceLedger
RESOURCE_LEDGER_SHA256 = ACCEPTED_RESOURCE_LEDGER_SHA256  # verified just above

# ── load the pinned hooks (never a rewrite: subclasses of these exact bytes) ────
for _rel, _expected in PINNED_HOOK_SHA256.items():
    _verify_file(REFERENCE_ROOT / _rel, _expected, "adapter_reference_drift",
                 revision=PINNED_BASE_REVISION)

if str(REFERENCE_ROOT) not in sys.path:
    sys.path.insert(0, str(REFERENCE_ROOT))
_tools = sys.modules.get("tools")
if _tools is not None and hasattr(_tools, "__path__") \
        and str(REFERENCE_ROOT) not in list(_tools.__path__):
    # bias an existing namespace package toward the pinned bytes; the
    # post-import verification below still refuses on any mismatch
    _tools.__path__.insert(0, str(REFERENCE_ROOT))

forest_loader = _module_from_path(
    "adapter_pinned_forest_loader",
    REFERENCE_ROOT / "tools/monkey_campaign/data/monkey_forest/forest_loader.py")
session_flow = _module_from_path(
    "adapter_pinned_session_flow",
    REFERENCE_ROOT / "tools/monkey_campaign/product/session_flow.py")

# verify what the pinned hooks ACTUALLY resolved to (sys.path could have
# offered different bytes -- that would be a loud stop, never a silent swap)
for _modname, _rel in (
        ("tools.monkey_campaign.product.input_mapper",
         "tools/monkey_campaign/product/input_mapper.py"),
        ("tools.science_funnel.typeb_export.command_record",
         "tools/science_funnel/typeb_export/command_record.py")):
    _resolved = sys.modules.get(_modname)
    _file = getattr(_resolved, "__file__", None)
    if not _file:
        raise AdapterRefusal("adapter_pinned_hook_missing", _modname)
    _verify_file(Path(_file).resolve(), PINNED_HOOK_SHA256[_rel],
                 "adapter_reference_drift", module=_modname)


# ── proposal B: the scene publishes its names to the ledger ─────────────────────
class _MirrorRelease:
    """One registered scene resource whose successful release mirrors one
    ledger release claim.  A resource with no release of its own gets a
    mirror-only release (the scene's drop-by-name IS the physical release);
    a raising release propagates BEFORE the claim -- the record stays live
    and the next close names the leak by exact id."""

    __slots__ = ("_inner", "_mirror", "_rid", "_owner", "_generation")

    def __init__(self, inner, ledger, rid, owner, generation):
        self._inner = inner
        self._mirror = ledger
        self._rid = rid
        self._owner = owner
        self._generation = generation

    def release(self):
        inner_release = getattr(self._inner, "release", None)
        if callable(inner_release):
            inner_release()
        self._mirror.release(self._rid, self._owner, self._generation)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class LedgeredForestScene(forest_loader.ForestScene):
    """ForestScene with every registered name mirrored into the ACCEPTED
    ledger as (generation, owner, "forest:<name>").  The teardown contract is
    the scene's own, unchanged: reverse-load order, one real teardown, a
    second call a named no-op; only the per-resource ownership RECORD is new
    (parent hook-up proposal B, forest_loader.py:380-405)."""

    MIRROR_PREFIX = "forest:"

    def __init__(self, objects, surface, initial_state, receipt,
                 engine_shutdown=None, ledger=None, generation=0,
                 owner="session"):
        if ledger is None:
            ledger = ResourceLedger()
        if not isinstance(ledger, ResourceLedger):
            raise AdapterRefusal(
                "adapter_ledger_type",
                "ledger must be an instance of the ACCEPTED "
                "ResourceLedger, never a duck-typed stand-in",
                got=type(ledger).__name__)
        self._mirror_ledger = ledger
        self._mirror_owner = owner
        self._mirror_generation = generation
        super().__init__(objects, surface, initial_state, receipt,
                         engine_shutdown=None)
        for name in list(self._resources):
            self._mirror_name(name)
        if engine_shutdown is not None:
            self.attach_engine_shutdown(engine_shutdown)

    @property
    def ledger(self):
        return self._mirror_ledger

    @property
    def mirror_generation(self):
        return self._mirror_generation

    def mirror_ids(self):
        """The ledger ids this scene registered, sorted (deterministic)."""
        return sorted(self.MIRROR_PREFIX + name
                      for name in self._resources)

    def _mirror_name(self, name):
        rid = self.MIRROR_PREFIX + name
        self._mirror_ledger.acquire(rid, self._mirror_owner,
                                    self._mirror_generation)
        self._resources[name] = _MirrorRelease(
            self._resources[name], self._mirror_ledger, rid,
            self._mirror_owner, self._mirror_generation)

    def attach_engine_shutdown(self, shutdown):
        super().attach_engine_shutdown(shutdown)
        self._mirror_name("engine_shutdown")


# ── proposal A: the flow owns the generation ────────────────────────────────────
class LedgeredSessionFlow(session_flow.SessionFlow):
    """SessionFlow with the ACCEPTED ledger wired around the frozen
    transitions.  The table, the gating, the quiesce and the declared
    restart/teardown referents are the flow's own, unchanged (parent hook-up
    proposal A, session_flow.py:327-350); only the per-resource ownership
    RECORD and the generation lifecycle are new.

    Claim timing (THE CLAIM-TIMING LAW, see module docstring): the exit
    releases are recorded AFTER the one real teardown returned; a failed
    boot/teardown records nothing and closes nothing.
    """

    def __init__(self, mapper, restart_scene, teardown, ledger=None,
                 ceilings=None, bindings=None):
        if ledger is None:
            ledger = ResourceLedger()
        if not isinstance(ledger, ResourceLedger):
            raise AdapterRefusal(
                "adapter_ledger_type",
                "ledger must be an instance of the ACCEPTED "
                "ResourceLedger, never a duck-typed stand-in",
                got=type(ledger).__name__)
        if ceilings is not None:
            if not isinstance(ceilings, dict):
                raise AdapterRefusal(
                    "adapter_bad_ceiling",
                    "ceilings must be a dict of caller-provided limits",
                    got=repr(ceilings))
            ceilings = dict(ceilings)
        self._declared_teardown = teardown          # the DECLARED referent
        self._ledger = ledger
        self._ceilings = ceilings
        self._generation = 0
        self._exit_closed = False
        self.restart_summaries = []
        self.exit_summary = None
        super().__init__(mapper, restart_scene, self._exit_teardown,
                         bindings=bindings)

    # ── reads ────────────────────────────────────────────────────────────────
    @property
    def ledger(self):
        return self._ledger

    @property
    def generation(self):
        return self._generation

    def live_ids(self, generation=...):
        """Live resource ids, whole ledger by default (sorted, deterministic)."""
        scope = None if generation is ... else generation
        return [record.resource_id
                for record in self._ledger.live(generation=scope)]

    # ── the session owner's claim surface ────────────────────────────────────
    def acquire(self, resource_id, owner="session", now_ms=None):
        """Record the session owner's acquire claim for the CURRENT
        generation (the ledger refuses acquisitions into closed
        generations by name -- acquire_generation_closed)."""
        return self._ledger.acquire(resource_id, owner, self._generation,
                                    now_ms=now_ms)

    def release(self, resource_id, owner="session", generation=None,
                now_ms=None):
        """Record a release claim.  ``generation=None`` claims the CURRENT
        generation; an explicit stale integer simulates a stale claimant
        (the ledger records ledger_wrong_generation and the record stays
        live -- falsifier F3's named evidence)."""
        scope = self._generation if generation is None else generation
        return self._ledger.release(resource_id, owner, scope, now_ms=now_ms)

    # ── the exit teardown wrapper (the flow calls it exactly once) ───────────
    def _release_session_owned(self, now_ms=None):
        """Release claims for the CURRENT generation's session-owned live
        records, in reverse-acquire order (the house reverse-order law).
        Other owners' records (operator, ...) are NEVER touched here -- the
        accepted ledger would refuse the cross-owner claim anyway."""
        owned = [record for record in self._ledger.live()
                 if record.generation == self._generation
                 and record.owner == "session"]
        released = []
        for record in sorted(owned, key=lambda r: (-r.seq, r.resource_id)):
            self._ledger.release(record.resource_id, "session",
                                 self._generation, now_ms=now_ms)
            released.append(record.resource_id)
        return released

    def _exit_teardown(self):
        result = self._declared_teardown()
        self._release_session_owned()
        return result

    # ── the frozen table, applied + accounted ────────────────────────────────
    def _transition(self, action, key_name, now_ms):
        dest = super()._transition(action, key_name, now_ms)
        if dest is None:
            return None                     # named drop or failed transition
        if action == "restart" and dest == session_flow.PLAYING:
            # THE RESTART ACCOUNT: the declared restart callable returned, so
            # the generation that just ended is closed NOW (its still-live
            # records are named live_at_close), then the generation bumps --
            # the mirror of World.boot_count (slice_server.py:128).
            old = self._generation
            summary = self._ledger.close_generation(
                old, ceilings=self._ceilings, now_ms=int(now_ms))
            self._generation = old + 1
            self.restart_summaries.append(
                {"closed_generation": old, "summary": summary})
            self.last_trace.setdefault("restart_leaks", []).append(
                self._receipt(old, summary, int(now_ms)))
        elif action == "exit" and dest == session_flow.EXITED \
                and not self._exit_closed:
            # THE EXIT ACCOUNT: the one real teardown returned; close the
            # final generation.  Unreleased records (operator-owned, or a
            # session resource the teardown never completed) are named
            # live_at_close and FAIL the cycle -- never launderable.
            summary = self._ledger.close_generation(
                self._generation, ceilings=self._ceilings, now_ms=int(now_ms))
            self._exit_closed = True
            self.exit_summary = summary
            self.last_trace.setdefault("exit_leaks", []).append(
                self._receipt(self._generation, summary, int(now_ms)))
        return dest

    @staticmethod
    def _receipt(generation, summary, now_ms):
        leaks = [detail["resource_id"]
                 for detail in summary["failure_details"]
                 if detail["code"] == resource_ledger.LIVE_AT_CLOSE]
        return {"at_ms": now_ms, "closed_generation": generation,
                "passed": summary["passed"],
                "live_at_close": summary["failures_by_code"][
                    resource_ledger.LIVE_AT_CLOSE],
                "leak_ids": leaks}


# ── selftest (deterministic, bounded, no I/O beyond stdout) ─────────────────────
def _selftest():
    ok = True

    class _Recorder:
        def __init__(self):
            self.calls = []

        def boot(self):
            self.calls.append("boot")
            return {"booted": True}

        def shutdown_engine(self):
            self.calls.extend(["terminate", "wait", "kill"])
            return True

    world = _Recorder()
    mapper = session_flow.CountingMapper()
    flow = LedgeredSessionFlow(mapper, world.boot, world.shutdown_engine)
    flow.key("Return", down=1, now_ms=0)            # attract -> playing
    flow.acquire("engine:9347", now_ms=1)
    flow.acquire("scene:forest", now_ms=2)
    flow.release("scene:forest", now_ms=3)
    flow.release("engine:9347", now_ms=4)
    flow.key("Escape", down=1, now_ms=10)           # playing -> paused
    flow.key("R", down=1, now_ms=20)                # restart: gen 0 closed
    ok &= flow.generation == 1
    ok &= flow.last_trace["restart_leaks"][-1]["passed"] is True
    flow.acquire("engine:9350", now_ms=21)
    flow.release("engine:9350", now_ms=22)
    flow.key("Q", down=1, now_ms=30)                # exit: teardown + close
    ok &= world.calls == ["boot", "terminate", "wait", "kill"]
    ok &= flow.exit_summary is not None and flow.exit_summary["passed"]
    before = len(flow.ledger.events())
    flow.key("Q", down=1, now_ms=40)                # named drop, no re-close
    ok &= len(flow.ledger.events()) == before
    ok &= flow.ledger.closed is False               # close_generation, not seal
    print(resource_ledger.canonical_json(
        {"schema": resource_ledger.SCHEMA,
         "adapter_selftest": "pass" if ok else "FAIL"}).decode("ascii"))
    return 0 if ok else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "selftest":
        return _selftest()
    raise AdapterRefusal("adapter_cli_verb", argv)


if __name__ == "__main__":
    sys.exit(main())
