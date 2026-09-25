"""failure_sequences.py -- I-R06-FAILURE-SEQUENCES: deterministic cross-component
failure-sequence regression runner.

CARD: I-R06-FAILURE-SEQUENCES (planning id R06), attempt
c57fd6bb125142ee9d593f800eb32dd4, branch-7, base revision
9afbddcd90164b5544a16fd0bc72278d985eb6e3.

WHAT THIS IS (prereg: PREREGISTRATION.md, frozen before this build): a replay
runner that drives the EXISTING pinned product components -- SessionFlow
filtering FocusPolicy filtering InputMapper (tools/monkey_campaign/product/,
extracted byte-identical from the pinned revision into reference/) -- through
eight cross-component failure sequences that no component's own unit suite
exercises, and checks three invariants on the observed command stream:

  (a) RELEASE-NO-LATCH: after a release / blur / disconnect release_all at
      instant E, no positive-speed record is emitted later than
      E + RELEASE_DECAY_MS, the post-release window lands on an EXACT-0.0
      record, and it carries at most two records (the declared decay samples).
  (b) PAUSE-SILENCE: after the flow leaves `playing`, the sink never receives
      another record, and the quiesce leaves the mapper held-empty.
  (c) TEARDOWN-EXACTLY-ONCE: World.shutdown_engine() (terminate->wait->kill)
      runs exactly once per session and World.boot() exactly once per restart,
      across repeated close, pause/resume/restart, and mid-play no-op keys.

THE IMPORT-BINDING MECHANISM (the rewrite falsifier's guard): at runner init
`bind_components()` imports the four pinned modules, resolves each module's
`__file__`, hashes the bytes, and REFUSES to run unless (1) every sha256
matches reference/EXTRACTION_LEDGER.json, (2) every file's git blob sha1
re-derives to the ledger's `git_blob` recorded from the pinned revision, and
(3) every imported module file physically lives under the reference root (no
shadowing from elsewhere on sys.path). The frozen constants must additionally
be the SAME OBJECTS across the three modules (the modules' own P2 identity
law). Any mismatch raises ImportBindingError: the runner fails closed.

The deliberately-broken controls (LatchingMapper / QuiesceIgnoringMapper) are
NOT here on purpose: they live in test_failure_sequences.py, are labeled
stand-ins, and are used only to prove the detectors fire (FS-3). This module
never substitutes its own logic for the components' logic in any sequence
path under test.

MOCKED-BOUNDARY STATEMENT: every adapter here is a MOCKED boundary. The clock
is an injected integer-millisecond stepper, the sink is a recording list, and
boot/teardown are the pinned module's own RecordingRestart/TeardownDouble
doubles. No window, process, device, transport, or wall clock is touched.
Nothing in this card certifies real Windows/device-loss behavior.

Headless, stdlib-only, deterministic: no randomness, no threads, no wall
clock anywhere in the sequence paths.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

__all__ = [
    "CARD_ID", "LEDGER_NAME", "BOUND_MODULE_NAMES",
    "ImportBindingError", "find_reference_root", "BoundComponents",
    "bind_components", "get_bound",
    "SteppedClock", "RecordingSink", "SequenceSession",
    "check_release_window", "check_silence", "check_stream_bounds",
    "SEQUENCE_REGISTRY", "run_sequence", "run_all", "main",
]

CARD_ID = "I-R06-FAILURE-SEQUENCES"
LEDGER_NAME = "EXTRACTION_LEDGER.json"

# The pinned modules the runner binds to, in import order. All four must hash
# to the ledger or the runner refuses to run (FS-1, the rewrite falsifier).
BOUND_MODULE_NAMES = (
    "tools.science_funnel.typeb_export.command_record",
    "tools.monkey_campaign.product.input_mapper",
    "tools.monkey_campaign.product.session_flow",
    "tools.monkey_campaign.product.focus_policy",
)


class ImportBindingError(RuntimeError):
    """The runner cannot prove it is testing the pinned bytes. Fail closed."""


# ── hashing helpers (real bytes only; never invent digits) ────────────────────
def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    """Re-derive the git blob id of these bytes (sha1 of the canonical header)."""
    feeder = hashlib.sha1()
    feeder.update(b"blob %d\0" % len(data))
    feeder.update(data)
    return feeder.hexdigest()


# ── locating the extraction ───────────────────────────────────────────────────
def find_reference_root(explicit: Optional[str] = None) -> Path:
    """Find the directory holding EXTRACTION_LEDGER.json + the extracted tree.

    Search order: the explicit argument, then FAILURE_SEQ_REFERENCE, then
    <this file's dir>/reference, then reference/ off each ancestor of this
    file's directory. Raises ImportBindingError with instructions otherwise
    (the checkout copy carries no extraction by design -- point it at one).
    """
    here = Path(__file__).resolve().parent
    named = []
    if explicit:
        named.append(Path(explicit))
    env = os.environ.get("FAILURE_SEQ_REFERENCE")
    if env:
        named.append(Path(env))
    # a NAMED root (argument or env) is honored EXACTLY: if it does not hold
    # the extraction, refuse -- never silently substitute another tree
    for cand in named:
        if (cand / LEDGER_NAME).is_file() and (cand / "tools").is_dir():
            return cand.resolve()
    if named:
        raise ImportBindingError(
            "the named extraction root(s) %r contain no %s + tools/ -- refusing "
            "to fall back to some other tree" % ([str(c) for c in named], LEDGER_NAME))
    candidates = [here / "reference"]
    for parent in [here] + list(here.parents):
        candidates.append(parent / "reference")
    for cand in candidates:
        ledger = cand / LEDGER_NAME
        if ledger.is_file() and (cand / "tools").is_dir():
            return cand.resolve()
    raise ImportBindingError(
        "no extraction found: %s + tools/ must exist together. Set "
        "FAILURE_SEQ_REFERENCE to the directory containing %s (see "
        "EXTRACTION_LEDGER.json). The checkout copy of this file intentionally "
        "ships without reference/ -- point it at the attempt workspace."
        % (LEDGER_NAME, LEDGER_NAME))


@dataclass
class BindingCheck:
    """One verified (or refused) module file binding."""
    module: str
    file: str
    sha256_expected: str
    sha256_actual: str
    git_blob_expected: str
    git_blob_actual: str
    under_reference_root: bool

    @property
    def ok(self) -> bool:
        return (self.sha256_expected == self.sha256_actual
                and self.git_blob_expected == self.git_blob_actual
                and self.under_reference_root)


class BoundComponents:
    """The hash-verified import of the pinned product components.

    Attributes are the REAL imported classes/constants -- the runner never
    redeclares any of them. `binding_report` lists every check that was made;
    `identity_checks` records the frozen-constant object-identity assertions
    (the modules' own P2 law: a second copy of a frozen constant is exactly
    where a silent divergence lives).
    """

    def __init__(self, reference_root: Path, ledger: dict,
                 modules: dict, binding_report: list, identity_checks: list):
        self.reference_root = reference_root
        self.ledger = ledger
        self._modules = modules
        self.binding_report = binding_report
        self.identity_checks = identity_checks
        cr = modules["tools.science_funnel.typeb_export.command_record"]
        im = modules["tools.monkey_campaign.product.input_mapper"]
        sf = modules["tools.monkey_campaign.product.session_flow"]
        fp = modules["tools.monkey_campaign.product.focus_policy"]
        # the REAL components -- imported, never rewritten:
        self.CommandRecord = cr.CommandRecord
        self.InputMapper = im.InputMapper
        self.MockSink = im.MockSink
        self.SessionFlow = sf.SessionFlow
        self.FlowError = sf.FlowError
        self.RecordingRestart = sf.RecordingRestart
        self.TeardownDouble = sf.TeardownDouble
        self.FocusPolicy = fp.FocusPolicy
        # the frozen numbers, read FROM the verified modules:
        self.INTERVAL_MS = im.INTERVAL_MS
        self.RELEASE_DECAY_MS = im.RELEASE_DECAY_MS
        self.VALID_MS = im.VALID_MS
        self.V_MAX_IN_BAND_M_S = im.V_MAX_IN_BAND_M_S
        self.OMEGA_MAX_RAD_S = im.OMEGA_MAX_RAD_S
        self.EXPIRY_TICKS = im.EXPIRY_TICKS
        self.PHYSICS_HZ = im.PHYSICS_HZ
        self.SOURCE_ID = im.SOURCE_ID

    def module_hash(self, module_name: str) -> dict:
        """The recorded identity (file + sha256 + git blob) of one bound module."""
        for entry in self.binding_report:
            if entry.module == module_name:
                return {"file": entry.file, "sha256": entry.sha256_actual,
                        "git_blob": entry.git_blob_actual}
        raise KeyError(module_name)


def bind_components(reference_root: Optional[str] = None) -> BoundComponents:
    """Import the pinned modules and PROVE they are the pinned bytes, or refuse."""
    if sys.version_info < (3, 11):
        raise ImportBindingError("Python 3.11+ required (card limit)")
    root = find_reference_root(reference_root)
    # purge anything already imported from a PREVIOUS bind (or a foreign tree)
    # so this bind can only resolve modules from THIS reference root
    for name in list(sys.modules):
        if name == "tools" or name.startswith("tools.") or name == "input_mapper":
            del sys.modules[name]
    ledger = json.loads((root / LEDGER_NAME).read_text(encoding="utf-8"))
    ledger_files = ledger.get("files")
    if not isinstance(ledger_files, dict) or not ledger_files:
        raise ImportBindingError("ledger %s carries no files table" % (root / LEDGER_NAME))
    # reference/ FIRST on sys.path so the imports can only resolve here...
    root_str = str(root)
    if root_str in sys.path:
        sys.path.remove(root_str)
    sys.path.insert(0, root_str)
    # ...and forbid accidental later shadowing of the pinned package by a
    # directory that happens to sit next to the runner.
    here_str = str(Path(__file__).resolve().parent)
    if here_str in sys.path:
        here_idx = sys.path.index(here_str)
        if here_idx < sys.path.index(root_str) and (Path(here_str) / "tools").is_dir():
            raise ImportBindingError(
                "a tools/ package sits beside the runner (%s) and would shadow "
                "the extraction -- remove it or move the runner" % here_str)

    modules = {}
    for name in BOUND_MODULE_NAMES:
        if name in sys.modules:            # a previous bind must not be reused blindly
            del sys.modules[name]
        modules[name] = importlib.import_module(name)

    binding_report = []
    for name in BOUND_MODULE_NAMES:
        mod = modules[name]
        file_path = getattr(mod, "__file__", None)
        if not file_path:
            raise ImportBindingError("%s has no __file__ (namespace package?)" % name)
        resolved = Path(file_path).resolve()
        try:
            rel = resolved.relative_to(root).as_posix()
        except ValueError:
            rel = resolved.as_posix()
            under = False
        else:
            under = True
        entry = ledger_files.get(rel)
        if entry is None:
            raise ImportBindingError(
                "imported file %r is not in the ledger -- refusing (shadowed "
                "import or foreign tree)" % rel)
        data = resolved.read_bytes()
        sha_actual = _sha256_bytes(data)
        blob_actual = _git_blob_sha1(data)
        check = BindingCheck(
            module=name, file=rel,
            sha256_expected=entry["sha256"], sha256_actual=sha_actual,
            git_blob_expected=entry["git_blob"], git_blob_actual=blob_actual,
            under_reference_root=under)
        binding_report.append(check)
        if not check.ok:
            raise ImportBindingError(
                "IMPORT BINDING FAILED for %s (file %s): sha256 %s vs ledger %s, "
                "git blob %s vs ledger %s, under_root=%s -- the runner would not "
                "be testing the pinned bytes; refusing (FS-1)."
                % (name, rel, sha_actual, entry["sha256"], blob_actual,
                   entry["git_blob"], under))
        # ledger self-consistency: the recorded sha256 must itself re-derive
        # from the recorded git blob's claim about the same bytes.
        if entry.get("git_blob") != _git_blob_sha1(data):
            raise ImportBindingError("ledger git_blob mismatch for %s" % rel)

    # focus_policy flat-imports `input_mapper` (its module attribute `_im`);
    # that module object must be the SAME FILE the ledger pins.
    fp = modules["tools.monkey_campaign.product.focus_policy"]
    flat_im = getattr(fp, "_im", None)
    pkg_im = modules["tools.monkey_campaign.product.input_mapper"]
    if flat_im is None or getattr(flat_im, "__file__", None) is None:
        raise ImportBindingError("focus_policy bound no flat input_mapper (`_im`)")
    if Path(flat_im.__file__).resolve() != Path(pkg_im.__file__).resolve():
        raise ImportBindingError(
            "flat `input_mapper` (%s) and package input_mapper (%s) resolved to "
            "DIFFERENT files -- refusing" % (flat_im.__file__, pkg_im.__file__))

    # the frozen-constant identity law (each module's own P2 rule):
    cr = modules["tools.science_funnel.typeb_export.command_record"]
    im = modules["tools.monkey_campaign.product.input_mapper"]
    sf = modules["tools.monkey_campaign.product.session_flow"]
    identity_checks = [
        ("input_mapper.V_MAX_IN_BAND_M_S is command_record.V_MAX_IN_BAND_M_S",
         im.V_MAX_IN_BAND_M_S is cr.V_MAX_IN_BAND_M_S),
        ("input_mapper.HOLD_TICKS is command_record.HOLD_TICKS",
         im.HOLD_TICKS is cr.HOLD_TICKS),
        ("focus_policy.RELEASE_DECAY_MS is input_mapper.RELEASE_DECAY_MS",
         fp.RELEASE_DECAY_MS is im.RELEASE_DECAY_MS),
        ("focus_policy.MAX_AGE_MS is input_mapper.VALID_MS",
         fp.MAX_AGE_MS is im.VALID_MS),
        ("session_flow.INTERVAL_MS is input_mapper.INTERVAL_MS",
         sf.INTERVAL_MS is im.INTERVAL_MS),
        ("focus_policy's flat `_im` resolves to the SAME FILE as the package "
         "input_mapper (two module objects over one pinned file -- enforced "
         "above by __file__ comparison)",
         Path(flat_im.__file__).resolve() == Path(pkg_im.__file__).resolve()),
    ]
    for label, held in identity_checks:
        if not held:
            raise ImportBindingError(
                "frozen-constant identity broken: %s -- refusing" % label)

    return BoundComponents(root, ledger, modules, binding_report, identity_checks)


_BOUND: Optional[BoundComponents] = None


def get_bound(reference_root: Optional[str] = None) -> BoundComponents:
    """Bind once per process; every later call reuses the verified import."""
    global _BOUND
    if _BOUND is None:
        _BOUND = bind_components(reference_root)
    return _BOUND


# ── the mocked harness boundaries (recording only; zero real effects) ─────────
class SteppedClock:
    """The injected clock: integer milliseconds, advanced by hand. No wall time."""

    def __init__(self, start_ms: int = 0):
        self._now = int(start_ms)

    @property
    def now_ms(self) -> int:
        return self._now

    def advance(self, delta_ms: int) -> int:
        self._now += int(delta_ms)
        return self._now


class RecordingSink:
    """The seam double the policy hands itself in front of: records every
    record WITH its (injected) emission time. This is the timeline the
    invariant checkers read. Mocked boundary -- nothing is sent anywhere."""

    def __init__(self, clock: SteppedClock):
        self.clock = clock
        self.timeline = []            # list[(emit_ms, CommandRecord)]

    def emit(self, record):
        self.timeline.append((int(self.clock.now_ms), record))
        return len(self.timeline)

    @property
    def records(self):
        return [r for (_t, r) in self.timeline]


class SequenceSession:
    """One composed session under test: SessionFlow(FocusPolicy(RecordingSink))
    with the pinned module's own RecordingRestart / TeardownDouble as the world
    referents. `mapper_factory` exists ONLY for the test file's broken controls;
    every sequence under test uses the default (the real FocusPolicy)."""

    def __init__(self, bound: BoundComponents, clock: Optional[SteppedClock] = None,
                 mapper_factory: Optional[Callable] = None):
        self.bound = bound
        self.clock = clock if clock is not None else SteppedClock(start_ms=1000)
        self.sink = RecordingSink(self.clock)
        factory = mapper_factory if mapper_factory is not None else bound.FocusPolicy
        self.mapper = factory(self.sink)          # mapper slot: policy (or control)
        self.restart_double = bound.RecordingRestart()
        self.teardown_double = bound.TeardownDouble()
        self.flow = bound.SessionFlow(
            self.mapper,
            restart_scene=self.restart_double.boot,
            teardown=self.teardown_double.shutdown_engine)
        self.events = []                          # the full ordered event log
        self.probes = {}                          # mid-sequence state snapshots

    def probe(self, label: str, value):
        """Snapshot a component state AT this instant. End-of-sequence checks
        cannot see mid-sequence states (a recovery press re-arms keys after a
        blur); probes pin the state where the invariant lives."""
        self.probes[label] = value
        self._log("probe", label=label, value=repr(value))
        return value

    # ── the event log ────────────────────────────────────────────────────────
    def _log(self, kind: str, **detail) -> dict:
        entry = {"t_ms": int(self.clock.now_ms), "kind": kind}
        entry.update(detail)
        self.events.append(entry)
        return entry

    # ── the driver surface (all times injected) ──────────────────────────────
    def at(self, ms: int) -> "SequenceSession":
        self.clock._now = int(ms)
        return self

    def key_down(self, name: str, ms: Optional[int] = None):
        if ms is not None:
            self.at(ms)
        self._log("key_down", key=name)
        return self.flow.key(name, down=1, now_ms=self.clock.now_ms)

    def key_up(self, name: str, ms: Optional[int] = None):
        if ms is not None:
            self.at(ms)
        self._log("key_up", key=name)
        return self.flow.key(name, down=0, now_ms=self.clock.now_ms)

    def tick(self, ms: Optional[int] = None):
        if ms is not None:
            self.at(ms)
        self._log("decision_tick")
        return self.flow.tick(self.clock.now_ms)

    def mouse(self, dx_counts: float, ms: Optional[int] = None):
        if ms is not None:
            self.at(ms)
        self._log("mouse", dx=float(dx_counts))
        return self.flow.mouse(dx_counts)

    def policy_event(self, name: str, ms: Optional[int] = None):
        """blur/focus/disconnect/reconnect -- events on the focus boundary BELOW
        the flow (the alt-tab / device-gone surface). Dispatches to the policy's
        real on_* methods; only legal when the mapper slot provides them."""
        if ms is not None:
            self.at(ms)
        method = getattr(self.mapper, "on_" + name, None)
        if method is None:
            raise TypeError("mapper slot %r has no on_%s() -- focus events need "
                            "the policy in the slot"
                            % (type(self.mapper).__name__, name))
        self._log("policy_" + name)
        return method(self.clock.now_ms)

    # ── failure forensics ────────────────────────────────────────────────────
    def minimal_event_log(self, up_to_ms: int) -> list:
        """The event prefix up to and including `up_to_ms` -- the minimal
        sequence a failure report preserves."""
        out = []
        for entry in self.events:
            out.append(entry)
            if entry["t_ms"] >= up_to_ms:
                break
        return out

    def component_identity(self) -> dict:
        """Which pinned bytes this session actually drove (for any failure)."""
        return {
            "bound_modules": [
                {"module": c.module, "file": c.file, "sha256": c.sha256_actual,
                 "git_blob": c.git_blob_actual}
                for c in self.bound.binding_report],
            "identity_checks_ok": all(held for _label, held in self.bound.identity_checks),
        }


# ── invariant checkers (pure functions over the recorded timeline) ────────────
def check_stream_bounds(session: SequenceSession, *, from_ms: int = 0,
                        until_ms: Optional[int] = None) -> list:
    """Every delivered record stays inside the frozen band: v in [0, V_MAX],
    |yaw| <= OMEGA_MAX (imported bounds; the runner redeclares none)."""
    b = session.bound
    violations = []
    for t, rec in session.sink.timeline:
        if t < from_ms or (until_ms is not None and t > until_ms):
            continue
        if rec.v_forward < 0.0 or rec.v_forward > b.V_MAX_IN_BAND_M_S:
            violations.append(
                "bounds: record at %d ms carries v_forward=%r outside [0, %r]"
                % (t, rec.v_forward, b.V_MAX_IN_BAND_M_S))
        if abs(rec.yaw_rate) > b.OMEGA_MAX_RAD_S:
            violations.append(
                "bounds: record at %d ms carries yaw_rate=%r outside +/-%r"
                % (t, rec.yaw_rate, b.OMEGA_MAX_RAD_S))
    return violations


def check_release_window(session: SequenceSession, e_ms: int, until_ms: int,
                         *, what: str = "release") -> list:
    """Invariant (a) over the window (E, until]: no zombie positive-speed record
    later than E + RELEASE_DECAY_MS; at most the two declared decay samples; the
    window lands on an EXACT-0.0 record."""
    b = session.bound
    deadline = e_ms + b.RELEASE_DECAY_MS
    window = [(t, rec) for (t, rec) in session.sink.timeline
              if e_ms < t <= until_ms]
    violations = []
    for t, rec in window:
        if rec.v_forward > 0.0 and t > deadline:
            violations.append(
                "zombie[%s]: positive speed %r still emitted at %d ms, later "
                "than release %d + decay %d = %d (released input remained "
                "latched)" % (what, rec.v_forward, t, e_ms,
                              b.RELEASE_DECAY_MS, deadline))
    if len(window) > 2:
        violations.append(
            "decay[%s]: %d records after the release at %d ms -- the declared "
            "policy allows at most the two boundary samples"
            % (what, len(window), e_ms))
    if window and window[-1][1].v_forward != 0.0:
        violations.append(
            "no-land[%s]: the post-release stream ends on v_forward=%r at %d "
            "ms, not on an exact 0.0 record" % (what, window[-1][1].v_forward,
                                                window[-1][0]))
    return violations


def check_silence(session: SequenceSession, after_ms: int, *,
                  until_ms: Optional[int] = None, what: str = "window") -> list:
    """Invariant (b): no record reaches the sink after `after_ms`."""
    violations = []
    for t, rec in session.sink.timeline:
        if t <= after_ms:
            continue
        if until_ms is not None and t > until_ms:
            continue
        violations.append(
            "not-silent[%s]: record with v_forward=%r emitted at %d ms, after "
            "the gate closed at %d ms" % (what, rec.v_forward, t, after_ms))
    return violations


def check_teardown_exactly_once(session: SequenceSession) -> list:
    """Invariant (c): the declared shutdown, terminate->wait->kill, exactly once."""
    calls = session.teardown_double.calls
    violations = []
    if calls.count("terminate") != 1:
        violations.append(
            "teardown: shutdown_engine ran %d time(s) (calls=%r) -- owned "
            "teardown must occur EXACTLY once" % (calls.count("terminate"), calls))
    if calls != ["terminate", "wait", "kill"] * calls.count("terminate"):
        violations.append(
            "teardown: call sequence %r is not the declared "
            "terminate->wait->kill ordering" % (calls,))
    return violations


def check_boot_count(session: SequenceSession, expected: int) -> list:
    boots = session.restart_double.calls.count(("boot",))
    if boots != expected:
        return ["boot: World.boot() ran %d time(s), expected exactly %d"
                % (boots, expected)]
    return []


# ── the sequences (each = one step script + one check script, so the broken
#    controls in the test file replay the IDENTICAL script and must fail) ──────

# SEQ-01: release stops emission (flow x mapper x gate x sink). Invariant (a).
def _steps_seq01(s: SequenceSession):
    s.key_down("Return", 995)              # start the session (attract -> playing)
    s.key_down("W", 1000)
    for t in (1000, 1050, 1100, 1150, 1200):
        s.tick(t)
    s.key_up("W", 1210)                      # release BETWEEN boundaries
    for t in (1250, 1300, 1350, 1400, 1450):
        s.tick(t)


def _checks_seq01(s: SequenceSession) -> list:
    v = list(check_release_window(s, 1210, 1450, what="seq01-key-release"))
    v += check_stream_bounds(s)
    if s.mapper.held != frozenset():
        v.append("latch: mapper still holds %r after the release" % sorted(s.mapper.held))
    if not s.sink.records:
        v.append("coverage: no records emitted at all -- the sequence drove nothing")
    return v


# SEQ-02: pause silences locomotion (flow quiesce x mapper x sink). (b)+(a).
def _steps_seq02(s: SequenceSession):
    s.key_down("Return", 995)              # start the session (attract -> playing)
    s.key_down("W", 1000)
    for t in (1000, 1050, 1100):
        s.tick(t)
    s.key_down("Escape", 1110)               # pause: quiesce, then gate closes
    for t in (1150, 1200, 1250, 1300, 1400, 1500, 1600, 2000, 3000):
        s.tick(t)                            # ticks while PAUSED: must emit nothing


def _checks_seq02(s: SequenceSession) -> list:
    v = list(check_silence(s, 1110, what="seq02-paused"))
    v += check_stream_bounds(s)
    if s.mapper.held != frozenset():
        v.append("quiesce: mapper still holds %r after the pause quiesce"
                 % sorted(s.mapper.held))
    quiesced = s.flow.last_trace.get("quiesced")
    if not quiesced or quiesced[0]["held"] != []:
        v.append("quiesce: flow recorded no clean quiesce receipt (%r)" % (quiesced,))
    drops = [d for d in s.flow.last_trace.get("dropped", [])
             if d["kind"] == "decision_tick"]
    if len(drops) != 9:
        v.append("pause: expected 9 named decision_tick drops while paused, "
                 "got %d" % len(drops))
    return v


# SEQ-03: resume arms a fresh grid; no phantom tail (flow x mapper). (b)+(a).
def _steps_seq03(s: SequenceSession):
    s.key_down("Return", 995)              # start the session (attract -> playing)
    s.key_down("W", 1000)
    for t in (1000, 1050, 1100):
        s.tick(t)
    s.key_down("Escape", 1110)               # pause (quiesce arms the decay tail)
    s.tick(2000)                             # paused tick: nothing
    s.key_down("Return", 3000)               # resume
    s.tick(3050)                             # the pending tail's first boundary
    s.tick(3100)                             # ...and its last
    s.key_down("W", 3105)                    # a NEW press after recovery
    for t in (3150, 3200, 3250):
        s.tick(t)


def _checks_seq03(s: SequenceSession) -> list:
    v = list(check_release_window(s, 1110, 3105, what="seq03-resume-tail"))
    v += check_stream_bounds(s)
    post_resume = [(t, rec) for (t, rec) in s.sink.timeline if 3000 < t <= 3105]
    if len(post_resume) != 1 or post_resume[0][1].v_forward != 0.0:
        v.append("resume: expected exactly one exact-0.0 record after resume, "
                 "got %r" % ([(t, r.v_forward) for t, r in post_resume],))
    fresh = [(t, rec) for (t, rec) in s.sink.timeline if t > 3105]
    if len(fresh) != 3 or any(r.v_forward != s.bound.V_MAX_IN_BAND_M_S
                              for _t, r in fresh):
        v.append("resume: the new press did not arm a fresh full-speed grid: %r"
                 % ([(t, r.v_forward) for t, r in fresh],))
    for t, rec in fresh:
        if t <= 3105:
            v.append("resume: pre-press record leaked into the fresh window")
    return v


# SEQ-04: restart through pause boots exactly once; exit tears down exactly
# once (flow x world x mapper). (c)+(a).
def _steps_seq04(s: SequenceSession):
    s.key_down("Return", 995)              # start the session (attract -> playing)
    s.key_down("W", 1000)
    for t in (1000, 1050, 1100):
        s.tick(t)
    s.key_down("Escape", 1110)               # pause
    s.key_down("R", 1115)                    # restart: quiesce + World.boot
    for t in (1150, 1200, 1250):             # the pending tail lands
        s.tick(t)
    s.key_down("W", 1255)                    # play on after the restart
    for t in (1300, 1350):
        s.tick(t)
    s.key_down("Q", 1360)                    # exit: teardown
    s.tick(1400)                             # post-exit ticks: nothing
    s.key_down("W", 1405)                    # post-exit press: dropped
    s.key_down("Q", 1410)                    # repeated close: no second teardown
    s.tick(1450)


def _checks_seq04(s: SequenceSession) -> list:
    v = list(check_boot_count(s, 1))
    v += check_teardown_exactly_once(s)
    v += list(check_release_window(s, 1110, 1255, what="seq04-resume-tail"))
    v += check_silence(s, 1360, what="seq04-post-exit")
    v += check_stream_bounds(s)
    if s.flow.state != "exited":
        v.append("exit: state %r after Q, expected the terminal state" % s.flow.state)
    drops = [d["kind"] for d in s.flow.last_trace.get("dropped", [])]
    if "key_press" not in drops:
        v.append("exit: the post-exit W press was not named-dropped")
    if "flow_action" not in drops:
        v.append("exit: the repeated Q was not named-dropped")
    return v


# SEQ-05: blur mid-emission decays to silence; blurred presses dropped
# (focus x mapper x gate x sink, flow gating). (a).
def _steps_seq05(s: SequenceSession):
    s.key_down("Return", 995)              # start the session (attract -> playing)
    s.key_down("W", 1000)
    for t in (1000, 1050, 1100):
        s.tick(t)
    s.policy_event("blur", 1110)             # alt-tab below the flow
    s.probe("held_after_blur", sorted(s.mapper.held))
    for t in (1150, 1200, 1250, 1300, 1500):
        s.tick(t)
    s.key_down("W", 1510)                    # pressed while blurred: dropped
    s.probe("held_while_blurred_after_press", sorted(s.mapper.held))
    s.tick(1550)
    s.policy_event("focus", 2000)            # recovery
    s.key_down("W", 2005)                    # a NEW press, armed fresh
    for t in (2050, 2100, 2150):
        s.tick(t)


def _checks_seq05(s: SequenceSession) -> list:
    v = list(check_release_window(s, 1110, 2000, what="seq05-blur"))
    v += check_silence(s, 1210, until_ms=2000,
                       what="seq05-blurred-idle-ticks")
    v += check_stream_bounds(s)
    if s.probes.get("held_after_blur") != []:
        v.append("blur: mapper held %r at the blur instant -- the blur release "
                 "did not clear the held set" % (s.probes.get("held_after_blur"),))
    if s.probes.get("held_while_blurred_after_press") != []:
        v.append("blur: a press was ACCEPTED while blurred (held=%r)"
                 % (s.probes.get("held_while_blurred_after_press"),))
    if not s.mapper.last_trace.get("dropped_blurred"):
        v.append("blur: the blurred W press was not dropped by name")
    fresh = [(t, rec) for (t, rec) in s.sink.timeline if t > 2005]
    if len(fresh) != 3 or any(r.v_forward != s.bound.V_MAX_IN_BAND_M_S
                              for _t, r in fresh):
        v.append("focus: recovery press did not arm a fresh full-speed grid: %r"
                 % ([(t, r.v_forward) for t, r in fresh],))
    return v


# SEQ-06: disconnect/reconnect leaves no zombie (focus x mapper x flow). (a)+(b).
def _steps_seq06(s: SequenceSession):
    s.key_down("Return", 995)              # start the session (attract -> playing)
    s.key_down("W", 1000)
    s.mouse(40, 1001)                        # counts pending at the next boundary
    for t in (1050, 1100):
        s.tick(t)
    s.mouse(5, 1105)                         # counts pending at DISCONNECT
    s.policy_event("disconnect", 1110)       # device gone: release_all + named
    s.probe("held_after_disconnect", sorted(s.mapper.held))
    s.tick(1150)                             # the tail + pending counts' last word
    s.key_down("W", 1160)                    # dropped while disconnected
    s.mouse(10, 1165)                        # dropped while disconnected
    s.tick(1200)                             # the tail lands on exact 0.0
    for t in (1250, 1300, 1500):
        s.tick(t)                            # silence
    s.policy_event("reconnect", 2000)
    s.key_down("W", 2005)
    for t in (2050, 2100):
        s.tick(t)


def _checks_seq06(s: SequenceSession) -> list:
    v = list(check_release_window(s, 1110, 2000, what="seq06-disconnect"))
    v += check_stream_bounds(s)
    v += check_silence(s, 1210, until_ms=2000, what="seq06-disconnected-idle")
    # the named disconnected state: read from the policy's own event trace
    # (the session ends RECONNECTED, so the live state here is 'focused')
    events = [name for (name, _t) in s.mapper.last_trace.get("events", [])]
    if "disconnect" not in events or "reconnect" not in events:
        v.append("disconnect: policy event trace %r lacks the named "
                 "disconnect/reconnect events" % (events,))
    if not s.mapper.last_trace.get("dropped_disconnected"):
        v.append("disconnect: the disconnected press was not dropped by name")
    if s.probes.get("held_after_disconnect") != []:
        v.append("disconnect: mapper held %r at the disconnect instant -- the "
                 "release_all did not clear the held set"
                 % (s.probes.get("held_after_disconnect"),))
    fresh = [(t, rec) for (t, rec) in s.sink.timeline if t > 2005]
    if len(fresh) != 2 or any(r.v_forward != s.bound.V_MAX_IN_BAND_M_S
                              for _t, r in fresh):
        v.append("reconnect: recovery press did not arm a fresh grid: %r"
                 % ([(t, r.v_forward) for t, r in fresh],))
    return v


# SEQ-07: a restart key mid-play is a named no-op (flow table x world x mapper).
# (c) -- an accidental R must never wipe the running session.
def _steps_seq07(s: SequenceSession):
    s.key_down("Return", 995)              # start the session (attract -> playing)
    s.key_down("W", 1000)
    for t in (1000, 1050, 1100):
        s.tick(t)
    s.key_down("R", 1110)                    # restart while PLAYING: absent row
    for t in (1150, 1200):
        s.tick(t)


def _checks_seq07(s: SequenceSession) -> list:
    v = list(check_boot_count(s, 0))
    v += check_stream_bounds(s)
    if s.flow.state != "playing":
        v.append("no-op: state %r after mid-play R, expected still playing"
                 % s.flow.state)
    if s.flow.last_trace.get("quiesced"):
        v.append("no-op: a mid-play R quiesced the mapper -- the held key was "
                 "silently wiped")
    if s.mapper.held != frozenset({"W"}):
        v.append("no-op: mapper holds %r, expected {W} untouched"
                 % sorted(s.mapper.held))
    late = [(t, rec) for (t, rec) in s.sink.timeline if t > 1110]
    if len(late) != 2 or any(r.v_forward != s.bound.V_MAX_IN_BAND_M_S
                             for _t, r in late):
        v.append("no-op: the held key stopped re-issuing after the rejected R: %r"
                 % ([(t, r.v_forward) for t, r in late],))
    drops = [d for d in s.flow.last_trace.get("dropped", [])
             if d["kind"] == "flow_action"]
    if not drops:
        v.append("no-op: the rejected restart was not named-dropped")
    return v


# SEQ-08: exit from attract tears down exactly once, then terminal (flow x
# world). (c) -- teardown occurs even though nothing ever played.
def _steps_seq08(s: SequenceSession):
    s.key_down("Q", 1000)                    # exit from attract
    s.key_down("W", 1005)                    # unbound key post-exit: dropped
    s.key_down("Return", 1010)               # bound key post-exit: named no-op
    s.tick(1050)
    s.tick(1100)
    s.key_down("Q", 1500)                    # repeated close: no second teardown
    s.tick(1550)


def _checks_seq08(s: SequenceSession) -> list:
    v = list(check_teardown_exactly_once(s))
    v += check_boot_count(s, 0)
    if s.sink.timeline:
        v.append("attract-exit: records reached the sink %r -- nothing ever "
                 "played" % ([(t, r.v_forward) for t, r in s.sink.timeline],))
    if s.flow.state != "exited":
        v.append("attract-exit: state %r after Q, expected terminal" % s.flow.state)
    drops = [d["kind"] for d in s.flow.last_trace.get("dropped", [])]
    for need in ("key_press", "flow_action", "decision_tick"):
        if need not in drops:
            v.append("attract-exit: post-exit %s was not named-dropped" % need)
    return v


SEQUENCE_REGISTRY = {
    "SEQ-01": ("release-stops-emission", _steps_seq01, _checks_seq01),
    "SEQ-02": ("pause-silences-locomotion", _steps_seq02, _checks_seq02),
    "SEQ-03": ("resume-fresh-grid-no-phantom", _steps_seq03, _checks_seq03),
    "SEQ-04": ("restart-through-pause-boots-once-exit-tears-down-once",
               _steps_seq04, _checks_seq04),
    "SEQ-05": ("blur-mid-emission-decays-to-silence", _steps_seq05, _checks_seq05),
    "SEQ-06": ("disconnect-reconnect-no-zombie", _steps_seq06, _checks_seq06),
    "SEQ-07": ("mid-play-restart-key-is-a-named-no-op", _steps_seq07, _checks_seq07),
    "SEQ-08": ("exit-from-attract-teardown-exactly-once", _steps_seq08, _checks_seq08),
}


@dataclass
class SequenceResult:
    seq_id: str
    name: str
    passed: bool
    violations: list
    events: list                     # the (minimal) event log, preserved on failure
    component_identity: dict
    used_control_mapper: Optional[str] = None   # set ONLY by the broken controls


def run_sequence(seq_id: str, session: Optional[SequenceSession] = None,
                 bound: Optional[BoundComponents] = None) -> SequenceResult:
    """Replay one sequence against one (hash-bound) session and check it."""
    b = bound if bound is not None else get_bound()
    if seq_id not in SEQUENCE_REGISTRY:
        raise KeyError("unknown sequence %r" % seq_id)
    name, steps, checks = SEQUENCE_REGISTRY[seq_id]
    s = session if session is not None else SequenceSession(b)
    control = type(s.mapper).__name__ if session is not None else None
    control = control if control != "FocusPolicy" else None
    steps(s)
    violations = checks(s)
    if violations:
        last_t = max([t for (t, _r) in s.sink.timeline] or [s.clock.now_ms])
        return SequenceResult(seq_id, name, False, violations,
                              s.minimal_event_log(last_t), s.component_identity(),
                              control)
    return SequenceResult(seq_id, name, True, [], [], s.component_identity(),
                          control)


def run_all(bound: Optional[BoundComponents] = None) -> list:
    b = bound if bound is not None else get_bound()
    return [run_sequence(seq_id, bound=b) for seq_id in sorted(SEQUENCE_REGISTRY)]


def main(argv: Optional[list] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root_arg = None
    if argv and not argv[0].startswith("-"):
        root_arg = argv.pop(0)
    bound = get_bound(root_arg)
    print("bound modules (sha256 verified against %s):" % LEDGER_NAME)
    for check in bound.binding_report:
        print("  %-55s %s" % (check.file, check.sha256_actual))
    failures = 0
    for result in run_all(bound):
        mark = "PASS" if result.passed else "FAIL"
        print("%s  %s  %s" % (mark, result.seq_id, result.name))
        for violation in result.violations:
            print("      violation: %s" % violation)
        if not result.passed:
            failures += 1
    print("%d/%d sequences passed" % (len(SEQUENCE_REGISTRY) - failures,
                                      len(SEQUENCE_REGISTRY)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
