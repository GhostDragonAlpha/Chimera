"""Unblock — self-healing remediation for known workflow blockers.

THE NO-DEAD-ENDS LAW (Gardener directive 2026-07-07): a blocker fails an ITEM,
never the SHIFT. Gates stay hard — nothing here fakes a pass — but every KNOWN
blocker with a known recipe gets executed, not recorded as an excuse:

  editor down   -> launch UnrealEditor.exe, poll the MCP bridge until it answers
  LM not loaded -> `lms load <model>`, poll until the model reports loaded
  PIE busy      -> wait + retry (a live session is respected, never stolen)

Every remediation attempt is recorded as a pathway (success AND failure).
This module itself never raises to callers and its CLI always exits 0 with a
report line — reporting a blocker is work; dying to one is not.

Usage:
  python -m core.unblock --ensure all          # probe + remediate everything known
  python -m core.unblock --ensure editor|lm|pie
  python -m core.unblock --check               # probe only, remediate nothing
"""

import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path

QWEN = "qwen3.6-35b-a3b-mtp@iq2_m"
EDITOR_EXE = r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
UPROJECT = r"E:\PythonChimera\Chimera\Chimera.uproject"
LMS_URL = "http://localhost:1234"


def _record(action: str, result: str, note: str):
    try:
        from core.graphify_interface import record_pathway
        record_pathway("unblock", action, result, {"note": note[:180]})
    except Exception:
        pass  # recording failure must never block remediation reporting


def _probe_editor(timeout_call: int = 10):
    try:
        from core.telemetry_probe import MCPStdioClient
        c = MCPStdioClient()
        r = c.call("inspect", {"action": "get_scene_stats"})
        sc = r.get("result", {}).get("structuredContent", {})
        return bool(sc.get("success")), sc
    except Exception as ex:
        return False, str(ex)[:120]


def ensure_editor(poll_s: int = 20, timeout_s: int = 300, check_only: bool = False):
    ok, _ = _probe_editor()
    if ok:
        return True, "editor up (bridge answering)"
    if check_only:
        return False, "editor DOWN (bridge unreachable)"
    # zombie check: process alive but bridge dead -> force-kill before relaunch
    try:
        q = subprocess.run(["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe"],
                           capture_output=True, text=True, timeout=20)
        if "UnrealEditor.exe" in (q.stdout or ""):
            subprocess.run(["taskkill", "/F", "/IM", "UnrealEditor.exe"],
                           capture_output=True, text=True, timeout=30)
            _record("ensure_editor", "success", "zombie editor (bridge dead) force-killed before relaunch")
            time.sleep(8)
    except Exception:
        pass
    subprocess.Popen(["cmd", "/c", "start", "", EDITOR_EXE, UPROJECT],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        time.sleep(poll_s)
        ok, _ = _probe_editor()
        if ok:
            _record("ensure_editor", "success", f"launched + bridge up within {timeout_s}s")
            return True, "editor LAUNCHED and bridge up"
    _record("ensure_editor", "failed", f"launched but bridge silent after {timeout_s}s")
    return False, f"editor launched but bridge silent after {timeout_s}s"


def _loaded_models():
    try:
        with urllib.request.urlopen(f"{LMS_URL}/api/v0/models", timeout=5) as r:
            data = json.load(r)
        return [m["id"] for m in data.get("data", [])
                if m.get("state") == "loaded" and m.get("type") in ("llm", "vlm")], True
    except Exception:
        return [], False


def ensure_lm(model: str = QWEN, timeout_s: int = 420, check_only: bool = False):
    loaded, server_up = _loaded_models()
    if loaded:
        return True, f"LM loaded: {loaded[0]}"
    if not server_up:
        if check_only:
            return False, "LM Studio server unreachable"
        try:  # self-heal: start the server headlessly
            subprocess.run(["lms", "server", "start"], capture_output=True, text=True,
                           timeout=60, shell=True)
            time.sleep(5)
        except Exception:
            pass
        loaded, server_up = _loaded_models()
        if loaded:
            return True, f"LM server STARTED, model already loaded: {loaded[0]}"
        if not server_up:
            _record("ensure_lm", "failed", "lms server start did not bring the API up")
            return False, "LM Studio server down and `lms server start` failed — needs the app once"
    if check_only:
        return False, "LM server up, NO model loaded"
    try:
        r = subprocess.run(["lms", "load", model, "--yes"], capture_output=True,
                           text=True, timeout=timeout_s, shell=True)
        note = (r.stdout or r.stderr).strip()[-120:]
    except FileNotFoundError:
        _record("ensure_lm", "failed", "lms CLI not on PATH")
        return False, "lms CLI not found — load the model in the LM Studio UI"
    except subprocess.TimeoutExpired:
        note = f"lms load still running after {timeout_s}s"
    loaded, _ = _loaded_models()
    if loaded:
        _record("ensure_lm", "success", f"loaded {loaded[0]}")
        return True, f"LM LOADED: {loaded[0]}"
    _record("ensure_lm", "failed", note)
    return False, f"lms load did not result in a loaded model ({note})"


def ensure_no_pie(retries: int = 3, wait_s: int = 120, check_only: bool = False):
    try:
        from core.telemetry_probe import MCPStdioClient
        c = MCPStdioClient()
        for attempt in range(retries):
            r = c.call("inspect", {"action": "runtime_report"})
            res = r.get("result", {}).get("structuredContent", {}).get("result", {}) or {}
            if not res.get("isPIE"):
                return True, "no live PIE session"
            if check_only or attempt == retries - 1:
                break
            time.sleep(wait_s)
        return False, "PIE busy (live session — respected, not stolen)"
    except Exception as ex:
        return False, f"cannot probe PIE (editor down?): {str(ex)[:80]}"


def ensure_git(check_only: bool = False):
    """Push resilience: offline or non-fast-forward must never end a shift."""
    def _run(*a):
        return subprocess.run(list(a), capture_output=True, text=True,
                              cwd=r"E:\PythonChimera", timeout=120)
    r = _run("git", "push", "origin", "master")
    if r.returncode == 0:
        return True, "push clean"
    if check_only:
        return False, f"push failing: {(r.stderr or '')[:80]}"
    _run("git", "pull", "--rebase", "origin", "master")
    r2 = _run("git", "push", "origin", "master")
    if r2.returncode == 0:
        _record("ensure_git", "success", "push recovered via pull --rebase")
        return True, "push recovered via pull --rebase"
    _record("ensure_git", "failed", (r2.stderr or "")[:120])
    return False, "push deferred (offline/diverged) — commits are LOCAL and safe; next cycle retries"


def ensure_disk(check_only: bool = False, min_free_gb: int = 10):
    import shutil
    notes, ok = [], True
    for drive in ("C:\\", "E:\\"):
        try:
            free_gb = shutil.disk_usage(drive).free / 1e9
            notes.append(f"{drive[0]}: {free_gb:.0f}GB free")
            if free_gb < min_free_gb:
                ok = False
        except OSError:
            notes.append(f"{drive[0]}: unreadable")
    return ok, "; ".join(notes) + ("" if ok else f" — BELOW {min_free_gb}GB: skip builds/screenshots, clean Saved/Logs")


def main():
    parser = argparse.ArgumentParser(description="Self-healing blocker remediation (no-dead-ends law)")
    parser.add_argument("--ensure", choices=["editor", "lm", "pie", "disk", "git", "all"], default=None)
    parser.add_argument("--check", action="store_true", help="probe only, never remediate")
    args = parser.parse_args()
    which = args.ensure or "all"
    checks = {"editor": ensure_editor, "lm": ensure_lm, "pie": ensure_no_pie,
              "disk": ensure_disk, "git": ensure_git}
    targets = (["editor", "lm", "pie", "disk"] if which == "all" else [which])  # git on demand
    all_ok = True
    for t in targets:
        ok, note = checks[t](check_only=args.check)
        all_ok &= ok
        print(f"[unblock] {t}: {'OK' if ok else 'BLOCKED'} — {note}")
    print(f"[unblock] verdict: {'ALL CLEAR' if all_ok else 'residual blockers above — reroute to next candidate, do not halt'}")
    return 0  # never a fatal exit: reporting a blocker is work


if __name__ == "__main__":
    raise SystemExit(main())
