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
        return False, "LM Studio server unreachable (start LM Studio / lms server start — human or startup task)"
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


def main():
    parser = argparse.ArgumentParser(description="Self-healing blocker remediation (no-dead-ends law)")
    parser.add_argument("--ensure", choices=["editor", "lm", "pie", "all"], default=None)
    parser.add_argument("--check", action="store_true", help="probe only, never remediate")
    args = parser.parse_args()
    which = args.ensure or "all"
    checks = {"editor": ensure_editor, "lm": ensure_lm, "pie": ensure_no_pie}
    targets = list(checks) if which == "all" else [which]
    all_ok = True
    for t in targets:
        ok, note = checks[t](check_only=args.check)
        all_ok &= ok
        print(f"[unblock] {t}: {'OK' if ok else 'BLOCKED'} — {note}")
    print(f"[unblock] verdict: {'ALL CLEAR' if all_ok else 'residual blockers above — reroute to next candidate, do not halt'}")
    return 0  # never a fatal exit: reporting a blocker is work


if __name__ == "__main__":
    raise SystemExit(main())
