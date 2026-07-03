import hashlib
from datetime import datetime
from pathlib import Path

# Route through Graphify interface
try:
    from core.graphify_interface import query, mutate, load_dna_graph, save_dna_graph, hash_error_signature as _hash_err_sig
except ImportError:
    try:
        from graphify_interface import query, mutate, load_dna_graph, save_dna_graph, hash_error_signature as _hash_err_sig
    except ImportError:
        def query(*args, **kwargs): return None
        def mutate(*args, **kwargs): return "mutate_dummy"
        def load_dna_graph(): return {"nodes": [], "edges": []}
        def save_dna_graph(*args): pass
        def _hash_err_sig(*args, **kwargs): return "hash_dummy"

def hash_error_signature(error_message: str) -> str:
    return hashlib.sha256(error_message.encode('utf-8')).hexdigest()[:16]

def record_compilation_success(graph, snapshot_diff: str, template_file: str, template_line: int):
    result = mutate("compilation", "pass", details={"snapshot_diff": snapshot_diff, "template_file": template_file})
    return result or f"mutation_{hashlib.sha256(f'success_no_error_{template_file}_{template_line}'.encode()).hexdigest()[:12]}"

def record_compilation_failure(graph, ubt_output: str, template_file: str):
    error_signature = hash_error_signature(ubt_output)
    
    # Query existing errors through Graphify
    mutations = query("mutation", "compilation") or []
    
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    existing_errors = [n for n in nodes if n["type"] == "Error" and n.get("error_signature") == error_signature]
    
    error_node = None
    is_recurring = False
    
    if existing_errors:
        error_node = existing_errors[0]
        is_recurring = True
        error_node["is_recurring"] = True
        
        # Link to similar errors
        for n in nodes:
            if n["type"] == "Error" and n.get("id") != error_node["id"]:
                edges.append({
                    "source": error_node["id"],
                    "target": n["id"],
                    "type": "similar_error"
                })
    else:
        error_node = {
            "id": f"error_{error_signature}",
            "type": "Error",
            "timestamp": datetime.utcnow().isoformat(),
            "error_message": ubt_output,
            "error_signature": error_signature,
            "template_file": template_file,
            "is_recurring": False,
            "links": []
        }
        nodes.append(error_node)
        
    # Link Error to Template
    edges.append({
        "source": error_node["id"],
        "target": f"template_{hashlib.sha256(template_file.encode()).hexdigest()[:12]}",
        "type": "generated_from"
    })
    
    save_dna_graph({"nodes": nodes, "edges": edges})
    return error_node["id"]

def record_fix_applied(graph, error_id: str, template_file: str, fix_description: str, category: str):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    fix_node = {
        "id": f"fix_{hashlib.sha256(f'{error_id}_{template_file}'.encode()).hexdigest()[:12]}",
        "type": "Fix",
        "timestamp": datetime.utcnow().isoformat(),
        "error_id": error_id,
        "template_file": template_file,
        "fix_description": fix_description,
        "categories": [category],
        "links": []
    }
    nodes.append(fix_node)
    
    # Link Fix -> Error
    edges.append({
        "source": fix_node["id"],
        "target": error_id,
        "type": "fixes"
    })
    
    # Link Fix -> Template
    template_id = f"template_{hashlib.sha256(template_file.encode()).hexdigest()[:12]}"
    edges.append({
        "source": fix_node["id"],
        "target": template_id,
        "type": "applied_to_template"
    })
    
    save_dna_graph({"nodes": nodes, "edges": edges})
    return fix_node["id"]

def get_mutations_by_category(category: str) -> list:
    graph = load_dna_graph()
    fixes = [n for n in graph.get("nodes", []) if n["type"] == "Fix" and category in n.get("categories", [])]
    return fixes
