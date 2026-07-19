"""pipeline_fixer.py — Auto-fix cascade compilation errors.

Runs the UE5 pipeline, parses errors, and auto-fixes missing declarations
in game_code_generator.py. Loops until the pipeline passes or hits an error
it can't fix.

Usage:
    cd E:\PythonChimera\Chimera
    python pipeline_fixer.py
"""

import re
import subprocess
import sys
import time

GENERATOR_PATH = "core/game_code_generator.py"
MAX_ITERATIONS = 30

def run_pipeline():
    """Run the pipeline and return stdout+stderr."""
    result = subprocess.run(
        [sys.executable, "run_deep_space_trader_pipeline.py"],
        capture_output=True, text=True, timeout=120, cwd="E:/PythonChimera/Chimera"
    )
    return result.stdout + result.stderr


def parse_undeclared_identifier(output):
    """Find the first undeclared identifier error.
    
    Pattern: error C2065: 'X': undeclared identifier
    Also: error C2039: 'X': is not a member of 'Y'
    """
    patterns = [
        r"error C2065:\s*'(\w+)':\s*undeclared identifier",
        r"error C2039:\s*'(\w+)':\s*is not a member",
    ]
    for pat in patterns:
        match = re.search(pat, output)
        if match:
            return match.group(1)
    return None


def parse_missing_function(output):
    """Find missing UFUNCTION declarations."""
    match = re.search(r"error C2039:\s*'(\w+)'", output)
    if match:
        return match.group(1)
    return None


def add_declaration_to_generator(identifier, context=""):
    """Add a declaration for the missing identifier to game_code_generator.py.
    
    Different identifier types need different declaration patterns.
    """
    with open(GENERATOR_PATH, "r") as f:
        content = f.read()
    
    # Common patterns for timer variable declarations
    timer_vars = {"RespirationTimer", "RepulsionResetTimer", "CurrentVelocity", 
                  "NextStormDay", "StormDuration", "GustTimer"}
    
    function_vars = {"OnRepulsionComplete", "OnStormEnd", "OnGustStart"}
    
    if identifier in timer_vars:
        # Add as UPROPERTY float declaration
        # Find a good insertion point — before the first UPROPERTY after the class definition
        insert_point = content.find("// Respiration cycle settings")
        if insert_point == -1:
            insert_point = content.find("// Current respiration phase")
        if insert_point == -1:
            insert_point = content.find("UPROPERTY(VisibleAnywhere, Category")
        
        if insert_point >= 0:
            decl = f"\n        /** Auto-fixed: {identifier} */\n        UPROPERTY()\n        float {identifier};\n"
            content = content[:insert_point] + decl + content[insert_point:]
            with open(GENERATOR_PATH, "w") as f:
                f.write(content)
            return True
    
    if identifier in function_vars:
        # Add as UFUNCTION declaration
        insert_point = content.find("// Respiration cycle settings")
        if insert_point >= 0:
            decl = f"\n        UFUNCTION()\n        void {identifier}();\n"
            content = content[:insert_point] + decl + content[insert_point:]
            with open(GENERATOR_PATH, "w") as f:
                f.write(content)
            return True
    
    # Unknown identifier — try generic fix
    # Look for the class definition and add before the first UPROPERTY
    class_match = re.search(r"class CHIMERA_API A\w+", content)
    if class_match:
        first_up = content.find("UPROPERTY", class_match.end())
        if first_up >= 0:
            decl = f"\n        /** Auto-fixed: {identifier} */\n        UPROPERTY()\n        float {identifier};\n"
            content = content[:first_up] + decl + content[first_up:]
            with open(GENERATOR_PATH, "w") as f:
                f.write(content)
            return True
    
    return False


def fix():
    """Main fix loop."""
    print("Pipeline cascade auto-fixer")
    print(f"Max iterations: {MAX_ITERATIONS}")
    print()
    
    for i in range(1, MAX_ITERATIONS + 1):
        print(f"\n=== Iteration {i} ===")
        print("Compiling...")
        
        try:
            output = run_pipeline()
        except subprocess.TimeoutExpired:
            print("  Compile timed out (120s). Continuing...")
            continue
        
        # Check if pipeline passed
        if "COMPLETE" in output and "BLOCKED" not in output:
            print("\n*** PIPELINE PASSED ***")
            print("All cascade errors fixed.")
            return True
        
        # Parse error
        identifier = parse_undeclared_identifier(output)
        if not identifier:
            identifier = parse_missing_function(output)
        
        if not identifier:
            print("  No recognizable error pattern.")
            print(f"  Last output: {output[-500:]}")
            return False
        
        print(f"  Error: undeclared identifier '{identifier}'")
        
        # Fix
        if add_declaration_to_generator(identifier):
            print(f"  Fixed: added declaration for '{identifier}'")
            time.sleep(1)  # Let file system settle
        else:
            print(f"  Could not auto-fix '{identifier}'")
            return False
        
        # Verify syntax
        import py_compile
        try:
            py_compile.compile(GENERATOR_PATH, doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  Generator syntax error after fix: {e}")
            return False
    
    print(f"Reached max iterations ({MAX_ITERATIONS}) without passing.")
    return False


if __name__ == "__main__":
    success = fix()
    sys.exit(0 if success else 1)
