"""
Two Pi agents conversing through a shared channel.
All output visible in this terminal.
"""
import subprocess, time, os
from pathlib import Path

HERE = Path("E:/PythonChimera/Chimera")
CHANNEL = HERE / "docs" / "CHANNEL.md"
PI = r"C:\Users\allen\node-portable\node-v22.23.1-win-x64\pi.CMD"

os.chdir(str(HERE))
CHANNEL.write_text("DYAD: Ready.\n")

print("\n=== TWO AGENTS CONVERSING ===\n")
print("DYAD reads channel, produces NEXT instruction.")
print("LEAD reads channel, executes instruction.")
print("Both outputs shown here. Ctrl+C to stop.\n")

turn = 0
try:
    while True:
        turn += 1
        print(f"\n--- TURN {turn} ---")
        
        # DYAD produces instruction
        channel = CHANNEL.read_text(encoding="utf-8", errors="replace")[-1500:]
        dp = f"CHANNEL:\n{channel}\n\nYou are DYAD. Read channel. What should LEAD do next? Start with NEXT:"
        
        r = subprocess.run(
            [PI, "--provider", "lmstudio", "--model", "unsloth/qwen3.6-35b-a3b",
             "--no-session", "-p", dp],
            capture_output=True, text=True, timeout=120)
        dyad = (r.stdout or "")[:600]
        print(f"\n[DYAD] {dyad[:200]}")
        CHANNEL.write_text(f"\n--- TURN {turn} ---\nDYAD: {dyad}\n")
        
        # LEAD executes
        channel = CHANNEL.read_text(encoding="utf-8", errors="replace")[-1500:]
        lp = f"CHANNEL:\n{channel}\n\nYou are LEAD. Full tools. Execute last instruction. End with RESULT:"
        
        r = subprocess.run(
            [PI, "--provider", "lmstudio", "--model", "unsloth/qwen3.6-35b-a3b",
             "--no-session", "-p", lp],
            capture_output=True, text=True, timeout=300)
        lead = (r.stdout or "")[:600]
        print(f"\n[LEAD] {lead[:200]}")
        CHANNEL.write_text(f"LEAD: {lead}\n")
        
        print(f"\n  -> Turn {turn} complete. Next in 5s...")
        time.sleep(5)

except KeyboardInterrupt:
    print(f"\n\nStopped after {turn} turns.")
