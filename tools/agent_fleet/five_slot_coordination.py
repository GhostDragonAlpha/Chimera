"""five_slot_coordination.py -- scripted five-client coordination driver.

Brings up a FRESH isolated five-slot registry with the REAL control service,
enrolls five agents, and drives nine preregistered coordination scenarios over
the REAL authenticated HTTP path. Evidence is written to an output directory.

LABEL: scripted clients. This driver does NOT certify the milestone
"five independent agents verified" -- that milestone requires Alan to start
one fresh agent (see docs/THE_AGENT_FLEET.md).

PREREGISTRATION (STATEMENT / PREDICTION / FALSIFIER):
- STATEMENT: five isolated clients coordinated through one controller exhibit
  capacity, FIFO resource fairness, benchmark isolation, memory admission,
  fail-hold + recovery, bootstrap guards, restart durability, the evidence
  gate, and deadlock-free progress WITHOUT any cross-client mutation.
- PREDICTION: scenarios S1-S9 all end PASS on a fresh isolated registry.
- FALSIFIER: any scenario ending FAIL, or any partial state observable in the
  exported snapshots.

Usage:  python five_slot_coordination.py [--out <dir>] [--keep]
"""
import argparse
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bootstrap_fleet import FleetBootstrap, fleet_on_port  # noqa: E402
from client import call as http_call  # noqa: E402

BASE = 'a' * 40
LEAD = 'a1'
AGENTS = ['a1', 'a2', 'a3', 'a4', 'a5']
MEMORY_BUDGET = 16384
SCOPE_DIR = 'docs/evidence/agent_fleet/FIVE-CLIENT-COORDINATION'
SCENARIOS = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']

# stale-smoke-autospawn-01: DRIFT-CATCHABLE HOOK. This driver is not
# test-imported (the unittest suite never executes it), so its scenario
# expectations can drift from the controller -- as happened when the capacity
# scenario kept pinning the superseded no_free_slot refusal after the
# slot-expansion fix deployed. The module imports with zero side effects
# (everything runs from main()), so any runner -- and main() itself -- can
# execute the loader-visible check below and refuse stale pins.
EXPECTED_SIXTH_AUTO_SPAWN = True


def test_scenario_pins_are_current():
    """Drift-catchable self-check, loader-visible for guarded import.

    Asserts the scenario source still expects the auto-spawn semantics
    (test_control.py test_five_slots_then_auto_spawn_on_sixth) and never
    re-pins the superseded no_free_slot refusal. Raises AssertionError on
    drift; returns a machine-readable detail dict otherwise. unittest can
    bind this directly: TestCase(lambda: test_scenario_pins_are_current()).
    """
    import re
    import unittest
    src = Path(__file__).read_text(encoding='utf-8')
    # Built by concatenation so this hook's own source never contains the
    # stale marker it greps for. The grep targets the capacity SCENARIO's
    # source only (prose elsewhere may name the refusal historically).
    stale_marker = 'no_free_' + 'slot'
    m = re.search(r"    def s1_capacity\(self\):.*?(?=\n    def )", src, re.S)
    scenario_src = m.group(0) if m else ''

    def _case():
        assert EXPECTED_SIXTH_AUTO_SPAWN, \
            'scenario regressed to the pre-fix refusal pin'
        assert scenario_src, 'capacity scenario not found in the driver source'
        assert stale_marker not in scenario_src, \
            'stale refusal pin re-appeared inside s1_capacity'
        assert 'auto-spawn' in scenario_src, \
            'auto-spawn expectation missing from the capacity scenario'
        assert 'test_five_slots_then_auto_spawn_on_sixth' in src, \
            'semantics anchor to the controller test suite missing'

    case = unittest.FunctionTestCase(_case)
    result = unittest.TestResult()
    case.run(result)
    if result.failures or result.errors:
        detail = (result.failures + result.errors)[0][1]
        raise AssertionError('scenario pins are STALE: %s' % detail)
    return {'expected_sixth_auto_spawn': True,
            'source': str(Path(__file__)),
            'scenarios': list(SCENARIOS)}


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _Foreign(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()
    log_message = lambda *a: None  # noqa: E731


class Driver:
    def __init__(self, registry_root, port, out):
        self.root = Path(registry_root)
        self.port = port
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.fb = FleetBootstrap(self.root, self.port)
        self.calls = {}
        self.tasks = {}
        self.results = {}
        self.events = []

    # ---- session/HTTP helpers -----------------------------------------
    def call(self, actor, op, **p):
        r = http_call(self.calls[actor], op, p)
        self.events.append({'op': op, 'actor': actor, 'rev': r.get('revision')})
        return r.get('result')

    def snap(self):
        return self.call('SUPERVISOR', 'snapshot')

    def epoch(self):
        return self.snap()['epoch']

    def gen(self, tid):
        return self.snap()['tasks'][tid]['generation']

    def rtx_holder(self):
        return self.snap()['resources'].get('rtx4090', {}).get('task')

    def release_rtx(self, holder_task=None):
        holder = self.rtx_holder()
        if holder is None:
            return
        assert holder_task is None or holder == holder_task, \
            'expected holder %s got %s' % (holder_task, holder)
        self.call(self.tasks[holder], 'resource_release', task=holder,
                  generation=self.gen(holder), resource='rtx4090',
                  evidence='fixture drained rtx')

    def record(self, scenario, ok, detail):
        self.results[scenario] = {'pass': bool(ok), 'detail': detail}
        print('[%s] %s' % (scenario, 'PASS' if ok else 'FAIL: ' + str(detail)),
              flush=True)

    # ---- setup ---------------------------------------------------------
    def start(self):
        self.fb.ensure_installation()
        self.fb.start(wait=True)
        endpoint = 'http://127.0.0.1:%d/v1/action' % self.port
        sup = self.fb.load_secrets()['supervisor']
        self.calls['SUPERVISOR'] = {'endpoint': endpoint, 'token': sup}
        for aid in AGENTS:
            r = self.call('SUPERVISOR', 'enroll', agent=aid, label=aid)
            self.calls[aid] = {'endpoint': endpoint, 'token': r['session_token']}
            self.call('SUPERVISOR', 'qualify', agent=aid,
                      capabilities=['cpu', 'gpu'], max_tasks=2,
                      can_lead=(aid == LEAD), rank=10 if aid == LEAD else 1,
                      evidence='five-client coordination fixture')
        self.call(LEAD, 'offer_lead', epoch=self.epoch(),
                  checkpoint='no foreign work; fixture ready')
        self.call('SUPERVISOR', 'elect')
        assert self.snap()['leader'] == LEAD
        for i, aid in enumerate(AGENTS):
            tid = 'coord-%d' % (i + 1)
            kind = 'integration' if i == 0 else 'worker'
            claimer = LEAD if i == 0 else aid
            self.call(LEAD, 'create_task', task=tid, base=BASE, kind=kind,
                      epoch=self.epoch(), scopes=[SCOPE_DIR + '/' + tid],
                      capabilities=['cpu', 'gpu'], packet='coordination fixture',
                      resources=[{'name': 'rtx4090'}])
            self.call(claimer, 'claim', task=tid)
            self.tasks[tid] = claimer
        assert sum(1 for s in self.snap()['slots'].values()
                   if s['task'] is not None) == 5
        return True

    def shutdown(self):
        try:
            if fleet_on_port(self.port)[1] == 'fleet':
                self.fb.stop('five-client coordinator teardown')
        except SystemExit:
            pass
        try:
            self.fb.pidfile.unlink(missing_ok=True)
        except OSError:
            pass

    # ---- scenarios ------------------------------------------------------
    def s1_capacity(self):
        self.call(LEAD, 'create_task', task='coord-sixth', base=BASE,
                  kind='worker', epoch=self.epoch(),
                  scopes=[SCOPE_DIR + '/coord-sixth'],
                  capabilities=['cpu'], packet='sixth task')
        before = self.snap()
        # stale-smoke-autospawn-01: the sixth claim AUTO-SPAWNS a fresh worker
        # slot above the registry high-water (the pre-fix refusal pin is
        # superseded by the slot-expansion fuse; semantics anchor:
        # test_control.py test_five_slots_then_auto_spawn_on_sixth).
        high_water = max(int(k) for k in before['slots'] if str(k).isdigit())
        claim = self.call('a2', 'claim', task='coord-sixth')
        after = self.snap()
        new_slot = str(claim['slot'])
        task = after['tasks']['coord-sixth']
        ok = (new_slot not in before['slots']
              and int(new_slot) > high_water
              and task['state'] == 'RUNNING'
              and task['owner'] == 'a2'
              and task['generation'] == 1
              and str(task['slot']) == new_slot
              and after['slots'][new_slot]['task'] == 'coord-sixth'
              and after['revision'] > before['revision']
              and sum(1 for s in after['slots'].values()
                      if s['task'] is not None) == 6)
        return ok, ('sixth claim auto-spawned slot %s above high-water %d; '
                    'coord-sixth RUNNING owned by a2 at generation 1; six '
                    'slots bound' % (new_slot, high_water))

    def s2_fifo_contention(self):
        self.call(self.tasks['coord-1'], 'resource_request', task='coord-1',
                  generation=self.gen('coord-1'),
                  wants=[{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        self.call(self.tasks['coord-2'], 'resource_request', task='coord-2',
                  generation=self.gen('coord-2'),
                  wants=[{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        st = self.snap()
        ok1 = st['resources']['rtx4090']['task'] == 'coord-1'
        pending = [q for q in st['resource_queues'] if not q['served']]
        ok2 = len(pending) == 1 and pending[0]['task'] == 'coord-2' \
            and pending[0]['wants'][0]['name'] == 'rtx4090'
        self.release_rtx('coord-1')
        ok3 = self.rtx_holder() == 'coord-2'
        return (ok1 and ok2 and ok3), 'later rtx request queued; earlier FIFO wins on release'

    def s3_benchmark_isolation(self):
        self.release_rtx('coord-2')
        self.call(self.tasks['coord-3'], 'resource_request', task='coord-3',
                  generation=self.gen('coord-3'),
                  wants=[{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        r = self.call(self.tasks['coord-4'], 'resource_request', task='coord-4',
                      generation=self.gen('coord-4'),
                      wants=[{'name': 'rtx4090', 'class': 'gpu_benchmark'}])
        ok1 = not r.get('granted') and r.get('stalled') == 'benchmark_exclusive:gpu_held'
        self.release_rtx('coord-3')
        st = self.snap()
        ok2 = st['resources'].get('rtx4090', {}).get('class') == 'gpu_benchmark' \
            and st['resources']['rtx4090']['task'] == 'coord-4'
        rr = self.call(self.tasks['coord-3'], 'resource_request', task='coord-3',
                       generation=self.gen('coord-3'),
                       wants=[{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        ok3 = not rr.get('granted') and rr.get('stalled') == 'benchmark_exclusive:gpu_held'
        self.release_rtx('coord-4')
        return (ok1 and ok2 and ok3), 'benchmark waits under utilization; grants on empty; excludes interactive'

    def s4_memory_admission(self):
        self.release_rtx('coord-3')
        r1 = self.call(self.tasks['coord-1'], 'resource_request', task='coord-1',
                       generation=self.gen('coord-1'),
                       wants=[{'name': 'memory', 'memory_mb': 16000}])
        ok0 = r1.get('granted') is True
        r2 = self.call(self.tasks['coord-2'], 'resource_request', task='coord-2',
                       generation=self.gen('coord-2'),
                       wants=[{'name': 'memory', 'memory_mb': 2000}])
        ok1 = r2.get('allocation_failed') and not r2.get('granted') \
            and r2.get('stalled') == 'memory_allocation_refused'
        # The refused request stays QUEUED (all-or-nothing, served=False) and
        # the controller retries it on the next promotion: releasing the large
        # hold admits it -- no client re-request needed.
        self.call(self.tasks['coord-1'], 'resource_release', task='coord-1',
                  generation=self.gen('coord-1'), resource='memory',
                  evidence='fixture drained memory')
        mem = [k for k in self.snap()['resources'] if k.startswith('memory.')]
        ok2 = len(mem) == 1 and self.snap()['resources'][mem[0]]['task'] == 'coord-2'
        for q in self.snap()['resource_queues']:
            if q['task'] == 'coord-2' and q['allocation_failed']:
                ok2 = ok2 and q['granted'] and q['granted_revision'] is not None
        return ((ok0 and ok1 and ok2),
                'over-budget refused (queued all-or-nothing); release admits '
                'the queued grant automatically (grant=%s refus=%s autoadmit=%s)'
                % (ok0, ok1, ok2))

    def s5_fail_hold_recovery(self):
        owner = self.tasks['coord-2']   # a2 owns only coord-2
        g = self.gen('coord-2')
        self.call('SUPERVISOR', 'fail', agent=owner, reason='PROCESS_EXIT',
                  evidence='coordination drill: owner terminated mid-task')
        st = self.snap()
        ok1 = st['tasks']['coord-2']['state'] == 'RECOVERY_HOLD' \
            and st['tasks']['coord-2']['generation'] == g + 1 \
            and st['agents'][owner]['alive'] is False
        ok2 = any(k.startswith('memory.') for k in st['resources'])
        try:
            self.call('SUPERVISOR', 'recover', task='coord-2',
                      evidence='attempted while resources still held')
            ok3 = False
        except ValueError as e:
            ok3 = 'resources_still_held' in str(e)
        held_mem = [k for k in self.snap()['resources'] if k.startswith('memory.')]
        for key in held_mem:
            self.call('SUPERVISOR', 'resource_clear', resource=key,
                      evidence='actual process drained (fixture)')
        self.call('SUPERVISOR', 'recover', task='coord-2',
                  evidence='preserved workspace; writer gone')
        survivor = 'a3'
        claim = self.call(survivor, 'claim', task='coord-2')
        ok4 = claim['owner'] == survivor and claim['generation'] > g \
            and claim['generation'] == self.snap()['tasks']['coord-2']['generation']
        self.tasks['coord-2'] = survivor
        return ((ok1 and ok2 and ok3 and ok4),
                'fail holds task+resource; recover gated on drain; fresh '
                'generation (hold=%s retained=%s gated=%s fresh=%s)'
                % (ok1, ok2, ok3, ok4))

    def s6_bootstrap_guards(self):
        port2 = free_port()
        foreign = ThreadingHTTPServer(('127.0.0.1', port2), _Foreign)
        threading.Thread(target=foreign.serve_forever, daemon=True).start()
        cp1 = subprocess.run(
            [sys.executable, str(HERE / 'bootstrap_fleet.py'), 'start',
             '--root', str(self.root / 'foreign-root'), '--port', str(port2)],
            capture_output=True, text=True, timeout=90)
        foreign.shutdown(); foreign.server_close()
        ok1 = cp1.returncode != 0 and \
            'conflicting_listener_refused' in (cp1.stdout + cp1.stderr)
        cp2 = subprocess.run(
            [sys.executable, str(HERE / 'bootstrap_fleet.py'), 'start',
             '--root', str(self.root), '--port', str(self.port)],
            capture_output=True, text=True, timeout=90)
        ok2 = cp2.returncode != 0 and \
            'duplicate_start_refused' in (cp2.stdout + cp2.stderr)
        return (ok1 and ok2), 'foreign listener and duplicate start both refused'

    def s7_restart_durability(self):
        before = self.snap()
        cp = subprocess.run(
            [sys.executable, str(HERE / 'bootstrap_fleet.py'), 'restart',
             '--root', str(self.root), '--port', str(self.port),
             '--ack', 'coordination driver restart; claims must survive'],
            capture_output=True, text=True, timeout=120)
        if cp.returncode != 0:
            return False, (cp.stdout + cp.stderr).strip()
        after = self.snap()
        ok1 = before['revision'] == after['revision'] \
            and before['epoch'] == after['epoch'] \
            and before['leader'] == after['leader']
        ok2 = all(
            after['tasks'][t]['state'] == 'RUNNING'
            and after['tasks'][t]['owner'] == before['tasks'][t]['owner']
            and after['tasks'][t]['slot'] == before['tasks'][t]['slot']
            for t in before['tasks'] if t.startswith('coord-')
            and t != 'coord-sixth')
        dr = self.call(LEAD, 'checkpoint', task='coord-1',
                       generation=self.gen('coord-1'),
                       checkpoint='session token survived restart',
                       state='RUNNING')
        ok3 = dr.get('saved') is True
        return ((ok1 and ok2 and ok3),
                'restart preserves revision/epoch/claims/tokens '
                '(rev=%s claims=%s token=%s)' % (ok1, ok2, ok3))

    def s8_evidence_gate(self):
        owner2 = self.snap()['tasks']['coord-2']['owner']
        self.tasks['coord-2'] = owner2
        rq = self.call(owner2, 'resource_request', task='coord-2',
                       generation=self.gen('coord-2'),
                       wants=[{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        ok0 = rq.get('granted') is True
        st = self.snap()
        try:
            self.call(owner2, 'submit_review', task='coord-2',
                      generation=st['tasks']['coord-2']['generation'],
                      branch=st['tasks']['coord-2']['branch'], head=BASE,
                      evidence='review while resources held')
            ok1 = False
        except ValueError as e:
            ok1 = 'release_resources_before_review' in str(e)
        self.release_rtx('coord-2')
        return (ok0 and ok1), 'review refused while resources held; gate cleared after drain'

    def s9_deadlock_free_progress(self):
        st = self.snap()
        for tid in ('coord-2', 'coord-4', 'coord-5'):
            self.tasks[tid] = st['tasks'][tid]['owner']
        r2 = self.call(self.tasks['coord-2'], 'resource_request', task='coord-2',
                       generation=self.gen('coord-2'),
                       wants=[{'name': 'rtx4090', 'class': 'gpu_functionality'}])
        ok0 = r2.get('granted') is True
        r4 = self.call(self.tasks['coord-4'], 'resource_request', task='coord-4',
                       generation=self.gen('coord-4'),
                       wants=[{'name': 'rtx4090', 'class': 'gpu_benchmark'}])
        ok1 = not r4.get('granted')
        r5 = self.call(self.tasks['coord-5'], 'resource_request', task='coord-5',
                       generation=self.gen('coord-5'),
                       wants=[{'name': 'memory', 'memory_mb': 6000}])
        ok2 = r5.get('granted') is True
        ok3 = self.rtx_holder() == 'coord-2'
        # Benchmark exclusivity spans the WHOLE machine: releasing coord-2's
        # rtx is not enough while coord-5 still holds memory (other_hold).
        self.release_rtx('coord-2')
        st = self.snap()
        stays = [q for q in st['resource_queues']
                 if q['task'] == 'coord-4' and not q['served']]
        ok4 = len(stays) == 1 \
            and (stays[0].get('stalled') or '').startswith('benchmark_exclusive')
        self.call(self.tasks['coord-5'], 'resource_release', task='coord-5',
                  generation=self.gen('coord-5'), resource='memory',
                  evidence='fixture drained memory')
        st = self.snap()
        ok5 = st['resources'].get('rtx4090', {}).get('class') == 'gpu_benchmark' \
            and st['resources']['rtx4090']['task'] == 'coord-4'
        grants = {}
        for q in st['resource_queues']:
            grants[q['task']] = q
        fifo = grants['coord-2']['granted_revision'] < \
            grants['coord-4']['granted_revision'] \
            and grants['coord-2']['enqueued_revision'] < \
            grants['coord-4']['enqueued_revision']
        self.release_rtx('coord-4')
        st = self.snap()
        ok6 = (not st['resources']
               and all(q['served'] for q in st['resource_queues']))
        return (ok0 and ok1 and ok2 and ok3 and ok4 and ok5 and fifo and ok6), \
            'overlapping wants progress without deadlock; FIFO on record; ' \
            'benchmark gates on full-machine drain'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default=None)
    ap.add_argument('--keep', action='store_true')
    a = ap.parse_args(argv)
    try:
        pins = test_scenario_pins_are_current()
        print('[pins] scenario pins current: %s' % json.dumps(pins), flush=True)
    except AssertionError as e:
        print('REFUSING TO RUN: %s' % e, file=sys.stderr)
        return 3
    if a.out is None:
        a.out = Path(__file__).resolve().parents[2] / 'docs' / 'evidence' / \
            'agent_fleet' / 'FIVE-CLIENT-COORDINATION' / \
            time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    registry = Path(tempfile.mkdtemp(prefix='coord-registry-'))
    d = Driver(registry / 'deploy', free_port(), a.out)
    try:
        d.start()
    except Exception as e:
        d.shutdown()
        print('setup FAILED: %s' % e, file=sys.stderr)
        shutil.rmtree(registry, ignore_errors=True)
        return 2
    try:
        for (sc, fn) in (('S1', d.s1_capacity), ('S2', d.s2_fifo_contention),
                         ('S3', d.s3_benchmark_isolation),
                         ('S4', d.s4_memory_admission),
                         ('S5', d.s5_fail_hold_recovery),
                         ('S6', d.s6_bootstrap_guards),
                         ('S7', d.s7_restart_durability),
                         ('S8', d.s8_evidence_gate),
                         ('S9', d.s9_deadlock_free_progress)):
            try:
                d.record(sc, *fn())
            except Exception as e:
                d.results[sc] = {'pass': False, 'detail': repr(e)}
                print('[%s] UNEXPECTED: %r' % (sc, e), flush=True)
    finally:
        try:
            final = d.snap()
        except Exception:
            final = {}
        d.shutdown()
    all_pass = all(d.results[s]['pass'] for s in SCENARIOS)
    summary = {
        'preregistration': {
            'statement': 'five isolated clients coordinate through one '
                         'controller without cross-client mutation',
            'prediction': 'S1-S9 all pass on a fresh isolated registry',
            'falsifier': 'any scenario FAIL or partial snapshot'},
        'scenarios': {s: d.results[s] for s in SCENARIOS},
        'all_pass': all_pass,
        'run': {'port': d.port, 'registry': str(registry / 'deploy'),
                'revision_final': final.get('revision'),
                'leader': final.get('leader'), 'epoch': final.get('epoch')},
        'label': 'scripted clients: does NOT claim FIVE INDEPENDENT AGENTS '
                 'VERIFIED',
    }
    (d.out / 'COORDINATION.json').write_text(json.dumps(summary, indent=2),
                                            encoding='utf-8')
    if final:
        (d.out / 'FINAL_SNAPSHOT.json').write_text(
            json.dumps(final, indent=2, default=str), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    if not a.keep:
        shutil.rmtree(registry, ignore_errors=True)
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())