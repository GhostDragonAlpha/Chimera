"""Publication adapter: the ONLY code path that moves a task branch into the
integration base branch.

Supervisor-path tool (the trusted publisher); ordinary agent sessions never
invoke it. Executes a fetch-verified fast-forward push: never force, never
master, and the pushed head is re-read from the remote before any success is
reported. An interrupted integration is reconciled against actual remote state
before a retry, so a push that succeeded but was never acknowledged is
detected instead of repeated blindly.

Bypass disclosure: the prototype cannot technically prevent a human or agent
with direct GitHub credentials from pushing outside this adapter; that bypass
is documented and detected only after the fact by re-reading remote state.
"""
import argparse
import json
import re
import subprocess
import sys

BASE_BRANCH = 'astra/gait-capture'
FORBIDDEN = 'master'


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args],
                          capture_output=True, text=True)


def require(cond, reason, detail=''):
    if not cond:
        print(json.dumps({'published': False, 'refused': reason, 'detail': detail}))
        sys.exit(2)


def remote_head(repo, branch):
    cp = git(repo, 'ls-remote', 'origin', 'refs/heads/' + branch)
    require(cp.returncode == 0, 'ls_remote_failed', cp.stderr.strip())
    if not cp.stdout.strip():
        return None
    return cp.stdout.split()[0]


def rev(repo, obj):
    cp = git(repo, 'rev-parse', '--verify', obj + '^{commit}')
    require(cp.returncode == 0, 'unknown_commit', obj)
    return cp.stdout.strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True, help='checkout whose origin is the remote')
    p.add_argument('--task-branch', required=True)
    p.add_argument('--head', required=True, help='registry-recorded task head (40-hex)')
    p.add_argument('--expected-base', required=True,
                   help='registry-recorded base the task branched from')
    p.add_argument('--reconcile-only', action='store_true',
                   help='report actual remote state without pushing')
    a = p.parse_args()

    require(bool(re.fullmatch('[0-9a-f]{40}', a.head)), 'invalid_head')
    require(bool(re.fullmatch('[0-9a-f]{40}', a.expected_base)), 'invalid_expected_base')
    require(a.task_branch != FORBIDDEN and a.task_branch.startswith('astra/'),
            'forbidden_branch')

    # 1. Re-read the actual remote before deciding anything.
    require(git(a.repo, 'fetch', 'origin').returncode == 0, 'fetch_failed')
    base_remote = remote_head(a.repo, BASE_BRANCH)
    require(base_remote is not None, 'base_branch_missing_remote')
    task_remote = remote_head(a.repo, a.task_branch)

    # 2. Identity gate: the remote task branch must equal the registry head.
    require(task_remote == a.head, 'task_head_mismatch_remote',
            'remote task branch is ' + str(task_remote))

    # 3. Interrupted-integration reconciliation: already merged? (This comes
    #    before base-rewrite detection: legitimate integrations advance the
    #    base, and an already-merged task must report as such, not as refusal.)
    if git(a.repo, 'merge-base', '--is-ancestor', a.head, base_remote).returncode == 0:
        print(json.dumps({'published': True, 'already_integrated': True,
                          'verified_remote_head': base_remote,
                          'base_before': base_remote, 'pushed_head': a.head}))
        return

    if a.reconcile_only:
        print(json.dumps({'published': False, 'not_integrated': True,
                          'verified_remote_head': base_remote}))
        sys.exit(3)

    # 4. The registry base must still be part of the remote base history
    #    (the base was never rewritten since the task forked).
    require(git(a.repo, 'merge-base', '--is-ancestor',
                a.expected_base, base_remote).returncode == 0,
            'base_rewritten_since_task_fork')

    # 5. Fast-forward proof at the remote heads: merge-base(base, head) must
    #    be the base itself. Otherwise the base diverged (legitimate
    #    integrations landed) and the task must be rebased, not forced.
    mb = git(a.repo, 'merge-base', base_remote, a.head)
    require(mb.returncode == 0, 'unrelated_histories')
    require(mb.stdout.strip() == base_remote, 'non_fast_forward_refused',
            'base has diverged; rebase the task branch instead')

    # 6. Materialize the task head as a local tracking ref, then push that
    #    exact object to the base branch. No local branch is created or
    #    moved; git itself refuses a non-FF push without '+'.
    cp = git(a.repo, 'fetch', 'origin',
             'refs/heads/' + a.task_branch +
             ':refs/remotes/origin/' + a.task_branch)
    require(cp.returncode == 0, 'task_fetch_failed', cp.stderr.strip())
    local = rev(a.repo, 'refs/remotes/origin/' + a.task_branch)
    require(local == a.head, 'fetched_head_identity', local)
    cp = git(a.repo, 'push', 'origin',
             'refs/remotes/origin/' + a.task_branch +
             ':refs/heads/' + BASE_BRANCH)
    require(cp.returncode == 0, 'push_refused', cp.stderr.strip())

    # 7. Verify by re-reading the remote; success requires the pushed head.
    verified = remote_head(a.repo, BASE_BRANCH)
    require(verified == a.head, 'verification_failed_after_push',
            'remote base is ' + str(verified))
    print(json.dumps({'published': True, 'already_integrated': False,
                      'base_before': base_remote, 'pushed_head': a.head,
                      'verified_remote_head': verified}))


if __name__ == '__main__':
    main()
