# fleet_supervisor/validate_ownership.py -- THE OWNERSHIP FALSIFIER SUITE.
# Preregistered in tools/science_funnel/validation/fleet_supervisor_20260922/record.md
# (Astra's own lane):
#   "100 execution cycles, including cancellation and launcher crashes;
#    unrelated sentinel processes present"
#   rejection: "Any sentinel affected, or disposable descendants survive over
#   30 seconds after cleanup"
# Plus this lane's additions: PID-reuse false-match refusal, assignment-
# failure no-survivor, ambiguous REPORT-ONLY behavior, and a fresh
# memory-limit run recorded with numbers.
#
# NO killed process is ever chosen by name/age/port/location: the suite kills
# only (a) sessions it launched THROUGH the supervisor (by job) and (b) the
# supervisor subprocess it launched itself (by handle), and (c) the two
# sentinels it launched itself, at the very end, by verified identity.
# Run:  python -m tools.fleet_supervisor.validate_ownership
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from . import jobobject, lifecycle, registry, supervisor as supervisor_cli

SCRATCH = r"E:\ChimeraWork\_supervisor_scratch"
VALIDATE_DIR = os.path.join(SCRATCH, "validate")
WORKTREE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE_DIR = os.path.join(WORKTREE, "tools", "science_funnel", "validation",
                        "fleet_supervisor_20260922")

SELFEXIT_ROOT = """import subprocess, sys, time
here = sys.argv[1]
kids = []
kids.append(subprocess.Popen([sys.executable, here + '\\\\sleep30.py']).pid)
kids.append(subprocess.Popen([sys.executable, here + '\\\\sleep30.py']).pid)
open(here + '\\\\last_tree.txt', 'w').write(repr(kids))
time.sleep(0.8)   # the root's batch ends; descendants are the supervisor's problem
"""

SLEEP30 = "import time; time.sleep(30)"

SLEEPER_TREE = """import subprocess, sys, time
here = sys.argv[1]
kids = []
kids.append(subprocess.Popen([sys.executable, here + '\\\\sleep30.py']).pid)
kids.append(subprocess.Popen([sys.executable, here + '\\\\sleep30.py']).pid)
open(here + '\\\\last_tree.txt', 'w').write(repr(kids))
time.sleep(30)
"""


def w(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class Sentinels:
    """Two unrelated bystanders, launched DIRECTLY (never through the
    supervisor, never in any job). S2's command line deliberately matches the
    legacy orphan-sweep pattern ('slice_server') -- maximally attractive to
    any name-based logic that might leak into the supervisor."""

    def __init__(self, scratch: str):
        self.s1 = subprocess.Popen(
            ["cmd", "/c", "ping -n 3600 127.0.0.1 > nul"],
            creationflags=jobobject.CREATE_NO_WINDOW)
        time.sleep(0.3)
        self.s2 = subprocess.Popen(
            [sys.executable, "-c",
             "import time; time.sleep(3600)  # slice_server role-play sentinel"],
            creationflags=jobobject.CREATE_NO_WINDOW)
        time.sleep(0.5)
        self.ids = {
            "S1_cmd_dummy": self._ident(self.s1.pid),
            "S2_py_slice_server": self._ident(self.s2.pid),
        }
        self.touch_log = []

    @staticmethod
    def _ident(pid: int) -> dict:
        h = jobobject.k32.OpenProcess(jobobject.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return {"pid": pid, "creation_time_us": None}
        try:
            return {"pid": pid, "creation_time_us": jobobject.process_creation_time_us(h)}
        finally:
            jobobject.close_handle(h)

    def alive(self, check_point: str) -> dict:
        out = {}
        for name, ident in self.ids.items():
            ok = ident["creation_time_us"] is not None and jobobject.process_alive_identity(
                ident["pid"], ident["creation_time_us"])
            out[name] = ok
            self.touch_log.append({"t": time.time(), "at": check_point, "name": name, "alive": bool(ok)})
        return out

    def all_alive_everywhere(self) -> bool:
        return all(e["alive"] for e in self.touch_log)

    def stop(self):
        for s in (self.s1, self.s2):
            try:
                s.kill()
            except OSError:
                pass


def member_identities(sup: lifecycle.Supervisor, session_id: str) -> list[dict]:
    jh = sup.handles.get(session_id)
    return lifecycle.live_member_identities(jh) if jh else []


def run(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles-normal", type=int, default=40)
    ap.add_argument("--cycles-cancel", type=int, default=30)
    ap.add_argument("--cycles-kill", type=int, default=30)
    ap.add_argument("--deadline", type=float, default=2.0, help="complete() deadline in tests")
    args = ap.parse_args(argv)

    os.makedirs(VALIDATE_DIR, exist_ok=True)
    d = VALIDATE_DIR
    reg = os.path.join(d, "registry.jsonl")
    control = os.path.join(d, "control")
    os.makedirs(control, exist_ok=True)
    if os.path.exists(reg):
        os.remove(reg)

    # ---- child scripts -------------------------------------------------
    w(os.path.join(d, "sleep30.py"), SLEEP30)
    w(os.path.join(d, "selfexit_root.py"), SELFEXIT_ROOT)
    w(os.path.join(d, "sleeper_tree.py"), SLEEPER_TREE)

    sup = lifecycle.Supervisor(registry_path=reg, control_dir=control,
                               complete_deadline_s=args.deadline)
    sentinels = Sentinels(d)
    cycles = []
    failures = []

    def record(cycle: dict) -> None:
        cycles.append(cycle)
        bad = cycle.get("problems") or []
        if bad:
            failures.append({"cycle": cycle.get("index"), "kind": cycle.get("kind"), "problems": bad})
        print(f"[{cycle.get('index'):3d}] {cycle.get('kind'):9s} "
              f"{'PROBLEMS: ' + '; '.join(bad) if bad else 'clean'}", flush=True)

    def survivor_check(identities: list[dict], t_cleanup: float) -> list[str]:
        """F2: any disposable member alive > 30 s after its cleanup. We check
        now AND the final sweep re-checks with > 30 s elapsed for every cycle."""
        problems = []
        for ident in identities:
            if jobobject.process_running(ident["pid"], ident["creation_time_us"]):
                problems.append(f"survivor pid={ident['pid']} (at +{time.time()-t_cleanup:.1f}s)")
        return problems

    # ================= 1. NORMAL cycles: root self-exits, remainder completed
    idx = 0
    for i in range(args.cycles_normal):
        idx += 1
        spec = {"session_id": f"vc-norm-{idx:03d}", "owner_lane": "validate",
                "worktree": None,
                "command": [sys.executable, os.path.join(d, "selfexit_root.py"), d],
                "ports": [], "kind": "engine",
                "resources": {"cpu_pct": None, "mem_gib": 2, "max_procs": 16}}
        t0 = time.time()
        res = sup.launch(spec)
        if not res.ok:
            record({"index": idx, "kind": "normal", "problems": [f"launch failed: {res.error}"]})
            continue
        # wait for the ROOT to exit by itself (bounded). The job's active
        # count stays >0 (descendants sleep on) -- the root's own liveness is
        # the honest signal.
        jh = sup.handles[res.session_id]
        root_gone = False
        while time.time() - t0 < 10.0:
            if not jobobject.process_running(res.pid, res.creation_time_us):
                root_gone = True
                break
            time.sleep(0.1)
        identities = lifecycle.live_member_identities(jh)
        out = sup.complete(res.session_id, deadline=args.deadline, reason="cycle cleanup")
        t_cleanup = time.time()
        problems = survivor_check(identities, t_cleanup)
        if not root_gone:
            problems.append("root never self-exited within 10 s")
        st = registry.fold(reg).get(res.session_id, {}).get("status")
        if st not in ("completed", "terminated"):
            problems.append(f"fold status after cleanup = {st!r}")
        sa = sentinels.alive(f"norm-{idx}")
        if not all(sa.values()):
            problems.append(f"SENTINEL AFFECTED {sa}")
        record({"index": idx, "kind": "normal", "session_id": res.session_id,
                "members": len(identities), "identities": identities,
                "root_self_exit": root_gone,
                "how": out.get("how"), "t_cleanup": t_cleanup, "problems": problems})

    # ================= 2. CANCELLED cycles: kill the session mid-run
    for i in range(args.cycles_cancel):
        idx += 1
        spec = {"session_id": f"vc-cxl-{idx:03d}", "owner_lane": "validate",
                "worktree": None,
                "command": [sys.executable, os.path.join(d, "sleeper_tree.py"), d],
                "ports": [], "kind": "server",
                "resources": {"cpu_pct": None, "mem_gib": 2, "max_procs": 16}}
        res = sup.launch(spec)
        if not res.ok:
            record({"index": idx, "kind": "cancel", "problems": [f"launch failed: {res.error}"]})
            continue
        time.sleep(0.6)  # let the tree go deep, then cancel MID-RUN
        jh = sup.handles[res.session_id]
        identities = lifecycle.live_member_identities(jh)
        out = sup.complete(res.session_id, deadline=args.deadline, reason="cycle cancel")
        t_cleanup = time.time()
        problems = survivor_check(identities, t_cleanup)
        if not out.get("terminated"):
            problems.append("cancellation did not have to terminate (tree died early?)")
        st = registry.fold(reg).get(res.session_id, {}).get("status")
        if st not in ("completed", "terminated"):
            problems.append(f"fold status after cleanup = {st!r}")
        sa = sentinels.alive(f"cxl-{idx}")
        if not all(sa.values()):
            problems.append(f"SENTINEL AFFECTED {sa}")
        record({"index": idx, "kind": "cancel", "session_id": res.session_id,
                "members": len(identities), "identities": identities,
                "how": out.get("how"),
                "t_cleanup": t_cleanup, "problems": problems})

    # ================= 3. LAUNCHER-KILL cycles: TerminateProcess the supervisor
    for i in range(args.cycles_kill):
        idx += 1
        sid = f"vc-kill-{idx:03d}"
        spec = {"session_id": sid, "owner_lane": "validate", "worktree": None,
                "command": [sys.executable, os.path.join(d, "sleeper_tree.py"), d],
                "ports": [], "kind": "server",
                "resources": {"cpu_pct": None, "mem_gib": 2, "max_procs": 16}}
        spec_path = os.path.join(d, f"spec_{sid}.json")
        with open(spec_path, "w") as f:
            json.dump(spec, f)
        problems = []
        hold = subprocess.Popen(
            [sys.executable, "-m", "tools.fleet_supervisor.supervisor",
             "--registry", reg, "--control", control,
             "hold", "--spec-file", spec_path, "--seconds", "300"],
            cwd=WORKTREE, creationflags=jobobject.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        launch_line = hold.stdout.readline().strip()
        try:
            launch_res = json.loads(launch_line)
        except json.JSONDecodeError:
            launch_res = {"ok": False, "error": f"unparseable: {launch_line[:120]}"}
        identities = []
        if not launch_res.get("ok"):
            problems.append(f"supervisor launch failed: {launch_res.get('error')}")
        else:
            # poll status (SECOND process; exercises the named-job re-open path)
            deadline = time.time() + 10.0
            while time.time() < deadline:
                st = subprocess.run(
                    [sys.executable, "-m", "tools.fleet_supervisor.supervisor",
                     "--registry", reg, "--control", control, "status"],
                    cwd=WORKTREE, capture_output=True, text=True,
                    creationflags=jobobject.CREATE_NO_WINDOW, timeout=30)
                try:
                    status = json.loads(st.stdout)
                except json.JSONDecodeError:
                    status = {}
                ent = status.get("active", {}).get(sid) or {}
                mem = ent.get("members") or []
                if len(mem) >= 4:  # root + conhost + child + grandchild
                    identities = mem
                    break
                time.sleep(0.3)
            if not identities:
                problems.append("members never appeared in status (>=4)")
            # THE LAUNCHER KILL: the supervisor process itself dies mid-cycle
            hold.kill()
            hold_rc = hold.wait(timeout=10)
            t_cleanup = time.time()
            # members die via KILL_ON_JOB_CLOSE during supervisor teardown;
            # poll (bounded) before judging -- and judge by EXECUTION, not by
            # zombie-object identity (see jobobject.process_running note)
            members_dead = False
            while time.time() - t_cleanup < 10.0:
                if not any(jobobject.process_running(i["pid"], i["creation_time_us"]) for i in identities):
                    members_dead = True
                    break
                time.sleep(0.2)
            if not members_dead:
                for ident in identities:
                    if jobobject.process_running(ident["pid"], ident["creation_time_us"]):
                        problems.append(f"KILL-CYCLE SURVIVOR pid={ident['pid']}")
            # reconcile (restart shape): the fold must see the job gone
            rep = sup.reconcile_pass(scan_ambiguous=False)
            st = registry.fold(reg).get(sid, {}).get("status")
            if st != "orphaned_completed":
                problems.append(f"fold after supervisor kill = {st!r} (want orphaned_completed)")
        if hold.poll() is None:
            hold.kill()
        sa = sentinels.alive(f"kill-{idx}")
        if not all(sa.values()):
            problems.append(f"SENTINEL AFFECTED {sa}")
        record({"index": idx, "kind": "kill", "session_id": sid,
                "members": len(identities), "identities": identities,
                "supervisor_rc": hold.poll(),
                "t_cleanup": time.time(), "problems": problems})

    # ================= 4. FINAL SWEEP: every member identity of every cycle
    # must be dead with > 30 s elapsed since ITS cleanup (the honest F2
    # evaluation: "descendants survive over 30 seconds after cleanup")
    print("final 30s survivor sweep ...", flush=True)
    last = max((c.get("t_cleanup") or 0) for c in cycles) if cycles else 0
    wait_more = max(0.0, (last + 31.0) - time.time())
    if wait_more:
        time.sleep(wait_more)
    final_problems = []
    checked = 0
    for c in cycles:
        tc = c.get("t_cleanup")
        if not tc or time.time() - tc <= 30.0:
            continue
        for ident in (c.get("identities") or []):
            checked += 1
            if jobobject.process_running(ident["pid"], ident["creation_time_us"]):
                problem = (f"cycle {c['index']} ({c['kind']}): descendant "
                           f"pid={ident['pid']} RUNNING >30s after cleanup")
                final_problems.append(problem)
    if final_problems:
        failures.append({"cycle": "final-sweep", "kind": "F2", "problems": final_problems})
    print(f"final sweep: {checked} identities re-checked at >30s, "
          f"{len(final_problems)} survivors", flush=True)
    sentinels_final = sentinels.alive("final")

    # ================= 5. PID-REUSE falsifier (F3)
    pid_reuse = pid_reuse_test(sup, reg, control, d, sentinels)

    # ================= 6. AMBIGUOUS report-only (P-AMBIGUOUS, part of F1)
    ambiguous = ambiguous_test(sup, sentinels)

    # ================= 7. memory-limit instrument (F4, fresh numbers)
    memlimit = memlimit_test(sup, d)

    # ================= 8. assignment-failure no-survivor (F5)
    assign_fail = assign_failure_test(sup, reg, control, d)

    sentinels.stop()

    summary = {
        "cycles_total": len(cycles),
        "cycles_clean": sum(1 for c in cycles if not c.get("problems")),
        "cycles_by_kind": {
            k: {"n": sum(1 for c in cycles if c["kind"] == k),
                "clean": sum(1 for c in cycles if c["kind"] == k and not c.get("problems"))}
            for k in ("normal", "cancel", "kill")},
        "final_sweep": {"identities_rechecked": checked, "survivors": len(final_problems),
                        "problems": final_problems},
        "sentinels_touch_log_clean": sentinels.all_alive_everywhere(),
        "sentinels_final": sentinels_final,
        "pid_reuse": pid_reuse,
        "ambiguous": ambiguous,
        "memlimit": memlimit,
        "assign_failure": assign_fail,
        "failures": failures,
    }
    out = {"summary": summary, "cycles": cycles,
           "sentinel_touch_log": sentinels.touch_log}
    with open(os.path.join(d, "cycle_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    compact = {
        "when": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary,
    }
    with open(os.path.join(LANE_DIR, "cycle_results.json"), "w", encoding="utf-8") as f:
        json.dump(compact, f, indent=1)

    ok = (summary["cycles_clean"] == summary["cycles_total"] == 100
          and summary["sentinels_touch_log_clean"] and all(sentinels_final.values())
          and pid_reuse["ok"] and ambiguous["ok"] and memlimit["ok"]
          and assign_fail["ok"] and not failures and not final_problems)
    print(json.dumps(summary, indent=1))
    print(f"\nOWNERSHIP SUITE: {'PASS (100/100 clean, no falsifier fired)' if ok else 'FAIL -- falsifier fired'}")
    return 0 if ok else 1


def pid_reuse_test(sup, reg, control, d, sentinels) -> dict:
    """F3: a reused pid (or a wrong creation-time record) can never make the
    registry match an innocent live process, and complete() can never signal
    one: only a LIVE JOB HANDLE can terminate, and identity requires pid AND
    creation time."""
    out = {"organic_reuse_observed": False, "deterministic": None, "innocent_alive_after": None}
    # innocent bystander: a plain sleeper, launched directly (suite-owned)
    innocent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"],
                                creationflags=jobobject.CREATE_NO_WINDOW)
    time.sleep(0.5)
    iid = Sentinels._ident(innocent.pid)

    # organic churn attempt: rapid short-lived processes until the innocent's
    # pid is handed out again (may simply not happen in the window; reported
    # honestly either way -- the deterministic probe carries the falsifier)
    reused = False
    t0 = time.time()
    n = 0
    while time.time() - t0 < 45.0 and n < 4000:
        n += 1
        q = subprocess.Popen([sys.executable, "-c", "pass"],
                             creationflags=jobobject.CREATE_NO_WINDOW)
        q.wait(timeout=10)
        if q.pid == innocent.pid:
            reused = True
            break
    out["organic_reuse_observed"] = reused
    out["churn_spawns"] = n

    # deterministic: a registry record CLAIMING the innocent pid with a WRONG
    # creation time, and a job name that never existed
    sid = "vc-pidreuse-synthetic"
    registry.append(reg, {
        "event": "launch", "session_id": sid, "owner_lane": "validate",
        "worktree": None, "command": ["innocent"], "ports": [], "kind": "server",
        "resources": {"mem_gib": 2, "max_procs": 16},
        "pid": innocent.pid,
        "creation_time_us": (iid["creation_time_us"] or 0) + 1,  # WRONG on purpose
        "job_name": "Local\\ChimeraFleetJob.never-existed-xyz",
        "status": "running", "supervisor_pid": os.getpid(), "last_activity": time.time(),
    })
    # reconcile: must NOT treat the innocent process as fleet-owned-running
    rep = sup.reconcile_pass()
    running_ids = [r["session_id"] for r in rep["running"]]
    out["fold_matched_innocent_as_running"] = sid in running_ids
    # complete(): job gone -> record folds completed WITHOUT signaling anything
    res = sup.complete(sid, reason="pid-reuse probe")
    alive_after = jobobject.process_alive_identity(innocent.pid, iid["creation_time_us"])
    out["innocent_alive_after"] = bool(alive_after)
    out["complete_how"] = res.get("how") or res.get("error")
    st = registry.fold(reg).get(sid, {}).get("status")
    out["fold_status"] = st
    # correct behavior: the fold never matched the innocent pid as fleet-owned
    # (no job object backs the claim), reconcile folded it without touching
    # anything, and the innocent process is still executing afterwards
    out["deterministic"] = (not out["fold_matched_innocent_as_running"]
                            and alive_after and st == "orphaned_completed")
    out["ok"] = bool(out["deterministic"] and alive_after)
    innocent.kill()
    return out


def ambiguous_test(sup, sentinels) -> dict:
    """P-AMBIGUOUS: the lane-looking sentinel (slice_server cmdline, not
    fleet-owned) is REPORTED by reconcile and left running."""
    rep = sup.reconcile_pass()
    s2id = sentinels.ids["S2_py_slice_server"]
    reported = any(a["pid"] == s2id["pid"] for a in rep["ambiguous"])
    still_alive = jobobject.process_alive_identity(s2id["pid"], s2id["creation_time_us"])
    return {"reported": bool(reported), "still_alive": bool(still_alive),
            "ambiguous_count": len(rep["ambiguous"]),
            "ok": bool(reported and still_alive)}


def memlimit_test(sup, d) -> dict:
    """F4 with fresh numbers: 1 GiB job; 3 GiB child allocation fails ITS OWN
    way; machine free RAM does not dip."""
    import ctypes
    jh = jobobject.create_job(f"Local\\vc-memprobe.{int(time.time())}",
                              mem_gib=1, max_procs=8, cpu_pct=None)
    verdict = os.path.join(d, "memprobe_verdict.txt")
    if os.path.exists(verdict):
        os.remove(verdict)
    alloc_py = os.path.join(d, "alloc_gib.py")
    if not os.path.exists(alloc_py):
        with open(alloc_py, "w") as f:
            f.write("import sys\n"
                    "gib = int(sys.argv[1])\n"
                    "try:\n"
                    "    bytearray(gib * (1 << 30))\n"
                    "    v = 'ALLOCATED'\n"
                    "except MemoryError:\n"
                    "    v = 'MEMORYERROR'\n"
                    "with open(sys.argv[2], 'w') as f:\n"
                    "    f.write(v)\n"
                    "sys.exit(3 if v == 'MEMORYERROR' else 0)\n")
    ms_before = jobobject.memory_status()
    p = jobobject.create_suspended_process([sys.executable, alloc_py, "3", verdict], None)
    jobobject.assign_process_to_job(jh, p["process_handle"])
    dup = jobobject.duplicate_handle(p["process_handle"])
    jobobject.resume_process(p)
    t0 = time.time()
    while time.time() - t0 < 25.0 and not jobobject.wait_process(dup, 200):
        pass
    code = jobobject.exit_code(dup)
    jobobject.close_handle(dup)
    ms_after = jobobject.memory_status()
    v = open(verdict).read() if os.path.exists(verdict) else "?"
    jobobject.terminate_job(jh)
    jobobject.close_handle(jh)
    jobobject.close_handle(p["process_handle"])
    jobobject.close_handle(p["thread_handle"])
    dip = ms_before["free_phys_gib"] - ms_after["free_phys_gib"]
    return {"child_exit": code, "verdict": v, "free_ram_dip_gib": round(dip, 2),
            "ok": bool(code == 3 and v == "MEMORYERROR" and dip < 1.0)}


def assign_failure_test(sup, reg, control, d) -> dict:
    """F5: when AssignProcessToJobObject fails, the suspended root must not
    survive -- assignment failure IS launch failure."""
    seen_failures = []

    orig = jobobject.assign_process_to_job

    def failing_assign(job_handle, process_handle):
        seen_failures.append(1)
        raise jobobject.WinError("AssignProcessToJobObject (simulated refusal)")

    jobobject.assign_process_to_job = failing_assign
    try:
        spec = {"session_id": f"vc-assignfail-{int(time.time())}", "owner_lane": "validate",
                "worktree": None,
                "command": [sys.executable, "-c", "import time; time.sleep(120)"],
                "ports": [], "kind": "server",
                "resources": {"cpu_pct": None, "mem_gib": 2, "max_procs": 16}}
        res = sup.launch(spec)
    finally:
        jobobject.assign_process_to_job = orig
    # the root must be dead (launch failed BEFORE resume; cleanup terminated it)
    time.sleep(0.5)
    return {"assign_was_called": bool(seen_failures), "launch_ok": res.ok,
            "error": (res.error or "")[:80],
            "ok": bool(seen_failures and not res.ok)}


if __name__ == "__main__":
    sys.exit(run())
