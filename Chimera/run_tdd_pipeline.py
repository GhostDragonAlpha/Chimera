"""
Run TDD Test Suite through the 7-stage Chimera pipeline.
"""

import json
from pathlib import Path

# Import the orchestrator
try:
    from core.game_generation_orchestrator import GameGenerationOrchestrator
except ImportError:
    try:
        from game_generation_orchestrator import GameGenerationOrchestrator
    except ImportError:
        print("Error: Could not import GameGenerationOrchestrator")
        exit(1)


def load_dsl_specification(file_path: str) -> str:
    """Load DSL specification from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Run the TDD test suite through the 7-stage pipeline."""
    print("=" * 80)
    print("TDD Test Suite - 7-Stage Pipeline Execution")
    print("=" * 80)

    # Initialize orchestrator
    schema_path = Path(__file__).parent / "schema" / "dsl_game_schema.json"
    source_dir = Path(__file__).parent / "Source" / "TDDTestSuiteGameGenerated"
    content_dir = Path(__file__).parent / "Content" / "ProceduralGenerated_TDD"
    output_dir = Path(__file__).parent / "GeneratedProjects_TDD"

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

    # Load TDD DSL specification
    tdd_dsl_path = Path(__file__).parent / "tests" / "dsl_grammar" / "tdd_test_suite.chimera"
    print(f"\nLoading DSL specification from: {tdd_dsl_path}")
    dsl_content = load_dsl_specification(str(tdd_dsl_path))

    # Process DSL specification
    print("\n" + "=" * 80)
    print("Executing 7-Stage Pipeline")
    print("=" * 80)

    result = orchestrator.process_dsl_specification(
        dsl_content=dsl_content,
        project_name="TDDTestSuiteGame"
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
    else:
        print("\n" + "=" * 80)
        print("Pipeline Execution Failed!")
        print("=" * 80)
        print(f"Error: {result.get('error')}")

    print("\n" + "=" * 80)
    print("TDD Pipeline Execution Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
