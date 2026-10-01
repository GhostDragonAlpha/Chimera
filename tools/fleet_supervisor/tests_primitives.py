# fleet_supervisor/tests_primitives.py -- every primitive tested alone, against
# real processes, BEFORE anything builds on it (S-1 validate). Assertions are
# MEASURED EFFECTS (trees die, allocations fail, limits read back), never API
# return values.
#
# Measured traps this gate caught and documents (2026-09-22, Win11 build 26200):
#   - the JobObjectInformationClass numbering differs from the classic header
#     for the accounting class (AND_IO works at 8 here) and CPU rate control
#     could not be pinned at all (F-CPURATE: silent no-op / err 87);
#   - a held child process handle turns a KILLED child into a zombie object,
#     so OpenProcess+GetProcessTimes still "succeeds" -- liveness checks are
#     only honest with NO child handles held (the launcher now closes both
#     right after resume);
#   - CreateFileW signals failure with INVALID_HANDLE_VALUE (non-NULL);
#   - undeclared ctypes argtypes truncate 64-bit handles silently.
# Scratch files go to E:\\ChimeraWork\\_supervisor_scratch (TEMP is unreliable
# under this harness sandbox: CreateFileW err 2 on a freshly mkdtemp'ed dir).
# Run:  python -m tools.fleet_supervisor.tests_primitives
from __future__ import annotations

import os
import sys
import time

from . import jobobject

SCRATCH = r"E:\ChimeraWork\_supervisor_scratch"

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)


def member_names(h):
    out = []
    for pid in jobobject.query_job_pids(h):
        img = (jobobject.process_image_name(pid) or "?").replace("\\", "/").split("/")[-1]
        out.append((pid, img))
    return out


def python_members(h):
    return [pid for pid, img in member_names(h) if img.lower().startswith("python")]


def main() -> int:
    os.makedirs(SCRATCH, exist_ok=True)

    # 1. named job creation with limits + READBACK verification
    jname = f"Local\\ChimeraFleetPrim.{int(time.time())}"
    jh = jobobject.create_job(jname, mem_gib=2, max_procs=4, cpu_pct=None)
    check("create_job(named,limits,readback)", bool(jh))

    # 2. cpu_pct is REFUSED (F-CPURATE), never silently ignored
    try:
        jobobject.create_job(jname + ".cpu", mem_gib=None, max_procs=None, cpu_pct=25)
        check("cpu_pct_refused", False, "create_job accepted cpu_pct")
    except NotImplementedError as e:
        check("cpu_pct_refused", "F-CPURATE" in str(e))

    # 3. suspended creation + creation time BEFORE resume
    proc = jobobject.create_suspended_process(
        [sys.executable, "-c", "import time;time.sleep(120)"], None)
    ct = proc["creation_time_us"]
    check("create_suspended + creation_time_pre_resume", ct > 0, f"pid={proc['pid']} ct={ct}")

    # 4. assign then resume -> alive in job
    jobobject.assign_process_to_job(jh, proc["process_handle"])
    jobobject.resume_process(proc)
    time.sleep(0.6)
    in_job = jobobject.pid_in_job(proc["pid"], jh)
    check("assign_then_resume_member", in_job is True, f"in_job={in_job}")
    check("identity_match_alive", jobobject.process_alive_identity(proc["pid"], ct))
    names = member_names(jh)
    n_conhost = sum(1 for _, img in names if img.lower() == "conhost.exe")
    print(f"NOTE  resumed console root members: {names} (conhost members: {n_conhost})", flush=True)

    # 5. accounting: active >= 1 (root + its conhost where present)
    acct = jobobject.query_job_accounting(jh)
    check("accounting_active_root", acct["active_processes"] >= 1, str(acct))

    # 6. descendants: child spawns two grandchildren -> all contained
    spawn_py = os.path.join(SCRATCH, "spawn_two.py")
    with open(spawn_py, "w") as f:
        f.write("import subprocess,sys,time\n"
                "kids=[]\n"
                "for i in range(2):\n"
                "    kids.append(subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)']).pid)\n"
                "print(kids, flush=True)\n"
                "time.sleep(120)\n")
    child = jobobject.create_suspended_process([sys.executable, spawn_py], None)
    jobobject.assign_process_to_job(jh, child["process_handle"])
    jobobject.resume_process(child)
    time.sleep(3.0)
    py_count = len(python_members(jh))
    check("descendants_contained_4_python", py_count == 4,
          f"python members={py_count} all={member_names(jh)}")

    # 7. active-process limit: DETACHED root (no conhost member) under
    # max_procs=1 cannot spawn a grandchild -- its CreateProcess must fail
    jh2 = jobobject.create_job(jname + ".b", mem_gib=None, max_procs=1, cpu_pct=None)
    spawn_one = os.path.join(SCRATCH, "spawn_one.py")
    result_file = os.path.join(SCRATCH, "spawn_one_result.txt")
    if os.path.exists(result_file):
        os.remove(result_file)
    with open(spawn_one, "w") as f:
        f.write("import subprocess,sys\n"
                "try:\n"
                "    subprocess.Popen([sys.executable,'-c','import time;time.sleep(120)'])\n"
                "    r = 'SPAWNED'\n"
                "except OSError as e:\n"
                "    r = 'REFUSED err=%s' % e.errno\n"
                "open(sys.argv[1], 'w').write(r)\n"
                "import time; time.sleep(60)\n")
    p2 = jobobject.create_suspended_process(
        [sys.executable, spawn_one, result_file], None, detached=True)
    jobobject.assign_process_to_job(jh2, p2["process_handle"])
    jobobject.resume_process(p2)
    t0 = time.time()
    while time.time() - t0 < 6.0 and not os.path.exists(result_file):
        time.sleep(0.2)
    res = open(result_file).read() if os.path.exists(result_file) else "?"
    py2 = python_members(jh2)
    check("active_process_limit_enforced", len(py2) == 1 and res.startswith("REFUSED"),
          f"spawn said {res!r}, python members={py2} (limit=1)")
    jobobject.terminate_job(jh2)
    jobobject.close_handle(jh2)
    jobobject.close_handle(p2["process_handle"])
    jobobject.close_handle(p2["thread_handle"])

    # 8. memory limit: child that allocates > limit fails ITS OWN allocation
    jh3 = jobobject.create_job(jname + ".c", mem_gib=1, max_procs=8, cpu_pct=None)
    ms_before = jobobject.memory_status()
    alloc_py = os.path.join(SCRATCH, "alloc_gib.py")
    verdict = os.path.join(SCRATCH, "alloc_verdict.txt")
    if os.path.exists(verdict):
        os.remove(verdict)
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
    p3 = jobobject.create_suspended_process(
        [sys.executable, alloc_py, "3", verdict], None)  # 3 GiB vs 1 GiB
    jobobject.assign_process_to_job(jh3, p3["process_handle"])
    dup = jobobject.duplicate_handle(p3["process_handle"])
    jobobject.resume_process(p3)
    # bounded wait for the child to finish (it exits by itself either way)
    t0 = time.time()
    while time.time() - t0 < 20.0 and not jobobject.wait_process(dup, 200):
        pass
    code = jobobject.exit_code(dup)
    jobobject.close_handle(dup)
    v = open(verdict).read() if os.path.exists(verdict) else "?"
    ms_after = jobobject.memory_status()
    dip = ms_before["free_phys_gib"] - ms_after["free_phys_gib"]
    # exit 3 == the child's OWN MemoryError path; exit 0 = allocation SUCCEEDED (F4 fires)
    check("mem_limit_child_fails_own_allocation", code == 3 and v == "MEMORYERROR",
          f"exit={code} verdict={v}")
    check("mem_limit_machine_untouched", dip < 1.0, f"free RAM dip {dip:.2f} GiB")
    jobobject.terminate_job(jh3)
    jobobject.close_handle(jh3)
    jobobject.close_handle(p3["process_handle"])
    jobobject.close_handle(p3["thread_handle"])

    # 9. stdio redirect: the child writes to OUR log file
    logf = os.path.join(SCRATCH, "prim_log.txt")
    if os.path.exists(logf):
        os.remove(logf)
    p5 = jobobject.create_suspended_process(
        [sys.executable, "-c",
         "print('stdout-line', flush=True); import sys; print('err-line', file=sys.stderr, flush=True); import time; time.sleep(60)"],
        None, stdout_file=logf, stderr_file=logf)
    jobobject.resume_process(p5)
    time.sleep(1.5)
    content = open(logf, "r", encoding="utf-8", errors="replace").read() if os.path.exists(logf) else ""
    check("stdio_redirect_to_file", "stdout-line" in content and "err-line" in content,
          f"content={content[:60]!r}")
    jobobject.terminate_pid_by_handle(p5["process_handle"])
    jobobject.close_handle(p5["process_handle"])
    jobobject.close_handle(p5["thread_handle"])

    # 10. open_job by name for a LIVE job (before terminating jh)
    alive_job = jobobject.open_job(jname)
    check("open_job_live_by_name", alive_job is not None)
    if alive_job:
        jobobject.close_handle(alive_job)

    # 11. TerminateJobObject kills the whole tree
    jobobject.terminate_job(jh)
    time.sleep(1.0)
    still = jobobject.query_job_accounting(jh)["active_processes"]
    check("terminate_job_kills_tree", still == 0, f"active={still}")
    jobobject.close_handle(jh)
    jobobject.close_handle(proc["process_handle"])
    jobobject.close_handle(proc["thread_handle"])
    jobobject.close_handle(child["process_handle"])
    jobobject.close_handle(child["thread_handle"])

    # 12. KILL_ON_JOB_CLOSE: member dies when the LAST handle closes.
    # We release the child's handles FIRST -- holding one would keep the
    # terminated child's object addressable and fake a "survivor".
    jh4 = jobobject.create_job(jname + ".d", mem_gib=None, max_procs=None, cpu_pct=None)
    p4 = jobobject.create_suspended_process(
        [sys.executable, "-c", "import time;time.sleep(120)"], None)
    jobobject.assign_process_to_job(jh4, p4["process_handle"])
    jobobject.resume_process(p4)
    time.sleep(0.5)
    pid4, ct4 = p4["pid"], p4["creation_time_us"]
    jobobject.close_handle(p4["process_handle"])
    jobobject.close_handle(p4["thread_handle"])
    jobobject.close_handle(jh4)   # last job handle closes -> KILL_ON_JOB_CLOSE
    dead_by = time.time() + 10.0
    died_at = None
    while time.time() < dead_by:
        if not jobobject.process_alive_identity(pid4, ct4):
            died_at = time.time()
            break
        time.sleep(0.2)
    check("kill_on_job_close_on_last_handle", died_at is not None, f"pid={pid4}")

    # 13. open_job for a destroyed job => None
    reopened = jobobject.open_job(jname + ".d")
    check("open_job_destroyed_is_None", reopened is None)

    print("\nprimitive summary: "
          f"{sum(1 for _, ok, _ in RESULTS if ok)}/{len(RESULTS)} pass")
    return 0 if all(ok for _, ok, _ in RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
