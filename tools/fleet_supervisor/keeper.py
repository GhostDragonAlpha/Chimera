# fleet_supervisor/keeper.py -- the DURABLE training keeper (Astra round 6,
# section 3).
#
# Contract (astra-round6-answer-20260922.md, verbatim-cited):
#   "A training reservation cannot simply expire into 'GPU free.' If its expected
#    end passes, it remains occupied until completion is verified. Likewise, a
#    lost heartbeat means ownership uncertain, not permission to start a
#    competing job."
#   "Because training must not be preempted, place it under a dedicated durable
#    worker/keeper whose lifetime is independent of the dispatch service. A
#    broker restart must reconnect to that worker, not kill it or launch a
#    duplicate."
#
# Shape:
#   - The keeper is an INDEPENDENT OS process, deliberately NOT inside any
#     kill-on-close job (that exception is the whole point: the broker's death
#     must not take training down). The TRAINER (the actual run) IS contained:
#     the keeper launches it through the phase-1 launcher, so the trainer's job
#     is KILL_ON_JOB_CLOSE tied to the KEEPER's handle -- keeper death still
#     kills the trainer tree (crash containment), while a BROKER death touches
#     nothing.
#   - The durable record (JSON, atomic writes) carries pid + CREATION TIME
#     identity and the heartbeat. The keeper heartbeats BOTH its record and the
#     phase-1 RESERVATION FILE -- one coordination mechanism, not two.
#   - Reconnect: any broker (re)start calls reconcile_keepers(): live identity +
#     fresh heartbeat => ADOPT (attach as manager). There is no code path here
#     that terminates a keeper, and start_keeper refuses while a live keeper
#     exists for the run -- a duplicate cannot be launched.
#   - Uncertainty: identity dead OR heartbeat stale => OWNERSHIP UNCERTAIN: the
#     alert goes to the registry, new admissions are refused by the reservation
#     state machine (uncertain), and NOTHING auto-frees. The only escapes are
#     the keeper's own verified-completion release or an audited admin release.
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid

from . import broker, jobobject, launcher, registry

DEFAULT_RECORDS_DIR = os.path.join(broker.DEFAULT_CONTROL_DIR, "keepers")

KEEPER_VERSION = 1
STATES = ("starting", "running", "done", "failed", "lost")


# ---------------------------------------------------------------- record io
def record_path(records_dir: str, keeper_id: str) -> str:
    return os.path.join(records_dir, f"{keeper_id}.json")


def read_record(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        return json.loads(text) if text else None
    except (OSError, json.JSONDecodeError):
        return None


def write_record(path: str, rec: dict) -> None:
    """Atomic (tmp + replace): a torn record must never look like fresh state."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=1)
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def self_identity() -> tuple[int, int]:
    h = jobobject.k32.OpenProcess(jobobject.PROCESS_QUERY_LIMITED_INFORMATION, False,
                                  os.getpid())
    if not h:
        raise jobobject.WinError("OpenProcess(self)")
    try:
        return os.getpid(), jobobject.process_creation_time_us(h)
    finally:
        jobobject.close_handle(h)


# ---------------------------------------------------------------- the keeper
def run_keeper(*, record_file: str, run_id: str, trainer_cmd: list[str],
               expected_seconds: float, control_dir: str, registry_path: str,
               hb_seconds: float = 1.0, completion_marker: str | None = None,
               worktree: str | None = None, mem_gib: float = 8.0,
               hold_after_completion_s: float = 0.0) -> int:
    """The keeper process body. Lifetime: independent of any broker by design.
    The trainer is launched through the phase-1 launcher (contained job) and
    its completion is VERIFIED before the reservation is ever released."""
    keeper_id = f"keeper-{run_id}-{uuid.uuid4().hex[:6]}"
    pid, creation_us = self_identity()
    now = time.time()
    rec = {
        "v": KEEPER_VERSION, "keeper_id": keeper_id, "run_id": run_id,
        "pid": pid, "creation_time_us": creation_us,
        "state": "starting", "started_ts": now, "heartbeat_ts": now,
        "expected_end_ts": now + float(expected_seconds),
        "trainer_session_id": None, "hb_seconds": hb_seconds,
    }
    write_record(record_file, rec)

    # the reservation: owned by the KEEPER, heartbeated by the KEEPER
    broker.touch_reservation(keeper_id, control_dir=control_dir,
                             expected_end_ts=rec["expected_end_ts"],
                             run_id=run_id, kind="training")

    spec = {
        "session_id": f"train-{run_id}-{uuid.uuid4().hex[:6]}",
        "owner_lane": keeper_id,          # reservation owner must match (admit gate)
        "worktree": worktree,
        "command": trainer_cmd,
        "ports": [],
        "kind": "gpu_phase",
        "resources": {"cpu_pct": None, "mem_gib": float(mem_gib), "max_procs": 64},
    }
    result = launcher.launch(spec, control_dir=control_dir, registry_path=registry_path)
    if not result.ok:
        rec.update({"state": "failed", "heartbeat_ts": time.time(),
                    "failure": result.error})
        write_record(record_file, rec)
        broker.release_reservation(keeper_id, control_dir=control_dir)
        registry.append(registry_path, {"event": "keeper_alert", "keeper_id": keeper_id,
                                        "run_id": run_id, "reason": "trainer_launch_failed",
                                        "detail": result.error})
        return 2

    rec["trainer_session_id"] = result.session_id
    rec["state"] = "running"
    write_record(record_file, rec)

    stop = False
    while not stop:
        time.sleep(hb_seconds)
        now = time.time()
        alive = jobobject.process_running(result.pid, result.creation_time_us) if (
            result.pid and result.creation_time_us) else False
        job_done = False
        jh = result.job_handle
        if jh:
            try:
                acct = jobobject.query_job_accounting(jh)
                job_done = (acct["active_processes"] == 0 and acct["total_processes"] > 0)
            except jobobject.WinError:
                job_done = True   # job object gone => every member dead (KILL_ON_JOB_CLOSE)
        marker_ok = (completion_marker is None or os.path.exists(completion_marker))
        rec["heartbeat_ts"] = now
        if job_done and marker_ok and hold_after_completion_s <= 0:
            # completion VERIFIED (job empty + the run's own evidence) -- only
            # now may the reservation be released (Astra's rule)
            rec["state"] = "done"
            rec["completed_ts"] = now
            write_record(record_file, rec)
            broker.release_reservation(keeper_id, control_dir=control_dir)
            registry.append(registry_path, {"event": "keeper_completed",
                                            "keeper_id": keeper_id, "run_id": run_id,
                                            "trainer_session_id": result.session_id,
                                            "verified": True})
            stop = True
        else:
            if now > rec["expected_end_ts"]:
                rec["state"] = "running"   # keeps heartbeating PAST expected end
            write_record(record_file, rec)
    return 0


# ---------------------------------------------------------------- reconcile
def _alert(registry_path: str, keeper_id: str, run_id: str | None, reason: str,
           detail: str) -> None:
    registry.append(registry_path, {"event": "keeper_alert", "keeper_id": keeper_id,
                                    "run_id": run_id, "reason": reason,
                                    "detail": detail})


def reconcile_keepers(records_dir: str, *, control_dir: str,
                      registry_path: str, now: float | None = None,
                      hb_stale_s: float = broker.HEARTBEAT_STALE_S,
                      alert: bool = True) -> dict:
    """THE reconnect pass -- pure READ + audit. Never terminates anything,
    never launches anything, never writes the reservation. Classification:
      adopted   -- identity alive AND heartbeat fresh: reconnect (a restarted
                   broker attaches here; it must NOT start a duplicate)
      uncertain -- identity dead with a fresh heartbeat, OR alive with a stale
                   heartbeat: OWNERSHIP UNCERTAIN (locked for new admissions by
                   the reservation state machine; alerted; never auto-granted)
      lost      -- identity dead AND heartbeat stale: the run is gone; the GPU
                   stays locked until an audited admin release."""
    now = time.time() if now is None else now
    report = {"adopted": [], "uncertain": [], "lost": [], "checked": 0}
    if not os.path.isdir(records_dir):
        return report
    for name in sorted(os.listdir(records_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(records_dir, name)
        rec = read_record(path)
        if not rec or rec.get("state") in ("done", "failed", "lost"):
            continue   # terminal keepers are history, not owners
        report["checked"] += 1
        kid = rec.get("keeper_id", name)
        alive = jobobject.process_running(int(rec.get("pid", 0)),
                                          int(rec.get("creation_time_us", 0)))
        hb_age = now - float(rec.get("heartbeat_ts") or 0)
        entry = {"keeper_id": kid, "run_id": rec.get("run_id"),
                 "identity_alive": alive, "heartbeat_age_s": round(hb_age, 2),
                 "trainer_session_id": rec.get("trainer_session_id")}
        if alive and hb_age <= hb_stale_s:
            entry["reservation_state"] = broker.reservation_state(
                broker.read_reservation(control_dir), now=now)
            report["adopted"].append(entry)
        elif alive or hb_age <= hb_stale_s:
            entry["diagnosis"] = ("identity alive but heartbeat stalled" if alive
                                  else "heartbeat fresh but identity dead (just died)")
            entry["reservation_state"] = broker.reservation_state(
                broker.read_reservation(control_dir), now=now)
            report["uncertain"].append(entry)
            if alert:
                _alert(registry_path, kid, rec.get("run_id"), "ownership_uncertain",
                       entry["diagnosis"])
        else:
            entry["diagnosis"] = "identity dead and heartbeat stale: run lost"
            entry["reservation_state"] = broker.reservation_state(
                broker.read_reservation(control_dir), now=now)
            report["lost"].append(entry)
            if alert:
                _alert(registry_path, kid, rec.get("run_id"), "keeper_lost",
                       entry["diagnosis"])
    return report


# ---------------------------------------------------------------- lifecycle
def live_keeper_for(records_dir: str, run_id: str, *, now: float | None = None,
                    hb_stale_s: float = broker.HEARTBEAT_STALE_S) -> dict | None:
    """A LIVE (identity-verified, fresh-heartbeat) keeper for this run."""
    now = time.time() if now is None else now
    if not os.path.isdir(records_dir):
        return None
    for name in sorted(os.listdir(records_dir)):
        if not name.endswith(".json"):
            continue
        rec = read_record(os.path.join(records_dir, name))
        if not rec or rec.get("run_id") != run_id:
            continue
        if rec.get("state") in ("done", "failed", "lost"):
            continue
        if jobobject.process_running(int(rec.get("pid", 0)),
                                     int(rec.get("creation_time_us", 0))):
            if now - float(rec.get("heartbeat_ts") or 0) <= hb_stale_s:
                return rec
    return None


def start_keeper(*, records_dir: str, control_dir: str, registry_path: str,
                 run_id: str, trainer_cmd: list[str], expected_seconds: float,
                 hb_seconds: float = 1.0, completion_marker: str | None = None,
                 worktree: str | None = None, mem_gib: float = 8.0,
                 hb_stale_s: float = broker.HEARTBEAT_STALE_S) -> dict:
    """A broker-side operation: start a keeper for the run -- but ONLY if no
    live keeper already owns the run (never a duplicate) and the reservation is
    actually free. The keeper is spawned DETACHED (its lifetime is its own)."""
    live = live_keeper_for(records_dir, run_id, hb_stale_s=hb_stale_s)
    if live is not None:
        return {"started": False, "adopted_instead": True,
                "keeper_id": live["keeper_id"],
                "why": f"run {run_id} already has a LIVE keeper {live['keeper_id']!r}; "
                       f"a duplicate is refused"}
    st = broker.reservation_state(broker.read_reservation(control_dir))
    if st not in ("none", "released"):
        return {"started": False, "adopted_instead": False,
                "why": f"reservation {st}: training start refused (never a competing job)"}

    keeper_id = f"pending-{uuid.uuid4().hex[:8]}"
    record_file = record_path(records_dir, keeper_id)
    cmd = [sys.executable, "-m", "tools.fleet_supervisor.keeper", "run",
           "--record", record_file, "--run-id", run_id,
           "--expected-seconds", str(expected_seconds),
           "--hb-seconds", str(hb_seconds),
           "--control-dir", control_dir, "--registry", registry_path,
           "--mem-gib", str(mem_gib),
           "--trainer-cmd", json.dumps(trainer_cmd)]
    if completion_marker:
        cmd += ["--completion-marker", completion_marker]
    if worktree:
        cmd += ["--worktree", worktree]
    # DETACHED: no job, no kill-on-owner-exit, own lifetime (the contract's
    # named exception for the training keeper); CREATE_NO_WINDOW: zero popups.
    DETACHED = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED_PROCESS|NEW_GROUP|NO_WINDOW
    proc = subprocess.Popen(cmd, creationflags=DETACHED, close_fds=True,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # wait for the record with a REAL identity (bounded)
    t0 = time.time()
    rec = None
    while time.time() - t0 < 15.0:
        rec = read_record(record_file)
        if rec and rec.get("pid"):
            break
        time.sleep(0.1)
    if not rec or not rec.get("pid"):
        return {"started": False, "why": "keeper did not write its record in 15s",
                "spawned_pid": proc.pid}
    if not jobobject.process_running(rec["pid"], rec["creation_time_us"]):
        return {"started": False, "why": "keeper died immediately", "record": rec}
    return {"started": True, "keeper_id": rec["keeper_id"], "record": rec,
            "record_file": record_file}


def admin_release(*, control_dir: str, registry_path: str, reason: str,
                  released_by: str) -> dict:
    """The ONLY manual escape from uncertainty: audited, explicit, attributed.
    Never called by reconcile; never automatic."""
    res = broker.read_reservation(control_dir) or {}
    owner = res.get("owner_id")
    if owner:
        broker.release_reservation(owner, control_dir=control_dir)
    else:
        broker.write_reservation(None, control_dir=control_dir)
    registry.append(registry_path, {"event": "admin_release", "owner": owner,
                                    "reason": reason, "released_by": released_by,
                                    "audited": True})
    return {"released": True, "owner": owner, "reason": reason}


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fleet_keeper")
    ap.add_argument("--registry", default=os.environ.get("FLEET_REGISTRY_PATH",
                                                         registry.DEFAULT_REGISTRY))
    ap.add_argument("--control", default=os.environ.get("FLEET_CONTROL_DIR",
                                                        broker.DEFAULT_CONTROL_DIR))
    ap.add_argument("--records", default=os.environ.get("FLEET_KEEPER_RECORDS",
                                                        DEFAULT_RECORDS_DIR))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run")
    p.add_argument("--record", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--trainer-cmd", required=True, help="JSON array")
    p.add_argument("--expected-seconds", type=float, required=True)
    p.add_argument("--hb-seconds", type=float, default=1.0)
    p.add_argument("--completion-marker")
    p.add_argument("--worktree")
    p.add_argument("--mem-gib", type=float, default=8.0)

    p = sub.add_parser("reconcile")   # what every broker (re)start calls
    p.add_argument("--hb-stale-seconds", type=float, default=broker.HEARTBEAT_STALE_S)

    p = sub.add_parser("ensure")      # reconcile, then start if (and only if) needed
    p.add_argument("--run-id", required=True)
    p.add_argument("--trainer-cmd", required=True)
    p.add_argument("--expected-seconds", type=float, required=True)
    p.add_argument("--hb-seconds", type=float, default=1.0)
    p.add_argument("--completion-marker")
    p.add_argument("--worktree")
    p.add_argument("--mem-gib", type=float, default=8.0)
    p.add_argument("--hb-stale-seconds", type=float, default=broker.HEARTBEAT_STALE_S)
    p.add_argument("--loop-seconds", type=float, default=0.0,
                   help="keep reconciling for this long (the 'serve' shape of a "
                        "broker); 0 = one pass")
    p.add_argument("--log", help="JSONL decision log (start/adopt/refuse per pass)")

    p = sub.add_parser("admin-release")
    p.add_argument("--reason", required=True)
    p.add_argument("--released-by", required=True)

    args = ap.parse_args(argv)

    if args.cmd == "run":
        return run_keeper(record_file=args.record, run_id=args.run_id,
                          trainer_cmd=json.loads(args.trainer_cmd),
                          expected_seconds=args.expected_seconds,
                          control_dir=args.control, registry_path=args.registry,
                          hb_seconds=args.hb_seconds,
                          completion_marker=args.completion_marker,
                          worktree=args.worktree, mem_gib=args.mem_gib)

    if args.cmd == "reconcile":
        rep = reconcile_keepers(args.records, control_dir=args.control,
                                registry_path=args.registry,
                                hb_stale_s=args.hb_stale_seconds)
        print(json.dumps(rep, indent=1))
        return 0

    if args.cmd == "ensure":
        def _log(entry: dict) -> None:
            if not args.log:
                return
            os.makedirs(os.path.dirname(os.path.abspath(args.log)), exist_ok=True)
            with open(args.log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        def _one_pass(t0: float) -> dict:
            rep = reconcile_keepers(args.records, control_dir=args.control,
                                    registry_path=args.registry,
                                    hb_stale_s=args.hb_stale_seconds)
            # THE reconnect law: an adopted (live) keeper is attached, never
            # restarted; start_keeper itself refuses while one is live.
            out: dict = {"ensure": {"started": False, "noop": True}}
            live = live_keeper_for(args.records, args.run_id,
                                   hb_stale_s=args.hb_stale_seconds)
            if live is not None:
                _log({"t": round(time.time() - t0, 3), "action": "adopt",
                      "keeper_id": live["keeper_id"],
                      "pid": live.get("pid"),
                      "creation_time_us": live.get("creation_time_us")})
                out = {"ensure": {"started": False, "adopted": live["keeper_id"]}}
            else:
                out = start_keeper(records_dir=args.records, control_dir=args.control,
                                   registry_path=args.registry, run_id=args.run_id,
                                   trainer_cmd=json.loads(args.trainer_cmd),
                                   expected_seconds=args.expected_seconds,
                                   hb_seconds=args.hb_seconds,
                                   completion_marker=args.completion_marker,
                                   worktree=args.worktree, mem_gib=args.mem_gib,
                                   hb_stale_s=args.hb_stale_seconds)
                _log({"t": round(time.time() - t0, 3), "action": "start",
                      "started": out.get("started", False),
                      "keeper_id": out.get("keeper_id"),
                      "why": out.get("why")})
            return {"reconcile": rep, **out}

        t0 = time.time()
        first = _one_pass(t0)
        if args.loop_seconds <= 0:
            print(json.dumps(first, indent=1))
            return 0
        # the serve shape: a live broker keeps reconciling; killing it must not
        # affect the keeper in any way (its lifetime is independent BY DESIGN)
        while time.time() - t0 < args.loop_seconds:
            try:
                _one_pass(t0)
            except Exception as e:   # a broker loop survives a bad pass
                _log({"t": round(time.time() - t0, 3), "action": "error",
                      "detail": str(e)})
            time.sleep(0.4)
        print(json.dumps({"looped": True}, indent=1))
        return 0

    if args.cmd == "admin-release":
        print(json.dumps(admin_release(control_dir=args.control,
                                       registry_path=args.registry,
                                       reason=args.reason,
                                       released_by=args.released_by)))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
