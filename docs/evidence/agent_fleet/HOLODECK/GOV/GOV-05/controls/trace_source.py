"""R7/R8: read-only measurements of the DEPLOYED source text at base.

R7 — locate the eight preregistered crash-recovery/publication semantics in
     tools/agent_fleet/control.py and tools/agent_fleet/publish.py at base
     62b8e357, quote them with their ACTUAL line numbers, and verify the key
     named refusals/fields are present (verdict computed, 8/8 threshold).
R8 — the known-regression delta: owner_instance textual occurrences in the
     interceptor claim path (review_handoff.py, predicted 0) vs the base
     controller (control.py, prereg-time count 8; exact measured count
     reported), quoting the bind sites.

Never opens a network connection; reads repo files only.
"""
import json
import os
import re
import sys


def read(repo, rel):
    with open(os.path.join(repo, rel), encoding='utf-8') as f:
        return f.read().splitlines()


def find(lines, pattern, start=0):
    pat = re.compile(pattern)
    for i in range(start, len(lines)):
        if pat.search(lines[i]):
            return i + 1          # 1-based line number
    return None


def quote(lines, lo, hi):
    return '\n'.join('    %d: %s' % (n, lines[n - 1])
                     for n in range(lo, hi + 1))


def run_r7(repo, path):
    out = ['R7 DEPLOYED-SOURCE TRACE at base 62b8e357 (source-only; the live',
           'service was never contacted) — threshold 8/8 semantics present',
           'with quoted lines. Line numbers below are MEASURED at this base;',
           'where PREREG cited approximate numbers, the actuals are recorded',
           'here and noted in RESULT.md.', '']
    ctl = read(repo, 'tools/agent_fleet/control.py')
    pub = read(repo, 'tools/agent_fleet/publish.py')
    results = []

    def check(label, ok, evidence):
        results.append(ok)
        out.append('(%s) %s -> %s' % (len(results), label,
                                      'PRESENT' if ok else 'MISSING'))
        out.append(evidence)
        out.append('')

    # (1) recover gates: RECOVERY_HOLD-only, resources_still_held, READY at
    #     generation+1, slot freed
    n = find(ctl, r"if op=='recover'")
    ev = quote(ctl, n, n + 17)
    ok = (find(ctl, r"'not_recovery_hold'", n) is not None
          and find(ctl, r"'resources_still_held'", n) is not None
          and find(ctl, r"state='READY',owner=None,slot=None,"
                        r"generation=t\['generation'\]\+1", n) is not None)
    check('recover gates (not_recovery_hold + resources_still_held + READY '
          'ownerless at generation+1, provision preserved, slot freed) at '
          'control.py:%d' % n, ok, ev)

    # (2) _fail: RECOVERY_HOLD + generation+1 for owned active tasks
    n = find(ctl, r'def _fail')
    ev = quote(ctl, n, n + 15)
    ok = ("t['state']='RECOVERY_HOLD';t['generation']+=1"
          in '\n'.join(ctl[n - 1:n + 15]))
    check('_fail: owned RUNNING/BLOCKED/REVIEW -> RECOVERY_HOLD with '
          'generation+1 at control.py:%d' % n, ok, ev)

    # (3) _preserve_provision: bounded history, active fields cleared
    n = find(ctl, r'def _preserve_provision')
    ev = quote(ctl, n, n + 21)
    seg = '\n'.join(ctl[n - 1:n + 21])
    ok = ('preserved_provisions' in seg and 'PRESERVED_PROVISION_LIMIT'
          in '\n'.join(ctl[n - 1:n + 30]) and "engine['provisioned']=False" in seg)
    check('_preserve_provision: bounded preserved_provisions history + active '
          'fields cleared at control.py:%d' % n, ok, ev)

    # (4) review_requeue: lead+epoch, REVIEW->RUNNING, head cleared, gen+1
    n = find(ctl, r"if op=='review_requeue'")
    ev = quote(ctl, n, n + 12)
    seg = '\n'.join(ctl[n - 1:n + 12])
    ok = ("'not_in_review'" in seg and "head=None" in seg
          and "t['generation']+1" in seg)
    check('review_requeue: lead+epoch-only, REVIEW->RUNNING at a NEW '
          'generation, review void (head cleared) at control.py:%d' % n,
          ok, ev)

    # (5) integration_request: lead+epoch, REVIEW-only, head identity,
    #     PENDING_EXTERNAL_BROKER with expected_base/epoch/leader
    n = find(ctl, r"if op=='integration_request'")
    ev = quote(ctl, n, n + 10)
    seg = '\n'.join(ctl[n - 1:n + 10])
    ok = ("'not_in_review'" in seg and "'head_or_branch_mismatch'" in seg
          and 'PENDING_EXTERNAL_BROKER' in seg and 'expected_base' in seg)
    check('integration_request: serialized ONE-request procedure, content-'
          'addressed expected_base, epoch+leader bound at control.py:%d' % n,
          ok, ev)

    # (6) ack_integration: trusted publisher, stale epoch, idempotence,
    #     review_changed, INTEGRATED with commit sha
    n = find(ctl, r"if op=='ack_integration'")
    ev = quote(ctl, n, n + 9)
    seg = '\n'.join(ctl[n - 1:n + 9])
    ok = ("'stale_integration_epoch'" in seg
          and "'integration_already_acknowledged'" in seg
          and "'review_changed'" in seg and "state='INTEGRATED'" in seg)
    check('ack_integration: trusted-publisher-only + stale_integration_epoch '
          '+ integration_already_acknowledged + review_changed -> INTEGRATED '
          'with content-addressed commit at control.py:%d' % n, ok, ev)

    # (7) atomic journal+state transaction and restart identity
    b = find(ctl, r"con\.execute\('BEGIN IMMEDIATE'\)")
    i = find(ctl, r'INSERT INTO events')
    u = find(ctl, r'UPDATE state SET body')
    c = find(ctl, r"con\.execute\('COMMIT'\)")
    rb = find(ctl, r"ROLLBACK")
    id1 = find(ctl, r'configuration_mismatch')
    id2 = find(ctl, r'service_identity_mismatch')
    ev = ('    %d: %s\n    %d: %s\n    %d: %s\n    %d: %s\n    %d: %s\n'
          '    %d: %s\n    %d: %s'
          % (b, ctl[b - 1], i, ctl[i - 1], u, ctl[u - 1], c, ctl[c - 1],
             rb, ctl[rb - 1], id1, ctl[id1 - 1], id2, ctl[id2 - 1]))
    ok = all(v is not None for v in (b, i, u, c, rb, id1, id2))
    check('atomic journal(event seq=revision)+state transaction '
          '(BEGIN/INSERT/UPDATE/COMMIT/ROLLBACK) and restart identity gates '
          'at control.py:%d,%d,%d,%d,%d,%d,%d' % (b, i, u, c, rb, id1, id2),
          ok, ev)

    # (8) publish.py gate chain
    marks = {
        'forbidden_branch': find(pub, r"'forbidden_branch'"),
        'task_head_mismatch_remote': find(pub, r"'task_head_mismatch_remote'"),
        'already_integrated': find(pub, r"'already_integrated': True"),
        'base_rewritten_since_task_fork': find(pub, r"'base_rewritten_since_task_fork'"),
        'non_fast_forward_refused': find(pub, r"'non_fast_forward_refused'"),
        'verification_failed_after_push': find(pub, r"'verification_failed_after_push'"),
    }
    ev = '\n'.join('    %s:%d: %s' % ('tools/agent_fleet/publish.py', ln, pub[ln - 1])
                   for ln in marks.values())
    ok = all(marks.values())
    check('publish.py gate chain (never master; content-addressed identity; '
          'interrupted-integration reconciliation before refusal; base-'
          'rewrite detection; FF-only; post-push re-verification)',
          ok, ev)

    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('R7 verdict: %s (%d/%d)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r8(repo, path):
    out = ['R8 KNOWN-REGRESSION DELTA (recorded finding, NOT adopted as the '
           'model truth) — the live claim path is served by the review-'
           'handoff interceptor whose claim bind omits owner_instance; fix '
           'in flight as PR #80 (in review at capture time).', '']
    rh = read(repo, 'tools/agent_fleet/review_handoff.py')
    ctl = read(repo, 'tools/agent_fleet/control.py')
    rh_occ = [(n, l) for n, l in enumerate(rh, 1) if 'owner_instance' in l]
    ctl_occ = [(n, l) for n, l in enumerate(ctl, 1) if 'owner_instance' in l]
    results = []
    # preregistered prediction: review_handoff.py occurrences == 0
    out.append('measured owner_instance occurrences: review_handoff.py = %d '
               '(preregistered prediction: 0); control.py = %d '
               '(prereg-time count 8; exact measured count reported)'
               % (len(rh_occ), len(ctl_occ)))
    r1 = len(rh_occ) == 0
    results.append(r1)
    out.append('R8-a interceptor claim path free of owner_instance: %s'
               % ('HOLDS' if r1 else 'MISSED — surprise finding, disclosed'))
    # the interceptor bind site: {owner, slot, state, generation} without
    # owner_instance
    n = find(rh, r'task\.update\(owner=actor')
    out.append('interceptor claim bind site (review_handoff.py:%d):' % n)
    out.append(quote(rh, n, n + 1))
    bind_text = rh[n - 1] + rh[n]   # the bind spans two source lines
    r2 = ('generation=task["generation"] + 1' in bind_text
          and 'owner_instance' not in bind_text)
    results.append(r2)
    out.append('R8-b interceptor bind omits owner_instance: %s'
               % ('HOLDS' if r2 else 'MISSED — surprise finding, disclosed'))
    # the intended bind + CAS gate in the base controller
    n_bind = find(ctl, r'owner_instance=p\.get\(\'_resolved_instance\'\)')
    n_cas = find(ctl, r'owner_instance=t\.get\(\'owner_instance\'\)')
    out.append('intended bind site (control.py:%d):' % n_bind)
    out.append(quote(ctl, n_bind - 2, n_bind))
    out.append('intended CAS gate (control.py:%d):' % n_cas)
    out.append(quote(ctl, n_cas, n_cas + 2))
    out.append('')
    out.append('CONSEQUENCE (measured, static): for interceptor-claimed tasks '
               'owner_instance stays None, so the _task instance check '
               '(control.py:%d-%d) is skipped — the INTENDED per-instance '
               'fencing is inert on the live claim path while '
               'instance_fencing==\'compat\'. The reference model models the '
               'INTENDED binding (claim carries owner_instance); the '
               'deviation is recorded here, matching the coordinator\'s '
               'known-regression note.' % (n_cas, n_cas + 2))
    out.append('all owner_instance sites in control.py: %s'
               % ', '.join(str(n) for n, _ in ctl_occ))
    verdict = 'HOLDS' if all(results) else 'MISSED'
    out.append('')
    out.append('R8 verdict: %s (%d/%d preregistered assertions)'
               % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def main():
    repo, base = sys.argv[1], sys.argv[2]
    checks = os.path.join(base, 'checks')
    os.makedirs(checks, exist_ok=True)
    r7 = run_r7(repo, os.path.join(checks, 'r7_source_trace.txt'))
    r8 = run_r8(repo, os.path.join(checks, 'r8_owner_instance_delta.txt'))
    print(json.dumps({'R7': r7, 'R8': r8}))


if __name__ == '__main__':
    main()
