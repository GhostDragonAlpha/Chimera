"""
Validation Test Suite — Verifies backward compatibility of all Chimera Python modules.

Tests each module independently without UE Editor dependencies where possible.
Reports pass/fail for each module and summarizes results.

Run from UE Python Console:
    from validation_test_suite import run_validation; run_validation()

Or standalone (simulation mode):
    python validation_test_suite.py
"""

import os
import sys


def validate_import(module_name, expected_classes=None, expected_functions=None):
    """Test that a module can be imported and has expected symbols.
    
    Args:
        module_name: Module name to import (e.g., 'play_test')
        expected_classes: List of class names to verify exist
        expected_functions: List of function names to verify exist
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        module = __import__(module_name, fromlist=[''])
        
        if expected_classes:
            for cls in expected_classes:
                if not hasattr(module, cls):
                    return False, f"Module '{module_name}' missing class '{cls}'"
        
        if expected_functions:
            for func in expected_functions:
                if not hasattr(module, func):
                    return False, f"Module '{module_name}' missing function '{func}'"
        
        return True, f"Module '{module_name}' imported successfully"
    
    except ImportError as e:
        return False, f"Failed to import '{module_name}': {e}"


def run_validation():
    """Execute complete validation test suite.
    
    Tests each module independently without UE Editor dependencies where possible.
    Reports pass/fail for each module and summarizes results.
    """
    print("=" * 70)
    print("CHIMERA PYTHON MODULE VALIDATION TEST SUITE")
    print("=" * 70)
    
    # Add Chimera/Python to sys.path if not already present
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    results = {}
    
    # Test 1: mcp_automation_client (new)
    success, msg = validate_import(
        'mcp_automation_client',
        expected_classes=['MCPTestClient'],
        expected_functions=['run_mcp_automated_test']
    )
    results['mcp_automation_client'] = {'success': success, 'message': msg}
    
    # Test 2: procedural_game_generator (existing)
    success, msg = validate_import(
        'procedural_game_generator',
        expected_classes=[],
        expected_functions=['generate_all', 'run_startup_workflow', 'sync_cpp_project_state']
    )
    results['procedural_game_generator'] = {'success': success, 'message': msg}
    
    # Test 3: play_test (existing)
    success, msg = validate_import(
        'play_test',
        expected_classes=['FlightPlayTest'],
        expected_functions=['run_playtest']
    )
    results['play_test'] = {'success': success, 'message': msg}
    
    # Test 4: runtime_screenshot_playtest (existing)
    success, msg = validate_import(
        'runtime_screenshot_playtest',
        expected_classes=['RuntimeScreenshotPlayTest'],
        expected_functions=['run_runtime_screenshot_playtest']
    )
    results['runtime_screenshot_playtest'] = {'success': success, 'message': msg}
    
    # Test 5: screenshot_lmstudio_workflow (existing)
    success, msg = validate_import(
        'screenshot_lmstudio_workflow',
        expected_classes=['LMStudioClient'],
        expected_functions=['run_screenshot_analysis_workflow', 'display_lmstudio_response']
    )
    results['screenshot_lmstudio_workflow'] = {'success': success, 'message': msg}
    
    # Test 6: unreal_api_operations (existing)
    success, msg = validate_import(
        'unreal_api_operations',
        expected_functions=['generate_levels_and_actors', 'create_procedural_level']
    )
    results['unreal_api_operations'] = {'success': success, 'message': msg}
    
    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    for module, result in results.items():
        status = "PASS" if result['success'] else "FAIL"
        print(f"  [{status}] {module}: {result['message']}")
    
    print(f"\n  Total: {passed}/{total} modules validated successfully")
    
    return results


if __name__ == "__main__":
    run_validation()
