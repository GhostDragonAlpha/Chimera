"""Task cards and inboxes. GitHub merge verification is read-only network access."""
import argparse
import json
from pathlib import Path
import sys
import sqlite3
from urllib.request import Request, urlopen
from agent_slots import Registry,DEFAULT_ROOT
from instruction_state import inspect,decode
import kanban as k

def github_pr(url):
    k.pr_identity(url,'0'*40)
    number=url.rsplit('/',1)[1]
    req=Request('https://api.github.com/repos/'+k.REPO+'/pulls/'+number,
                headers={'Accept':'application/vnd.github+json','User-Agent':'Chimera-Kanban'})
    with urlopen(req,timeout=20) as response:
        raw=response.read(1024*1024+1)
    if len(raw)>1024*1024:raise ValueError('github_response_size_limit')
    return decode(raw)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['status','inbox','join','message','submit','review','accept-merge','enqueue','park'])
    p.add_argument('--task');p.add_argument('--agent');p.add_argument('--arguments',type=Path)
    args=p.parse_args();instructions=inspect(Path(__file__).resolve().parents[2]);r=Registry(DEFAULT_ROOT)
    if args.action=='status':result=k.read(r)
    elif args.action=='inbox':
        card=k.read(r,args.task);result={'task_id':card['id'],'state':card['state'],'messages':card['messages'],'prs':card['prs'],'winner':card['winner']}
    elif args.action=='join':result=k.join(r,args.agent,args.task)
    else:
        if not args.arguments:raise ValueError('arguments_file_required')
        with args.arguments.open('rb') as f:raw=f.read(65537)
        if len(raw)>65536:raise ValueError('arguments_size_limit')
        a=decode(raw)
        if args.action=='accept-merge':result=k.accept_merge(r,a,github_pr(a['pr_url']))
        else:result={'message':k.post,'submit':k.submit,'review':k.review,'enqueue':k.enqueue,'park':k.park}[args.action](r,a)
    print(json.dumps({'instruction_revision':instructions['revision_id'],'result':result},indent=2))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError,sqlite3.Error) as exc:
        print(json.dumps({'refused':str(exc)}),file=sys.stderr);sys.exit(2)
