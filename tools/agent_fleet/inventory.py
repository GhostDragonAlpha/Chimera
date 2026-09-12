"""Read-only logical-size/free-space inventory and five-slot worktree plan.

No cleanup, Git mutation, process control, quotas or provisioning is performed.
A missing path is reported; large trees can stop at an explicit entry budget.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
from layout import slot_layout

def inspect(path,max_entries=1000000):
    root=Path(path)
    out={'path':str(root),'logical_bytes':0,'files':0,'directories':0,'skipped_links':0,'errors':[], 'complete':True}
    if not root.exists():out.update(complete=False,errors=['path_missing']);return out
    # Do not follow even a root symlink or Windows reparse/junction point.
    def linked(p):
        st=p.lstat()
        return stat.S_ISLNK(st.st_mode) or bool(getattr(st,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))
    if linked(root):out.update(complete=False,errors=['root_link_refused']);return out
    d=shutil.disk_usage(root);out['volume']={'total_bytes':d.total,'free_bytes':d.free,'used_bytes':d.used}
    pending=[root];seen=0
    while pending:
        p=pending.pop()
        if seen>=max_entries:out['complete']=False;out['errors'].append('entry_budget_reached');break
        seen+=1
        try:
            if linked(p):out['skipped_links']+=1;continue
            if p.is_dir():
                out['directories']+=1
                with os.scandir(p) as it:pending.extend(Path(e.path) for e in it)
            elif p.is_file():out['files']+=1;out['logical_bytes']+=p.stat().st_size
        except OSError as e:out['complete']=False;out['errors'].append(type(e).__name__+': '+str(p))
    return out

def plan(root,base,slots=5):
    # Intentionally names no active task branch: the lead binds real task IDs
    # after preservation/migration and uses the control service's branch value.
    return {'root':str(root),'shared_store':str(root/'repo.git'),'base':base,
        'slots':[{'id':i,**slot_layout(root,i)} for i in range(1,(slots if isinstance(slots,int) and slots>0 else 5)+1)],
        'pr_base':'astra/gait-capture','branch_template':'astra/tasks/<unique-task-id>',
        'provisioned':False,'policy':'No task branches are reused; no worktree is removed before preserved-evidence and clean/process-stop checks.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--path',action='append',default=[])
    p.add_argument('--repo',type=Path)
    p.add_argument('--plan-root',type=Path)
    p.add_argument('--base',default='UNRESOLVED')
    p.add_argument('--max-entries',type=int,default=1000000)
    a=p.parse_args()
    if a.max_entries<=0:p.error('max-entries must be positive')
    result={'paths':[inspect(x,a.max_entries) for x in a.path],
            'measurement':'logical file bytes; not allocated extents, shared-object deduplication or peak-build forecast'}
    if a.repo:
        cp=subprocess.run(['git','-C',str(a.repo),'worktree','list','--porcelain'],capture_output=True,text=True)
        result['git_worktrees']={'exit_code':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}
    if a.plan_root:result['plan']=plan(a.plan_root,a.base)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
