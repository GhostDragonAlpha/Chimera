#!/usr/bin/env python3
"""
council_to_forge.py — Bridge between Council (dialectic) and Workshop (forge).

Reads the latest chronicle entries and extracts a spec_manifest.json
that the forge can execute.  This is the automation that closes the loop:
  Council talks → spec emerges → Workshop builds → Proving Ground tests
"""

import json
import re
from pathlib import Path

CHRONICLE_DIR = Path(__file__).parent / "chronicle"
SPEC_DIR = Path(__file__).parent / "specs"
SPEC_DIR.mkdir(exist_ok=True)


def find_latest_turn() -> int:
    """Find the highest turn number in the chronicle."""
    turns = set()
    for p in CHRONICLE_DIR.iterdir():
        if p.suffix == ".txt":
            m = re.match(r"turn_(\d+)_", p.stem)
            if m:
                turns.add(int(m.group(1)))
    return max(turns) if turns else 0


def read_chronicle(turn: int, phase: str) -> str:
    """Read a specific chronicle entry."""
    path = CHRONICLE_DIR / f"turn_{turn:03d}_{phase}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def extract_implementation_targets(chronicle_text: str) -> list[dict]:
    """Parse chronicle text for actionable implementation targets.
    
    Looks for patterns like:
    - "the fix is to change X in file.py"
    - "add Y to path/to/file.py"
    - "modify lines 42-67"
    """
    known_project_files = {
        "splat_emit.py", "splat_gpu.py", "bake.py", "fractal_zoom_sweep.py",
        "council.py", "ds4_brain.py", "lm_gateway.py", "preflight.py",
        "postflight.py", "matter_gpu.py", "expectation_violator.py",
        "onboarding_audit.py", "autonomous.py", "dyad.py",
        "claude.md", "MASTER_ONBOARDING.md", "TASK_BOARD.md",
        "HISTORY_BOOK.md", "PENDING_HEURISTICS.md", "envelope.json",
        "chimera_dna_graph.json",
    }
    targets = []
    
    # Pattern: file paths
    file_patterns = re.findall(
        r'(?:in|to|at)\s+([\w./\\]+\.(?:py|cpp|h|json))',
        chronicle_text,
        re.IGNORECASE,
    )
    
    # Pattern: "lines X-Y" or "line X"
    line_patterns = re.findall(r'lines?\s+(\d+)(?:\s*[-–to]+\s*(\d+))?', chronicle_text)
    
    # Pattern: "change X to Y"
    change_patterns = re.findall(
        r'(?:change|replace|modify|fix|add|implement)\s+([^.]{10,100})',
        chronicle_text,
        re.IGNORECASE,
    )

    # Pattern: specific file + line references with "edit", "change"
    edit_patterns = re.findall(
        r'edit[:\s]+(\S+\.\w+)(?:\s+lines?\s*(\d+)(?:\s*[-–to]+\s*(\d+))?)?',
        chronicle_text,
        re.IGNORECASE,
    )

    for match in edit_patterns:
        file_path = match[0]
        start_line = int(match[1]) if match[1] else None
        end_line = int(match[2]) if match[2] else None
        targets.append({
            "file": file_path,
            "line_range": [start_line, end_line] if start_line else None,
            "source": "edit_pattern",
        })

    for fp in file_patterns:
        # Normalize path
        fp = fp.replace("\\", "/")
        if not any(t["file"] == fp for t in targets):
            targets.append({
                "file": fp,
                "line_range": None,
                "source": "file_pattern",
            })

    return targets
    # Pattern: known project files mentioned anywhere in the text
    for kf in known_project_files:
        if kf in chronicle_text:
            if not any(t["file"] == kf for t in targets):
                targets.append({
                    "file": kf,
                    "line_range": None,
                    "source": "known_project_file",
                })



def extract_questions(text: str) -> list[str]:
    """Extract questions from chronicle text."""
    questions = []
    for line in text.split("\n"):
        line = line.strip()
        if re.match(r'^Q\d+[\.\)]\s', line) or re.match(r'^\d+[\.\)]\s.*\?', line):
            questions.append(line)
    return questions


def extract_answers(text: str) -> list[str]:
    """Extract numbered answers from chronicle text."""
    answers = []
    for line in text.split("\n"):
        line = line.strip()
        if re.match(r'^\*\*\d+\.', line) or re.match(r'^\d+\.\s*\*\*', line):
            answers.append(line)
    return answers


def guess_change_type(text: str) -> str:
    """Guess the change type from context."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["bug", "fix", "error", "issue", "incorrect"]):
        return "fix"
    if any(w in text_lower for w in ["refactor", "reorganize", "rename", "restructure"]):
        return "refactor"
    if any(w in text_lower for w in ["perf", "performance", "faster", "optimize", "bottleneck"]):
        return "perf"
    if any(w in text_lower for w in ["add", "implement", "new", "create", "introduce"]):
        return "feature"
    return "feature"


def build_spec(turn: int = None) -> dict:
    """Build a spec_manifest.json from the latest chronicle entries."""
    if turn is None:
        turn = find_latest_turn()

    # Read both phases
    worker_q = read_chronicle(turn, "worker_questions")
    main_a = read_chronicle(turn, "main_answers")
    main_q = read_chronicle(turn, "main_questions")
    worker_a = read_chronicle(turn, "worker_answers")

    all_text = f"{worker_q}\n{main_a}\n{main_q}\n{worker_a}"

    # Extract targets
    targets = extract_implementation_targets(all_text)
    questions = extract_questions(worker_q) + extract_questions(main_q)

    # Find the most substantive answer for rationale
    rationale_sources = [main_a, worker_a]
    rationale = ""
    for src in rationale_sources:
        if len(src) > len(rationale):
            rationale = src[:2000]  # trim for spec length

    # Build the spec
    spec = {
        "spec_version": "1.0.0",
        "task_id": f"tb-generated-{turn:03d}",
        "title": f"Implementation targets from dialectical turn {turn}",
        "target_files": list(set(t["file"] for t in targets if t["file"])),
        "change_type": guess_change_type(all_text),
        "design_rationale": (
            f"Derived from dialectical turn {turn}.\n"
            f"Questions asked: {len(questions)}\n"
            f"Implementation targets identified: {len(targets)}\n\n"
            f"Key rationale:\n{rationale[:3000]}"
        ),
        "rejected_alternatives": [
            "Alternatives were discussed in the Council cycle and rejected "
            "before reaching the workshop stage."
        ],
        "edit_plan": [
            {
                "file": t["file"],
                "line_range": t["line_range"],
                "what": f"Modify based on turn {turn} dialectic findings",
                "how": "See chronicle for details",
            }
            for t in targets[:5]  # cap at 5 edits per spec
        ],
        "test_strategy": "regolith_yard",
        "regression_risk": "MEDIUM",
        "council_dialectic_ref": f"chronicle/turn_{turn:03d}_*.txt",
    }

    return spec


def generate_and_save(turn: int = None) -> Path:
    """Generate a spec and save it."""
    spec = build_spec(turn)
    turn_used = turn or find_latest_turn()
    spec_path = SPEC_DIR / f"spec_turn_{turn_used:03d}.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"[COUNCIL->FORGE] Spec written to {spec_path}")
    print(f"  Title: {spec['title']}")
    print(f"  Files: {spec['target_files']}")
    print(f"  Edits: {len(spec['edit_plan'])}")
    print(f"  Type: {spec['change_type']}")
    return spec_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bridge Council dialectic to Workshop forge")
    parser.add_argument("--turn", type=int, default=None, help="Specific turn to extract")
    parser.add_argument("--run-forge", action="store_true", help="Also run the forge after generating spec")
    args = parser.parse_args()

    spec_path = generate_and_save(args.turn)

    if args.run_forge:
        print(f"\n[BRIDGE] Running forge with {spec_path}...")
        from forge import run_forge
        result = run_forge(str(spec_path))
        print(f"\nForge result: {'PASS' if result['success'] else 'FAIL at ' + str(result.get('failed_at', 'unknown'))}")
