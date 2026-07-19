"""
autonomous — self-running dyad loop with Pi CLI execution.

Architecture:
  1. DYAD (LM Studio 35B + 27B): reads brief, decides WHAT to do next
  2. Pi CLI: executes the instruction with full tool access (read, edit,
     bash, MCP to Unreal, graph queries, everything)
  3. Results reported back to brief
  4. Loop continues until Ctrl+C (or Escape in Pi)

Usage:
    python -m core.autonomous

Press Ctrl+C to stop. Watch the terminal for live output.
"""
from __future__ import annotations

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BRIEF_PATH = ROOT / "docs" / "BRIEF.md"

from core.dyad import build_project_context
from core.lm_gateway import evict_others

# --- find pi executable -----------------------------------------------------

def _find_pi() -> str:
    """Find the pi CLI executable."""
    # Check common locations
    candidates = [
        "npx.cmd pi",
        "npx pi",
        r"C:\Users\allen\AppData\Roaming\npm\pi.cmd",
        r"C:\Users\allen\AppData\Roaming\npm\node_modules\pi\bin\pi.js",
    ]
    for c in candidates:
        try:
            r = subprocess.run(c.split() + ["--version"], capture_output=True,
                               text=True, timeout=10)
            if r.returncode == 0:
                return c
        except Exception:
            continue
    # Try finding via node
    try:
        r = subprocess.run(
            ["node", "--eval",
             r"console.log(require.resolve('@earendil-works/pi-coding-agent/bin/pi.js'))"],
            capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return f"node {r.stdout.strip()}"
    except Exception:
        pass
    return "npx.cmd pi"  # best guess


# --- the loop ---------------------------------------------------------------

def run_cycle(turn: int, pi_cmd: str) -> str:
    """One autonomous cycle: DYAD decides, Pi CLI executes."""
    print(f"\n{'='*60}")
    print(f"  CYCLE {turn}")
    print(f"{'='*60}")

    # === STEP 1: DYAD decides what to do next ===
    print("\n[DYAD] Analyzing project state...")
    ctx = build_project_context()

    from core.dyad import drive
    instruction = drive(context=ctx)

    print(f"\n>>> DYAD INSTRUCTION: {instruction[:200]} <<<")

    if not instruction or len(instruction) < 10:
        print("[DYAD] No clear instruction — skipping this cycle.")
        return ""

    # === STEP 2: Spawn Pi CLI with the instruction ===
    print(f"\n[Pi] Executing with full tool access...")
    print(f"[Pi] Command: {instruction[:120]}...")

    # Build a prompt for Pi
    brief_text = BRIEF_PATH.read_text(encoding="utf-8", errors="replace")[:2000] \
        if BRIEF_PATH.exists() else "No prior context."

    prompt = (
        f"You are working on the Chimera project (E:/PythonChimera).\n\n"
        f"CURRENT BRIEF:\n{brief_text}\n\n"
        f"YOUR TASK:\n{instruction}\n\n"
        f"You have full tool access — read files, edit code, run commands, "
        f"use MCP to interact with Unreal Engine, query the DNA graph. "
        f"Do the work and report what you did and what you found. "
        f"Be thorough — read relevant files before editing, run tests after. "
        f"When done, summarize the results in a single paragraph starting with 'RESULT:'."
    )

    prompt_file = ROOT / f"_pi_prompt_turn{turn}.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    try:
        result = subprocess.run(
            pi_cmd.split() + ["-p", f"@{prompt_file}", "--no-session",
                              "--approve"],
            capture_output=True, text=True, timeout=300)
        output = result.stdout + result.stderr
        # Clean up the prompt file
        try:
            prompt_file.unlink()
        except Exception:
            pass
    except subprocess.TimeoutExpired:
        output = "[Pi] Timed out after 300s"
        print(f"  {output}")
    except Exception as e:
        output = f"[Pi] Error: {e}"
        print(f"  {output}")

    # === STEP 3: Report results ===
    from core.dyad import report

    # Extract RESULT: line from Pi output
    result_line = ""
    for line in output.splitlines():
        if line.strip().upper().startswith("RESULT:"):
            result_line = line.strip()[7:].strip()
            break
    if not result_line:
        # Fallback: last substantial lines
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        result_line = "\n".join(lines[-5:]) if lines else "No output captured"

    report(outcome=result_line[:600], context=output[:1000])

    print(f"\n  -> Result: {result_line[:150]}...")
    print(f"  -> Brief updated")
    return result_line


def main():
    pi_cmd = _find_pi()
    print(f"Pi CLI: {pi_cmd}")
    print(f"\n{'#'*60}")
    print(f"#  AUTONOMOUS DYAD LOOP")
    print(f"#  DYAD (LM Studio) decides WHAT")
    print(f"#  Pi CLI executes with full tools")
    print(f"#  Press Ctrl+C (Escape in Pi) to stop")
    print(f"{'#'*60}\n")

    evict_others(None)
    time.sleep(2)

    turn = 0
    try:
        while True:
            turn += 1
            run_cycle(turn, pi_cmd)
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n{'='*60}")
        print(f"  STOPPED after {turn} cycles")
        print(f"{'='*60}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
