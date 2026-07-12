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
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from pathlib import Path

QUEUE_DIR = Path(__file__).resolve().parents[1] / "docs" / "world" / "lm_queue"
COUNTER = QUEUE_DIR / ".counter"
LOCK_PATH = QUEUE_DIR / ".lock"

MAX_CONCURRENT = max(1, int(os.environ.get("CHIMERA_LM_CONCURRENCY", "1")))
STALE_TTL = 25.0            # a ticket unheartbeated this long = dead holder
HEARTBEAT_S = 8.0
POLL_S = 0.4
MAX_WAIT_S = float(os.environ.get("CHIMERA_LM_MAX_WAIT", "300"))

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


def lm_urlopen(req, timeout: float = 600.0, agent: str = None):
    """Drop-in for urllib.request.urlopen against the LM endpoint, fair-queued.
    Holds a slot only for the network+generation, then releases. Waiting for a
    slot never consumes `timeout` — that budget is for the call itself."""
    ticket, waited = _acquire(agent)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
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
