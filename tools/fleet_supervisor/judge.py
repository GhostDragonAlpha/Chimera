# fleet_supervisor/judge.py -- the dedicated fleet judge service (Astra round 6,
# section 3): ONE loaded model, ONE parallel request, under the supervisor.
#
# Contract (astra-round6-answer-20260922.md, verbatim-cited):
#   "Start the dedicated fleet Ollama instance with one loaded model and one
#    parallel request. Preload after obtaining the reservation; retain it during
#    a bounded judging batch; unload before releasing the reservation."
#   "Gaming mode: admit no fleet GPU work; unload fleet-owned judge models."
#   OLLAMA_LOAD_TIMEOUT: "current Ollama source exposes OLLAMA_LOAD_TIMEOUT,
#    defaulting to five minutes, for stalled model loading. Verify the installed
#    version and distinguish this from client/proxy deadlines."
#
# MEASURED (this lane, 2026-09-22, installed binary + tagged source):
#   - installed: `ollama version is 0.34.2`; the binary contains the literal
#     OLLAMA_LOAD_TIMEOUT (grep -a on ollama.exe), alongside OLLAMA_NUM_PARALLEL,
#     OLLAMA_MAX_LOADED_MODELS, OLLAMA_KEEP_ALIVE, OLLAMA_MAX_QUEUED.
#   - source tag v0.34.2 envconfig/config.go: LoadTimeout() default 5m
#     ("How long to allow model loads to STALL before giving up"); values <= 0
#     mean infinite. It is a SERVER-SIDE scheduler stall timeout -- a different
#     layer from this client's HTTP deadlines and from any proxy timeout.
#   Therefore the three budgets below are DISTINCT and labeled distinctly:
#     queue deadline      -> the queue's (queue.py), before any model contact
#     load-stall budget   -> what we hand the server for the load phase
#                            (server also enforces its own OLLAMA_LOAD_TIMEOUT,
#                            default 5m; our client budget defaults to 330 s =
#                            the server's 5 m + margin, and is labeled
#                            load_client_budget -- never conflated with it)
#     inference budget    -> per-request, after readiness
#
# GAMING-MACHINE NOTE (honest): the real OllamaBackend ships here but is NOT
# exercised against the GPU this lane -- the operator is gaming (a title is on
# the GPU at suite time); the no-fleet-GPU law outranks lane curiosity. The
# falsifier suite drives the service through an ollama-API-shaped FakeBackend
# with scripted latencies; Astra's rejection conditions test THIS service's
# ordering and labeling decisions, which are backend-independent.
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

from . import broker
from .queue import (ADMITTED_LOADING, BatchWindow, COMPLETED, GpuBrokerQueue,
                    INFERENCE_TIMEOUT, MODEL_LOAD_TIMEOUT, QUEUED, RUNNING,
                    Request)

# Astra's named config for the fleet judge instance: one loaded model, one
# parallel request. Real instance env (OllamaBackend.start_server):
JUDGE_SERVER_ENV = {
    "OLLAMA_MAX_LOADED_MODELS": "1",   # one loaded model
    "OLLAMA_NUM_PARALLEL": "1",        # one parallel request
    "OLLAMA_KEEP_ALIVE": "5m",         # retention is overridden per call via keep_alive
    # OLLAMA_LOAD_TIMEOUT: left at the server default (5m) unless configured;
    # verified above on the installed 0.34.2 binary.
}
DEFAULT_FLEET_JUDGE_PORT = 18114   # NEVER 11434 (the operator's instance); never 8127


class JudgeError(RuntimeError):
    pass


# ---------------------------------------------------------------- backends
class OllamaBackend:
    """The REAL fleet judge: a dedicated ollama instance on a fleet port. This
    lane never starts it (see the gaming note above); production uses:
      start_server() -> spawn `ollama serve` with JUDGE_SERVER_ENV + OLLAMA_HOST
      on the fleet port and an OLLAMA_MODELS dir OUTSIDE the operator's.
    It never attaches to, configures, or terminates any existing ollama on the
    default port -- the operator's instance is untouchable."""

    def __init__(self, *, host: str = f"127.0.0.1:{DEFAULT_FLEET_JUDGE_PORT}",
                 model: str | None = None, load_client_budget_s: float = 330.0,
                 inference_budget_s: float = 120.0):
        self.host = host
        self.base = f"http://{host}"
        self.model = model
        self.load_client_budget_s = float(load_client_budget_s)
        self.inference_budget_s = float(inference_budget_s)
        self._proc: subprocess.Popen | None = None

    # ---- low-level HTTP (stdlib only; client-side deadlines are explicit)
    def _post(self, path: str, body: dict, timeout_s: float) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}", data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise JudgeError(f"ollama {path} failed: {e}") from e
        except TimeoutError:
            raise   # our own socket deadline: classified by the caller's phase

    def reachable(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base}/api/tags", timeout=2.0) as r:
                return r.status == 200
        except Exception:
            return False

    def start_server(self, *, models_dir: str, server_startup_s: float = 20.0) -> dict:
        """Spawn OUR OWN dedicated instance on the fleet port. Never touches an
        already-running ollama: if something answers on the fleet port first,
        that is a config error, not ours to use."""
        if self.reachable():
            raise JudgeError(f"something already answers on {self.base}; "
                             "refusing to reuse an instance we do not own")
        env = dict(os.environ)
        env.update(JUDGE_SERVER_ENV)
        env["OLLAMA_HOST"] = self.host
        env["OLLAMA_MODELS"] = models_dir
        env["OLLAMA_NOPRUNE"] = "1"
        env.pop("HTTP_PROXY", None), env.pop("HTTPS_PROXY", None)
        env.pop("http_proxy", None), env.pop("https_proxy", None)  # no proxy deadlines
        self._proc = subprocess.Popen(
            ["ollama", "serve"], env=env,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while time.time() - t0 < server_startup_s:
            if self.reachable():
                return {"host": self.host, "pid": self._proc.pid,
                        "startup_s": round(time.time() - t0, 3)}
            time.sleep(0.2)
        raise JudgeError(f"fleet ollama did not become reachable within {server_startup_s}s")

    def stop_server(self) -> None:
        """Terminate ONLY the process this object spawned (launch-established
        ownership); a foreign instance is never touched."""
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None

    # ---- the three phases
    def load(self, model: str, *, timeout_s: float) -> float:
        """Preload: a zero-work generate with a long keep_alive pins the model.
        Returns the measured load seconds. Raises TimeoutError on OUR client
        budget; the SERVER independently enforces its own OLLAMA_LOAD_TIMEOUT
        (default 5m) for stalled loads -- distinct layers, distinct labels."""
        t0 = time.time()
        self._post("/api/generate",
                   {"model": model, "prompt": "", "keep_alive": "5m", "stream": False},
                   timeout_s=timeout_s)
        return time.time() - t0

    def infer(self, model: str, prompt: str, *, timeout_s: float,
              keep_alive_s: float = 0.0) -> dict:
        body = {"model": model, "prompt": prompt, "stream": False}
        if keep_alive_s:
            body["keep_alive"] = int(keep_alive_s)
        return self._post("/api/generate", body, timeout_s=timeout_s)

    def unload(self, model: str, *, timeout_s: float = 30.0) -> float:
        """keep_alive=0 evicts the model BEFORE the reservation is released."""
        t0 = time.time()
        self._post("/api/generate",
                   {"model": model, "prompt": "", "keep_alive": 0, "stream": False},
                   timeout_s=timeout_s)
        return time.time() - t0


class FakeBackend:
    """Ollama-API-shaped injected backend for the falsifier suite: scripted
    latencies + failure injection; every call is RECORDED (the suite proves
    no model call happens while requests are merely queued). Mirrors the real
    backend's contract exactly: load/infer raise TimeoutError when the script
    exceeds the budget the service handed them -- the SERVICE still owns the
    classification of which phase timed out."""

    def __init__(self, *, model="fake-judge-model", load_latency_s=0.05,
                 infer_latency_s=0.02, unload_latency_s=0.01):
        self.model = model
        self.load_latency_s = load_latency_s
        self.infer_latency_s = infer_latency_s
        self.unload_latency_s = unload_latency_s
        self.calls: list[dict] = []
        self.load_stalls = False      # next load exceeds any budget
        self.infer_stall_ids: set[str] = set()

    def _rec(self, op, **kw):
        self.calls.append({"op": op, "t": time.time(), **kw})

    def load(self, model: str, *, timeout_s: float) -> float:
        self._rec("load", model=model, timeout_s=timeout_s)
        if self.load_stalls:
            time.sleep(min(timeout_s, timeout_s + 0.05))  # exceed any handed budget
            raise TimeoutError("scripted load stall")
        time.sleep(self.load_latency_s)
        return self.load_latency_s

    def infer(self, model: str, prompt: str, *, timeout_s: float,
              keep_alive_s: float = 0.0) -> dict:
        self._rec("infer", model=model, timeout_s=timeout_s)
        rid = prompt
        if rid in self.infer_stall_ids:
            time.sleep(min(timeout_s, timeout_s + 0.05))
            raise TimeoutError("scripted inference stall")
        time.sleep(self.infer_latency_s)
        return {"response": f"fake-verdict({prompt})", "done": True}

    def unload(self, model: str, *, timeout_s: float = 30.0) -> float:
        self._rec("unload", model=model)
        time.sleep(self.unload_latency_s)
        return self.unload_latency_s

    def count(self, op: str) -> int:
        return sum(1 for c in self.calls if c["op"] == op)


# ---------------------------------------------------------------- the service
class JudgeService:
    """Runs ONE bounded judging batch under the reservation, with the ordering
    the contract demands, and reports per-phase numbers.

    Ordering is ASSERTED, not convention:
      reservation acquired -> (server ready) -> preload -> members -> unload
      -> reservation released. A violation raises JudgeError (and the suite
      treats it as F-firing).

    The three timeout states are classified HERE, by phase:
      MODEL_LOAD_TIMEOUT  -- admitted, load phase exceeded the load budget
      INFERENCE_TIMEOUT   -- ready, inference exceeded the per-request budget
    (The queue deadline lives in queue.py, before any of this can run.)"""

    def __init__(self, *, control_dir: str, backend,
                 reservation_owner: str = "fleet-judge",
                 load_client_budget_s: float = 330.0,
                 inference_budget_s: float = 120.0):
        self.control_dir = control_dir
        self.backend = backend
        self.reservation_owner = reservation_owner
        self.load_client_budget_s = float(load_client_budget_s)
        self.inference_budget_s = float(inference_budget_s)
        self.events: list[str] = []   # ordering audit trail

    # -- reservation (the phase-1 file is the single coordination mechanism)
    def _try_acquire(self) -> tuple[bool, str]:
        mode = broker.read_mode(self.control_dir)
        if mode == "gaming":
            return False, "gaming mode admits no fleet GPU work; judges stay queued"
        st = broker.reservation_state(broker.read_reservation(self.control_dir))
        if st == "none":
            broker.touch_reservation(self.reservation_owner, control_dir=self.control_dir)
            self.events.append("reservation_acquired")
            return True, "acquired"
        if st == "released":
            broker.touch_reservation(self.reservation_owner, control_dir=self.control_dir)
            self.events.append("reservation_acquired")
            return True, "re-acquired after release"
        # active / expired_pending / uncertain: NEVER grab, NEVER auto-free --
        # the queue keeps holding the requests (visibly deferred).
        return False, f"reservation {st}: queued requests keep waiting (deferred)"

    def _release(self) -> None:
        broker.release_reservation(self.reservation_owner, control_dir=self.control_dir)
        self.events.append("reservation_released")

    # -- the batch
    def run_batch(self, batch: BatchWindow, *, now: float | None = None,
                  model: str | None = None) -> dict:
        """Preload AFTER the reservation; retain through the bounded batch;
        unload BEFORE release. Batch duration is capped by the BatchWindow --
        members that cannot START before the cap keep their queue deadline
        (expire_pass re-queues them honestly as deferred)."""
        now = time.time() if now is None else now
        ok, why = self._try_acquire()
        if not ok:
            return {"ran": False, "why": why, "outcomes": []}

        report: dict = {"ran": True, "outcomes": [], "load_seconds": None,
                        "unload_seconds": None, "loads": 0, "gaming_abort": False}
        t0 = time.time()
        loaded = False
        try:
            # 1. preload -- strictly AFTER the reservation
            model = model or getattr(self.backend, "model", None) or "unset-model"
            try:
                report["load_seconds"] = self.backend.load(
                    model, timeout_s=self.load_client_budget_s)
                report["loads"] = 1
                loaded = True
                self.events.append("model_loaded")
            except TimeoutError:
                self.events.append("model_load_timeout")
                for r in batch.members:
                    report["outcomes"].append(self._finish(
                        r, MODEL_LOAD_TIMEOUT,
                        "failed: model load stalled past the load budget AFTER admission "
                        "(server-side stall timeout is OLLAMA_LOAD_TIMEOUT, default 5m)",
                        now))
                return report

            # 2. members -- one at a time (one parallel request), deadline-capped
            for r in list(batch.members):
                if time.time() >= batch.closed_at_ts:
                    # hard batch cap: this member was never started; hand it back
                    # to the queue as QUEUED (its own deadline still governs).
                    r.state = QUEUED
                    r.admitted_ts = None
                    self.events.append(f"batch_cap_returned:{r.request_id}")
                    continue
                r.state = RUNNING
                try:
                    out = self.backend.infer(
                        model, r.request_id,
                        timeout_s=self.inference_budget_s,
                        keep_alive_s=max(1.0, batch.closed_at_ts - time.time()))
                    self._finish(r, COMPLETED,
                                 "completed (judged in a batch of "
                                 f"{len(batch.members)}, one shared model load)", now)
                    report["outcomes"].append(
                        {"request_id": r.request_id, "state": COMPLETED,
                         "response": out.get("response", "")})
                except TimeoutError:
                    report["outcomes"].append(self._finish(
                        r, INFERENCE_TIMEOUT,
                        "failed: inference exceeded the per-request budget AFTER the "
                        "model was ready", now))

            # 3. unload -- strictly BEFORE the release
            if loaded:
                report["unload_seconds"] = self.backend.unload(model)
                self.events.append("model_unloaded")
        finally:
            self._release()
        report["batch_wall_s"] = round(time.time() - t0, 3)
        return report

    def _finish(self, r: Request, state: str, label: str, now: float) -> dict:
        r.state = state
        r.label = label
        r.completed_ts = time.time()
        return {"request_id": r.request_id, "state": state, "label": label}

    def abort_for_gaming(self, batch: BatchWindow, *, model: str | None = None) -> dict:
        """'Gaming mode: ... unload fleet-owned judge models.' Members still
        waiting go back to QUEUED (visibly deferred; their queue deadlines keep
        running). Unload THEN release -- the ordering never changes."""
        self.events.append("gaming_abort")
        model = model or getattr(self.backend, "model", None) or "unset-model"
        try:
            self.backend.unload(model)
            self.events.append("model_unloaded")
        finally:
            self._release()
        requeued = []
        for r in batch.members:
            if r.state in (QUEUED, ADMITTED_LOADING):
                r.state = QUEUED
                r.admitted_ts = None
                requeued.append(r.request_id)
        return {"requeued": requeued}


# ---------------------------------------------------------------- the broker loop
class BrokerLoop:
    """ONE exclusive executor: ties the bounded queue (queue.py), the GPU
    reservation file, the judge service (above) and capture grants into a
    single pump loop. Exclusivity is STRUCTURAL here -- there is exactly one
    current activity, ever -- and AUDITED in the queue's GrantLedger (F1) plus
    the reservation file itself (a second acquire raises PermissionError)."""

    def __init__(self, *, control_dir: str, queue: GpuBrokerQueue, judge: JudgeService,
                 capture_run_fn=None):
        self.control_dir = control_dir
        self.q = queue
        self.judge = judge
        # Capture stubs are TIME-BASED and non-blocking: the grant holds
        # `current` until end_ts (payload duration_s) while the loop keeps
        # pumping. (A blocking stub would freeze the whole broker for the
        # capture's duration -- the wrong shape for a supervisor loop.)
        self.capture_run_fn = capture_run_fn or (lambda r: None)
        self.current: dict | None = None

    def pump(self, *, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        expired = self.q.expire_pass(now=now)

        # current activity finished?
        if self.current and now >= self.current["end_ts"]:
            kind = self.current["kind"]
            self.q.ledger.close(self.current["grant"], end_ts=now)
            for r in self.current["reqs"]:
                if r.state in (ADMITTED_LOADING, RUNNING):
                    self.judge._finish(r, COMPLETED,
                                       "completed (exclusive capture grant)", now)
            if kind == "capture":
                # the capture held the reservation under the requester's lane id
                res = broker.read_reservation(self.control_dir) or {}
                if res.get("owner_id") == self.current["owner"]:
                    broker.release_reservation(self.current["owner"],
                                               control_dir=self.control_dir)
            self.current = None

        if self.current:
            return {"pump": "busy", "current": self.current["kind"],
                    "remaining_s": round(self.current["end_ts"] - now, 3),
                    "expired": expired}

        mode = broker.read_mode(self.control_dir)
        if mode == "gaming":
            return {"pump": "gaming", "note": "no fleet GPU work admitted; "
                    "queued requests stay visibly deferred", "expired": expired}

        # cross-process exclusivity: a training keeper (or any other owner)
        # holding the reservation keeps every queued request waiting -- the
        # "do not send requests to Ollama while waiting for the GPU" rule.
        st = broker.reservation_state(broker.read_reservation(self.control_dir), now=now)
        if st not in ("none", "released"):
            return {"pump": "deferred",
                    "why": f"reservation {st}: GPU owned elsewhere; queued requests "
                           "keep waiting (visibly deferred)",
                    "expired": expired}

        adm = self.q.admit_pass(now=now, gpu_free=True)
        if adm is None:
            return {"pump": "idle", "expired": expired}

        if adm.kind == "capture":
            r = adm.members[0]
            owner = f"capture:{r.request_id}"
            try:
                broker.touch_reservation(owner, control_dir=self.control_dir,
                                         expected_end_ts=now + float(
                                             (r.payload or {}).get("duration_s", 0.05)) * 2)
            except PermissionError:
                # lost a race against another owner: back off, stay deferred
                r.state = QUEUED
                r.admitted_ts = None
                return {"pump": "deferred", "why": "reservation taken by another owner "
                        "between check and grant", "expired": expired}
            grant = self.q.ledger.open(owner, "capture", now, [r.request_id])
            self.current = {"kind": "capture", "end_ts": now + float(
                (r.payload or {}).get("duration_s", 0.05)),
                "grant": grant, "reqs": [r], "owner": owner}
            r.state = RUNNING
            self.capture_run_fn(r)
            return {"pump": "capture", "request_id": r.request_id}

        # judge batch: runs synchronously (bounded by the BatchWindow cap);
        # arrivals during the batch wait -- the cap is what bounds their wait.
        grant = self.q.ledger.open("fleet-judge", "judge_batch", now,
                                   [r.request_id for r in adm.members])
        report = self.judge.run_batch(adm.batch, now=now)
        self.q.ledger.close(grant, end_ts=time.time())
        return {"pump": "judge_batch", "report": report}
