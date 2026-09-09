"""Offline fault-injection tests for WORKFLOW-BOOTSTRAP-01.

Distinct module so the recovered DeepSeek suite stays untouched. Covers the
operator-required scenarios beyond test_control.py: atomic single-winner
claims via HTTP under true concurrency, publication FF-verify + stale-epoch
refusal + interrupted-integration reconciliation against a real local git
origin, provisioning gates, and the untracked demo shader gap evidence.
"""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Control, Refusal
from service import Server
from client import call as http_call
import publish

BASE = 'a' * 40
HEAD = 'b' * 40
MERGED = 'c' * 40


def make_repo(origin, repo=None):
    """Bare local origin with one seeded commit on astra/gait-capture.

    When `repo` (path, not yet existing) is provided it becomes the working
    clone that authors and pushes the seed commit, so tests use real objects.
    """
    subprocess.run(['git', 'init', '-q', '--bare', str(origin)], check=True)
    scratch = None
    if repo is not None:
        subprocess.run(['git', 'clone', '-q', str(origin), str(repo)], check=True)
    else:
        scratch = origin.parent / (origin.name + '_seed')
        subprocess.run(['git', 'clone', '-q', str(origin), str(scratch)], check=True)
        repo = scratch
    subprocess.run(['git', '-C', str(repo), 'config', 'user.email', 't@t'], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'user.name', 't'], check=True)
    (Path(repo) / 'README.md').write_text('seed', encoding='utf-8')
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'seed'], check=True)
    subprocess.run(['git', '-C', str(repo), 'branch', '-M', 'astra/gait-capture'], check=True)
    subprocess.run(['git', '-C', str(repo), 'push', '-q', 'origin',
                    'astra/gait-capture'], check=True)
    if scratch is not None:
        shutil.rmtree(str(scratch), ignore_errors=True)
    return subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                          capture_output=True, text=True).stdout.strip()


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.c = Control(self.root / 'state.sqlite', 'super-secret',
                         'enroll-secret', self.root / 'slots')
        self.tokens = {}
        for aid in ('lead', 'standby', 'worker', 'other'):
            self.tokens[aid] = self.c.call(
                'enroll', 'enroll-secret', agent=aid, label=aid)['result']['session_token']
            self.c.call('qualify', 'super-secret', agent=aid,
                        capabilities=['cpu', 'gpu'], max_tasks=5,
                        can_lead=aid in ('lead', 'standby'),
                        rank=10 if aid == 'lead' else 1,
                        evidence='fixture qualification record')
        self.c.call('offer_lead', self.tokens['lead'], epoch=0,
                    checkpoint='ready; no foreign work')
        self.c.call('elect', 'super-secret')
        self.server = Server(('127.0.0.1', 0), self.c)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.sessions = {aid: {'endpoint': 'http://127.0.0.1:%d/v1/action'
                               % self.server.server_port, 'token': tok}
                         for aid, tok in self.tokens.items()}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def call(self, op, actor='lead', **p):
        return self.c.call(op, self.tokens.get(actor, actor), **p)['result']

    def call_alive(self, op, actor='other', **p):
        """Call as a specific still-alive agent (the dead leader's token is revoked)."""
        return self.call(op, actor, **p)

    def task(self, tid, **kw):
        p = dict(task=tid, epoch=self.call('snapshot')['epoch'], base=BASE,
                 scopes=['tools/labs/' + tid],
                 packet='statement / prediction / falsifier', kind='worker')
        p.update(kw)
        return self.call('create_task', **p)

    # --- required scenario: two workers race for one task -------------
    def test_race_for_one_task_exactly_one_claim_via_http(self):
        self.task('race')
        results = {}

        def take(aid):
            try:
                r = http_call(self.sessions[aid], 'claim', {'task': 'race'})
                results[aid] = r['result']['slot']
                return True
            except ValueError:
                return False

        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            r = list(pool.map(take, ['worker', 'other']))
        self.assertEqual(sorted(r), [False, True])
        snap = self.call('snapshot')
        owner = snap['tasks']['race']['owner']
        self.assertIn(owner, ('worker', 'other'))
        self.assertEqual(snap['tasks']['race']['state'], 'RUNNING')
        self.assertEqual(snap['tasks']['race']['generation'], 1)

    # --- required scenario: dependencies block premature work ----------
    def test_dependency_blocks_premature_claim(self):
        self.task('first')
        self.task('second', dependencies=['first'])
        with self.assertRaisesRegex(Refusal, 'dependencies_not_integrated'):
            self.claim('second', 'other')
        # full path releases the dependency
        t = self.claim('first', 'worker')
        self.call('submit_review', 'worker', task='first',
                  generation=t['generation'], branch=t['branch'], head=HEAD,
                  evidence='offline review record')
        rid = self.call('integration_request', task='first', head=HEAD,
                        branch=t['branch'], expected_base=BASE,
                        epoch=self.call('snapshot')['epoch'], review='r')['request']
        self.call('ack_integration', 'super-secret', request=rid,
                  base_branch='astra/gait-capture', expected_base=BASE,
                  commit=MERGED, evidence='offline publication evidence')
        self.assertEqual(self.call('snapshot')['tasks']['first']['state'],
                         'INTEGRATED')
        self.assertEqual(self.call('claim', 'other', task='second')['owner'],
                         'other')

    def claim(self, tid, actor='worker'):
        return self.call('claim', actor, task=tid)

    # --- required scenario: restart preserves claims/refs --------------
    def test_restart_preserves_claims_checkpoints_and_evidence_refs(self):
        self.task('one')
        t = self.claim('one')
        self.call('checkpoint', 'worker', task='one', generation=t['generation'],
                  checkpoint='cp-1: derived bound; evidence at docs/evidence/x')
        before = self.call('snapshot')
        c2 = Control(self.root / 'state.sqlite', 'super-secret',
                     'enroll-secret', self.root / 'slots')
        after = c2.call('snapshot', self.tokens['lead'])['result']
        self.assertEqual(before, after)
        self.assertEqual(after['tasks']['one']['checkpoint'], 'cp-1: derived bound; evidence at docs/evidence/x')
        # and a token from the old session file still works across restart
        self.call('checkpoint', 'worker', task='one', generation=t['generation'],
                  checkpoint='cp-2: still the owner')

    # --- required scenario: obsolete-generation token refused ----------
    def test_obsolete_generation_write_refused(self):
        self.task('one')
        t = self.claim('one')
        self.call('fail', 'super-secret', agent='worker',
                  reason='PROCESS_EXIT', evidence='process gone')
        self.assertEqual(self.call('snapshot')['tasks']['one']['state'],
                         'RECOVERY_HOLD')
        # The disconnected worker returns and writes with its obsolete claim:
        # refused either by session revocation or by generation fencing.
        with self.assertRaises(Refusal):
            self.call('checkpoint', 'worker', task='one',
                      generation=t['generation'],
                      checkpoint='zombie write from disconnected worker')
        # Recovery bumps the generation; the new claim owner cannot be
        # overridden by anything carrying the old generation either.
        self.call('recover', 'super-secret', task='one',
                  evidence='worktree preserved; writer stopped')
        t2 = self.claim('one', 'other')
        self.assertGreater(t2['generation'], t['generation'])
        with self.assertRaisesRegex(Refusal, 'stale_or_foreign_claim'):
            self.call('checkpoint', 'other', task='one',
                      generation=t['generation'], checkpoint='stale generation')

    # --- required scenario: one authorized integrator per epoch --------
    def test_leader_replacement_leaves_one_authorized_integrator(self):
        # worker owns the task; leader only issues/acks at its own epoch.
        self.task('one')
        t = self.claim('one', 'worker')
        self.call('submit_review', 'worker', task='one',
                  generation=t['generation'], branch=t['branch'], head=HEAD,
                  evidence='r')
        rid = self.call('integration_request', task='one', head=HEAD,
                        branch=t['branch'], expected_base=BASE,
                        epoch=self.call('snapshot')['epoch'], review='r')['request']
        # failover: standby becomes leader at a new epoch
        self.call('offer_lead', self.tokens['standby'],
                  epoch=self.call('snapshot')['epoch'], checkpoint='ready')
        self.call('fail', 'super-secret', agent='lead', reason='PROCESS_EXIT',
                  evidence='trusted runner exited')
        new_epoch = self.call('snapshot', 'standby')['epoch']
        self.assertEqual(self.call('snapshot', 'standby')['leader'], 'standby')
        # old leader's pending request is now stale — refused at ack
        with self.assertRaisesRegex(Refusal, 'stale_integration_epoch'):
            self.call('ack_integration', 'super-secret', request=rid,
                      base_branch='astra/gait-capture', expected_base=BASE,
                      commit=MERGED, evidence='must not pass')
        # new leader re-issues at the new epoch; old request stays refused
        rid2 = self.call('integration_request', 'standby', task='one', head=HEAD,
                         branch=t['branch'], expected_base=BASE,
                         epoch=new_epoch, review='re-review')['request']
        self.call('ack_integration', 'super-secret', request=rid2,
                  base_branch='astra/gait-capture', expected_base=BASE,
                  commit=MERGED, evidence='re-issued by new leader')
        self.assertEqual(self.call('snapshot', 'standby')['tasks']['one']['state'],
                         'INTEGRATED')
        self.assertEqual(self.call('snapshot', 'standby')['requests'][rid]['state'],
                         'PENDING_EXTERNAL_BROKER')

    def test_failed_leader_own_tasks_go_to_recovery_hold(self):
        # The control plane's law: a failed owner's tasks are held, not
        # silently published — even when the owner was the leader itself.
        self.task('ownwork')
        t = self.claim('ownwork', 'lead')
        self.call('submit_review', 'lead', task='ownwork',
                  generation=t['generation'], branch=t['branch'], head=HEAD,
                  evidence='r')
        self.call('offer_lead', self.tokens['standby'],
                  epoch=self.call('snapshot')['epoch'], checkpoint='ready')
        self.call('fail', 'super-secret', agent='lead', reason='PROCESS_EXIT',
                  evidence='trusted runner exited')
        self.assertEqual(self.call('snapshot', 'standby')
                         ['tasks']['ownwork']['state'], 'RECOVERY_HOLD')

    # --- interrupted integration reconciles actual Git state -----------
    def test_publish_reconciles_interrupted_integration(self):
        origin = self.root / 'origin'
        repo = self.root / 'clone'
        base_head = make_repo(origin, repo)
        # real task commit, pushed to the origin task branch
        subprocess.run(['git', '-C', str(repo), 'checkout', '-qb',
                        'astra/tasks/one', base_head], check=True)
        (repo / 'task.txt').write_text('task work', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'task work'],
                       check=True)
        task_head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                   capture_output=True, text=True).stdout.strip()
        subprocess.run(['git', '-C', str(repo), 'push', '-q', 'origin',
                        'astra/tasks/one'], check=True)
        self.task('one')
        t = self.claim('one')
        self.call('submit_review', 'worker', task='one',
                  generation=t['generation'], branch=t['branch'], head=task_head,
                  evidence='r')
        self.call('integration_request', task='one', head=task_head,
                  branch=t['branch'], expected_base=base_head,
                  epoch=self.call('snapshot')['epoch'], review='r')
        # Simulate: push succeeded earlier but was never acknowledged.
        subprocess.run(['git', '-C', str(origin), 'update-ref',
                        'refs/heads/astra/gait-capture', task_head], check=True)
        out = self.publish(repo, t['branch'], task_head, base_head,
                           '--reconcile-only')
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        r = json.loads(out.stdout)
        self.assertTrue(r['published'])
        self.assertTrue(r['already_integrated'])
        self.assertEqual(r['verified_remote_head'], task_head)

    def publish(self, repo, branch, head, base, *extra):
        return subprocess.run(
            [sys.executable, str(Path(publish.__file__)), '--repo', str(repo),
             '--task-branch', branch, '--head', head, '--expected-base', base,
             *extra], capture_output=True, text=True)

    def test_publish_refuses_head_mismatch_nonff_and_master(self):
        origin = self.root / 'origin'
        repo = self.root / 'clone'
        base_head = make_repo(origin, repo)
        # real task commit on top of the seed, pushed to the origin task branch
        subprocess.run(['git', '-C', str(repo), 'checkout', '-qb',
                        'astra/tasks/one', base_head], check=True)
        (repo / 'task.txt').write_text('task work', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'task work'],
                       check=True)
        task_head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                   capture_output=True, text=True).stdout.strip()
        subprocess.run(['git', '-C', str(repo), 'push', '-q', 'origin',
                        'astra/tasks/one'], check=True)

        self.task('one')
        t = self.claim('one')
        # 1. head mismatch: registry head is not the remote task branch
        out = self.publish(repo, t['branch'], HEAD, base_head)
        self.assertEqual(out.returncode, 2)
        self.assertIn('task_head_mismatch_remote', out.stdout)
        # 2. legitimate base advancement (another task integrated) -> FF
        #    refused, task must rebase; never force.
        subprocess.run(['git', '-C', str(repo), 'checkout', '-q',
                        'astra/gait-capture'], check=True)
        (repo / 'other.txt').write_text('other integration', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'other task'],
                       check=True)
        subprocess.run(['git', '-C', str(repo), 'push', '-q', 'origin',
                        'astra/gait-capture'], check=True)
        out = self.publish(repo, t['branch'], task_head, base_head)
        self.assertEqual(out.returncode, 2)
        self.assertIn('non_fast_forward_refused', out.stdout)
        # 3. forbidden target
        out = self.publish(repo, 'master', task_head, base_head)
        self.assertEqual(out.returncode, 2)
        self.assertIn('forbidden_branch', out.stdout)
        # 4. reset base to the fork point; FF publication succeeds and is
        #    verified by re-reading the remote.
        subprocess.run(['git', '-C', str(origin), 'update-ref',
                        'refs/heads/astra/gait-capture', base_head], check=True)
        out = self.publish(repo, t['branch'], task_head, base_head)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        r = json.loads(out.stdout)
        self.assertTrue(r['published'])
        self.assertEqual(r['verified_remote_head'], task_head)
        # 5. second run: already integrated, reconciles cleanly
        out = self.publish(repo, t['branch'], task_head, base_head,
                           '--reconcile-only')
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertTrue(json.loads(out.stdout)['already_integrated'])

    # --- provisioning gates -------------------------------------------
    def test_provision_slot_lifecycle_and_gates(self):
        self.task('one')
        t = self.claim('one')
        slot = t['slot']
        with self.assertRaisesRegex(Refusal, 'supervisor_only'):
            self.call('provision_slot', 'worker', task='one',
                      worktree_head=BASE, evidence='e')
        self.call('provision_slot', 'super-secret', task='one',
                  worktree_head=BASE, evidence='worktree created, clean')
        with self.assertRaisesRegex(Refusal, 'slot_already_provisioned'):
            self.call('provision_slot', 'super-secret', task='one',
                      worktree_head=BASE, evidence='again')
        snap = self.call('snapshot')
        self.assertTrue(snap['slots'][slot]['engine']['provisioned'])
        # release resets provisioning
        self.call('submit_review', 'worker', task='one',
                  generation=t['generation'], branch=t['branch'], head=HEAD,
                  evidence='r')
        rid = self.call('integration_request', task='one', head=HEAD,
                        branch=t['branch'], expected_base=BASE,
                        epoch=self.call('snapshot')['epoch'], review='r')['request']
        self.call('ack_integration', 'super-secret', request=rid,
                  base_branch='astra/gait-capture', expected_base=BASE,
                  commit=MERGED, evidence='e')
        self.call('release_slot', 'super-secret', task='one',
                  evidence='preserved; no processes')
        snap = self.call('snapshot')
        self.assertFalse(snap['slots'][slot]['engine']['provisioned'])
        self.assertIsNone(snap['slots'][slot]['task'])

    def test_provision_slot_tool_real_worktree(self):
        origin = self.root / 'origin'
        repo = self.root / 'clone'
        base_head = make_repo(origin, repo)
        wt = self.root / 'slot-03'
        out = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent /
                                 'provision_slot.py'), 'create',
             '--repo', str(repo), '--worktree', str(wt),
             '--task', 'one', '--branch', 'astra/tasks/one',
             '--base', base_head], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        r = json.loads(out.stdout)
        self.assertEqual(r['head'], base_head)
        # verify passes
        out = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent /
                                 'provision_slot.py'), 'verify',
             '--repo', str(repo), '--worktree', str(wt),
             '--task', 'one', '--branch', 'astra/tasks/one',
             '--base', base_head], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        # re-create refuses (no branch reuse)
        out = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent /
                                 'provision_slot.py'), 'create',
             '--repo', str(repo), '--worktree', str(self.root / 'slot-04'),
             '--task', 'one', '--branch', 'astra/tasks/one',
             '--base', base_head], capture_output=True, text=True)
        self.assertEqual(out.returncode, 2)
        self.assertIn('branch_already_exists', out.stdout)

    # --- partial evidence cannot become an accepted verdict ------------
    def test_partial_evidence_cannot_integrate(self):
        self.task('one')
        t = self.claim('one')
        self.call('submit_review', 'worker', task='one',
                  generation=t['generation'], branch=t['branch'], head=HEAD,
                  evidence='tests claimed but empty')
        # review alone does not integrate...
        self.assertEqual(self.call('snapshot')['tasks']['one']['state'], 'REVIEW')
        # ...and integration ack without a verified commit is refused
        with self.assertRaises(Refusal):
            self.call('integration_request', task='one', head='bad',
                      branch=t['branch'], expected_base=BASE,
                      epoch=self.call('snapshot')['epoch'], review='r')
        # ack with mismatched expected base refused
        s = self.call('snapshot')
        rid = self.call('integration_request', task='one', head=HEAD,
                        branch=t['branch'], expected_base=BASE,
                        epoch=s['epoch'], review='r')['request']
        with self.assertRaisesRegex(Refusal, 'wrong_integration_base'):
            self.call('ack_integration', 'super-secret', request=rid,
                      base_branch='astra/gait-capture', expected_base='d' * 40,
                      commit=MERGED, evidence='e')

    # --- slot/port conflicts refused ------------------------------------
    def test_port_conflicts_refused_and_ports_unique(self):
        snap = self.call('snapshot')
        ports = [v['engine']['port_candidate'] for v in snap['slots'].values()]
        self.assertEqual(len(ports), len(set(ports)))
        self.assertEqual(sorted(ports), [8101, 8102, 8103, 8104, 8105])
        # claiming all five slots leaves none for a sixth
        self.task('integrate', kind='integration')
        self.claim('integrate', 'lead')
        for i in range(4):
            self.task('w%d' % i)
            self.claim('w%d' % i, 'other' if i % 2 else 'worker')
        self.task('sixth')
        with self.assertRaisesRegex(Refusal, 'no_free_slot'):
            self.claim('sixth', 'other')

    def test_untracked_demo_shader_recorded(self):
        """Documented repo gap: membrane_demo.comp was never committed.

        This test pins the gap until the demo task closes it; the demo task in
        the live loop is exactly 'commit the shader'. It must NOT pass once the
        shader is tracked — update this test in that task.
        """
        import subprocess as sp
        here = Path(__file__).resolve()
        repo = here.parents[2]
        cp = sp.run(['git', '-C', str(repo), 'ls-files', '--error-unmatch',
                     'ChimeraEngine/engine/shaders/membrane_demo.comp'],
                    capture_output=True, text=True)
        self.assertNotEqual(
            cp.returncode, 0,
            'shader now tracked: update this gap test and close demo task')


if __name__ == '__main__':
    unittest.main(verbosity=2)
