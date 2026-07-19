#!/usr/bin/env python3
"""
run.py — Gaussian Foundry Entry Point

Runs the full autonomous pipeline:
  Council (dialectic) → Bridge (spec) → Workshop (forge) → Proving Ground (eval)

Usage:
  python run.py                            # Full pipeline
  python run.py --council-only             # Just the Q&A cycle
  python run.py --forge-only specs/spec_001.json  # Just build from spec
"""

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

WORKER_URL = "http://127.0.0.1:8892"


def check_worker():
    """Ensure the worker bridge is running."""
    try:
        resp = urllib.request.urlopen(f"{WORKER_URL}/api/status", timeout=3)
        status = json.loads(resp.read().decode())
        if status.get("status") != "running":
            print(f"[ERROR] Worker bridge not running on {WORKER_URL}")
            print(f"  Start: cd E:\\PythonChimera\\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8892")
            sys.exit(1)
        print(f"[OK] Worker bridge: running (PID {status.get('pid')})")
        return True
    except Exception as e:
        print(f"[ERROR] Cannot reach worker: {e}")
        print(f"  Start: cd E:\\PythonChimera\\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8892")
        sys.exit(1)


def run_council(turns: int = 2):
    """Run the dialectical loop."""
    print(f"\n{'='*60}")
    print(f"  COUNCIL — {turns} turns of dialectical Q&A")
    print(f"{'='*60}\n")
    
    from dialogos import run_loop
    run_loop(max_turns=turns)
    print("[COUNCIL] Complete")


def run_bridge(turn: int = None):
    """Bridge council output to forge spec."""
    print(f"\n{'='*60}")
    print(f"  BRIDGE — Council → Workshop")
    print(f"{'='*60}\n")

    from council_to_forge import generate_and_save
    spec_path = generate_and_save(turn)
    print(f"[BRIDGE] Spec ready: {spec_path}")
    return spec_path


def run_forge(spec_path: str):
    """Run the implementation workshop."""
    print(f"\n{'='*60}")
    print(f"  WORKSHOP — Implement, Build, Review, Test")
    print(f"{'='*60}\n")

    from forge import run_forge
    result = run_forge(spec_path)

    if result["success"]:
        print(f"\n[WORKSHOP] ALL STAGES PASSED")
    else:
        print(f"\n[WORKSHOP] FAILED at stage [{result['failed_at']}]")
        print(f"  Reason: {result['failure_reason']}")
    return result


def run_proving_ground():
    """Run evaluation probes."""
    print(f"\n{'='*60}")
    print(f"  PROVING GROUND — Evaluation")
    print(f"{'='*60}\n")

    results = {}
    
    # 1. Build check
    print("\n--- Proving Ground: Build check ---")
    try:
        body = json.dumps({"command": "cd E:/PythonChimera/Chimera && python -m ubt status 2>&1 | tail -5"}).encode()
        req = urllib.request.Request(f"{WORKER_URL}/api/bash", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
        results["build"] = data.get("data", {})
        print(f"  Exit code: {results['build'].get('exitCode')}")
    except Exception as e:
        results["build"] = {"error": str(e)}
        print(f"  Error: {e}")

    # 2. Status check
    print("\n--- Proving Ground: Status ---")
    try:
        resp = urllib.request.urlopen(f"{WORKER_URL}/api/get_state", timeout=5)
        state = json.loads(resp.read().decode())
        model = state.get("data", {}).get("model", {}).get("id", "unknown")
        msgs = state.get("data", {}).get("messageCount", 0)
        results["agent_state"] = {"model": model, "messages": msgs}
        print(f"  Model: {model}")
        print(f"  Messages: {msgs}")
    except Exception as e:
        results["agent_state"] = {"error": str(e)}
        print(f"  Error: {e}")

    # 3. Visual (placeholder — real SSIM check needs a baseline)
    print("\n--- Proving Ground: Visual (placeholder) ---")
    print("  SSIM check requires baseline reference frame")
    print("  Run: python -m core.sleepwalker run --beats regolith_yard")

    # Save report
    report_path = Path("chronicle") / "proving_ground_report.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[PROVING GROUND] Report: {report_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Gaussian Foundry — Autonomous Game Dev Pipeline")
    parser.add_argument("--council-only", action="store_true", help="Run only the dialectical Q&A cycle")
    parser.add_argument("--forge-only", type=str, default=None, help="Run only the workshop on a spec file")
    parser.add_argument("--bridge-only", action="store_true", help="Generate spec from latest chronicle only")
    parser.add_argument("--turns", type=int, default=2, help="Number of council turns")
    parser.add_argument("--port", type=int, default=8892, help="Worker bridge port")
    args = parser.parse_args()

    global WORKER_URL
    WORKER_URL = f"http://127.0.0.1:{args.port}"

    print(f"\n{'#'*60}")
    print(f"#  GAUSSIAN FOUNDRY — Autonomous AI Development System")
    print(f"#  Worker bridge: {WORKER_URL}")
    print(f"#  Chronicle:     {Path.cwd() / 'chronicle'}")
    print(f"#  Specs:         {Path.cwd() / 'specs'}")
    print(f"{'#'*60}\n")

    check_worker()

    if args.forge_only:
        # Forge-only mode
        spec_path = args.forge_only
        if not Path(spec_path).exists():
            print(f"[ERROR] Spec not found: {spec_path}")
            sys.exit(1)
        result = run_forge(spec_path)
        if result["success"]:
            run_proving_ground()
        sys.exit(0 if result["success"] else 1)

    if args.council_only:
        run_council(args.turns)
        sys.exit(0)

    if args.bridge_only:
        run_bridge()
        sys.exit(0)

    # Full pipeline
    run_council(args.turns)
    spec_path = run_bridge()
    result = run_forge(str(spec_path))
    if result["success"]:
        run_proving_ground()

    print(f"\n{'#'*60}")
    print(f"#  PIPELINE COMPLETE")
    if result["success"]:
        print(f"#  Council → Spec → Workshop → Proving Ground: ALL PASS")
    else:
        print(f"#  Failed at Workshop stage [{result['failed_at']}]")
        print(f"#  Reason: {result['failure_reason']}")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
