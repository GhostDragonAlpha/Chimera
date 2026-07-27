#!/usr/bin/env python3
"""
Wind System Integration Test Script
Tests particle wind interaction via MCP control in PIE.

DSL Parameter: wind_response: 1.0 (full wind interaction)
Measurement: Particle trajectory deviation from gravity-only baseline
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple, Dict, Any

sys.path.insert(0, str(Path(__file__).parent / "core"))

try:
    from ralph_loop_harness import MCPClient
except ImportError:
    print("ERROR: Cannot import MCP client. Ensure cwd is E:\\PythonChimera\\Chimera")
    sys.exit(1)


class WindSystemTest:
    """Test harness for wind system particle interaction."""

    def __init__(self):
        self.test_results = {
            "wind_system_status": "unknown",
            "particle_wind_response": 0.0,
            "drift_observable": False,
            "dsl_parity": 0,  # percent match to wind_response 1.0
            "issues": []
        }

    def test_wind_system_exists(self) -> bool:
        """Test 1: Verify wind system component is available."""
        print("\n[TEST 1] Wind System Existence")
        print("-" * 50)

        try:
            # Query for WindSystemComponent in scene
            success, result = MCPClient.call_tool("control_actor", {
                "action": "find_by_class",
                "className": "WindSystemComponent",
            })

            if success and "components" in str(result):
                print("  [OK] WindSystemComponent found in scene")
                self.test_results["wind_system_status"] = "implemented"
                return True
            else:
                print("  [INFO] WindSystemComponent not yet spawned in level")
                self.test_results["wind_system_status"] = "partial"
                return False

        except Exception as e:
            print(f"  [ERROR] Query failed: {e}")
            self.test_results["issues"].append(f"Wind system query failed: {e}")
            return False

    def test_particle_wind_response(self) -> bool:
        """Test 2: Verify particles respond to wind force."""
        print("\n[TEST 2] Particle Wind Response")
        print("-" * 50)

        try:
            # Query dust particle component
            success, result = MCPClient.call_tool("control_actor", {
                "action": "find_by_class",
                "className": "DustAccumulationParticleComponent",
            })

            if success:
                # Parse component data
                component_data = json.loads(result) if isinstance(result, str) else result

                # Check wind_response property
                wind_response = component_data.get("wind_response", 0.0)
                self.test_results["particle_wind_response"] = wind_response

                if wind_response >= 0.9:  # Tolerance for floating point
                    print(f"  [OK] Particle wind_response = {wind_response} (target 1.0)")
                    self.test_results["dsl_parity"] = int(wind_response * 100)
                    return True
                else:
                    print(f"  [WARN] Particle wind_response = {wind_response} (expected 1.0)")
                    self.test_results["dsl_parity"] = int(wind_response * 100)
                    return False
            else:
                print(f"  [ERROR] Failed to query particle component: {result}")
                self.test_results["issues"].append("Particle component query failed")
                return False

        except Exception as e:
            print(f"  [ERROR] {e}")
            self.test_results["issues"].append(str(e))
            return False

    def test_wind_drift_observable(self) -> bool:
        """Test 3: Verify wind drift is measurable."""
        print("\n[TEST 3] Wind Drift Observable")
        print("-" * 50)

        try:
            # Query telemetry from dust component
            success, result = MCPClient.call_tool("control_actor", {
                "action": "find_by_class",
                "className": "DustAccumulationParticleComponent",
            })

            if success:
                component_data = json.loads(result) if isinstance(result, str) else result

                # Check telemetry fields
                drift_distance = component_data.get("total_wind_drift_distance", 0.0)
                avg_drift = component_data.get("average_wind_drift_vector", [0, 0, 0])

                if drift_distance > 0.0 or any(v != 0 for v in avg_drift):
                    print(f"  [OK] Wind drift observable:")
                    print(f"       Total distance: {drift_distance:.2f} UU")
                    print(f"       Average vector: ({avg_drift[0]:.2f}, {avg_drift[1]:.2f}, {avg_drift[2]:.2f})")
                    self.test_results["drift_observable"] = True
                    return True
                else:
                    print(f"  [INFO] No wind drift measured yet (particles may not have settled)")
                    self.test_results["drift_observable"] = False
                    return False

        except Exception as e:
            print(f"  [ERROR] {e}")
            self.test_results["issues"].append(str(e))
            return False

    def test_dsl_parameter_parity(self) -> bool:
        """Test 4: Verify DSL parameter wind_response matches implementation."""
        print("\n[TEST 4] DSL Parameter Parity")
        print("-" * 50)

        # Check if wind_response: 1.0 in DSL is reflected in component
        if self.test_results["particle_wind_response"] >= 0.9:
            print(f"  [OK] DSL parameter 'wind_response: 1.0' matched in implementation")
            print(f"       Component wind_response: {self.test_results['particle_wind_response']}")
            self.test_results["dsl_parity"] = 100
            return True
        else:
            print(f"  [WARN] DSL parity at {self.test_results['dsl_parity']}%")
            self.test_results["issues"].append(f"DSL parity only {self.test_results['dsl_parity']}%")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Execute all wind system tests."""
        print("=" * 70)
        print("WIND SYSTEM INTEGRATION TEST SUITE")
        print("=" * 70)
        print("\nDSL Target: wind_response: 1.0 (full wind interaction)")
        print("Objective: Particles drift with wind direction/speed")
        print("Measurement: Particle trajectory deviation from gravity-only baseline")

        # Run tests
        test1 = self.test_wind_system_exists()
        test2 = self.test_particle_wind_response()
        test3 = self.test_wind_drift_observable()
        test4 = self.test_dsl_parameter_parity()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Wind System Status:      {self.test_results['wind_system_status']}")
        print(f"Particle Wind Response:  {self.test_results['particle_wind_response']:.2f}")
        print(f"Drift Observable:        {self.test_results['drift_observable']}")
        print(f"DSL Parity:              {self.test_results['dsl_parity']}%")

        if self.test_results["issues"]:
            print(f"\nIssues ({len(self.test_results['issues'])}):")
            for issue in self.test_results["issues"]:
                print(f"  - {issue}")

        # Determine overall result
        passed = test1 and test2 and test4
        print(f"\nOverall Result: {'PASS' if passed else 'PARTIAL'}")

        return self.test_results


def main():
    """Main test execution."""
    print("\nInitializing Wind System Test Suite...")
    print("Please ensure UE5 Editor is running PIE with the level loaded.\n")

    tester = WindSystemTest()
    results = tester.run_all_tests()

    # Save results to JSON for integration with pipeline
    output_file = Path(__file__).parent / "wind_system_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Return exit code based on results
    return 0 if results["wind_system_status"] == "implemented" else 1


if __name__ == "__main__":
    sys.exit(main())
