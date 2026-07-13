"""Witness Runner — bounded, self-cleaning wrapper around Sleepwalker beat runs.

THE ORPHAN-EDITOR FIX (design directive Part A #2, 2026-07-13): a prior witness
session hung for ~7-8 real minutes (an O2-depletion beat literally waiting out
the drain in real time) and left UnrealEditor.exe running — nothing OUTSIDE the
hung process could stop PIE or close the editor once whatever was driving it
(an external tool-call timeout, a dropped terminal, anything) killed the child
without letting its own `finally: stop_pie()` run.

This wrapper fixes the pattern, not just this one incident:

  1. HARD WALL-CLOCK BUDGET. The beat run executes in a CHILD PROCESS
     (`python -m core.sleepwalker ...`) under a real timeout. The sleepwalker
     itself no longer has to be trusted to self-terminate — if it (or any MCP
     call inside it) hangs past `--budget-s`, this wrapper kills the child's
     WHOLE process tree (`taskkill /T /F`, not just the immediate PID — a bare
     subprocess.run(timeout=) kill only touches the direct child on Windows and
     can strand grandchildren, e.g. the node.exe MCP bridge CLI each
     MCPStdioClient() construction spawns).

  2. ALWAYS CLEAN UP, EVEN ON FAILURE. A `finally` block (timeout, crash, or a
     clean exit) always attempts `stop_pie` via a FRESH MCPStdioClient. This is
     safe to rely on regardless of the child's fate: MCPStdioClient spawns its
     OWN short-lived bridge-CLI process on construction and reaches the SAME
     running editor over its socket — it does not depend on the dead child's
     pipes or state. Calling stop_pie when nothing is playing is a harmless
     no-op (wrapped in try/except regardless).

  3. OPTIONAL FULL CLOSE. `--close-editor-on-exit` additionally force-kills
     UnrealEditor.exe / UnrealEditor-Cmd.exe / CrashReportClientEditor.exe
     (the same kill-list core.editor_scheduler._kill_ue_processes() uses) and
     releases this agent's editor_scheduler claim if it holds one. Off by
     default because the studio's normal convention is ONE shared long-lived
     editor across concurrent agents (core/editor_scheduler.py) — this wrapper
     must not tear that down on every routine sleepwalk. Use the flag when a
     witness session is explicitly meant to be the last thing you do before
     ending your shift (exactly what a bounded, one-shot witnessed cycle is).

  4. UN-THROTTLE BEFORE LAUNCH (found empirically running this task, 2026-07-13):
     an editor started without OS window focus (any headless/background launch,
     `core.unblock.ensure_editor()` included) throttles to ~3fps
     (`bThrottleCPUWhenNotForeground`, pathway #25's known trap) — and separately,
     UE's OWN automation framework has a `FWaitForInteractiveFrameRate` latent
     command that BLOCKS `Automation RunTests` until fps >= 10, so a
     background-launched headless test run stalls indefinitely, not just runs
     slow (confirmed live: fps pinned at 3, "Will timeout in 570[s]"). This
     wrapper writes `bThrottleCPUWhenNotForeground=False` into
     `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini` before ANY
     editor launch it triggers, so the beat run (and any automation test run
     sharing the editor) ticks at full speed regardless of window focus.

Usage
-----
    python -m core.witness_runner --beats docs/beats/X.beats.json --session Y \
        [--budget-s 240] [--close-editor-on-exit] [--no-record] [--keep-pie] \
        [--fuzz N] [--agent-id ID]

Every flag not consumed by this wrapper (--no-record/--keep-pie/--fuzz/--agent-id)
passes straight through to `core.sleepwalker`.

Exit codes: 0 = child completed within budget (regardless of beats pass/fail —
that verdict is in the printed JSON, same as running sleepwalker directly).
2 = budget exceeded (child killed). 3 = child crashed (nonzero return code).
Cleanup is attempted identically in every case.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _record(action: str, result: str, note: str):
    try:
        from core.graphify_interface import record_pathway
        record_pathway("witness_runner", action, result, {"note": note[:200]})
    except Exception:
        pass  # recording must never block cleanup or the exit code


def _kill_process_tree(pid: int) -> None:
    """Kill a process and everything it spawned (Windows: taskkill /T /F).
    A bare Popen.kill()/subprocess.run(timeout=) only signals the immediate
    child — any grandchild (e.g. the node.exe MCP bridge CLI a hung
    sleepwalker's MCPStdioClient spawned) would otherwise survive as an
    orphan of its own."""
    try:
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(pid)],
            capture_output=True, text=True, timeout=20,
        )
    except Exception:
        pass


def _stop_pie_best_effort() -> tuple[bool, str]:
    """Fresh, independent connection to the (still-running) editor — proven to
    work regardless of what happened to any other process, since
    MCPStdioClient spawns its own bridge-CLI client per construction."""
    try:
        from core.telemetry_probe import MCPStdioClient
        c = MCPStdioClient()
        try:
            r = c.call("control_editor", {"action": "stop_pie"})
            sc = (r or {}).get("result", {}).get("structuredContent", {})
            return True, f"stop_pie issued (success={sc.get('success')})"
        finally:
            c.close()
    except Exception as ex:
        return False, f"stop_pie unreachable ({type(ex).__name__}: {str(ex)[:100]})"


_THROTTLE_INI = ROOT / "Saved" / "Config" / "WindowsEditor" / "EditorPerProjectUserSettings.ini"
_THROTTLE_SECTION = "[/Script/UnrealEd.EditorPerformanceSettings]"
_THROTTLE_KEY = "bThrottleCPUWhenNotForeground=False"


def _ensure_unthrottled() -> str:
    """Write bThrottleCPUWhenNotForeground=False so a background-launched editor
    (no OS window focus) still ticks at full speed -- required for
    FWaitForInteractiveFrameRate-gated automation tests and for honest fps
    telemetry either way (pathway #25/#33). Idempotent; a no-op once set."""
    try:
        text = _THROTTLE_INI.read_text(encoding="utf-8") if _THROTTLE_INI.exists() else ""
        if _THROTTLE_KEY in text:
            return "already set"
        _THROTTLE_INI.parent.mkdir(parents=True, exist_ok=True)
        if _THROTTLE_SECTION in text:
            # Section exists without the key -- append the key right after the header.
            text = text.replace(_THROTTLE_SECTION, f"{_THROTTLE_SECTION}\n{_THROTTLE_KEY}", 1)
        else:
            sep = "\n" if text and not text.endswith("\n") else ""
            text += f"{sep}\n{_THROTTLE_SECTION}\n{_THROTTLE_KEY}\n"
        _THROTTLE_INI.write_text(text, encoding="utf-8")
        return "written"
    except Exception as ex:
        return f"failed ({ex}) -- editor may throttle to ~3fps unfocused"


def _close_editor_fully() -> str:
    """Force-close the editor + release any editor_scheduler claim this
    process/agent might hold. Reuses the scheduler's own kill-list so there is
    exactly one place that knows which processes constitute 'the editor'."""
    try:
        from core.editor_scheduler import _kill_ue_processes
        _kill_ue_processes()
        return "UnrealEditor.exe/-Cmd.exe/CrashReportClientEditor.exe force-killed"
    except Exception as ex:
        return f"kill helper unavailable ({ex}); editor may still be running"


def run_witness(beats: str, session: str, budget_s: float = 240.0,
                 close_editor_on_exit: bool = False, extra_args: list[str] = None,
                 agent_id: str = None) -> int:
    extra_args = extra_args or []
    unthrottle_note = _ensure_unthrottled()
    print(f"[witness_runner] un-throttle ini: {unthrottle_note} "
          f"(takes effect on the editor's NEXT launch, not a live instance)")

    cmd = [sys.executable, "-m", "core.sleepwalker",
           "--beats", beats, "--session", session] + extra_args
    if agent_id:
        cmd += ["--agent-id", agent_id]

    print(f"[witness_runner] launching (budget={budget_s:.0f}s): {' '.join(cmd)}")
    start = time.monotonic()
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    proc = subprocess.Popen(
        cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, creationflags=creationflags,
    )

    exit_code = 0
    outcome = "completed"
    stdout_text = ""
    try:
        try:
            stdout_text, _ = proc.communicate(timeout=budget_s)
            elapsed = time.monotonic() - start
            if proc.returncode == 0:
                print(stdout_text)
                print(f"[witness_runner] child completed in {elapsed:.1f}s (within {budget_s:.0f}s budget)")
                _record("beat_run", "success", f"{session}: completed in {elapsed:.1f}s")
            else:
                outcome, exit_code = "crashed", 3
                print(stdout_text)
                print(f"[witness_runner] child EXITED NONZERO ({proc.returncode}) after {elapsed:.1f}s")
                _record("beat_run", "failed", f"{session}: child exit code {proc.returncode}")
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            outcome, exit_code = "timeout", 2
            print(f"[witness_runner] BUDGET EXCEEDED after {elapsed:.1f}s (budget {budget_s:.0f}s) — "
                  f"killing child process tree (pid={proc.pid})")
            _kill_process_tree(proc.pid)
            try:
                stdout_text = proc.stdout.read() if proc.stdout else ""
                if stdout_text:
                    print(stdout_text)
            except Exception:
                pass
            _record("beat_run", "timeout", f"{session}: exceeded {budget_s:.0f}s budget, child tree killed")
    finally:
        # ALWAYS — timeout, crash, or clean exit — try to leave PIE stopped.
        # This is the actual fix for "orphaned editor stuck mid-PIE": it does
        # not matter whether the child ever reached its own finally block.
        ok, note = _stop_pie_best_effort()
        print(f"[witness_runner] cleanup: {note}")
        if close_editor_on_exit:
            close_note = _close_editor_fully()
            print(f"[witness_runner] cleanup: {close_note}")
            if agent_id:
                try:
                    from core.editor_scheduler import release_editor
                    release_editor(agent_id)
                except Exception:
                    pass

    print(f"[witness_runner] verdict: {outcome.upper()} (exit={exit_code})")
    return exit_code


def main():
    p = argparse.ArgumentParser(description="Bounded, self-cleaning wrapper around core.sleepwalker")
    p.add_argument("--beats", required=True)
    p.add_argument("--session", required=True)
    p.add_argument("--budget-s", type=float, default=240.0,
                   help="Hard wall-clock cap in seconds (default 240). The child's whole "
                        "process tree is killed if it runs past this.")
    p.add_argument("--close-editor-on-exit", action="store_true",
                   help="Force-close the editor after cleanup (use for a standalone witnessed "
                        "session that should not leave the editor running — NOT for routine "
                        "sleepwalks sharing the studio's long-lived editor).")
    p.add_argument("--no-record", action="store_true")
    p.add_argument("--keep-pie", action="store_true",
                   help="Passed through to sleepwalker; note --close-editor-on-exit still "
                        "stops PIE + closes the editor in THIS wrapper's cleanup regardless.")
    p.add_argument("--fuzz", type=int, default=None)
    p.add_argument("--agent-id", default=None)
    args = p.parse_args()

    extra = []
    if args.no_record:
        extra.append("--no-record")
    if args.keep_pie:
        extra.append("--keep-pie")
    if args.fuzz is not None:
        extra += ["--fuzz", str(args.fuzz)]

    exit_code = run_witness(
        beats=args.beats, session=args.session, budget_s=args.budget_s,
        close_editor_on_exit=args.close_editor_on_exit, extra_args=extra,
        agent_id=args.agent_id,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
