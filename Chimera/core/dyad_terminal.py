"""
dyad_terminal — two Pi agents talking to each other through the brief.

  DYAD AGENT (deep model, LM Studio)  ←→  LEAD AGENT (tools, LM Studio)
       │                                        │
       └────────── brief (docs/BRIEF.md) ────────┘

The DYAD reads the project state and decides what to build next.
The LEAD executes with full tool access.
The brief carries context between turns.

They talk. You watch. Press Ctrl+C to stop.
"""
from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BRIEF_PATH = ROOT / "docs" / "BRIEF.md"

# Pi commands for each agent
PI_BASE = ["npx", "pi", "-p", "--provider", "lmstudio", "--no-session"]
DYAD_MODEL = "unsloth/qwen3.6-35b-a3b"   # FAST 35B for the dyad role
LEAD_MODEL = "unsloth/qwen3.6-35b-a3b"   # Same model for LEAD (has tools)

# But the DYAD's DEEP turn uses python -m core.council which handles model swap
# The DYAD agent just drives the dyad.drive() process

def call_pi(prompt: str, model: str = None, timeout: int = 180) -> str:
    """Call Pi CLI in non-interactive mode. Returns stdout."""
    cmd = PI_BASE + (["--model", model] if model else [])
    try:
        r = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True,
            timeout=timeout, cwd=str(ROOT))
        return (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"

def dyad_turn() -> str:
    """The DYAD agent reads the brief and produces a NEXT instruction."""
    brief = BRIEF_PATH.read_text(encoding="utf-8", errors="replace")[:2000] \
        if BRIEF_PATH.exists() else "No prior context."
    
    prompt = (
        f"You are the DYAD — a two-mind system that drives development.\n\n"
        f"CURRENT BRIEF:\n{brief}\n\n"
        f"Read the project state. Decide what to build next.\n"
        f"First, call: python -m core.dyad drive\n"
        f"This runs FAST (35B) + DEEP (27B) to produce an instruction.\n"
        f"Output the instruction starting with 'NEXT:'.\n"
        f"Be specific: name files, functions, tests, evidence."
    )
    
    print(f"\n{'─'*60}")
    print(f"  DYAD AGENT — reading brief, producing instruction")
    print(f"{'─'*60}")
    t0 = time.time()
    
    output = call_pi(prompt, model=DYAD_MODEL, timeout=120)
    elapsed = time.time() - t0
    
    print(f"  DYAD ({elapsed:.0f}s):")
    # Extract the key part
    for line in output.splitlines():
        if "NEXT:" in line or "instruction" in line.lower():
            print(f"    {line.strip()[:150]}")
    
    # Also run dyad.drive directly for the real instruction
    print(f"  Running dyad.drive()...")
    r = subprocess.run(
        ["python", "-m", "core.dyad", "drive"],
        capture_output=True, text=True, timeout=300,
        cwd=str(ROOT),
        env={**os.environ, "CHIMERA_FAST_MODEL": "unsloth/qwen3.6-35b-a3b",
             "CHIMERA_DEEP_MODEL": "qwen3.6-27b-mtp"})
    instruction = (r.stdout or "").strip()
    if not instruction:
        instruction = "[no instruction from dyad]"
    
    print(f"  DYAD INSTRUCTION: {instruction[:200]}")
    return instruction

def lead_turn(instruction: str) -> str:
    """The LEAD agent executes the instruction with full tools."""
    brief = BRIEF_PATH.read_text(encoding="utf-8", errors="replace")[:2000] \
        if BRIEF_PATH.exists() else ""
    
    prompt = (
        f"You are the LEAD developer. You have FULL TOOL ACCESS.\n"
        f"You can read files, edit code, run commands, use MCP.\n\n"
        f"CURRENT BRIEF:\n{brief}\n\n"
        f"YOUR INSTRUCTION:\n{instruction}\n\n"
        f"Execute this instruction. Read relevant files first, then make changes.\n"
        f"Run tests afterward. Report what you did and what you found.\n"
        f"End with 'RESULT:' followed by a summary of what was accomplished."
    )
    
    print(f"\n{'─'*60}")
    print(f"  LEAD AGENT — executing with full tools")
    print(f"{'─'*60}")
    t0 = time.time()
    
    output = call_pi(prompt, model=LEAD_MODEL, timeout=300)
    elapsed = time.time() - t0
    
    print(f"  LEAD ({elapsed:.0f}s):")
    for line in output.splitlines():
        if "RESULT:" in line:
            print(f"    {line.strip()[:200]}")
    
    # Extract result
    result = ""
    for line in output.splitlines():
        if line.strip().upper().startswith("RESULT:"):
            result = line.strip()[7:].strip()
            break
    if not result:
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        result = lines[-1][:200] if lines else "No output"
    
    # Report to brief
    subprocess.run(
        ["python", "-m", "core.dyad", "report", result[:600]],
        capture_output=True, timeout=30, cwd=str(ROOT))
    
    print(f"  -> Brief updated")
    return result

def main():
    print(f"\n{'#'*60}")
    print(f"#  TWO AGENTS, ONE CONVERSATION")
    print(f"#  DYAD (LM Studio) → LEAD (full tools)")
    print(f"#  Press Ctrl+C to stop")
    print(f"{'#'*60}\n")
    
    # Reset brief
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    BRIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    BRIEF_PATH.write_text(
        f"# DYAD - {ts}\n\n"
        f"The compositional world model pipeline is built:\n"
        f"- Big Bang → planets → climates → materialization → matter → splats → stress\n"
        f"- GPU shaker fixed, LOD merger built, stress mapper proven\n"
        f"- Gradient-to-emission probability function implemented\n"
        f"Next: the DYAD decides what to build.\n",
        encoding="utf-8")
    
    turn = 0
    try:
        while True:
            turn += 1
            print(f"\n{'='*60}")
            print(f"  CONVERSATION TURN {turn}")
            print(f"{'='*60}")
            
            # DYAD thinks
            instruction = dyad_turn()
            
            if not instruction or instruction == "[no instruction from dyad]":
                print("\n[DYAD has no direction. Pausing...]")
                time.sleep(5)
                continue
            
            # LEAD executes
            result = lead_turn(instruction)
            
            print(f"\n  >>> TURN {turn} COMPLETE <<<")
            print(f"  Next turn in 5 seconds...")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n{'='*60}")
        print(f"  CONVERSATION STOPPED after {turn} turns")
        print(f"{'='*60}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
