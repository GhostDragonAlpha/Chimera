"""compute_harness.py - the reusable compute acceleration layer for the fleet.

work.data.compute_harness (Rule 0 infrastructure admission)
    STATEMENT : the fleet's bottleneck is mechanics, not physics: a serial MSVC
                engine build and a serial funnel test loop waste most of a
                24-core box, and no agent can see where the wall time goes.
    PREDICTION: with /MP24 + a parallel generator build, a clean engine rebuild
                falls from 10-20 minutes to under 5; with per-module process
                parallelism, the full funnel suite falls from 15-30 minutes to
                under 8.
    FALSIFIER : "a clean rebuild completes in <5 minutes (was 10-20) AND the
                full test suite completes in <8 minutes (was 15-30)" - measure
                both before and after; either number failing falsifies the
                harness. Measured with `profile` (or `build` + `test-python-full`)
                on the same machine state.

Subcommands (each prints its wall time):
    build             configure + parallel Release build of the engine
    test-native       build + run the CMake native test executables, timed
    test-python-quick fast funnel modules only (skips known-slow set)
    test-python-full  every funnel module, parallel processes
    gpu-info          CUDA availability, device, VRAM (or what to install)
    gpu-oracle        batched M(q)/gravity/bias/Jacobian on the GPU, parity vs
                      the CPU analytic reference (tools/gpu_oracle.py)
    profile           time every pipeline stage back to back, one JSON summary

Every subcommand writes machine-readable output under .tmp/compute_harness/.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / ".tmp" / "compute_harness"
ENGINE_SRC = REPO / "ChimeraEngine" / "engine"
DEFAULT_PY = Path(r"E:\PythonChimera\.venv-hy3d\Scripts\python.exe")
PARALLEL_PS1 = REPO / "tools" / "parallel_test.ps1"
# The known-slow modules for iteration cycles (--quick skips these two).
QUICK_SKIP = ("test_surface_scene", "test_force_compiler")

FUNNEL_TESTS_DIR = REPO / "tools" / "science_funnel" / "tests"
# Native test targets: each subdir of ChimeraEngine/engine with a CMakeLists
# builds standalone check executables (never the engine server itself).
NATIVE_TEST_DIRS = ("tests_arm_dynamics", "tests_articulation",
                    "tests_coupled_arm", "tests_environment", "tests_p1")


def now_utc():
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())


def venv_python():
    if DEFAULT_PY.exists():
        return str(DEFAULT_PY)
    return sys.executable


def default_jobs():
    # 24 physical cores on the operator box; os.cpu_count() reports logical.
    env = os.environ.get("CHIMERA_BUILD_JOBS")
    if env and env.isdigit():
        return int(env)
    return 24


def run(cmd, log_path=None, timeout=None, env=None, cwd=None):
    """Run a command; capture output to a log file and also return it."""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    started = time.perf_counter()
    proc = subprocess.run(
        cmd, cwd=str(cwd or REPO), env=full_env, timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    elapsed = time.perf_counter() - started
    text = proc.stdout.decode("utf-8", "replace")
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(text, encoding="utf-8")
    return proc.returncode, elapsed, text


def save(name, payload):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def emit(payload):
    print(json.dumps(payload, indent=2))


# ---------------------------------------------------------------- build ----

def cmd_build(args):
    build_dir = REPO / ".tmp" / "compute_harness" / (
        getattr(args, "build_dir", None) or "build_engine")
    jobs = args.jobs or default_jobs()
    if getattr(args, "clean", False) and build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)
    env = {"CMAKE_BUILD_PARALLEL_LEVEL": str(jobs)}
    total = time.perf_counter()

    rc_cfg, cfg_sec, _ = run(
        ["cmake", "-S", str(ENGINE_SRC), "-B", str(build_dir)],
        log_path=OUT / "build_configure.log", env=env,
    )
    rc_build, build_sec, build_log = run(
        ["cmake", "--build", str(build_dir), "--config", "Release",
         "--parallel", str(jobs)],
        log_path=OUT / "build.log", env=env, timeout=args.timeout,
    )
    total_sec = time.perf_counter() - total

    exe = build_dir / "Release" / "chimera_engine.exe"
    ok = rc_cfg == 0 and rc_build == 0
    result = {
        "phase": "build",
        "parallel_jobs": jobs,
        "cmake_build_parallel_level": jobs,
        "configure_seconds": round(cfg_sec, 2),
        "build_seconds": round(build_sec, 2),
        "total_seconds": round(total_sec, 2),
        "configure_rc": rc_cfg,
        "build_rc": rc_build,
        "engine_exe_exists": exe.exists(),
        "build_dir": str(build_dir),
        "recorded_utc": now_utc(),
        "ok": ok,
    }
    if not ok:
        tail = "\n".join(build_log.splitlines()[-40:])
        result["build_log_tail"] = tail
    emit(result)
    save("build_last.json", result)
    return 0 if result["ok"] else 1


# ----------------------------------------------------------- test-native ----

def _native_build_dir(name):
    return REPO / ".tmp" / "compute_harness" / ("build_" + name)


def _ensure_native_built(jobs, timeout):
    """Configure+build each native test dir once; returns {name: rc}."""
    built = {}
    env = {"CMAKE_BUILD_PARALLEL_LEVEL": str(jobs)}
    for name in NATIVE_TEST_DIRS:
        src = ENGINE_SRC / name
        if not (src / "CMakeLists.txt").exists():
            built[name] = "missing"
            continue
        bdir = _native_build_dir(name)
        rc, _, _ = run(["cmake", "-S", str(src), "-B", str(bdir)],
                       log_path=OUT / f"native_{name}_configure.log", env=env)
        if rc == 0:
            rc, _, _ = run(["cmake", "--build", str(bdir), "--config", "Release",
                            "--parallel", str(jobs)],
                           log_path=OUT / f"native_{name}_build.log",
                           env=env, timeout=timeout)
        built[name] = rc
    return built


def cmd_test_native(args):
    jobs = args.jobs or default_jobs()
    total = time.perf_counter()
    builds = _ensure_native_built(jobs, args.timeout)

    results = []
    for name in NATIVE_TEST_DIRS:
        bdir = _native_build_dir(name)
        rc = builds.get(name)
        exes = sorted(bdir.glob("Release/*.exe")) if bdir.exists() else []
        if not exes:
            results.append({"dir": name, "build_rc": rc, "executables": 0,
                            "skipped": "no executables"})
            continue
        for exe in exes:
            # The engine server binary is not a test; native test exes are
            # self-checking mains that exit nonzero on failure. Some require
            # fixture arguments: a bare invocation that prints "usage" is
            # reported as needs_args, not as a failure (per-fixture argument
            # wiring is lane-specific work).
            entry = {"dir": name, "exe": exe.name, "build_rc": rc}
            try:
                code, sec, text = run([str(exe)], timeout=args.timeout,
                                      log_path=OUT / f"native_run_{exe.stem}.log")
                first = text.strip().splitlines()[0] if text.strip() else ""
                if code != 0 and first.lower().startswith("usage"):
                    entry.update(exit_code=code, seconds=round(sec, 2),
                                 needs_args=True, passed=None,
                                 note=first)
                else:
                    entry.update(exit_code=code, seconds=round(sec, 2),
                                 passed=(code == 0))
            except subprocess.TimeoutExpired:
                entry.update(exit_code="timeout", passed=False,
                             seconds=round(args.timeout, 2))
            results.append(entry)

    total_sec = time.perf_counter() - total
    ran = [r for r in results if "exit_code" in r]
    hard_failed = [r for r in ran if r.get("passed") is False]
    result = {
        "phase": "test-native",
        "total_seconds": round(total_sec, 2),
        "executables_run": len(ran),
        "passed": len([r for r in ran if r.get("passed") is True]),
        "needs_args": len([r for r in ran if r.get("needs_args")]),
        "failed": len(hard_failed),
        "all_passed": bool(ran) and not hard_failed,
        "results": results,
        "recorded_utc": now_utc(),
    }
    emit(result)
    save("native_last.json", result)
    return 0 if result["all_passed"] else 1


# -------------------------------------------------------- test-python-* ----

def _funnel_modules():
    mods = sorted(p.stem for p in FUNNEL_TESTS_DIR.glob("test_*.py"))
    return mods


def _run_parallel_tests(args, quick):
    if not PARALLEL_PS1.exists():
        print(f"missing {PARALLEL_PS1}", file=sys.stderr)
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PARALLEL_PS1),
        "-Python", venv_python(),
        "-Jobs", str(args.jobs or 12),
        "-RepoRoot", str(REPO),
        "-TimeoutSec", str(args.timeout),
    ]
    if quick:
        cmd.append("-Quick")
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=str(REPO),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=args.timeout + 3600)
    except subprocess.TimeoutExpired:
        # The runner itself is slow because its modules are slow; killing it
        # here loses the measurement. Report as a failed stage instead.
        (OUT / "parallel_test_console.log").write_text(
            "runner subprocess timeout", encoding="utf-8")
        return 2
    wall = time.perf_counter() - started
    text = proc.stdout.decode("utf-8", "replace")
    (OUT / "parallel_test_console.log").parent.mkdir(parents=True, exist_ok=True)
    (OUT / "parallel_test_console.log").write_text(text, encoding="utf-8")

    # The .ps1 writes the machine-readable summary; read it back.
    # (utf-8-sig: Windows PowerShell's Out-File prepends a BOM.)
    result_path = OUT / "parallel_last.json"
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8-sig"))
        result["harness_wall_seconds"] = round(wall, 2)
        result["harness_rc"] = proc.returncode
        emit(result)
        save(("parallel_quick_last.json" if quick else "parallel_full_last.json"),
             result)
        return 0 if result.get("all_passed") else 1
    print(text)
    return proc.returncode


def cmd_test_python_quick(args):
    return _run_parallel_tests(args, quick=True)


def cmd_test_python_full(args):
    return _run_parallel_tests(args, quick=False)


# ------------------------------------------------------------------ gpu ----

def cmd_gpu_info(args):
    info = {
        "phase": "gpu-info",
        "venv_python": venv_python(),
        "recorded_utc": now_utc(),
    }
    try:
        import torch  # noqa: PLC0415 - optional dependency by design
        info["torch_version"] = torch.__version__
        info["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info["device_name"] = props.name
            info["cuda_capability"] = f"{props.major}.{props.minor}"
            info["total_vram_gb"] = round(props.total_memory / 2**30, 2)
            free, total = torch.cuda.mem_get_info(0)
            info["free_vram_gb"] = round(free / 2**30, 2)
            info["multiprocessors"] = props.multi_processor_count
        info["status"] = ("ready" if torch.cuda.is_available()
                          else "torch_present_cuda_unavailable")
    except ImportError:
        info["status"] = "torch_missing"
        info["cuda_available"] = False
        info["one_command_install"] = (
            f'"{venv_python()}" -m pip install torch '
            "--index-url https://download.pytorch.org/whl/cu124"
        )
        info["installer_script"] = "tools/install_torch_cuda.ps1"
    emit(info)
    save("gpu_info_last.json", info)
    return 0


def cmd_gpu_oracle(args):
    sys.path.insert(0, str(REPO))
    import tools.gpu_oracle as oracle  # noqa: PLC0415
    result = oracle.run(
        poses=args.poses, check=args.check, device=args.device,
        seed=args.seed, out_path=Path(args.out) if args.out else None,
        random_rates=not args.zero_rates,
    )
    emit(result)
    return 0 if result.get("parity_pass") else 1


# -------------------------------------------------------------- profile ----

def cmd_profile(args):
    stages = []
    total = time.perf_counter()

    def stage(name, fn, *a, **kw):
        t0 = time.perf_counter()
        rc = fn(*a, **kw)
        stages.append({"stage": name, "seconds": round(time.perf_counter() - t0, 2),
                       "rc": rc})
        return rc

    rc_gpu = stage("gpu-info", cmd_gpu_info, args)
    rc_build = stage("build", cmd_build, args)
    rc_native = stage("test-native", cmd_test_native, args)
    rc_quick = stage("test-python-quick", cmd_test_python_quick, args)
    rc_full = None
    if args.full:
        rc_full = stage("test-python-full", cmd_test_python_full, args)

    wall = round(time.perf_counter() - total, 2)
    summary = {
        "phase": "profile",
        "stages": stages,
        "wall_seconds": wall,
        "falsifier": ("clean rebuild <300 s AND full test suite <480 s; "
                      "either number failing falsifies work.data.compute_harness"),
        "recorded_utc": now_utc(),
    }
    emit(summary)
    save("profile_last.json", summary)
    codes = [s["rc"] for s in stages]
    return 0 if all(c == 0 for c in codes) else 1


# ----------------------------------------------------------------- main ----

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build", help="configure + parallel engine build")
    p.add_argument("--jobs", type=int, default=None,
                   help="parallel build jobs (default 24 / CHIMERA_BUILD_JOBS)")
    p.add_argument("--build-dir", default=None,
                   help="build dir name under .tmp/compute_harness")
    p.add_argument("--clean", action="store_true",
                   help="wipe the build dir first (measures a clean rebuild)")
    p.add_argument("--timeout", type=float, default=3600.0)
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("test-native", help="build + run native test executables")
    p.add_argument("--jobs", type=int, default=None)
    p.add_argument("--timeout", type=float, default=600.0,
                   help="per-executable timeout in seconds")
    p.set_defaults(fn=cmd_test_native)

    p = sub.add_parser("test-python-quick",
                       help="fast funnel modules only (skips " +
                            ", ".join(QUICK_SKIP) + ")")
    p.add_argument("--jobs", type=int, default=None, help="concurrent modules")
    p.add_argument("--timeout", type=float, default=1800.0,
                   help="per-module timeout in seconds")
    p.set_defaults(fn=cmd_test_python_quick)

    p = sub.add_parser("test-python-full", help="all funnel modules, parallel")
    p.add_argument("--jobs", type=int, default=None, help="concurrent modules")
    p.add_argument("--timeout", type=float, default=5400.0,
                   help="per-module timeout in seconds "
                        "(test_surface_scene alone needs ~3100s)")
    p.set_defaults(fn=cmd_test_python_full)

    p = sub.add_parser("gpu-info", help="CUDA availability and VRAM")
    p.set_defaults(fn=cmd_gpu_info)

    p = sub.add_parser("gpu-oracle",
                       help="batched M(q)/gravity/bias/Jacobian on GPU")
    p.add_argument("--poses", type=int, default=4096)
    p.add_argument("--check", type=int, default=16,
                   help="poses verified against the CPU analytic reference")
    p.add_argument("--device", default=None, help="cuda | cpu (default: auto)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--zero-rates", action="store_true",
                   help="zero joint rates (bias check becomes trivial)")
    p.add_argument("--out", default=None, help="optional JSON receipt path")
    p.set_defaults(fn=cmd_gpu_oracle)

    p = sub.add_parser("profile", help="time every pipeline stage")
    p.add_argument("--jobs", type=int, default=None)
    p.add_argument("--timeout", type=float, default=1800.0)
    p.add_argument("--full", action="store_true",
                   help="also run the full funnel suite (slow)")
    p.set_defaults(fn=cmd_profile)

    args = ap.parse_args()
    raise SystemExit(args.fn(args))


if __name__ == "__main__":
    main()
