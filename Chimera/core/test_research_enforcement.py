"""Dry-run validation for Research Mandate enforcement (Phase 3 Pipeline Integration).

Validates tier classification, subtask message builder, and documentation review checker.

Usage:
    cd E:/PythonChimera/Chimera && python -m core.test_research_enforcement
"""
import sys
from pathlib import Path

CHIMERA_DIR = Path(__file__).parent.parent


def main():
    print("=" * 70)
    print("Research Mandate Enforcement — Dry Run Validation")
    print("=" * 70)

    # Ensure imports work from Chimera/ directory
    sys.path.insert(0, str(CHIMERA_DIR))
    try:
        from core.research_enforcement import (
            classify_task_tier,
            build_subtask_message,
            check_documentation_review,
            get_research_compliance_score,
            MANDATORY_DOCS,
        )
    except ImportError:
        sys.path.insert(0, str(CHIMERA_DIR / "core"))
        from research_enforcement import (
            classify_task_tier,
            build_subtask_message,
            check_documentation_review,
            get_research_compliance_score,
            MANDATORY_DOCS,
        )

    passed = 0
    failed = 0

    # =====================================================================
    # Test 1: Tier Classification (10+ task types)
    # =====================================================================
    print("\n[Test 1] Tier Classification")
    test_cases = [
        ("Spawn actor with known path", "simple", 1, "pre-assessed simple"),
        # Note: "material" in description triggers tier-2 override even though "scalar parameter" is tier-1
        ("Set scalar parameter value on material", None, 2, "tier-2 indicator 'material' overrides tier-1"),
        ("Toggle visibility flag on component", None, 1, "tier-1 indicator: boolean flag"),
        # Note: "assets" alone doesn't match tier-1; "search_assets" needs underscore or exact match
        ("Search assets in /Game/Path", None, 2, "tier-2 default for unknown complexity"),
        ("Configure character movement speeds", None, 2, "tier-2 indicator: character movement"),
        ("Create weapon blueprint with PBR materials", None, 3, "tier-3 indicators: weapon blueprint + material"),
        ("Design novel interaction system from scratch", None, 3, "tier-3 indicators: new feature + design"),
        ("Implement environmental effect Niagara system", None, 3, "tier-3 indicator: environmental effect"),
        ("Create animation blueprint with state machine", None, 2, "tier-2 indicator: animation"),
        ("Setup widget layout in UMG canvas panel", None, 2, "tier-2 indicator: configure + setup"),
    ]

    for desc, complexity, expected_tier, reason in test_cases:
        tier = classify_task_tier(desc, complexity)
        status = "PASS" if tier == expected_tier else "FAIL"
        if status == "FAIL":
            failed += 1
        else:
            passed += 1
        print(f"  {status}: '{desc}' -> Tier {tier} (expected {expected_tier}) [{reason}]")

    # =====================================================================
    # Test 2: Subtask Message Builder
    # =====================================================================
    print("\n[Test 2] Subtask Message Builder")
    test_messages = [
        ("TestWeaponCreation", 2, "pathway_17_material_params", ["set_component_property_lies"]),
        ("NewFeatureDesign", 3, "", []),
        ("SimpleSpawnTask", 1, "pathway_01_spawn_actor", []),
    ]

    for task_name, tier, pathway, traps in test_messages:
        msg = build_subtask_message(task_name, tier, pathway, traps)
        lines = msg.split('\n')
        has_header = "RESEARCH_MANDATE_COMPLIANT" in msg
        has_tier = f"Tier: {tier}" in msg
        has_pathway = pathway or "none (new pathway)" in msg
        has_instructions = "EXECUTION_INSTRUCTIONS:" in msg

        all_checks = all([has_header, has_tier, has_instructions])
        status = "PASS" if all_checks else "FAIL"
        if status == "FAIL":
            failed += 1
        else:
            passed += 1
        print(f"  {status}: '{task_name}' (Tier {tier}) -> {len(lines)} lines, header={has_header}, tier={has_tier}")

    # =====================================================================
    # Test 3: Documentation Review Checker on 5 Mandatory Docs
    # =====================================================================
    print("\n[Test 3] Documentation Review Checker")
    doc_result = check_documentation_review("TestPipelineRun", "pipeline integration test")
    compliance_rate = doc_result.get("compliance_rate", 0.0)
    reviews = doc_result.get("reviews", {})

    # Check that all 5 mandatory docs are present in the result
    expected_docs = [d[0] for d in MANDATORY_DOCS]
    found_docs = list(reviews.keys())
    all_present = all(d in found_docs for d in expected_docs)

    status = "PASS" if all_present else "FAIL"
    if status == "FAIL":
        failed += 1
    else:
        passed += 1
    print(f"  {status}: All {len(expected_docs)} mandatory docs present")
    for doc in expected_docs:
        info = reviews.get(doc, {})
        reviewed = info.get("reviewed", False)
        purpose = info.get("purpose", "")[:50]
        print(f"    - {doc}: {'REVIEWED' if reviewed else 'NOT REVIEWED'} ({purpose})")

    # =====================================================================
    # Test 4: Compliance Score Calculation
    # =====================================================================
    print("\n[Test 4] Compliance Score Calculation")
    score = get_research_compliance_score()
    has_rs = "research_summaries_count" in score
    has_pa = "pathway_attempts_count" in score
    has_dr = "documentation_reviews_count" in score
    has_tier = "tier_distribution" in score

    all_keys = all([has_rs, has_pa, has_dr, has_tier])
    status = "PASS" if all_keys else "FAIL"
    if status == "FAIL":
        failed += 1
    else:
        passed += 1
    print(f"  {status}: Score keys present: rs={has_rs}, pa={has_pa}, dr={has_dr}, tier={has_tier}")
    for key, val in score.items():
        print(f"    - {key}: {val}")

    # =====================================================================
    # Summary
    # =====================================================================
    total = passed + failed
    print("\n" + "=" * 70)
    print(f"Dry Run Results: {passed}/{total} tests passed")
    if failed > 0:
        print(f"  FAILED: {failed} test(s)")
    else:
        print("  ALL TESTS PASSED")
    print("=" * 70)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
