"""lm_gateway — fair cross-process queue for the single LM Studio endpoint.

The one local model is a single physical resource: when two agent PROCESSES
call it at once, LM Studio queues them internally, and the one waiting behind
a long generation hits its client-side timeout (observed 2026-07-12, Stage 7
Ralph loop). The editor has a scheduler; the model didn't. This is it.

Design (informed by 'you can stack calls on the LM server'): NOT a hard
one-at-a-time lock that throws away stacking — a FAIR FIFO QUEUE. Callers take
a numbered ticket and wait their turn instead of dogpiling; up to
CHIMERA_LM_CONCURRENCY run at once (default 1 = strict serialization, which
eliminates the timeout entirely; raise it if your LM Studio is configured for
parallel/continuous-batching). Waiting for a slot does NOT eat the call's own
timeout budget — you wait, THEN you get your full generation window.

Cross-process because agents are separate processes: tickets are files under
docs/world/lm_queue/ (machine-local, gitignored), liveness by mtime with a
heartbeat thread, so a crashed holder's slot is reclaimed in ~STALE_TTL.

Usage — a drop-in for urllib.request.urlopen at the four generation sites:
    from core.lm_gateway import lm_urlopen
    with lm_urlopen(req, timeout=600, agent="critic") as r:
        msg = json.load(r)["choices"][0]["message"]

It also ADOPTS THE RESIDENT MODEL (see resolve_model): every request is retargeted
at whatever model LM Studio already has loaded, so the studio never forces a swap,
never evicts another client, and changing models everywhere is just "load a
different model in LM Studio".
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

QUEUE_DIR = Path(__file__).resolve().parents[1] / "docs" / "world" / "lm_queue"
COUNTER = QUEUE_DIR / ".counter"
LOCK_PATH = QUEUE_DIR / ".lock"

# LEGACY, and deliberately EMPTY. Nothing in this studio names a model. The model
# is whatever LM Studio has resident (resolve_model), and lm_urlopen rewrites every
# outgoing body to it — call sites still import this to stamp a body, so the NAME
# has to survive, but its VALUE must stay blank.
#
# A real id here is a pinned model in disguise: the moment anything bypasses the
# gateway it would silently drag THAT model onto a GPU shared with other clients.
# Blank fails loudly instead, which is the honest outcome. Set CHIMERA_LM_MODEL
# only to force an id for a one-off debug run.
LM_MODEL = os.environ.get("CHIMERA_LM_MODEL", "")

# The shared per-call generation budget. qwen-agentworld is a REASONING model —
# it emits a long thinking trace before answering, so every call site needs
# generous time or it dies mid-thought (600s = 10 min ceiling; most finish far
# sooner). One env var, read everywhere.
LM_TIMEOUT = int(os.environ.get("CHIMERA_LM_TIMEOUT", "600"))

MAX_CONCURRENT = max(1, int(os.environ.get("CHIMERA_LM_CONCURRENCY", "1")))

# The endpoint's base URL — /v1 is the OpenAI-compat surface the call sites post
# to; /api/v0 is LM Studio's native REST surface, the only one that reports which
# models are RESIDENT (state=loaded) rather than merely on disk.
LM_BASE = os.environ.get("CHIMERA_LM_BASE", "http://localhost:1234").rstrip("/")

# If you swap the resident model while a call is in flight, that call can catch
# LM Studio mid-handover and 400 with "Engine protocol startup was aborted".
# Transient — ride it out rather than failing the agent's whole turn.
RELOAD_BACKOFF_S = float(os.environ.get("CHIMERA_LM_RELOAD_BACKOFF", "5"))
LOAD_ATTEMPTS = max(1, int(os.environ.get("CHIMERA_LM_LOAD_ATTEMPTS", "3")))
STALE_TTL = 25.0            # a ticket unheartbeated this long = dead holder (the
                           # heartbeat thread keeps a LIVE holder fresh through
                           # even a 10-min call, so this only catches crashes)
HEARTBEAT_S = 8.0
POLL_S = 0.4
# A queued caller must be willing to wait LONGER than one full call, or it
# fail-opens into the very contention the queue exists to prevent. Auto-scales
# above LM_TIMEOUT.
MAX_WAIT_S = float(os.environ.get("CHIMERA_LM_MAX_WAIT", str(LM_TIMEOUT + 300)))

# --- cross-platform advisory lock (same idiom as editor_scheduler) ----------
if os.name == "nt":
    import msvcrt

    def _acquire_lock_fd():
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR)
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        return fd

    def _release_lock_fd(fd):
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)
else:
    import fcntl

    def _acquire_lock_fd():
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd

    def _release_lock_fd(fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


_PROC_LOCK = threading.Lock()   # in-process guard; file lock guards across processes


def _next_seq() -> int:
    with _PROC_LOCK:            # threads serialize here before touching the OS lock
        fd = _acquire_lock_fd()
        try:
            try:
                n = int(COUNTER.read_text() or "0")
            except (OSError, ValueError):
                n = 0
            COUNTER.write_text(str(n + 1))
            return n + 1
        finally:
            _release_lock_fd(fd)


def _live_tickets() -> list:
    """Sorted (seq, path) of non-stale tickets; reclaims dead holders' files."""
    now = time.time()
    live = []
    for p in QUEUE_DIR.glob("t_*.json"):
        try:
            if now - p.stat().st_mtime > STALE_TTL:
                p.unlink(missing_ok=True)        # holder died; reclaim its slot
                continue
            seq = int(p.stem.split("_")[1])
            live.append((seq, p))
        except (OSError, ValueError, IndexError):
            continue
    return sorted(live)


class _Ticket:
    def __init__(self, seq: int, agent: str):
        self.seq = seq
        self.path = QUEUE_DIR / f"t_{seq}_{os.getpid()}.json"
        self.path.write_text(json.dumps({"agent": agent, "pid": os.getpid(),
                                         "ts": time.time()}))
        self._stop = threading.Event()
        self._hb = threading.Thread(target=self._heartbeat, daemon=True)
        self._hb.start()

    def _heartbeat(self):
        while not self._stop.wait(HEARTBEAT_S):
            try:
                self.path.touch()                # refresh mtime = still alive
            except OSError:
                return

    def cleared(self) -> bool:
        ahead = [s for s, _ in _live_tickets() if s < self.seq]
        return len(ahead) < MAX_CONCURRENT

    def release(self):
        self._stop.set()
        self.path.unlink(missing_ok=True)


def _acquire(agent: str) -> tuple:
    """Take a ticket, wait until cleared (or MAX_WAIT elapses -> fail-open,
    since blocking forever is worse than an honest attempt). Returns
    (ticket, waited_seconds)."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    seq = _next_seq()
    ticket = _Ticket(seq, agent or "unknown")
    start = time.time()
    while not ticket.cleared():
        if time.time() - start > MAX_WAIT_S:
            print(f"[lm_gateway] {agent}: waited {MAX_WAIT_S:.0f}s for a slot — "
                  f"proceeding anyway (queue jammed or holder slow)")
            break
        time.sleep(POLL_S + (seq % 5) * 0.05)     # tiny per-ticket jitter
    return ticket, time.time() - start


class _BufferedResponse:
    """Holds the fully-read body so the queue slot can free the instant the
    generation is done. Supports the read()/context-manager surface the four
    call sites use (json.load(r) and r.read())."""
    def __init__(self, data: bytes, status: int):
        self._data, self.status, self._pos = data, status, 0

    def read(self, *_a) -> bytes:
        d = self._data[self._pos:]
        self._pos = len(self._data)
        return d

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False


# --- model adoption ---------------------------------------------------------
# THE RULE (2026-07-14, the human's design): check what model is loaded, and use
# that model. That is the whole policy.
#
# The studio used to PIN a model id into every request body, which made LM Studio
# JIT-load THAT model — evicting whatever was already resident. With a second
# client on the same endpoint (a `pi` agent harness sitting on a different quant
# of the same base model) the two fought: each request evicted the other's model
# mid-startup and BOTH died with "Engine protocol startup was aborted". Two
# clients, two models, one GPU — no retry budget wins that.
#
# Adopting the resident model dissolves it. Nobody evicts anybody, the model
# stays warm, and switching models for the ENTIRE operation is just "load a
# different one in LM Studio" — no config, no env, no code.
#
# And there is NO fallback. If the endpoint is empty we raise NoModelLoaded
# rather than JIT-loading a default of our own choosing — a "fallback" is just a
# pinned model wearing a hat, and it means Chimera silently pulling a multi-GB
# model the operator never asked for. The operator decides what runs.
#
# Model TYPE is deliberately NOT consulted: LM Studio labels several of these
# builds `llm` when they are in fact vision-capable (vision was added to them
# after the fact), so the label would lie. The operator owns that choice.
# (Python/lmstudio_client.py used to reroute on that same bad flag — removed.)

ADOPT_RESIDENT = os.environ.get("CHIMERA_LM_ADOPT", "1").lower() not in (
    "0", "false", "no")


def _lms_exe() -> str | None:
    """LM Studio's CLI — the only surface that can UNLOAD. Its REST API exposes
    /api/v0/{models,chat/completions,completions,embeddings,fim} and no unload."""
    env = os.environ.get("CHIMERA_LMS_EXE")
    if env and Path(env).exists():
        return env
    local = Path.home() / ".lmstudio" / "bin" / ("lms.exe" if os.name == "nt" else "lms")
    return str(local) if local.exists() else shutil.which("lms")


def loaded_models() -> list:
    """Model ids RESIDENT in memory right now (state=loaded), newest surface."""
    try:
        with urllib.request.urlopen(f"{LM_BASE}/api/v0/models", timeout=8) as r:
            payload = json.load(r)
    except Exception:
        return []                       # endpoint down: residency isn't ours to fix
    return [m.get("id") for m in payload.get("data", [])
            if m.get("state") == "loaded" and m.get("id")]


class NoModelLoaded(RuntimeError):
    """LM Studio is up but holding nothing. We do not pick one for you."""


def resolve_model() -> str:
    """The model every request targets: whatever LM Studio has resident.

    If NOTHING is resident we RAISE — we do not load a model. Naming a default
    here would mean Chimera silently JIT-loading a multi-GB model of its own
    choosing, which is the very behaviour this design exists to remove (it just
    wears a different hat: "fallback" instead of "pinned"). The operator decides
    what runs; the studio only ever adopts. If several are resident, take the
    first — we never evict to break the tie."""
    resident = loaded_models()
    if not resident:
        raise NoModelLoaded(
            "No model is loaded in LM Studio. Load one (vision-capable) and the "
            "studio will adopt it. Chimera never loads or picks a model for you.")
    return resident[0]


def evict_others(model: str | None) -> list:
    """MANUAL ONLY — `python -m core.lm_gateway evict`. The request path never
    calls this; it exists to reclaim VRAM from a model that is squatting.

    Unload every resident model that isn't `model` (None = unload everything).
    Returns what was evicted."""
    others = [m for m in loaded_models() if m != model]
    if not others:
        return []
    exe = _lms_exe()
    if not exe:
        print(f"[lm_gateway] {len(others)} foreign model(s) resident ({', '.join(others)}) "
              f"but the `lms` CLI was not found - cannot evict; set CHIMERA_LMS_EXE")
        return []
    evicted = []
    for m in others:
        try:
            p = subprocess.run([exe, "unload", m], capture_output=True,
                               text=True, timeout=90)
            if p.returncode == 0:
                evicted.append(m)
            else:
                print(f"[lm_gateway] unload {m} failed rc={p.returncode}: "
                      f"{(p.stderr or p.stdout or '').strip()[:200]}")
        except (OSError, subprocess.SubprocessError) as e:
            print(f"[lm_gateway] unload {m} errored: {e}")
    if evicted:
        tail = f"only {model} stays resident" if model else "endpoint now empty"
        print(f"[lm_gateway] evicted {', '.join(evicted)} -> {tail}")
    return evicted


def _retarget(req) -> str | None:
    """Point the outgoing body at the resident model.

    The call sites still build their bodies with a hardcoded model id. This is
    the one place that rewrites it, so all of them become model-agnostic without
    a single edit — and a model swap needs no code change anywhere. Raises
    NoModelLoaded if LM Studio is holding nothing: we never load one.
    Tolerates a body-less/opaque req (the unit tests pass a bare object())."""
    body = getattr(req, "data", None)
    if not body:
        return None
    try:
        payload = json.loads(body)
    except (TypeError, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None

    asked = payload.get("model")
    if not ADOPT_RESIDENT:
        return asked
    model = resolve_model()                           # raises if nothing is loaded
    if model != asked:
        payload["model"] = model
        try:
            req.data = json.dumps(payload).encode()   # setter drops stale Content-length
        except (AttributeError, TypeError):
            return asked                              # not a real Request; body stands
    return model


def _urlopen_riding_out_engine_races(req, timeout: float, agent: str, model: str):
    """urlopen, retrying the one failure a model handover provokes.

    If the resident model changes while we are calling (you loaded a new one, or
    the endpoint was cold and is now loading), LM Studio 400s with "Failed to
    load model ... Engine protocol startup was aborted" — the load simply never
    happens. Transient, so retry with escalating backoff. Anything else (and a
    model that truly cannot load) propagates on the final attempt."""
    for attempt in range(1, LOAD_ATTEMPTS + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            last = attempt == LOAD_ATTEMPTS
            if e.code != 400 or last:
                raise
            detail = e.read().decode(errors="replace")
            if "Failed to load model" not in detail:
                raise
            backoff = RELOAD_BACKOFF_S * attempt
            print(f"[lm_gateway] {agent or '?'}: engine-startup race on {model} "
                  f"(try {attempt}/{LOAD_ATTEMPTS}) - retrying in {backoff:.0f}s")
            time.sleep(backoff)


def lm_urlopen(req, timeout: float = 600.0, agent: str = None):
    """Drop-in for urllib.request.urlopen against the LM endpoint, fair-queued.
    Holds a slot only for the network+generation, then releases. Waiting for a
    slot never consumes `timeout` — that budget is for the call itself.

    Retargets the request at whatever model LM Studio currently holds, so no
    caller has to know or care which one that is, and nothing is ever evicted."""
    ticket, waited = _acquire(agent)
    try:
        model = _retarget(req)
        resp = _urlopen_riding_out_engine_races(req, timeout, agent, model)
        data = resp.read()
        if waited > 1.0:
            print(f"[lm_gateway] {agent or '?'}: waited {waited:.1f}s in queue "
                  f"(concurrency={MAX_CONCURRENT})")
        return _BufferedResponse(data, getattr(resp, "status", 200))
    finally:
        ticket.release()


def queue_depth() -> int:
    """Live tickets right now — for observability (preflight/herald)."""
    return len(_live_tickets())


def _main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m core.lm_gateway",
        description="LM endpoint — which model the studio will use, and queue depth.")
    ap.add_argument("command", choices=["status", "evict"], nargs="?", default="status",
                    help="status: which model requests will use. "
                         "evict: manually free VRAM (never happens on its own).")
    ap.add_argument("--model", default=None,
                    help="evict: the model to KEEP resident (default: the resident one)")
    ap.add_argument("--all", action="store_true",
                    help="evict: unload everything, emptying the endpoint")
    args = ap.parse_args()

    resident = loaded_models()
    print(f"endpoint   : {LM_BASE}")
    print(f"queue      : depth {queue_depth()} (concurrency={MAX_CONCURRENT})")
    print(f"resident   : {', '.join(resident) if resident else '(none)'}")
    if not ADOPT_RESIDENT:
        print("adopt      : OFF - callers keep their own model id")
    elif resident:
        print(f"WILL USE   : {resident[0]}  (adopted from what you have loaded)")
    else:
        print("WILL USE   : nothing - NO MODEL IS LOADED.")
        print("             Load one in LM Studio and the studio adopts it.")
        print("             Chimera will not load or pick a model for you.")

    if args.command == "status":
        if len(resident) > 1:
            print(f"\nNote: {len(resident)} models resident. Requests use the first. "
                  f"`evict` frees the rest.")
        return 0 if resident or not ADOPT_RESIDENT else 1

    keep = None if args.all else (args.model or (resident[0] if resident else None))
    evicted = evict_others(keep)
    if not evicted:
        print("\nnothing to evict - endpoint already clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
