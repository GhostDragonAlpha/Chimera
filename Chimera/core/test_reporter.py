"""
Test Reporter — Generates structured test reports mapping results back to DSL blocks.

Follows the same error-mapping pattern as build_validator.py, with failure
suggestions and statistical aggregation for balance tests.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .playtest_runner import PlaytestReport, TestResult


class TestReporter:
    """Generates test reports mapping results to DSL blocks with failure suggestions."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir) / "ValidationReports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, results: PlaytestReport, dsl_spec: dict) -> dict:
        """Generate a structured test report mapping results to DSL blocks."""
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "project": Path(results.project).stem if results.project else "UnknownProject",
            "summary": results.summary,
            "tests": [],
            "regression_check": {
                "previous_pass_rate": 1.0,
                "current_pass_rate": results.summary.get("pass_rate", 0.0),
                "new_failures": [],
                "resolved_failures": []
            }
        }

        new_failures = []

        for test_result in results.tests:
            test_report = {
                "name": test_result.test_name,
                "type": self._get_test_type_from_dsl(test_result.test_name, dsl_spec),
                "dsl_block": f"tests.{test_result.test_name}",
                "status": test_result.status,
                "duration_ms": test_result.duration_ms
            }

            if test_result.assertions:
                test_report["assertions"] = test_result.assertions

            if test_result.statistics:
                test_report["statistics"] = test_result.statistics
                # For balance tests with iterations, add pass_rate to statistics
                if "pass_rate" not in test_report["statistics"]:
                    passed_count = sum(1 for a in test_result.assertions if a.get("passed", False))
                    total_count = len(test_result.assertions) if test_result.assertions else 1
                    test_report["statistics"]["pass_rate"] = passed_count / total_count

            if test_result.suggestion:
                test_report["suggestion"] = test_result.suggestion

            report["tests"].append(test_report)

            if test_result.status == "FAILED":
                new_failures.append(test_result.test_name)

        report["regression_check"]["new_failures"] = new_failures

        # Write report to file
        timestamp_str = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        report_path = self.output_dir / f"test_report_{timestamp_str}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        return report

    def _get_test_type_from_dsl(self, test_name: str, dsl_spec: dict) -> str:
        """Extract test type from DSL specification."""
        tests_block = dsl_spec.get("tests", {})
        test_defs = tests_block.get("test_definitions", [])
        
        for td in test_defs:
            if td.get("name") == test_name:
                return td.get("type", "unit")
                
        return "unknown"

    def map_failure_to_dsl(self, test_name: str, failure_detail: str) -> Dict[str, Any]:
        """Map a test failure back to the DSL test block that defined it."""
        dsl_reference = {
            "test_name": test_name,
            "dsl_block": f"tests.{test_name}",
            "failure_detail": failure_detail,
            "suggested_fix": None
        }

        # Generate specific suggestions based on failure details
        if "health_percent" in failure_detail or "damage" in failure_detail.lower():
            dsl_reference["suggested_fix"] = "DSL gameplay.combat_system may need balance adjustments. Consider reducing enemy damage values or increasing player starting health attributes."
        elif "cooldown" in failure_detail.lower() and "seconds" in failure_detail:
            dsl_reference["suggested_fix"] = f"DSL gameplay.abilities.{test_name.replace('CooldownCorrect', '')} cooldown duration may need adjustment. Verify the GE_{test_name}_Cooldown effect duration matches expected values."
        elif "craft" in failure_detail.lower() or "consumes" in failure_detail.lower():
            dsl_reference["suggested_fix"] = "DSL gameplay.crafting_systems.recipes material consumption values may be incorrect. Verify input quantities match expected crafting costs."
        elif "biome" in failure_detail.lower() or "temperature" in failure_detail.lower():
            dsl_reference["suggested_fix"] = "DSL planet_generation_systems.biome_configs temperature parameters or status effect thresholds may need adjustment for the specified biome."

        return dsl_reference
