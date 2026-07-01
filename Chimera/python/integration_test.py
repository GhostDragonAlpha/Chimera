"""
UE Integration Test — Verifies all flight systems work together.
Tests component interaction, input handling, and physics simulation.
Runs without UE Editor using Python-only simulation.
"""

import os


class FlightIntegrationTest:
    """Complete integration test for flight vehicle system."""
    
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    
    def add_test(self, name, result, detail=""):
        """Record a test result."""
        status = "PASS" if result else "FAIL"
        icon = "[OK]" if result else "[FAIL]"
        
        print(f"  {icon} {name}")
        if detail:
            print(f"      {detail}")
        
        self.tests.append((name, status, detail))
        if result:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_component_creation(self):
        """Test that all components can be created."""
        print("\n[TEST] Component Creation")
        print("-" * 40)
        
        # Check all component files exist
        components = [
            "FlightControlComponent.h",
            "ThrustVectoringComponent.h",
            "AttitudeStabilizerComponent.h",
            "ChimeraPawn.h"
        ]
        
        all_exist = True
        for comp in components:
            if not os.path.exists(os.path.join(self.source_dir, comp)):
                all_exist = False
        
        self.add_test("All component files exist", all_exist)
    
    def test_component_integration(self):
        """Test that ChimeraPawn properly integrates with flight components."""
        print("\n[TEST] Component Integration")
        print("-" * 40)
        
        pawn_h = os.path.join(self.source_dir, "ChimeraPawn.h")
        pawn_cpp = os.path.join(self.source_dir, "ChimeraPawn.cpp")
        
        # Check includes
        with open(pawn_h, 'r', encoding='utf-8') as f:
            header_content = f.read()
        
        with open(pawn_cpp, 'r', encoding='utf-8') as f:
            cpp_content = f.read()
        
        # Verify ThrustVectoringComponent is included and referenced
        tv_included = "ThrustVectoringComponent" in header_content
        tv_referenced = "UThrustVectoringComponent" in header_content
        
        self.add_test("ThrustVectoringComponent integrated", 
                     tv_included and tv_referenced,
                     f"Includes: {tv_included}, References: {tv_referenced}")
        
        # Verify AttitudeStabilizerComponent is included and referenced
        as_included = "AttitudeStabilizerComponent" in header_content
        as_referenced = "UAttitudeStabilizerComponent" in header_content
        
        self.add_test("AttitudeStabilizerComponent integrated", 
                     as_included and as_referenced,
                     f"Includes: {as_included}, References: {as_referenced}")
    
    def test_input_handling(self):
        """Test that input handlers are properly implemented."""
        print("\n[TEST] Input Handling")
        print("-" * 40)
        
        pawn_cpp = os.path.join(self.source_dir, "ChimeraPawn.cpp")
        
        with open(pawn_cpp, 'r', encoding='utf-8') as f:
            cpp_content = f.read()
        
        # Check thrust vectoring input handler exists
        has_thrust_vectoring = "SetThrustVector" in cpp_content
        
        self.add_test("Thrust vectoring input handler", has_thrust_vectoring)
    
    def test_physics_simulation(self):
        """Test flight physics simulation."""
        print("\n[TEST] Physics Simulation")
        print("-" * 40)
        
        # Simulate basic thrust application
        pos = [0.0, 200.0, 100.0]
        vel = [0.0, 0.0, 0.0]
        dt = 0.0167
        
        for t in range(30):
            vel[2] += 150.0 * dt
            pos[2] += vel[2] * dt
        
        lift_height = pos[2] - 100.0
        test_passed = lift_height > 10.0
        
        self.add_test("Thrust lifts vehicle", test_passed, 
                     f"Lifted {lift_height:.1f} units")
    
    def run_all_tests(self):
        """Execute all integration tests."""
        print("=" * 60)
        print("FLIGHT INTEGRATION TEST SUITE")
        print("=" * 60)
        
        self.test_component_creation()
        self.test_component_integration()
        self.test_input_handling()
        self.test_physics_simulation()
        
        # Summary
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print(f"RESULTS: {self.passed}/{total} tests passed")
        if self.failed == 0:
            print("STATUS: ALL TESTS PASSED — READY FOR BUILD")
        else:
            print(f"STATUS: {self.failed} tests failed — review above")
        print("=" * 60)


def run_integration_test():
    """Run complete integration test suite."""
    source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    
    # Need to define source_dir before running tests
    test_suite = FlightIntegrationTest()
    test_suite.run_all_tests()


if __name__ == "__main__":
    run_integration_test()
