# fleet_supervisor/lifecycle.py -- completion, reconciliation, idle expiry,
# and the AMBIGUOUS-PROCESS report that must never kill anything.
#
# Astra's contract (astra-round6-answer-20260922.md):
#   "Completion triggers graceful shutdown, then job termination after a short
#    deadline."
#   "Never authorize termination by executable name, age, port number, or
#    location alone. ... Ambiguous processes are reported and left alone."
#   "Reconcile live jobs frequently; retain the two-hour janitor as an audit
#    and disk-retention mechanism."
# Termination is ALWAYS TerminateJobObject (by job handle) -- never by pid,
# name, port, age, or path. A pid is only ever READ (identity check), and an
# identity mismatch makes the process MORE untouchable, not less.
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import time

from . import broker, jobobject, launcher, registry

DEFAULT_POLL_INTERVAL_S = 15.0   # "Reconcile live jobs frequently"
DEFAULT_COMPLETE_DEADLINE_S = 10.0

LANE_LOOKING_IMAGE_NAMES = (
    # classes the fleet census uses; REPORT-ONLY here, always
    "chimera_engine.exe",
    "chrome-headless-shell.exe",
)


def live_member_identities(job_handle: int) -> list[dict]:
    """(pid, creation_time) for every live member -- the identity list used for
    survivor checks. Identity, never bare pids."""
    out = []
    for pid in jobobject.query_job_pids(job_handle):
        h = jobobject.k32.OpenProcess(jobobject.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            continue
        try:
            out.append({"pid": pid,
                        "creation_time_us": jobobject.process_creation_time_us(h)})
        except jobobject.WinError:
            continue
        finally:
            jobobject.close_handle(h)
    return out


def python_cmdline_map() -> dict[int, str]:
    """One read-only CIM query: pid -> command line for python* processes.
    Used ONLY to classify lane-looking processes for the REPORT; its result can
    never authorize a kill (only job handles can kill)."""
    import subprocess
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
             "ForEach-Object { \"{0}`t{1}\" -f $_.ProcessId, $_.CommandLine }"],
            capture_output=True, text=True, timeout=20,
            creationflags=jobobject.CREATE_NO_WINDOW)
        result: dict[int, str] = {}
        for line in (out.stdout or "").splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2 and parts[0].strip().isdigit():
                result[int(parts[0])] = parts[1] or ""
        return result
    except Exception:
        return {}


def cmdline_looks_like_lane(cmdline: str) -> bool:
    return any(pat in (cmdline or "") for pat in
               ("slice_server", "lesson_shell", "thin_client", "demo_package",
                "game_shell", "walkthrough", "server.py", "fleet_supervisor"))


class Supervisor:
    """Holds job handles for sessions launched from THIS process and reconciles
    the registry (including sessions from dead supervisors, via named jobs)."""

    def __init__(self, *, registry_path: str = registry.DEFAULT_REGISTRY,
                 control_dir: str = broker.DEFAULT_CONTROL_DIR,
                 poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
                 complete_deadline_s: float = DEFAULT_COMPLETE_DEADLINE_S):
        self.registry_path = registry_path
        self.control_dir = control_dir
        self.poll_interval_s = poll_interval_s
        self.complete_deadline_s = complete_deadline_s
        self.handles: dict[str, int] = {}   # session_id -> job handle (non-inheritable)
        self._stop = False

    # ------------------------------------------------------------- launch
    def launch(self, spec: dict) -> launcher.LaunchResult:
        result = launcher.launch(spec, control_dir=self.control_dir,
                                 registry_path=self.registry_path)
        if result.ok and result.job_handle:
            self.handles[result.session_id] = result.job_handle
        return result

    # ------------------------------------------------------------- completion
    def complete(self, session_id: str, *, deadline: float | None = None,
                 reason: str = "requested") -> dict:
        """Graceful attempt -> bounded wait -> TerminateJobObject -> record.
        NEVER signals or kills by pid; the job is the only weapon."""
        deadline = self.complete_deadline_s if deadline is None else deadline
        rec = registry.active_sessions(self.registry_path).get(session_id)
        if rec is None:
            return {"session_id": session_id, "ok": False,
                    "error": "no active session record (nothing to complete)"}

        job_handle = self.handles.get(session_id)
        opened_here = False
        if job_handle is None:
            job_handle = jobobject.open_job(rec["job_name"], terminate_access=True)
            opened_here = job_handle is not None
        if job_handle is None:
            # Job object gone => all members are dead (KILL_ON_JOB_CLOSE).
            # The WRONG move here would be falling back to OpenProcess+kill by
            # pid: ownership cannot be re-verified against a live job, so by
            # the ownership law nothing may be signaled.
            registry.append(self.registry_path, registry.status_record(
                session_id, "completed", reason=reason,
                detail="job object already gone; members dead; nothing signaled"))
            self.handles.pop(session_id, None)
            return {"session_id": session_id, "ok": True, "how": "already-gone",
                    "terminated": False, "graceful_signal": False}

        # graceful attempt: CTRL_BREAK to the root's process group, ONLY when
        # the root's identity (pid + creation time) still matches the record.
        # CTRL_BREAK reaches groups that share our console; detached consoles
        # (CREATE_NO_WINDOW) will not receive it -- a documented Windows
        # restriction ("where applicable" per the contract); the deadline +
        # TerminateJobObject remain the guaranteed path.
        graceful = False
        if jobobject.process_alive_identity(rec["pid"], rec["creation_time_us"]):
            graceful = bool(jobobject.k32.GenerateConsoleCtrlEvent(
                jobobject.CTRL_BREAK_EVENT, wt.DWORD(rec["pid"])))

        # bounded wait for natural drain
        t0 = time.time()
        acct = jobobject.query_job_accounting(job_handle)
        while acct["active_processes"] > 0 and time.time() - t0 < deadline:
            time.sleep(0.05)
            acct = jobobject.query_job_accounting(job_handle)

        terminated = False
        if acct["active_processes"] > 0:
            jobobject.terminate_job(job_handle)
            terminated = True
            t1 = time.time()
            while time.time() - t1 < 5.0:
                if jobobject.query_job_accounting(job_handle)["active_processes"] == 0:
                    break
                time.sleep(0.05)

        if opened_here:
            jobobject.close_handle(job_handle)
        else:
            jobobject.close_handle(self.handles.pop(session_id, job_handle))
        self.handles.pop(session_id, None)
        status = "terminated" if terminated else "completed"
        registry.append(self.registry_path, registry.status_record(
            session_id, status, reason=reason, graceful_signal=graceful,
            total_processes=acct["total_processes"],
            io_bytes_total=acct["io_bytes_total"]))
        return {"session_id": session_id, "ok": True, "how": status,
                "graceful_signal": graceful, "terminated": terminated}

    def touch(self, session_id: str) -> bool:
        """A lane marks activity (resets its idle clock)."""
        if session_id not in registry.active_sessions(self.registry_path):
            return False
        registry.append(self.registry_path, {
            "event": "touch", "session_id": session_id, "last_activity": time.time()})
        return True

    # ------------------------------------------------------------- reconcile
    def reconcile_pass(self, *, reap: bool = True) -> dict:
        """One pass over the active registry:
          - live jobs verified via their JOB HANDLE (or re-opened by name);
            completed jobs detected and reaped;
          - jobs killed by a dead supervisor recognized as orphaned_completed;
          - idle sessions expired per kind;
          - lane-looking processes belonging to NO fleet job REPORTED, never
            touched (the ownership law).
        """
        report = {"checked": 0, "running": [], "completed": [], "orphaned_completed": [],
                  "idle_expired": [], "ambiguous": [], "identity_drift": []}
        actives = registry.active_sessions(self.registry_path)
        timeouts = broker.idle_timeouts(self.control_dir)
        now = time.time()
        live_job_handles: list[int] = []
        opened_by_pass: list[int] = []

        for sid, rec in actives.items():
            report["checked"] += 1
            job_handle = self.handles.get(sid)
            if job_handle is None:
                job_handle = jobobject.open_job(rec.get("job_name") or "", terminate_access=False)
                if job_handle:
                    opened_by_pass.append(job_handle)
            if job_handle is None:
                # named job destroyed => with KILL_ON_JOB_CLOSE every member is
                # dead. A supervisor death closes its handles: this is the
                # expected post-crash fold, recorded for the audit trail.
                registry.append(self.registry_path, registry.status_record(
                    sid, "orphaned_completed",
                    detail="job object gone (owner handles closed); members dead"))
                report["orphaned_completed"].append(sid)
                continue

            live_job_handles.append(job_handle)
            acct = jobobject.query_job_accounting(job_handle)
            if acct["active_processes"] == 0:
                if reap:
                    registry.append(self.registry_path, registry.status_record(
                        sid, "completed", reason="reconcile: job empty (natural exit)",
                        total_processes=acct["total_processes"],
                        io_bytes_total=acct["io_bytes_total"]))
                    report["completed"].append(sid)
                continue

            # root identity drift (pid reuse INSIDE a live job): report it;
            # job-level ownership is still valid, so completion stays safe.
            if not jobobject.process_alive_identity(rec["pid"], rec["creation_time_us"]):
                report["identity_drift"].append(
                    {"session_id": sid, "pid": rec["pid"],
                     "note": "root pid/creation-time mismatch; job still owned; nothing signaled by identity"})

            idle_to = timeouts.get(rec.get("kind"))
            last_activity = float(rec.get("last_activity") or 0)
            if idle_to is not None and now - last_activity > idle_to:
                out = self.complete(sid, reason=f"idle expiry ({idle_to:.0f}s)")
                report["idle_expired"].append({sid: out["how"]})
                continue

            report["running"].append({"session_id": sid, "active": acct["active_processes"],
                                      "io_bytes_total": acct["io_bytes_total"]})

        for h in opened_by_pass:
            if h not in self.handles.values():
                jobobject.close_handle(h)

        # THE AMBIGUOUS SCAN: report-only, always. A lane-looking process that
        # is in none of our live jobs and matches no active registry identity.
        ours_identities = [(r["pid"], r["creation_time_us"])
                           for r in registry.active_sessions(self.registry_path).values()]
        py_cmdlines = None
        for p in jobobject.enumerate_processes():
            name = (p["name"] or "").lower()
            looks_like_lane = False
            if name in LANE_LOOKING_IMAGE_NAMES:
                looks_like_lane = True
            elif name.startswith("python"):
                if py_cmdlines is None:
                    py_cmdlines = python_cmdline_map()
                if cmdline_looks_like_lane(py_cmdlines.get(p["pid"], "")):
                    looks_like_lane = True
            if not looks_like_lane:
                continue
            if self._is_ours(p["pid"], live_job_handles, ours_identities):
                continue
            report["ambiguous"].append({
                "pid": p["pid"], "name": p["name"],
                "image": jobobject.process_image_name(p["pid"]) or "",
                "note": "REPORT ONLY: lane-looking but not fleet-owned; never touched",
            })
        return report

    @staticmethod
    def _is_ours(pid: int, live_job_handles: list[int], ours_identities: list[tuple]) -> bool:
        for opid, ocreation in ours_identities:
            if opid == pid and jobobject.process_alive_identity(pid, ocreation):
                return True
        for jh in live_job_handles:
            try:
                if pid in jobobject.query_job_pids(jh):
                    return True
            except jobobject.WinError:
                continue
        return False

    # ------------------------------------------------------------- serve loop
    def serve(self, poll_interval_s: float | None = None) -> None:
        """Long-running supervisor: reconcile every poll; complete everything
        on interrupt (graceful supervisor shutdown)."""
        import signal as _signal
        interval = poll_interval_s or self.poll_interval_s
        self._stop = False

        def _bye(signum, frame):
            self._stop = True
        try:
            _signal.signal(_signal.SIGINT, _bye)
            _signal.signal(_signal.SIGBREAK, _bye)
        except (ValueError, OSError):
            pass
        while not self._stop:
            t0 = time.time()
            try:
                rep = self.reconcile_pass()
                for sid in rep["completed"] + rep["orphaned_completed"]:
                    self.handles.pop(sid, None)
                for ent in rep["ambiguous"]:
                    print(f"AMBIGUOUS {ent['pid']} {ent['name']} (report only)", flush=True)
            except Exception as e:  # the loop must survive a bad pass
                print(f"reconcile error: {e}", flush=True)
            while not self._stop and time.time() - t0 < interval:
                time.sleep(0.2)
        # graceful supervisor exit: complete every session we still hold
        for sid in list(self.handles.keys()):
            try:
                self.complete(sid, reason="supervisor shutdown")
            except Exception as e:
                print(f"shutdown complete({sid}) error: {e}", flush=True)
        # any last handles die here => KILL_ON_JOB_CLOSE backstop
        for h in self.handles.values():
            jobobject.close_handle(h)
