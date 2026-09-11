"""test_controller_transition.py -- isolated controller source-transition rehearsal.

Rehearses, end to end and entirely on temporary roots, the controller source
transition that THE_CONTROLLER_TRANSITION.md requires before any live
deployment: two deployment directories built in the MANIFEST pattern of the
live deployment, the real bootstrap stop/start CLI, one durable store carried
across an upgrade and a backup restore rollback, and a refusal matrix that
must fire BEFORE any stop or mutation.

Preregistered (docs/evidence/agent_fleet/CONTROLLER_TRANSITION/
PREREGISTRATION.md, committed before this file):
STATEMENT: current-generation acknowledged quiescence, verified process
identity, SQLite-consistent backup and same-store restart/rollback can upgrade
controller source without stale authority or data loss.
PREDICTION: (a) positive upgrade preserves claims, generations, leader/epoch,
sessions and audit history; (b) rollback restores exactly the pre-upgrade
registry and keeps pre-upgrade sessions valid; (c) stale ack, wrong PID/image
identity, active unacknowledged worker, held runtime/eye resource and
incompatible schema each refuse BEFORE stop/mutation.
FALSIFIER: wrong process stopped, stale generation admitted, lost claims,
exposed credentials, direct DB patches treated as normal rollback, or source
integration falsely called deployment.

The incompatible-schema store in test 2 is a hand-crafted FIXTURE whose only
legal role is to be refused; the rollback path under rehearsal is exclusively
the verified consistent backup restore. No live control-plane store, service
or supervisor operation is ever touched, and no GPU/model work runs here.
"""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bootstrap_fleet
from bootstrap_fleet import FleetBootstrap, fleet_on_port
from client import call as http_call
from test_bootstrap_fleet import free_port

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCRATCH = REPO / '.tmp' / 'transition-rehearsal'
# Runtime files of a controller deployment: exactly the set the live
# deployment MANIFEST (slot-binding-d012b4b1) carries. credentials_copied
# is always false; secrets live only under the temp fleet root.
DEPLOYMENT_FILES = (
    'bootstrap_fleet.py', 'client.py', 'control.py', 'enroll_agent.py',
    'launch_worker.py', 'layout.py', 'master_catalogue.py',
    'provision_slot.py', 'publish.py', 'review_handoff.py',
    'run_queue.py', 'run_queue_worker.py', 'service.py',
    'worktree_reconcile.py',
)
BASE = 'a' * 40
HEAD_B = 'b' * 40
COMMIT_C = 'c' * 40


def sha256_file(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def source_revision():
    out = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'],
                         capture_output=True, text=True)
    return out.stdout.strip() or 'unknown'


def process_command_line(pid):
    """Listener executable/command ownership: gate 3 of the transition doc.
    The PID record alone must never establish identity."""
    if os.name == 'nt':
        script = ("Get-CimInstance Win32_Process -Filter 'ProcessId=%d' "
                  "| Select-Object -ExpandProperty CommandLine" % pid)
        r = subprocess.run(['powershell', '-NoProfile', '-Command', script],
                           capture_output=True, text=True, timeout=30)
    else:
        r = subprocess.run(['ps', '-p', str(pid), '-o', 'command='],
                           capture_output=True, text=True, timeout=30)
    out = (r.stdout or '').strip()
    return out or None


class RehearsalRefusal(Exception):
    """A transition-gate refusal. Like a controller refusal, it is a STOP for
    that action -- the rehearsal treats it as terminal for the attempt."""


def make_deployment(dest, marker):
    """Build a deployment directory in the live MANIFEST pattern: copied
    runtime files plus a hash manifest; `marker` is an inert SERVICE_MARKER
    constant that makes the generational content state externally visible.
    Returns the manifest dict. A deployment is never the integration checkout.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    rev = source_revision()
    for name in DEPLOYMENT_FILES:
        shutil.copyfile(HERE / name, dest / name)
    if marker:
        service = dest / 'service.py'
        service.write_text(service.read_text(encoding='utf-8')
                           + '\nSERVICE_MARKER = %r  # inert rehearsal marker\n'
                           % marker, encoding='utf-8')
    files = {}
    for name in DEPLOYMENT_FILES:
        p = dest / name
        files[name] = {'sha256': sha256_file(p), 'bytes': p.stat().st_size,
                       'source': 'worktree %s:tools/agent_fleet/%s' % (rev, name)}
    manifest = {'source_revision': rev, 'marker': marker or '',
                'credentials_copied': False, 'files': files}
    (dest / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2),
                                        encoding='utf-8')
    return manifest


def verify_deployment(dep):
    """Source-integrity gate: every file must still hash to its manifest row
    before that deployment is allowed to serve."""
    manifest = json.loads((Path(dep) / 'MANIFEST.json').read_text(encoding='utf-8'))
    for name, row in manifest['files'].items():
        p = Path(dep) / name
        if not p.exists() or sha256_file(p) != row['sha256'] \
                or p.stat().st_size != row['bytes']:
            raise RehearsalRefusal('deployment_integrity_mismatch: %s' % p)
    return manifest


class Rehearsal:
    """The gated upgrade/rollback procedure, composed ONLY from the existing
    machinery: bootstrap CLI lifecycle, HTTP controller surface, SQLite
    backup API. Every gate in preflight() is read-only and runs BEFORE any
    stop; a refusal raises instead of stopping the service."""

    def __init__(self, root, port, secrets):
        self.root = Path(root)
        self.port = int(port)
        self.secrets = secrets
        self.db = self.root / 'control' / 'state.sqlite'
        self.service_pid = None
        self.fb = FleetBootstrap(self.root, self.port)

    # --- operator CLI path (deployment-bound; HERE is the deployment) ----
    def cli(self, dep, command, *extra, expect=None):
        r = subprocess.run(
            [sys.executable, str(Path(dep) / 'bootstrap_fleet.py'), command,
             '--root', str(self.root), '--port', str(self.port), *extra],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=120)
        if expect is not None and r.returncode != expect:
            raise AssertionError(
                'cli %s %s: returncode %s != %s\nstdout:\n%s\nstderr:\n%s'
                % (command, list(extra), r.returncode, expect, r.stdout, r.stderr))
        return r

    def start(self, dep):
        r = self.cli(dep, 'start', '--json', expect=0)
        m = re.search(r'spawned service pid (\d+)', r.stdout)
        self.service_pid = int(m.group(1))
        return self.service_pid

    def stop(self, dep, ack):
        return self.cli(dep, 'stop', '--ack', ack, expect=0)

    # --- HTTP controller surface -----------------------------------------
    def act(self, token, op, **p):
        sess = {'endpoint': 'http://127.0.0.1:%d/v1/action' % self.port,
                'token': token}
        return http_call(sess, op, p)['result']

    def snap(self):
        return self.act(self.secrets['supervisor'], 'snapshot')

    def events(self):
        return self.act(self.secrets['supervisor'], 'events', since=0)

    # --- transition gates (all read-only, all pre-stop) -------------------
    def refuse(self, reason):
        raise RehearsalRefusal(reason)

    def preflight(self, expected_dep):
        """Gates 1-5 of THE_CONTROLLER_TRANSITION.md, in order, all BEFORE
        any stop. Returns the verified listener pid + snapshot."""
        verify_deployment(expected_dep)
        on_port, kind = fleet_on_port(self.port)
        if kind != 'fleet':
            self.refuse('no_fleet_listener_on_port:%s' % self.port)
        listener = self.fb._listener_pid()
        if listener is None:
            self.refuse('listener_pid_unresolved:%s' % self.port)
        pf = self.fb._read_pidfile()
        if pf is None or pf.get('pid') != listener:
            self.refuse('pidfile_listener_mismatch: pidfile=%r listener=%r'
                        % (pf and pf.get('pid'), listener))
        cmdline = process_command_line(listener)
        image = str(Path(expected_dep) / 'service.py')
        if not cmdline or os.path.normcase(image) not in os.path.normcase(cmdline):
            self.refuse('listener_image_mismatch: expected %s, served %r'
                        % (image, cmdline))
        ok, state = self.fb.verify_reconciled(self.secrets)
        if not ok:
            self.refuse('store_preflight_failed:%s' % state)
        if state.get('schema') != 1:
            self.refuse('incompatible_store_schema:%r' % state.get('schema'))
        snap = self.snap()
        evs = self.events()['events']
        for tid, t in snap['tasks'].items():
            if t['state'] != 'RUNNING':
                continue
            acks = [e for e in evs
                    if e.get('kind') == 'checkpoint' and e.get('task') == tid]
            if not acks:
                self.refuse('unacknowledged_active_worker:%s' % tid)
            latest = max(acks, key=lambda e: e['sequence'])
            if latest.get('generation') != t['generation']:
                self.refuse(
                    'stale_worker_acknowledgment:%s: ack gen %r != current gen %r'
                    % (tid, latest.get('generation'), t['generation']))
        held = sorted(snap.get('resources', {}))
        if held:
            self.refuse('resources_not_drained:' + ','.join(held))
        return {'listener': listener, 'snapshot': snap}

    # --- SQLite-consistent backup / verified restore ----------------------
    def backup(self, label):
        dest = self.root / 'control' / 'snapshots' / ('pre-%s.sqlite' % label)
        dest.parent.mkdir(parents=True, exist_ok=True)
        src = sqlite3.connect(str(self.db), timeout=10)
        dst = sqlite3.connect(str(dest))
        with dst:
            src.backup(dst)
        dst.close()
        src.close()
        con = sqlite3.connect(str(dest))
        try:
            integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
            row = con.execute('SELECT body FROM state WHERE id=1').fetchone()
        finally:
            con.close()
        if integrity != 'ok':
            self.refuse('backup_integrity_failed:%s' % integrity)
        if row is None or json.loads(row[0]).get('schema') != 1:
            self.refuse('backup_schema_unreadable')
        return dest

    def restore_backup(self, path):
        """THE rollback path: file-level restore of the verified consistent
        backup over the same store. Never a row-level SQL patch."""
        shutil.copyfile(str(path), str(self.db))


class ControllerTransitionRehearsalTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='case-', dir=str(SCRATCH))
        base = Path(self.tmp.name)
        self.root = base / 'fleet-root'
        self.port = free_port()
        self.secrets = {'supervisor': 'SUP-SECRET-%08x' % id(self),
                        'enrollment': 'ENR-SECRET-%08x' % id(self)}
        (self.root / 'control').mkdir(parents=True)
        (self.root / 'control' / '.service_secrets.json').write_text(
            json.dumps(self.secrets), encoding='utf-8')
        self.dep_old = base / 'dep-old'
        self.dep_new = base / 'dep-new'
        self.manifest_old = make_deployment(self.dep_old, 'rehearsal-gen-1')
        self.manifest_new = make_deployment(self.dep_new, 'rehearsal-gen-2')
        verify_deployment(self.dep_old)
        verify_deployment(self.dep_new)
        self.r = Rehearsal(self.root, self.port, self.secrets)

    def tearDown(self):
        if fleet_on_port(self.port)[1] == 'fleet':
            listener = self.r.fb._listener_pid()
            pf = self.r.fb._read_pidfile()
            if pf is None or pf.get('pid') != listener:
                # repair fixture tampering so the managed stop can proceed
                self.r.fb._write_pidfile(listener)
            try:
                self.r.fb.stop('test teardown controlled transition')
            except SystemExit:
                pass
        self.tmp.cleanup()

    # --- live-state builders ---------------------------------------------
    def seed_agents(self):
        sup = self.secrets['supervisor']
        enr = self.secrets['enrollment']
        wk = self.r.act(enr, 'enroll', agent='worker',
                        label='rehearsal worker')['session_token']
        op = self.r.act(enr, 'enroll', agent='op',
                        label='rehearsal lead')['session_token']
        self.r.act(sup, 'qualify', agent='worker', capabilities=['cpu', 'docs'],
                   max_tasks=5, can_lead=False, rank=1,
                   evidence='transition rehearsal fixture')
        self.r.act(sup, 'qualify', agent='op', capabilities=['cpu', 'docs'],
                   max_tasks=5, can_lead=True, rank=10,
                   evidence='transition rehearsal fixture')
        epoch = self.r.snap()['epoch']
        self.r.act(op, 'offer_lead', epoch=epoch,
                   checkpoint='rehearsal lead ready; no foreign work')
        self.r.act(sup, 'elect')
        return wk, op

    def create_and_claim(self, op, wk, tid, ack=True):
        self.r.act(op, 'create_task', task=tid, epoch=self.r.snap()['epoch'],
                   base=BASE, kind='worker',
                   scopes=['docs/evidence/transition-rehearsal-' + tid],
                   packet='statement / prediction / falsifier')
        t = self.r.act(wk, 'claim', task=tid)
        if ack:
            self.r.act(wk, 'checkpoint', task=tid, generation=t['generation'],
                       checkpoint='cp: %s acknowledged quiescence at gen %d'
                                  % (tid, t['generation']))
        return t

    # --- test 1: positive upgrade + backup rollback -----------------------
    def test_1_upgrade_preserves_registry_and_sessions_then_rollback_restores(self):
        self.r.start(self.dep_old)
        wk, op = self.seed_agents()
        run_t = self.create_and_claim(op, wk, 'upgrade-proof')
        rev_t = self.create_and_claim(op, wk, 'review-proof')
        self.r.act(wk, 'submit_review', task='review-proof',
                   generation=rev_t['generation'], branch=rev_t['branch'],
                   head=HEAD_B, evidence='rehearsal review record')
        int_t = self.create_and_claim(op, wk, 'integrated-proof')
        self.r.act(wk, 'submit_review', task='integrated-proof',
                   generation=int_t['generation'], branch=int_t['branch'],
                   head=HEAD_B, evidence='rehearsal review record')
        rid = self.r.act(op, 'integration_request', task='integrated-proof',
                         head=HEAD_B, branch=int_t['branch'],
                         expected_base=BASE, epoch=self.r.snap()['epoch'],
                         review='rehearsal independent review')['request']
        self.r.act(self.secrets['supervisor'], 'ack_integration', request=rid,
                   base_branch='astra/gait-capture', expected_base=BASE,
                   commit=COMMIT_C, evidence='rehearsal publication record')

        before = self.r.snap()
        before_events = self.r.events()['events']
        self.assertEqual(before['tasks']['integrated-proof']['state'],
                         'INTEGRATED')

        backup_path = self.r.backup('upgrade-rehearsal')
        pre = self.r.preflight(self.dep_old)
        self.assertEqual(pre['listener'], self.r.service_pid)

        self.r.stop(self.dep_old, 'rehearsal: quiesced, backed up, identity verified')
        self.r.start(self.dep_new)

        # served image identity: the running process names the NEW deployment,
        # not the integration checkout (deployment != source integration).
        cmdline = process_command_line(self.r.service_pid)
        self.assertIsNotNone(cmdline)
        self.assertIn(os.path.normcase(str(self.dep_new / 'service.py')),
                      os.path.normcase(cmdline))
        self.assertNotIn(os.path.normcase(str(HERE / 'service.py')),
                         os.path.normcase(cmdline))
        self.assertEqual(self.r.preflight(self.dep_new)['listener'],
                         self.r.service_pid)

        # the upgrade preserved everything: registry byte-equal
        after = self.r.snap()
        self.assertEqual(after, before)
        # audit history preserved exactly (no new ops since the capture)
        evs = self.r.events()['events']
        self.assertEqual(evs, before_events)
        # the pre-upgrade session token still writes (nothing was rekeyed)
        self.r.act(wk, 'checkpoint', task='upgrade-proof',
                   generation=run_t['generation'],
                   checkpoint='cp: post-upgrade checkpoint; same token, same owner')
        self.assertEqual(
            self.r.snap()['tasks']['upgrade-proof']['checkpoint'],
            'cp: post-upgrade checkpoint; same token, same owner')
        # audit history extends across the upgrade without rewriting the past
        evs = self.r.events()['events']
        self.assertEqual(evs[:len(before_events)], before_events)
        self.assertEqual(len(evs), len(before_events) + 1)
        self.assertEqual(evs[-1]['kind'], 'checkpoint')
        self.assertEqual(evs[-1].get('task'), 'upgrade-proof')

        # ROLLBACK: stop, restore the verified backup, start the OLD deployment
        self.r.stop(self.dep_new, 'rehearsal: rollback to pre-upgrade deployment')
        self.r.restore_backup(backup_path)
        self.r.start(self.dep_old)
        rb = self.r.snap()
        self.assertEqual(rb, before)  # byte-faithful: upgrade-era writes reverted
        evs = self.r.events()['events']
        self.assertEqual(evs, before_events)  # upgrade-era audit event reverted
        # the pre-upgrade session token is still the valid one after rollback
        self.r.act(wk, 'checkpoint', task='upgrade-proof',
                   generation=run_t['generation'],
                   checkpoint='cp: post-rollback checkpoint; pre-upgrade token valid')
        self.assertEqual(self.r.preflight(self.dep_old)['listener'],
                         self.r.service_pid)

    # --- test 2: refusal matrix, each BEFORE stop/mutation ----------------
    def test_2_refusal_matrix_refuses_before_stop_or_mutation(self):
        self.r.start(self.dep_old)
        wk, op = self.seed_agents()
        lane_a = self.create_and_claim(op, wk, 'lane-a')  # acked at gen 1
        lane_b = self.create_and_claim(op, wk, 'lane-b', ack=False)

        def unchanged():
            on_port, kind = fleet_on_port(self.port)
            self.assertEqual(kind, 'fleet', 'service must survive every refusal')
            return self.r.snap()['revision']

        # (c-PREDICTION) active unacknowledged worker refuses first
        rev = unchanged()
        with self.assertRaisesRegex(RehearsalRefusal, '^unacknowledged_active_worker:lane-b'):
            self.r.preflight(self.dep_old)
        self.assertEqual(unchanged(), rev)
        self.r.act(wk, 'checkpoint', task='lane-b', generation=lane_b['generation'],
                   checkpoint='cp: lane-b acknowledged quiescence')

        # (c-PREDICTION) held runtime/eye resource refuses (registry holds,
        # no GPU work anywhere in this suite)
        self.r.act(wk, 'resource_acquire', task='lane-b',
                   generation=lane_b['generation'], resource='rtx4090')
        self.r.act(wk, 'resource_acquire', task='lane-b',
                   generation=lane_b['generation'], resource='dyad_eye')
        rev = unchanged()
        with self.assertRaisesRegex(RehearsalRefusal, '^resources_not_drained:dyad_eye'):
            self.r.preflight(self.dep_old)
        self.assertEqual(unchanged(), rev)
        self.r.act(wk, 'resource_release', task='lane-b',
                   generation=lane_b['generation'], resource='dyad_eye',
                   evidence='rehearsal drain: eye released')
        self.r.act(wk, 'resource_release', task='lane-b',
                   generation=lane_b['generation'], resource='rtx4090',
                   evidence='rehearsal drain: gpu released')

        # (a-PREDICTION) stale acknowledgment: a gen-1 "done" must not count
        # after the task advanced to gen 2 (review cycle bumped generation)
        self.r.act(wk, 'submit_review', task='lane-a', generation=lane_a['generation'],
                   branch=lane_a['branch'], head=HEAD_B,
                   evidence='rehearsal review record')
        self.r.act(op, 'review_requeue', task='lane-a',
                   epoch=self.r.snap()['epoch'],
                   evidence='rehearsal: stale base reconciled; generation bumped')
        self.assertEqual(self.r.snap()['tasks']['lane-a']['generation'], 2)
        rev = unchanged()
        with self.assertRaisesRegex(RehearsalRefusal,
                                    '^stale_worker_acknowledgment:lane-a'):
            self.r.preflight(self.dep_old)
        self.assertEqual(unchanged(), rev)
        self.r.act(wk, 'checkpoint', task='lane-a', generation=2,
                   checkpoint='cp: lane-a re-acknowledged at current generation')

        # (d-PREDICTION) wrong PID identity: the pidfile names a LIVE but
        # different process (this test process). Both the gate and the
        # bootstrap stop must refuse, the service must survive, and the
        # wrongly-named process must survive.
        self.r.fb.pidfile.write_text(json.dumps(
            {'pid': os.getpid(), 'port': self.port, 'root': str(self.root),
             'started_at_utc': 'tampered-by-fixture'}, indent=2), encoding='utf-8')
        rev = unchanged()
        with self.assertRaisesRegex(RehearsalRefusal, '^pidfile_listener_mismatch'):
            self.r.preflight(self.dep_old)
        self.assertEqual(unchanged(), rev)
        r = self.r.cli(self.dep_old, 'stop', '--ack', 'rehearsal: stop attempt with tampered pidfile')
        self.assertEqual(r.returncode, 1)
        self.assertIn('refusing_stop_unmanaged', r.stdout + r.stderr)
        self.assertEqual(unchanged(), rev)  # service still answering, not mutated
        self.assertTrue(self.r.fb._pid_alive(self.r.service_pid))
        listener = self.r.fb._listener_pid()
        self.assertTrue(self.r.fb._pid_alive(listener))
        self.assertNotEqual(listener, os.getpid())
        self.r.fb._write_pidfile(listener)  # repair fixture

        # (e-PREDICTION) listener image mismatch: the plan expects dep-new
        # while dep-old serves
        rev = unchanged()
        with self.assertRaisesRegex(RehearsalRefusal, '^listener_image_mismatch'):
            self.r.preflight(self.dep_new)
        self.assertEqual(unchanged(), rev)

        # (f-PREDICTION) incompatible schema: crafted FIXTURE store refuses
        # preflight while running, then refuses start at the constructor --
        # and only the backup restore recovers, never a SQL patch.
        pristine = self.r.backup('pre-schema-tamper')
        pre_tamper = self.r.snap()
        con = sqlite3.connect(str(self.r.db), timeout=10)
        try:
            body = json.loads(con.execute(
                'SELECT body FROM state WHERE id=1').fetchone()[0])
            body['schema'] = 2  # simulate a future, incompatible store
            con.execute('UPDATE state SET body=? WHERE id=1',
                        (json.dumps(body),))
            con.commit()
        finally:
            con.close()
        rev = unchanged()
        with self.assertRaisesRegex(RehearsalRefusal, '^incompatible_store_schema'):
            self.r.preflight(self.dep_old)
        self.assertEqual(unchanged(), rev)
        r = self.r.cli(self.dep_old, 'stop', '--ack', 'rehearsal: controlled stop before incompatible-store restart probe')
        self.assertEqual(r.returncode, 0)
        r = self.r.cli(self.dep_old, 'start', '--json')
        self.assertEqual(r.returncode, 3)
        self.assertIn('service_exited_before_ready', r.stdout + r.stderr)
        self.assertIn('configuration_mismatch', r.stdout + r.stderr)
        self.r.restore_backup(pristine)
        self.r.start(self.dep_old)
        self.assertEqual(self.r.snap(), pre_tamper)

    # --- test 3: credentials are never exposed by any surface -------------
    def test_3_credentials_never_appear_in_reports_events_status_or_logs(self):
        self.r.start(self.dep_old)
        wk, op = self.seed_agents()
        secrets = [self.secrets['supervisor'], self.secrets['enrollment'], wk]
        secrets_path = self.root / 'control' / '.service_secrets.json'
        # sanity: the strings under test are real and live only in the
        # private secrets file under the temp root
        self.assertTrue(all(secrets))
        self.assertIn(self.secrets['supervisor'],
                      secrets_path.read_text(encoding='utf-8'))
        surfaces = {
            'snapshot': json.dumps(self.r.snap()),
            'events': json.dumps(self.r.events()),
            'status_json': self.r.cli(self.dep_old, 'status', '--json',
                                      expect=0).stdout,
            'service_out_log': (self.root / 'control' / 'service.out.log')
                .read_text(encoding='utf-8', errors='replace'),
            'service_err_log': (self.root / 'control' / 'service.err.log')
                .read_text(encoding='utf-8', errors='replace'),
        }
        for surface, text in surfaces.items():
            for secret in secrets:
                self.assertNotIn(secret, text,
                                 'credential exposed in %s' % surface)
        snap = self.r.snap()
        self.assertNotIn('supervisor_hash', snap)
        self.assertNotIn('enrollment_hash', snap)
        for agent in snap['agents'].values():
            self.assertNotIn('token_hash', agent)


if __name__ == '__main__':
    unittest.main(verbosity=2)
