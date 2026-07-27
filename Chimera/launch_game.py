import subprocess
from pathlib import Path

# Launch UE5 editor command line
ue_cmd_path = Path("C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe")
uproject_path = Path("E:/PythonChimera/Chimera/Chimera.uproject")

cmd = [
    str(ue_cmd_path),
    str(uproject_path),
    "/Game/Levels/chimeradefaultlevel?Game=/Script/Chimera.DeepSpaceTraderGameMode",
    "-game",
    "-log",
    "-stdout",
    "-nosound",
    "-nodebugger",
    "-nopause",
    "-windowed",
    "-resx=800",
    "-resy=600"
]

print(f"Launching: {' '.join(cmd)}")
log_file = Path("ue5_launch_log.txt")

# Use subprocess to launch and capture output
p = subprocess.Popen(cmd, cwd="E:/PythonChimera/Chimera", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# Wait for completion or timeout
try:
    out, _ = p.communicate(timeout=90)
except subprocess.TimeoutExpired:
    p.kill()
    out = p.stdout.read() if p.stdout else ""

with open(log_file, 'w', encoding='utf-8') as f:
    f.write(out)

# Search for SPAWNED or errors
spawned_found = "SPAWNED" in out
spawn_failed = "SPAWN FAILED" in out
errors_found = "Error:" in out or "Crash" in out

print("\n=== SEARCH RESULTS ===")
if spawned_found:
    print("FOUND: SPAWNED messages")
else:
    print("NOT FOUND: SPAWNED messages")

if spawn_failed:
    print("FOUND: SPAWN FAILED messages")
    
if errors_found:
    print("FOUND: Error or Crash messages")

# Extract relevant log lines
lines = out.split('\n')
relevant_lines = [l for l in lines if 'SPAWNED' in l or 'SPAWN FAILED' in l or 'Error:' in l or 'Crash' in l or 'PreExit Game' in l or 'BeginPlay' in l]

print("\n=== RELEVANT LOG LINES ===")
for line in relevant_lines[-30:]:  # Last 30 relevant lines
    print(line)
