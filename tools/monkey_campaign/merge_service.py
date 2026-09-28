"""Read-only worklist for the connected lead; no credentials or merge side effects."""
from kanban import LEAD

def queue(registry):
    b=registry.readonly()['kanban'];ready=[];blocked=[]
    for c in b['cards'].values():
        if c['state']=='DONE':continue
        for url,pr in c['prs'].items():
            review=pr.get('review') or {}
            if review.get('verdict')!='ACCEPTED':continue
            reasons=[]
            if review.get('head_sha')!=pr['head_sha'] or review.get('criteria_sha256')!=c['criteria_sha256']:
                reasons.append('approval_head_or_criteria_mismatch')
            if any(m['status']=='OPEN' and (m['author']==LEAD or m.get('authority')=='OPERATIONAL_LEAD') and m.get('pr_url') in (None,url) for m in c['messages']):
                reasons.append('unresolved_applicable_findings')
            row={'task_id':c['id'],'pr_url':url,'expected_head_sha':pr['head_sha'],'criteria_sha256':c['criteria_sha256'],'evidence_reference':review.get('evidence_reference')}
            if reasons:blocked.append(dict(row,reasons=reasons))
            else:ready.append(row)
    return {'service':b.get('merge_service',{}),'ready_for_connected_lead':ready,'blocked':blocked,
            'limits':'Local acceptance worklist only. Re-fetch GitHub head/base/checks, mark ready, merge with expected head, then CLI accept-merge. No merged state is inferred here.'}

def coordination_actionable(row,connected_lead_only):
    if row['requests']:return True
    for url,pr in row['prs'].items():
        if (pr.get('review') or {}).get('verdict')=='ACCEPTED':
            if not connected_lead_only:return True
            continue
        if any(r['state']=='COMPLETE' and r.get('verdict')=='PASS' and r['pr_url']==url and r['head_sha']==pr['head_sha'] for r in row['worker_reviews']):return True
    return False
