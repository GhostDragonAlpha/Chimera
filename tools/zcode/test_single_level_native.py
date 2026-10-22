"""Real Z Code CLI with a deterministic local endpoint; never uses model services.

Tests built-in Explore, wildcard general-purpose, custom explicit tool grants,
parent follow-up, reports, compression and direct child-session restoration.
"""
import hashlib,http.server,json,os,re,shutil,sqlite3,subprocess,threading,time
from pathlib import Path

BASE=Path(os.environ["CHIMERA_TEST_ROOT"])
RUN=BASE/("single-level-"+str(time.time_ns()));HOME=RUN/"home";WORK=RUN/"workspace"
(HOME/".zcode/v2").mkdir(parents=True);(WORK/".zcode/agents").mkdir(parents=True)
NODE=r"C:/Users/allen/node-portable/node-v22.23.1-win-x64/node.exe"
ENTRY=os.environ.get("CHIMERA_TEST_ENTRY",r"C:/Program Files/ZCode/resources/glm/zcode.cjs")
REAL=Path(r"C:/Users/allen/.zcode/v2/provider_config.json")
real_hash=hashlib.sha256(REAL.read_bytes()).hexdigest()
DENIED={"Agent","Task","SendMessage","CreateWorkflow","AmendWorkflow"}
profiles=["Explore","general-purpose","fixture-explicit"]
(WORK/".zcode/agents/fixture-explicit.md").write_text('''---
name: fixture-explicit
description: Fixture explicitly requesting delegation tools to test the runtime boundary.
tools: [Read, Agent, Task, SendMessage, CreateWorkflow, AmendWorkflow, RespondToCoordinator]
---
Return a report to the lead. No grandchildren.
''',encoding="utf-8")
config={"features":{"compact":True,"subagent":True,"memory":False,"skill":False,"mcp":False},"memory":{"use":False},"plugins":{"enabled":False},"skills":{"enabled":False},"hooks":{"enabled":False}}
(WORK/".zcode/config.json").write_text(json.dumps(config))
(HOME/".zcode/cli").mkdir();(HOME/".zcode/cli/config.json").write_text(json.dumps(config))
(HOME/".zcode/v2/compression-model.json").write_text('{"enabled":false}')
(WORK/"fixture.txt").write_text("EXISTING_CONSTRUCTION_PRESERVED",encoding="utf-8")
requests=[];faults=[];phase="dispatch";root_calls=0;child_rounds={};operations=[];child_id=None
def flat(v):
    if isinstance(v,str):return v
    if isinstance(v,dict):return "\n".join(flat(x) for x in v.values())
    if isinstance(v,list):return "\n".join(map(flat,v))
    return str(v)
def attempts():
    return [("Agent",{"subagent_type":"Explore","description":"Forbidden grandchild","prompt":"NEVER_RUN_GRANDCHILD","run_in_background":False}),
            ("Task",{"subagent_type":"general-purpose","description":"Forbidden alias","prompt":"NEVER_RUN_GRANDCHILD","run_in_background":False}),
            ("CreateWorkflow",{"script":"throw new Error('NEVER_RUN_WORKFLOW')"}),
            ("AmendWorkflow",{"run_id":"nonexistent-fixture"}),
            ("SendMessage",{"to":"agent_nonexistent_fixture","summary":"Forbidden peer resume","message":"NEVER_RUN_PEER"})]
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        data=json.dumps({"object":"list","data":[{"id":"fixture-local","object":"model"}]}).encode()
        self.send_response(200);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        global root_calls
        body=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if "messages" not in body:
            data=b'{"ok":true,"released":true}';self.send_response(200);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data);return
        number=len(requests);tools={t["function"]["name"] for t in body.get("tools",[])}
        text=flat(body["messages"]);compact="Your task is to create a detailed summary" in text
        child=phase.startswith("child_") or "RespondToCoordinator" in tools
        requests.append({"phase":phase,"child":child,"compact":compact,"body":body})
        (RUN/f"request-{number}.json").write_text(json.dumps(requests[-1],indent=2),encoding="utf-8")
        self.send_response(200);self.send_header("Content-Type","text/event-stream");self.send_header("Connection","close");self.end_headers()
        def chunk(delta,finish=None):
            data={"id":f"fixture-{number}","object":"chat.completion.chunk","created":int(time.time()),"model":body["model"],"choices":[{"index":0,"delta":delta,"finish_reason":finish}]}
            self.wfile.write(("data: "+json.dumps(data)+"\n\n").encode());self.wfile.flush()
        def call(name,args,ident):
            chunk({"role":"assistant","tool_calls":[{"index":0,"id":ident,"type":"function","function":{"name":name,"arguments":json.dumps(args)}}]});chunk({},"tool_calls")
        if compact:
            chunk({"role":"assistant","content":"<summary>Continue the existing Blender construction. This is a child assignment; only the lead delegates. Report evidence and limits. Existing construction preserved.</summary>"},"stop")
        elif child:
            if DENIED & tools:faults.append({"phase":phase,"request":number,"exposed":sorted(DENIED & tools)})
            # Parent dispatch includes a unique marker; resumed tests use phase.
            key=phase if phase.startswith("child_") else (re.findall(r"PROFILE_CASE_[\w-]+",text) or ["missing-child-marker"])[-1]
            n=child_rounds.get(key,0);child_rounds[key]=n+1
            # Even if schemas hide tools, inject stale/malicious calls to check execution denial.
            if n<len(attempts()):
                name,args=attempts()[n];call(name,args,f"blocked_{n}")
            elif n==5:
                call("Read",{"file_path":str(WORK/"fixture.txt")},"allowed_read")
            elif n==6 and "RespondToCoordinator" in tools:
                call("RespondToCoordinator",{"summary":"Child policy verified","message":"REPORT: worked directly, existing construction preserved, no delegation."},"allowed_report")
            else:
                # Initial/native and resumed contexts must both refuse all five calls before execution.
                responses={m.get("tool_call_id"):flat(m.get("content")) for m in body["messages"] if m.get("role")=="tool"}
                for i in range(5):
                    if "CHIMERA_SINGLE_LEVEL" not in responses.get(f"blocked_{i}",""):
                        faults.append({"phase":phase,"key":key,"missing_denial":i,"result":responses.get(f"blocked_{i}","")[:300]})
                if "EXISTING_CONSTRUCTION_PRESERVED" not in responses.get("allowed_read",""):
                    faults.append({"phase":phase,"missing_read":True})
                if "allowed_report" in responses and "queued for the coordinator" not in responses["allowed_report"]:
                    faults.append({"phase":phase,"report_failed":responses["allowed_report"]})
                chunk({"role":"assistant","content":"CHILD_REPORT_OK: no delegation, construction preserved. Return decisions to Qwen."},"stop")
        elif phase=="dispatch" and root_calls<len(profiles):
            profile=profiles[root_calls];root_calls+=1
            if not {"Agent","SendMessage"}<=tools:faults.append({"lead_tools_missing":sorted(tools)})
            call("Agent",{"subagent_type":profile,"description":f"Single-level {profile}","prompt":f"PROFILE_CASE_{profile}: inspect the fixture and return a report.","run_in_background":False},f"lead_dispatch_{root_calls}")
        elif phase=="followup" and root_calls==3:
            root_calls+=1;call("SendMessage",{"to":child_id.removeprefix("sess_subagent_"),"summary":"Same child report","message":"Resume the same task and return the report; no nested delegation."},"lead_followup")
        else:chunk({"role":"assistant","content":"LEAD_OK: all child reports received; lead retains delegation authority."},"stop")
        self.wfile.write(b"data: [DONE]\n\n");self.wfile.flush();self.close_connection=True

server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler);server.daemon_threads=True
threading.Thread(target=server.serve_forever,daemon=True).start()
# Copy provider shape only, then replace connection settings with the local fixture.
provider=json.loads(REAL.read_text(encoding="utf-8"));c=provider["config"]
rule=next(p for p in c["providerConfigRules"]["providerRules"] if p["providerId"]=="chimera-strata-q4km")
rule["config"]["api"]={"type":rule["config"]["api"]["type"],"baseUrl":f"http://127.0.0.1:{server.server_port}/v1"}
models=[m for m in c["modelConfigRules"]["providerModelRules"] if m["providerId"]=="chimera-strata-q4km"]
model_id=models[0]["modelId"]
c["providerOrder"]=[rule["providerId"]];c["providerConfigRules"]={"providerRules":[rule]}
c["modelConfigRules"]={"providerModelRules":models,"manualProviderModelRules":[]}
c["defaultModelSelection"]={"providerId":rule["providerId"],"modelId":model_id,"options":{"reasoningLevel":"on"}}
pc=HOME/".zcode/v2/provider_config.json";pc.write_text(json.dumps(provider),encoding="utf-8")
builtin=HOME/"builtin.json";shutil.copy2(r"C:/Program Files/ZCode/resources/config/provider/zcode-builtin.json",builtin)
env=dict(os.environ,USERPROFILE=str(HOME),HOME=str(HOME),ZCODE_DATA_BASE_DIR=str(HOME),ZCODE_HOME=str(HOME/".zcode"),ZCODE_PERSONAL_PROVIDER_CONFIG_FILE=str(pc),ZCODE_BUILTIN_PROVIDER_CONFIG_FILE=str(builtin),ZCODE_BUILTIN_PROVIDER_BUNDLED_CONFIG_FILE=str(builtin))
def invoke(label,prompt,sid=None):
    global phase
    phase=label;cmd=[NODE,ENTRY,"--cwd",str(WORK),"--surface","terminal","--mode","yolo","--no-color"]
    if sid:cmd += ["--resume",sid]
    cmd += ["-p",prompt];start=time.monotonic()
    with (RUN/(label+".stdout.log")).open("w",encoding="utf-8") as out,(RUN/(label+".stderr.log")).open("w",encoding="utf-8") as err:
        proc=subprocess.Popen(cmd,cwd=WORK,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=proc.wait(timeout=100)
        except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=10);raise
    operations.append({"label":label,"code":code,"seconds":round(time.monotonic()-start,2)});print(json.dumps(operations[-1]),flush=True)
    assert code==0,(label,(RUN/(label+".stderr.log")).read_text(encoding="utf-8")[-1600:])
    return (RUN/(label+".stdout.log")).read_text(encoding="utf-8")
result={"status":"FAIL","run":str(RUN)}
try:
    invoke("dispatch","Run the three single-level delegation fixtures and collect each report. No real inference or project files are involved.")
    dbpath=next(HOME.rglob("db.sqlite"))
    with sqlite3.connect(dbpath) as db:rows=db.execute("select id,parent_id,task_type from session order by time_created").fetchall()
    assert len(rows)==4,rows
    parent=next(r[0] for r in rows if r[1] is None);children=[r[0] for r in rows if r[1]==parent];assert len(children)==3,rows
    child_id=children[0]
    invoke("followup","Ask the same Explore child for its report, then summarize it.",parent)
    invoke("child_compact","/compact Preserve assignment, evidence and role.",child_id)
    invoke("child_resume","Continue the existing assignment and return your report.",child_id)
    invoke("parent_resume","Report progress and retain your delegation role.",parent)
    with sqlite3.connect(dbpath) as db:final_rows=db.execute("select id,parent_id from session").fetchall()
    assert len(final_rows)==4,final_rows
    assert root_calls==4,root_calls
    assert not faults,faults
    assert any(r["phase"]=="child_compact" and r["compact"] for r in requests)
    assert all({"Agent","SendMessage"}<={t["function"]["name"] for t in r["body"].get("tools",[])} for r in requests if r["phase"]=="parent_resume")
    assert hashlib.sha256(REAL.read_bytes()).hexdigest()==real_hash
    result.update(status="PASS",profiles=profiles,session_count=4,no_grandchildren=True,lead_dispatch_and_followup=True,child_read_and_report=True,child_compact_resume_restricted=True,provider_settings_unchanged=True,requests=len(requests),operations=operations,bundle_sha256=hashlib.sha256(Path(ENTRY).read_bytes()).hexdigest(),scope="Real CLI and persisted sessions, scripted local endpoint, no GPU/model quality claim")
except Exception as ex:
    result.update(error=repr(ex),faults=faults,operations=operations);raise
finally:
    server.shutdown();(RUN/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8");print(json.dumps(result,indent=2),flush=True)
