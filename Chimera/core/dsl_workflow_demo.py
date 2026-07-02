"""
DSL Workflow Demo — Example usage of the DSL Workflow Orchestrator.

This script demonstrates how to use the DSLWorkflowOrchestrator to:
1. Process natural language prompts for term alignment
2. Generate validated DSL JSON via LM Studio
3. Output Unreal-compatible .json config files

Usage:
    python core/dsl_workflow_demo.py
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

from core.dsl_workflow_orchestrator import DSLWorkflowOrchestrator


def run_demo():
    """Run a demonstration of the DSL workflow orchestrator."""
    print("=" * 70)
    print("DSL WORKFLOW ORCHESTRATOR DEMO")
    print("=" * 70)

    # Initialize orchestrator with paths relative to Chimera project root
    registry_path = project_root / "registry" / "term_registry.json"
    schema_path = project_root / "schema" / "dsl_schema.json"
    output_dir = project_root / "Content" / "ProceduralGenerated" / "Workflows"

    print(f"\n[1] Loading Semantic Term Registry: {registry_path}")
    print(f"[2] Loading DSL Schema: {schema_path}")
    print(f"[3] Output Directory: {output_dir}")

    # Initialize the orchestrator
    orchestrator = DSLWorkflowOrchestrator(
        registry_path=str(registry_path),
        schema_path=str(schema_path),
        output_dir=str(output_dir)
    )

    print("\n[4] Orchestrator initialized successfully.")
    print("-" * 70)

    # Demo prompt 1: Simple term alignment
    prompt_1 = "Align Component Alpha with Data Processor and log the alignment with confidence score 0.85"
    
    print(f"\n[DEMO 1] Processing prompt:")
    print(f"  '{prompt_1}'\n")

    result_1 = orchestrator.process_prompt(
        natural_language_prompt=prompt_1,
        workflow_id="demo_workflow_alignment_001"
    )

    if result_1.get("success"):
        print("[DEMO 1] SUCCESS:")
        print(f"  Workflow ID: {result_1['workflow_id']}")
        print(f"  Output File: {result_1['workflow_file']}")
        print(f"  Steps Count: {result_1['steps_count']}")
    else:
        error_msg = str(result_1.get('error', 'Unknown error')).encode('utf-8', 'ignore').decode('utf-8')
        print(f"[DEMO 1] FAILED:")
        print(f"  Error: {error_msg}")

    print("-" * 70)

    # Demo prompt 2: Conditional branch logic
    prompt_2 = "If Data Processor matches Output Logger with condition context_overlap > 0.75, then log alignment"
    
    print(f"\n[DEMO 2] Processing prompt:")
    print(f"  '{prompt_2}'\n")

    result_2 = orchestrator.process_prompt(
        natural_language_prompt=prompt_2,
        workflow_id="demo_workflow_conditional_002"
    )

    if result_2.get("success"):
        print("[DEMO 2] SUCCESS:")
        print(f"  Workflow ID: {result_2['workflow_id']}")
        print(f"  Output File: {result_2['workflow_file']}")
        print(f"  Steps Count: {result_2['steps_count']}")
    else:
        error_msg = str(result_2.get('error', 'Unknown error')).encode('utf-8', 'ignore').decode('utf-8')
        print(f"[DEMO 2] FAILED:")
        print(f"  Error: {error_msg}")

    print("-" * 70)
    print("\n[COMPLETED] DSL workflow demo finished.")
    print(f"Generated config files are available in: {output_dir}")


if __name__ == "__main__":
    run_demo()
