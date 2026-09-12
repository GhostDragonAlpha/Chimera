"""Slot provisioning: bind a real worktree to a registry claim, or verify it.

Supervisor/lead-path tool. The registry claim alone creates nothing; this tool
is the only supported provisioner and refuses unless the control plane agrees
(RUNNING task, matching slot, unprovisioned engine). `create` adds a worktree
on the task's recorded base and branch; `verify` checks an existing worktree's
HEAD and branch against the claim. Never touches protected build paths.
"""
import argparse
import json
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args],
                          capture_output=True, text=True)


def fail(reason, detail=''):
    print(json.dumps({'provisioned': False, 'refused': reason, 'detail': detail}))
    sys.exit(2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['create', 'verify'])
    p.add_argument('--repo', required=True, help='primary checkout to branch from')
    p.add_argument('--worktree', required=True, help='slot worktree path')
    p.add_argument('--task', required=True)
    p.add_argument('--branch', required=True)
    p.add_argument('--base', required=True, help='registry-recorded task base (40-hex)')
    a = p.parse_args()

    import re
    if not re.fullmatch('[0-9a-f]{40}', a.base):
        fail('invalid_base')
    if not a.branch.startswith('astra/tasks/'):
        fail('invalid_task_branch')

    if a.mode == 'create':
        if a.branch == 'astra/gait-capture' or a.branch == 'master':
            fail('forbidden_branch')
        cp = git(a.repo, 'rev-parse', '--verify', '--quiet', a.base + '^{commit}')
        if cp.returncode != 0:
            fail('unknown_base_commit')
        cp = git(a.repo, 'rev-parse', '--verify', '--quiet', 'refs/heads/' + a.branch)
        if cp.returncode == 0:
            fail('branch_already_exists', 'no task-branch reuse; pick a new task id')
        wt = subprocess.run(['git', '-C', a.worktree, 'rev-parse', '--git-dir'],
                            capture_output=True, text=True)
        if wt.returncode == 0:
            fail('worktree_path_already_a_repo')
        cp = git(a.repo, 'worktree', 'add', '-b', a.branch, a.worktree, a.base)
        if cp.returncode != 0:
            fail('worktree_add_failed', cp.stderr.strip())
        head = git(a.worktree, 'rev-parse', 'HEAD').stdout.strip()
        print(json.dumps({'provisioned': True, 'mode': 'create',
                          'worktree': a.worktree, 'branch': a.branch,
                          'head': head, 'base': a.base}))
        return

    # verify: HEAD and branch must match the claim.
    cp = git(a.worktree, 'rev-parse', '--verify', 'HEAD')
    if cp.returncode != 0:
        fail('worktree_not_a_repo')
    head = cp.stdout.strip()
    cp = git(a.worktree, 'rev-parse', '--abbrev-ref', 'HEAD')
    branch = cp.stdout.strip()
    if branch != a.branch:
        fail('worktree_branch_mismatch', branch)
    print(json.dumps({'provisioned': True, 'mode': 'verify',
                      'worktree': a.worktree, 'branch': branch, 'head': head}))


if __name__ == '__main__':
    main()
