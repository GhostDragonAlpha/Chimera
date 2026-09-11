"""Execute PREREG R1-R6 controls against the GOV-05 reference model.

Read-only w.r.t. the model file. Writes nothing except the six evidence
*.txt files under checks/ (paths derived from the evidence dir given on the
command line). Each control records refusals verbatim and computes every
post-state assertion; verdicts are computed, never asserted.

Card falsifier under test: "Duplicate publication or orphaned ownership
changes task truth" — R4 (duplicate publication) and R5 (orphaned ownership)
must show the model refusing every such path; R2 shows a kill
mid-transaction cannot corrupt state or journal; R3 shows the epoch/leader/
identity gates hold; R6 shows replay reconstructs accepted task state.

Fixture note: add_agent/add_task/add_slot and the remote's commit DAG are
test-registry setup, NOT modeled contract ops (see the model docstring); the
R6 replay therefore restarts from the captured fixture baseline and
re-executes only journaled (contract) ops.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'reference'))
from gov05_reference_model import (ReferenceModel, Refusal, Remote,  # noqa: E402
                                   Crash)

def reason_of(result):
    """Named refusal without its detail suffix (detail kept verbatim
    in the recorded output lines)."""
    return result[1].split(' (')[0] if result[0] == 'REFUSED' else result[1]


BASE = '62b8e35757c71e31d621c26b32a7c52558905b02'


def sha(token):
    """Deterministic 40-hex content-address-looking token for fixtures."""
    return hashlib.sha256(token.encode()).hexdigest()[:40]


def attempt(fn, *a, **kw):
    try:
        return ('OK', fn(*a, **kw))
    except Refusal as exc:
        return ('REFUSED', str(exc))
    except Crash as exc:
        return ('CRASHED', str(exc))


def fresh(remote=None):
    m = ReferenceModel(remote=remote)
    m.add_agent('alice', {'cpu', 'docs', 'python'}, max_tasks=2)
    m.add_agent('bob', {'cpu', 'docs', 'python'}, max_tasks=2)
    for n in ('1', '2', '3'):
        m.add_slot(n)
    return m


def scenario_remote():
    """root -> base(62b8e357) on the integration branch."""
    r = Remote()
    root = r.add_commit(sha('root'), None)
    r.add_commit(BASE, root)
    r.set_ref('astra/gait-capture', BASE)
    return r


def workspace(remote=None, leader='alice'):
    m = fresh(remote)
    m.leader = leader
    m.epoch = 1
    m.add_task('t1', ['docs/evidence/x'], base=BASE)
    m.add_task('t2', ['docs/evidence/y'], base=BASE)
    return m


def review_state(remote, tid='t1', owner='alice', token='head'):
    """Fixture: claim + submit_review; ALSO publishes the task-branch ref to
    the modeled remote (in the deployed world the worker pushes its task
    branch before publication is possible — publish.py:73-74 reads it)."""
    h = sha(token)
    remote.add_commit(h, remote.refs['astra/gait-capture'])
    remote.set_ref('astra/tasks/' + tid, h)
    m = workspace(remote)
    m.claim(owner, tid)
    m.submit_review(owner, tid, h)
    return m, h


def assert_eq(out, label, actual, expected, results):
    ok = actual == expected
    results.append(ok)
    out.append('  assert %s == %r (actual %r) -> %s'
               % (label, expected, actual, 'OK' if ok else 'MISMATCH'))
    return ok


def snapshot_fields(m, tids):
    snap = m.snapshot()
    return {t: {f: snap['tasks'][t][f]
                for f in ('state', 'owner', 'generation', 'slot', 'head',
                          'checkpoint', 'owner_instance')}
            for t in tids}


def run_r1(path):
    out = ['R1 POSITIVE CONTROLS (model must ACCEPT) — threshold 6/6 cases,',
           'every case asserting all its post-conditions', '']
    results = []
    # ---- (a) legal chain: claim -> checkpoint -> submit_review ->
    #          integration_request; exactly one PENDING request
    remote = scenario_remote()
    m, head = review_state(remote)
    rid = m.integration_request('alice', 1, 't1', head, 'astra/tasks/t1', BASE)
    r = m.requests[rid]
    ok = (r['state'] == 'PENDING_EXTERNAL_BROKER' and r['head'] == head
          and r['expected_base'] == BASE and r['epoch'] == 1
          and r['leader'] == 'alice'
          and sum(1 for q in m.requests.values()
                  if q['state'] == 'PENDING_EXTERNAL_BROKER') == 1)
    results.append(ok)
    out.append('(a) legal chain to one PENDING request %r: %s'
               % (rid, 'OK' if ok else 'MISMATCH'))
    # ---- (b) publish: FF push success, remote base becomes the task head
    outcome = m.publish(rid)
    ok = (outcome == 'pushed' and remote.refs['astra/gait-capture'] == head
          and remote.push_count == 1)
    results.append(ok)
    out.append('(b) publish pushed: outcome=%r remote_base==head:%s '
               'push_count=%d: %s'
               % (outcome, remote.refs['astra/gait-capture'] == head,
                  remote.push_count, 'OK' if ok else 'MISMATCH'))
    # ---- (c) ack: INTEGRATED with content-addressed commit
    commit = sha('merge-t1')
    m.ack('SUPERVISOR', rid, commit, base_branch='astra/gait-capture',
          expected_base=BASE)
    t1 = m.snapshot()['tasks']['t1']
    ok = (t1['state'] == 'INTEGRATED'
          and t1['integration'] == {'commit': commit}
          and m.requests[rid]['state'] == 'ACKNOWLEDGED')
    results.append(ok)
    out.append('(c) ack -> INTEGRATED, integration.commit content-addressed: %s'
               % ('OK' if ok else 'MISMATCH: %r' % t1))
    # ---- (d) crash mid-transaction then retry == never-crashed control
    def build(run_crash):
        rem = scenario_remote()
        mx = workspace(rem)
        mx.claim('alice', 't1')
        if run_crash:
            mx.arm_crash()                    # kill armed at the commit boundary
            killed = attempt(mx.mutate, 'alice', 1, 't1')
            assert killed[0] == 'CRASHED', killed
        else:
            mx.mutate('alice', 1, 't1')
        return mx
    crashed, control = build(True), build(False)
    crashed.mutate('alice', 1, 't1')          # the retry after the crash
    ok = crashed.snapshot() == control.snapshot()
    results.append(ok)
    out.append('(d) crash-mid-transaction then retry: state == never-crashed '
               'control (full 9-field registry snapshot equality): %s'
               % ('OK' if ok else 'MISMATCH'))
    # ---- (e) fail -> recover cycle: READY gen+1, ownerless, slot freed,
    #          provision preserved (record retained, active fields cleared)
    m2 = workspace(scenario_remote())
    m2.claim('alice', 't1')
    m2.provision_slot('SUPERVISOR', 't1', sha('wt-head'), 'provision evidence')
    m2.fail('alice', 'PROCESS_EXIT')
    gen_after_fail = m2.snapshot()['tasks']['t1']['generation']
    m2.recover('SUPERVISOR', 't1', sha('preservation-evidence'))
    snap = m2.snapshot()
    t1 = snap['tasks']['t1']
    engine = snap['slots']['1']['engine']
    hist = engine.get('preserved_provisions', [])
    ok = (t1['state'] == 'READY' and t1['owner'] is None
          and t1['slot'] is None
          and t1['generation'] == gen_after_fail + 1
          and snap['slots']['1']['task'] is None
          and len(hist) == 1
          and hist[0]['provision_task'] == 't1'
          and hist[0]['provision_generation'] == 1
          and hist[0]['reason'] == 'recovered_task_generation'
          and engine.get('provisioned') is False
          and engine.get('provision_task') is None)
    results.append(ok)
    out.append('(e) fail->recover: READY gen %d (after fail gen %d), '
               'ownerless, slot freed, preserved provision record (task %r, '
               'gen %r), active fields cleared: %s'
               % (t1['generation'], gen_after_fail,
                  hist[0]['provision_task'] if hist else None,
                  hist[0]['provision_generation'] if hist else None,
                  'OK' if ok else 'MISMATCH: %r %r' % (t1, engine)))
    # ---- (f) idempotence of publication (case = 2 assertions, both
    #      required): (f1) re-publish of an already-pushed head while the
    #      request is still PENDING (the lost-ack interrupted integration)
    #      -> already_integrated with NO second push; (f2) after ack, a
    #      third publish is refused integration_already_acknowledged.
    #      Disclosed refinement of the prereg wording: publish.py reads no
    #      registry state, so the registry-side witness of the same
    #      idempotence is the acknowledged-refusal; both are asserted here.
    remote3 = scenario_remote()
    m3, h3 = review_state(remote3, token='head-f')
    rid3 = m3.integration_request('alice', 1, 't1', h3, 'astra/tasks/t1', BASE)
    out3 = m3.publish(rid3)
    pc_after_first = remote3.push_count
    out3b = m3.publish(rid3)                  # lost-ack retry
    f1 = (out3 == 'pushed' and out3b == 'already_integrated'
          and remote3.push_count == pc_after_first == 1)
    m3.ack('SUPERVISOR', rid3, sha('merge-f'), base_branch='astra/gait-capture',
           expected_base=BASE)
    out3c = attempt(m3.publish, rid3)
    f2 = (out3c[0] == 'REFUSED'
          and out3c[1] == 'integration_already_acknowledged'
          and remote3.push_count == 1)
    results.append(f1 and f2)
    out.append('(f) idempotence: first=%r lost-ack retry=%r push_count=%d; '
               'post-ack publish=(%s, %r) push_count=%d -> %s'
               % (out3, out3b, pc_after_first, out3c[0], out3c[1],
                  remote3.push_count, 'OK' if (f1 and f2) else 'MISMATCH'))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('R1 verdict: %s (%d/%d cases)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r2(path):
    out = ['R2 KILL-MID-TRANSACTION (no corruption, no torn journal) — '
           'threshold 5/5', '']
    results = []
    tids = ('t1', 't2')

    def build(pending_request=True):
        remote = scenario_remote()
        m = workspace(remote)
        m.claim('alice', 't1')
        m.claim('bob', 't2')
        if pending_request:
            h = sha('t1-head')
            m.submit_review('alice', 't1', h)
            m.integration_request('alice', 1, 't1', h, 'astra/tasks/t1', BASE)
        return m

    # kill a staged checkpoint on t1
    m = build()
    before_fields = snapshot_fields(m, tids)
    before_journal = len(m.journal)
    before_rev = m.revision
    m.arm_crash()                  # kill armed at the commit boundary
    killed = attempt(m.mutate, 'alice', 1, 't1')   # staged; process died
    assert killed[0] == 'CRASHED', killed
    after_fields = snapshot_fields(m, tids)
    results.append(after_fields == before_fields)
    out.append('(a) staged state change NOT visible after crash: %s'
               % ('OK' if results[-1] else 'MISMATCH: %r vs %r'
                  % (after_fields, before_fields)))
    results.append(len(m.journal) == before_journal)
    out.append('(b) journal length unchanged (%d): %s'
               % (len(m.journal), 'OK' if results[-1] else 'MISMATCH'))
    results.append(m.revision == before_rev)
    out.append('(c) revision unchanged (%d): %s'
               % (m.revision, 'OK' if results[-1] else 'MISMATCH'))
    # (d) retry after crash == twin that never crashed
    m.mutate('alice', 1, 't1')
    twin = build()
    twin.mutate('alice', 1, 't1')
    ok = m.snapshot() == twin.snapshot()
    results.append(ok)
    out.append('(d) retry-after-crash state == never-crashed twin: %s'
               % ('OK' if ok else 'MISMATCH'))
    # (e) two crashes then one success -> exactly one new event, revision+1
    m2 = build()
    rev0, j0 = m2.revision, len(m2.journal)
    for _ in range(2):                 # two kills at the commit boundary
        m2.arm_crash()
        assert attempt(m2.mutate, 'alice', 1, 't1')[0] == 'CRASHED'
    m2.mutate('alice', 1, 't1')        # the one that commits
    ok = (m2.revision == rev0 + 1 and len(m2.journal) == j0 + 1
          and m2.journal[-1]['seq'] == rev0 + 1)
    results.append(ok)
    out.append('(e) 2 crashes + 1 success -> one event seq=%d (rev %d): %s'
               % (m2.journal[-1]['seq'], m2.revision,
                  'OK' if ok else 'MISMATCH'))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('R2 verdict: %s (%d/%d)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def review_pending(token='head'):
    """t1 REVIEWed with a PENDING integration request at epoch 1."""
    remote = scenario_remote()
    m, h = review_state(remote, token=token)
    rid = m.integration_request('alice', 1, 't1', h, 'astra/tasks/t1', BASE)
    return m, rid, h


def run_r3(path):
    out = ['R3 STALE-EPOCH / SERIALIZED-INTEGRATION REFUSALS — threshold 5/5',
           '',
           '(a)/(b) exercise the two conjuncts of the ack epoch+leader gate',
           '(control.py:716 stale_integration_epoch). Under the deployed',
           'fail->election (control.py:147 _elect) epoch and leader move',
           'together, so each case isolates one conjunct of the same named',
           'refusal.', '']
    results = []
    # (a) ack after the epoch moved (leader failed -> election bumped epoch)
    m, rid, h = review_pending()
    m.fail('alice', 'PROCESS_EXIT')            # epoch 1 -> 2, leader -> bob
    snap = m.snapshot()
    r = attempt(m.ack, 'SUPERVISOR', rid, sha('merge-x'),
                base_branch='astra/gait-capture', expected_base=BASE)
    ok = (r[0] == 'REFUSED' and r[1] == 'stale_integration_epoch'
          and snap['requests'][rid]['state'] == 'PENDING_EXTERNAL_BROKER'
          and snap['tasks']['t1']['state'] == 'RECOVERY_HOLD'
          and snap['tasks']['t1']['head'] == h
          and snap['requests'][rid]['epoch'] == 1
          and snap['epoch'] == 2)
    results.append(ok)
    out.append('(a) ack with pre-fail epoch (req epoch 1, registry epoch 2): '
               '(%s, %r); request PENDING, task head intact: %s'
               % (r[0], r[1], 'OK' if ok else 'MISMATCH'))
    # (b) the leader conjunct: request bound to alice, leader is now bob
    m2, rid2, h2 = review_pending(token='head-b')
    m2.fail('alice', 'PROCESS_EXIT')
    snap2 = m2.snapshot()
    req2 = snap2['requests'][rid2]
    pre = (req2['leader'] == 'alice' and snap2['leader'] == 'bob'
           and req2['epoch'] != snap2['epoch'])
    r2 = attempt(m2.ack, 'SUPERVISOR', rid2, sha('merge-y'),
                 base_branch='astra/gait-capture', expected_base=BASE)
    ok2 = (pre and r2[0] == 'REFUSED'
           and r2[1] == 'stale_integration_epoch')
    results.append(ok2)
    out.append('(b) ack with leader-mismatched request (req leader %r vs '
               'registry %r): (%s, %r): %s'
               % (req2['leader'], snap2['leader'], r2[0], r2[1],
                  'OK' if ok2 else 'MISMATCH'))
    # (c) second ack on an acknowledged request
    m3, rid3, h3 = review_pending(token='head-c')
    m3.publish(rid3)
    m3.ack('SUPERVISOR', rid3, sha('merge-z'), base_branch='astra/gait-capture',
           expected_base=BASE)
    r3 = attempt(m3.ack, 'SUPERVISOR', rid3, sha('merge-z2'),
                 base_branch='astra/gait-capture', expected_base=BASE)
    snap3 = m3.snapshot()
    ok3 = (r3[0] == 'REFUSED'
           and r3[1] == 'integration_already_acknowledged'
           and snap3['tasks']['t1']['integration'] == {'commit': sha('merge-z')})
    results.append(ok3)
    out.append('(c) second ack: (%s, %r); first commit preserved: %s'
               % (r3[0], r3[1], 'OK' if ok3 else 'MISMATCH'))
    # (d) integration_request while RUNNING
    m4 = workspace(scenario_remote())
    m4.claim('alice', 't1')
    r4 = attempt(m4.integration_request, 'alice', 1, 't1', sha('nope'),
                 'astra/tasks/t1', BASE)
    ok4 = r4[0] == 'REFUSED' and r4[1] == 'not_in_review'
    results.append(ok4)
    out.append('(d) integration_request while RUNNING: (%s, %r): %s'
               % (r4[0], r4[1], 'OK' if ok4 else 'MISMATCH'))
    # (e) integration_request with a head that differs from the recorded head
    m5, rid5, h5 = review_pending(token='head-e')
    r5 = attempt(m5.integration_request, 'alice', 1, 't1', sha('forged'),
                 'astra/tasks/t1', BASE)
    ok5 = r5[0] == 'REFUSED' and r5[1] == 'head_or_branch_mismatch'
    results.append(ok5)
    out.append('(e) integration_request head mismatch: (%s, %r): %s'
               % (r5[0], r5[1], 'OK' if ok5 else 'MISMATCH'))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('SERIALIZED-INTEGRATION verdict in the reference model: '
               'stale/foreign publication paths all refused -> %s' % verdict)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r4(path):
    out = ['R4 DUPLICATE PUBLICATION / OVERWRITE PROTECTION (card falsifier',
           'clause 1: "Duplicate publication ... changes task truth") — model',
           'must REJECT — threshold 5/5, push_count asserted in every case',
           'and the remote base ref never moved backwards or sideways', '']
    results = []
    # (a) already-integrated head: re-publish reports integrated, no push
    remote = scenario_remote()
    m, h = review_state(remote)
    rid = m.integration_request('alice', 1, 't1', h, 'astra/tasks/t1', BASE)
    m.publish(rid)                              # pushes; push_count 1
    pc = remote.push_count
    base_after_first = remote.refs['astra/gait-capture']
    outcome = m.publish(rid)                    # the duplicate attempt
    ok = (outcome == 'already_integrated' and remote.push_count == pc == 1
          and remote.refs['astra/gait-capture'] == base_after_first == h)
    results.append(ok)
    out.append('(a) duplicate publish -> already_integrated, push_count %d, '
               'base unchanged: %s'
               % (remote.push_count, 'OK' if ok else 'MISMATCH'))
    # (b) base legitimately advanced (unpublished newer work landed): the
    #     task head chains from the OLD base -> non_fast_forward_refused,
    #     remote base UNCHANGED
    remote2 = scenario_remote()
    advanced = remote2.add_commit(sha('other-lane-integration'), BASE)
    remote2.set_ref('astra/gait-capture', advanced)
    h2 = sha('head-b')
    remote2.add_commit(h2, BASE)                # task head chains from OLD base
    remote2.set_ref('astra/tasks/t1', h2)
    m2 = workspace(remote2)
    m2.claim('alice', 't1')
    m2.submit_review('alice', 't1', h2)
    rid2 = m2.integration_request('alice', 1, 't1', h2, 'astra/tasks/t1', BASE)
    r2 = attempt(m2.publish, rid2)
    ok = (r2[0] == 'REFUSED' and reason_of(r2) == 'non_fast_forward_refused'
          and remote2.push_count == 0
          and remote2.refs['astra/gait-capture'] == advanced)
    results.append(ok)
    out.append('(b) diverged base -> (%s, %r); push_count %d; newer work '
               'still at base: %s'
               % (r2[0], r2[1], remote2.push_count, 'OK' if ok else 'MISMATCH'))
    # (c) base rewritten since the fork: expected_base not an ancestor
    remote3 = scenario_remote()
    stranger = remote3.add_commit(sha('rewritten-root-child'), None)
    remote3.set_ref('astra/gait-capture', stranger)
    h3 = sha('head-c')
    remote3.add_commit(h3, BASE)
    remote3.set_ref('astra/tasks/t1', h3)
    m3 = workspace(remote3)
    m3.claim('alice', 't1')
    m3.submit_review('alice', 't1', h3)
    rid3 = m3.integration_request('alice', 1, 't1', h3, 'astra/tasks/t1', BASE)
    r3 = attempt(m3.publish, rid3)
    ok = (r3[0] == 'REFUSED' and r3[1] == 'base_rewritten_since_task_fork'
          and remote3.push_count == 0
          and remote3.refs['astra/gait-capture'] == stranger)
    results.append(ok)
    out.append('(c) rewritten base -> (%s, %r); push_count %d: %s'
               % (r3[0], r3[1], remote3.push_count, 'OK' if ok else 'MISMATCH'))
    # (d) remote task branch moved off the registry head
    remote4 = scenario_remote()
    h4 = sha('head-d')
    remote4.add_commit(h4, BASE)
    remote4.set_ref('astra/tasks/t1', sha('tampered'))
    m4 = workspace(remote4)
    m4.claim('alice', 't1')
    m4.submit_review('alice', 't1', h4)
    rid4 = m4.integration_request('alice', 1, 't1', h4, 'astra/tasks/t1', BASE)
    r4 = attempt(m4.publish, rid4)
    ok = (r4[0] == 'REFUSED' and reason_of(r4) == 'task_head_mismatch_remote'
          and remote4.push_count == 0)
    results.append(ok)
    out.append('(d) remote task branch tampered -> (%s, %r); push_count %d: %s'
               % (r4[0], r4[1], remote4.push_count, 'OK' if ok else 'MISMATCH'))
    # (e) publication targeting the forbidden branch
    remote5 = scenario_remote()
    h5 = sha('head-e')
    remote5.add_commit(h5, BASE)
    remote5.set_ref('master', h5)
    m5 = workspace(remote5)
    m5.claim('alice', 't1')
    m5.submit_review('alice', 't1', h5)
    m5.tasks['t1']['branch'] = 'master'         # fixture surgery: the request
    rid5 = m5.integration_request('alice', 1, 't1', h5, 'master', BASE)
    r5 = attempt(m5.publish, rid5)
    ok = (r5[0] == 'REFUSED' and r5[1] == 'forbidden_branch'
          and remote5.push_count == 0)
    results.append(ok)
    out.append('(e) forbidden branch -> (%s, %r); push_count %d: %s'
               % (r5[0], r5[1], remote5.push_count, 'OK' if ok else 'MISMATCH'))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('CARD FALSIFIER CLAUSE 1 in the reference model: NOT '
               'reproduced (no duplicate publication; unpublished/newer '
               'work never overwritten) -> %s' % verdict)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r5(path):
    out = ['R5 ORPHANED OWNERSHIP (card falsifier clause 2: "orphaned',
           'ownership changes task truth") — model must REJECT — threshold',
           '4/4', '']
    results = []
    # (a) fail -> RECOVERY_HOLD gen+1; orphan's old-generation mutation refused
    m = workspace(scenario_remote())
    m.claim('alice', 't1')
    m.mutate('alice', 1, 't1')
    m.fail('alice', 'PROCESS_EXIT')
    snap = m.snapshot()
    t1 = snap['tasks']['t1']
    r = attempt(m.mutate, 'alice', 1, 't1')     # pre-fail generation
    ok = (t1['state'] == 'RECOVERY_HOLD' and t1['generation'] == 2
          and r[0] == 'REFUSED' and r[1] == 'stale_or_foreign_claim')
    results.append(ok)
    out.append('(a) fail -> RECOVERY_HOLD gen 2; orphan mutate at gen 1: '
               '(%s, %r): %s' % (r[0], r[1], 'OK' if ok else 'MISMATCH'))
    # (b) recover while a resource is still held -> refused, state unchanged
    m.resources['rtx4090'] = {'task': 't1'}
    before = snapshot_fields(m, ('t1',))
    r = attempt(m.recover, 'SUPERVISOR', 't1', sha('pres'))
    after = snapshot_fields(m, ('t1',))
    ok = r[0] == 'REFUSED' and r[1] == 'resources_still_held' and after == before
    results.append(ok)
    out.append('(b) recover with held resource: (%s, %r); state unchanged: %s'
               % (r[0], r[1], 'OK' if ok else 'MISMATCH'))
    m.resources.clear()
    # (c) recover on a non-HOLD task -> refused, unchanged
    m2 = workspace(scenario_remote())
    m2.claim('bob', 't2')
    before2 = snapshot_fields(m2, ('t2',))
    r = attempt(m2.recover, 'SUPERVISOR', 't2', sha('pres2'))
    ok = (r[0] == 'REFUSED' and r[1] == 'not_recovery_hold'
          and snapshot_fields(m2, ('t2',)) == before2)
    results.append(ok)
    out.append('(c) recover on RUNNING task: (%s, %r); unchanged: %s'
               % (r[0], r[1], 'OK' if ok else 'MISMATCH'))
    # (d) recover + re-claim by B: orphan refused at the pre-fail generation;
    #     generation chain follows the deployed monotone bumps; provision
    #     history retained with its task/generation identity.
    m3 = workspace(scenario_remote())
    m3.claim('alice', 't1')
    m3.provision_slot('SUPERVISOR', 't1', sha('wt'), 'prov')
    m3.fail('alice', 'PROCESS_EXIT')              # gen 2
    m3.recover('SUPERVISOR', 't1', sha('pres3'))  # gen 3, READY
    m3.claim('bob', 't1')                         # gen 4 per deployed chain
    snap3 = m3.snapshot()
    t1 = snap3['tasks']['t1']
    r = attempt(m3.mutate, 'alice', 1, 't1')
    hist = snap3['slots']['1']['engine'].get('preserved_provisions', [])
    ok = (r[0] == 'REFUSED' and r[1] == 'stale_or_foreign_claim'
          and t1['owner'] == 'bob' and t1['generation'] == 4
          and len(hist) == 1
          and hist[0]['provision_task'] == 't1'
          and hist[0]['provision_generation'] == 1)
    results.append(ok)
    out.append('(d) orphan gen-1 mutate after recover+re-claim: (%s, %r); '
               'new owner %r at gen %d (deployed chain: fail +1 '
               '[control.py:140], recover +1 [control.py:646], claim +1 '
               '[control.py:554] from the claim-time gen 1); preserved '
               'provision %r: %s'
               % (r[0], r[1], t1['owner'], t1['generation'],
                  hist[0]['provision_task'] if hist else None,
                  'OK' if ok else 'MISMATCH'))
    out.append('  NOTE: PREREG text predicted "old+2" for the new claimant '
               'generation; the deployed monotone chain gives old+3 (= 4 '
               'from claim-time gen 1). The model implements the deployed '
               'chain; the prereg expectation text is corrected here and '
               'disclosed in RESULT.md (a prereg arithmetic slip, not a '
               'model or deployed-contract defect; the card falsifier is '
               'unaffected — the orphan cannot write at ANY stale '
               'generation).')
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('CARD FALSIFIER CLAUSE 2 in the reference model: NOT '
               'reproduced (orphaned ownership cannot change task truth) '
               '-> %s' % verdict)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r6(path):
    out = ['R6 REPLAY/RESTART RECONSTRUCTION (card prediction: "Replay',
           'reconstructs accepted task state without overwriting unpublished',
           'work") — threshold 14/14', '',
           'Replay re-executes the journal through the public gate chain on a',
           'fresh registry that restarts from the fixture baseline and shares',
           'the content-addressed remote; the committed registry is compared',
           'field by field. The journal itself is the audit of executions and',
           'is re-recorded at replay time (a replayed publish of an already-',
           'pushed head records already_integrated, exactly as the deployed',
           'idempotence requires), so journal-body equality is not a',
           'task-truth property and is not asserted.', '']
    results = []
    # --- build a rich committed history -------------------------------
    remote = scenario_remote()
    m = workspace(remote)
    baseline = m.snapshot()                       # fixture baseline for replay
    h1 = sha('t1-head')
    m.claim('alice', 't1')
    m.mutate('alice', 1, 't1')
    m.submit_review('alice', 't1', h1)
    remote.add_commit(h1, remote.refs['astra/gait-capture'])
    remote.set_ref('astra/tasks/t1', h1)
    rid1 = m.integration_request('alice', 1, 't1', h1, 'astra/tasks/t1', BASE)
    m.publish(rid1)                               # pushed (base -> h1)
    m2h = sha('t2-head')
    m.claim('bob', 't2')
    m.mutate('bob', 1, 't2')
    m.submit_review('bob', 't2', m2h)
    # t2 chains from the pre-h1 base first: the direct publish would be a
    # divergence refusal (that class is R4(b)); the lane rebases, which on a
    # content-addressed remote IS re-parenting the commit:
    remote.parents[m2h] = h1
    remote.set_ref('astra/tasks/t2', m2h)
    rid2 = m.integration_request('alice', 1, 't2', m2h, 'astra/tasks/t2', BASE)
    m.publish(rid2)                               # pushed (base -> m2h)
    m.ack('SUPERVISOR', rid2, sha('merge-t2'),
          base_branch='astra/gait-capture', expected_base=BASE)
    m.fail('alice', 'PROCESS_EXIT')               # t1 RECOVERY_HOLD, epoch 2
    m.recover('SUPERVISOR', 't1', sha('pres-r6'))
    m.claim('bob', 't1')
    committed = m.snapshot()
    # --- replay -------------------------------------------------------
    fresh_m = m.replay(m.journal, baseline)
    replayed = fresh_m.snapshot()
    for tid in ('t1', 't2'):
        for field in ('state', 'owner', 'generation', 'slot', 'head'):
            same = committed['tasks'][tid][field] == replayed['tasks'][tid][field]
            results.append(same)
            out.append('  %s.%s: %r == %r -> %s'
                       % (tid, field, committed['tasks'][tid][field],
                          replayed['tasks'][tid][field],
                          'OK' if same else 'MISMATCH'))
    same_rev = committed['revision'] == replayed['revision']
    results.append(same_rev)
    out.append('  revision: %r == %r -> %s'
               % (committed['revision'], replayed['revision'],
                  'OK' if same_rev else 'MISMATCH'))
    n_pend = sum(1 for r in committed['requests'].values()
                 if r['state'] == 'PENDING_EXTERNAL_BROKER')
    n_pend_r = sum(1 for r in replayed['requests'].values()
                   if r['state'] == 'PENDING_EXTERNAL_BROKER')
    results.append(n_pend == n_pend_r)
    out.append('  pending integration requests: %d == %d -> %s'
               % (n_pend, n_pend_r, 'OK' if n_pend == n_pend_r else 'MISMATCH'))
    # (13) post-replay stale ack still refused: rid1 is stale (epoch moved)
    r = attempt(fresh_m.ack, 'SUPERVISOR', rid1, sha('merge-late'),
                base_branch='astra/gait-capture', expected_base=BASE)
    ok = r[0] == 'REFUSED' and r[1] == 'stale_integration_epoch'
    results.append(ok)
    out.append('(13) post-replay stale ack refused: (%s, %r)' % (r[0], r[1]))
    # (14) post-replay publish still refuses to overwrite a diverged base:
    #      a head chaining from the OLD base must not move the base backwards
    hX = sha('unpublished-x')
    remote.add_commit(hX, BASE)                   # chains from OLD base only
    remote.set_ref('astra/tasks/tx', hX)
    m3 = fresh(remote)
    m3.leader, m3.epoch = fresh_m.leader, fresh_m.epoch
    m3.add_task('tx', ['docs/evidence/x'], base=BASE)
    m3.claim('alice', 'tx')
    m3.submit_review('alice', 'tx', hX)
    ridX = m3.integration_request(m3.leader, m3.epoch, 'tx', hX,
                                  'astra/tasks/tx', BASE)
    r2 = attempt(m3.publish, ridX)
    ok = (r2[0] == 'REFUSED' and reason_of(r2) == 'non_fast_forward_refused'
          and remote.refs['astra/gait-capture'] == m2h)
    results.append(ok)
    out.append('(14) post-replay diverged publish refused: (%s, %r); base '
               'still at the accepted head: %s'
               % (r2[0], r2[1], 'OK' if ok else 'MISMATCH'))
    out.append('  replay push_count witness: %d (replay never republishes — '
               'the deployed already_integrated idempotence)' % remote.push_count)
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('R6 verdict: %s (%d/%d)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def main(base):
    checks = os.path.join(base, 'checks')
    os.makedirs(checks, exist_ok=True)
    outcomes = {
        'R1': run_r1(os.path.join(checks, 'r1_positive.txt')),
        'R2': run_r2(os.path.join(checks, 'r2_kill_mid_transaction.txt')),
        'R3': run_r3(os.path.join(checks, 'r3_stale_epoch.txt')),
        'R4': run_r4(os.path.join(checks, 'r4_duplicate_publication.txt')),
        'R5': run_r5(os.path.join(checks, 'r5_orphaned_ownership.txt')),
        'R6': run_r6(os.path.join(checks, 'r6_replay_restart.txt')),
    }
    print(json.dumps(outcomes))


if __name__ == '__main__':
    main(sys.argv[1])
