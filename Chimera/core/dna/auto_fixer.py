import re
from pathlib import Path
from core.game_code_generator import CppSyntaxValidator
from core.dna.mutation_logger import load_dna_graph, save_dna_graph, create_mutation_node, hash_error_signature

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

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
        
        mutation_node = create_mutation_node(
            error_signature=hash_error_signature(f"brace_mismatch_{file_path}"),
            template_file=template_file,
            template_line=brace_info.get("line", 0),
            error_category="brace_mismatch",
            fix_description="Auto-fixed unbalanced braces",
            fix_diff=fixed_content or "",
            compilation_result="pending_review"
        )
        
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        nodes.append(mutation_node)
        save_dna_graph({"nodes": nodes, "edges": edges})
        
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
