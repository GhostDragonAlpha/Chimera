"""feature_graph.py — Feature development through graph-first questioning.

Every feature starts as questions in the graph. NO code until the graph
says the feature is fully designed. Construction is just materializing
already-answered questions.

Workflow:
1. Identify a feature (from the task board, spawn it as a node)
2. Ask ALL questions about it (across all categories)
3. Record each Q&A pair as a graph node
4. When all questions are answered, the feature is DESIGNED
5. Implement by referencing the graph nodes
6. The implementation PROVES the answers were correct
"""

import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional

FEATURES_DIR = Path("E:/PythonChimera/Chimera/docs/features")
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

# Category tree that grows with the project
# Node categories - what IS this thing
NODE_CATEGORIES = [
    "education",    # Does it teach real knowledge?
    "fame",         # Does it make the game desirable?
    "world",        # Does it feel real and alive?
    "shipping",     # Does it move toward release?
    "foundation",   # Does it strengthen the toolchain?
]

# Edge categories - how does it RELATE to other things
EDGE_CATEGORIES = [
    "depends_on",   # What must exist before this?
    "proves",       # What existing answer does this validate?
    "derived_from", # What question led to this?
    "conflicts",    # What existing design does this challenge?
    "requires",     # What skills, tools, or data are needed?
]


def create_feature(name: str, description: str = "") -> Dict:
    """Create a new feature node in the graph.
    
    A feature starts as a stub — just a name and description.
    Questions are added to it, not the other way around.
    """
    feature = {
        "name": name,
        "description": description,
        "created": datetime.datetime.now().isoformat(),
        "status": "questioning",  # questioning -> designed -> building -> verified
        "questions": [],
        "answers": [],
        "implementations": [],
    }
    
    path = FEATURES_DIR / f"{name.replace(' ', '_').replace('/', '_')}.json"
    path.write_text(json.dumps(feature, indent=2), encoding="utf-8")
    
    print(f"[GRAPH] Feature created: {name}")
    return feature


def load_feature(name: str) -> Optional[Dict]:
    """Load a feature from the graph."""
    path = FEATURES_DIR / f"{name.replace(' ', '_').replace('/', '_')}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def ask_question(feature_name: str, category: str, question: str, 
                   is_edge: bool = False) -> int:
    """Add a question to a feature.
    
    Questions are added before answers. A feature is not ready to build
    until all questions have answers.
    """
    feature = load_feature(feature_name)
    if not feature:
        feature = create_feature(feature_name)
    
    q_id = len(feature["questions"]) + 1
    feature["questions"].append({
        "id": q_id,
        "category": category,
        "question": question,
        "is_edge": is_edge,
        "answered": False,
        "answer": None,
    })
    
    _save_feature(feature)
    return q_id


def answer_question(feature_name: str, q_id: int, answer: str):
    """Record an answer to a question.
    
    When all questions are answered, the feature is designed.
    """
    feature = load_feature(feature_name)
    if not feature:
        return
    
    for q in feature["questions"]:
        if q["id"] == q_id:
            q["answered"] = True
            q["answer"] = answer
            break
    
    # Check if all questions are answered
    unanswered = [q for q in feature["questions"] if not q["answered"]]
    if not unanswered:
        feature["status"] = "designed"
        print(f"[GRAPH] Feature '{feature_name}' FULLY DESIGNED — ready to build.")
    else:
        print(f"[GRAPH] {len(unanswered)} questions remaining for '{feature_name}'.")
    
    _save_feature(feature)


def get_unanswered_questions(feature_name: str) -> List[Dict]:
    """Get all unanswered questions for a feature.
    
    These are the questions that need answers before construction.
    """
    feature = load_feature(feature_name)
    if not feature:
        return []
    return [q for q in feature["questions"] if not q["answered"]]


def feature_status(feature_name: str) -> str:
    """Get the design status of a feature."""
    feature = load_feature(feature_name)
    if not feature:
        return "not_started"
    
    total = len(feature["questions"])
    answered = len([q for q in feature["questions"] if q["answered"]])
    
    if total == 0:
        return "no_questions"
    
    if answered == total:
        return f"DESIGNED ({answered}/{total} questions answered)"
    
    return f"QUESTIONING ({answered}/{total} answered, {total - answered} remaining)"


def _save_feature(feature: Dict):
    """Save a feature back to disk."""
    path = FEATURES_DIR / f"{feature['name'].replace(' ', '_').replace('/', '_')}.json"
    path.write_text(json.dumps(feature, indent=2), encoding="utf-8")


def feature_report(feature_name: str) -> str:
    """Generate a full design report for a feature from the graph."""
    feature = load_feature(feature_name)
    if not feature:
        return f"Feature '{feature_name}' not found."
    
    lines = []
    lines.append(f"=== FEATURE: {feature['name']} ===")
    lines.append(f"Status: {feature['status']}")
    lines.append(f"Description: {feature['description']}")
    lines.append("")
    lines.append("--- Questions ---")
    
    for q in feature["questions"]:
        status = "✓" if q["answered"] else "○"
        lines.append(f"  [{status}] [{q['category']}] Q{q['id']}: {q['question']}")
        if q["answered"] and q["answer"]:
            lines.append(f"         A: {q['answer'][:200]}")
    
    lines.append("")
    lines.append(f"Total: {len(feature['questions'])} questions, "
                 f"{len([q for q in feature['questions'] if q['answered']])} answered")
    
    return "\n".join(lines)
