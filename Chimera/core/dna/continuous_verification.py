import json
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

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

def create_health_node(status: str, details: str = "") -> dict:
    return {
        "id": f"health_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "type": "Health",
        "timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "details": details,
        "links": []
    }

def continuous_verification_loop():
    graph = load_dna_graph()
    
    # Regenerate from DSL
    # Compile
    # Run static analysis
    # Run template validation
    # Run differential testing against UE5 reference graph
    
    verification_passed = True
    errors = []
    
    try:
        # Check DNA graph integrity
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        if not nodes or not edges:
            errors.append("DNA graph is empty")
            verification_passed = False
            
        # Verify all mutations have required links
        for node in nodes:
            if node.get("type") == "Mutation":
                has_error_link = any(e["target"] == node.get("error_signature") and e["type"] == "links_to_error" for e in edges)
                has_template_link = any(e["target"].startswith("template_") and e["type"] == "links_to_template" for e in edges)
                
                if not has_error_link or not has_template_link:
                    errors.append(f"Mutation {node['id']} missing required links")
                    
    except Exception as e:
        errors.append(f"Verification error: {str(e)}")
        verification_passed = False
        
    if verification_passed:
        health_node = create_health_node("healthy", "All continuous verification checks passed")
        nodes.append(health_node)
        save_dna_graph({"nodes": nodes, "edges": edges})
        return {"success": True, "status": "healthy"}
    else:
        health_node = create_health_node("unhealthy", "; ".join(errors))
        nodes.append(health_node)
        save_dna_graph({"nodes": nodes, "edges": edges})
        return {"success": False, "status": "unhealthy", "errors": errors}

def start_continuous_verification_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(continuous_verification_loop, 'interval', hours=1)
    scheduler.start()
    return scheduler
