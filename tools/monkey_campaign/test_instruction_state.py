import json
from pathlib import Path
import tempfile
import unittest

import instruction_state as c


class InstructionStateTests(unittest.TestCase):
    def test_placeholder_or_naive_ack_time_is_refused(self):
        for value in ('placeholder', '2026-09-24T00:00:00', '2026-09-24T00:00:00-05:00'):
            a = self.ack(); a['acknowledged_at_utc'] = value
            with self.assertRaisesRegex(ValueError, 'invalid_ack_timestamp'):
                c.inspect(self.root, a)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'docs').mkdir()
        (self.root/'policy.txt').write_text('preserved policy')
        self.meta = {'schema':'chimera.lead_instructions.v1','lead_id':'astra-codex',
                     'revision':1,'revision_id':'astra-0001','scope_sha256':c.SCOPE,
                     'files':['docs/MONKEY_RUN.md','policy.txt']}
        self.write_entry()

    def write_entry(self, suffix=''):
        (self.root/'docs'/'MONKEY_RUN.md').write_text(c.BEGIN+json.dumps(self.meta)+c.END+'\nGoal\n'+suffix,encoding='utf-8')

    def ack(self):
        current = c.inspect(self.root)
        return {'schema':'chimera.instruction_ack.v1',**{k:current[k] for k in
               ('lead_id','revision','revision_id','scope_sha256','bundle_sha256')},
               'coordinator_id':'fixture-coordinator','native_checkpoint':'fixture-only',
               'acknowledged_at_utc':'2026-09-24T00:00:00Z'}

    def test_first_read_matching_ack_and_new_revision(self):
        self.assertEqual(c.inspect(self.root)['state'],'READ_AND_ACK_REQUIRED')
        a = self.ack()
        self.assertEqual(c.inspect(self.root,a)['state'],'ACK_RECORD_MATCHES')
        self.meta.update(revision=2,revision_id='astra-0002'); self.write_entry()
        self.assertEqual(c.inspect(self.root,a)['state'],'UPDATED_READ_AND_ACK_REQUIRED')

    def test_approved_prior_scope_requires_reread_not_silent_ack(self):
        self.meta.update(revision=15, revision_id='astra-0015'); self.write_entry()
        a = self.ack()
        a.update(revision=14, revision_id='astra-0014',
                 scope_sha256='5b07ce0c49c6a8cae42bc4f04ebce8d2835104d5591df4f1feecf7fa0dc56a00')
        self.assertEqual(c.inspect(self.root,a)['state'], 'UPDATED_READ_AND_ACK_REQUIRED')
        a.update(revision=15, revision_id='astra-0015')
        with self.assertRaisesRegex(ValueError, 'ack_scope_mismatch'):
            c.inspect(self.root,a)

    def test_entry_or_linked_policy_changed_without_revision_refused(self):
        a = self.ack()
        self.write_entry('unversioned edit')
        with self.assertRaisesRegex(ValueError,'CHANGED_WITHOUT_REVISION'):
            c.inspect(self.root,a)
        self.write_entry()
        (self.root/'policy.txt').write_text('changed policy')
        with self.assertRaisesRegex(ValueError,'CHANGED_WITHOUT_REVISION'):
            c.inspect(self.root,a)

    def test_rollback_refused(self):
        self.meta.update(revision=2,revision_id='astra-0002'); self.write_entry(); a=self.ack()
        self.meta.update(revision=1,revision_id='astra-0001'); self.write_entry()
        with self.assertRaisesRegex(ValueError,'ROLLBACK'):
            c.inspect(self.root,a)

    def test_path_escape_missing_files_unknown_lead_and_scope(self):
        for bad in ('../outside','C:/outside','/outside','file:stream'):
            self.meta['files']=['docs/MONKEY_RUN.md',bad]; self.write_entry()
            with self.subTest(path=bad),self.assertRaises(ValueError):
                c.inspect(self.root)
        self.meta['files']=['docs/MONKEY_RUN.md','missing'];self.write_entry()
        with self.assertRaises(OSError):c.inspect(self.root)
        self.meta['files']=['docs/MONKEY_RUN.md'];self.meta['lead_id']='worker';self.write_entry()
        with self.assertRaisesRegex(ValueError,'lead_changed'):c.inspect(self.root)
        self.meta['lead_id']='astra-codex';self.meta['scope_sha256']='0'*64;self.write_entry()
        with self.assertRaisesRegex(ValueError,'scope_change'):c.inspect(self.root)

    def test_malformed_duplicate_metadata_and_size_limit(self):
        path=self.root/'docs'/'MONKEY_RUN.md'
        path.write_text(c.BEGIN+'{"schema":1,"schema":2}'+c.END)
        with self.assertRaises(ValueError):c.inspect(self.root)
        path.write_bytes(b'x'*(c.MAX_BYTES+1))
        with self.assertRaisesRegex(ValueError,'size_limit'):c.inspect(self.root)

    def test_ack_is_not_authentication_and_no_files_written(self):
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        out=c.inspect(self.root,self.ack())
        self.assertIn('does not authenticate',out['limits'])
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})


if __name__ == '__main__':unittest.main(verbosity=2)
