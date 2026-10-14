import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import task_package as t


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.src=self.root/'source';self.src.mkdir()
        t.git(self.src,'init');t.git(self.src,'config','user.name','fixture');t.git(self.src,'config','user.email','fixture@example.invalid')
        (self.src/'mod').mkdir();(self.src/'dep').mkdir();(self.src/'images').mkdir()
        (self.src/'mod/code.py').write_text('original\n');(self.src/'dep/api.py').write_text('dependency\n')
        (self.src/'images/old.png').write_bytes(b'x'*1024**2)
        t.git(self.src,'add','.');t.git(self.src,'commit','-m','base')
        self.base=t.git(self.src,'rev-parse','HEAD').decode().strip()
        self.pkg=self.root/'package'
        t.create(self.src,self.base,self.pkg,'tester','T',['dep'],['mod'])
        self.runner=self.root/'runner'

    def tearDown(self):
        def writable(fn,p,exc):os.chmod(p,0o700);fn(p)
        shutil.rmtree(self.root,onerror=writable);self.temp.cleanup()

    def sealed(self):return Path(t.seal(self.pkg)['sealed'])

    def test_no_git_or_images_source_untouched(self):
        self.assertFalse((self.pkg/'files/.git').exists())
        self.assertFalse((self.pkg/'files/images').exists())
        self.assertTrue((self.pkg/'files/dep/api.py').exists())
        self.assertEqual(t.git(self.src,'status','--porcelain'),b'')

    @unittest.skipUnless(os.name=='nt','Windows job recovery')
    def test_crashed_runner_recovers_declared_output_on_next_run(self):
        import time
        s=self.sealed()
        command=[sys.executable,'-c',"from pathlib import Path;import time;Path('outputs/result').write_text('preserve');time.sleep(120)"]
        script='import task_package as t;t.run('+repr(str(s))+','+repr(command)+",['outputs/result'],root="+repr(str(self.runner))+')'
        proc=subprocess.Popen([sys.executable,'-B','-c',script],cwd=Path(t.__file__).parent)
        try:
            ready=self.runner/'slot-0/scratch/outputs/result';until=time.monotonic()+15
            while not ready.exists():
                if time.monotonic()>until:self.fail('runner did not start')
                time.sleep(.05)
            proc.kill();proc.wait(timeout=10)
            r=t.run(s,[sys.executable,'-c','pass'],root=self.runner)
            self.assertEqual(r['state'],'PASSED',r)
            recovered=list((self.runner/'results').glob('*/recovery.json'))
            self.assertEqual(len(recovered),1)
            self.assertTrue(json.loads(recovered[0].read_text())['cleanup_verified'])
            self.assertEqual((recovered[0].parent/'artifacts/outputs/result').read_text(),'preserve')
            self.assertFalse((self.runner/'slot-0/scratch').exists())
        finally:
            if proc.poll() is None:proc.kill();proc.wait()

    def test_storage_budget_fails_and_cleans(self):
        r=t.run(self.sealed(),[sys.executable,'-c',"from pathlib import Path;import time;Path('huge').write_bytes(b'x'*10000);time.sleep(5)"],root=self.runner,job_limit=5000)
        self.assertEqual(r['state'],'FAILED',r)
        self.assertIn('storage_budget',r['error'])
        self.assertTrue(r['cleanup_verified'])

    def test_patch_add_edit_delete_binary_and_apply(self):
        (self.pkg/'files/mod/code.py').unlink()
        (self.pkg/'files/mod/new.py').write_text('new\n')
        (self.pkg/'files/mod/new.bin').write_bytes(bytes(range(256)))
        s=self.sealed()
        self.assertEqual(t.git(self.src,'status','--porcelain'),b'')
        self.assertEqual(t.apply(s,self.src)['state'],'APPLIED_STAGED_NOT_COMMITTED')
        self.assertFalse((self.src/'mod/code.py').exists())
        self.assertEqual((self.src/'mod/new.bin').read_bytes(),bytes(range(256)))

    def test_scope_escape_and_readonly_change(self):
        with self.assertRaises(ValueError):t.relpath('../outside')
        with self.assertRaises(ValueError):t.relpath('C:/outside')
        (self.pkg/'files/dep/api.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'write_outside_scope'):self.sealed()

    def test_seal_tamper_is_refused(self):
        s=self.sealed();(s/'files/mod/code.py').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'sealed_file_changed'):t.verify(s)

    def test_stale_base_refused(self):
        s=self.sealed();(self.src/'advance').write_text('advance')
        t.git(self.src,'add','.');t.git(self.src,'commit','-m','advance')
        with self.assertRaisesRegex(ValueError,'stale_base'):t.apply(s,self.src)

    def test_success_keeps_output_removes_scratch(self):
        s=self.sealed()
        r=t.run(s,[sys.executable,'-c',"from pathlib import Path;Path('outputs/result.txt').write_text('result');Path('temporary.bin').write_bytes(b'x'*10000)"],
                ['outputs/result.txt'],root=self.runner)
        self.assertEqual(r['state'],'PASSED',r);self.assertTrue(r['cleanup_verified'])
        self.assertFalse((self.runner/'slot-0/scratch').exists())
        self.assertEqual((Path(r['result_directory'])/'artifacts/outputs/result.txt').read_text(),'result')

    def test_failure_and_timeout_clean(self):
        s=self.sealed()
        for code,timeout in [('raise SystemExit(7)',5),('import time;time.sleep(30)',.2)]:
            r=t.run(s,[sys.executable,'-c',code],timeout=timeout,root=self.runner)
            self.assertEqual(r['state'],'FAILED',r);self.assertTrue(r['cleanup_verified'],r)

    def test_child_processes_do_not_survive_runner(self):
        s=self.sealed()
        # Child would recreate a file after parent exit if it escaped ownership.
        code="import subprocess,sys;subprocess.Popen([sys.executable,'-c',\"import time;from pathlib import Path;time.sleep(2);Path('escaped').write_text('bad')\"])"
        r=t.run(s,[sys.executable,'-c',code],root=self.runner)
        self.assertEqual(r['state'],'PASSED',r);self.assertTrue(r['cleanup_verified'],r)

    def test_residue_and_concurrent_owner_are_not_deleted(self):
        s=self.sealed();slot=self.runner/'slot-0';slot.mkdir(parents=True)
        (slot/'scratch').mkdir();(slot/'scratch/evidence').write_text('keep')
        with self.assertRaisesRegex(ValueError,'slot_recovery_required'):
            t.run(s,[sys.executable,'-c','pass'],root=self.runner)
        self.assertTrue((slot/'scratch/evidence').exists())
        with t.lock(slot/'slot.lock'):
            with self.assertRaises(OSError):
                t.run(s,[sys.executable,'-c','pass'],root=self.runner,slot=0)

    def test_missing_declared_output_fails_but_cleans(self):
        r=t.run(self.sealed(),[sys.executable,'-c','pass'],['outputs/missing'],root=self.runner)
        self.assertEqual(r['state'],'FAILED',r);self.assertTrue(r['cleanup_verified'],r)


if __name__=='__main__':unittest.main()
