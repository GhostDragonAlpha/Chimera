# fleet_supervisor/launcher.py -- the owned-process launcher.
#
# THE CONTRACT (Astra, astra-round6-answer-20260922.md, verbatim):
#   "The launcher creates the root process suspended, assigns it to its job,
#    then resumes it. Assignment failure means launch failure."
#   "Keep job handles non-inheritable. An accidentally inherited handle can
#    defeat cleanup on supervisor death."
#   "Children remain contained; prohibit breakaway."
# Ordering is load-bearing: job first, suspended root second, assignment third,
# resume fourth, registry record LAST (a crash before the record leaves an
# unrecorded process that KILL_ON_JOB_CLOSE still kills when our handles close).
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
import time

from . import broker, jobobject, registry

WAIT_OBJECT_0 = 0

KIND_PRIORITY = {
    "build": jobobject.BELOW_NORMAL_PRIORITY_CLASS,  # ordinary background work
    "engine": jobobject.NORMAL_PRIORITY_CLASS,
    "server": jobobject.NORMAL_PRIORITY_CLASS,
    "browser": jobobject.NORMAL_PRIORITY_CLASS,
    "gpu_phase": jobobject.NORMAL_PRIORITY_CLASS,
}


def job_name_for(session_id: str) -> str:
    # Named jobs let a restarted supervisor re-open (and re-verify) live jobs
    # by name instead of trusting a bare pid.
    return f"Local\\ChimeraFleetJob.{session_id}"


class LaunchResult:
    def __init__(self, *, ok: bool, session_id: str | None = None, pid: int | None = None,
                 creation_time_us: int | None = None, job_name: str | None = None,
                 job_handle: int | None = None, error: str | None = None,
                 admitted: str | None = None):
        self.ok = ok
        self.session_id = session_id
        self.pid = pid
        self.creation_time_us = creation_time_us
        self.job_name = job_name
        self.job_handle = job_handle
        self.error = error
        self.admitted = admitted

    def to_dict(self) -> dict:
        d = {"ok": self.ok, "session_id": self.session_id, "pid": self.pid,
             "creation_time_us": self.creation_time_us, "job_name": self.job_name,
             "error": self.error, "admitted": self.admitted}
        return d

    def __repr__(self):
        return f"LaunchResult({self.to_dict()})"


def launch(spec: dict, *, control_dir: str = broker.DEFAULT_CONTROL_DIR,
           registry_path: str = registry.DEFAULT_REGISTRY,
           supervisor_pid: int | None = None) -> LaunchResult:
    """Admit, then contain: admission -> job -> suspended root -> assign -> resume
    -> durable record. Returns a LaunchResult with ok=False and NO surviving
    process on any failure path."""
    supervisor_pid = supervisor_pid or os.getpid()
    try:
        spec = broker.normalize_spec(spec)
    except ValueError as e:
        return LaunchResult(ok=False, error=f"invalid spec: {e}")

    session_id = spec["session_id"]
    job_name = job_name_for(session_id)
    res = spec["resources"]

    # 1. admission control (mode, reservation, memory ceiling, ports, free RAM)
    ok, why = broker.admit(spec, control_dir=control_dir, registry_path=registry_path)
    if not ok:
        registry.append(registry_path, {
            "event": "refusal", "session_id": session_id, "owner_lane": spec["owner_lane"],
            "kind": spec["kind"], "reason": why,
        })
        return LaunchResult(ok=False, session_id=session_id, error=why, admitted=why)

    priority = KIND_PRIORITY.get(spec["kind"], jobobject.NORMAL_PRIORITY_CLASS)
    job_handle = None
    proc = None
    try:
        # 2. the job: KILL_ON_JOB_CLOSE + declared limits; breakaway prohibited
        #    (neither BREAKAWAY_OK flag is set); handle non-inheritable.
        job_handle = jobobject.create_job(
            job_name,
            mem_gib=res["mem_gib"],
            max_procs=res["max_procs"],
            cpu_pct=res["cpu_pct"],
            priority_class=priority,
            set_priority_limit=(spec["kind"] == "build"),
        )
        # 3. root process SUSPENDED (never runs a single instruction unassigned)
        proc = jobobject.create_suspended_process(
            spec["command"], spec.get("worktree"), priority_class=priority,
            stdout_file=spec.get("stdout_file"), stderr_file=spec.get("stderr_file"))
        # 4. assignment BEFORE resume; failure = launch failure
        jobobject.assign_process_to_job(job_handle, proc["process_handle"])
    except jobobject.WinError as e:
        # Nothing may survive: terminate the suspended root, drop everything.
        if proc:
            jobobject.terminate_pid_by_handle(proc["process_handle"])
            jobobject.close_handle(proc["thread_handle"])
            # bounded reap: the terminated suspended process must die
            deadline = time.time() + 5.0
            while time.time() < deadline:
                if jobobject.k32.WaitForSingleObject(wt.HANDLE(proc["process_handle"]), 100) == WAIT_OBJECT_0:
                    break
            jobobject.close_handle(proc["process_handle"])
        if job_handle:
            jobobject.close_handle(job_handle)
        return LaunchResult(ok=False, session_id=session_id,
                            error=f"launch failed before resume (no survivor): {e}")

    # 5. resume -- only now may it execute. We then release BOTH child handles:
    # the supervisor's ownership instrument is the JOB, and keeping a process
    # handle would turn terminated children into zombie objects that defeat
    # pid+creation-time liveness checks (measured lesson this lane).
    try:
        jobobject.resume_process(proc)
    except jobobject.WinError as e:
        jobobject.terminate_pid_by_handle(proc["process_handle"])
        jobobject.close_handle(proc["process_handle"])
        jobobject.close_handle(proc["thread_handle"])
        jobobject.close_handle(job_handle)
        return LaunchResult(ok=False, session_id=session_id,
                            error=f"resume failed (no survivor): {e}")
    jobobject.close_handle(proc["thread_handle"])
    jobobject.close_handle(proc["process_handle"])

    # 6. durable ownership record: pid + CREATION TIME (PIDs are reused)
    record = registry.launch_record(
        session_id, spec, proc["pid"], proc["creation_time_us"], job_name, supervisor_pid)
    registry.append(registry_path, record)

    return LaunchResult(
        ok=True, session_id=session_id, pid=proc["pid"],
        creation_time_us=proc["creation_time_us"], job_name=job_name,
        job_handle=job_handle, admitted=why,
    )
