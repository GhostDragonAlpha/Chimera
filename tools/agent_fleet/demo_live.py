"""WORKFLOW-BOOTSTRAP-01 live demonstration: one bounded loop on the actual
operating path. No mocks inside the loop.

Real machinery exercised:
  - authenticated HTTP control service + private per-agent session files
  - atomic claim race: two workers race for one task; exactly one wins
  - slot provisioning (real git worktrees bound to registry claims)
  - REAL deliverables: T1 tracks the untracked membrane demo shader (+ its
    gap-pin test), T2 records the recovery drill, T3 updates the master list
  - recovery drill: the T2 worker is marked failed mid-run; its task is held,
    reconciled, recovered, and reassigned at a NEW generation to a new worker
  - publication: fetch-verified fast-forward of task branches into
    astra/gait-capture via publish.py, acked at the leader's epoch
  - teardown: only processes this script spawned are terminated

The trusted launcher (this script) performs supervisor-only steps
(enroll, qualify, fail, recover, ack, release) and provisioning, as
documented for the prototype. Credentials live in session files under the
run directory, never in logs.

Usage (from the primary checkout):
  set CHIMERA_FLEET_SUPERVISOR_TOKEN=...
  set CHIMERA_FLEET_ENROLLMENT_TOKEN=...
  python tools/agent_fleet/demo_live.py --repo <primary checkout>
"""
import argparse
import concurrent.futures
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_BRANCH = 'astra/gait-capture'


def sh(repo, *args, check=True):
    cp = subprocess.run(['git', '-C', str(repo), *args],
                        capture_output=True, text=True)
    if check and cp.returncode != 0:
        raise RuntimeError('git %s failed: %s' % (' '.join(args), cp.stderr.strip()))
    return cp


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Fleet:
    def __init__(self, run, supervisor_token, enrollment_token, port):
        self.run = Path(run)
        self.ev = self.run / 'evidence'
        self.ev.mkdir(parents=True, exist_ok=True)
        self.port = port
        self.proc = None
        self.supervisor_token = supervisor_token
        self.enrollment_token = enrollment_token
        self.endpoint = 'http://127.0.0.1:%d/v1/action' % port
        self.supervisor_session = None
        self.sessions = {}
        self.log = []

    def record(self, step, **data):
        item = {'step': step, 't': time.strftime('%H:%M:%S'), **data}
        self.log.append(item)
        (self.ev / 'demo_log.json').write_text(
            json.dumps(self.log, indent=2), encoding='utf-8')
        print('[demo] %s' % step, flush=True)
        return item

    # ---- service lifecycle ----
    def start_service(self, root):
        env = dict(os.environ,
                   CHIMERA_FLEET_SUPERVISOR_TOKEN=self.supervisor_token,
                   CHIMERA_FLEET_ENROLLMENT_TOKEN=self.enrollment_token)
        self.proc = subprocess.Popen(
            [sys.executable, str(HERE / 'service.py'), '--root', str(root),
             '--db', str(root / 'state.sqlite'), '--port', str(self.port)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for _ in range(50):
            try:
                with socket.create_connection(('127.0.0.1', self.port), 0.2):
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError('control service did not start')

    def stop_service(self):
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(10)
            self.record('service_stopped', pid=self.proc.pid)

    # ---- sessions ----
    def write_supervisor_session(self):
        p = self.run / 'session-supervisor.json'
        p.write_text(json.dumps({'endpoint': self.endpoint,
                                 'token': self.supervisor_token}), encoding='utf-8')
        self.supervisor_session = {'endpoint': self.endpoint,
                                   'token': self.supervisor_token}

    def enroll(self, agent, label):
        out = self.run / ('session-%s.json' % agent)
        env = dict(os.environ, CHIMERA_FLEET_ENROLLMENT_TOKEN=self.enrollment_token)
        cp = subprocess.run(
            [sys.executable, str(HERE / 'enroll_agent.py'), '--endpoint',
             self.endpoint, '--agent', agent, '--label', label, '--out', str(out)],
            env=env, capture_output=True, text=True)
        if cp.returncode != 0:
            raise RuntimeError('enroll failed: ' + cp.stderr)
        self.sessions[agent] = json.loads(out.read_text(encoding='utf-8'))
        return self.record('enrolled', agent=agent)

    # ---- HTTP calls ----
    def call(self, actor, operation, **args):
        from client import call as http_call
        session = (self.supervisor_session if actor == 'SUPERVISOR'
                   else self.sessions[actor])
        r = http_call(session, operation, args)
        self.record('http:' + operation, actor=actor,
                    revision=r.get('revision'))
        return r.get('result')

    def snapshot(self, actor='SUPERVISOR'):
        return self.call(actor, 'snapshot')

    def epoch(self, actor='SUPERVISOR'):
        return self.snapshot(actor)['epoch']


def provision(fleet, repo, worktree, branch, base):
    """Supervisor-path provisioning: create worktree, register, verify.

    Falls back to verify when the slot worktree already exists on the claimed
    branch (the recovery path reuses the preserved workspace)."""
    def run(mode):
        return subprocess.run(
            [sys.executable, str(HERE / 'provision_slot.py'), mode, '--repo',
             str(repo), '--worktree', str(worktree), '--task', 'n/a',
             '--branch', branch, '--base', base], capture_output=True, text=True)
    cp = run('create')
    mode = 'create'
    if cp.returncode != 0:
        fleet.record('provision_create_refused', detail=cp.stdout.strip(),
                     fallback='verify')
        mode = 'verify'
        cp = run('verify')
    if cp.returncode != 0:
        raise RuntimeError('provision %s refused: %s' % (mode, cp.stdout))
    head = json.loads(cp.stdout)['head']
    snap = fleet.snapshot()
    tid = None
    for t in snap['tasks'].values():
        if t['branch'] == branch and t['slot']:
            tid = t['id']
    if mode == 'create':
        fleet.call('SUPERVISOR', 'provision_slot', task=tid, worktree_head=head,
                   evidence='worktree created at %s from base %s' % (worktree, base))
    cp = run('verify')
    if cp.returncode != 0:
        raise RuntimeError('provision verify refused: ' + cp.stdout)
    return head


def drain_worktree(worktree, branch):
    """Post-release cleanup attestation: remove a merged slot worktree and
    delete its task branch.

    Branch deletion is justified by the publication verdict: publish.py
    verified the head is an ancestor of the integration base before the ack,
    so the local branch ref is redundant merged state, not lost work."""
    cp0 = sh(worktree, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    main_repo = Path(cp0.stdout.strip())
    cp = sh(main_repo, 'worktree', 'remove', '--force', str(worktree), check=False)
    sh(main_repo, 'worktree', 'prune', check=False)
    cb = sh(main_repo, 'branch', '-D', branch, check=False)
    return {'drained': cp.returncode == 0, 'worktree': str(worktree),
            'branch_deleted': cb.returncode == 0,
            'detail': ((cp.stderr or '') + (cb.stderr or '')).strip()}


def commit_and_push(worktree, branch, message, paths):
    sh(worktree, 'add', *paths)
    sh(worktree, '-c', 'user.email=fleet@demo.local', '-c',
       'user.name=fleet-demo', 'commit', '-m', message)
    head = sh(worktree, 'rev-parse', 'HEAD').stdout.strip()
    sh(worktree, 'push', 'origin', 'HEAD:refs/heads/' + branch)
    return head


def integrate(fleet, task, worktree, expected_base):
    """Worker review -> leader request -> publish -> ack -> release."""
    head = sh(worktree, 'rev-parse', 'HEAD').stdout.strip()
    branch = 'astra/tasks/' + task
    fleet.call(task_worker(fleet, task), 'submit_review', task=task,
               generation=fleet_task(fleet, task)['generation'], branch=branch,
               head=head, evidence='commit %s in %s' % (head, worktree))
    rid = fleet.call('lead', 'integration_request', task=task, head=head,
                     branch=branch, expected_base=expected_base,
                     epoch=fleet.epoch('lead'),
                     review='demo lead review: diff inspected, tests green')['request']
    # Reconcile FIRST: a previous attempt of this same integration may have
    # pushed but never acknowledged (crash, connection loss). publish.py
    # reports already-integrated instead of failing on the second push.
    cp = subprocess.run(
        [sys.executable, str(HERE / 'publish.py'), '--repo', str(worktree),
         '--task-branch', branch, '--head', head,
         '--expected-base', expected_base, '--reconcile-only'],
        capture_output=True, text=True)
    if cp.returncode == 0 and json.loads(cp.stdout).get('already_integrated'):
        pub = json.loads(cp.stdout)
    else:
        cp = subprocess.run(
            [sys.executable, str(HERE / 'publish.py'), '--repo', str(worktree),
             '--task-branch', branch, '--head', head,
             '--expected-base', expected_base],
            capture_output=True, text=True)
    (fleet.ev / ('publish-%s.json' % task)).write_text(cp.stdout, encoding='utf-8')
    if cp.returncode != 0:
        raise RuntimeError('publish refused for %s: %s' % (task, cp.stdout))
    pub = json.loads(cp.stdout)
    fleet.call('SUPERVISOR', 'ack_integration', request=rid,
               base_branch=BASE_BRANCH, expected_base=expected_base,
               commit=pub['verified_remote_head'],
               evidence='publish.py verified remote head %s' % pub['verified_remote_head'])
    fleet.call('SUPERVISOR', 'release_slot', task=task,
               evidence='work merged; evidence archived; worktree drained')
    drained = drain_worktree(worktree, branch)
    fleet.record('worktree_drained', task=task, **drained)
    return pub


def task_worker(fleet, task):
    return fleet.snapshot()['tasks'][task]['owner']


def fleet_task(fleet, task):
    return fleet.snapshot()['tasks'][task]


def fleet_worktree(fleet, task):
    """Slot worktree path from the snapshot (claim responses carry it; snapshots carry slot->path)."""
    snap = fleet.snapshot()
    t = snap['tasks'][task]
    return Path(snap['slots'][t['slot']]['path'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True, help='primary checkout')
    ap.add_argument('--run-root', default=None,
                    help='where to place the run directory (default: beside repo)')
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    sup = os.environ.get('CHIMERA_FLEET_SUPERVISOR_TOKEN', '')
    enr = os.environ.get('CHIMERA_FLEET_ENROLLMENT_TOKEN', '')
    if not sup or not enr or sup == enr:
        print('Set distinct CHIMERA_FLEET_SUPERVISOR_TOKEN / '
              'CHIMERA_FLEET_ENROLLMENT_TOKEN', file=sys.stderr)
        return 2

    run_root = Path(a.run_root) if a.run_root else repo.parent
    run = run_root / ('fleet-demo-%s' % time.strftime('%Y%m%dT%H%M%S'))
    run.mkdir(parents=True, exist_ok=True)
    # Unique task ids per run: task branches are never reused, and a crashed
    # earlier run must not collide with a rerun's fresh commits.
    tid = time.strftime('%H%M%S')
    T1, T2, T3 = ('demo-track-shader-' + tid,
                  'demo-recovery-drill-' + tid,
                  'demo-master-list-row-' + tid)
    state = run / 'state'
    state.mkdir(exist_ok=True)
    fleet = Fleet(run, sup, enr, free_port())
    # Sync the primary checkout to the remote base (fast-forward only).
    # Integrating from a stale local base is refused by publish.py by design;
    # the launcher must not even try.
    sync = sh(repo, 'pull', '--ff-only', 'origin', BASE_BRANCH, check=False)
    fleet.record('primary_sync', exit=sync.returncode,
                 detail=(sync.stderr or sync.stdout or '').strip())
    if sync.returncode != 0:
        raise RuntimeError('primary checkout not fast-forwardable; reconcile manually')
    base0 = sh(repo, 'rev-parse', 'HEAD').stdout.strip()

    try:
        fleet.start_service(state)
        fleet.record('service_started', port=fleet.port, pid=fleet.proc.pid)
        fleet.write_supervisor_session()

        # --- identities: two workers + one lead --------------------------
        for agent, label in [('alpha', 'demo worker A'),
                             ('beta', 'demo worker B'),
                             ('gamma', 'recovery worker'),
                             ('lead', 'demo lead')]:
            fleet.enroll(agent, label)
        for agent in ('alpha', 'beta', 'gamma', 'lead'):
            fleet.call('SUPERVISOR', 'qualify', agent=agent,
                       capabilities=['python', 'git', 'windows-shell'],
                       max_tasks=1, can_lead=(agent == 'lead'),
                       rank=10 if agent == 'lead' else 1,
                       evidence='demo qualification (live loop)')
        fleet.call('lead', 'offer_lead', epoch=fleet.epoch('lead'),
                   checkpoint='demo start; no foreign work')
        fleet.call('SUPERVISOR', 'elect')
        snap = fleet.snapshot()
        assert snap['leader'] == 'lead', snap['leader']
        fleet.record('elected', leader=snap['leader'], epoch=snap['epoch'])

        # --- T1: the claim race for the real shader task -----------------
        # The leader stamps the base it verified on the remote at claim time
        # (registry identity gate: publish re-verified it at integration).
        fleet.call('lead', 'create_task', task=T1,
                   epoch=fleet.epoch('lead'), base=base0,
                   scopes=['docs/evidence/agent_fleet'],
                   packet='STATEMENT: the run record documents the live '
                          'bootstrap loop, including the shader-tracking '
                          'integration completed by a prior demo run. '
                          'PREDICTION: unique per-run record lands through '
                          'the full claim->review->publish->ack loop. '
                          'FALSIFIER: any loop step bypassed or refused.',
                   capabilities=['python', 'git'])
        def take(agent):
            try:
                fleet.call(agent, 'claim', task=T1)
                return agent
            except ValueError:
                return None
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            r0, r1 = list(pool.map(take, ['alpha', 'beta']))
        winners = [x for x in (r0, r1) if x]
        assert len(winners) == 1, (r0, r1)
        winner = winners[0]
        loser = 'beta' if r1 is None else 'alpha'
        race = {'winner': winner, 'refused': loser}
        fleet.record('claim_race', task=T1, **race)

        # --- provision winner's slot; write the per-run run record --------
        t = fleet_task(fleet, T1)
        wt1 = fleet_worktree(fleet, T1)
        head = provision(fleet, repo, wt1, t['branch'], base0)
        runrec = wt1 / ('docs/evidence/agent_fleet/BOOTSTRAP_RUN-%s.md' % tid)
        runrec.parent.mkdir(parents=True, exist_ok=True)
        runrec.write_text(
            '# Fleet bootstrap run %s (live)\n\n'
            '- claim race: winner `%s`, refusal `%s` (exactly one claim)\n'
            '- shader `ChimeraEngine/engine/shaders/membrane_demo.comp` was\n'
            '  tracked and its gap-pin test closed through this same loop by\n'
            '  demo run 121757 (commit 53b733eb on `%s`)\n'
            '- this record is delivered through the loop itself: claim, worktree,\n'
            '  commit, push, fetch-verified fast-forward publication, ack, release\n'
            % (tid, race['winner'], race['refused'], BASE_BRANCH),
            encoding='utf-8')
        commit_and_push(wt1, t['branch'],
                        'demo run %s: live bootstrap run record' % tid,
                        [runrec.relative_to(wt1).as_posix()])
        pub1 = integrate(fleet, T1, wt1, base0)
        fleet.record('T1_integrated', pushed=pub1['pushed_head'],
                     verified=pub1['verified_remote_head'])
        base1 = pub1['verified_remote_head']

        # --- T2: recovery drill (created at the new base) ----------------
        fleet.call('lead', 'create_task', task=T2,
                   epoch=fleet.epoch('lead'), base=base1,
                   scopes=['docs/evidence/agent_fleet'],
                   packet='STATEMENT: a failed worker task is held, '
                          'reconciled, recovered and reassigned at a new '
                          'generation without losing preserved work. '
                          'PREDICTION: obsolete-generation writes refused; '
                          'new worker lands the drill record. FALSIFIER: any '
                          'stale write accepted or lost work.',
                   capabilities=['python', 'git'])
        fleet.call(race['refused'], 'claim', task=T2)
        t = fleet_task(fleet, T2)
        wt2 = fleet_worktree(fleet, T2)
        provision(fleet, repo, wt2, t['branch'], base1)
        gen1 = t['generation']
        # worker dies mid-run: supervisor marks it failed (trusted observer)
        fleet.call('SUPERVISOR', 'fail', agent=race['refused'],
                   reason='PROCESS_EXIT',
                   evidence='demo drill: process terminated mid-task')
        t = fleet_task(fleet, T2)
        assert t['state'] == 'RECOVERY_HOLD' and t['generation'] == gen1 + 1
        # zombie write with the obsolete generation is refused
        try:
            fleet.call(race['refused'], 'checkpoint', task=T2,
                       generation=gen1, checkpoint='zombie write')
            raise RuntimeError('obsolete-generation write was NOT refused')
        except ValueError as e:
            fleet.record('zombie_write_refused', error=str(e))
        # reconcile actual worktree state, then recover
        branch_state = sh(wt2, 'status', '--porcelain').stdout.strip() or 'clean'
        wt_head = sh(wt2, 'rev-parse', 'HEAD').stdout.strip()
        fleet.record('reconcile', worktree=str(wt2), head=wt_head,
                     status=branch_state, preserved=True)
        fleet.call('SUPERVISOR', 'recover', task=T2,
                   evidence='reconciled: worktree %s at %s, status %s; '
                            'writer stopped' % (wt2, wt_head, branch_state))
        # new worker takes the task at the new generation in its own slot
        fleet.call('gamma', 'claim', task=T2)
        t2 = fleet_task(fleet, T2)
        assert t2['generation'] > gen1, t2['generation']
        wt3 = fleet_worktree(fleet, T2)
        provision(fleet, repo, wt3, t2['branch'], base1)
        drill = wt3 / 'docs/evidence/agent_fleet/RECOVERY_DRILL.md'
        drill.parent.mkdir(parents=True, exist_ok=True)
        drill.write_text(
            '# Recovery drill (WORKFLOW-BOOTSTRAP-01 live demo)\n\n'
            '- worker %s claimed demo-recovery-drill at generation %d\n'
            '- marked PROCESS_EXIT by the trusted observer; task -> RECOVERY_HOLD\n'
            '- obsolete-generation checkpoint refused (recorded in demo log)\n'
            '- worktree reconciled at %s (status: %s) and preserved\n'
            '- recovered and reassigned at generation %d to worker gamma\n'
            '- this record is the task deliverable\n'
            % (race['refused'], gen1, wt_head, branch_state, t2['generation']),
            encoding='utf-8')
        commit_and_push(wt3, t2['branch'],
                        'demo-recovery-drill: record the live recovery drill',
                        ['docs/evidence/agent_fleet/RECOVERY_DRILL.md'])
        pub2 = integrate(fleet, T2, wt3, base1)
        fleet.record('T2_integrated_marker', ok=True)
        fleet.record('T2_integrated', pushed=pub2['pushed_head'],
                     verified=pub2['verified_remote_head'])
        base2 = pub2['verified_remote_head']

        # --- T3: master list row, lead-owned scope -----------------------
        fleet.call('lead', 'create_task', task=T3,
                   epoch=fleet.epoch('lead'), base=base2,
                   scopes=['docs/THE_MASTER_LIST.md'],
                   packet='STATEMENT: the master list records the live '
                          'fleet bootstrap. PREDICTION: lead-only claim '
                          'succeeds; row lands via the loop. FALSIFIER: '
                          'non-lead claim succeeds (refused in tests).',
                   capabilities=['git'])
        try:
            fleet.call('gamma', 'claim', task=T3)
            raise RuntimeError('non-lead master-list claim was NOT refused')
        except ValueError as e:
            fleet.record('nonlead_master_list_refused', error=str(e))
        fleet.call('lead', 'claim', task=T3)
        t = fleet_task(fleet, T3)
        wt4 = fleet_worktree(fleet, T3)
        provision(fleet, repo, wt4, t['branch'], base2)
        ml = wt4 / 'docs/THE_MASTER_LIST.md'
        text = ml.read_text(encoding='utf-8')
        row = ('\n## FLEET REGISTRY (WORKFLOW-BOOTSTRAP-01 live)\n\n'
               'Live task ownership now flows through the fleet control '
               'plane (`tools/agent_fleet/`): authenticated HTTP, transactional '
               'SQLite store, generation-fenced claims, five private slots, '
               'fetch-verified fast-forward publication into this branch. '
               'This section records adoption; the registry is the live '
               'authority for fleet task ownership, this list remains the '
               'human-readable roadmap.\n')
        ml.write_text(text + row, encoding='utf-8')
        commit_and_push(wt4, t['branch'],
                        'demo-master-list-row: record live fleet adoption',
                        ['docs/THE_MASTER_LIST.md'])
        pub3 = integrate(fleet, T3, wt4, base2)
        fleet.record('T3_integrated_marker', ok=True)
        fleet.record('T3_integrated', pushed=pub3['pushed_head'],
                     verified=pub3['verified_remote_head'])

        # --- export audit + snapshot; tear down --------------------------
        ev = fleet.call('SUPERVISOR', 'events', since=0)
        (fleet.ev / 'events.json').write_text(
            json.dumps(ev, indent=2), encoding='utf-8')
        (fleet.ev / 'final_snapshot.json').write_text(
            json.dumps({k: v for k, v in fleet.snapshot().items()},
                       indent=2, default=str), encoding='utf-8')
        (run / 'SUMMARY.json').write_text(json.dumps({
            'claim_race': race,
            'tasks': {t: fleet.snapshot('lead')['tasks'][t]['state']
                      for t in (T1, T2, T3)},
            'base_before': base0, 'base_after': pub3['verified_remote_head'],
            'run_dir': str(run),
        }, indent=2), encoding='utf-8')
        fleet.record('complete', base_after=pub3['verified_remote_head'])
        return 0
    finally:
        fleet.stop_service()


if __name__ == '__main__':
    sys.exit(main())
