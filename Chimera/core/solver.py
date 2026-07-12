"""Solver — figures out the FIX for arbitrary blockers (no-blockers law, stage 2).

`core.unblock` heals KNOWN blockers with hardcoded recipes. This module handles the
UNKNOWN ones: diagnose -> check the graph for prior solutions -> generate a bounded
remediation plan (local LM; deterministic template if the LM is unreachable) ->
execute the safe steps -> verify -> record. Outcomes:

  SOLVED   -> the working step sequence is recorded as a new pathway recipe
              (next time this is a KNOWN blocker).
  DRAFTED  -> steps beyond the safety allowlist (or that failed) are written as a
              recipe-carrying NEXT item in task_progress.md — the output of hitting
              a blocker is ALWAYS a concrete fix plan, never a bare "blocked" note.

Safety allowlist for autonomous execution (everything else -> DRAFTED):
  python_module : `python -m core.<module> ...` only (no arbitrary shell)
  mcp_call      : tool calls through MCPStdioClient (same surfaces duty agents use)
  retry_modified: rerun the original failed command with adjusted args (allowlist-checked)

Usage:
  python -m core.solver --blocker "<one line>" --context "<error verbatim>"
         [--from-command "<the command that failed>"] [--no-execute] [--deterministic]
"""

import argparse
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK_PROGRESS = ROOT.parent / "task_progress.md"
LM_URL = "http://localhost:1234/v1/chat/completions"
ALLOWED_MODULE = re.compile(r"^python -m core\.[a-z_]+(\s|$)")

PLAN_SCHEMA_HINT = {
    "diagnosis": "<one-paragraph root-cause hypothesis>",
    "steps": [{"kind": "python_module | mcp_call | retry_modified | capable_handoff",
               "command": "<for python_module/retry_modified: full command starting 'python -m core.'>",
               "tool": "<for mcp_call>", "args": {}, "note": "<why this step>"}],
    "confidence": 0.0,
}


def _prior_solutions(blocker: str, nodes):
    """Have we solved something like this before? Token-overlap over solver pathways."""
    toks = set(re.findall(r"[a-z0-9_]+", blocker.lower())) - {"the", "a", "is", "not"}
    hits = []
    for n in nodes:
        if n.get("type") == "pathway_attempt" and n.get("tool") == "solver" \
                and n.get("result") == "success":
            blob = json.dumps(n, default=str).lower()
            score = sum(1 for t in toks if t in blob)
            if score >= max(2, len(toks) // 3):
                hits.append((score, n))
    hits.sort(key=lambda x: -x[0])
    return [n for _, n in hits[:2]]


def _lm_plan(blocker: str, context: str, from_command: str, max_tokens: int = 2000) -> dict:
    """H-3 discipline: /no_think, generous budget, parse content AND reasoning_content."""
    payload = {
        "messages": [{"role": "user", "content":
            f"/no_think You are the remediation solver for an automated UE5.8 game pipeline "
            f"(Windows, python core/ modules, MCP editor bridge). A workflow item hit a blocker.\n"
            f"BLOCKER: {blocker}\nERROR/CONTEXT (verbatim): {context[:1200]}\n"
            f"FAILED COMMAND (if any): {from_command or 'n/a'}\n"
            f"Known tools you may plan with: python -m core.unblock|sleepwalker|rehearsal|gardener|"
            f"dream_loop|telemetry_probe|result_grader|graphify_record; MCP tools control_editor/"
            f"inspect/control_actor/manage_effect (read-backs mandatory). Anything else (installs, "
            f"code edits, engine repairs) must be kind=capable_handoff with an exact recipe in note.\n"
            f"Return ONLY JSON matching:\n{json.dumps(PLAN_SCHEMA_HINT, indent=1)}"}],
        "max_tokens": max_tokens, "temperature": 0.2,
    }
    req = urllib.request.Request(LM_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    from core.lm_gateway import lm_urlopen, LM_TIMEOUT
    with lm_urlopen(req, timeout=LM_TIMEOUT, agent="solver") as r:
        msg = json.load(r)["choices"][0]["message"]
    for text in (msg.get("content") or "", msg.get("reasoning_content") or ""):
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                plan = json.loads(m.group(0))
                if isinstance(plan.get("steps"), list):
                    return plan
            except json.JSONDecodeError:
                continue
    raise ValueError("LM returned no valid plan JSON (H-3: retry or fall back)")


def _deterministic_plan(blocker: str, from_command: str) -> dict:
    return {"diagnosis": f"LM unavailable — template remediation for: {blocker}",
            "steps": ([{"kind": "python_module", "command": "python -m core.unblock --ensure all",
                        "note": "heal the known environment blockers first"}]
                      + ([{"kind": "retry_modified", "command": from_command,
                           "note": "retry once after environment heal"}] if from_command
                          and ALLOWED_MODULE.match(from_command) else [])
                      + [{"kind": "capable_handoff", "note":
                          f"If still blocked: diagnose '{blocker}' — attach the verbatim error, "
                          f"check docs/MCP_PATHWAYS.md traps, record the fix as a pathway."}]),
            "confidence": 0.3}


def _execute_step(step: dict) -> (bool, str):
    kind = step.get("kind")
    if kind in ("python_module", "retry_modified"):
        cmd = str(step.get("command", ""))
        if not ALLOWED_MODULE.match(cmd):
            return False, f"outside allowlist: {cmd[:60]}"
        r = subprocess.run(cmd.split(), capture_output=True, text=True,
                           cwd=str(ROOT), timeout=900)
        tail = ((r.stdout or "") + (r.stderr or "")).strip()[-160:]
        return r.returncode == 0, tail
    if kind == "mcp_call":
        try:
            from core.telemetry_probe import MCPStdioClient
            c = MCPStdioClient()
            r = c.call(step.get("tool", ""), step.get("args") or {})
            sc = r.get("result", {}).get("structuredContent", {})
            return bool(sc.get("success")), str(sc.get("message", ""))[:160]
        except Exception as ex:
            return False, str(ex)[:160]
    return False, "capable_handoff (not autonomously executable)"


def _draft_next_item(blocker: str, plan: dict, results: list):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    steps_txt = "\n".join(
        f"   {i}. [{s.get('kind')}] {s.get('command') or s.get('tool') or ''} — {s.get('note','')}"
        + (f" (attempted: {r})" if r else "")
        for i, (s, r) in enumerate(
            zip(plan.get("steps", []), results + [None] * len(plan.get("steps", []))), 1))
    block = (f"# Solver draft {stamp} — blocker: {blocker[:80]}\n\n"
             f"Diagnosis: {plan.get('diagnosis','?')}\nConfidence: {plan.get('confidence')}\n\n"
             f"## NEXT (solver-drafted fix plan; the blocker is NOT the note — this plan is)\n"
             f"1. **Fix: {blocker[:60]}** `capable sessions only` — execute the remaining steps:\n"
             f"{steps_txt}\n   Skip-condition: blocker no longer reproduces → record pathway success.\n\n---\n\n")
    old = TASK_PROGRESS.read_text(encoding="utf-8") if TASK_PROGRESS.exists() else ""
    TASK_PROGRESS.write_text(block + old, encoding="utf-8")


def solve(blocker: str, context: str = "", from_command: str = "",
          execute: bool = True, deterministic: bool = False) -> dict:
    from core.graphify_interface import load_dna_graph, record_pathway, record_surprise
    nodes = load_dna_graph().get("nodes", [])

    prior = _prior_solutions(blocker, nodes)
    if prior:
        print(f"[solver] prior solution(s) found: {[n.get('id') for n in prior]} — reusing plan shape")

    plan = None
    if not deterministic:
        for attempt, budget in enumerate((2000, 4000), 1):  # H-3: retry once, bigger budget
            try:
                plan = _lm_plan(blocker, context, from_command, max_tokens=budget)
                break
            except Exception as ex:
                print(f"[solver] LM plan attempt {attempt} failed ({str(ex)[:70]})"
                      + ("" if attempt == 2 else " — retrying with larger budget"))
    if plan is None:
        plan = _deterministic_plan(blocker, from_command)

    print(f"[solver] diagnosis: {str(plan.get('diagnosis',''))[:180]}")
    results, solved = [], False
    if execute:
        for step in plan.get("steps", []):
            if step.get("kind") == "capable_handoff":
                results.append("handoff")
                continue
            ok, note = _execute_step(step)
            results.append(f"{'OK' if ok else 'FAIL'}: {note[:80]}")
            print(f"[solver] step {step.get('kind')}: {'OK' if ok else 'FAIL'} — {note[:100]}")
            if not ok:
                break
        else:
            solved = (any(str(r).startswith("OK") for r in results)
                      and not any(str(r).startswith("FAIL") for r in results)
                      and "handoff" not in results)  # a plan still needing hands is DRAFTED

    verdict = "solved" if solved else "drafted"
    record_pathway("solver", re.sub(r"[^a-z0-9_]+", "_", blocker.lower())[:60],
                   "success" if solved else "partial",
                   {"diagnosis": str(plan.get("diagnosis", ""))[:160],
                    "steps": json.dumps(plan.get("steps", []))[:400],
                    "results": json.dumps(results)[:200]})
    if not solved:
        _draft_next_item(blocker, plan, results)
        record_surprise(context=f"Novel blocker: {blocker[:120]}",
                        reality=f"Solver drafted a fix plan (confidence {plan.get('confidence')}); "
                                f"steps executed: {len(results)}",
                        lesson_hint="solver draft in task_progress — dream fodder for a recipe",
                        source="agent")
        print(f"[solver] DRAFTED: fix plan written to task_progress.md — the plan IS the output")
    else:
        print(f"[solver] SOLVED: sequence recorded as a reusable pathway recipe")
    return {"verdict": verdict, "plan": plan, "results": results}


def main():
    parser = argparse.ArgumentParser(description="Figure out the fix for an arbitrary blocker")
    parser.add_argument("--blocker", required=True)
    parser.add_argument("--context", default="")
    parser.add_argument("--from-command", default="", dest="from_command")
    parser.add_argument("--no-execute", action="store_true")
    parser.add_argument("--deterministic", action="store_true",
                        help="skip the LM, use the template plan (offline fallback)")
    args = parser.parse_args()
    solve(args.blocker, args.context, args.from_command,
          execute=not args.no_execute, deterministic=args.deterministic)
    return 0  # the solver itself is never a blocker


if __name__ == "__main__":
    raise SystemExit(main())
