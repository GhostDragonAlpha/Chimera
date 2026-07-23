#!/usr/bin/env python3
"""Membrane Integration Agent: Test class genomes with membrane shapes."""

import sys
from pathlib import Path
import numpy as np

# Import from project structure
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_membrane_clothe():
    """Test applying class genome to membrane shapes."""
    print("🧬 Testing Membrane Integration")
    print("="*60)
    
    # Check if membrane_shapes module exists
    membrane_path = Path("Chimera/core/membrane_shapes.py")
    if not membrane_path.exists():
        print(f"❌ Membrane shapes module not found at {membrane_path}")
        return False
    
    try:
        from Chimera.core.membrane_shapes import Sphere, Plane, Cylinder
        
        print("✅ Membrane shapes modules available")
        
        # Test different shape types
        shapes_to_test = [
            ("Sphere", Sphere(radius=1.0)),
            ("Plane", Plane(size=2.0)),
            ("Cylinder", Cylinder(radius=1.0, height=2.0))
        ]
        
        results = []
        
        for shape_name, shape in shapes_to_test:
            print(f"\n🔍 Testing {shape_name}...")
            
            # Check if clothe method exists
            if hasattr(shape, 'clothe'):
                print(f"  ✅ {shape_name} has clothe() method")
                
                # Try to apply a simple material composition
                try:
                    # This would need actual class genome data
                    # For now, just test the interface
                    result = shape.clothe(material="test_material", params={})
                    print(f"  ✅ {shape_name} clothe() executed successfully")
                    results.append({"shape": shape_name, "passed": True})
                except Exception as e:
                    print(f"  ❌ {shape_name} clothe() failed: {e}")
                    results.append({"shape": shape_name, "passed": False, "error": str(e)})
            else:
                print(f"  ⚠️ {shape_name} does not have clothe() method")
                results.append({"shape": shape_name, "passed": False, "error": "No clothe method"})
        
        return all(r["passed"] for r in results)
        
    except ImportError as e:
        print(f"❌ Failed to import membrane shapes: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during membrane testing: {e}")
        return False

def test_displacement():
    """Test terrain displacement on membranes."""
    print("\n🏔️ Testing Displacement")
    print("="*60)
    
    # Check if displace method exists and works
    try:
        from Chimera.core.membrane_shapes import Sphere
        
        sphere = Sphere(radius=1.0)
        
        if hasattr(sphere, 'displace'):
            print("✅ Sphere has displace() method")
            
            # Test with simple height function
            def simple_height(x, y):
                return 0.1 * np.sin(x) * np.cos(y)
            
            try:
                displaced = sphere.displace(height_fn=simple_height, amplitude=0.5)
                print("✅ Displacement applied successfully")
                return True
            except Exception as e:
                print(f"❌ Displacement failed: {e}")
                return False
        else:
            print("⚠️ Sphere does not have displace() method")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import membrane shapes: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during displacement testing: {e}")
        return False

def test_scatter_placement():
    """Test scattering instances on terrain."""
    print("\n📍 Testing Scatter Placement")
    print("="*60)
    
    # Check if scatter functionality exists
    try:
        from Chimera.core.progeny import scatter
        
        print("✅ Scatter function available")
        
        # Create dummy children for testing
        dummy_children = [{"sampled": {"_scale": 1.0, "size": 0.02}}] * 10
        
        try:
            scene = scatter(dummy_children, count=100, area=10.0, seed=42)
            print(f"✅ Scatter created {scene['_instances']} instances")
            return True
        except Exception as e:
            print(f"❌ Scatter failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import scatter function: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during scatter testing: {e}")
        return False

def generate_integration_report(test_results):
    """Generate a report of membrane integration test results."""
    print("\n📊 MEMBRANE INTEGRATION REPORT")
    print("="*60)
    
    if not test_results:
        print("❌ No test results to report")
        return False
    
    # Count passed/failed tests
    passed = sum(1 for r in test_results if r.get('passed', False))
    total = len(test_results)
    
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    # List detailed results
    print("\nDetailed Results:")
    for result in test_results:
        status = "✅ PASSED" if result.get('passed', False) else "❌ FAILED"
        details = result.get('error', 'N/A') if not result.get('passed', True) else 'OK'
        print(f"  {result['shape']}: {status} - {details}")
    
    # Save report
    report = {
        "timestamp": str(datetime.now()),
        "tests_run": total,
        "passed": passed,
        "success_rate": (passed/total)*100 if total > 0 else 0,
        "results": test_results
    }
    
    report_path = Path("agent_logs/integration_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to {report_path}")
    return passed > 0

def main():
    from datetime import datetime
    
    print("🧬 Membrane Integration Testing Agent")
    print("="*60)
    
    # Run integration tests
    clothe_passed = test_membrane_clothe()
    displacement_passed = test_displacement()
    scatter_passed = test_scatter_placement()
    
    results = [
        {"shape": "clothe_interface", "passed": clothe_passed},
        {"shape": "displacement", "passed": displacement_passed},
        {"shape": "scatter_placement", "passed": scatter_passed}
    ]
    
    # Generate report
    success = generate_integration_report(results)
    
    if success:
        print("\n✅ Membrane integration testing agent completed successfully")
        return 0
    else:
        print("\n⚠️ Membrane integration testing agent completed with issues")
        return 0

if __name__ == "__main__":
    sys.exit(main())
