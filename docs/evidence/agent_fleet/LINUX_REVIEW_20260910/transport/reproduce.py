import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/agent_fleet'))
from control import Control
from service import Server
from client import call
rows=[]
class RecordedServer(Server):
 def handle_error(self,request,address):
  rows.append({'server_exception':type(sys.exception()).__name__})
with tempfile.TemporaryDirectory() as d:
 c=Control(Path(d)/'state.sqlite','test-supervisor','test-enrollment',Path(d)/'slots')
 token=c.call('enroll','test-enrollment',agent='worker',label='local review')['result']['session_token']
 c.call('qualify','test-supervisor',agent='worker',capabilities=['cpu'],can_lead=True,evidence='synthetic local qualification')
 c.call('offer_lead',token,epoch=0,checkpoint='local ready');c.call('elect','test-supervisor')
 c.call('create_task',token,epoch=1,task='transport',base='a'*40,scopes=['tools/example'],packet='local test',kind='worker')
 t=c.call('claim',token,task='transport')['result']
 s=RecordedServer(('127.0.0.1',0),c);thr=threading.Thread(target=s.serve_forever,daemon=True);thr.start()
 session={'endpoint':f'http://127.0.0.1:{s.server_port}/v1/action','token':token}
 try:
  for name in (None,42,'unknown'):
   before=call(session,'snapshot',{})['revision']
   args={'task':'transport','generation':t['generation']}
   if name is not None:args['resource']=name
   try:result=call(session,'resource_acquire',args);outcome='unexpected success'
   except Exception as e:outcome=type(e).__name__+': '+str(e)
   after=call(session,'snapshot',{})['revision']
   rows.append({'resource':name,'outcome':outcome,'state_unchanged':before==after,'next_snapshot':'PASS'})
 finally:s.shutdown();s.server_close();thr.join()
print(json.dumps(rows,indent=2))
