#!/usr/bin/env python3
"""
dialogos.py -- Fully automated dialectical development loop.

Two simulated roles (Main and Worker) take turns asking and answering
10 questions each, building on the entire prior conversation.

Cycle:
  1. Worker asks 10 questions of Main
  2. Main (simulated) answers those 10
  3. Main asks 10 questions of Worker
  4. Worker answers those 10
  5. Goto 1 (with history)

All work is done by the Worker PI agent (via the bridge); "Main" is also
simulated by asking the Worker to role-play Main.  The orchestrator (this
script) manages the flow, chronicles everything, and can seed code changes.
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

# Make stdout handle Unicode gracefully on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -- Config ----------------------------------------------------------------
WORKER_URL = "http://127.0.0.1:8891"
QUESTIONS_PER_TURN = 10
CHRONICLE_DIR = Path(__file__).parent / "chronicle"
CHRONICLE_DIR.mkdir(exist_ok=True)

SYSTEM_CONTEXT = """
GAUSSIAN SPLATTING SYSTEM -- Current state:
- splat_gpu.py: GPU render pipeline with tile-based radix sort (256-splat tiles)
- splat_emit.py: per-batch normalization, logistic midpoint
- bake.py: asset baking pipeline (resolve_assets function MISSING -- needs creation)
- fractal_zoom_sweep.py: 614,813 splats, 7 zoom levels, tested pass
- Dyad module: LM Studio two-brain (Qwen 3.6B MoE + 27B dense)
- Build: last 20 all pass. GPA 1.78 (flat). Vision track CONTAIN at 86%
- Pending: Tool_Scanner_Model (needs_refinement), Tool_Scanner_Material (needs_refinement)
- Gaps: screen-space density cap in splat_gpu.py incomplete, per-batch normalization bug in emit, resolve_assets missing in bake.py
"""


# -- Helpers ----------------------------------------------------------------

def chronicle(turn: int, phase: str, content: str):
    path = CHRONICLE_DIR / f"turn_{turn:03d}_{phase}.txt"
    path.write_text(content, encoding="utf-8")
    return path


def read_history() -> str:
    parts = []
    for p in sorted(CHRONICLE_DIR.iterdir()):
        if p.suffix == ".txt":
            parts.append(f"=== {p.stem} ===\n{p.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def worker_prompt(message: str) -> dict:
    body = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        f"{WORKER_URL}/api/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        result = json.loads(r.read().decode())

    deadline = time.time() + 600
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(f"{WORKER_URL}/api/get_state", timeout=5)
            state = json.loads(resp.read().decode())
            if not state.get("data", {}).get("isStreaming", True):
                break
        except Exception:
            pass
        time.sleep(3)

    return result


def get_worker_last_message() -> str:
    resp = urllib.request.urlopen(f"{WORKER_URL}/api/get_messages", timeout=5)
    msgs = json.loads(resp.read().decode())
    messages = msgs.get("data", {}).get("messages", [])
    for m in reversed(messages):
        if m.get("role") == "assistant" and m.get("content"):
            text = m["content"]
            if isinstance(text, list):
                parts = []
                for seg in text:
                    if seg.get("type") == "text":
                        parts.append(seg["text"])
                return "".join(parts)
            return text
    return ""


def extract_json_array(text: str) -> list[str] | None:
    m = re.search(r'\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\]', text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            pass
    m = re.search(r'```(?:json)?\s*\n?(\[.*?\])\s*\n?```', text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            pass
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    results = []
    for l in lines:
        l = re.sub(r'^\d+[\.\)]\s*', "", l)
        if l and not l.startswith("```") and not l.startswith("{"):
            results.append(l)
    return results[:QUESTIONS_PER_TURN]


# -- Core loop ---------------------------------------------------------------

def run_loop(max_turns: int = 6):
    print("=" * 60)
    print(f"  DIALOGOS v2 -- Fully Automated Dialectical Loop")
    print(f"  {QUESTIONS_PER_TURN} questions/turn, {max_turns} turns")
    print(f"  Worker: {WORKER_URL}")
    print(f"  Chronicle: {CHRONICLE_DIR}")
    print("=" * 60)

    chronicle(0, "seed", SYSTEM_CONTEXT)

    for turn in range(1, max_turns + 1):
        history = read_history()
        print(f"\n{'='*60}")
        print(f"  Turn {turn}")
        print(f"{'='*60}")

        # -- Phase A: Worker asks -> Main answers --------------------------
        print(f"\n--- Phase A: Worker asks {QUESTIONS_PER_TURN} questions of Main ---\n")

        worker_ask_prompt = f"""You are the Worker agent in a dialectical development loop about the Gaussian splatting system.

Your role: ASKER. Formulate exactly {QUESTIONS_PER_TURN} specific, technical questions for the Main agent.

SYSTEM CONTEXT:
{SYSTEM_CONTEXT}

FULL CONVERSATION HISTORY (all previous Q&A rounds):
{history}

INSTRUCTIONS:
- Ask questions that BUILD on the history -- probe deeper into topics raised in previous answers.
- Be technical and specific. Reference actual algorithms, data structures, tradeoffs.
- Do NOT answer your own questions. List them only.
- Return ONLY a JSON array of {QUESTIONS_PER_TURN} strings, nothing else.

Example: ["Question 1?", "Question 2?", ..., "Question {QUESTIONS_PER_TURN}?"]
"""

        worker_prompt(worker_ask_prompt)
        time.sleep(2)
        questions_text = get_worker_last_message()
        questions = extract_json_array(questions_text) or [f"(auto-gen Q{i})" for i in range(1, QUESTIONS_PER_TURN + 1)]
        chronicle(turn, "worker_questions", json.dumps(questions, indent=2))

        print(f"  Worker's {len(questions)} questions:")
        for i, q in enumerate(questions, 1):
            print(f"    Q{i}. {q}")

        # Main (role-played) answers
        print("\n  Main is answering...")
        main_answer_prompt = f"""You are the MAIN agent in a dialectical development loop.

Your role: ANSWERER. Answer every question from the Worker agent thoroughly.

SYSTEM CONTEXT:
{SYSTEM_CONTEXT}

FULL CONVERSATION HISTORY:
{history}

THE QUESTIONS TO ANSWER:
{' '.join(f'{i+1}. {q}' for i, q in enumerate(questions))}

INSTRUCTIONS:
- Number each answer (1. 2. 3. ...).
- Be technical and specific. Reference code paths, algorithms, tradeoffs.
- Be honest about unknowns.
- Each answer should be 2-4 sentences minimum.
"""

        worker_prompt(main_answer_prompt)
        time.sleep(2)
        main_answers = get_worker_last_message()
        chronicle(turn, "main_answers", main_answers)

        print(f"\n  Main's answers:")
        for line in main_answers.split("\n")[:25]:
            print(f"    {line}")
        if len(main_answers.split("\n")) > 25:
            print(f"    ... ({len(main_answers.splitlines())} total lines)")

        # -- Phase B: Main asks -> Worker answers --------------------------
        history = read_history()
        print(f"\n--- Phase B: Main asks {QUESTIONS_PER_TURN} questions of Worker ---\n")

        main_ask_prompt = f"""You are the MAIN agent in a dialectical development loop.

Your role: ASKER. Formulate exactly {QUESTIONS_PER_TURN} new questions for the Worker agent.

SYSTEM CONTEXT:
{SYSTEM_CONTEXT}

FULL CONVERSATION HISTORY (including your own answers from Phase A):
{history}

INSTRUCTIONS:
- Ask questions that BUILD on both the Worker's previous questions and your own answers.
- Probe deeper: implementation details, edge cases not covered, testing strategies, tradeoffs.
- Be technical and specific.
- Return ONLY a JSON array of {QUESTIONS_PER_TURN} strings, nothing else.
"""

        worker_prompt(main_ask_prompt)
        time.sleep(2)
        main_questions_text = get_worker_last_message()
        main_questions = extract_json_array(main_questions_text) or [f"(auto-gen Q{i})" for i in range(1, QUESTIONS_PER_TURN + 1)]
        chronicle(turn, "main_questions", json.dumps(main_questions, indent=2))

        print(f"  Main's {len(main_questions)} questions:")
        for i, q in enumerate(main_questions, 1):
            print(f"    Q{i}. {q}")

        # Worker answers
        print("\n  Worker is answering...")
        worker_answer_prompt = f"""You are the WORKER agent in a dialectical development loop.

Your role: ANSWERER. Answer every question from the Main agent thoroughly.

SYSTEM CONTEXT:
{SYSTEM_CONTEXT}

FULL CONVERSATION HISTORY:
{history}

THE QUESTIONS TO ANSWER:
{' '.join(f'{i+1}. {q}' for i, q in enumerate(main_questions))}

INSTRUCTIONS:
- Number each answer (1. 2. 3. ...).
- Be technical and specific. Reference code paths, algorithms, tradeoffs.
- Be honest about unknowns.
- Where appropriate, suggest concrete code changes or file edits.
- Each answer should be 2-4 sentences minimum.
"""

        worker_prompt(worker_answer_prompt)
        time.sleep(2)
        worker_answers = get_worker_last_message()
        chronicle(turn, "worker_answers", worker_answers)

        print(f"\n  Worker's answers:")
        for line in worker_answers.split("\n")[:25]:
            print(f"    {line}")
        if len(worker_answers.split("\n")) > 25:
            print(f"    ... ({len(worker_answers.splitlines())} total lines)")

        # Summary
        print(f"\n--- Turn {turn} complete [{len(str(history))} chars in chronicle] ---")
        print(f"  Next turn in 3s... (Ctrl+C to stop)")
        time.sleep(3)

    print(f"\n{'='*60}")
    print(f"  DIALOGOS COMPLETE: {max_turns} turns")
    print(f"  Chronicle: {CHRONICLE_DIR}")
    print(f"{'='*60}\n")


# -- CLI -------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fully automated dialectical development loop")
    parser.add_argument("--turns", type=int, default=6, help="Number of turns (each turn = 2 phases x 10 questions)")
    parser.add_argument("--port", type=int, default=8891, help="Worker bridge port")
    args = parser.parse_args()

    WORKER_URL = f"http://127.0.0.1:{args.port}"

    try:
        resp = urllib.request.urlopen(f"{WORKER_URL}/api/status", timeout=3)
        status = json.loads(resp.read().decode())
        if status.get("status") != "running":
            print(f"[ERROR] Worker bridge not running on {WORKER_URL}")
            sys.exit(1)
        print(f"[OK] Worker bridge alive (PID {status.get('pid')})")
    except Exception as e:
        print(f"[ERROR] Cannot reach worker bridge: {e}")
        sys.exit(1)

    run_loop(max_turns=args.turns)
