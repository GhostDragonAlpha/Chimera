"""Seam-3 executable-checklist lifecycle test for
work.mechanism-factory-patch-equilibrium (11.18 first deliverable).

Builds the graph-required control plane on a temp service over the REAL
creature graph, creates a task bound to the authored work object, assembles a
temp git candidate carrying the current bytes of tools/mechanism_factory,
tools/membrane_scale_lab and docs/evidence/mechanism_factory (the lab is
imported read-only, never edited), and runs the full lifecycle: claim,
workflow_prepare with the bound read hashes, trusted-runner execute (pinned
argv, clean-candidate enforcement, evidence written OUTSIDE the worktree),
workflow_attest, submit_review -> REVIEW.

Green = the checklist is executable end to end.
Run: python tools/mechanism_factory/test_workflow_checklist.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))                       # mechanism_factory
sys.path.insert(0, str(_REPO / "tools"))             # creature_graph pkg
sys.path.insert(0, str(_REPO / "tools" / "agent_fleet"))

from control import Refusal                          # noqa: E402
from creature_graph.store import CreatureGraph       # noqa: E402
from graph_workflow import (                         # noqa: E402
    GraphWorkflowControl, binding, candidate, file_hash, unpack,
)
from graph_workflow_runner import execute            # noqa: E402

REAL_GRAPH = _REPO / "tools" / "creature_graph" / "data" / "creature_graph.json"
WORK_ID = "work.mechanism-factory-patch-equilibrium"
SCOPE_DIRS = ("tools/mechanism_factory", "tools/membrane_scale_lab",
              "docs/evidence/mechanism_factory")
SCOPE_FILES = ("tools/port_registry.py", ".gitignore")


class WorkflowChecklistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.g = CreatureGraph.load(str(REAL_GRAPH))
        self.bound = binding(self.g, WORK_ID)        # real graph, real contract
        self.c = GraphWorkflowControl(
            self.root / 'db.sqlite', 'admin', 'enroll', self.root / 'slots',
            graph_path=REAL_GRAPH)
        self.tokens = {'SUPERVISOR': 'admin'}
        for agent in ('lead', 'worker'):
            self.tokens[agent] = self.c.call(
                'enroll', 'enroll', agent=agent, label=agent)['result']['session_token']
            self.c.call('qualify', 'admin', agent=agent, capabilities=['cpu'],
                        max_tasks=5, can_lead=agent == 'lead', rank=1,
                        evidence='seam-3 checklist fixture')
        self.call('offer_lead', 'lead', epoch=0, checkpoint='fixture')
        self.call('elect', 'SUPERVISOR')

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, op, actor='lead', **args):
        return self.c.call(op, self.tokens[actor], **args)['result']

    def git(self, *args):
        p = subprocess.run(
            ['git', '-c', 'safe.directory=' + self.repo.as_posix(),
             '-C', str(self.repo), *args], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def ready(self):
        self.call('create_task', task='mech-factory-p1', epoch=1,
                  base='a' * 40, scopes=['source'],
                  packet='seam-3 executable checklist for the 11.18 first deliverable',
                  graph_work=WORK_ID)
        self.claim = self.call('claim', 'worker', task='mech-factory-p1')
        self.repo = Path(self.claim['worktree'])
        self.repo.mkdir(parents=True)
        # candidate = CURRENT bytes of the three scoped paths (the graph pins
        # were authored from these bytes; git archive HEAD would pin stale
        # pre-seam bytes because this seam's work is not yet committed).
        for rel in SCOPE_DIRS:
            shutil.copytree(_REPO / rel, self.repo / rel,
                            ignore=shutil.ignore_patterns('__pycache__'),
                            dirs_exist_ok=True)
        for rel in SCOPE_FILES:                      # p1-battery imports
            shutil.copyfile(_REPO / rel, self.repo / rel)   # port_registry;
        # .gitignore keeps runner-created __pycache__ out of candidate cleanliness
        self.git('init')
        self.git('add', '.')
        self.git('-c', 'user.name=Seam3', '-c', 'user.email=seam3@local',
                 'commit', '-m', 'mechanism-factory checklist candidate')
        self.assertEqual(candidate(self.repo)['head'], self.git('rev-parse', 'HEAD'))
        self.context = self.call('workflow_context', 'worker', task='mech-factory-p1')
        read_hashes = {
            oid: file_hash(self.repo / self.g.get(oid)['document']['original_path'])
            for oid in self.bound['read_hashes']}
        self.call('workflow_prepare', 'worker', task='mech-factory-p1',
                  generation=self.claim['generation'],
                  input_hash=self.context['input_hash'],
                  read_hashes=read_hashes)

    def test_checklist_executable_end_to_end(self):
        self.ready()
        receipt = execute(self.context, self.repo, self.root / 'runner_run1')
        expected_ids = [c['id'] for c in self.bound['contract']['checks']]
        self.assertEqual([c['id'] for c in receipt['checks']], expected_ids)
        for record in receipt['checks']:
            self.assertEqual(record['exit_code'], 0,
                             (record['id'], Path(record['log']).read_text()[-2000:]))
        from auxiliary_graph import run
        aux = self.call('workflow_verifier_context', 'SUPERVISOR',
                        task='mech-factory-p1')
        receipt['independent'] = run(aux, self.repo, self.root / 'private1')
        result = self.call('workflow_attest', 'SUPERVISOR',
                           task='mech-factory-p1', receipt=receipt)
        self.assertTrue(result['all_passed'], result)
        submitted = self.call('submit_review', 'worker', task='mech-factory-p1',
                              generation=self.claim['generation'],
                              branch=self.claim['branch'],
                              head=candidate(self.repo)['head'],
                              evidence='retained runner receipt')
        self.assertEqual(submitted['state'], 'REVIEW')

    def test_dirty_candidate_refused_by_runner(self):
        self.ready()
        (self.repo / 'tools' / 'mechanism_factory' / 'dirty.txt').write_text(
            'uncommitted scratch', encoding='utf-8')
        with self.assertRaisesRegex(Refusal, 'workflow_candidate_not_clean'):
            execute(self.context, self.repo, self.root / 'runner_run_dirty')

    def test_foreign_graph_work_refused(self):
        with self.assertRaisesRegex(Refusal, 'unknown_graph_work'):
            self.call('create_task', task='mech-factory-x', epoch=1,
                      base='a' * 40, scopes=['source'], packet='x',
                      graph_work='work.missing-mechanism-factory')


if __name__ == '__main__':
    unittest.main()
