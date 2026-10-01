import sys,unittest,tempfile,hashlib
from pathlib import Path
sys.path.append('E:/PythonChimera/tools/monkey_campaign')
from agent_slots import Registry
import kanban as k,continuous_cycle as cycle
from test_kanban import spec
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.r=Registry(Path(self.tmp.name));self.r.initialize();k.initialize(self.r,[spec('T0')],k.LEAD)
  with self.r.transaction() as s:s['kanban'].update(separate_review_lane=True,continuous_cycle=True,branch_policy='TEN_PERSISTENT_SLOT_BRANCHES',operational_takeover=True,operational_lead={'agent_id':'busy-coordinator','token':'unchanged'})
  p=cycle.join(self.r,'author','T0');a=p['attempt'];root=Path(a['workspace']);root.mkdir(parents=True);f=root/'code.py';f.write_text('pass')
  request=cycle.request_publication(self.r,dict(task_id='T0',agent_id='author',attempt_id=a['id'],criteria_sha256=a['criteria_sha256'],checkpoint='saved',writes_stopped=True,artifacts=[dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest())]))
  c=k.read(self.r,'T0');r=c['publication_requests'][0]
  self.args=dict(actor=k.LEAD,task_id='T0',request_id=request['request_id'],criteria_sha256=c['criteria_sha256'],artifact_manifest_sha256=k.digest(r['artifacts']),body='Reproduced failure; correct existing candidate',evidence_reference='local/probe')
 def test_rejection_unblocks_same_card_without_stealing_coordination(self):
  before=k.read(self.r,'T0');result=k.reject_publication(self.r,self.args);self.assertEqual(result['lane'],'DEVELOPMENT')
  after=k.read(self.r,'T0');self.assertEqual(after['criteria_sha256'],before['criteria_sha256']);self.assertEqual(after['publication_requests'][0]['artifacts'],before['publication_requests'][0]['artifacts'])
  p=cycle.join(self.r,'new-worker');self.assertEqual(p['state'],'ASSIGNED');self.assertEqual(p['task_id'],'T0');self.assertIsNone(after['winner']);self.assertEqual(self.r.readonly()['kanban']['operational_lead']['agent_id'],'busy-coordinator')
  self.assertEqual(k.reject_publication(self.r,self.args)['state'],'ALREADY_RETURNED')
 def test_wrong_authority_or_manifest_refused(self):
  for key,value in [('actor','worker'),('artifact_manifest_sha256','wrong'),('criteria_sha256','wrong'),('request_id','wrong')]:
   before=k.digest(self.r.readonly())
   with self.assertRaises(ValueError):k.reject_publication(self.r,{**self.args,key:value})
   self.assertEqual(before,k.digest(self.r.readonly()))
 def test_second_pending_candidate_stays_in_review(self):
  with self.r.transaction() as s:
   import copy
   c=s['kanban']['cards']['T0'];r=copy.deepcopy(c['publication_requests'][0]);r['id']='another';c['publication_requests'].append(r)
  self.assertEqual(k.reject_publication(self.r,self.args)['lane'],'REVIEW')
if __name__=='__main__':unittest.main()
