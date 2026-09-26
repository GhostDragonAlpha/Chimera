"""implementation.py -- I-R06-FAILURE-SEQUENCES-FOLLOWUP: the product
regression ENTRY ADAPTER for the accepted failure-sequence runner (merged
PR #123).

The smallest test entry: verify the accepted runner's identity (sha256 pins),
then invoke it — clean run via its CLI (the eight cross-component sequences
against the ledger-bound pinned product classes) plus its own unittest suite
via subprocess — and demonstrate injected-counterexample detection by
replaying the runner's OWN deliberately-broken LatchingMapper control through
the invariant checker. No new sequences, no new fuzz, no production change,
no device claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

RUNNER_DIR = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/kanban-attempts/"
    "I-R06-FAILURE-SEQUENCES/c57fd6bb125142ee9d593f800eb32dd4")
RUNNER = "failure_sequences.py"
SUITE = "test_failure_sequences.py"
RUNNER_SHA256 = "d3e11285627259f5989e6085051df22051343e657e1ebda7ad97c63f8a459e69"
SUITE_SHA256 = "283efad2ec8140e47fc82587b1342ac9bc43b9afe90113b100bb496d81fb247c"
SCHEMA = "i-r06-followup.regression_entry.v1"


class IdentityFailure(RuntimeError):
    pass


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_identity(runner_dir: pathlib.Path = RUNNER_DIR) -> dict:
    runner = runner_dir / RUNNER
    suite = runner_dir / SUITE
    ledger = runner_dir / "reference" / "EXTRACTION_LEDGER.json"
    for path in (runner, suite, ledger):
        if not path.is_file():
            raise IdentityFailure(f"missing {path.name} in accepted runner dir")
    actual_runner = sha256_file(runner)
    actual_suite = sha256_file(suite)
    if actual_runner != RUNNER_SHA256:
        raise IdentityFailure(f"runner identity mismatch: {actual_runner}")
    if actual_suite != SUITE_SHA256:
        raise IdentityFailure(f"suite identity mismatch: {actual_suite}")
    ledger_data = json.loads(ledger.read_text(encoding="utf-8"))
    if not ledger_data:
        raise IdentityFailure("empty extraction ledger")
    return {"runner_sha256": actual_runner, "suite_sha256": actual_suite,
            "ledger_entries": len(json.dumps(ledger_data))}


def clean_run() -> dict:
    proc = subprocess.run([sys.executable, "-B", RUNNER],
                          cwd=str(RUNNER_DIR), capture_output=True,
                          timeout=110)
    return {"exit": proc.returncode,
            "all_eight": b"8/8 sequences passed" in proc.stdout,
            "tail": proc.stdout.decode("utf-8", "replace").strip()
                     .splitlines()[-1] if proc.stdout else ""}


def suite_run() -> dict:
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", SUITE[:-3], "-v"],
        cwd=str(RUNNER_DIR), capture_output=True, timeout=110)
    return {"exit": proc.returncode,
            "ok": proc.returncode == 0,
            "summary_line": (proc.stdout.decode("utf-8", "replace")
                             .strip().splitlines() or [""])[-1]}


def counterexample_detection() -> dict:
    """Replay the runner's OWN broken control (CTRL-01): the latch must be
    DETECTED by SEQ-01's invariant checker — same call shape the accepted
    suite's BrokenControls test uses."""
    code = (
        "import sys, json\n"
        f"sys.path.insert(0, r'{RUNNER_DIR}')\n"
        "import failure_sequences as fs\n"
        "from test_failure_sequences import LatchingMapper\n"
        "bound = fs.get_bound()\n"
        "session = fs.SequenceSession(bound, mapper_factory=lambda sink: "
        "LatchingMapper(sink))\n"
        "result = fs.run_sequence('SEQ-01', session=session, bound=bound)\n"
        "print(json.dumps({'passed': result.passed, "
        "'violations': result.violations[:3], "
        "'control': result.used_control_mapper}))\n")
    proc = subprocess.run([sys.executable, "-B", "-c", code],
                          cwd=str(RUNNER_DIR), capture_output=True,
                          timeout=110)
    try:
        payload = json.loads(proc.stdout.decode("utf-8", "replace")
                             .strip().splitlines()[-1])
    except (ValueError, IndexError):
        payload = {"passed": None, "violations": [], "control": None}
    detected = (payload["passed"] is False
                and any(str(v).startswith("zombie") for v in payload["violations"])
                and payload["control"] == "LatchingMapper")
    return {"exit": proc.returncode, "payload": payload,
            "detected": bool(detected)}


def run_entry() -> dict:
    identity = verify_identity()
    clean = clean_run()
    suite = suite_run()
    detection = counterexample_detection()
    result = {
        "schema": SCHEMA, "identity": identity, "clean_run": clean,
        "suite_run": suite, "counterexample_detection": detection,
        "device_testing_claimed": False,
        "note": "headless CPU regression entry; no device/native testing "
                "claimed (card falsifier law)",
        "all_ok": (clean["exit"] == 0 and clean["all_eight"]
                   and suite["ok"] and detection["detected"]),
    }
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="regression_entry_result.json")
    args = ap.parse_args(argv)
    result = run_entry()
    pathlib.Path(args.out).write_text(
        json.dumps(result, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({k: result[k] for k in
                      ("all_ok",)}, indent=1))
    print("clean:", result["clean_run"], "| suite:", result["suite_run"],
          "| detection:", result["counterexample_detection"]["detected"])
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
