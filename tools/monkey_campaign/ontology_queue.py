"""Deterministic ontology-derived qualification cards; no inferred acceptance."""
from copy import deepcopy
from pathlib import Path
import re
from agent_slots import require
from ontology_plan import project, load_catalog

HERE = Path(__file__).resolve().parent

def generate(projection):
    cards = []
    for t in sorted(projection['tasks'], key=lambda t: (t['dependency_layer'], t['id'])):
        if not t['selected']:
            continue
        cards.append(dict(
            id='ONT-'+t['id'], planning_ids=[t['id']],
            objective=t['title']+' — '+t['done_when'],
            depends_on=['ONT-'+d for d in t['depends_on']],
            ontology_qualification=dict(scope_sha256=projection['scope_sha256'],
                task_id=t['id'], task=t,
                definition_raw_sha256=projection['definition_raw_sha256']),
            falsifier=t['verification_profile']['falsifier'],
            steps=[
                'Reconcile existing commits, diagnostics and receipts first; reuse verified work. Do not repeat completed implementation.',
                'Read ontology ports, calculations, dependency receipts and task inbox. Freeze statement, prediction, falsifier and applicable numerical/runtime/visual probes before implementation.',
                'Implement the missing task-owned behavior in your isolated checkout. Preserve physical authority, resource admission and training gates; never invent missing anatomy or constants.',
                'Verify the exact done_when clause and profile; capture native behavior where required. Include diagnostic tags and the declared camera fields for visual evidence.',
                'Submit source/test patches and a source-bound qualification receipt for independent review; then take the next eligible card.'],
            completion='Lead-approved exact-head PR merged with full ontology qualification evidence. A diagnostic or scaffold alone cannot close this card.',
            write_authority='Only isolated attempt checkout/artifacts; production publication remains lead-serialized. Existing resource and scientific gates apply.',
        ))
    return cards

def sync(b):
    config=b.get('ontology_scheduler')
    if not config:
        return
    projection=project(load_catalog(HERE/'monkey_completion_map.json'))
    require(projection['scope_sha256']==config['scope_sha256'], 'ontology_queue_scope_changed')
    generated=generate(projection)
    # Preserve authored work and all active cards. Generated dependency cards have
    # priority only when a slot becomes free, never displacing an active assignment.
    by={s['id']:s for s in generated}
    for cid,c in b['cards'].items():
        if cid in by:
            require(c['spec']==by[cid], 'ontology_active_criteria_changed')
    authored=[s for s in b['backlog'] if not s.get('ontology_qualification')]
    b['backlog']=generated+authored

def dependencies_satisfied(b,spec):
    for dep in spec.get('depends_on',[]):
        c=b['cards'].get(dep,{})
        if c.get('state')!='DONE':
            return False
        if spec.get('ontology_qualification') and not (c.get('winner') or {}).get('ontology_qualification'):
            return False
    return True

def eligible(b,spec):
    if not dependencies_satisfied(b,spec):
        return False
    # Let already commissioned diagnostics/scaffolds finish before commissioning
    # full qualification of the same catalog task.
    q=spec.get('ontology_qualification')
    if q:
        for c in b['cards'].values():
            if c['state']!='DONE' and not c['spec'].get('ontology_qualification') and q['task_id'] in c['spec'].get('planning_ids',[]):
                return False
    return True

def qualification(c,a):
    contract=c['spec'].get('ontology_qualification')
    if not contract:
        return None
    q=a.get('ontology_qualification',{})
    require(isinstance(q,dict), 'qualification_receipt_invalid')
    require(q.get('scope_sha256')==contract['scope_sha256'] and q.get('task_id')==contract['task_id'], 'qualification_identity_required')
    require(q.get('head_sha')==a['head_sha'] and q.get('criteria_sha256')==c['criteria_sha256'], 'qualification_head_or_criteria_changed')
    require(q.get('done_when_verified') is True and q.get('profile_verified') is True, 'full_task_qualification_required')
    evidence=q.get('evidence',{})
    require(isinstance(evidence,dict), 'qualification_evidence_invalid')
    required=['numerical','source','independent_review']
    profile=contract['task']['verification_profile']
    if profile['kind']!='offline':
        required+=['visual','camera']
    if profile['kind'] in ('motion','final_playthrough'):
        required+=['runtime']
    for kind in required:
        item=evidence.get(kind,{})
        require(isinstance(item,dict), 'qualification_evidence_invalid:'+kind)
        require(isinstance(item.get('reference'),str) and bool(item['reference'].strip()) and
                re.fullmatch('[0-9a-f]{64}',item.get('raw_sha256','')) is not None,
                'qualification_evidence_required:'+kind)
    if profile['kind']!='offline':
        from visual_gate import verify
        verify(q,contract)
    # These are lead-reviewed receipts, not automated proof of physical truth.
    return deepcopy(q)
