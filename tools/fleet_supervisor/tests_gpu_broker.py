# fleet_supervisor/tests_gpu_broker.py -- the FALSIFIER SUITE for the GPU-broker
# lane (Astra round 6, "GPU broker" row of the preregistered lanes).
#
# Rejection conditions (astra-round6-answer-20260922.md, verbatim):
#   "Mixed capture/judge workload plus simulated reservation loss |
#    Overlapping exclusive reservations; a lost heartbeat grants a second owner;
#    queue wait mislabeled as model failure" + (section 3) "A broker restart must
#    reconnect to that worker, not kill it or launch a duplicate."
#
# HONEST SCOPE (preregistered): the operator is gaming -- a title is on the GPU
# at suite time -- so ZERO fleet GPU work happens here. Every scheduling decision,
# timeout state, label, batch cap, reservation fault and keeper reconnect is
# exercised against an INJECTED ollama-API-shaped backend with scripted latencies
# and timer-based capture stubs. Numbers produced by the scripted backend are
# reported as SCRIPTED, never as GPU measurements. The only REAL kernel-level
# measurements are the keeper/broker process-lifecycle checks and the
# P-CPUAFFINITY job-object measurement (1 s, below-normal priority).
#
# Run:  python -m tools.fleet_supervisor.tests_gpu_broker
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time

from . import broker, jobobject, keeper, registry
from .judge import BrokerLoop, FakeBackend, JudgeService
from .queue import (COMPLETED, GpuBrokerQueue, INFERENCE_TIMEOUT,
                    MODEL_LOAD_TIMEOUT, NEVER_ADMITTED_STATES,
                    QUEUE_DEADLINE_EXCEEDED, QUEUED, TERMINAL_STATES, status_of)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VALIDATION_DIR = os.path.join(REPO_ROOT, "tools", "science_funnel", "validation",
                              "gpu_broker2_20260922")
CREATE_NO_WINDOW = 0x08000000

FORBIDDEN_IN_QUEUE_LABELS = ("model", "inference", "load", "failed", "stall",
                             "timeout", "error")


def pct(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return float("nan")
    i = min(len(sorted_vals) - 1, max(0, int(round(p / 100 * (len(sorted_vals) - 1)))))
    return sorted_vals[i]


def wait_for(fn, timeout: float, interval: float = 0.1):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = fn()
        if v:
            return v
        time.sleep(interval)
    return None


def kill_by_record_identity(rec: dict) -> bool:
    """The suite's own injected fault on a keeper THIS suite started (ownership
    chain: suite -> its broker -> the durable record). Guarded by the record's
    (pid, creation_time) identity: a reused pid is never touched."""
    h = jobobject.k32.OpenProcess(
        jobobject.PROCESS_QUERY_LIMITED_INFORMATION | jobobject.PROCESS_TERMINATE,
        False, int(rec["pid"]))
    if not h:
        return False
    try:
        if jobobject.process_creation_time_us(h) != int(rec["creation_time_us"]):
            return False
        jobobject.terminate_pid_by_handle(h)
        return True
    finally:
        jobobject.close_handle(h)


def drain(loop: BrokerLoop, q: GpuBrokerQueue, max_s: float = 20.0) -> float:
    t0 = time.time()
    while time.time() - t0 < max_s:
        loop.pump()
        if all(r.state in TERMINAL_STATES for r in q.requests.values()):
            break
        time.sleep(0.01)
    return time.time() - t0


# ================================================================ checks
def check_three_timeouts(td: str) -> tuple[bool, dict]:
    """P-TIMEOUTS + F3: the three Astra states are distinct and correctly
    labeled; a pure queue wait is NEVER worded as a model failure; requests
    waiting in the queue are never sent to the backend."""
    ctl = os.path.join(td, "ctl1")
    broker.write_mode("fleet", ctl)
    q = GpuBrokerQueue(max_batch_size=4, batch_duration_cap_s=0.5)
    fb = FakeBackend()
    svc = JudgeService(control_dir=ctl, backend=fb,
                       load_client_budget_s=0.15, inference_budget_s=0.10)
    loop = BrokerLoop(control_dir=ctl, queue=q, judge=svc)

    # A pure queue-deadline expiry behind a long capture: the capture is
    # admitted FIRST (pump once), and judge A -- with a tight queue deadline --
    # waits behind the busy GPU until its deadline passes.
    cap = q.submit("capture", "cap-lane", 30.0, now=time.time(),
                   payload={"duration_s": 1.0})
    loop.pump()                       # capture becomes the current activity
    cap_admitted = cap.state in ("admitted_loading", "running")
    a = q.submit("judge", "judge-lane", 0.2, now=time.time(), model="m")
    drain(loop, q, max_s=4.0)
    loads_at_expiry = fb.count("load")
    st_a = a.state
    label_a = a.label

    # B: admitted, load stalls -> MODEL_LOAD_TIMEOUT (inference never reached)
    fb.load_stalls = True
    b = q.submit("judge", "judge-lane", 30.0, now=time.time(), model="m")
    drain(loop, q, max_s=5.0)
    st_b = b.state
    fb.load_stalls = False

    # C: load ok, inference stalls -> INFERENCE_TIMEOUT
    c = q.submit("judge", "judge-lane", 30.0, now=time.time(), model="m")
    fb.infer_stall_ids = {c.request_id}
    drain(loop, q, max_s=5.0)
    st_c = c.state

    detail = {
        "capture_admitted_first": cap_admitted,
        "A_state": st_a, "A_label": label_a,
        "B_state": st_b, "B_label": b.label,
        "C_state": st_c, "C_label": c.label,
        "backend_loads_when_A_expired": loads_at_expiry,
        "B_infer_calls": fb.count("infer"),
    }
    ok = (cap_admitted
          and st_a == QUEUE_DEADLINE_EXCEEDED
          and st_b == MODEL_LOAD_TIMEOUT
          and st_c == INFERENCE_TIMEOUT
          and loads_at_expiry == 0                       # never sent while waiting
          and len({st_a, st_b, st_c}) == 3               # three DISTINCT states
          and "AFTER admission" in (b.label or "")
          and "ready" in (c.label or ""))
    # F3 scan: a never-admitted request's label must be queue-worded only
    for r in (a,):
        low = (r.label or "").lower()
        if r.state not in NEVER_ADMITTED_STATES:
            ok = False
        if any(w in low for w in FORBIDDEN_IN_QUEUE_LABELS):
            ok = False
        if not any(w in low for w in ("deferred", "refused", "cancelled")):
            ok = False
    detail["f3_scan"] = "PASS" if ok else "FAIL"
    return ok, detail


def check_mixed_overlaps(td: str) -> tuple[bool, dict]:
    """F1/P-NOVERLAP + M1 latency percentiles: mixed capture/judge load under
    contention; exclusive grants must never overlap; every judge batch must run
    acquire -> load -> ... -> unload -> release in that order."""
    ctl = os.path.join(td, "ctl2")
    broker.write_mode("fleet", ctl)
    q = GpuBrokerQueue(max_batch_size=4, batch_duration_cap_s=0.6)
    fb = FakeBackend(load_latency_s=0.04, infer_latency_s=0.015)
    svc = JudgeService(control_dir=ctl, backend=fb)
    loop = BrokerLoop(control_dir=ctl, queue=q, judge=svc)

    t0 = time.time()
    for i in range(6):
        q.submit("capture", f"cap-lane-{i % 2}", 30.0, now=time.time(),
                 payload={"duration_s": 0.04 + 0.02 * (i % 3)})
    for i in range(8):
        q.submit("judge", f"judge-lane-{i % 2}", 30.0, now=time.time(), model="m")
    drain(loop, q)
    wall = time.time() - t0

    overlaps = q.ledger.overlapping_pairs()
    ev = svc.events
    order_ok = True
    for phase in ("reservation_acquired", "model_loaded", "model_unloaded",
                  "reservation_released"):
        if phase not in ev:
            order_ok = False
    if order_ok:
        # every load must sit between ITS acquire and ITS unload+release
        idx_acquire, idx_load = ev.index("reservation_acquired"), ev.index("model_loaded")
        idx_unload, idx_release = ev.index("model_unloaded"), ev.index("reservation_released")
        order_ok = idx_acquire < idx_load < idx_unload < idx_release

    waits = {"capture": [], "judge": []}
    for r in q.requests.values():
        if r.admitted_ts is not None:
            waits[r.kind].append(r.admitted_ts - r.enqueued_ts)
    for k in waits:
        waits[k].sort()
    m1 = {k: {"n": len(v), "p50_s": round(pct(v, 50), 3),
              "p95_s": round(pct(v, 95), 3), "max_s": round(pct(v, 100), 3)}
          for k, v in waits.items()}
    completed = sum(1 for r in q.requests.values() if r.state == "completed")

    detail = {"grants": len(q.ledger.grants), "overlapping_pairs": len(overlaps),
              "ordering": "PASS" if order_ok else "FAIL",
              "completed": completed, "submitted": len(q.requests),
              "queue_latency_percentiles_BY_KIND_SCRIPTED": m1,
              "wall_s": round(wall, 3)}
    ok = (not overlaps and order_ok and completed == len(q.requests)
          and len(q.ledger.grants) > 0)
    return ok, detail


def check_batch_amortization(td: str) -> tuple[bool, dict]:
    """M2/P-BATCH: batching amortizes model loads; the batch duration cap holds;
    a capture arriving mid-run waits no longer than the batch cap."""
    ctl = os.path.join(td, "ctl3")
    broker.write_mode("fleet", ctl)
    loads_per_judge = {}
    capture_wait = None
    walls = []
    for label, max_batch in (("unbatched", 1), ("batched", 4)):
        q = GpuBrokerQueue(max_batch_size=max_batch, batch_duration_cap_s=0.6)
        fb = FakeBackend(load_latency_s=0.05, infer_latency_s=0.02)
        svc = JudgeService(control_dir=ctl, backend=fb)
        loop = BrokerLoop(control_dir=ctl, queue=q, judge=svc)
        for i in range(8):
            q.submit("judge", "jl", 30.0, now=time.time(), model="m")
        if label == "batched":
            # a capture arrives while judge batches are still running: bounded wait
            time.sleep(0.02)
            capture = q.submit("capture", "cl", 30.0, now=time.time(),
                               payload={"duration_s": 0.02})
        drain(loop, q)
        loads_per_judge[label] = fb.count("load") / 8.0
        if label == "batched":
            capture_wait = (capture.admitted_ts or time.time()) - capture.enqueued_ts
        # batch walls from a same-config pass (reports carry them)
        q2 = GpuBrokerQueue(max_batch_size=max_batch, batch_duration_cap_s=0.6)
        fb2 = FakeBackend(load_latency_s=0.05, infer_latency_s=0.02)
        svc2 = JudgeService(control_dir=ctl, backend=fb2)
        loop2 = BrokerLoop(control_dir=ctl, queue=q2, judge=svc2)
        for i in range(8):
            q2.submit("judge", "jl", 30.0, now=time.time(), model="m")
        while any(r.state == QUEUED for r in q2.requests.values()):
            out = loop2.pump()
            if out.get("pump") == "judge_batch":
                w = out["report"].get("batch_wall_s")
                if max_batch == 4:
                    walls.append(w)
            time.sleep(0.005)

    amort = loads_per_judge["unbatched"] / max(loads_per_judge["batched"], 1e-9)
    detail = {"loads_per_judge_SCRIPTED": loads_per_judge,
              "amortization_factor": round(amort, 2),
              "batch_walls_s_cap_0.6": walls,
              "capture_wait_s": round(capture_wait, 3)}
    ok = (loads_per_judge["unbatched"] == 1.0
          and loads_per_judge["batched"] <= 0.25 + 1e-9
          and amort >= 3.5
          and all(w is not None and w <= 0.6 for w in walls)
          and capture_wait <= 0.6 + 0.5)
    return ok, detail


def check_aging_starvation(td: str) -> tuple[bool, dict]:
    """P-AGING (synthetic clock): under a continuous tighter-deadline capture
    flood, the aged queue bounds the judge's wait (~half the flood slack delta);
    the unaged baseline drives it to the deadline's edge."""
    def run(gain: float, horizon: float) -> dict:
        q = GpuBrokerQueue(aging_gain=gain)
        j = q.submit("judge", "judge-lane", 120.0, now=0.0, model="m")
        served = 0
        t = 0.0
        step = 0.05
        while t <= horizon:
            q.submit("capture", "cap-lane", 2.0, now=t, payload={"duration_s": 0})
            q.expire_pass(now=t)
            adm = q.admit_pass(now=t, gpu_free=True)
            if adm is not None:
                for r in adm.members:
                    r.admitted_ts = t
                    if r is not j:
                        # the zero-duration capture stub completes immediately
                        r.state = COMPLETED
                        r.completed_ts = t
                        served += 1
            if j.admitted_ts is not None:
                break
            t += step
        return {"admitted_at": (j.admitted_ts if j.admitted_ts is not None else None),
                "expired": j.state == QUEUE_DEADLINE_EXCEEDED,
                "captures_served": served}

    aged = run(1.0, horizon=130.0)
    unaged = run(0.0, horizon=130.0)
    aged_wait = aged["admitted_at"]
    unaged_wait = unaged["admitted_at"]
    detail = {"aged_judge_wait_s": aged_wait, "unaged_judge_wait_s": unaged_wait,
              "aged_expired": aged["expired"], "unaged_expired": unaged["expired"],
              "note": "gain 1.0 bound = (judge_slack - capture_slack)/2 = (120-2)/2 = 59; "
                      "gain 0 drifts to (deadline - capture_slack) and ANY tick past "
                      "120 with a competing lower score expires it"}
    ok = (aged_wait is not None and 50.0 <= aged_wait <= 70.0
          and not aged["expired"]
          and unaged_wait is not None and unaged_wait >= 110.0)
    return ok, detail


def check_gaming(td: str) -> tuple[bool, dict]:
    """Rule 1: gaming admits no fleet GPU work; judges stay VISIBLY deferred;
    the abort path unloads BEFORE releasing."""
    ctl = os.path.join(td, "ctl5")
    broker.write_mode("gaming", ctl)
    q = GpuBrokerQueue()
    fb = FakeBackend()
    svc = JudgeService(control_dir=ctl, backend=fb)
    loop = BrokerLoop(control_dir=ctl, queue=q, judge=svc)
    j = q.submit("judge", "jl", 30.0, now=time.time(), model="m")
    out = loop.pump()
    pumped_gaming = out.get("pump") == "gaming"
    st = status_of(q, j.request_id, now=time.time())
    deferred_label = "deferred" in (st["label"] or "").lower()

    # abort ordering: unload BEFORE release, members requeued as deferred.
    # (The abort path's unload is the CONTRACT, not a violation: gaming must
    # unload fleet-owned judge models. The violation would be a model call
    # while gaming -- counted before the abort, below.)
    calls_while_gaming = fb.count("load") + fb.count("infer")
    broker.write_mode("fleet", ctl)
    ok2, _ = svc._try_acquire()
    from .queue import BatchWindow
    bw = BatchWindow(closed_at_ts=time.time() + 1.0)
    bw.members = [j]
    j.state = QUEUED
    svc.events = []
    abort = svc.abort_for_gaming(bw, model=fb.model)
    ev = svc.events
    unloaded_in_abort = fb.count("unload") >= 1
    detail = {"pump_result": out.get("pump"), "status_label": st["label"],
              "model_calls_while_gaming": calls_while_gaming,
              "abort_unloaded_model": unloaded_in_abort,
              "abort_events": ev, "requeued": abort["requeued"]}
    ok = (pumped_gaming and deferred_label and st["state"] == QUEUED
          and calls_while_gaming == 0
          and unloaded_in_abort
          and ev.index("model_unloaded") < ev.index("reservation_released")
          and abort["requeued"] == [j.request_id])
    return ok, detail


TRAINER_SRC = ("import sys, time; time.sleep(float(sys.argv[1])); "
               "open(sys.argv[2], 'w').write('done')")


def _spawn_ensure(tmp: str, run_id: str, trainer_cmd: list[str], expected_s: float,
                  log: str, loop_s: float = 0.0, hb: float = 0.5) -> subprocess.Popen:
    cmd = [sys.executable, "-m", "tools.fleet_supervisor.keeper",
           "--records", os.path.join(tmp, "records"),
           "--control", os.path.join(tmp, "ctl"),
           "--registry", os.path.join(tmp, "registry.jsonl"),
           "ensure", "--run-id", run_id,
           "--trainer-cmd", json.dumps(trainer_cmd),
           "--expected-seconds", str(expected_s),
           "--hb-seconds", str(hb), "--log", log]
    if loop_s:
        cmd += ["--loop-seconds", str(loop_s)]
    # the handle is duplicated by the child at spawn; closing ours keeps the
    # suite's temp dirs removable on Windows (open handles block rmtree)
    with open(log + ".out", "w", encoding="utf-8") as out:
        return subprocess.Popen(cmd, cwd=REPO_ROOT, stdout=out,
                                stderr=subprocess.STDOUT,
                                creationflags=CREATE_NO_WINDOW)


def check_keeper_reconnect(td: str) -> tuple[bool, dict]:
    """P-KEEPERRECONNECT + F4 + P-EXPIRED, with REAL processes: a broker restart
    (kill mid-loop) must reconnect to the live keeper -- never kill it, never
    duplicate it; the passed expected-end keeps the reservation occupied until
    completion is verified; while training holds the GPU, queued judge requests
    stay deferred and are never sent to the backend."""
    # NOTE: _spawn_ensure points its child at <td>/ctl (the same dir this check
    # polls) -- the earlier draft polled <td>/ctl6 while the child wrote to
    # <td>/ctl: a perfectly healthy keeper "invisible" to the observer.
    ctl = os.path.join(td, "ctl")
    os.makedirs(ctl, exist_ok=True)
    broker.write_mode("fleet", ctl)
    records = os.path.join(td, "records")
    reg = os.path.join(td, "registry.jsonl")
    marker = os.path.join(td, "marker6.done")
    trainer = [sys.executable, "-c", TRAINER_SRC, "4.0", marker]

    d: dict = {}
    ok = True

    # broker1: starts the keeper, exits (its death must not matter -- and does not)
    b1 = _spawn_ensure(td, "run-R1", trainer, expected_s=1.5,
                       log=os.path.join(td, "broker1.log"))

    def _live_with_reservation():
        r = keeper.live_keeper_for(records, "run-R1", hb_stale_s=3.0)
        res = broker.read_reservation(ctl) or {}
        return r if (r and res.get("owner_id") == r.get("keeper_id")) else None

    rec = wait_for(_live_with_reservation, timeout=12.0)
    ok &= rec is not None
    if not rec:
        b1.kill()
        b1.wait(5)
        # rich diagnosis: what did the child actually do?
        recs_dump = {}
        if os.path.isdir(records):
            for f in os.listdir(records):
                if f.endswith(".json"):
                    recs_dump[f] = keeper.read_record(os.path.join(records, f))
        return False, {"error": "keeper never became live",
                       "b1_log": _slurp(td, "broker1.log"),
                       "records": recs_dump,
                       "reservation": broker.read_reservation(ctl),
                       "registry_events": _registry_events(reg)}
    kid, pid, ctime = rec["keeper_id"], rec["pid"], rec["creation_time_us"]
    d["keeper"] = {"keeper_id": kid, "pid": pid}
    ok &= broker.reservation_state(broker.read_reservation(ctl)) == "active"
    d["reservation_while_training"] = (broker.read_reservation(ctl) or {}).get("owner_id")

    # while training holds the GPU: queued judges stay deferred, never sent
    q = GpuBrokerQueue()
    fb = FakeBackend()
    svc = JudgeService(control_dir=ctl, backend=fb)
    loop = BrokerLoop(control_dir=ctl, queue=q, judge=svc)
    j = q.submit("judge", "jl", 60.0, now=time.time(), model="m")
    out = loop.pump()
    d["pump_while_training"] = out.get("pump")
    ok &= out.get("pump") == "deferred" and fb.count("load") == 0 and j.state == QUEUED

    # broker2: the LONG-RUNNING broker; it must ADOPT (never start a duplicate)
    log2 = os.path.join(td, "broker2.log")
    b2 = _spawn_ensure(td, "run-R1", trainer, expected_s=1.5, log=log2, loop_s=4.0)
    time.sleep(1.2)
    log2_adopted = _log_actions(td, "broker2.log")
    d["broker2_actions"] = log2_adopted
    ok &= "adopt" in log2_adopted and "start" not in log2_adopted

    # the expected end (1.5 s) passes while the keeper runs: STILL OCCUPIED
    passed = wait_for(lambda: (time.time() - rec["started_ts"] > 2.2) or None,
                      timeout=5.0, interval=0.05)
    time.sleep(0.1)
    st = broker.reservation_state(broker.read_reservation(ctl))
    d["state_after_expected_end"] = st
    ok &= st == "expired_pending"
    comp = {"session_id": "competitor-1", "owner_lane": "competitor",
            "worktree": None, "command": ["cmd", "/c", "exit"], "ports": [],
            "kind": "gpu_phase",
            "resources": {"cpu_pct": None, "mem_gib": 8.0, "max_procs": 64}}
    c_ok, c_why = broker.admit(comp, control_dir=ctl, registry_path=reg)
    d["competitor_admitted_after_expected_end"] = c_ok
    d["competitor_why"] = c_why
    ok &= not c_ok

    # KILL the broker mid-loop (real kill, launch-owned handle)
    b2.kill()
    b2.wait(5)
    id_before = (pid, ctime)
    time.sleep(0.8)
    rec2 = keeper.read_record(keeper.record_path(records, _record_name(records, "run-R1")))
    alive_after_kill = jobobject.process_running(rec2["pid"], rec2["creation_time_us"])
    hb_advancing = rec2["heartbeat_ts"] > rec["heartbeat_ts"]
    d["after_broker_kill"] = {"identity_unchanged": (rec2["pid"], rec2["creation_time_us"]) == id_before,
                              "keeper_alive": alive_after_kill, "heartbeat_advanced": hb_advancing}
    ok &= alive_after_kill and hb_advancing and (
        rec2["pid"], rec2["creation_time_us"]) == id_before

    # broker3: the RESTARTED broker: adopts exactly the same keeper
    log3 = os.path.join(td, "broker3.log")
    b3 = _spawn_ensure(td, "run-R1", trainer, expected_s=1.5, log=log3, loop_s=1.2)
    wait_for(lambda: len(_log_actions(td, "broker3.log")) >= 2, timeout=6.0)
    acts3 = _log_actions(td, "broker3.log")
    d["broker3_actions"] = acts3
    live_records = [f for f in os.listdir(records) if f.endswith(".json")
                    and (keeper.read_record(os.path.join(records, f)) or {}).get("run_id") == "run-R1"]
    d["keeper_records_for_run"] = len(live_records)
    ok &= "adopt" in acts3 and "start" not in acts3 and len(live_records) == 1

    # completion verified -> only now is the reservation released
    done = wait_for(lambda: (keeper.read_record(keeper.record_path(
        records, _record_name(records, "run-R1"))) or {}).get("state") == "done",
        timeout=10.0)
    d["keeper_state_final"] = (keeper.read_record(keeper.record_path(
        records, _record_name(records, "run-R1"))) or {}).get("state")
    st_final = broker.reservation_state(broker.read_reservation(ctl))
    d["reservation_final"] = st_final
    ok &= bool(done) and st_final == "released" and os.path.exists(marker)
    reg_events = _registry_events(reg)
    d["keeper_completed_event"] = any(e.get("event") == "keeper_completed" for e in reg_events)
    ok &= d["keeper_completed_event"]

    # cross-process handoff: with the GPU free the SAME queue now admits + judges
    drain(loop, q)
    d["judge_after_training"] = j.state
    ok &= j.state == "completed" and fb.count("load") >= 1

    for b in (b1, b3):
        if b.poll() is None:
            b.kill(); b.wait(5)
    return ok, d


def _record_name(records: str, run_id: str) -> str:
    for f in os.listdir(records):
        if f.endswith(".json") and (keeper.read_record(os.path.join(records, f)) or {}).get("run_id") == run_id:
            return f[:-5]
    raise FileNotFoundError(run_id)


def _slurp(td: str, name: str) -> str:
    try:
        with open(os.path.join(td, name + ".out"), "r", encoding="utf-8") as f:
            return f.read()[-2000:]
    except OSError:
        return ""


def _log_actions(td: str, name: str) -> list[str]:
    try:
        with open(os.path.join(td, name), "r", encoding="utf-8") as f:
            return [json.loads(line).get("action") for line in f if line.strip()]
    except OSError:
        return []


def _registry_events(reg: str) -> list[dict]:
    out = []
    try:
        with open(reg, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
    except OSError:
        pass
    return out


def check_uncertain(td: str) -> tuple[bool, dict]:
    """F2/P-UNCERTAIN: a killed keeper mid-run and a corrupted heartbeat each
    leave the reservation UNCERTAIN (locked + alerted, never auto-granted); the
    trainer tree dies with its keeper (containment); only an audited admin
    release frees the GPU; a live keeper's resumed heartbeat heals a transient
    stall WITHOUT admin action."""
    ctl = os.path.join(td, "ctl7")
    os.makedirs(ctl, exist_ok=True)
    broker.write_mode("fleet", ctl)
    records = os.path.join(td, "records7")
    reg = os.path.join(td, "registry7.jsonl")
    marker = os.path.join(td, "marker7.done")
    trainer = [sys.executable, "-c", TRAINER_SRC, "6.0", marker]
    d: dict = {}
    ok = True

    # --- run 1: kill the keeper mid-run (simulated reservation loss)
    b1 = _spawn_ensure7(td, "run-K", trainer, 30.0, os.path.join(td, "k1.log"), ctl, records, reg)

    def _live7(run_id):
        r = keeper.live_keeper_for(records, run_id, hb_stale_s=2.0)
        res = broker.read_reservation(ctl) or {}
        return r if (r and res.get("owner_id") == r.get("keeper_id")) else None

    rec = wait_for(lambda: _live7("run-K"), timeout=12.0)
    ok &= rec is not None
    if not rec:
        b1.kill()
        return False, {"error": "keeper not live", "log": _slurp7(td, "k1.log")}
    time.sleep(1.0)   # let the trainer be well underway
    killed = kill_by_record_identity(rec)
    d["keeper_killed_by_identity"] = killed
    ok &= killed
    time.sleep(2.6)   # heartbeat goes stale past the suite's 2.0 s threshold

    rep = keeper.reconcile_keepers(records, control_dir=ctl, registry_path=reg,
                                   hb_stale_s=2.0)
    d["reconcile_after_kill"] = {"lost": len(rep["lost"]),
                                 "uncertain": len(rep["uncertain"]),
                                 "adopted": len(rep["adopted"])}
    st = broker.reservation_state(broker.read_reservation(ctl))
    d["reservation_state_after_kill"] = st
    ok &= (len(rep["lost"]) + len(rep["uncertain"]) == 1 and rep["adopted"] == []
           and st == "uncertain")
    comp = {"session_id": "intruder-1", "owner_lane": "intruder", "worktree": None,
            "command": ["cmd", "/c", "exit"], "ports": [], "kind": "gpu_phase",
            "resources": {"cpu_pct": None, "mem_gib": 8.0, "max_procs": 64}}
    c_ok, c_why = broker.admit(comp, control_dir=ctl, registry_path=reg)
    d["second_owner_admitted"] = c_ok
    d["second_owner_why"] = c_why
    ok &= not c_ok
    alerts = [e for e in _registry_events7(reg) if e.get("event") == "keeper_alert"]
    d["registry_alerts"] = [a.get("reason") for a in alerts]
    ok &= len(alerts) >= 1
    # containment: the trainer tree died WITH its keeper (KILL_ON_JOB_CLOSE)
    time.sleep(1.0)
    d["trainer_marker_absent"] = not os.path.exists(marker)
    ok &= d["trainer_marker_absent"]
    # a duplicate start is refused while the reservation is locked
    dup = keeper.start_keeper(records_dir=records, control_dir=ctl, registry_path=reg,
                              run_id="run-K", trainer_cmd=trainer, expected_seconds=30.0,
                              hb_stale_s=2.0)
    d["duplicate_start_refused"] = (not dup.get("started"))
    ok &= not dup.get("started")
    # the ONLY escape: audited admin release
    rel = keeper.admin_release(control_dir=ctl, registry_path=reg,
                               reason="suite fault recovery (keeper killed)",
                               released_by="broker2-suite")
    st2 = broker.reservation_state(broker.read_reservation(ctl))
    d["after_admin_release"] = st2
    ok &= st2 == "released" and rel["released"]
    ok &= any(e.get("event") == "admin_release" for e in _registry_events7(reg))

    # --- run 2: corrupt the heartbeat of a LIVE keeper (transient stall)
    marker2 = os.path.join(td, "marker7b.done")
    trainer2 = [sys.executable, "-c", TRAINER_SRC, "3.0", marker2]
    b2 = _spawn_ensure7(td, "run-L", trainer2, 30.0, os.path.join(td, "k2.log"), ctl, records, reg)
    rec2 = wait_for(lambda: _live7("run-L"), timeout=12.0)
    ok &= rec2 is not None
    if not rec2:
        b2.kill()
        return False, {"error": "keeper2 not live", "log": _slurp7(td, "k2.log")}
    # corrupt: rewind the heartbeat (record corruption / stall simulation)
    corrupt = dict(rec2)
    corrupt["heartbeat_ts"] = time.time() - 999.0
    keeper.write_record(keeper.record_path(records, _record_name7(records, "run-L")), corrupt)
    rep2 = keeper.reconcile_keepers(records, control_dir=ctl, registry_path=reg,
                                    hb_stale_s=2.0)
    st3 = broker.reservation_state(broker.read_reservation(ctl))
    d["corrupted_reconcile"] = {"uncertain": len(rep2["uncertain"]),
                                "reservation_state": st3}
    ok &= len(rep2["uncertain"]) == 1 and st3 == "uncertain"
    c2_ok, _ = broker.admit(dict(comp, session_id="intruder-2"), control_dir=ctl,
                            registry_path=reg)
    ok &= not c2_ok
    # the LIVE keeper's own next heartbeat heals it (identity alive, liveness proven)
    healed = wait_for(lambda: (keeper.live_keeper_for(records, "run-L", hb_stale_s=2.0)
                               and broker.reservation_state(
                                   broker.read_reservation(ctl)) == "active"),
                      timeout=6.0)
    d["healed_by_heartbeat"] = bool(healed)
    ok &= bool(healed)
    done2 = wait_for(lambda: (keeper.read_record(keeper.record_path(
        records, _record_name7(records, "run-L"))) or {}).get("state") == "done",
        timeout=12.0)
    ok &= bool(done2)
    for b in (b1, b2):
        if b.poll() is None:
            b.kill(); b.wait(5)
    return ok, d


def _spawn_ensure7(td, run_id, trainer_cmd, expected_s, log, ctl, records, reg):
    cmd = [sys.executable, "-m", "tools.fleet_supervisor.keeper",
           "--records", records, "--control", ctl, "--registry", reg,
           "ensure", "--run-id", run_id,
           "--trainer-cmd", json.dumps(trainer_cmd),
           "--expected-seconds", str(expected_s),
           "--hb-seconds", "0.5", "--log", log]
    with open(log + ".out", "w", encoding="utf-8") as out:
        return subprocess.Popen(cmd, cwd=REPO_ROOT, stdout=out,
                                stderr=subprocess.STDOUT,
                                creationflags=CREATE_NO_WINDOW)


def _record_name7(records: str, run_id: str) -> str:
    for f in os.listdir(records):
        if f.endswith(".json") and (keeper.read_record(os.path.join(records, f)) or {}).get("run_id") == run_id:
            return f[:-5]
    raise FileNotFoundError(run_id)


def _slurp7(td, name):
    try:
        with open(os.path.join(td, name + ".out"), "r", encoding="utf-8") as f:
            return f.read()[-2000:]
    except OSError:
        return ""


def _registry_events7(reg: str) -> list[dict]:
    out = []
    try:
        with open(reg, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
    except OSError:
        pass
    return out


SPINNER_SRC = (
    "import subprocess, sys, time\n"
    "MODE, D, OUT = sys.argv[1], float(sys.argv[2]), sys.argv[3]\n"
    "if MODE == 'child':\n"
    "    t0 = time.time()\n"
    "    while time.time() - t0 < D:\n"
    "        pass\n"
    "    open(OUT, 'w').write(str(time.process_time()))\n"
    "else:\n"
    "    kids = [subprocess.Popen([sys.executable, sys.argv[0], 'child', str(D),\n"
    "                              OUT + f'.{i}.txt']) for i in range(8)]\n"
    "    for k in kids:\n"
    "        k.wait()\n"
    "    total = 0.0\n"
    "    for i in range(8):\n"
    "        try:\n"
    "            total += float(open(OUT + f'.{i}.txt').read())\n"
    "        except OSError:\n"
    "            pass\n"
    "    open(OUT, 'w').write(str(total))\n")


def check_cpu_affinity(td: str) -> tuple[bool, dict]:
    """P-CPUAFFINITY: where CPU-RATE caps are unenforceable on this build
    (F-CPURATE), an AFFINITY partition IS enforceable: 8 spinner PROCESSES
    pinned to 2 of 32 logical processors must accrue ~2 cores of CPU time;
    unpinned they accrue ~8. (Python THREADS cannot show this -- the GIL makes
    8 threads measure ~1 core; the first draft of this check proved that on
    itself, so the spinner uses real child processes.)"""
    spinner = os.path.join(td, "spinner.py")
    with open(spinner, "w", encoding="utf-8") as f:
        f.write(SPINNER_SRC)

    def measure(mask: int | None) -> dict:
        import uuid
        out_file = os.path.join(td, f"spin_{mask}.txt")
        job = jobobject.create_job(
            f"Local\\ChimeraFleetJob.suite-affinity-{mask}-{uuid.uuid4().hex[:6]}",
            mem_gib=None, max_procs=None, affinity_mask=mask)
        proc = jobobject.create_suspended_process(
            [sys.executable, spinner, "root", "1.0", out_file], None,
            priority_class=jobobject.BELOW_NORMAL_PRIORITY_CLASS)
        jobobject.assign_process_to_job(job, proc["process_handle"])
        t0 = time.time()
        jobobject.resume_process(proc)
        jobobject.wait_process(proc["process_handle"], 15000)
        wall = time.time() - t0
        jobobject.close_handle(proc["process_handle"])
        jobobject.close_handle(proc["thread_handle"])
        jobobject.close_handle(job)
        with open(out_file, "r", encoding="utf-8") as f:
            cpu_s = float(f.read().strip())
        return {"wall_s": round(wall, 3), "cpu_s": round(cpu_s, 3),
                "cores_effective": round(cpu_s / max(wall - 0.35, 0.1), 2)}

    pinned = measure(0b11)
    unpinned = measure(None)
    detail = {"pinned_to_2_of_32_LPs": pinned, "unpinned_8_threads": unpinned,
              "note": "create_job verified the affinity by READBACK before use "
                      "(the phase-1 wrong-class trap); 1 s at below-normal priority"}
    ok = (pinned["cores_effective"] <= 3.0
          and unpinned["cores_effective"] >= 5.0
          and unpinned["cores_effective"] / max(pinned["cores_effective"], 0.1) >= 2.0)
    return ok, detail


# ================================================================ runner
CHECKS = [
    ("TIMEOUTS_three_states_F3", check_three_timeouts),
    ("MIXED_overlaps_F1_latency", check_mixed_overlaps),
    ("BATCH_amortization_M2", check_batch_amortization),
    ("AGING_starvation_bound", check_aging_starvation),
    ("GAMING_defer_and_abort_order", check_gaming),
    ("KEEPER_reconnect_F4_expired", check_keeper_reconnect),
    ("UNCERTAIN_kill_and_corrupt_F2", check_uncertain),
    ("CPUAFFINITY_measured_alternative", check_cpu_affinity),
]


def main(argv=None) -> int:
    results = {}
    with tempfile.TemporaryDirectory(prefix="gpu-broker2-suite-") as td:
        for name, fn in CHECKS:
            t0 = time.time()
            try:
                ok, detail = fn(td)
            except Exception as e:   # a crash IS a red result, kept verbatim
                ok, detail = False, {"exception": repr(e)}
            results[name] = {"pass": bool(ok), "seconds": round(time.time() - t0, 2),
                             "detail": detail}
            print(f"[{'PASS' if ok else 'FAIL'}] {name} "
                  f"({results[name]['seconds']}s)", flush=True)
        suite_pass = all(r["pass"] for r in results.values())
        # environment honesty: what was on the GPU while this ran (read-only)
        try:
            games = [p for p in jobobject.enumerate_processes()
                     if "shipping" in (p["name"] or "").lower()
                     or p["name"] in ("WardogsClient-Win64-Shipping.exe",)]
            results["environment"] = {
                "note": "CPU-only suite; zero fleet GPU work (operator may be gaming)",
                "game_like_processes_seen": [g["name"] for g in games],
            }
        except Exception:
            pass
        os.makedirs(VALIDATION_DIR, exist_ok=True)
        with open(os.path.join(VALIDATION_DIR, "suite_results.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"suite_pass": suite_pass, "checks": results}, f, indent=1)
        print(json.dumps({"suite_pass": suite_pass}, indent=1))
        return 0 if suite_pass else 1


if __name__ == "__main__":
    sys.exit(main())
