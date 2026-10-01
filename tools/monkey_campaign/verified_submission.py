"""Worker-facing PR intake must verify GitHub before mutating the board."""
from agent_slots import require
import kanban

def submit(registry,args,fetch=None):
    if fetch is None:
        from kanban_cli import github_pr
        fetch=github_pr
    remote=fetch(args['pr_url'])
    require(remote.get('html_url')==args['pr_url'] and remote.get('state')=='open', 'submitted_pr_not_open_on_github')
    require(remote.get('head',{}).get('sha')==args['head_sha'], 'submitted_pr_head_mismatch')
    require(remote.get('base',{}).get('ref')==kanban.BASE, 'submitted_pr_wrong_base')
    return kanban.submit(registry,args)
