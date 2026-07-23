#!/usr/bin/env python3
"""Setup agent environment and fix common issues."""

from pathlib import Path
import os

def setup_environment():
    """Create necessary directories and fix imports."""
    
    # Create agent_logs directory
    logs_dir = Path("agent_logs")
    logs_dir.mkdir(exist_ok=True)
    print(f"Created {logs_dir} directory")
    
    # Fix datetime import in recombination_agent.py
    recomb_path = Path("agents/recombination_agent.py")
    if recomb_path.exists():
        with open(recomb_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "from datetime import datetime" not in content:
            # Add import at top
            lines = content.split('\n')
            lines.insert(0, "from datetime import datetime")
            with open(recomb_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print("Fixed datetime import in recombination_agent.py")
    
    # Fix datetime import in integration_agent.py
    integ_path = Path("agents/integration_agent.py")
    if integ_path.exists():
        with open(integ_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "from datetime import datetime" not in content:
            lines = content.split('\n')
            lines.insert(0, "from datetime import datetime")
            with open(integ_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print("Fixed datetime import in integration_agent.py")
    
    # Fix graphify_record command in documentation_agent.py
    doc_path = Path("agents/documentation_agent.py")
    if doc_path.exists():
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Change "in_progress" to "accepted" for observe command
        content = content.replace("--verdict \"in_progress\"", "--verdict accepted")
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed graphify_record command in documentation_agent.py")

def main():
    print("Setting up agent environment...")
    print("="*60)
    
    setup_environment()
    
    print("\nSetup complete!")
    print("Run 'python run_agents_sequential.py' to execute the workflow.")

if __name__ == "__main__":
    main()
