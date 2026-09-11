"""Trusted enrollment/qualification launcher for one queue worker."""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
from typing import Callable

def load_secrets(path: Path | None) -> tuple[str, str]:
    if path is not None:
        data = json.loads(path.read_text(encoding="utf-8"))
        supervisor, enrollment = data.get("supervisor_token", ""), data.get("enrollment_token", "")
    else:
        supervisor = os.environ.get("CHIMERA_FLEET_SUPERVISOR_TOKEN", "")
        enrollment = os.environ.get("CHIMERA_FLEET_ENROLLMENT_TOKEN", "")
    if not supervisor or not enrollment or supervisor == enrollment:
        raise ValueError("distinct_launcher_secrets_required")
    return supervisor, enrollment

def launch_worker(*, endpoint: str, agent: str, label: str, session_path: Path,
                  supervisor_token: str, enrollment_token: str, capabilities: list[str],
                  max_tasks: int = 1, worker_script: Path, python_exe: str = sys.executable,
                  enroll_runner: Callable[..., None] | None = None,
                  qualify_call: Callable[..., dict] | None = None,
                  process_runner: Callable[..., object] | None = None) -> object:
    if session_path.exists(): raise ValueError("session_path_already_exists")
    if not agent or not label or not capabilities or max_tasks < 1: raise ValueError("invalid_worker_profile")
    if not supervisor_token or not enrollment_token or supervisor_token == enrollment_token:
        raise ValueError("distinct_launcher_secrets_required")
    enroll_runner = enroll_runner or _enroll
    qualify_call = qualify_call or _qualify
    process_runner = process_runner or subprocess.Popen
    enroll_runner(endpoint, agent, label, session_path, enrollment_token)
    qualify_call(endpoint, supervisor_token, agent, capabilities, max_tasks)
    child_env = dict(os.environ)
    child_env.pop("CHIMERA_FLEET_SUPERVISOR_TOKEN", None)
    child_env.pop("CHIMERA_FLEET_ENROLLMENT_TOKEN", None)
    return process_runner([python_exe, str(worker_script), "--session", str(session_path)], env=child_env)

def _enroll(endpoint, agent, label, session_path, enrollment_token):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CHIMERA_FLEET_SUPERVISOR_TOKEN", "CHIMERA_FLEET_ENROLLMENT_TOKEN")}
    env["CHIMERA_FLEET_ENROLLMENT_TOKEN"] = enrollment_token
    cmd = [sys.executable, str(Path(__file__).with_name("enroll_agent.py")), "--endpoint", endpoint,
           "--agent", agent, "--label", label, "--out", str(session_path)]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if result.returncode: raise RuntimeError("enrollment_failed")

def _qualify(endpoint, supervisor_token, agent, capabilities, max_tasks):
    from client import call
    return call({"endpoint": endpoint, "token": supervisor_token}, "qualify", {
        "agent": agent, "capabilities": capabilities, "max_tasks": max_tasks,
        "can_lead": False, "rank": 0, "evidence": "trusted launcher qualification"})

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--endpoint", required=True); p.add_argument("--agent", required=True)
    p.add_argument("--label", required=True); p.add_argument("--out", required=True, type=Path)
    p.add_argument("--worker-script", type=Path, default=Path(__file__).with_name("run_queue_worker.py"))
    p.add_argument("--secrets-file", type=Path); p.add_argument("--max-tasks", type=int, default=1)
    a = p.parse_args()
    try:
        sup, enr = load_secrets(a.secrets_file)
        launch_worker(endpoint=a.endpoint, agent=a.agent, label=a.label, session_path=a.out,
                      supervisor_token=sup, enrollment_token=enr,
                      capabilities=["cpu", "docs", "evidence", "git", "python"],
                      max_tasks=a.max_tasks, worker_script=a.worker_script)
        print(json.dumps({"launched": a.agent, "session_file": str(a.out)}), flush=True); return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print("REFUSED: " + str(exc), file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
