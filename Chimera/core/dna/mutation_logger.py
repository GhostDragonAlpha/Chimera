import json
import hashlib
from datetime import datetime
from pathlib import Path

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

def load_dna_graph():
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

def save_dna_graph(graph):
    DNA_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

def hash_error_signature(error_message: str) -> str:
    return hashlib.sha256(error_message.encode('utf-8')).hexdigest()[:16]

def create_mutation_node(error_signature: str, template_file: str, template_line: int, 
                         error_category: str, fix_description: str, fix_diff: str, 
                         compilation_result: str) -> dict:
    return {
        "id": f"mutation_{hashlib.sha256(f'{error_signature}_{template_file}_{template_line}'.encode()).hexdigest()[:12]}",
        "type": "Mutation",
        "timestamp": datetime.utcnow().isoformat(),
        "error_signature": error_signature,
        "template_file": template_file,
        "template_line": template_line,
        "error_category": error_category,
        "fix_description": fix_description,
        "fix_diff": fix_diff,
        "compilation_result": compilation_result,
        "links": []
    }

def create_error_node(error_message: str, template_file: str) -> dict:
    error_signature = hash_error_signature(error_message)
    return {
        "id": f"error_{error_signature}",
        "type": "Error",
        "timestamp": datetime.utcnow().isoformat(),
        "error_message": error_message,
        "error_signature": error_signature,
        "template_file": template_file,
        "is_recurring": False,
        "links": []
    }

def create_fix_node(error_id: str, template_file: str, fix_description: str) -> dict:
    return {
        "id": f"fix_{hashlib.sha256(f'{error_id}_{template_file}'.encode()).hexdigest()[:12]}",
        "type": "Fix",
        "timestamp": datetime.utcnow().isoformat(),
        "error_id": error_id,
        "template_file": template_file,
        "fix_description": fix_description,
        "categories": [],
        "links": []
    }

def record_compilation_success(graph, snapshot_diff: str, template_file: str, template_line: int):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    mutation_node = create_mutation_node(
        error_signature="success_no_error",
        template_file=template_file,
        template_line=template_line,
        error_category="none",
        fix_description=snapshot_diff or "no changes",
        fix_diff=snapshot_diff or "",
        compilation_result="pass"
    )
    
    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return mutation_node["id"]

def record_compilation_failure(graph, ubt_output: str, template_file: str):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    error_signature = hash_error_signature(ubt_output)
    
    existing_errors = [n for n in nodes if n["type"] == "Error" and n["error_signature"] == error_signature]
    
    error_node = None
    is_recurring = False
    
    if existing_errors:
        error_node = existing_errors[0]
        is_recurring = True
        error_node["is_recurring"] = True
        
        # Link to similar errors
        for n in nodes:
            if n["type"] == "Error" and n["id"] != error_node["id"]:
                edges.append({
                    "source": error_node["id"],
                    "target": n["id"],
                    "type": "similar_error"
                })
    else:
        error_node = create_error_node(ubt_output, template_file)
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
    
    fix_node = create_fix_node(error_id, template_file, fix_description)
    fix_node["categories"] = [category]
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
    
    # Link to Mutation if exists
    mutations = [n for n in nodes if n["type"] == "Mutation" and n.get("error_signature") == hash_error_signature(graph.get("nodes", []))]
    
    save_dna_graph({"nodes": nodes, "edges": edges})
    return fix_node["id"]

def get_mutations_by_category(category: str) -> list:
    graph = load_dna_graph()
    fixes = [n for n in graph.get("nodes", []) if n["type"] == "Fix" and category in n.get("categories", [])]
    return fixes
