"""run_falsifiers.py -- ONT-U04 candidate verification bootstrap.

This attempt checkout contains NO campaign product tree (sparse checkout of
tools/monkey_campaign/contributions/ONT-U04/ only, HEAD c525b82c). The pinned
battery `reference/tools/monkey_campaign/product/input_settings_tests.py`
resolves its own imports relative to its parents[3] "repo root", which inside
this candidate IS `reference/` (same package shape as the pin: implicit
namespace packages for tools/monkey_campaign, byte-exact package __init__
files where the pin has them). This runner therefore runs THE PINNED TEST
FILE ITSELF -- unmodified, byte-exact (sha256 in EXTRACTION_LEDGER.json) --
with `reference/` as the root and this directory on sys.path so that
`import input_settings` resolves to the reference module.

It adds exactly three things and no more:
  1. Hash proof FIRST: the two product modules under test are byte-identical
     to the extracted reference copies (any drift aborts before running).
  2. A bounded run: wall-clock limit 120 s (per-attempt test bound) and a
     stdout capture cap of 16 MiB (the attempt's max_new_output_bytes). The
     battery itself is bounded by construction (frozen seed, 2000-payload
     fuzz); this runner additionally enforces the attempt limits.
  3. A machine-checkable verdict: exit 0 iff the pinned battery's own main()
     returns 0 (its VERDICT: GREEN line), plus a JSON summary line printed
     LAST containing hashes, limits, elapsed time and outcome.

Headless, CPU-only, deterministic: no network, no GPU, no engine, no clock
dependency (elapsed time is reported, never asserted).

Usage:  python -B tools/monkey_campaign/contributions/ONT-U04/run_falsifiers.py
        (from the attempt checkout root; or from anywhere with an explicit
        path -- all paths are resolved from __file__, never cwd)
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

_TIME_LIMIT_S = 120.0        # per-attempt test invocation bound (brief)
_OUTPUT_LIMIT_BYTES = 16 * 1024 * 1024   # max_new_output_bytes (brief)

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
BATTERY = REFERENCE / "tools" / "monkey_campaign" / "product" / "input_settings_tests.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    started = time.monotonic()
    summary = {
        "schema": "chimera.ont-u04.verification.v1",
        "attempt": "caffa214d5c1429f87a145634f3dd373",
        "source_revision": "9afbddcd90164b5544a16fd0bc72278d985eb6e3",
        "battery": str(BATTERY.relative_to(HERE)),
        "limits": {"time_s": _TIME_LIMIT_S, "output_bytes": _OUTPUT_LIMIT_BYTES},
    }

    # ── hash proof before anything runs ──────────────────────────────────
    module_under_test = REFERENCE / "tools" / "monkey_campaign" / "product" / "input_settings.py"
    mapper = REFERENCE / "tools" / "monkey_campaign" / "product" / "input_mapper.py"
    command_record = REFERENCE / "tools" / "science_funnel" / "typeb_export" / "command_record.py"
    ledger = json.loads((HERE / "EXTRACTION_LEDGER.json").read_text(encoding="utf-8"))
    ledger_hashes = {entry["path"]: entry["sha256"] for entry in ledger["entries"]}
    checks = {
        str(module_under_test.relative_to(HERE).as_posix()): sha256(module_under_test),
        str(mapper.relative_to(HERE).as_posix()): sha256(mapper),
        str(command_record.relative_to(HERE).as_posix()): sha256(command_record),
        str(BATTERY.relative_to(HERE).as_posix()): sha256(BATTERY),
    }
    drift = {p: h for p, h in checks.items() if ledger_hashes.get(p) != h}
    summary["hashes"] = checks
    if drift:
        summary["outcome"] = "ABORTED_HASH_DRIFT"
        summary["drift"] = drift
        print(json.dumps(summary, indent=1))
        return 3
    summary["hash_proof"] = "candidate == reference == ledger for every module under test"

    # ── run THE PINNED BATTERY, unmodified, in a controlled namespace ────
    # The battery's own bootstrap adds its parent directory (where
    # input_settings/input_mapper live) and its parents[3] root (= reference/)
    # to sys.path before importing; nothing else is needed or added.
    sys.path.insert(0, str(REFERENCE))     # the battery's parents[3] root
    spec_path = str(BATTERY)
    captured = io.StringIO()
    verdict_output: str
    code = 1
    outcome = "ERROR"
    t0 = time.monotonic()
    elapsed = 0.0
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("input_settings_tests", spec_path)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        with redirect_stdout(captured):
            spec.loader.exec_module(mod)          # defines falsifier_* + main
            code = int(mod.main())                # the battery's own verdict
        elapsed = time.monotonic() - t0
        verdict_output = captured.getvalue()
        if len(verdict_output.encode("utf-8", "replace")) > _OUTPUT_LIMIT_BYTES:
            outcome = "OUTPUT_LIMIT_EXCEEDED"
            code = 4
        elif elapsed > _TIME_LIMIT_S:
            outcome = "TIME_LIMIT_EXCEEDED"
            code = 5
        else:
            outcome = "GREEN" if code == 0 else "RED"
    except BaseException as exc:  # noqa: BLE001 -- a crashed battery is a RED
        elapsed = time.monotonic() - t0
        verdict_output = captured.getvalue() + f"\n[runner] battery raised: {exc!r}\n"
        outcome = "BATTERY_EXCEPTION"

    summary["outcome"] = outcome
    summary["battery_exit_code"] = code
    summary["elapsed_s"] = round(elapsed, 3)
    lines = verdict_output.splitlines()
    summary["verdict_line"] = next((l for l in lines if l.startswith("VERDICT:")), None)
    summary["pass_fail_counts"] = {
        "pass": sum(1 for l in lines if "[PASS]" in l),
        "fail": sum(1 for l in lines if "[FAIL]" in l),
    }
    # Full battery output goes to stderr (bounded); the JSON summary is the
    # LAST stdout line so a caller can machine-check the verdict.
    sys.stderr.write(verdict_output)
    print(json.dumps(summary, indent=1))
    return 0 if outcome == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
