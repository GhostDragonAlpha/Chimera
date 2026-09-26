"""adapter.py -- I-U07-TRACE-FOLLOWUP: connect the ACCEPTED trace format to the
EXISTING input/camera test seam.

The card: drive the REAL U01 input seam (pinned ``input_mapper.py`` bytes,
injected sink, injected integer-millisecond monotonic clock) so that the two
Python-observable stages of the accepted four-stage format emit as actual seam
events, while the two native stages stay structurally missing:

    input -> command_emitted            <- emitted HERE, from real seam events
    simulation_consumed -> presented    <- native (engine ZOH tick boundary and
                                           engine frame offer); NO Python source
                                           exists, so the adapter NEVER emits
                                           them -- only an explicit caller may
                                           attach real native observations.

The trace FORMAT and its whole law are owned by the accepted module, imported
from the sibling merged contribution (``../I-U07-TRACE/input_trace.py``, PR
#138 head ``4d2ececc``). This adapter holds no latency arithmetic, no limits
and no clocks of its own: a latency remains EXACTLY the accepted module's
matched-stage difference, and the seam's 2-stage trace therefore REFUSES
(``missing_stage``) instead of producing one.

WHAT IS PINNED, WHAT IS NOT:
  * the accepted module is IMPORTED, never copied; tests assert its sha256
    (``c8f4e444…``, PR #138 bytes);
  * ``input_mapper.py`` (7a36a45e…), ``command_record.py`` (67711759…),
    ``follow_camera.py`` (d61347f0…) and the two existing seam test modules
    are pinned byte-identically under ``reference/`` (see
    ``reference/EXTRACTION_LEDGER.json``, revision ``9afbddcd`` -- the same
    revision the accepted I-U07-TRACE report cites) and materialized
    UNMODIFIED into an OS temp directory in the canonical repo layout so the
    unmodified files' own imports resolve; nothing is rewritten.

THE CHAIN LAW of this adapter (one causal fact, no interpretation): every
CommandRecord the mapper actually emits opens exactly one fresh chain
(``seq``); that chain's ``input`` stage is the adapter's latest observed
key-state transition at or before the emission on the one injected clock --
copied with its payload (``transition_index`` records the sharing; several
re-issued commands lawfully share one press). A command without any observed
input antecedent is refused by name (``command_without_input_antecedent``);
a non-monotonic or non-integer injected clock is refused by name
(``clock_regression`` / ``non_integer_clock``) -- causal matching needs an
ordered clock, and a silent reorder would be invention.

Headless and deterministic: no wall clock, no window, no network; the only
I/O beyond caller data is reading the pinned ``reference/`` bytes and
materializing them to the temp directory documented above.

stdlib only, Python 3.11+.
"""
from __future__ import annotations

import importlib
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

__all__ = [
    "SeamTraceRefused", "TraceSink", "SeamTracer", "load_accepted_trace_module",
    "PINNED_SHA256", "ACCEPTED_SHA256", "PYTHON_STAGES", "NATIVE_STAGES",
]

HERE = Path(__file__).resolve().parent

# ── identity pins (asserted here once, loudly; details in the ledger) ──────────
ACCEPTED_SHA256 = "c8f4e4442a3ceedecd9c636857eda92642d26ec535d45f2c91a3ce9fd4550a57"
PINNED_SHA256 = {
    "tools/monkey_campaign/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "tools/monkey_campaign/product/follow_camera.py":
        "d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7",
    "tools/monkey_campaign/product/follow_camera_tests.py":
        "4d75164ff6a16bf0d817332b7c5229513750782727ad1a23911025dc93d31b27",
    "tools/monkey_campaign/product/input_mapper_tests.py":
        "95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e",
    "tools/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
}

# The accepted format's four stages; the two this Python seam can observe and
# the two that only the native engine can supply. Declared, not discovered.
PYTHON_STAGES = ("input", "command_emitted")
NATIVE_STAGES = ("simulation_consumed", "presented")


class SeamTraceRefused(Exception):
    """The adapter refuses an operation by name; nothing is invented.

    Distinct from the accepted module's ``TraceRefused`` (which owns the trace
    law); this names the SEAM connection's own refusals.
    """

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        super().__init__(f"{reason}: {details or {}}")
        self.reason = reason
        self.details = details or {}


# ── the accepted module: imported from the sibling merged contribution ────────
def load_accepted_trace_module():
    """Import the ACCEPTED ``input_trace`` module -- never a local copy.

    Refuses by name if the sibling merged contribution is absent, and lets the
    caller's hash assertion (tests pin ``ACCEPTED_SHA256``) catch any bytes
    that are not the PR #138 merge. No fallback path exists: a vendored or
    rewritten stand-in is the card's falsifier.
    """
    path = HERE.parent / "I-U07-TRACE" / "input_trace.py"
    if not path.is_file():
        raise SeamTraceRefused(
            "accepted_module_missing",
            {"expected": str(path),
             "note": "the adapter imports the accepted I-U07-TRACE module "
                     "(merged PR #138); it is never vendored or rewritten"})
    name = "input_trace"
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "__file__", None) == str(path):
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise SeamTraceRefused("accepted_module_unloadable", {"path": str(path)})
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_IT = load_accepted_trace_module()


# ── the pinned seam sources: byte-identical reference/ materialization ─────────
def _sha256_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_pinned_seam() -> Path:
    """Copy the pinned ``reference/`` bytes into a fresh OS temp directory in
    the canonical repo layout, asserting every pin hash, so the UNMODIFIED
    files import exactly as they do in the seam's own repo (their internal
    ``from tools.science_funnel...`` resolves against the same layout).

    The only I/O this adapter performs beyond caller data; the directory is
    OS-disposable and nothing outside it is written.
    """
    root = Path(tempfile.mkdtemp(prefix="i_u07_trace_followup_seam_"))
    for repo_path, want in PINNED_SHA256.items():
        src = HERE / "reference" / repo_path
        if not src.is_file():
            shutil.rmtree(root, ignore_errors=True)
            raise SeamTraceRefused("pinned_source_missing",
                                   {"expected": str(src)})
        got = _sha256_file(src)
        if got != want:
            shutil.rmtree(root, ignore_errors=True)
            raise SeamTraceRefused("pinned_source_hash_mismatch",
                                   {"path": repo_path, "sha256": got,
                                    "expected": want})
        dst = root / repo_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return root


def load_pinned_input_mapper():
    """Import the pinned REAL ``input_mapper`` module (never a stand-in)."""
    root = materialize_pinned_seam()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        return importlib.import_module("tools.monkey_campaign.product.input_mapper")
    except Exception:  # pragma: no cover - surface with layout context
        shutil.rmtree(root, ignore_errors=True)
        raise


# ── the seam connection ────────────────────────────────────────────────────────
class TraceSink:
    """Wraps ANY existing seam sink: forwards every ``emit`` untouched and
    hands the actual CommandRecord to the tracer as the ``command_emitted``
    stage, stamped with the EXACT boundary time the mapper was driven at (the
    tracer's ``boundary_t`` -- one clock read per boundary, never re-read).
    Adds zero authority -- the mapper's no-teleport law is unchanged (every
    call it sees is still exactly ``emit(CommandRecord)``)."""

    def __init__(self, inner: Any, tracer: "SeamTracer"):
        if not hasattr(inner, "emit"):
            raise SeamTraceRefused("bad_sink", {"type": type(inner).__name__})
        self._inner = inner
        self._tracer = tracer
        self.calls: list[tuple[str, Any]] = []   # audit: ("emit", record) only

    def emit(self, record):
        self.calls.append(("emit", record))
        self._tracer._record_command(record)     # reads tracer.boundary_t
        return self._inner.emit(record)

    def __len__(self):
        return len(self.calls)


class SeamTracer:
    """The adapter: drives the pinned REAL ``InputMapper`` on ONE injected
    integer-millisecond monotonic clock and emits accepted-format events for
    the stages this seam actually observes.

    Identity (`clock_name`, `run`, `build`) is CALLER DATA, like the accepted
    module's limits -- nothing is defaulted. ``clock()`` must return integers
    (the mapper's own contract) and may not go backwards; violations refuse by
    name instead of being silently ordered.

    Stage coverage -- declared, not discovered:
      input, command_emitted      emitted here, from actual seam events;
      simulation_consumed         NATIVE (engine ZOH tick boundary) -- absent;
      presented                   NATIVE (engine frame offer) -- absent; the
                                  existing camera harness yields an ordering
                                  fact (``armed_after``), never a timestamp.
    """

    def __init__(self, *, clock: Callable[[], int], clock_name: str, run: str,
                 build: str, sink: Optional[Any] = None):
        for field in ("clock_name", "run", "build"):
            value = locals()[field]
            if not isinstance(value, str) or not value:
                raise SeamTraceRefused("bad_identity", {"field": field})
        if not callable(clock):
            raise SeamTraceRefused("bad_clock", {"type": type(clock).__name__})
        self._clock = clock
        self._clock_name = clock_name
        self._run = run
        self._build = build
        self._last_t: Optional[int] = None
        self.boundary_t: Optional[int] = None    # set by tick(); the mapper's
                                                 # exact boundary time
        self._transitions: list[dict[str, Any]] = []   # observed input events
        self._chains: list[dict[str, Any]] = []        # one per emitted record
        self._events: list[dict[str, Any]] = []        # accepted-format records
        im = load_pinned_input_mapper()
        inner = sink if sink is not None else im.MockSink()
        self.mapper = im.InputMapper(TraceSink(inner, self))
        self.inner_sink = inner

    # -- the injected clock: one read per seam event, ordered, integral ──────
    def now_ms(self) -> int:
        t = self._clock()
        if isinstance(t, bool) or not isinstance(t, int):
            raise SeamTraceRefused("non_integer_clock",
                                   {"type": type(t).__name__,
                                    "note": "the mapper's contract is "
                                            "integer milliseconds"})
        if self._last_t is not None and t < self._last_t:
            raise SeamTraceRefused("clock_regression",
                                   {"t": t, "previous": self._last_t,
                                    "note": "causal matching needs a "
                                            "monotonic clock"})
        self._last_t = t
        return t

    # -- input events: the mapper is driven AT the clock's own reading ───────
    def press(self, key: str) -> Any:
        t = self.now_ms()
        action = self.mapper.press(key, t)
        self._record_input("press", key, action, t)
        return action

    def release(self, key: str) -> Any:
        t = self.now_ms()
        action = self.mapper.release(key, t)
        self._record_input("release", key, action, t)
        return action

    def release_all(self) -> None:
        t = self.now_ms()
        self.mapper.release_all(t)
        self._record_input("release_all", "*", None, t)

    def mouse(self, dx_counts: float) -> None:
        # accumulated by the mapper; consumed at boundaries (never an event of
        # its own -- counts alone emit nothing on this seam)
        self.mapper.mouse(dx_counts)

    def tick(self) -> list[Any]:
        """One mapper boundary at the clock's own reading; any CommandRecords
        the mapper emits become chains via the TraceSink hook, stamped with
        THIS boundary time (the mapper's actual ``now_ms``)."""
        t = self.now_ms()
        self.boundary_t = t
        return self.mapper.tick(t)

    # -- event recording (the ONLY writers of self._events) ─────────────────
    def _record_input(self, kind: str, key: str, action: Any, t: int) -> None:
        transition = {"transition_index": len(self._transitions),
                      "kind": kind, "key": key, "action": action, "t_ms": t}
        self._transitions.append(transition)

    def _record_command(self, record: Any) -> None:
        if self.boundary_t is None:
            raise SeamTraceRefused("command_outside_boundary",
                                   {"note": "emissions are stamped with the "
                                            "boundary time they were driven "
                                            "at"})
        t = self.boundary_t
        if not self._transitions:
            raise SeamTraceRefused("command_without_input_antecedent",
                                   {"record": repr(record)})
        antecedent = self._transitions[-1]
        seq = len(self._chains)
        record_payload = {"v_forward": record.v_forward,
                          "yaw_rate": record.yaw_rate,
                          "issued_tick": record.issued_tick,
                          "source": record.source}
        self._chains.append({"seq": seq, "antecedent": antecedent, "t_ms": t,
                             "record": record_payload})
        for stage, t_stage, payload in (
            ("input", antecedent["t_ms"],
             {k: antecedent[k] for k in
              ("transition_index", "kind", "key", "action")}),
            ("command_emitted", t, record_payload),
        ):
            self._events.append({"seq": seq, "stage": stage, "t": t_stage,
                                 "unit": "ms", "clock": self._clock_name,
                                 "run": self._run, "build": self._build,
                                 "payload": payload})

    # -- explicit caller attachment of NATIVE observations (never internal) ──
    def attach_native_stage(self, seq: int, stage: str, t: int,
                            payload: Any = None) -> None:
        """Attach a REAL native-stage observation supplied by the caller.

        The adapter itself has no native source (declared above); this entry
        point exists so a live integrator can attach engine-side observations
        on the SAME clock. Tests use it only with fixture-labeled values.
        """
        if stage not in NATIVE_STAGES:
            raise SeamTraceRefused("not_a_native_stage",
                                   {"stage": stage, "native": list(NATIVE_STAGES),
                                    "note": "the two Python-observable stages "
                                            "are emitted by driving the seam"})
        if not (0 <= seq < len(self._chains)):
            raise SeamTraceRefused("unknown_seq",
                                   {"seq": seq, "chains": len(self._chains)})
        if isinstance(t, bool) or not isinstance(t, int):
            raise SeamTraceRefused("non_integer_clock",
                                   {"t": repr(t),
                                    "note": "native observations arrive on "
                                            "the same integer-ms clock, as "
                                            "caller data"})
        self._events.append({"seq": seq, "stage": stage, "t": t,
                             "unit": "ms", "clock": self._clock_name,
                             "run": self._run, "build": self._build,
                             "payload": payload})

    # -- output: accepted-format events + analysis THROUGH the accepted law ───
    def events(self) -> list[dict[str, Any]]:
        """The event records in the accepted module's input format (JSON-safe;
        deterministic order: input precedes its command per chain)."""
        return [dict(e) for e in self._events]

    def analyze(self, limits: Optional[dict[str, float]] = None) -> dict[str, Any]:
        """Hand the trace to the ACCEPTED module and report its verdict, whatever
        it is. With only the Python-observable stages present the accepted law
        refuses (``missing_stage``); that refusal IS the honest result and is
        surfaced with ``latency_output: None`` -- never softened, never worked
        around. Limits pass through as caller data or stay absent (the
        accepted module then answers ``unqualified`` / ``p06_limits_absent``).
        """
        try:
            parsed = _IT.parse_trace(self.events())
            summary = _IT.summarize(parsed, limits)
        except _IT.TraceRefused as ref:
            return {"schema": "chimera.i_u07_followup.analysis.v1",
                    "complete": False,
                    "refused": ref.reason, "details": ref.details,
                    "latency_output": None,
                    "python_stages_present": list(PYTHON_STAGES),
                    "native_stages_missing": list(NATIVE_STAGES)}
        return {"schema": "chimera.i_u07_followup.analysis.v1",
                "complete": True, "summary": summary,
                "python_stages_present": list(PYTHON_STAGES),
                "native_stages_missing": []}

    def causal_pairs(self) -> list[dict[str, Any]]:
        """The raw causal facts for matching tests: per chain, the antecedent
        transition and the emitted record's boundary time. NO latency here --
        arithmetic belongs to the accepted module on complete chains only."""
        return [{"seq": c["seq"], "antecedent": dict(c["antecedent"]),
                 "command_t_ms": c["t_ms"],
                 "record": dict(c["record"])} for c in self._chains]
