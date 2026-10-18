"""Exercise the installed Z Code CLI with an isolated mock endpoint; no GPU inference."""
from pathlib import Path
import hashlib,http.server,json,os,re,shutil,sqlite3,subprocess,threading,time
BASE=Path(os.environ.get("CHIMERA_WORKFLOW_TEST_ROOT",r"D:\Chimera-Maintenance\Runtime\zcode-goal-workflow-tests"))
BASE.mkdir(parents=True,exist_ok=True)
RUN=BASE/("native-"+str(time.time_ns()));HOME=RUN/"home";WORK=RUN/"workspace"
assert not RUN.exists(),"Use a fresh test directory; do not overwrite prior evidence"
(HOME/".zcode/v2").mkdir(parents=True);(WORK/".zcode/agents").mkdir(parents=True)
REPO=Path(r"D:\Chimera-Maintenance\PythonChimera")
REAL=Path(r"C:\Users\allen\.zcode\v2\provider_config.json")
before=hashlib.sha256(REAL.read_bytes()).hexdigest()
NODE=r"C:\Users\allen\node-portable\node-v22.23.1-win-x64\node.exe"
ENTRY=r"C:\Program Files\ZCode\resources\glm\zcode.cjs"
HOOK=r"D:/Chimera-Maintenance/Runtime/zcode-two-agent/role_gate.py"
PYTHON=r"C:/Python314/python.exe"
for file in (REPO/".zcode/agents").glob("*.md"):
 shutil.copy2(file,WORK/".zcode/agents"/file.name)
shutil.copy2(REPO/".zcode/COMPACT_INSTRUCTIONS.md",WORK/".zcode/COMPACT_INSTRUCTIONS.md")
# Capture native hook identity for resume diagnostics; pass input through unchanged.
wrapper=RUN/"capture-hook.py"
wrapper.write_text("import json,sys,subprocess,time\nfrom pathlib import Path\n"+
 "raw=sys.stdin.read()\n"+
 "Path("+repr(str(RUN))+",'hook-event-'+str(time.time_ns())+'.json').write_text(raw,encoding='utf-8')\n"+
 "p=subprocess.run(["+repr(PYTHON)+",'-B',"+repr(HOOK)+"],input=raw,text=True,capture_output=True)\n"+
 "sys.stdout.write(p.stdout);sys.stderr.write(p.stderr);sys.exit(p.returncode)\n",encoding="utf-8")
command=PYTHON+" -B "+str(wrapper)
hooks={"enabled":True,"events":{kind:[{"hooks":[{"type":"command","command":command}]}]
       for kind in ["SessionStart","UserPromptSubmit","PreToolUse","PostToolUse","Stop"]}}
(WORK/".zcode/config.json").write_text(json.dumps({"features":{"compact":True,"subagent":True,"memory":False,"skill":False,"mcp":False},
    "memory":{"use":False}}),encoding="utf-8")
(HOME/".zcode/v2/compression-model.json").write_text('{"enabled":false}')
CHILD_PROFILE=os.environ.get("CHIMERA_TEST_CHILD_PROFILE","chimera-maya")
CHILD_MODEL={"chimera-maya":"glm-5.3-flash","chimera-step37":"step-3.7-flash-iq4_xs"}[CHILD_PROFILE]
STEP_READONLY=CHILD_PROFILE=="chimera-step37"
FORBIDDEN={"Write","Edit","Bash","NotebookEdit","TodoWrite","js","js_reset",
           "js_add_node_module_dir","Agent","Task","CreateWorkflow","AmendWorkflow"}
fixture=WORK/"review-fixture.txt"
fixture.write_text("REVIEW_FIXTURE: restore must retain the accepted construction.",encoding="utf-8")
faults=[];requests=[];phase="dispatch";calls=0;followup=False;child_reads=0;resume_attempts=0;lock=threading.Lock()
def flatten(value):
 if isinstance(value,str):return value
 if isinstance(value,dict):return "\n".join(flatten(v) for v in value.values())
 if isinstance(value,list):return "\n".join(flatten(v) for v in value)
 return str(value)
SUMMARY="""<summary>
Goal and purpose: build a playable matter-simulator game.
Milestone/player benefit: the player can retry a failed construction without losing it.
Why this task matters: restore/recovery makes experimentation useful instead of punishing.
Decision: determine whether restore returns the accepted construction; retain failed checks.
Current task: inspect the restore path; no new solver, no GPU test.
Process: choose a focused existing check; the lead may research, select peers and improve the workflow.
Next action: report game impact, evidence/limits, decision and next useful action.
</summary>"""
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  data=json.dumps({"object":"list","data":[{"id":m,"object":"model"} for m in ["qwen3.8-flash-next-agention-ap-q4_k_m","glm-5.3-flash","step-3.7-flash-iq4_xs"]]}).encode();self.send_response(200);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
 def do_POST(self):
  global calls,followup,child_reads,resume_attempts
  body=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
  if "messages" not in body:
   data=json.dumps({"ok":True,"released":True}).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data);return
  with lock:
   number=len(requests);requests.append({"phase":phase,"body":body})
  (RUN/f"request-{number}.json").write_text(json.dumps(body,indent=2),encoding="utf-8")
  self.send_response(200);self.send_header("Content-Type","text/event-stream");self.send_header("Connection","close");self.end_headers()
  def chunk(delta,finish=None):
   value={"id":"test-"+str(number),"object":"chat.completion.chunk","created":int(time.time()),
    "model":body["model"],"choices":[{"index":0,"delta":delta,"finish_reason":finish}]}
   self.wfile.write(("data: "+json.dumps(value)+"\n\n").encode());self.wfile.flush()
  tools=[x["function"]["name"] for x in body.get("tools",[])]
  text=flatten(body.get("messages",[]))
  iscompact="Your task is to create a detailed summary of the conversation" in text
  if iscompact:
   assert "Begin the summary with a compact" in text,"Project compact instructions missing"
   assert "why this particular main/child task matters" in text,"Task rationale missing from compact instructions"
   if STEP_READONLY and "Step's explicit read-only analyst/reviewer role" not in text:
    faults.append({"failure":"missing_readonly_compression_instruction","phase":phase})
   chunk({"role":"assistant","content":SUMMARY+("\nStep remains read-only; return findings to the lead, who delegates fixes." if STEP_READONLY else "")},"stop")
  elif phase=="dispatch" and "Agent" in tools and calls==0:
   calls+=1
   # Deliberately omit the common goal so the real hook must prepend it.
   args={"subagent_type":CHILD_PROFILE,"description":"Review restore purpose",
         "prompt":"Task purpose: make retry safe for the player. Inspect restore, report the decision it enables; do not use tools.",
         "run_in_background":False}
   chunk({"role":"assistant","tool_calls":[{"index":0,"id":"call_purpose_child","type":"function","function":{"name":"Agent","arguments":json.dumps(args)}}]})
   chunk({},"tool_calls")
  elif phase=="dispatch" and "Agent" in tools and calls==1:
   ids=re.findall(r"agent_[a-zA-Z0-9-]+",text)
   assert ids,"No actual child identity returned"
   agent=next((x for x in reversed(ids) if len(x)>20),ids[-1])
   calls+=1
   args={"to":agent,"summary":"Review the same construction restore task","message":"Keep the same task: explain why restore matters to a playable construction loop. Do not use tools."}
   chunk({"role":"assistant","tool_calls":[{"index":0,"id":"call_purpose_followup","type":"function","function":{"name":"SendMessage","arguments":json.dumps(args)}}]})
   chunk({},"tool_calls")
  elif STEP_READONLY and body["model"]==CHILD_MODEL and phase=="dispatch" and child_reads==0:
   forbidden=FORBIDDEN.intersection(tools)
   if forbidden:faults.append({"failure":"step_write_tools_exposed","phase":phase,"tools":sorted(forbidden)})
   if "Read" not in tools:faults.append({"failure":"step_read_missing","phase":phase})
   child_reads+=1
   chunk({"role":"assistant","tool_calls":[{"index":0,"id":"call_review_read","type":"function","function":{"name":"Read","arguments":json.dumps({"file_path":str(fixture)})}}]})
   chunk({},"tool_calls")
  elif STEP_READONLY and body["model"]==CHILD_MODEL and phase=="child_resume" and resume_attempts<2:
   # Direct CLI resume exposes the root schema. Exercise the real PreToolUse
   # guard rather than mistaking schema exposure for permission to execute.
   name="Write" if resume_attempts==0 else "Bash"
   args={"file_path":str(WORK/"forbidden-write.txt"),"content":"must not be written"} if resume_attempts==0 else {"command":"echo FORBIDDEN_SHELL_EXECUTED","description":"Negative fixture: this must be denied"}
   resume_attempts+=1
   chunk({"role":"assistant","tool_calls":[{"index":0,"id":"call_denied_"+str(resume_attempts),"type":"function","function":{"name":name,"arguments":json.dumps(args)}}]})
   chunk({},"tool_calls")
  else:
   if STEP_READONLY and body["model"]==CHILD_MODEL:
    forbidden=FORBIDDEN.intersection(tools)
    if phase=="dispatch" and forbidden:faults.append({"failure":"step_write_tools_exposed","phase":phase,"tools":sorted(forbidden)})
    if phase=="dispatch" and "REVIEW_FIXTURE: restore must retain" not in text:
     faults.append({"failure":"step_did_not_read_fixture","phase":phase})
   if phase=="dispatch" and "Agent" not in tools:
    if "[CHIMERA TASK PURPOSE v1]" not in text: faults.append({"phase":phase,"failure":"missing_child_purpose","request":number})
    content="CHILD_PURPOSE_OK. Game impact: safe retry is the player benefit; restore needs evidence. Decision: inspect the existing restore check. No new experiment."
   else:content="PURPOSE_RESUME_OK. The game goal is playable construction; this task makes retry safe. Next decision: verify existing restore evidence, then connect the controls."
   chunk({"role":"assistant","content":content},"stop")
  self.wfile.write(b"data: [DONE]\n\n");self.wfile.flush();self.close_connection=True
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler)
server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start()
d=json.loads(REAL.read_text(encoding="utf-8"));c=d["config"]
wanted=["chimera-strata-q4km","chimera-strata-maya","chimera-step37"]
rules=[p for p in c["providerConfigRules"]["providerRules"] if p["providerId"] in wanted]
models=[m for m in c["modelConfigRules"]["providerModelRules"] if m["providerId"] in wanted]
assert len(rules)==3,(len(rules),[r["providerId"] for r in rules])
for provider in rules:
 api=provider["config"]["api"];api["baseUrl"]=f"http://127.0.0.1:{server.server_port}/v1"
 if "headers" in api:api["headers"]={}
c["providerOrder"]=wanted;c["providerConfigRules"]={"providerRules":rules}
c["modelConfigRules"]={"providerModelRules":models,"manualProviderModelRules":[]}
c["defaultModelSelection"]={"providerId":wanted[0],"modelId":"qwen3.8-flash-next-agention-ap-q4_k_m","options":{"reasoningLevel":"on"}}
config=HOME/".zcode/v2/provider_config.json";config.write_text(json.dumps(d),encoding="utf-8")
(HOME/".zcode/cli").mkdir(parents=True,exist_ok=True)
(HOME/".zcode/cli/config.json").write_text(json.dumps({"features":{"compact":True,"subagent":True,"memory":False,"skill":False,"mcp":False},"memory":{"use":False},"hooks":hooks}),encoding="utf-8")
builtin=HOME/"builtin.json";shutil.copy2(r"C:\Program Files\ZCode\resources\config\provider\zcode-builtin.json",builtin)
env=dict(os.environ,USERPROFILE=str(HOME),HOME=str(HOME),ZCODE_DATA_BASE_DIR=str(HOME),ZCODE_HOME=str(HOME/".zcode"),
 ZCODE_PERSONAL_PROVIDER_CONFIG_FILE=str(config),ZCODE_BUILTIN_PROVIDER_CONFIG_FILE=str(builtin),
 ZCODE_BUILTIN_PROVIDER_BUNDLED_CONFIG_FILE=str(builtin),CHIMERA_WORKFLOW_STATE_DIR=str(RUN/"hook-sessions"))
operations=[]
def invoke(label,prompt,sid=None):
 global phase
 phase=label
 cmd=[NODE,ENTRY,"--cwd",str(WORK),"--surface","terminal","--mode","yolo","--verbose","--no-color"]
 if sid:cmd+=["--resume",sid]
 cmd+=["-p",prompt]
 start=time.monotonic()
 with (RUN/(label+".stdout.log")).open("w",encoding="utf-8") as out,(RUN/(label+".stderr.log")).open("w",encoding="utf-8") as err:
  proc=subprocess.Popen(cmd,cwd=WORK,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
  try:code=proc.wait(timeout=90)
  except subprocess.TimeoutExpired:
   proc.terminate();proc.wait(timeout=10);raise
 operations.append({"label":label,"exit_code":code,"seconds":round(time.monotonic()-start,2)})
 print(json.dumps(operations[-1]),flush=True)
 assert code==0,(label,(RUN/(label+".stderr.log")).read_text(errors="replace")[-1800:])
 return (RUN/(label+".stdout.log")).read_text(encoding="utf-8",errors="replace")
try:
 invoke("dispatch","Our game goal is a playable matter workshop. The task is safe construction retry: inspect restore so the player can experiment without losing a build. Use the assigned reviewer/worker, follow up with the same child, then report. This is a wiring fixture; no filesystem changes or GPU work.")
 dbpath=next(HOME.rglob("db.sqlite"))
 with sqlite3.connect(str(dbpath)) as db:
  rows=db.execute("select id,parent_id from session order by time_created").fetchall()
 parent=next(row[0] for row in rows if row[1] is None)
 child=next(row[0] for row in rows if row[1]==parent)
 assert not faults,faults
 followup_replies=[flatten(m.get("content")) for r in requests for m in r["body"].get("messages",[])
                   if m.get("role")=="tool" and m.get("tool_call_id")=="call_purpose_followup"]
 assert followup_replies and not any("tool_use_error" in text or "InputValidationError" in text for text in followup_replies),followup_replies
 assert calls==2,"Parent did not use actual dispatch and follow-up"
 invoke("main_compact","/compact Retain the decision about safe retry.",parent)
 assert "PURPOSE_RESUME_OK" in invoke("main_resume","Explain the preserved task purpose and next decision. Do not use tools.",parent)
 invoke("child_compact","/compact Retain the assigned purpose and uncertainty.",child)
 assert "PURPOSE_RESUME_OK" in invoke("child_resume","Explain the preserved task purpose and next decision. Do not use tools.",child)
 if STEP_READONLY:
  assert resume_attempts==2,resume_attempts
  assert not (WORK/"forbidden-write.txt").exists(),"Step wrote a file on resume"
  last=next(r["body"] for r in reversed(requests) if r["phase"]=="child_resume")
  replies={m.get("tool_call_id"):flatten(m.get("content")) for m in last["messages"] if m.get("role")=="tool"}
  for call in ["call_denied_1","call_denied_2"]:
   assert "Step is a read-only analyst/reviewer" in replies.get(call,""),(call,replies)
 # Confirm exactly one child was resumed rather than replaced.
 with sqlite3.connect(str(dbpath)) as db:
  count=db.execute("select count(*) from session where parent_id=?",(parent,)).fetchone()[0]
 assert count==1,count
 compact_requests=[r for r in requests if "Your task is to create a detailed summary" in flatten(r["body"].get("messages",[]))]
 assert {r["phase"] for r in compact_requests}>={"main_compact","child_compact"}
 assert next(r["body"]["model"] for r in compact_requests if r["phase"]=="child_compact")==CHILD_MODEL
 assert next(r["body"]["model"] for r in compact_requests if r["phase"]=="main_compact")=="qwen3.8-flash-next-agention-ap-q4_k_m"
 assert not faults,faults
 assert hashlib.sha256(REAL.read_bytes()).hexdigest()==before
 result={"status":"PASS","scope":"Installed Z Code dispatch/follow-up/manual compression/resume with deterministic mock model; no model intelligence or full-context claim",
 "operations":operations,"request_count":len(requests),"same_child_resumed":True,
 "main_and_child_compression_purpose_injected":True,"model_inheritance_preserved":True,"real_provider_unchanged":True,
 "child_profile":CHILD_PROFILE,"readonly_step_schema_checked":STEP_READONLY,
 "step_read_executed":bool(child_reads),"direct_resume_write_and_shell_denied":STEP_READONLY and resume_attempts==2,
 "child_tools_by_phase":[{"phase":r["phase"],"tools":[t["function"]["name"] for t in r["body"].get("tools",[])]}
  for r in requests if r["body"]["model"]==CHILD_MODEL]}
finally:
 server.shutdown()
(RUN/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2),flush=True)
