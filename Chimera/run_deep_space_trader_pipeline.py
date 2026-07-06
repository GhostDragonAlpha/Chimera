"""
Run Deep Space Trader game spec through the 7-stage Chimera pipeline.

MANDATORY GATES: If any stage gate fails, the pipeline exits with code 1.
The exit code propagates so CI/automation can detect failures.
"""

import json
import sys
from pathlib import Path

# Import the orchestrator
try:
    from core.game_generation_orchestrator import GameGenerationOrchestrator
    from core.gates import GateViolation, PRE_FLIGHT_GATES, POST_FLIGHT_GATES
except ImportError:
    try:
        from game_generation_orchestrator import GameGenerationOrchestrator
        from gates import GateViolation, PRE_FLIGHT_GATES, POST_FLIGHT_GATES
    except ImportError:
        print("Error: Could not import GameGenerationOrchestrator")
        sys.exit(1)


def load_dsl_specification(file_path: str) -> str:
    """Load DSL specification from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Run the Deep Space Trader game spec through the 7-stage pipeline.

    Returns exit code 0 on success, 1 on gate violation, 2 on other failure.
    """
    print("=" * 80)
    print("Deep Space Trader - 7-Stage Pipeline Execution")
    print("=" * 80)

    # Initialize orchestrator
    project_name = "DeepSpaceTrader"
    schema_path = Path(__file__).parent / "schema" / "dsl_game_schema.json"

    # Source directory for C++ files must be in the GeneratedProject/Source folder
    source_dir = Path(__file__).parent / "Source" / "Chimera"
    content_dir = Path(__file__).parent / "Content"
    output_dir = Path(__file__).parent

    print(f"\nInitializing orchestrator...")
    print(f"  Schema path: {schema_path}")
    print(f"  Source directory: {source_dir}")
    print(f"  Content directory: {content_dir}")
    print(f"  Output directory: {output_dir}")

    # Ensure directories exist
    source_dir.mkdir(parents=True, exist_ok=True)
    content_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    orchestrator = GameGenerationOrchestrator(
        schema_path=str(schema_path),
        source_dir=str(source_dir),
        content_dir=str(content_dir),
        output_dir=str(output_dir)
    )

    # Load Deep Space Trader DSL specification
    dsl_spec_path = Path(__file__).parent / "tests" / "dsl_grammar" / "deep_space_trader.chimera"
    print(f"\nLoading DSL specification from: {dsl_spec_path}")
    dsl_content = load_dsl_specification(str(dsl_spec_path))

    # Process DSL specification
    print("\n" + "=" * 80)
    print("Executing 7-Stage Pipeline")
    print("=" * 80)

    try:
        result = orchestrator.process_dsl_specification(
            dsl_content=dsl_content,
            project_name=project_name
        )

        if result.get("success"):
            print("\n" + "=" * 80)
            print("Pipeline Execution Complete!")
            print("=" * 80)
            print(f"Project Name: {result.get('project_name')}")
            print(f".uproject Path: {result.get('uproject_path')}")
            print(f"Validation Report: {result.get('validation_report_path')}")
            print(f"All Tests Passed: {result.get('all_tests_passed')}")
            print(f"Playtest Summary: {result.get('playtest_summary')}")
            print(f"Generated Assets Count: {result.get('generated_assets_count')}")
            print(f"Generated Files Count: {result.get('generated_files_count')}")
            return 0
        else:
            print("\n" + "=" * 80)
            print("Pipeline Execution Failed!")
            print("=" * 80)
            print(f"Error: {result.get('error')}")
            return 2

    except GateViolation as gv:
        # Hard gate failure — pipeline could not proceed past a mandatory checkpoint.
        # This is the alignment funnel: the gate caught us and refused to continue.
        print(f"\n{'=' * 80}")
        print(f"[GATE VIOLATION] Pipeline BLOCKED at gate: {gv.gate_name}")
        print(f"  Reason: {gv.reason}")
        if gv.remediation:
            print(f"  Remediation: {gv.remediation}")
        print(f"  Severity: {gv.severity}")
        print(f"{'=' * 80}")
        return 1

    except Exception as e:
        print(f"\n{'=' * 80}")
        print(f"Pipeline Execution Failed with unexpected error:")
        import traceback
        traceback.print_exc()
        print(f"{'=' * 80}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    print(f"\nExit code: {exit_code}")
    sys.exit(exit_code)
