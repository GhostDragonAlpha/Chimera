import subprocess
from pathlib import Path

# Run UBT compilation
ubt_path = Path("C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll")
uproject_path = Path("E:/PythonChimera/Chimera/Chimera.uproject")

cmd = [
    "dotnet",
    str(ubt_path),
    "Chimera",
    "Win64",
    "Development",
    f"-project=\"{uproject_path}\"",
    "-progress"
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, cwd="E:/PythonChimera/Chimera", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)

output = result.stdout if result.stdout else result.stderr
print("=== UBT OUTPUT ===")
print(output[-5000:] if len(output) > 5000 else output)

# Check for success or errors
if "Succeeded" in output or "Build succeeded" in output:
    print("\n=== BUILD SUCCEEDED ===")
else:
    print("\n=== BUILD FAILED OR IN PROGRESS ===")
