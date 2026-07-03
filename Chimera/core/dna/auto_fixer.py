import re
from pathlib import Path

# Route through Graphify interface
try:
    from core.graphify_interface import query, mutate, load_dna_graph, save_dna_graph
except ImportError:
    try:
        from graphify_interface import query, mutate, load_dna_graph, save_dna_graph
    except ImportError:
        def query(*args, **kwargs): return None
        def mutate(*args, **kwargs): return "mutate_dummy"
        def load_dna_graph(): return {"nodes": [], "edges": []}
        def save_dna_graph(*args): pass

from core.game_code_generator import CppSyntaxValidator
import hashlib

def find_unbalanced_braces(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {"has_error": False, "line": 0}
        
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    if open_braces != close_braces:
        # Find the line with unbalanced brace
        lines = content.split('\n')
        brace_count = 0
        error_line = 0
        
        for i, line in enumerate(lines):
            brace_count += line.count('{') - line.count('}')
            if brace_count < 0:
                error_line = i + 1
                break
                
        if brace_count > 0:
            # Missing closing braces at the end
            error_line = len(lines)
            
        return {
            "has_error": True,
            "open_braces": open_braces,
            "close_braces": close_braces,
            "line": error_line,
            "missing_closing": brace_count > 0
        }
        
    return {"has_error": False}

def attempt_brace_fix(file_path: str) -> tuple[bool, str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False, "Failed to read file"
        
    lines = content.split('\n')
    brace_count = 0
    
    # Count braces
    for line in lines:
        brace_count += line.count('{') - line.count('}')
        
    if brace_count > 0:
        # Try to add missing closing braces at the end of the file or class
        fix_applied = False
        
        # Look for the last class/struct definition
        for i in range(len(lines)-1, -1, -1):
            line = lines[i]
            if 'class ' in line or 'struct ' in line or 'UCLASS()' in line:
                # Find the matching closing brace position
                fix_line = i + 1
                while fix_line < len(lines) and not lines[fix_line].strip().endswith('};'):
                    fix_line += 1
                    
                if fix_line >= len(lines):
                    # Add closing braces at the end
                    for _ in range(brace_count):
                        lines.append('}')
                else:
                    # Insert before the };
                    indent = '    '
                    for _ in range(brace_count - 1):
                        lines.insert(fix_line, indent)
                        
                fix_applied = True
                break
                
        if fix_applied:
            fixed_content = '\n'.join(lines)
            
            # Validate the fix
            is_valid, errors = CppSyntaxValidator.validate_cpp_file(file_path + "_fixed.cpp")
            
            # Write fixed content to validate
            try:
                with open(file_path + "_fixed.cpp", 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                    
                is_valid, errors = CppSyntaxValidator.validate_cpp_file(file_path + "_fixed.cpp")
                
                if is_valid:
                    # Apply fix to original file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                        
                    return True, fixed_content
                else:
                    Path(file_path + "_fixed.cpp").unlink(missing_ok=True)
            except Exception:
                pass
                
    return False, "Fix validation failed"

def auto_fix_brace_error(file_path: str, template_file: str) -> dict:
    brace_info = find_unbalanced_braces(file_path)
    
    if not brace_info["has_error"]:
        return {"fixed": False, "reason": "No unbalanced braces found"}
        
    fix_success, fixed_content = attempt_brace_fix(file_path)
    
    if fix_success:
        graph = load_dna_graph()
        
        error_signature = hashlib.sha256(f"brace_mismatch_{file_path}".encode('utf-8')).hexdigest()[:16]
        
        mutation_node = {
            "id": f"mutation_{hashlib.sha256(f'success_no_error_{template_file}_{brace_info.get("line", 0)}'.encode()).hexdigest()[:12]}",
            "type": "Mutation",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
            "error_signature": error_signature,
            "template_file": template_file,
            "template_line": brace_info.get("line", 0),
            "error_category": "brace_mismatch",
            "fix_description": "Auto-fixed unbalanced braces",
            "fix_diff": fixed_content or "",
            "compilation_result": "pending_review",
            "links": []
        }
        
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        nodes.append(mutation_node)
        save_dna_graph({"nodes": nodes, "edges": edges})
        
        mutate("generation", "pass", details={"fix_description": "Auto-fixed unbalanced braces", "file_path": file_path})
        
        return {
            "fixed": True,
            "reason": "Brace error auto-fixed and mutation recorded for review",
            "line": brace_info.get("line", 0),
            "mutation_id": mutation_node["id"]
        }
    else:
        return {
            "fixed": False,
            "reason": "Auto-fix validation failed"
        }
