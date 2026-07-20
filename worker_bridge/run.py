#!/usr/bin/env python3
"""
run.py — Gaussian Foundry End-to-End Orchestrator

Chains four stages into one command:
  1. COUNCIL       — Two-model dialectical Q&A (core/council.py)
  2. BRIDGE        — Extract spec_manifest.json from the council transcript
  3. WORKSHOP      — Writer → Builder → Reviewer → Beats (forge.py)
  4. PROVING GROUND — Final status, git diff summary, verdict

Usage:
  # Full pipeline
  python run.py --topic "Implement a day/night cycle" --turns 2

  # Individual stages
  python run.py --council-only --topic "Design the shelter system" --turns 2
  python run.py --bridge-only chronicle/council_turn_001.txt
  python run.py --forge-only specs/spec_manifest.json

Requirements:
  - Worker bridge running: python -m uvicorn main:app --host 127.0.0.1 --port 8888
  - LM Studio with models loaded (CHIMERA_FAST_MODEL + CHIMERA_DEEP_MODEL, or one resident)
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
HERE = Path(__file__).parent.resolve()
CHRONICLE_DIR = HERE / "chronicle"
SPECS_DIR = HERE / "specs"
WORKER_URL = os.environ.get("CHIMERA_WORKER_URL", "http://127.0.0.1:8888")
CHIMERA_DIR = Path(os.environ.get("CHIMERA_DIR", "E:/PythonChimera/Chimera"))

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _bold(text: str) -> str:
    """ANSI bold if stdout is a terminal."""
    if sys.stdout.isatty():
        return f"\033[1m{text}\033[0m"
    return text


def _header(title: str):
    print(f"\n{_bold('=' * 60)}")
    print(_bold(f"  {title}"))
    print(f"{_bold('=' * 60)}\n", flush=True)


def _ok(msg: str):
    print(f"  \033[32m✓\033[0m {msg}", flush=True)


def _fail(msg: str):
    print(f"  \033[31m✗\033[0m {msg}", flush=True)


def _info(msg: str):
    print(f"  → {msg}", flush=True)


def _worker_alive() -> bool:
    """Check if the worker bridge is running."""
    try:
        resp = urllib.request.urlopen(f"{WORKER_URL}/api/status", timeout=5)
        data = json.loads(resp.read().decode())
        return data.get("status") == "running"
    except Exception:
        return False


def _worker_prompt(message: str, timeout: int = 600) -> str:
    """Send a prompt to the worker bridge and wait for the response."""
    body = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        f"{WORKER_URL}/api/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        json.loads(r.read().decode())  # ack — response comes async

    # Poll get_state until streaming is done
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(f"{WORKER_URL}/api/get_state", timeout=5)
            state = json.loads(resp.read().decode())
            if not state.get("data", {}).get("isStreaming", True):
                break
        except Exception:
            pass
        time.sleep(3)

    # Read the last assistant message
    try:
        resp = urllib.request.urlopen(f"{WORKER_URL}/api/get_messages", timeout=5)
        msgs = json.loads(resp.read().decode())
        messages = msgs.get("data", {}).get("messages", [])
        for m in reversed(messages):
            if m.get("role") == "assistant" and m.get("content"):
                text = m["content"]
                if isinstance(text, list):
                    parts = [seg.get("text", "") for seg in text if seg.get("type") == "text"]
                    return "".join(parts)
                return text
    except Exception:
        pass
    return ""


# ─── Stage 1: Council ────────────────────────────────────────────────────────

def _run_council(topic: str, rounds: int = 2, record: bool = True) -> Path:
    """Run the two-model council. Returns path to the transcript file."""
    _header("STAGE 1: COUNCIL (dialectical Q&A)")

    CHRONICLE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_path = CHRONICLE_DIR / f"council_{ts}.txt"

    _info(f"Topic: {topic}")
    _info(f"Rounds: {rounds}")
    _info(f"Transcript: {transcript_path.name}")

    cmd = [
        sys.executable, "-m", "core.council", topic,
        "--rounds", str(rounds),
    ]
    if record:
        cmd.append("--record")

    _info("Launching council (this may take 5-15 minutes)...")
    t0 = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(CHIMERA_DIR),
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min max
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    except subprocess.TimeoutExpired:
        _fail("Council timed out after 30 minutes")
        return None

    elapsed = time.time() - t0

    # Write transcript
    transcript = f"# Council Transcript — {ts}\n"
    transcript += f"# Topic: {topic}\n"
    transcript += f"# Rounds: {rounds}\n"
    transcript += f"# Duration: {elapsed:.0f}s\n\n"
    transcript += result.stdout
    if result.stderr:
        transcript += f"\n\n# STDERR:\n{result.stderr}"

    transcript_path.write_text(transcript, encoding="utf-8")

    if result.returncode == 0:
        _ok(f"Council complete ({elapsed:.0f}s)")
    else:
        _fail(f"Council exited with code {result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}", file=sys.stderr)

    return transcript_path


# ─── Stage 2: Bridge ─────────────────────────────────────────────────────────

def _extract_spec(transcript_path: Path) -> Path:
    """Send the council transcript to the worker bridge, ask it to extract a
    spec_manifest.json identifying target files and concrete edits."""
    _header("STAGE 2: BRIDGE (spec extraction)")

    if not _worker_alive():
        _fail("Worker bridge not running — start with: python -m uvicorn main:app --host 127.0.0.1 --port 8888")
        return None

    transcript_text = transcript_path.read_text(encoding="utf-8")

    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    spec_path = SPECS_DIR / f"spec_{ts}.json"

    prompt = f"""You are the BRIDGE agent in the Gaussian Foundry system.

Below is a council transcript — a two-model dialectical Q&A about a design problem.
Your job: extract a concrete, machine-readable implementation spec from it.

COUNCIL TRANSCRIPT:
```
{transcript_text[:12000]}
```

Produce a JSON spec with these fields:
- "title": short feature name
- "task_id": "forge_{ts}"
- "design_rationale": what was decided and why (2-4 sentences)
- "target_files": list of file paths that need changes (full paths from E:/PythonChimera/)
- "edit_plan": list of objects, each with:
    "file": path to the file
    "line_range": approximate lines (e.g. "45-60")
    "what": clear description of the change to make
- "test_strategy": which beats file to run (e.g. "docs/beats/regolith_yard.beats.json")

Rules:
- Only include files that actually exist or are clearly NEW files to create
- Be specific and concrete — the Writer agent will execute these exact edits
- If the council reached no concrete conclusion, emit an empty edit_plan and note it in design_rationale
- Return ONLY the JSON, no other text

BEGIN JSON:
{{"""

    _info("Sending transcript to worker bridge for spec extraction...")
    response = _worker_prompt(prompt)
    
    if not response:
        _fail("No response from worker bridge")
        return None

    # Extract JSON from response
    json_text = response
    # Try to find JSON block
    import re
    m = re.search(r'\{.*\}', response, re.DOTALL)
    if m:
        json_text = m.group(0)
    else:
        # Try wrapping
        json_text = "{" + response.split("{", 1)[-1] if "{" in response else response

    # Parse and validate
    try:
        spec = json.loads(json_text)
    except json.JSONDecodeError:
        _fail("Could not parse spec JSON from bridge response")
        # Save raw response for debugging
        raw_path = SPECS_DIR / f"spec_{ts}_raw.txt"
        raw_path.write_text(response, encoding="utf-8")
        _info(f"Raw response saved to {raw_path}")
        return None

    # Ensure required fields
    spec.setdefault("task_id", f"forge_{ts}")
    spec.setdefault("title", "Untitled")
    spec.setdefault("target_files", [])
    spec.setdefault("edit_plan", [])
    spec.setdefault("design_rationale", "")
    spec.setdefault("test_strategy", "docs/beats/regolith_yard.beats.json")

    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    _ok(f"Spec extracted: {len(spec.get('edit_plan', []))} edits across "
        f"{len(spec.get('target_files', []))} files")
    _info(f"Spec: {spec_path.name}")

    if not spec.get("edit_plan"):
        _info("WARNING: Empty edit plan — forge will be a no-op")

    return spec_path


# ─── Stage 3: Workshop ───────────────────────────────────────────────────────

def _run_forge(spec_path: Path) -> dict:
    """Run the Workshop pipeline (Writer → Builder → Reviewer → Beats)."""
    _header("STAGE 3: WORKSHOP (Writer → Builder → Reviewer → Beats)")

    if not _worker_alive():
        _fail("Worker bridge not running — forge requires the bridge")
        return {"success": False, "failed_at": "pre-flight", "failure_reason": "Worker bridge not running"}

    _info(f"Spec: {spec_path}")

    # Import and run forge directly
    sys.path.insert(0, str(HERE))
    try:
        from forge import run_forge
        result = run_forge(str(spec_path))
    except Exception as e:
        _fail(f"Forge crashed: {e}")
        return {"success": False, "failed_at": "forge", "failure_reason": str(e)}

    if result.get("success"):
        _ok("Workshop complete — all stages passed")
    else:
        _fail(f"Workshop failed at [{result.get('failed_at', 'unknown')}]")
        print(f"    Reason: {result.get('failure_reason', 'unknown')}")

    return result


# ─── Stage 4: Proving Ground ─────────────────────────────────────────────────

def _proving_ground(workshop_result: dict = None) -> bool:
    """Final status check and verdict."""
    _header("STAGE 4: PROVING GROUND (evaluation)")

    # Git diff summary
    _info("Changes made:")
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=str(Path("E:/PythonChimera")),
            capture_output=True, text=True, timeout=30,
        )
        if diff_result.stdout.strip():
            print(diff_result.stdout)
        else:
            print("  (no changes)")
    except Exception as e:
        print(f"  Could not get diff: {e}")

    # Summary
    stages = {}
    if workshop_result:
        stages = workshop_result.get("stages", {})

    print(f"\n{_bold('Pipeline Summary:')}")
    print(f"  Council  : {'✓' if True else '✗'}")  # reached this point = passed
    print(f"  Bridge   : {'✓' if True else '✗'}")
    print(f"  Writer   : {'✓' if stages.get('writer', {}).get('pass') else '✗'}")
    print(f"  Builder  : {'✓' if stages.get('builder', {}).get('pass') else '✗'}")
    print(f"  Reviewer : {'✓' if stages.get('reviewer', {}).get('pass') else '✗'}")
    print(f"  Beats    : {'✓' if stages.get('beats', {}).get('pass') else '✗'}")

    success = workshop_result.get("success", False) if workshop_result else True
    if success:
        print(f"\n{_bold('VERDICT: PASS')} — pipeline complete")
    else:
        failed_at = workshop_result.get("failed_at", "unknown") if workshop_result else "unknown"
        print(f"\n{_bold(f'VERDICT: FAIL at [{failed_at}]')} — see chronicle/forge_*.log for details")

    return success


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gaussian Foundry — End-to-End Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --topic "Implement a day/night cycle" --turns 2
  python run.py --council-only --topic "Design the shelter system"
  python run.py --bridge-only chronicle/council_20260720_120000.txt
  python run.py --forge-only specs/spec_manifest.json
        """,
    )
    parser.add_argument(
        "--topic", type=str,
        help="Design problem or feature to discuss in the council",
    )
    parser.add_argument(
        "--turns", type=int, default=2,
        help="Number of council dialogue rounds (default: 2)",
    )
    parser.add_argument(
        "--no-record", action="store_true",
        help="Do not record the council synthesis to CAPCOM/DNA graph",
    )
    parser.add_argument(
        "--council-only", action="store_true",
        help="Run only the council stage (save transcript, exit)",
    )
    parser.add_argument(
        "--bridge-only", type=str, metavar="TRANSCRIPT",
        help="Run only the bridge stage from a transcript file",
    )
    parser.add_argument(
        "--forge-only", type=str, metavar="SPEC",
        help="Run only the workshop stage from a spec file",
    )
    parser.add_argument(
        "--skip-council", action="store_true",
        help="Skip the council stage (use existing transcript)",
    )

    args = parser.parse_args()

    # ── Mode dispatch ────────────────────────────────────────────────────────

    # Council-only
    if args.council_only:
        if not args.topic:
            print("ERROR: --council-only requires --topic", file=sys.stderr)
            sys.exit(1)
        path = _run_council(args.topic, args.turns, record=not args.no_record)
        if path:
            _ok(f"Transcript saved: {path}")
            sys.exit(0)
        else:
            sys.exit(1)

    # Bridge-only
    if args.bridge_only:
        transcript = Path(args.bridge_only)
        if not transcript.exists():
            print(f"ERROR: Transcript not found: {transcript}", file=sys.stderr)
            sys.exit(1)
        spec_path = _extract_spec(transcript)
        if spec_path:
            _ok(f"Spec saved: {spec_path}")
            sys.exit(0)
        else:
            sys.exit(1)

    # Forge-only
    if args.forge_only:
        spec = Path(args.forge_only)
        if not spec.exists():
            print(f"ERROR: Spec not found: {spec}", file=sys.stderr)
            sys.exit(1)
        result = _run_forge(spec)
        sys.exit(0 if result.get("success") else 1)

    # ── Full pipeline ────────────────────────────────────────────────────────

    if not args.topic:
        print("ERROR: --topic is required for the full pipeline", file=sys.stderr)
        sys.exit(1)

    print(_bold("GAUSSIAN FOUNDRY — END-TO-END PIPELINE"))
    print(f"  Topic: {args.topic}")
    print(f"  Turns: {args.turns}")
    print(f"  Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Logs:  {CHRONICLE_DIR}")

    t0 = time.time()

    # 1. Council
    transcript = _run_council(args.topic, args.turns, record=not args.no_record)
    if not transcript:
        print("\nPipeline halted: council failed.", file=sys.stderr)
        sys.exit(1)

    # 2. Bridge
    spec = _extract_spec(transcript)
    if not spec:
        print("\nPipeline halted: bridge failed.", file=sys.stderr)
        sys.exit(1)

    # 3. Workshop
    result = _run_forge(spec)

    # 4. Proving Ground
    success = _proving_ground(result)

    elapsed = time.time() - t0
    print(f"\n{_bold(f'Total time: {elapsed:.0f}s ({elapsed/60:.1f}m)')}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
