"""Execute PREREG R1-R4 negative/positive controls against the reference model.

Read-only w.r.t. the model file. Writes nothing except the four evidence
*.txt files given on the command line. Each control records the refusal
verbatim and the full post-state assertions; verdicts are computed, never
asserted.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'reference'))
from gov01_reference_model import ReferenceModel, Refusal  # noqa: E402


def fresh_registry(max_tasks=2):
    m = ReferenceModel()
    m.add_agent('alice', {'cpu', 'docs', 'python'}, max_tasks=max_tasks)
    m.add_agent('bob', {'cpu', 'docs', 'python'}, max_tasks=max_tasks)
    for n in ('1', '2', '3'):
        m.add_slot(n)
    return m


def attempt(fn, *a, **kw):
    """Run fn; return ('OK', result) or ('REFUSED', reason)."""
    try:
        return ('OK', fn(*a, **kw))
    except Refusal as exc:
        return ('REFUSED', str(exc))


def assert_state(out, label, task, expect):
    for field in ('owner', 'generation', 'state', 'slot'):
        want = expect.get(field, task[field])
        out.append('  assert %s.%s == %r (actual %r) -> %s'
                   % (label, field, want, task[field],
                      'OK' if task[field] == want else 'MISMATCH'))


def run_r1(path):
    out = ['R1 POSITIVE CONTROLS (model must ACCEPT) — threshold 6/6', '']
    results = []
    # (a) qualified claim of a READY task
    m = fresh_registry()
    m.add_task('t1', ['docs/evidence/x'])
    r = attempt(m.claim, 'alice', 't1')
    results.append(r[0] == 'OK')
    out.append('(a) legal claim: %s %s' % r)
    # (b) second agent claims scope-disjoint task
    m.add_task('t2', ['docs/evidence/y'])
    r2 = attempt(m.claim, 'bob', 't2')
    results.append(r2[0] == 'OK')
    out.append('(b) scope-disjoint second claim: %s %s' % r2)
    # (c) checkpoint mutate with exact current generation
    r3 = attempt(m.mutate, 'alice', m.tasks['t1']['generation'], 't1',
                 payload={'k': 'v'})
    results.append(r3[0] == 'OK')
    out.append('(c) mutate with exact generation: %s %s' % r3)
    # (d) save -> new instance -> load -> mutate with pre-restart generation
    path_json = path + '.r1d.json'
    m.save(path_json)
    m2 = ReferenceModel.load(path_json)
    os.remove(path_json)
    gen = m2.tasks['t1']['generation']
    r4 = attempt(m2.mutate, 'alice', gen, 't1', payload={'k': 'v2'})
    results.append(r4[0] == 'OK')
    out.append('(d) post-reload legal mutate (gen %d): %s %s' % (gen, r4[0], r4[1] if r4[0] == 'REFUSED' else ''))
    # (e) capacity boundary: alice claims a second task with max_tasks=2
    m.add_task('t3', ['docs/evidence/z'])
    r5 = attempt(m.claim, 'alice', 't3')
    results.append(r5[0] == 'OK')
    out.append('(e) capacity boundary claim (2 of max_tasks=2): %s %s' % r5)
    # (f) casefold-prefix semantics: 'a/b' vs 'a/bc' are DISJOINT (no conflict)
    m3 = fresh_registry()
    m3.add_task('p', ['docs/w/a/b'])
    m3.add_task('q', ['docs/w/a/bc'])
    ra = attempt(m3.claim, 'alice', 'p')
    rb = attempt(m3.claim, 'bob', 'q')
    results.append(ra[0] == 'OK' and rb[0] == 'OK')
    out.append('(f) a/b vs a/bc disjoint (prefix semantics, not string prefix): claim p (%s, %r); claim q (%s, %r)'
               % (ra[0], ra[1], rb[0], rb[1]))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('R1 verdict: %s (%d/%d)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r2(path):
    out = ['R2 CONFLICTING CLAIMS (card falsifier clause 1: "Two agents own the same '
           'write scope") — model must REJECT — threshold 5/5', '']
    results = []
    cases = [
        ('(a) equal scope', ['docs/evidence/shared'], ['docs/evidence/shared']),
        ('(b) parent/child overlap', ['docs/evidence/shared'],
         ['docs/evidence/shared/child']),
        ('(c) child/parent overlap', ['docs/evidence/shared/child'],
         ['docs/evidence/shared']),
        ('(d) casefold duplicate', ['docs/Evidence/Shared'], ['docs/evidence/shared']),
    ]
    for label, scopes_a, scopes_b in cases:
        m = fresh_registry()
        m.add_task('ta', scopes_a)
        m.add_task('tb', scopes_b)
        first = attempt(m.claim, 'alice', 'ta')
        second = attempt(m.claim, 'bob', 'tb')
        ok = first[0] == 'OK' and second[0] == 'REFUSED' and second[1] == 'write_scope_conflict'
        results.append(ok)
        out.append('%s: alice(ta)=%s; bob(tb)=(%s, %r)' % (label, first[0], second[0], second[1]))
        assert_state(out, 'tb', m.tasks['tb'],
                     {'owner': None, 'generation': 0, 'state': 'READY', 'slot': None})
        out.append('  tb post-state: %s' % ('INTACT' if ok else 'VIOLATED'))
    # (e) same task claimed twice
    m = fresh_registry()
    m.add_task('t1', ['docs/evidence/one'])
    first = attempt(m.claim, 'alice', 't1')
    second = attempt(m.claim, 'bob', 't1')
    ok = first[0] == 'OK' and second[0] == 'REFUSED' and second[1] == 'task_not_ready'
    results.append(ok)
    out.append('(e) same task twice: alice=%s; bob=(%s, %r)' % (first[0], second[0], second[1]))
    assert_state(out, 't1', m.tasks['t1'],
                 {'owner': 'alice', 'generation': 1, 'state': 'RUNNING', 'slot': '1'})
    out.append('  t1 post-state: %s' % ('INTACT (single owner)' if ok else 'VIOLATED'))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('CARD FALSIFIER CLAUSE 1 in the reference model: NOT reproduced '
               '(every dual-ownership path refused) -> %s' % verdict)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r3(path):
    out = ['R3 STALE-STATE MUTATION (card falsifier clause 2: "stale state replaces a '
           'newer claim") — model must REJECT — threshold 4/4', '']
    results = []
    # (a) stale generation
    m = fresh_registry()
    m.add_task('t1', ['docs/evidence/s1'])
    m.claim('alice', 't1')                      # generation -> 1
    m.mutate('alice', 1, 't1', payload={'v': 1})  # generation stays 1 (CAS, not bumping here)
    r = attempt(m.mutate, 'alice', 0, 't1', payload={'v': 'stale'})
    ok = r[0] == 'REFUSED' and r[1] == 'stale_or_foreign_claim'
    results.append(ok)
    out.append('(a) stale generation (0 < 1): (%s, %r); payload after: %s'
               % (r[0], r[1], m.tasks['t1']['data']))
    results[-1] = ok and m.tasks['t1']['data'] == {'v': 1}
    out.append('  stale payload NOT applied: %s' % (m.tasks['t1']['data'] == {'v': 1}))
    # (b) foreign actor with owner's generation
    r = attempt(m.mutate, 'bob', 1, 't1', payload={'v': 'foreign'})
    ok = r[0] == 'REFUSED' and r[1] == 'stale_or_foreign_claim'
    results.append(ok)
    out.append('(b) foreign actor with owner generation: (%s, %r)' % (r[0], r[1]))
    # (c) unknown task
    r = attempt(m.mutate, 'alice', 1, 'nope', payload={'v': 1})
    ok = r[0] == 'REFUSED' and r[1] == 'unknown_task'
    results.append(ok)
    out.append('(c) unknown task: (%s, %r)' % (r[0], r[1]))
    # (d) release -> re-claim by B: A's old generation is stale against newer claim
    m2 = fresh_registry()
    m2.add_task('t9', ['docs/evidence/s9'])
    m2.claim('alice', 't9')
    gen_a = m2.tasks['t9']['generation']
    m2.release_and_reclaim('alice', 't9', 'bob')
    gen_b = m2.tasks['t9']['generation']
    r = attempt(m2.mutate, 'alice', gen_a, 't9', payload={'v': 'stale-owner'})
    ok = r[0] == 'REFUSED' and r[1] == 'stale_or_foreign_claim'
    results.append(ok)
    out.append('(d) old owner gen %d vs newer claim gen %d: (%s, %r); owner now %s'
               % (gen_a, gen_b, r[0], r[1], m2.tasks['t9']['owner']))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('CARD FALSIFIER CLAUSE 2 in the reference model: NOT reproduced '
               '(every stale-write path refused) -> %s' % verdict)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r4(path):
    out = ['R4 RESTART PERSISTENCE (card prediction clause 2: "active assignments '
           'survive restart") — model must PRESERVE — threshold 10/10 + 2', '']
    results = []
    m = fresh_registry()
    m.add_task('t1', ['docs/evidence/r1'])
    m.add_task('t2', ['docs/evidence/r2'])
    m.claim('alice', 't1', instance='inst-alice')
    m.claim('bob', 't2')
    m.mutate('alice', 1, 't1', payload={'stage': 'pre-restart'},
             instance='inst-alice')
    path_json = path + '.r4.json'
    m.save(path_json)
    m2 = ReferenceModel.load(path_json)
    os.remove(path_json)
    for tid in ('t1', 't2'):
        for field in ('owner', 'generation', 'state', 'slot', 'checkpoint'):
            same = m.tasks[tid][field] == m2.tasks[tid][field]
            results.append(same)
            out.append('  %s.%s: %r == %r -> %s'
                       % (tid, field, m.tasks[tid][field], m2.tasks[tid][field],
                          'OK' if same else 'MISMATCH'))
    out.append('  instance binding preserved: t1.owner_instance=%r'
               % (m2.tasks['t1']['owner_instance'],))
    results.append(m2.tasks['t1']['owner_instance'] == 'inst-alice')
    r_stale = attempt(m2.mutate, 'alice', 0, 't1', payload={'v': 'stale'})
    ok_stale = r_stale[0] == 'REFUSED' and r_stale[1] == 'stale_or_foreign_claim'
    results.append(ok_stale)
    out.append('post-reload stale mutation refused: (%s, %r)' % (r_stale[0], r_stale[1]))
    r_ok = attempt(m2.mutate, 'bob', 1, 't2', payload={'v': 'post-restart'})
    ok_ok = r_ok[0] == 'OK'
    results.append(ok_ok)
    out.append('post-reload legal mutation accepted: %s' % (r_ok[0],))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('R4 verdict: %s (%d/%d)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def main(base):
    checks = os.path.join(base, 'checks')
    os.makedirs(checks, exist_ok=True)
    r1 = run_r1(os.path.join(checks, 'r1_positive.txt'))
    r2 = run_r2(os.path.join(checks, 'r2_conflicting_claims.txt'))
    r3 = run_r3(os.path.join(checks, 'r3_stale_generation.txt'))
    r4 = run_r4(os.path.join(checks, 'r4_restart_persistence.txt'))
    print(json.dumps({'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4}))


if __name__ == '__main__':
    main(sys.argv[1])
