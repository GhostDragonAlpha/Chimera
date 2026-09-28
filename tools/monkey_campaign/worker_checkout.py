"""Prepare a small per-attempt checkout on the correct local slot branch."""
from pathlib import Path
import json
import re
import subprocess
import shutil

def git(repo,*args):
    p=subprocess.run(['git','-c','safe.directory='+str(repo),'-C',str(repo),*args],capture_output=True,text=True,timeout=90)
    if p.returncode:raise ValueError('checkout_git_failed: '+p.stderr[-1800:])
    return p.stdout.strip()

def prepare(source,allocation):
    source=Path(source).resolve()
    assignment=allocation.get('attempt') or allocation.get('review')
    if assignment is None:return None
    attempt=Path(assignment['workspace']).resolve();attempt.mkdir(parents=True,exist_ok=True)
    checkout=attempt/'checkout'
    branch=allocation.get('checkout_branch') or 'branch-'+str(allocation['card_slot'])
    if not re.fullmatch(r'branch-(?:[1-9]|10)',branch):raise ValueError('invalid_slot_branch')
    if checkout==source or source.is_relative_to(checkout):raise ValueError('checkout_overlaps_source')
    manifest=attempt/'checkout_identity.json'
    identity={'task_id':allocation['task_id'],'assignment_id':assignment['id'],'branch':branch,'source':str(source)}
    if manifest.exists():
        saved=json.loads(manifest.read_text())
        if any(saved.get(k)!=v for k,v in identity.items()):raise ValueError('checkout_identity_mismatch')
        if git(checkout,'branch','--show-current')!=branch:raise ValueError('checkout_branch_changed_preserve_work')
        return {**saved,'working_directory':str(checkout),'state':'RESUMED'}
    if checkout.exists():raise ValueError('unrecorded_checkout_preserved_inspect_before_retry')
    if shutil.disk_usage(attempt).free<100*1024**3:raise ValueError('disk_floor_100GiB')
    remote=git(source,'remote','get-url','origin')
    # Share existing objects, avoid a full clone/assets per attempt, and leave source
    # HEAD, index and worktree untouched. No branch checkout conflict across agents.
    git(source,'clone','--shared','--no-checkout',str(source),str(checkout))
    git(checkout,'remote','set-url','origin',remote)
    if allocation.get('review'):
        head=allocation['review']['head_sha']
        git(checkout,'fetch','--no-tags','origin',head)
    else:
        git(checkout,'fetch','--no-tags','origin','refs/heads/'+branch+':refs/remotes/origin/'+branch)
        head=git(checkout,'rev-parse','refs/remotes/origin/'+branch)
    path=allocation['brief'].get('pr_destination','tools/monkey_campaign/contributions/'+allocation['task_id']+'/').strip('/')
    if not path.startswith('tools/monkey_campaign/contributions/') or '..' in path.split('/'):
        raise ValueError('invalid_sparse_contribution_path')
    git(checkout,'config','core.sparseCheckout','true')
    git(checkout,'config','core.sparseCheckoutCone','false')
    (checkout/'.git/info/sparse-checkout').write_text('/'+path+'/\n',encoding='utf-8')
    git(checkout,'checkout','--no-track','-b',branch,head)
    if git(checkout,'branch','--show-current')!=branch:raise ValueError('checkout_branch_verification_failed')
    saved={**identity,'head_sha':git(checkout,'rev-parse','HEAD'),'sparse_path':path,'remote':remote}
    manifest.write_text(json.dumps(saved,indent=2),encoding='utf-8')
    return {**saved,'working_directory':str(checkout),'state':'PREPARED'}
