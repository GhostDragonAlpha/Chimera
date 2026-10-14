"""Sealed-runner driver for the native combine-window transaction gate.

The baseline executable must reproduce the known late-refusal partial commit.
The candidate executable must preserve the live store and scheduler ledger on
all refused windows, permit a clean retry, and stay deterministic across the
declared worker counts and contribution-list permutations.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ENGINE = ROOT / "ChimeraEngine" / "engine"
BASELINE = HERE / "baseline"
BASELINE_HEADER = BASELINE / "baseline_combine_core.hpp"
GATE_SOURCE = HERE / "transaction_gate.cpp"
PINNED_BASELINE_SHA256 = (
    "6d7e0ea757c112c60d4fef3e3cbc408011ef51ec1c4bc44eb1a6babc9bb4eb89"
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def short(text, limit=1200):
    text = text.decode("utf-8", errors="replace")
    return text[-limit:]


def compile_one(gxx, source, output, include_dirs, baseline=False):
    command = [gxx, "-std=c++17", "-O2", "-fno-fast-math",
               "-ffp-contract=off", "-pthread", "-Wall", "-Wextra"]
    if baseline:
        command.append("-DCHIMERA_USE_BASELINE_CORE=1")
    for include in include_dirs:
        command.extend(["-I", str(include)])
    command.extend([str(source), "-o", str(output)])
    proc = subprocess.run(command, capture_output=True, check=False,
                          timeout=180)
    record = {"returncode": proc.returncode,
              "stdout_tail": short(proc.stdout),
              "stderr_tail": short(proc.stderr)}
    if proc.returncode:
        raise RuntimeError("compile failed: " + json.dumps(record))
    record["binary_sha256"] = sha256(output)
    return record


def run_one(binary, mode, expected_marker, timeout=180):
    proc = subprocess.run([str(binary), mode], capture_output=True,
                          check=False, timeout=timeout)
    stdout = proc.stdout.decode("utf-8", errors="replace").strip()
    stderr = proc.stderr.decode("utf-8", errors="replace").strip()
    if proc.returncode != 0 or expected_marker not in stdout:
        raise RuntimeError(
            f"{binary.name} {mode} failed (exit={proc.returncode}); "
            f"stdout={stdout[-1000:]}; stderr={stderr[-1000:]}")
    return {"mode": mode, "returncode": proc.returncode,
            "stdout": stdout, "stderr": stderr,
            "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
            "stdout_bytes": len(proc.stdout)}


def main():
    out_raw = os.environ.get("CHIMERA_OUTPUT_DIR")
    if not out_raw:
        raise RuntimeError("CHIMERA_OUTPUT_DIR is required by the sealed runner")
    out = Path(out_raw)
    out.mkdir(parents=True, exist_ok=True)
    build = out / "native_coupling_transaction_build"
    build.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "chimera.native_coupling_transaction_result.v1",
        "passed": False,
        "scope": "native scheduler whole-window rollback, retry, and deterministic success parity",
        "worker_counts": [1, 2, 4],
        "success_parity_cases_expected": 9,
        "refusal_cases_expected": 15,
        "compiles": {},
        "runs": [],
        "inputs": {},
        "failures": [],
    }
    try:
        gxx = shutil.which("g++")
        if not gxx:
            raise RuntimeError("GNU g++ is unavailable; installs are forbidden")
        if not BASELINE_HEADER.is_file():
            raise RuntimeError(f"pinned baseline header missing: {BASELINE_HEADER}")
        baseline_sha = sha256(BASELINE_HEADER)
        if baseline_sha != PINNED_BASELINE_SHA256:
            raise RuntimeError(
                f"baseline header hash mismatch: {baseline_sha} != "
                f"{PINNED_BASELINE_SHA256}")
        candidate_core = ENGINE / "combine_core.hpp"
        executor_header = ENGINE / "contribution_executor.hpp"
        for required in (candidate_core, executor_header, GATE_SOURCE):
            if not required.is_file():
                raise RuntimeError(f"required input missing: {required}")
        version = subprocess.run([gxx, "--version"], capture_output=True,
                                  check=False, timeout=15)
        if version.returncode:
            raise RuntimeError("g++ --version failed")
        version_text = version.stdout.decode("utf-8", errors="replace").splitlines()
        report["compiler"] = {"path": str(Path(gxx).resolve()),
                              "version_line": version_text[0] if version_text else ""}
        report["inputs"] = {
            "baseline_combine_core.hpp": baseline_sha,
            "candidate_combine_core.hpp": sha256(candidate_core),
            "contribution_executor.hpp": sha256(executor_header),
            "transaction_gate.cpp": sha256(GATE_SOURCE),
        }
        baseline_bin = build / "transaction_gate_baseline.exe"
        candidate_bin = build / "transaction_gate_candidate.exe"
        report["compiles"]["baseline"] = compile_one(
            gxx, GATE_SOURCE, baseline_bin, [BASELINE, ENGINE], baseline=True)
        report["compiles"]["candidate"] = compile_one(
            gxx, GATE_SOURCE, candidate_bin, [ENGINE], baseline=False)
        report["runs"].append(run_one(
            baseline_bin, "baseline", "BASELINE_PARTIAL_MUTATION=true"))
        baseline_reference = run_one(
            baseline_bin, "reference", "SUCCESS_STORE_BYTES=")
        candidate_run = run_one(
            candidate_bin, "candidate", "CANDIDATE_SUCCESS_PARITY=9")
        report["runs"].extend([baseline_reference, candidate_run])
        baseline_signature = {
            line.split("=", 1)[0]: line.split("=", 1)[1]
            for line in baseline_reference["stdout"].splitlines()
            if line.startswith("SUCCESS_")
        }
        candidate_signature = {
            line.split("=", 1)[0]: line.split("=", 1)[1]
            for line in candidate_run["stdout"].splitlines()
            if line.startswith("SUCCESS_")
        }
        if not baseline_signature or baseline_signature != candidate_signature:
            raise AssertionError(
                "successful-window bytes/routing/ledger differ from unmodified baseline")
        report["success_parity_against_unmodified_baseline"] = True
        report["passed"] = True
    except Exception as exc:  # receipts must survive any compile/run failure
        report["failures"].append({"type": type(exc).__name__,
                                   "detail": str(exc)})
    finally:
        report["driver_sha256"] = sha256(Path(__file__))
        (out / "result.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n",
            encoding="utf-8")
        print(json.dumps({"passed": report["passed"],
                          "runs_completed": len(report["runs"]),
                          "failures": report["failures"]}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
