import json
import hashlib
from pathlib import Path

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

def load_dna_graph():
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

def hash_template_name(template_name: str) -> str:
    return hashlib.sha256(template_name.encode('utf-8')).hexdigest()[:16]

def check_template_history(graph, template_file: str) -> dict:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    template_id = f"template_{hashlib.sha256(template_file.encode()).hexdigest()[:12]}"
    
    # Find errors linked to this template
    template_errors = []
    for edge in edges:
        if edge.get("target") == template_id and edge.get("type") == "generated_from":
            error_node_id = edge.get("source")
            error_node = next((n for n in nodes if n["id"] == error_node_id and n["type"] == "Error"), None)
            if error_node:
                template_errors.append(error_node)
                
    # Find fixes linked to this template
    template_fixes = []
    for edge in edges:
        if edge.get("target") == template_id and edge.get("type") == "applied_to_template":
            fix_node_id = edge.get("source")
            fix_node = next((n for n in nodes if n["id"] == fix_node_id and n["type"] == "Fix"), None)
            if fix_node:
                template_fixes.append(fix_node)
                
    has_unresolved_errors = False
    for error in template_errors:
        # Check if there's a fix for this error
        fix_found = False
        for edge in edges:
            if edge.get("target") == error["id"] and edge.get("type") == "fixes":
                fix_node_id = edge.get("source")
                if any(f["id"] == fix_node_id for f in template_fixes):
                    fix_found = True
                    break
        
        if not fix_found or error.get("is_recurring", False):
            has_unresolved_errors = True
            break
            
    return {
        "template_file": template_file,
        "has_errors_before": len(template_errors) > 0,
        "error_count": len(template_errors),
        "fix_count": len(template_fixes),
        "unresolved_patterns": has_unresolved_errors,
        "errors": [e.get("error_signature") for e in template_errors],
        "applied_fixes": [f["fix_description"] for f in template_fixes]
    }

def validate_template_before_generation(graph, template_file: str) -> bool:
    history = check_template_history(graph, template_file)
    
    if history["unresolved_patterns"]:
        return False
        
    return True

def flag_known_bad_pattern(graph, template_file: str, error_message: str) -> dict:
    history = check_template_history(graph, template_file)
    
    return {
        "is_know_bad": history["has_errors_before"],
        "template_file": template_file,
        "error_signature": hashlib.sha256(error_message.encode('utf-8')).hexdigest()[:16],
        "previous_errors": history["errors"],
        "applied_fixes": history["applied_fixes"]
    }
