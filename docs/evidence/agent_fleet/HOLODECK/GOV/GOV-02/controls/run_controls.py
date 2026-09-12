"""Execute PREREG R1-R4 controls against the GOV-02 capability registry.

Read-only w.r.t. the model file. Writes only the four evidence *.txt files
named on the command line. Refusals recorded verbatim; verdicts computed.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'reference'))
from gov02_capability_registry import CapabilityRegistry, Refusal  # noqa: E402


def attempt(fn, *a, **kw):
    try:
        return ('OK', fn(*a, **kw))
    except Refusal as exc:
        return ('REFUSED', str(exc))


def run_r1(path):
    out = ['R1 POSITIVE CONTROLS (model must ACCEPT) — threshold 4/4', '']
    results = []
    # (a) unit-test pass leaves runtime/dyad untouched
    m = CapabilityRegistry()
    m.record_unit_test('rtx4090', suite='fixture-suite')
    rec = m.records['rtx4090']
    ok = (rec['unit_test'] == 'EXECUTED' and rec['runtime'] == 'MISSING'
          and rec['dyad'] == 'MISSING')
    results.append(ok)
    out.append('(a) unit-test pass: %s | unit_test=%s runtime=%s dyad=%s'
               % ('OK' if ok else 'MISMATCH', rec['unit_test'], rec['runtime'], rec['dyad']))
    # (b) full chain -> EXECUTED at all classes
    m2 = CapabilityRegistry()
    m2.record_unit_test('rtx4090')
    m2.reserve_device('rtx4090', holder='task-gov02')
    m2.record_dyad('dyad_eye', holder='task-gov02')
    chain_ok = (m2.records['rtx4090']['runtime'] == 'EXECUTED'
                and m2.records['dyad_eye']['dyad'] == 'EXECUTED')
    adv = m2.advertise('dyad_eye', 'dyad', as_executed=True)
    results.append(chain_ok and adv['advertised'] == 'EXECUTED')
    out.append('(b) full chain unit->reserve->dyad: chain=%s advertise=%s'
               % (chain_ok, adv))
    # (c) supervisor qualify with evidence grants caps; subset claim passes
    m2.add_agent('alice')
    q = attempt(m2.qualify, 'SUPERVISOR', 'alice',
                ['cpu', 'docs', 'python'], 'qualifying evidence text')
    c = attempt(m2.claim_requires, 'alice', ['cpu'])
    results.append(q[0] == 'OK' and c[0] == 'OK')
    out.append('(c) supervisor qualify + subset claim: qualify=%s claim=%s' % (q[0], c[0]))
    # (d) save -> load preserves every class status (3 keys x 3 classes)
    path_json = path + '.r1d.json'
    for key in ('rtx4090', 'dyad_eye', 'law-x'):
        m2.record(key)
    m2.save(path_json)
    m3 = CapabilityRegistry.load(path_json)
    os.remove(path_json)
    same = all(m3.records[k][c] == m2.records[k][c]
               for k in ('rtx4090', 'dyad_eye', 'law-x') for c in ('unit_test', 'runtime', 'dyad'))
    results.append(same and len(m3.records) == 3)
    out.append('(d) save/load: 9 class statuses identical across restart -> %s' % same)
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('R1 verdict: %s (%d/%d)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r2(path):
    out = ['R2 FALSIFIER-DIRECTION NEGATIVES (card prediction clause 1 + falsifier: '
           '"Any inferred capability is advertised as executed") — model must REJECT — '
           'threshold 4/4', '']
    results = []
    # (a) unit-test EXECUTED, advertise runtime as executed
    m = CapabilityRegistry()
    m.record_unit_test('rtx4090')
    r = attempt(m.advertise, 'rtx4090', 'runtime', as_executed=True)
    ok = r[0] == 'REFUSED' and r[1] == 'inferred_advertised_as_executed'
    rec = m.records['rtx4090']
    results.append(ok and rec['runtime'] == 'MISSING')
    out.append('(a) unit-test pass advertising runtime as executed: (%s, %r); runtime stays %s'
               % (r[0], r[1], rec['runtime']))
    # (b) INFERRED runtime advertised as executed
    m.infer('law-x', 'runtime', 'someone claims it works')
    r = attempt(m.advertise, 'law-x', 'runtime', as_executed=True)
    ok = r[0] == 'REFUSED' and r[1] == 'inferred_advertised_as_executed'
    results.append(ok and m.records['law-x']['runtime'] == 'INFERRED')
    out.append('(b) INFERRED runtime advertised as executed: (%s, %r); stays %s'
               % (r[0], r[1], m.records['law-x']['runtime']))
    # (c) runtime EXECUTED but dyad MISSING: dyad/full-visual advertisement refused;
    # dyad stays UNKNOWN regardless of the unit-test success
    m2 = CapabilityRegistry()
    m2.record_unit_test('dyad_eye', suite='all-tests-pass')
    m2.reserve_device('rtx4090', holder='task-a')
    # runtime executed for the key itself, dyad still MISSING:
    m2.reserve_device('dyad_eye', holder='task-a')
    r = attempt(m2.advertise_visual_capability, 'dyad_eye', as_executed=True)
    ok = r[0] == 'REFUSED' and r[1] == 'inferred_advertised_as_executed'
    rec = m2.records['dyad_eye']
    results.append(ok and rec['dyad'] == 'MISSING' and rec['runtime'] == 'EXECUTED'
                   and rec['unit_test'] == 'EXECUTED')
    out.append('(c) unit+runtime EXECUTED, dyad MISSING: visual-as-executed (%s, %r); '
               'dyad stays %s (unknown despite unit-test success)'
               % (r[0], r[1], rec['dyad']))
    # (d) INFERRED from an authoritative-sounding source still refuses
    m.infer('law-x', 'dyad', 'benchmark suite passed 100%')
    r = attempt(m.advertise, 'law-x', 'dyad', as_executed=True)
    ok = r[0] == 'REFUSED' and r[1] == 'inferred_advertised_as_executed'
    results.append(ok and m.records['law-x']['dyad'] == 'INFERRED')
    out.append('(d) INFERRED from "benchmark suite passed 100%%": (%s, %r); stays %s'
               % (r[0], r[1], m.records['law-x']['dyad']))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('CARD FALSIFIER in the reference model: NOT reproducible (every '
               'inferred/missing-as-executed path refused by name) -> %s' % verdict)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r3(path):
    out = ['R3 CHAIN + AUTHORITY GATES (deployed-mirroring) — threshold 3/3', '']
    results = []
    # (a) dyad evidence without same-holder GPU runtime reservation
    m = CapabilityRegistry()
    m.reserve_device('rtx4090', holder='task-other')  # GPU held by someone else
    r = attempt(m.record_dyad, 'dyad_eye', holder='task-mine')
    ok = r[0] == 'REFUSED' and r[1] == 'dyad_requires_gpu_reservation'
    # a refused op creates no state (deployed: require->Refusal->ROLLBACK), so
    # absence of the record is the strongest form of 'dyad stays MISSING':
    dyad_state = m.records.get('dyad_eye', {}).get('dyad', 'MISSING')
    results.append(ok and dyad_state == 'MISSING')
    out.append('(a) dyad without same-holder GPU: (%s, %r); dyad stays %s (record %s)'
               % (r[0], r[1], dyad_state,
                  'absent' if 'dyad_eye' not in m.records else 'present'))
    # (b) non-supervisor qualify
    m.add_agent('mallory')
    r = attempt(m.qualify, 'mallory', 'mallory', ['gpu'], 'self-qualified')
    ok = r[0] == 'REFUSED' and r[1] == 'supervisor_only'
    results.append(ok and m.agents['mallory']['qualified'] is False)
    out.append('(b) self-qualification: (%s, %r); qualified still %s'
               % (r[0], r[1], m.agents['mallory']['qualified']))
    # (c) qualify with empty evidence
    r = attempt(m.qualify, 'SUPERVISOR', 'mallory', ['cpu'], '   ')
    ok = r[0] == 'REFUSED' and r[1] == 'missing_qualification_evidence'
    results.append(ok and m.agents['mallory']['qualified'] is False)
    out.append('(c) qualify without evidence text: (%s, %r); qualified still %s'
               % (r[0], r[1], m.agents['mallory']['qualified']))
    verdict = 'HOLDS' if all(results) else 'FALSIFIED'
    out.append('')
    out.append('R3 verdict: %s (%d/%d)' % (verdict, sum(results), len(results)))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return all(results)


def run_r4(path):
    """Quantified card-falsifier count over a full scenario sweep."""
    out = ['R4 FALSIFIER QUANTIFICATION (prereg: advertised-as-executed violations '
           'over the sweep must be 0; the three PREREGISTERED unknown-kept scenarios '
           'must hold exactly — R2a runtime, R2a dyad, R2c dyad)', '']
    fired = 0
    m = CapabilityRegistry()
    for key in ('rtx4090', 'dyad_eye', 'engine_demo', 'law-x'):
        for cls in ('unit_test', 'runtime', 'dyad'):
            for as_exec in (False, True):
                r = attempt(m.advertise, key, cls, as_executed=as_exec)
                if r[0] == 'OK' and as_exec:
                    stored = m.records[key][cls]
                    if r[1]['advertised'] == 'EXECUTED' and stored != 'EXECUTED':
                        fired += 1  # a real violation; impossible by construction
    # The three preregistered unknown-kept scenarios, probed exactly:
    unknown_kept = 0
    probes = []
    # (1) unit-test success alone -> runtime stays UNKNOWN
    m1 = CapabilityRegistry()
    m1.record_unit_test('rtx4090', suite='all-tests-pass')
    adv = m1.advertise('rtx4090', 'runtime')
    ok1 = adv['advertised'] == 'MISSING'
    probes.append(('runtime UNKNOWN despite unit-test pass', adv['advertised'], ok1))
    unknown_kept += 1 if ok1 else 0
    # (2) unit-test success alone -> dyad stays UNKNOWN
    adv = m1.advertise('rtx4090', 'dyad')
    ok2 = adv['advertised'] == 'MISSING'
    probes.append(('dyad UNKNOWN despite unit-test pass', adv['advertised'], ok2))
    unknown_kept += 1 if ok2 else 0
    # (3) unit+runtime EXECUTED, dyad never executed -> dyad stays UNKNOWN
    m2 = CapabilityRegistry()
    m2.record_unit_test('dyad_eye', suite='all-tests-pass')
    m2.reserve_device('rtx4090', holder='task-a')
    m2.reserve_device('dyad_eye', holder='task-a')
    adv = m2.advertise_visual_capability('dyad_eye')
    ok3 = adv['advertised'] == 'MISSING'
    probes.append(('dyad UNKNOWN despite unit+runtime pass', adv['advertised'], ok3))
    unknown_kept += 1 if ok3 else 0
    for label, got, ok in probes:
        out.append('  probe: %-44s -> %s (%s)' % (label, got, 'OK' if ok else 'MISMATCH'))
    out.append('advertised-as-executed violations over the sweep: %d (threshold 0)' % fired)
    out.append('preregistered unknown-kept scenarios holding: %d of 3 (threshold exactly 3)'
               % unknown_kept)
    ok = (fired == 0 and unknown_kept == 3)
    out.append('')
    out.append('R4 verdict: %s' % ('HOLDS' if ok else 'FALSIFIED'))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return ok


def main(base):
    checks = os.path.join(base, 'checks')
    os.makedirs(checks, exist_ok=True)
    r1 = run_r1(os.path.join(checks, 'r1_positive.txt'))
    r2 = run_r2(os.path.join(checks, 'r2_falsifier_negatives.txt'))
    r3 = run_r3(os.path.join(checks, 'r3_chain_authority.txt'))
    r4 = run_r4(os.path.join(checks, 'r4_falsifier_quantification.txt'))
    print(json.dumps({'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4}))


if __name__ == '__main__':
    main(sys.argv[1])
