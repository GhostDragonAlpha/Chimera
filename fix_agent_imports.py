#!/usr/bin/env python3
"""Fix missing datetime imports in agent scripts."""

from pathlib import Path

def fix_file(filepath):
    """Add datetime import if missing."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"File not found: {filepath}")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if datetime is imported
    if "from datetime import datetime" in content:
        print(f"Already has datetime import: {filepath}")
        return True
    
    # Add import after existing imports
    lines = content.split('\n')
    
    # Find the first non-import line to insert before
    insert_index = 0
    for i, line in enumerate(lines):
        if not line.startswith('import ') and not line.startswith('from '):
            insert_index = i
            break
    
    # Insert datetime import
    lines.insert(insert_index, "from datetime import datetime")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Added datetime import to {filepath}")
    return True

def main():
    files_to_fix = [
        "agents/recombination_agent.py",
        "agents/integration_agent.py"
    ]
    
    for filepath in files_to_fix:
        fix_file(filepath)
    
    print("\nFixed all agent imports.")

if __name__ == "__main__":
    main()
