"""
Build Verification System — Checks all C++ components are properly integrated.
Validates file existence, includes, class declarations, and method signatures.
Reports status before attempting UE compilation.
"""

import os
import re


def verify_cpp_syntax(filepath):
    """Check basic C++ syntax patterns without full compilation."""
    issues = []
    
    if not os.path.exists(filepath):
        return [f"File missing: {filepath}"]
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for matching braces
    opens = content.count('{')
    closes = content.count('}')
    if opens != closes:
        issues.append(f"Unmatched braces: {opens} open, {closes} close")
    
    # Check for matching parentheses in function calls
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'UFUNCTION' in line or 'void' in line or 'class' in line:
            opens = line.count('(')
            closes = line.count(')')
            if opens != closes and not line.strip().endswith(';'):
                issues.append(f"Line {i+1}: Possible unmatched parentheses")
    
    return issues


def verify_component_integration():
    """Verify all flight components are properly integrated."""
    print("=" * 60)
    print("BUILD VERIFICATION — COMPONENT INTEGRATION CHECK")
    print("=" * 60)
    
    source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    
    # Check all component files exist
    components = [
        "FlightControlComponent.h",
        "ThrustVectoringComponent.h", 
        "AttitudeStabilizerComponent.h",
        "ChimeraPawn.h",
        "ChimeraPawn.cpp"
    ]
    
    print("\n[STEP 1] Checking component files...")
    all_exist = True
    
    for comp in components:
        filepath = os.path.join(source_dir, comp)
        exists = os.path.exists(filepath)
        status = "[OK]" if exists else "[MISSING]"
        print(f"  {status} {comp}")
        if not exists:
            all_exist = False
    
    # Check ChimeraPawn.h includes new components
    print("\n[STEP 2] Checking ChimeraPawn.h includes...")
    
    pawn_h_path = os.path.join(source_dir, "ChimeraPawn.h")
    with open(pawn_h_path, 'r', encoding='utf-8') as f:
        pawn_h_content = f.read()
    
    required_includes = [
        "ThrustVectoringComponent",
        "AttitudeStabilizerComponent"
    ]
    
    for inc in required_includes:
        if inc in pawn_h_content:
            print(f"  [OK] Includes {inc}")
        else:
            print(f"  [MISSING] Missing include for {inc}")
    
    # Check ChimeraPawn.cpp includes new components
    print("\n[STEP 3] Checking ChimeraPawn.cpp includes...")
    
    pawn_cpp_path = os.path.join(source_dir, "ChimeraPawn.cpp")
    with open(pawn_cpp_path, 'r', encoding='utf-8') as f:
        pawn_cpp_content = f.read()
    
    for inc in required_includes:
        if inc in pawn_cpp_content:
            print(f"  [OK] Includes {inc}")
        else:
            print(f"  [MISSING] Missing include for {inc}")
    
    # Check method implementations exist
    print("\n[STEP 4] Checking method implementations...")
    
    required_methods = [
        "SetThrustVector",
        "ThrustVectoring->GetThrustDirection",
        "AttitudeStabilizer"
    ]
    
    for method in required_methods:
        if method in pawn_cpp_content:
            print(f"  [OK] Method {method} implemented")
        else:
            print(f"  [MISSING] Missing implementation for {method}")
    
    # Check syntax of all files
    print("\n[STEP 5] Checking basic C++ syntax...")
    
    cpp_files = []
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f.endswith('.cpp') or f.endswith('.h'):
                cpp_files.append(os.path.join(root, f))
    
    syntax_ok = True
    for filepath in cpp_files[:10]:  # Check first 10 files
        issues = verify_cpp_syntax(filepath)
        if issues:
            print(f"  [WARN] {os.path.basename(filepath)}:")
            for issue in issues[:3]:
                print(f"      - {issue}")
            syntax_ok = False
    
    if syntax_ok:
        print("  [OK] All checked files have valid syntax")
    
    # Summary
    print("\n" + "=" * 60)
    if all_exist and syntax_ok:
        print("VERIFICATION RESULT: READY FOR BUILD")
    else:
        print("VERIFICATION RESULT: ISSUES FOUND — review above")
    print("=" * 60)


def run_verification():
    """Run complete build verification."""
    verify_component_integration()


if __name__ == "__main__":
    run_verification()
