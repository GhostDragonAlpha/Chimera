"""Reproducible, anchor-checked patch for the installed Z Code 3.14 bundle.

Only the child tool policy changes. The lead retains delegation; reporting to
the owning coordinator and all existing model settings are preserved.
"""
import hashlib
from pathlib import Path

MARKER = "CHIMERA_SINGLE_LEVEL_20261022"
HELPERS = '''/* CHIMERA_SINGLE_LEVEL_20261022 */
function chimeraChildRuntime(e){return ["subagent_child","workflow_child","nested_workflow_child"].includes(e.config?.taskType)||String(e.sessionId??"").startsWith("sess_subagent_")}
function chimeraDelegationTool(e){return ["agent","task","sendmessage","createworkflow","amendworkflow"].includes(String(e??"").toLowerCase())}
'''

def patch(source):
    if MARKER in source:
        raise ValueError("Already patched; do not stack patches")
    edits = [
        ('function Byn(e){', HELPERS + 'function Byn(e){'),
        ('bla=[Bz,jy];', 'bla=[Bz,jy,"Agent","Task","SendMessage","CreateWorkflow","AmendWorkflow"];'),
        ('function R1o(e){if(this.config.subagents?.enabled!==!1)',
         'function R1o(e){if(chimeraChildRuntime(this))return;if(this.config.subagents?.enabled!==!1)'),
        ('function gko(e){if(e.taskType!=="workflow_child")',
         'function gko(e){if(["subagent_child","workflow_child","nested_workflow_child"].includes(e.taskType))return [...new Set([...(e.toolDisallowlist??[]),...(e.taskType==="workflow_child"?qva:[]),"Agent","Task","SendMessage","CreateWorkflow","AmendWorkflow"])];if(e.taskType!=="workflow_child")'),
        ('this.cachedTools.filter(t=>t.name!=="WebSearch"||oba.call(this,e))',
         'this.cachedTools.filter(t=>!(chimeraChildRuntime(this)&&chimeraDelegationTool(t.name))&&(t.name!=="WebSearch"||oba.call(this,e)))'),
        ('runtimeScope:e.config.taskType==="subagent_child"?"subagent":"main",permissionTimeoutMs:',
         'getChimeraChildScope:()=>chimeraChildRuntime(e),runtimeScope:e.config.taskType==="subagent_child"?"subagent":"main",permissionTimeoutMs:'),
        ('runtimeScope:t.runtimeScope??"main",traceContext:',
         'getChimeraChildScope:t.getChimeraChildScope,runtimeScope:t.runtimeScope??"main",traceContext:'),
        ('T=w.traceId,I=w.turnId??e.turnId;if(!_)',
         'T=w.traceId,I=w.turnId??e.turnId;if((e.getChimeraChildScope?.()||e.runtimeScope==="subagent"||String(e.sessionId??"").startsWith("sess_subagent_"))&&chimeraDelegationTool(b.name)){let Ye=tT(b,Jr(fr.PermissionDenied,"CHIMERA_SINGLE_LEVEL: Only the lead can delegate or resume other agents, including Explore. Complete this task directly or return the need to the lead with RespondToCoordinator or a final report.",{recoverable:!0,retryable:!1}));await LG(e,b.id,w,I,Ye.error);a?.finishDenied?.();return Ye}if(!_)'),
    ]
    for old,new in edits:
        if source.count(old) != 1:
            raise ValueError(f"Unsupported bundle anchor count {source.count(old)}: {old[:90]}")
        source=source.replace(old,new,1)
    return source

if __name__ == "__main__":
    import argparse,json
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path);parser.add_argument("output",type=Path)
    a=parser.parse_args();raw=a.source.read_bytes()
    out=patch(raw.decode("utf-8")).encode("utf-8")
    if a.output.exists():raise SystemExit("Output already exists")
    a.output.write_bytes(out)
    print(json.dumps({"source_sha256":hashlib.sha256(raw).hexdigest(),"patched_sha256":hashlib.sha256(out).hexdigest(),"output":str(a.output)}))
