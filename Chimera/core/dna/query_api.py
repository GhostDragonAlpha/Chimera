from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import json
from pathlib import Path
from core.dna.mutation_logger import load_dna_graph, get_mutations_by_category, save_dna_graph
from core.dna.pattern_validator import check_template_history

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

app = FastAPI(title="Chimera DNA Query API", version="1.0.0")

@app.get("/dna/errors")
def get_all_errors():
    graph = load_dna_graph()
    errors = [n for n in graph.get("nodes", []) if n["type"] == "Error"]
    return JSONResponse(content={"errors": errors})

@app.get("/dna/errors/{category}")
def get_errors_by_category(category: str):
    graph = load_dna_graph()
    fixes = get_mutations_by_category(category)
    
    # Extract error IDs from fixes
    edges = graph.get("edges", [])
    error_ids = [e["target"] for e in edges if e.get("type") == "fixes" and any(f["id"] == e["source"] for f in [n for n in graph.get("nodes", []) if n["type"] == "Fix" and category in n.get("categories", [])])]
    
    errors = [n for n in graph.get("nodes", []) if n["type"] == "Error" and n["id"] in error_ids]
    return JSONResponse(content={"category": category, "errors": errors})

@app.get("/dna/template/{template_name}/history")
def get_template_history(template_name: str):
    history = check_template_history(load_dna_graph(), template_name)
    return JSONResponse(content=history)

@app.get("/dna/verify/{template_name}")
def verify_template(template_name: str):
    from core.dna.pattern_validator import validate_template_before_generation, flag_known_bad_pattern
    graph = load_dna_graph()
    
    is_valid = validate_template_before_generation(graph, template_name)
    bad_pattern_flag = flag_known_bad_pattern(graph, template_name, "verification_check")
    
    return JSONResponse(content={
        "template_name": template_name,
        "is_valid": is_valid,
        "bad_pattern_detected": bad_pattern_flag["is_know_bad"]
    })

@app.post("/dna/mutation")
def record_mutation(mutation: dict):
    graph = load_dna_graph()
    nodes = graph.get("nodes", [])
    
    # Ensure mutation has required fields
    if "id" not in mutation or "type" not in mutation:
        raise HTTPException(status_code=400, detail="Invalid mutation format")
        
    nodes.append(mutation)
    save_dna_graph({"nodes": nodes, "edges": graph.get("edges", [])})
    
    return JSONResponse(content={"success": True, "mutation_id": mutation["id"]})

@app.get("/dna/health")
def get_system_health():
    graph = load_dna_graph()
    nodes = graph.get("nodes", [])
    
    health_nodes = [n for n in nodes if n["type"] == "Health"]
    mutations = [n for n in nodes if n["type"] == "Mutation"]
    errors = [n for n in nodes if n["type"] == "Error"]
    fixes = [n for n in nodes if n["type"] == "Fix"]
    
    # Calculate compilation success rate
    total_mutations = len(mutations)
    successful_compilations = sum(1 for m in mutations if m.get("compilation_result") == "pass")
    success_rate = (successful_compilations / total_mutations * 100) if total_mutations > 0 else 100.0
    
    # Get most recent health status
    latest_health = health_nodes[-1] if health_nodes else {"status": "unknown", "details": "No health checks recorded"}
    
    return JSONResponse(content={
        "health_status": latest_health.get("status", "unknown"),
        "total_mutations": total_mutations,
        "total_errors": len(errors),
        "total_fixes": len(fixes),
        "compilation_success_rate": success_rate,
        "latest_health_check": latest_health.get("timestamp")
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8766)
