"""
Code Generation Demo — Example usage of the Code Generation Orchestrator.

This script demonstrates how to use the CodeGenerationOrchestrator to:
1. Generate or repair C++ code based on natural language descriptions
2. Generate Blueprint design descriptions
3. Save generated code to files

Usage:
    python core/code_generation_demo.py
"""

import sys
from pathlib import Path

# Ensure UTF-8 encoding for stdout
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.code_generation_orchestrator import CodeGenerationOrchestrator


def run_demo():
    """Run a demonstration of the code generation orchestrator."""
    print("=" * 70)
    print("CODE GENERATION ORCHESTRATOR DEMO")
    print("=" * 70)

    # Initialize orchestrator
    orchestrator = CodeGenerationOrchestrator(project_root=str(project_root))

    print(f"\n[1] Orchestrator initialized with project root: {project_root}")
    print("-" * 70)

    # Demo prompt 1: C++ code repair (based on git history: fix broken Kenney cockpit mesh refs)
    cpp_prompt = "Fix broken Kenney cockpit mesh refs in ChimeraPilotPawn.cpp - remove broken references that cause CDO errors"
    
    print(f"\n[DEMO 1] Processing C++ code repair prompt:")
    print(f"  '{cpp_prompt}'\n")

    cpp_result = orchestrator.generate_cpp_code(
        prompt=cpp_prompt,
        file_path=project_root / "Source/Chimera/ChimeraPilotPawn.cpp",
        model_id='qwen3.6-35b-a3b-mtp@iq2_m',
        temperature=0.1,
        max_tokens=2048,
        timeout=180
    )

    if cpp_result.get("success"):
        print("[DEMO 1] C++ CODE GENERATION SUCCESS:")
        print(f"  Language: {cpp_result['language']}")
        print(f"  Filename Hint: {cpp_result['filename_hint']}")
        print(f"  Explanation: {cpp_result.get('explanation', 'N/A')[:100]}...")
        
        # Save generated code
        saved_file = orchestrator.save_generated_code(cpp_result, target_dir=str(project_root / "GeneratedCode"))
        print(f"  Saved to: {saved_file}")
    else:
        error_msg = str(cpp_result.get('error', 'Unknown error')).encode('utf-8', 'ignore').decode('utf-8')
        print(f"[DEMO 1] C++ CODE GENERATION FAILED:")
        print(f"  Error: {error_msg}")

    print("-" * 70)

    # Demo prompt 2: Blueprint design generation
    bp_prompt = "Design a Blueprint for a spaceship shield component with directional shields, recharge delay, absorption, and EMP disable functionality"
    
    print(f"\n[DEMO 2] Processing Blueprint design prompt:")
    print(f"  '{bp_prompt}'\n")

    bp_result = orchestrator.generate_blueprint_code(
        prompt=bp_prompt,
        model_id='qwen3.6-35b-a3b-mtp@iq2_m',
        temperature=0.1,
        max_tokens=2048,
        timeout=180
    )

    if bp_result.get("success"):
        print("[DEMO 2] BLUEPRINT DESIGN GENERATION SUCCESS:")
        print(f"  Language: {bp_result['language']}")
        print(f"  Filename Hint: {bp_result['filename_hint']}")
        print(f"  Explanation: {bp_result.get('explanation', 'N/A')[:100]}...")
        
        # Save generated code
        saved_file = orchestrator.save_generated_code(bp_result, target_dir=str(project_root / "GeneratedCode"))
        print(f"  Saved to: {saved_file}")
    else:
        error_msg = str(bp_result.get('error', 'Unknown error')).encode('utf-8', 'ignore').decode('utf-8')
        print(f"[DEMO 2] BLUEPRINT DESIGN GENERATION FAILED:")
        print(f"  Error: {error_msg}")

    print("-" * 70)
    print("\n[COMPLETED] Code generation demo finished.")
    print(f"Generated code files are available in: {project_root / 'GeneratedCode'}")


if __name__ == "__main__":
    run_demo()
