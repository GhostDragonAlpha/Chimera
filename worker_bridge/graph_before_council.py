"""graph_before_council.py — Query the graph before the internal council.

Every cycle, before running the 7 gates, check if the questions have
already been answered in the graph. If a question's answer exists in
chronicle history or the knowledge graph, skip it — reference the
existing answer instead of re-asking.

This prevents redundant cycles and grows the graph as a living memory.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional

CHRONICLE_DIR = Path("E:/PythonChimera/worker_bridge/chronicle")
KNOWLEDGE_GRAPH = Path("E:/PythonChimera/Chimera/docs/chimera_knowledge_graph.json")


def search_chronicle(query: str) -> List[Dict]:
    """Search chronicle files for existing Q&A matching the query.
    
    Returns list of matching entries with their source file and content.
    """
    if not CHRONICLE_DIR.exists():
        return []
    
    results = []
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    for f in sorted(CHRONICLE_DIR.glob("*.txt")):
        content = f.read_text(encoding="utf-8")
        content_lower = content.lower()
        
        # Count word overlap
        content_words = set(content_lower.split())
        overlap = len(query_words & content_words)
        ratio = overlap / max(len(query_words), 1)
        
        if ratio > 0.15:  # 15% word overlap = likely relevant
            results.append({
                "file": f.name,
                "relevance": round(ratio, 3),
                "preview": content[:300],
            })
    
    return sorted(results, key=lambda r: r["relevance"], reverse=True)


def search_knowledge_graph(query: str) -> List[Dict]:
    """Search the knowledge graph for nodes matching the query.
    
    The knowledge graph has labeled nodes with community structure.
    """
    if not KNOWLEDGE_GRAPH.exists():
        return []
    
    try:
        graph = json.loads(KNOWLEDGE_GRAPH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception):
        return []
    
    results = []
    query_lower = query.lower()
    
    for node in graph.get("nodes", []):
        label = node.get("label", "").lower()
        if query_lower in label:
            results.append({
                "id": node.get("id", ""),
                "label": node.get("label", ""),
                "community": node.get("community"),
                "source": node.get("source_file", ""),
            })
    
    return results[:10]


def check_answered(category: str, question: str) -> Optional[str]:
    """Check if a question has already been answered.
    
    Returns the existing answer text if found, None if unanswered.
    """
    # 1. Search chronicle for matching Q&A
    chronicle_matches = search_chronicle(f"{category}: {question}")
    if chronicle_matches:
        best = chronicle_matches[0]
        if best["relevance"] > 0.3:  # Strong match
            return best["preview"]
    
    # 2. Search knowledge graph for relevant nodes
    kg_matches = search_knowledge_graph(question)
    if kg_matches:
        # If we find relevant nodes, note them but don't treat as answered
        # (the graph has code structure, not Q&A pairs)
        pass
    
    return None


def filter_questions(category_questions: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Filter out questions that have already been answered.
    
    Returns only unanswered questions, organized by category.
    """
    unanswered = {}
    
    for category, questions in category_questions.items():
        pending = []
        for q in questions:
            existing = check_answered(category, q)
            if existing:
                print(f"  [GRAPH] Already answered: {q[:60]}...")
            else:
                pending.append(q)
        
        if pending:
            unanswered[category] = pending
    
    return unanswered


def record_answer(category: str, question: str, answer: str):
    """Record a new Q&A pair to the chronicle.
    
    This grows the graph as a living memory for future cycles.
    """
    CHRONICLE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find the next turn number
    existing = list(CHRONICLE_DIR.glob("turn_*.txt"))
    turn_num = 1
    if existing:
        nums = []
        for f in existing:
            m = re.search(r"turn_(\d+)", f.name)
            if m:
                nums.append(int(m.group(1)))
        if nums:
            turn_num = max(nums) + 1
    
    # Write the Q&A pair
    q_file = CHRONICLE_DIR / f"turn_{turn_num:03d}_{category}_question.txt"
    a_file = CHRONICLE_DIR / f"turn_{turn_num:03d}_{category}_answer.txt"
    
    if not q_file.exists():
        q_file.write_text(question, encoding="utf-8")
    a_file.write_text(answer, encoding="utf-8")
    
    return turn_num
