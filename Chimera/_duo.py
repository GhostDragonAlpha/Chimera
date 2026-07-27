"""
Two Pi agents. One loop. All output here.
"""
import subprocess, time
from pathlib import Path

HERE = Path("E:/PythonChimera/Chimera")
CHAN = HERE / "docs" / "CHANNEL.md"
CHAN.write_text("DYAD: Ready.\n")

CMDS = ["npx", "pi", "-p", "--provider", "lmstudio", "--no-session", "--model", "unsloth/qwen3.6-35b-a3b"]

def talk(agent, prompt):
    r = subprocess.run(CMDS + [prompt], capture_output=True, text=True, timeout=180, cwd=str(HERE))
    return (r.stdout or "")[:500]

turn = 0
try:
    while True:
        turn += 1
        print(f"\n=== TURN {turn} ===")
        
        d = talk("DYAD", f"CHANNEL:\n{CHAN.read_text()[-1000:]}\n\nYou are DYAD. What next? Start with NEXT:")
        print(f"\nDYAD: {d[:200]}")
        CHAN.write_text(f"\n--- TURN {turn} ---\nDYAD: {d}\n")
        
        l = talk("LEAD", f"CHANNEL:\n{CHAN.read_text()[-1000:]}\n\nYou are LEAD. Full tools. Execute. End with RESULT:")
        print(f"\nLEAD: {l[:200]}")
        CHAN.write_text(f"LEAD: {l}\n")
        
        subprocess.run(["python", "-m", "core.dyad", "report", l[:400]], capture_output=True, timeout=30)
        print(f"\n  [{turn}s] Next in 5s...")
        time.sleep(5)

except KeyboardInterrupt:
    print(f"\n\n{'-'*40}\nDone after {turn} turns.")
