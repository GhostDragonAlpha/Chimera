#!/usr/bin/env python3
"""Replace old agent scripts with fixed versions."""

from pathlib import Path
import shutil

agents_dir = Path("agents")

# Backup old files
for name in ["recombination_agent", "integration_agent"]:
    old_file = agents_dir / f"{name}.py"
    backup = agents_dir / f"{name}_old.py"
    
    if old_file.exists():
        shutil.copy2(old_file, backup)
        print(f"Backed up {old_file} -> {backup}")

# Replace with fixed versions
fixed_files = [
    ("recombination_agent_fixed.py", "recombination_agent.py"),
    ("integration_agent_fixed.py", "integration_agent.py")
]

for fixed_name, target_name in fixed_files:
    source = Path("agents") / fixed_name
    target = agents_dir / target_name
    
    if source.exists():
        shutil.copy2(source, target)
        print(f"Replaced {target} with {fixed_name}")
    else:
        print(f"Fixed file not found: {source}")

print("\nAgent replacement complete!")
