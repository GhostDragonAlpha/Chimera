"""Review is a durable queue, not one of the ten development slots."""

def development(c):
    return c['state']!='DONE' and c.get('lane','DEVELOPMENT')=='DEVELOPMENT'

def free_slot(b):
    used={c['slot'] for c in b['cards'].values() if development(c)}
    return next((n for n in range(1,11) if n not in used),None)

def detach(b,c):
    if not b.get('separate_review_lane'):return
    c.setdefault('slot_history',[])
    if development(c):c['slot_history'].append(c['slot'])
    c['lane']='REVIEW'
    c['review_branch']='review/'+c['id']
    c['publication_branch']=c['review_branch']
    # Historical slot is retained for old attempt checkouts only. It no longer
    # occupies development capacity or gives authority over that numbered branch.

def corrections(b,c):
    if not b.get('separate_review_lane'):return
    if any(r['status']=='PENDING' for r in c.get('publication_requests',[])) or pending_review_prs(c):
        detach(b,c)  # an already submitted correction must not be duplicated
        c['state']='REVIEW' if c['prs'] else 'PUBLICATION_PENDING'
    elif not development(c):
        c['lane']='CORRECTION_QUEUED'

def refill_corrections(b):
    if not b.get('separate_review_lane'):return
    for c in b['cards'].values():
        if c.get('lane')!='CORRECTION_QUEUED' or c['state']=='DONE':continue
        slot=free_slot(b)
        if slot is None:return
        c.update(slot=slot,lane='DEVELOPMENT')

def sections(b):
    return {'development':[c['id'] for c in b['cards'].values() if development(c)],
            'review':[c['id'] for c in b['cards'].values() if c['state']!='DONE' and c.get('lane')=='REVIEW'],
            'corrections':[c['id'] for c in b['cards'].values() if c['state']!='DONE' and c.get('lane')=='CORRECTION_QUEUED']}

def checkpoint_packet(c,a,agent):
    import kanban as k
    packet=k.packet(c,a,'CHECKPOINT_FOR_COORDINATION')
    packet['park_template']={'agent_id':agent,'task_id':c['id'],'attempt_id':a['id'],
        'checkpoint':'REPLACE with exact saved work or explicitly no writes made','writes_stopped':True}
    packet['next_action']='This task left Development. Preserve your existing work, cease writes, save the completed park_template and immediately run E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id '+agent+' --park PATH_TO_JSON. Execute its next assignment. Do not resume detached work or publish to its former numbered slot.'
    return packet

def pending_review_prs(c):
    """Non-rejected candidates, newest submission first; old findings stay intact."""
    result=[]
    for url,pr in c['prs'].items():
        rejected=((pr.get('review') or {}).get('verdict')=='CHANGES_REQUIRED' and
                  (pr.get('review') or {}).get('head_sha')==pr['head_sha']) or any(
            r['state']=='COMPLETE' and r.get('verdict')=='CHANGES_REQUIRED' and
            r['pr_url']==url and r['head_sha']==pr['head_sha'] and
            r['criteria_sha256']==c['criteria_sha256'] for r in c.get('worker_reviews',[]))
        if not rejected:result.append((url,pr))
    order={r['pr_url']:i for i,r in enumerate(c.get('submission_history',[]))}
    return sorted(result,key=lambda row:order.get(row[0],-1),reverse=True)
