"""Bounded exact-head review coverage; no liveness inference or other-owner expiry."""
from review_lane import pending_review_prs


def candidates(card):
    if card['state'] == 'DONE':
        return []
    return [(url, pr) for url, pr in pending_review_prs(card)
            if not ((pr.get('review') or {}).get('verdict') == 'ACCEPTED'
                    and pr['review'].get('head_sha') == pr['head_sha'])]


def coverage(card, url, pr):
    return [r for r in card.get('worker_reviews', [])
            if r['pr_url'] == url and r['head_sha'] == pr['head_sha']
            and r['criteria_sha256'] == card['criteria_sha256']
            and (r['state'] == 'WORKING' or
                 (r['state'] == 'COMPLETE' and r.get('verdict') == 'PASS'))]


def target(pr):
    # Only the lead's bounded request_review() mutation writes this allowance.
    return 1 + sum(a.get('head_sha') == pr['head_sha'] for a in pr.get('additional_review_authorizations', []))


def resume_allowed(card, review):
    pr = dict(candidates(card)).get(review['pr_url'])
    if not pr or review['head_sha'] != pr['head_sha']:
        return False
    if review['criteria_sha256'] != card['criteria_sha256']:
        return False
    rows = coverage(card, review['pr_url'], pr)
    # Keep completed evidence first, then oldest assignments. Never mutate a
    # different worker: excess owners retire their own record at next startup.
    rows.sort(key=lambda r: r['state'] != 'COMPLETE')
    return review['id'] in {r['id'] for r in rows[:target(pr)]}


def available(cards, agent, task_id=None):
    from delivery import priority
    result = []
    for card in cards:
        if task_id and card['id'] != task_id:
            continue
        for url, pr in candidates(card):
            if card['attempts'][pr['attempt_id']]['agent_id'] == agent:
                continue
            rows = coverage(card, url, pr)
            if any(r['agent_id'] == agent for r in rows):
                continue
            if len(rows) >= target(pr):
                continue
            result.append((len(rows), priority(card['spec']), card['slot'], card, url, pr))
    return sorted(result, key=lambda r: r[:3])


def request_review(registry, args):
    """Lead may commission one extra review for a concrete risk (max three)."""
    from agent_slots import require
    from operational_lead import authority
    with registry.transaction() as state:
        card = state['kanban']['cards'][args['task_id']]
        authority(state, args, card, approval=False)
        pr = card['prs'][args['pr_url']]
        require(pr['head_sha'] == args['head_sha'], 'review_head_changed')
        require(args['pr_url'] in dict(candidates(card)), 'candidate_not_reviewable')
        require(isinstance(args.get('reason'), str) and 0 < len(args['reason'].strip()) <= 2000,
                'additional_review_reason_required')
        rows = pr.setdefault('additional_review_authorizations', [])
        require(sum(a.get('head_sha') == pr['head_sha'] for a in rows) < 2, 'additional_review_limit')
        rows.append(dict(actor=args['actor'], reason=args['reason'], head_sha=pr['head_sha']))
        registry.event(state, 'additional_review_requested', dict(task=card['id'], head=pr['head_sha']))
        return {'state': 'ADDITIONAL_REVIEW_AUTHORIZED', 'target': target(pr)}
