import tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from worker_checkout import prepare,git

class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.src=self.root/'source';self.src.mkdir()
        git(self.src,'init');git(self.src,'config','user.name','Test');git(self.src,'config','user.email','test@example.invalid')
        p=self.src/'tools/monkey_campaign/contributions/T/file.txt';p.parent.mkdir(parents=True);p.write_text('baseline')
        git(self.src,'add','.');git(self.src,'commit','-m','fixture');git(self.src,'branch','-M','forearm-package-20260924')
        git(self.src,'branch','branch-1')
        remote=self.root/'remote.git';git(self.src,'clone','--bare',str(self.src),str(remote));git(self.src,'remote','add','origin',str(remote))
        self.head=git(self.src,'rev-parse','HEAD')
        self.disk=patch('worker_checkout.shutil.disk_usage',return_value=SimpleNamespace(free=200*1024**3));self.disk.start();self.addCleanup(self.disk.stop)
    def allocation(self,name='a'):
        return {'task_id':'T','card_slot':1,'publication_branch':'branch-1','attempt':{'id':name,'workspace':str(self.root/name)},'brief':{'pr_destination':'tools/monkey_campaign/contributions/T/'}}
    def test_correct_branch_without_switching_source_and_resume_dirty(self):
        a=self.allocation();r=prepare(self.src,a);p=Path(r['working_directory'])
        self.assertEqual(git(p,'branch','--show-current'),'branch-1')
        self.assertEqual(git(self.src,'branch','--show-current'),'forearm-package-20260924')
        self.assertEqual(git(self.src,'rev-parse','HEAD'),self.head)
        (p/'mine.txt').write_text('unfinished')
        self.assertEqual(prepare(self.src,a)['state'],'RESUMED');self.assertEqual((p/'mine.txt').read_text(),'unfinished')
    def test_competitors_have_independent_checkouts_same_slot_branch(self):
        a=prepare(self.src,self.allocation('a'));b=prepare(self.src,self.allocation('b'))
        self.assertNotEqual(a['working_directory'],b['working_directory'])
        self.assertEqual(a['branch'],b['branch'])
    def test_wrong_branch_refuses_without_discarding_work(self):
        a=self.allocation();r=prepare(self.src,a);p=Path(r['working_directory']);git(p,'checkout','-b','wrong')
        with self.assertRaisesRegex(ValueError,'checkout_branch_changed'):prepare(self.src,a)
        self.assertEqual(git(p,'branch','--show-current'),'wrong')

if __name__=='__main__':unittest.main()
