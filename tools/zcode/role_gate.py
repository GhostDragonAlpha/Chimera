"""Project-scoped Z Code instructions and purpose-preserving dispatch.

Native permissions, goal continuation and model settings remain authoritative.
This hook adds no mandatory review/research ceremony or completion marker.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get("CHIMERA_WORKFLOW_STATE_DIR", str(ROOT / "sessions")))
VERSION = "playable-purpose-20261018-v1"
PROFILES = {"chimera-worker", "chimera-maya", "chimera-step37", "chimera-researcher"}
RESEARCH_TOOLS = {"Read", "Glob", "Grep", "WebSearch", "WebFetch",
                  "ListMcpResourcesTool", "ReadMcpResourceTool",
                  "RespondToCoordinator"}
DELEGATION = {"Agent", "Task", "CreateWorkflow", "AmendWorkflow"}
MARKER = "[CHIMERA TASK PURPOSE v1]"
TRANSFER = (
    MARKER + "\n"
    "Main goal: a playable matter-simulator game where players build, test, repair "
    "and reuse meaningful constructions. Follow the lead's current milestone and "
    "specific task below; do not replace it with a new project. Understand the "
    "player benefit, why this task matters now, and the decision your result enables. "
    "If the lead omitted the rationale, state a grounded assumption from the task "
    "and surface ambiguity that would change the work. Preserve this purpose, task "
    "identity and pending decision through compression and resume. Report game "
    "impact, evidence/limits, decision and next useful action. Suggest a better "
    "method when useful; the lead may choose any suitable peer or work directly.\n"
)

def context():
    return (ROOT / "GAME_WORKFLOW.md").read_text(encoding="utf-8")

def _load(event):
    sid = str(event.get("session_id", event.get("sessionId", "")))
    if not sid:
        return None, {}
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / (hashlib.sha256(sid.encode()).hexdigest() + ".json")
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(saved, dict):
            saved = {}
    except (FileNotFoundError, ValueError):
        saved = {}
    return path, saved

def _save(path, saved):
    if path is None:
        return
    temp = path.with_name(path.name + "." + str(os.getpid()) + ".tmp")
    temp.write_text(json.dumps(saved), encoding="utf-8")
    os.replace(temp, path)

def _deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "deny", "permissionDecisionReason": reason}}

def respond(event):
    kind = event.get("hook_event_name", event.get("hookEventName"))
    path, saved = _load(event)
    # Identity comes from the native lifecycle, never tool arguments.
    role = event.get("agent_type") or event.get("agentName") or saved.get("role")
    if not role and saved.get("researcher"):
        role = "chimera-researcher"
    elif not role and saved.get("consultant"):
        role = "chimera-consultant"
    elif not role and saved.get("worker"):
        role = "chimera-worker"
    sid = str(event.get("session_id", event.get("sessionId", "")))
    child = bool(role in PROFILES or role == "chimera-consultant"
                 or saved.get("child") or sid.startswith("sess_subagent_"))
    researcher = role in {"chimera-researcher", "chimera-consultant"}
    saved.update(role=role, child=child)
    result = {}
    extra = []
    if kind == "SessionStart" or (kind in {"UserPromptSubmit", "PreToolUse", "PostToolUse"}
                                 and saved.get("purpose_version") != VERSION):
        extra.append(context())
        saved["purpose_version"] = VERSION

    name = event.get("tool_name", event.get("toolName", ""))
    args = event.get("tool_input", event.get("toolInput", {})) or {}
    if kind == "PreToolUse":
        if researcher and name not in RESEARCH_TOOLS:
            result = _deny("This researcher is read-only; return findings or a suggested implementation to the lead.")
        elif child and name in DELEGATION:
            result = _deny("Return delegation suggestions to the lead; this harness uses one child level.")
        elif not child and name in {"Agent", "Task"}:
            if args.get("run_in_background"):
                result = _deny("Use a foreground child on this single-GPU host; choose any suitable available profile.")
            elif isinstance(args.get("prompt"), str) and MARKER not in args["prompt"]:
                result = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                          "updatedInput": {**args, "prompt": TRANSFER + "\nASSIGNED TASK:\n" + args["prompt"]}}}
        elif not child and name == "SendMessage":
            # Preserve target/model and all other native arguments.
            for key in ("message", "prompt", "content"):
                if isinstance(args.get(key), str):
                    if MARKER not in args[key]:
                        result = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                  "updatedInput": {**args, key: TRANSFER + "\nFOLLOW-UP:\n" + args[key]}}}
                    break
        # The lead otherwise uses its actual tools and ordinary permission policy.
    if kind == "PostToolUse" and not child and name in {"Agent", "Task", "SendMessage"}:
        extra.append("Inspect the actual terminal child result (TaskOutput if needed). "
                     "Acknowledge game impact and limits, then choose implementation, "
                     "research, focused review, optimization or the next useful action. "
                     "Delivery/running status is not a verdict; no automatic review round is required.")
    if extra:
        result["additionalContext"] = "\n\n".join(extra)
    _save(path, saved)
    return result

if __name__ == "__main__":
    print(json.dumps(respond(json.load(sys.stdin))))
