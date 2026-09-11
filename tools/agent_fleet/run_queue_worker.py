"""Authenticated worker-side queue loop.

The controller remains the authority. This module only reads snapshots and
requests claims; it never edits Git, SQLite, worktrees, or engine state.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import time
from typing import Callable


class WorkerQueue:
    def __init__(self, call: Callable[[str, dict], dict], *, agent: str, sleep=time.sleep):
        self.call = call
        self.agent = agent
        self.sleep = sleep

    def claim_once(self) -> dict | None:
        snapshot = self.call("snapshot", {})
        state = snapshot.get("result", snapshot)
        tasks = state["tasks"]
        identity = state["agents"].get(self.agent)
        if not identity or not identity.get("alive") or not identity.get("qualified"):
            raise ValueError("worker_identity_unavailable")
        owned = [t for t in tasks.values() if t.get("owner") == self.agent
                 and t.get("state") in ("RUNNING", "BLOCKED")]
        active = [t for t in tasks.values() if t.get('owner') == self.agent
                  and t.get('state') in ('RUNNING','BLOCKED','REVIEW','RECOVERY_HOLD')
                  and not (t.get('state') == 'REVIEW' and t.get('slot') is None and t.get('review_slot_handoffs'))]
        if owned and (any(t['state'] == 'RUNNING' for t in owned)
                      or len(active) >= identity.get('max_tasks',1)):
            task = sorted(owned, key=lambda t: (t['state'] != 'RUNNING', t['id']))[0]
            slot = state['slots'][str(task['slot'])]
            return {'task': task['id'], 'claim': {**task, 'worktree': slot['path'], 'engine': slot['engine']}}
        ready = sorted(
            (t for t in tasks.values() if t.get("state") == "READY"
             and set(t.get('capabilities',[])) <= set(identity.get('capabilities',[]))
             and all(tasks.get(d,{}).get('state') == 'INTEGRATED' for d in t.get('dependencies',[]))
             and (t.get('kind','worker') != 'integration' or self.agent == state.get('leader'))
             and (self.agent == state.get('leader') or 'docs/THE_MASTER_LIST.md' not in t.get('scopes',[]))),
            key=lambda t: (-int(t.get("priority", 5)), t["id"]),
        )
        refusals = []
        for task in ready:
            try:
                result = self.call("claim", {"task": task["id"]})
                return {"task": task["id"], "claim": result.get("result", result)}
            except Exception as exc:  # only named controller contention is recoverable
                if not self._claim_contention(exc):
                    raise
                refusals.append(f"{task['id']}:{type(exc).__name__}")
        return {"task": None, "refusals": refusals} if ready else None

    @staticmethod
    def _claim_contention(exc: Exception) -> bool:
        """Classify only expected claim races; never mask auth or transport errors."""
        message = str(exc)
        try:
            code = json.loads(message).get("error")
        except (ValueError, TypeError, AttributeError):
            code = message
        return code in {
            "task_not_ready", "no_free_slot", "write_scope_conflict",
            "dependencies_not_integrated", "capability_missing", "agent_capacity_reached",
            # A stale-provisioned free slot needs supervisor slot_rebind; skip
            # and retry later rather than crashing the worker loop.
            "stale_provision_requires_recovery",
        }

    def run_forever(self, *, poll_seconds: float = 5.0, max_cycles: int | None = None,
                    on_assignment: Callable[[dict], None] | None = None) -> None:
        if not math.isfinite(poll_seconds) or poll_seconds <= 0:
            raise ValueError("positive_finite_poll_required")
        if on_assignment is None:
            raise ValueError("executor_required_before_claim")
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            assignment = self.claim_once()
            if assignment is not None and assignment.get('task'):
                on_assignment(assignment)
            cycles += 1
            if max_cycles is None or cycles < max_cycles:
                self.sleep(poll_seconds)


class SessionLock:
    """OS lock survives pathname persistence; released only when its owner closes/exits."""
    def __init__(self, path):
        self.path = Path(path)
        self.handle = None

    def __enter__(self):
        self.handle = self.path.open('a+b')
        self.handle.seek(0, 2)
        if self.handle.tell() == 0:
            self.handle.write(b'0'); self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise ValueError('worker_already_running') from None
        return self

    def __exit__(self, *args):
        self.handle.close()


class CommandExecutor:
    """Run an explicit provider command; a zero exit alone never accepts a task."""
    def __init__(self, profile, call, agent, session_path):
        data = json.loads(Path(profile).read_text(encoding='utf-8'))
        argv = data.get('argv')
        if (not isinstance(argv, list) or not argv or
                not all(isinstance(x, str) and x for x in argv) or
                not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file()):
            raise ValueError('executor_command_required')
        self.argv, self.call, self.agent = argv, call, agent
        self.timeout = data.get('timeout_seconds', 900)
        if (isinstance(self.timeout, bool) or not isinstance(self.timeout, (int,float))
                or not math.isfinite(self.timeout) or self.timeout <= 0):
            raise ValueError('positive_finite_executor_timeout_required')
        self.session_path = str(Path(session_path).resolve())

    def __call__(self, assignment):
        claim = assignment['claim']
        if claim['state'] == 'BLOCKED' or not claim['engine'].get('provisioned'):
            return  # retain owned assignment and await supervised reconciliation
        state = self.call('snapshot', {})['result']
        task = state['tasks'][claim['id']]
        if (task['owner'], task['generation'], task['state']) != (self.agent, claim['generation'], 'RUNNING'):
            raise ValueError('execution_claim_changed')
        slot = state['slots'][str(task['slot'])]
        cwd = Path(slot['path']).resolve()
        if slot['task'] != task['id'] or not slot['engine'].get('provisioned'):
            raise ValueError('execution_slot_not_provisioned')
        def git(*args):
            return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()
        if git('branch', '--show-current') != task['branch']:
            raise ValueError('execution_branch_mismatch')
        recorded = slot['engine']['worktree_head']
        if subprocess.run(['git','-C',str(cwd),'merge-base','--is-ancestor',recorded,'HEAD'], capture_output=True).returncode:
            raise ValueError('execution_history_mismatch')
        prompt = {'task': task, 'generation': task['generation'], 'worktree': str(cwd),
                  'session_file': self.session_path,
                  'instruction': 'Read docs/AGENT_START.md and task contract. Complete only this owned milestone; '
                  'run actual tests, preserve evidence, push task branch and open PR targeting astra/gait-capture. '
                  'Submit exact Git-derived head using your own session, then end this invocation. '
                  'Do not claim another task, merge, weaken gates, use supervisor credentials or edit protected build artifacts.'}
        env = {k:v for k,v in os.environ.items() if k.upper() not in
               ('CHIMERA_FLEET_SUPERVISOR_TOKEN','CHIMERA_FLEET_ENROLLMENT_TOKEN')}
        kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
        # Bound the direct child. Descendants and resource drain still require
        # supervisor verification; never return this claim to READY on timeout.
        failure = None
        try:
            result = subprocess.run(self.argv, cwd=cwd, input=json.dumps(prompt), text=True,
                                    encoding='utf-8', env=env, timeout=self.timeout, **kwargs)
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            failure = 'executor_timeout_direct_child_reaped_descendant_drain_unverified'
            exit_code = None
        except OSError:
            failure = 'executor_launch_failed'
            exit_code = None
        after = self.call('snapshot', {})['result']['tasks'][task['id']]
        if after['owner'] != self.agent or after['generation'] != task['generation']:
            raise ValueError('execution_claim_changed')
        if after['state'] == 'RUNNING':
            self.call('checkpoint', {'task':task['id'], 'generation':task['generation'], 'state':'BLOCKED',
                      'checkpoint':f'executor_exit={exit_code}; failure={failure}; no submitted review. Preserve worktree; lead follow-up required.'})
        # REVIEW is still unaccepted and physical-slot handoff is a broker operation.


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--executor-profile", required=True)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    args = parser.parse_args()
    from client import call
    import json
    from pathlib import Path
    session = json.loads(Path(args.session).read_text(encoding="utf-8"))
    invoke = lambda op, values: call(session, op, values)
    executor = CommandExecutor(args.executor_profile, invoke, args.agent, args.session)
    worker = WorkerQueue(invoke, agent=args.agent)
    with SessionLock(str(Path(args.session).resolve()) + '.runner.lock'):
        worker.run_forever(poll_seconds=args.poll_seconds, on_assignment=executor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
