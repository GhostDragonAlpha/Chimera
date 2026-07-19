"""
dyad — THE DRIVER. Two minds that drive development, turn by turn.

The dyad reads the brief + project state, decides what to build next,
hands the instruction to the lead agent. The lead executes, reports back,
the dyad evaluates and decides the next move. Loop continues until human
stops it manually.

  from core.dyad import drive, report
  instr = drive()          # dyad decides what to do next
  # ... execute instr ...
  report(outcome, context) # tell dyad what happened

The dyad has no file access — the lead agent injects real project state
via build_project_context() before each drive() call.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BRIEF_PATH = ROOT / "docs" / "BRIEF.md"

from core.lm_gateway import loaded_models, load_model
from core.council import FAST_MODEL_ID, DEEP_MODEL_ID, _ensure_model, _fast, _deep


# --- brief: the shared artifact ---------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())


def read_brief() -> str:
    if not BRIEF_PATH.exists():
        return "No prior context."
    return BRIEF_PATH.read_text(encoding="utf-8", errors="replace")[:2000]


def append_brief(entry: str):
    BRIEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    exists = BRIEF_PATH.exists()
    with open(BRIEF_PATH, "a", encoding="utf-8") as f:
        if not exists:
            f.write(f"# DYAD BRIEF - {_now()}\n\n")
        f.write(entry + "\n\n")


# --- model resolution -------------------------------------------------------

def _resolve_fast() -> str:
    if FAST_MODEL_ID: return FAST_MODEL_ID
    r = loaded_models()
    if r: return r[0]
    try:
        import json, urllib.request
        with urllib.request.urlopen("http://localhost:1234/api/v0/models", timeout=8) as r:
            avail = [m["id"] for m in json.load(r).get("data", [])
                     if m.get("type") == "llm" and m.get("id")]
        if avail:
            load_model(avail[0], timeout=120, context_length=32768)
            return avail[0]
    except Exception:
        pass
    raise RuntimeError("No model available in LM Studio.")

def _resolve_deep() -> str:
    return DEEP_MODEL_ID or _resolve_fast()


# --- strip reasoning thinking trace -----------------------------------------

def _strip_thinking(text: str) -> str:
    """Remove the 'thinking process' preamble that reasoning models emit."""
    markers = [
        "Here's a thinking process:",
        "Thinking Process:",
        "Let me think about this:",
        "Let me analyze:",
    ]
    for m in markers:
        idx = text.find(m)
        if idx < 0:
            continue
        after = text[idx + len(m):].strip()
        # The thinking process is typically a numbered list or bullet section.
        # Collect lines after the thinking block ends.
        lines = after.split("\n")
        answer = []
        in_thinking = True
        for line in lines:
            s = line.strip()
            if in_thinking and (
                    s.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))
                    or s.startswith(("*", "-", "**"))):
                continue
            in_thinking = False
            answer.append(line)
        if answer:
            return "\n".join(answer).strip()
        return after.strip()
    return text.strip()


# --- project context builder (the dyad's eyes) ------------------------------

def build_project_context() -> str:
    """Gather real project state so the dyad knows what exists."""
    parts = ["=== PROJECT STATE ==="]

    brief = read_brief()
    parts.append(f"BRIEF:\n{brief[:1000]}")

    core_dir = HERE
    key_files = ["splat_lod.py", "splat_gpu.py", "splat_emit.py",
                 "matter.py", "limb.py", "rig.py", "bake.py",
                 "trainer.py", "matter_gpu.py", "dyad.py",
                 "council.py", "lm_gateway.py"]
    existing = [f for f in key_files if (core_dir / f).exists()]
    parts.append(f"EXISTING CORE FILES:\n" + ", ".join(existing))

    tests_dir = ROOT / "tests"
    if tests_dir.exists():
        tests = sorted(f.name for f in tests_dir.glob("*.py"))
        parts.append(f"TESTS:\n" + ", ".join(tests))

    try:
        import subprocess as sp
        gl = sp.run(["git", "log", "--oneline", "-5", "--", "core/", "tests/"],
                     capture_output=True, text=True, timeout=10, cwd=str(ROOT))
        if gl.stdout.strip():
            parts.append(f"RECENT CHANGES:\n{gl.stdout.strip()}")
    except Exception:
        pass

    return "\n\n".join(parts)


# --- the drive function -----------------------------------------------------

def drive(context: str = "") -> str:
    """Ask the dyad: what should the developer do next?

    Injects real project state so the dyad can make informed decisions.

    Returns a concrete instruction starting with 'NEXT:'.
    """
    brief = context or build_project_context()

    # FAST proposes
    fast_id = _resolve_fast()
    _ensure_model(fast_id)
    fast_prompt = (
        f"PROJECT STATE:\n{brief}\n\n"
        f"You are the FAST mind. Assess the current state.\n"
        f"What is the ONE most important thing to do next?\n"
        f"Be concrete: name files, APIs, tests, evidence.\n"
        f"Keep it tight - 1-2 paragraphs.\n"
        f"State your recommendation clearly.\n"
        f"Then say what you want DEEP to pressure-test about it.")
    fast_raw = _fast(fast_prompt, max_tokens=1200, temperature=0.6, agent="dyad-fast")
    fast_out = _strip_thinking(fast_raw)
    if not fast_out:
        fast_out = fast_raw[:400]

    # DEEP pressure-tests
    deep_id = _resolve_deep()
    _ensure_model(deep_id)
    deep_prompt = (
        f"PROJECT STATE:\n{brief}\n\n"
        f"FAST recommends:\n{fast_out[:1500]}\n\n"
        f"You are the DEEP mind. Pressure-test FAST's recommendation.\n"
        f"Surface hidden assumptions. Name what FAST missed.\n"
        f"Suggest refinements or alternatives.\n"
        f"Keep it focused - a single dense paragraph.")
    deep_raw = _deep(deep_prompt, max_tokens=1200, temperature=0.5)
    deep_out = _strip_thinking(deep_raw)
    if not deep_out:
        deep_out = deep_raw[:400]

    # FAST synthesizes into a concrete instruction
    _ensure_model(fast_id)
    instr_prompt = (
        f"PROJECT STATE:\n{brief}\n\n"
        f"FAST's recommendation:\n{fast_out[:1000]}\n\n"
        f"DEEP's critique:\n{deep_out[:1000]}\n\n"
        f"Now synthesize into ONE concrete instruction for the developer.\n"
        f"Respond in exactly this format:\n"
        f"NEXT: <the instruction>"
        f"\n\nName the specific file, function, test, or evidence to touch.\n"
        f"Be precise and actionable. This is what gets executed NOW.")
    instr_raw = _fast(instr_prompt, max_tokens=2000, temperature=0.5, agent="dyad-drive")
    instruction = _strip_thinking(instr_raw)

    # Extract NEXT: line
    for line in instruction.splitlines():
        s = line.strip()
        if s.upper().startswith("NEXT:"):
            instruction = s[5:].strip()
            break
    else:
        # Fallback: take the last substantial line
        for line in reversed(instruction.splitlines()):
            s = line.strip()
            if s and len(s) > 15:
                instruction = s
                break

    # Record to brief
    ts = _now()
    append_brief(
        f"### TURN {ts}\n"
        f"**Dyad instruction:** {instruction[:400]}\n"
        f"**FAST reasoning:** {fast_out[:200]}\n"
        f"**DEEP scrutiny:** {deep_out[:200]}\n"
        f"---")

    try:
        from core.capcom import post_safe
        post_safe("dyad", f"dyad: {instruction[:120]}", level="note", source="dyad")
    except Exception:
        pass

    return instruction


# --- report function --------------------------------------------------------

def report(outcome: str, context: str = ""):
    """Report the results of executing the dyad's instruction."""
    ts = _now()
    entry = (
        f"### RESULT {ts}\n"
        f"**Outcome:** {outcome[:600]}\n"
        + (f"**Evidence:** {context[:600]}\n" if context else "")
        + "---")
    append_brief(entry)

    try:
        from core.graphify_interface import record_surprise
        record_surprise(
            context="dyad turn result",
            reality=outcome[:400],
            expectation="the dyad's instruction was executed",
            source="agent")
    except Exception:
        pass


# --- CLI --------------------------------------------------------------------

def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog="dyad", description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)

    sd = sub.add_parser("drive", help="ask the dyad what to do next")
    sd.add_argument("context", nargs="?", default="",
                    help="context (auto-gathered if empty)")

    sr = sub.add_parser("report", help="report results of the last instruction")
    sr.add_argument("outcome", help="what happened")
    sr.add_argument("--context", default="", help="extra evidence")

    sb = sub.add_parser("brief", help="read the current brief")

    a = p.parse_args(argv)

    if a.cmd == "brief":
        print(read_brief())
        return 0

    if a.cmd == "drive":
        instr = drive(context=a.context)
        print(instr)
        return 0

    if a.cmd == "report":
        report(a.outcome, context=a.context)
        print("Reported to brief.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
