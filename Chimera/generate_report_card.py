import json
import hashlib
from datetime import datetime
from pathlib import Path

DNA_GRAPH_PATH = Path("docs/chimera_dna_graph.json")

def load_dna_graph():
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

def save_dna_graph(graph):
    DNA_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

dna_graph = load_dna_graph()
nodes = dna_graph.get("nodes", [])
edges = dna_graph.get("edges", [])

details = {
    "scope": "loops_0_through_6",
    "gpa": None,
    "total_graded_features": 0,
    "has_real_lm_studio_grades": False,
    "findings": "No ProfessorGrade nodes with verbatim lm_studio_raw responses from LM Studio were found in the DNA graph. The report card is empty until the measurements are real.",
    "recommendations": "Begin sending research summaries to LM Studio with the grading prompt for verified features across Loops 0-6. Record explicit ProfessorGrade nodes via g.mutate('professor_grade', {...}) with the lm_studio_raw field containing the full verbatim LM Studio response."
}

report_card_node = {
    "id": f"professor_report_card_{hashlib.sha256(f'{details["scope"]}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
    "type": "ProfessorReportCard",
    "timestamp": datetime.utcnow().isoformat(),
    "scope": details["scope"],
    "gpa": details["gpa"],
    "total_graded_features": details["total_graded_features"],
    "has_real_lm_studio_grades": details["has_real_lm_studio_grades"],
    "findings": details["findings"],
    "recommendations": details["recommendations"],
    "error_signature": "success_no_error",
    "template_file": f"professor_report_card/{details['scope']}",
    "error_category": "none",
    "fix_description": f"Professor report card recorded for {details['scope']}: {details['total_graded_features']} features graded, has_real_lm_studio_grades={details['has_real_lm_studio_grades']}",
    "compilation_result": "pass",
    "links": []
}

nodes.append(report_card_node)
save_dna_graph({"nodes": nodes, "edges": edges})
print("Report card mutation recorded successfully")
