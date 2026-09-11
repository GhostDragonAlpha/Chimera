"""Preregistered orchestration falsifiers; subprocess fixtures are NOT coding models.

Reject overlap failure, duplicate ownership, replayed execution, execution before
provisioning, and acceptance inferred solely from process success.
"""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from control import Control
from service import Server
from client import call
from run_queue_worker import WorkerQueue, CommandExecutor, SessionLock

FIXTURE = r'''
import json, os, pathlib, sys, time
p=json.load(sys.stdin)
assert not os.environ.get('CHIMERA_FLEET_SUPERVISOR_TOKEN')
assert not os.environ.get('CHIMERA_FLEET_ENROLLMENT_TOKEN')
root=pathlib.Path(sys.argv[1]); root.joinpath(p['task']['id']).touch()
deadline=time.monotonic()+15
while len(list(root.iterdir())) < 3:
    if time.monotonic() > deadline: raise RuntimeError('parallel_overlap_missing')
    time.sleep(.02)
sys.path.insert(0,sys.argv[2])
from client import call
s=json.loads(pathlib.Path(p['session_file']).read_text())
head=__import__('subprocess').check_output(['git','-C',p['worktree'],'rev-parse','HEAD'],text=True).strip()
call(s,'submit_review',{'task':p['task']['id'],'generation':p['generation'],
     'branch':p['task']['branch'],'head':head,'evidence':'temporary subprocess fixture; not model or physics certification'})
'''


class ExecutionProof(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.control = Control(self.root/'state.sqlite', 'fixture-super', 'fixture-enroll', self.root/'slots')
        self.server = Server(('127.0.0.1', 0), self.control)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f'http://127.0.0.1:{self.server.server_port}/v1/action'
        self.sessions = {}
        for name in ('lead', 'worker1', 'worker2', 'worker3'):
            token = self.control.call('enroll','fixture-enroll',agent=name,label=name)['result']['session_token']
            self.control.call('qualify','fixture-super',agent=name,capabilities=['cpu'],max_tasks=1,
                              can_lead=name=='lead',evidence='isolated test profile')
            self.sessions[name] = {'endpoint':self.endpoint,'token':token}
            (self.root/(name+'.json')).write_text(json.dumps(self.sessions[name]))
        self.invoke('lead','offer_lead',epoch=0,checkpoint='isolated test')
        self.control.call('elect','fixture-super')

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.tmp.cleanup()

    def invoke(self, name, op, **args):
        return call(self.sessions[name], op, args)['result']

    def task(self, name):
        self.invoke('lead','create_task',epoch=1,task=name,kind='worker',base='a'*40,
                    scopes=['tests/'+name],capabilities=['cpu'],packet='statement/prediction/falsifier: isolated fixture')

    def queue(self, name):
        return WorkerQueue(lambda op,args: call(self.sessions[name],op,args),agent=name)

    def provision(self, assignment):
        claim=assignment['claim']; cwd=Path(claim['worktree']); cwd.mkdir(parents=True)
        def git(*args):
            return subprocess.check_output(['git','-C',str(cwd),*args],stderr=subprocess.PIPE,text=True).strip()
        git('init','-b',claim['branch'])
        git('-c','user.name=fixture','-c','user.email=fixture@invalid','commit','--allow-empty','-m','fixture')
        head=git('rev-parse','HEAD')
        self.control.call('provision_slot','fixture-super',task=claim['id'],worktree_head=head,evidence='temporary initialized repo fixture')
        return head

    def executor(self, name, argv):
        profile=self.root/(name+'-profile.json'); profile.write_text(json.dumps({'argv':argv}))
        return CommandExecutor(profile,lambda op,args: call(self.sessions[name],op,args),name,self.root/(name+'.json'))

    def test_three_http_workers_execute_overlapping_processes_and_restart_owned(self):
        for n in range(3): self.task('task'+str(n))
        names=['worker1','worker2','worker3']
        with concurrent.futures.ThreadPoolExecutor(3) as pool:
            claims=list(pool.map(lambda n:self.queue(n).claim_once(),names))
        self.assertEqual(len({c['task'] for c in claims}),3)
        self.assertEqual(len({c['claim']['worktree'] for c in claims}),3)
        for c in claims: self.provision(c)
        restarted=Control(self.root/'state.sqlite','fixture-super','fixture-enroll',self.root/'slots')
        self.assertEqual(restarted.call('snapshot',self.sessions['lead']['token'])['result']['tasks'],
                         self.invoke('lead','snapshot')['tasks'])
        # New queue instances recover owned work; no additional claim generation.
        resumed=[self.queue(n).claim_once() for n in names]
        self.assertEqual([x['claim']['generation'] for x in resumed],[1,1,1])
        barrier=self.root/'barrier'; barrier.mkdir()
        executors=[self.executor(n,[sys.executable,'-c',FIXTURE,str(barrier),str(HERE)]) for n in names]
        with concurrent.futures.ThreadPoolExecutor(3) as pool:
            futures=[pool.submit(e,c) for e,c in zip(executors,resumed)]
            for f in futures: f.result(timeout=25)
        state=self.invoke('lead','snapshot')
        self.assertEqual({t['state'] for t in state['tasks'].values()},{'REVIEW'})
        self.assertTrue(all(t['integration'] is None for t in state['tasks'].values()))
        self.assertEqual(len(list(barrier.iterdir())),3)

    def test_no_provision_no_execution_and_zero_exit_not_acceptance(self):
        self.task('task0'); c=self.queue('worker1').claim_once()
        marker=self.root/'must-not-exist'
        executor=self.executor('worker1',[sys.executable,'-c',f'from pathlib import Path; Path({str(marker)!r}).touch()'])
        executor(c)
        self.assertFalse(marker.exists())
        self.provision(c)
        executor(self.queue('worker1').claim_once())
        task=self.invoke('lead','snapshot')['tasks']['task0']
        self.assertTrue(marker.exists())
        self.assertEqual(task['state'],'BLOCKED')
        self.assertIsNone(task['integration'])

    def test_duplicate_runner_lock_and_missing_profile(self):
        lock=self.root/'runner.lock'
        with SessionLock(lock):
            with self.assertRaisesRegex(ValueError,'worker_already_running'):
                with SessionLock(lock): pass
        with SessionLock(lock): pass  # owner exit releases OS lock
        with self.assertRaisesRegex(ValueError,'executor_command_required'):
            self.executor('worker1',[])

    def test_timeout_preserves_claim_instead_of_reassigning(self):
        self.task('slow'); c=self.queue('worker1').claim_once(); self.provision(c)
        executor=self.executor('worker1',[sys.executable,'-c','import time; time.sleep(60)'])
        executor.timeout=.1  # explicit fault injection deadline, not production policy
        executor(self.queue('worker1').claim_once())
        task=self.invoke('lead','snapshot')['tasks']['slow']
        self.assertEqual((task['state'],task['owner'],task['generation']),('BLOCKED','worker1',1))
        self.assertIn('drain_unverified',task['checkpoint'])


if __name__ == '__main__': unittest.main()
