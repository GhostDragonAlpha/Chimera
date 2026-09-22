"""Chimera verification farm runner (Astra P1, lane agent/verification-farm-20260921).

Given N candidate checkouts (git worktrees of a pinned commit), builds and runs each
as a PRIVATE job -- own worktree, own build dir, own run dir (the L8 discipline) --
captures raw stdout bytes per job, and compares them against expected shas.

Scheduling policy (banked in the receipt PREREG.md, spine-first):
  * Exploratory work-in-progress is BOUNDED (default 8) and never exceeds
    floor(logical_cores) - RESERVE, RESERVE default 4 logical cores held for the
    serial spine's blocking verification.
  * A spine-priority job bypasses the WIP bound, is admitted immediately, and
    while one is in flight no new exploratory job is admitted. The serial
    spine's blocking verification always has capacity.

Usage:
  python tools/agent_fleet/verify_farm.py --lane-root <root> --commit <sha> \
      --jobs N --batch-label cN --scene <scene.json> \
      --expected-stdout-sha <sha> --expected-stdout-bytes <n> \
      --expected-scene-sha <sha> --receipt-dir <dir> [--spine] [--timeout-s S]

Falsifiers enforced here: F-FARM-BYTES (per-job byte identity),
F-FARM-TAIL (spine latency limit), F-FARM-NO-GAIN (adjudicated from batch JSONs).
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import queue
import shutil
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

RESERVE_CORES = 4          # held for the serial spine (Astra P1 reserve-capacity rule)
EXPLO_WIP_CAP = 8          # bounded exploratory WIP
CANONICAL = "origin"


class _RamSampler(threading.Thread):
    """Samples system-wide available physical bytes; peak used = total - min(avail)."""

    class _STAT(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    def __init__(self, period_s: float = 0.5):
        super().__init__(daemon=True)
        self.period = period_s
        self.samples: list[tuple[float, int, int]] = []  # (t_rel, total, avail)
        self._t0 = time.monotonic()
        self._stop = threading.Event()

    def run(self) -> None:
        stat = self._STAT(); stat.dwLength = ctypes.sizeof(self._STAT)
        while not self._stop.is_set():
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                self.samples.append((round(time.monotonic() - self._t0, 3),
                                     int(stat.ullTotalPhys), int(stat.ullAvailPhys)))
            self._stop.wait(self.period)

    def stop(self) -> None:
        self._stop.set()

    def peak(self) -> dict:
        if not self.samples:
            return {"peak_used_bytes": None, "min_avail_bytes": None}
        total = self.samples[0][1]
        min_avail = min(s[2] for s in self.samples)
        return {"peak_used_bytes": total - min_avail, "min_avail_bytes": min_avail,
                "total_bytes": total, "n_samples": len(self.samples)}


def _run(cmd, cwd=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, timeout=timeout, capture_output=True, text=True)


def _job_worker(job: dict, q_done: "queue.Queue[dict]") -> None:
    lane = Path(job["lane_root"])
    base = lane / ".tmp" / "verify_farm" / job["batch"] / job["job_id"]
    checkout, build, run = base / "checkout", base / "build", base / "run"
    rec = dict(job)
    try:
        t0 = time.monotonic()
        base.mkdir(parents=True, exist_ok=True)
        r = _run(["git", "worktree", "add", "--detach", str(checkout), job["commit"]], cwd=str(lane))
        if r.returncode != 0:
            raise RuntimeError(f"worktree add failed: {r.stderr[-500:]}")
        rec["worktree_s"] = round(time.monotonic() - t0, 3)

        # cold build: fresh private build dir, /m:2 fixed per-job policy
        t0 = time.monotonic()
        r = _run(["cmake", "-S", str(checkout / "ChimeraEngine/engine/tests_coupled_arm"),
                  "-B", str(build)], timeout=job["timeout_s"])
        if r.returncode != 0:
            raise RuntimeError(f"configure failed: {r.stderr[-800:]}")
        r = _run(["cmake", "--build", str(build), "--config", "Release",
                  "--target", "gait_unit", "--parallel", "2"], timeout=job["timeout_s"])
        if r.returncode != 0:
            raise RuntimeError(f"build failed: {r.stderr[-800:]}")
        rec["build_s"] = round(time.monotonic() - t0, 3)

        # private scene copy, hashed in place (guards copy corruption)
        run.mkdir(parents=True, exist_ok=True)
        scene = run / "scene.json"
        shutil.copyfile(job["scene"], scene)
        scene_bytes = scene.read_bytes()
        rec["scene_sha256"] = hashlib.sha256(scene_bytes).hexdigest()
        rec["scene_bytes"] = len(scene_bytes)

        # run via cmd /c raw redirect (no shell re-encoding), sample child RSS
        exe = build / "Release" / "gait_unit.exe"
        cmd = f'cmd /c ""{exe}" "{scene}" > "{run / "stdout.txt"}" 2> "{run / "stderr.txt"}""'
        t0 = time.monotonic()
        proc = subprocess.Popen(cmd, cwd=str(run))
        import psutil
        p = psutil.Process(proc.pid)
        exe_rss_peak, exe_pid = 0, None
        try:
            while proc.poll() is None:
                try:
                    for c in p.children(recursive=True):
                        if c.name().lower().startswith("gait_unit"):
                            exe_pid = c.pid
                            exe_rss_peak = max(exe_rss_peak, c.memory_info().rss)
                except psutil.Error:
                    pass
                time.sleep(0.25)
            exit_code = proc.returncode
        finally:
            if proc.poll() is None:
                proc.kill()
            exit_code = proc.returncode
        rec["run_s"] = round(time.monotonic() - t0, 3)
        rec["queue_delay_s"] = round(t0 - rec["admitted_at"], 3)
        rec["exit_code"] = exit_code
        rec["exe_pid"] = exe_pid
        rec["exe_rss_peak_bytes"] = exe_rss_peak

        stdout = (run / "stdout.txt").read_bytes()
        rec["stdout_bytes"] = len(stdout)
        rec["stdout_sha256"] = hashlib.sha256(stdout).hexdigest()
        rec["bytes_ok"] = (rec["stdout_sha256"] == job["expected_stdout_sha"]
                           and rec["stdout_bytes"] == job["expected_stdout_bytes"]
                           and rec["scene_sha256"] == job["expected_scene_sha"]
                           and exit_code == 0)
        rec["f_farm_bytes_fired"] = not rec["bytes_ok"]
        if exe_pid:
            try:
                rec["exe_wset_peak_bytes"] = psutil.Process(exe_pid).memory_full_info().wset
            except psutil.Error:
                pass
    except Exception as e:  # noqa: BLE001 -- every failure is a recorded finding
        rec["error"] = str(e)
        rec["f_farm_bytes_fired"] = True
    finally:
        rec["done_at"] = time.monotonic()
        # keep receipts, remove the heavy build dir; worktree pruned by the driver
        q_done.put(rec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane-root", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--jobs", type=int, required=True)
    ap.add_argument("--batch-label", required=True)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--expected-stdout-sha", required=True)
    ap.add_argument("--expected-stdout-bytes", type=int, required=True)
    ap.add_argument("--expected-scene-sha", required=True)
    ap.add_argument("--receipt-dir", required=True)
    ap.add_argument("--timeout-s", type=int, default=1800)
    ap.add_argument("--spine", action="store_true", help="submit one spine-priority job first")
    ap.add_argument("--r1-total", type=float, default=None, help="banked c=1 build+run seconds")
    ap.add_argument("--r1-run", type=float, default=None, help="banked c=1 run-phase seconds")
    args = ap.parse_args()

    lane = Path(args.lane_root).resolve()
    receipt = Path(args.receipt_dir).resolve()
    receipt.mkdir(parents=True, exist_ok=True)
    cores = os_cpu = __import__("os").cpu_count() or 1
    wip_limit = min(args.jobs + (1 if args.spine else 0), EXPLO_WIP_CAP, cores - RESERVE_CORES)
    timeout_s = args.timeout_s if args.r1_total is None else max(900, int(3 * args.r1_total))

    t0 = time.monotonic()
    sampler = _RamSampler()
    sampler.start()
    pending: deque = deque()
    for i in range(args.jobs):
        pending.append({"batch": args.batch_label, "job_id": f"job_{i:02d}", "spine": False,
                        "lane_root": str(lane), "commit": args.commit, "scene": args.scene,
                        "expected_stdout_sha": args.expected_stdout_sha,
                        "expected_stdout_bytes": args.expected_stdout_bytes,
                        "expected_scene_sha": args.expected_scene_sha,
                        "timeout_s": timeout_s, "admitted_at": None})
    if args.spine:
        pending.appendleft({"batch": args.batch_label, "job_id": "job_spine", "spine": True,
                            "lane_root": str(lane), "commit": args.commit, "scene": args.scene,
                            "expected_stdout_sha": args.expected_stdout_sha,
                            "expected_stdout_bytes": args.expected_stdout_bytes,
                            "expected_scene_sha": args.expected_scene_sha,
                            "timeout_s": timeout_s, "admitted_at": None})

    q_done: "queue.Queue[dict]" = queue.Queue()
    in_flight: list[tuple[dict, threading.Thread]] = []
    records: list[dict] = []
    total = len(pending)
    spine_in_flight = False

    while pending or in_flight:
        # spine-first admission: spine bypasses the WIP bound and drains exploratory admission
        if pending and pending[0]["spine"] and not spine_in_flight:
            job = pending.popleft()
            job["admitted_at"] = time.monotonic()
            th = threading.Thread(target=_job_worker, args=(job, q_done), daemon=True)
            th.start()
            in_flight.append((job, th))
            spine_in_flight = True
        while pending and not pending[0]["spine"] and len(in_flight) < wip_limit and not spine_in_flight:
            job = pending.popleft()
            job["admitted_at"] = time.monotonic()
            th = threading.Thread(target=_job_worker, args=(job, q_done), daemon=True)
            th.start()
            in_flight.append((job, th))
        for job, th in list(in_flight):
            if not th.is_alive():
                in_flight.remove((job, th))
                if job["spine"]:
                    spine_in_flight = False
        try:
            while True:
                records.append(q_done.get_nowait())
        except queue.Empty:
            pass
        time.sleep(0.05)

    while True:
        try:
            records.append(q_done.get_nowait())
        except queue.Empty:
            break
    sampler.stop()
    sampler.join(timeout=2)

    batch_s = round(time.monotonic() - t0, 3)
    run_secs = sorted(r.get("run_s", 0.0) for r in records)
    p50 = run_secs[len(run_secs) // 2] if run_secs else None
    p95 = run_secs[min(len(run_secs) - 1, int(0.95 * len(run_secs)))] if run_secs else None
    verdict = {
        "batch": args.batch_label,
        "requested_jobs": args.jobs,
        "spine_submitted": args.spine,
        "wip_limit": wip_limit,
        "policy": {"reserve_cores": RESERVE_CORES, "exploratory_wip_cap": EXPLO_WIP_CAP,
                   "spine_first": True, "per_job_build_parallel": 2},
        "cores": cores,
        "commit": args.commit,
        "wall_clock_s": batch_s,
        "jobs": sorted(records, key=lambda r: r["job_id"]),
        "run_p50_s": p50,
        "run_p95_s": p95,
        "ram": sampler.peak(),
        "f_farm_bytes_fired": any(r.get("f_farm_bytes_fired") for r in records),
        "f_farm_tail_fired": any(
            r.get("spine") and r.get("run_s") is not None and args.r1_run is not None
            and r["run_s"] > 1.35 * args.r1_run
            for r in records),
    }
    out = receipt / f"batch_{args.batch_label}.json"
    out.write_text(json.dumps(verdict, indent=2), encoding="utf-8")

    # prune the batch worktrees (object store is shared; heavy dirs already removed)
    for r in records:
        wt = lane / ".tmp" / "verify_farm" / args.batch_label / r["job_id"] / "checkout"
        if wt.exists():
            _run(["git", "worktree", "remove", "--force", str(wt)], cwd=str(lane))
            _run(["git", "worktree", "prune"], cwd=str(lane))
        shutil.rmtree(lane / ".tmp" / "verify_farm" / args.batch_label / r["job_id"],
                      ignore_errors=True)

    print(json.dumps({k: v for k, v in verdict.items() if k != "jobs"}, indent=2))
    for r in verdict["jobs"]:
        print(f"  {r['job_id']}: exit={r.get('exit_code')} run_s={r.get('run_s')} "
              f"bytes={r.get('stdout_bytes')} sha={str(r.get('stdout_sha256'))[:12]} "
              f"bytes_ok={r.get('bytes_ok')}")
    return 1 if verdict["f_farm_bytes_fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
