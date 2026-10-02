from contextlib import ExitStack
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import test_task_package
import task_package as t
import runner_resources as r


class ResourcesTests(unittest.TestCase):
    setUp=test_task_package.Tests.setUp
    tearDown=test_task_package.Tests.tearDown
    sealed=test_task_package.Tests.sealed

    def test_auto_selects_free_slot_and_injects_thread_limits(self):
        with t.lock(self.runner/'slot-0/slot.lock'):
            result=t.run(self.sealed(),[sys.executable,'-c',"import os,json;from pathlib import Path;Path('outputs/env.json').write_text(json.dumps({k:os.environ[k] for k in ['OMP_NUM_THREADS','NUMBA_NUM_THREADS','CMAKE_BUILD_PARALLEL_LEVEL']}))"],['outputs/env.json'],root=self.runner)
        self.assertEqual(result['slot'],1,result)
        self.assertEqual(set(json.loads((Path(result['result_directory'])/'artifacts/outputs/env.json').read_text()).values()),{'4'})
        self.assertEqual(result['resource_profile']['job_memory_gib'],16)

    def test_all_slots_busy_no_extra_workspace(self):
        sealed=self.sealed()
        with ExitStack() as stack:
            for i in range(4):stack.enter_context(t.lock(self.runner/f'slot-{i}/slot.lock'))
            result=t.run(sealed,[sys.executable,'-c','pass'],root=self.runner)
        self.assertEqual(result['state'],'BUSY')
        self.assertFalse((self.runner/'slot-4').exists())
        self.assertFalse(list(self.runner.glob('slot-*/scratch')))

    def test_memory_pressure_refuses_before_scratch_creation(self):
        with patch.object(r,'available_memory',return_value=30*1024**3):
            result=t.run(self.sealed(),[sys.executable,'-c','pass'],root=self.runner)
        self.assertEqual(result['reason'],'memory_reserve')
        self.assertFalse(list(self.runner.glob('slot-*/scratch')))

    def test_windows_job_rejects_excess_committed_memory(self):
        p=r.profile();p['job_memory_gib']=1
        with patch.object(r,'profile',return_value=p):
            result=t.run(self.sealed(),[sys.executable,'-c','a=bytearray(2*1024**3)'],root=self.runner)
        self.assertEqual(result['state'],'FAILED',result)
        self.assertTrue(result['cleanup_verified'])

    def test_four_jobs_actually_overlap(self):
        from concurrent.futures import ThreadPoolExecutor
        import time
        sealed=self.sealed();release=self.root/'release'
        code="from pathlib import Path;import time;Path('ready').write_text('yes');"+"\nwhile not Path("+repr(str(release))+").exists():time.sleep(.05)"
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(t.run,sealed,[sys.executable,'-c',code],root=self.runner,timeout=15) for _ in range(4)]
            try:
                until=time.monotonic()+10
                while len(list(self.runner.glob('slot-*/scratch/ready')))!=4:
                    if time.monotonic()>until:self.fail('four jobs did not overlap')
                    time.sleep(.05)
            finally:release.write_text('go')
            results=[f.result() for f in futures]
        self.assertEqual({x['slot'] for x in results},{0,1,2,3})
        self.assertTrue(all(x['state']=='PASSED' and x['cleanup_verified'] for x in results),results)


if __name__=='__main__':unittest.main()
