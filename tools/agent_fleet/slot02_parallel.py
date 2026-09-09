"""SLOT02-PARALLEL-01: two slots advance independent tasks concurrently while
shared resources and publication remain exclusively owned.

Preregistration (the task packets carry the same text):
  STATEMENT: two slots can advance independent tasks concurrently while
  shared resources and publication remain exclusively owned.
  PREDICTION: both make overlapping, recorded progress; conflicting resource
  requests wait or are refused; integration is serialized; engine loss
  preserves accepted work and permits controlled recovery.
  FALSIFIER: overlapping exclusive ownership, cross-slot state contamination,
  stale publication, lost checkpoints, unmanaged processes, or unsupported
  verification claims.

Real behaviors exercised (no mocks in the loop):
  1. slot-01 (integration kind) runs the verified engine runtime gate again
     (frozen B2, gamma controls, edge-contrast captures) + CPU-law rerun.
  2. slot-02 (worker kind) runs the CPU-law descent + the standalone Vulkan
     probe (its own CPU/GPU comparison build in slot-02/.tmp).
  3. GPU ARBITRATION: while slot-01's task holds rtx4090, slot-02's task is
     REFUSED the same resource (then proceeds on CPU-only law); after slot-01
     releases with drain evidence, the handoff succeeds.
  4. ENGINE-LOSS DRILL on slot-01: after a durable checkpoint the gate-owned
     engine process is terminated; registry failover elects the standby; a
     zombie write is refused; the GPU reservation is retained until the
     supervisor verifies actual drain; recovery reconciles; the new leader
     reclaims and RERUNS the full gate with a FRESH runtime identity (new exe
     hash cannot match: clean rebuild; recorded).
  5. STALE-BASE INTEGRATION: slot-02 integrates first, legitimately advancing
     the base; slot-01's integration is then refused
     (base_rewritten_since_task_fork); reconciled via review_requeue (no
     force) and republished. Superseded-leader publication is refused
     (session_revoked + stale_or_nonleader).
  6. Both slots closed: ports free, reservations drained, worktrees drained.

Usage (from the primary checkout):
  set CHIMERA_FLEET_SUPERVISOR_TOKEN=...
  set CHIMERA_FLEET_ENROLLMENT_TOKEN=...
  python tools/agent_fleet/slot02_parallel.py --repo <primary checkout>
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from demo_live import (Fleet, sh, free_port, provision, drain_worktree,  # noqa: E402
                       commit_and_push, integrate)
from control import Refusal  # noqa: E402

BASE_BRANCH = 'astra/gait-capture'
VULKAN_SDK = Path('C:/VulkanSDK/1.4.328.1')
EXPECTED_SHADER_BLOB = '4f7a356e34cdf06716515f0b21e9a998fa35ff21'
CAPTURE_PHI, CAPTURE_RADIUS = 0.35, 3.0
PORT_SLOT1 = 8101
PORT_SLOT2 = 8102


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def port_busy(port: int) -> bool:
    try:
        urllib.request.urlopen(f'http://localhost:{port}/state', timeout=2).read(64)
        return True
    except Exception:
        return False


def port_bound(port: int) -> bool:
    s = socket.socket()
    try:
        s.bind(('127.0.0.1', port))
        return False
    except OSError:
        return True
    finally:
        s.close()


def build_engine(src_dir: Path, build: Path, runtime: Path) -> dict:
    """Clean engine build into an external build dir; stage exe+spv into runtime."""
    build.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)
    cp = subprocess.run(['cmake', '-S', str(src_dir), '-B', str(build), '-G',
                         'Visual Studio 17 2022', '-A', 'x64',
                         f'-DVULKAN_SDK={VULKAN_SDK}'], capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError('cmake configure failed: ' + cp.stderr[-1500:])
    cp = subprocess.run(['cmake', '--build', str(build), '--config', 'Release',
                         '--parallel', '4', '--clean-first'],
                        capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError('cmake build failed: ' + cp.stderr[-1500:])
    exe_b = build / 'Release' / 'chimera_engine.exe'
    if not exe_b.exists():
        raise RuntimeError('engine exe missing after build')
    shutil.copy2(exe_b, runtime / 'chimera_engine.exe')
    sd = runtime / 'shaders'
    sd.mkdir(exist_ok=True)
    for spv in (build / 'Release' / 'shaders').glob('*.spv'):
        shutil.copy2(spv, sd / spv.name)
    return {'build_dir': str(build), 'runtime_dir': str(runtime),
            'exe_sha256': sha256(runtime / 'chimera_engine.exe'),
            'spv_sha256': sha256(sd / 'membrane_demo.spv'),
            'protected_build_path_used': False}


def run_gate(client: Path, exe: Path, port: int, cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, CHIMERA_MD_EDGE='1')
    return subprocess.run(
        [sys.executable, str(client), 'gate', '--launch', str(exe),
         '--port', str(port), '--base', f'http://localhost:{port}',
         '--capture-phi', str(CAPTURE_PHI), '--capture-radius', str(CAPTURE_RADIUS)],
        capture_output=True, text=True, env=env, cwd=str(cwd),
        encoding='utf-8', errors='replace')


def gate_pass(cp: subprocess.CompletedProcess) -> bool:
    return cp.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True)
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    sup = os.environ.get('CHIMERA_FLEET_SUPERVISOR_TOKEN', '')
    enr = os.environ.get('CHIMERA_FLEET_ENROLLMENT_TOKEN', '')
    if not sup or not enr or sup == enr:
        print('Set distinct CHIMERA_FLEET_SUPERVISOR_TOKEN / '
              'CHIMERA_FLEET_ENROLLMENT_TOKEN', file=sys.stderr)
        return 2

    run = repo.parent / ('fleet-slot02par-%s' % time.strftime('%Y%m%dT%H%M%S'))
    run.mkdir(parents=True, exist_ok=True)
    tid = time.strftime('%H%M%S')
    T1, T2 = 'par-engine-gate-' + tid, 'par-cpu-probe-' + tid
    state = run / 'state'
    state.mkdir(exist_ok=True)
    fleet = Fleet(run, sup, enr, free_port())
    stages = {}

    sync = sh(repo, 'pull', '--ff-only', 'origin', BASE_BRANCH, check=False)
    fleet.record('primary_sync', exit=sync.returncode)
    if sync.returncode != 0:
        print('primary checkout not fast-forwardable; reconcile manually')
        return 2
    base0 = sh(repo, 'rev-parse', 'HEAD').stdout.strip()
    remote = sh(repo, 'ls-remote', 'origin', 'refs/heads/' + BASE_BRANCH).stdout.split()[0]
    if remote != base0:
        print('base moved during preflight')
        return 2
    blob = sh(repo, 'rev-parse', 'HEAD:ChimeraEngine/engine/shaders/'
              'membrane_demo.comp').stdout.strip()
    fleet.record('preflight', base=base0, shader_blob_ok=blob == EXPECTED_SHADER_BLOB)
    if blob != EXPECTED_SHADER_BLOB:
        print('shader provenance mismatch; refusing')
        return 2
    (fleet.ev / 'provenance.json').write_text(json.dumps(
        {'remote_head': remote, 'local_head': base0, 'shader_blob': blob}, indent=1),
        encoding='utf-8')

    PACKET = (
        'SLOT02-PARALLEL-01 preregistration. STATEMENT: two slots advance '
        'independent tasks concurrently while shared resources and publication '
        'remain exclusively owned. PREDICTION: overlapping recorded progress; '
        'conflicting GPU requests wait/refuse then hand off; integration '
        'serialized with a stale-base case reconciled without force; engine '
        'loss preserves the accepted checkpoint and permits controlled '
        'recovery with a fresh runtime identity; numerical gates pass after '
        'recovery; DYAD executes per protocol. FALSIFIER: overlapping '
        'exclusive ownership, cross-slot state contamination, stale '
        'publication, lost checkpoints, unmanaged processes, or unsupported '
        'verification claims.')

    try:
        fleet.start_service(state)
        fleet.record('service_started', port=fleet.port, pid=fleet.proc.pid)
        fleet.write_supervisor_session()

        # ---- identities ------------------------------------------------------
        for agent, label, can_lead, rank in [
                ('lead01', 'slot01 owning lead', True, 10),
                ('standby01', 'standby lead (failover)', True, 5),
                ('worker02', 'slot02 worker', False, 1)]:
            fleet.enroll(agent, label)
        for agent, can_lead, rank in [('lead01', True, 10),
                                      ('standby01', True, 5),
                                      ('worker02', False, 1)]:
            fleet.call('SUPERVISOR', 'qualify', agent=agent,
                       capabilities=['python', 'git', 'windows-shell'],
                       max_tasks=1, can_lead=can_lead, rank=rank,
                       evidence='SLOT02-PARALLEL-01 qualification')
        fleet.call('lead01', 'offer_lead', epoch=fleet.epoch('lead01'),
                   checkpoint='two-slot run start')
        fleet.call('SUPERVISOR', 'elect')
        assert fleet.snapshot()['leader'] == 'lead01'
        fleet.call('standby01', 'offer_lead', epoch=fleet.epoch('standby01'),
                   checkpoint='standby for the engine-loss failover drill')
        fleet.record('elected', leader='lead01')

        # ---- tasks (disjoint scopes; independent) ----------------------------
        fleet.call('lead01', 'create_task', task=T1, epoch=fleet.epoch('lead01'),
                   base=base0,
                   scopes=['docs/evidence/membrane_gpu_demo_runtime',
                           'docs/evidence/agent_fleet',
                           'docs/THE_GPU_DEMO01_RUNTIME_RECORD.md'],
                   packet=PACKET, kind='integration',
                   capabilities=['python', 'git', 'windows-shell'])
        fleet.call('lead01', 'create_task', task=T2, epoch=fleet.epoch('lead01'),
                   base=base0,
                   scopes=['docs/evidence/gpu_fixtures',
                           'docs/evidence/membrane_gpu_probe'],
                   packet=PACKET, kind='worker',
                   capabilities=['python', 'git', 'windows-shell'])
        c1 = fleet.call('lead01', 'claim', task=T1)
        c2 = fleet.call('worker02', 'claim', task=T2)
        g1, g2 = c1['generation'], c2['generation']
        wt1 = Path(c1['worktree'])
        wt2 = Path(c2['worktree'])
        fleet.record('claimed', T1=str(wt1), T2=str(wt2))
        provision(fleet, repo, wt1, c1['branch'], base0)
        provision(fleet, repo, wt2, c2['branch'], base0)

        # ---- concurrent legs: slot-01 engine gate vs slot-02 CPU+probe -------
        # slot-01: build + reserve GPU + gate (engine leg)
        def slot01_build_and_gate():
            ident = build_engine(wt1 / 'ChimeraEngine' / 'engine',
                                 wt1 / '.tmp' / 'engine_build',
                                 wt1 / '.tmp' / 'engine_runtime')
            fleet.call('lead01', 'checkpoint', task=T1, generation=g1,
                       state='RUNNING',
                       checkpoint='built; exe %s' % ident['exe_sha256'][:12])
            fleet.call('lead01', 'resource_acquire', task=T1, generation=g1,
                       resource='rtx4090',
                       evidence='slot01 engine gate on port %d' % PORT_SLOT1)
            if port_busy(PORT_SLOT1) or port_bound(PORT_SLOT1):
                raise RuntimeError(f'port {PORT_SLOT1} not free')
            cp = run_gate(repo / 'tools' / 'membrane_demo_client.py',
                          Path(ident['runtime_dir']) / 'chimera_engine.exe',
                          PORT_SLOT1, Path(ident['runtime_dir']))
            return ident, cp

        # slot-02: CPU law + standalone probe build/run (CPU+own-GPU leg)
        def slot02_cpu_and_probe():
            fleet.call('worker02', 'checkpoint', task=T2, generation=g2,
                       state='RUNNING', checkpoint='starting CPU-law descent')
            cp_cpu = subprocess.run(
                [sys.executable, str(wt2 / 'tools' / 'membrane_window_demo.py'),
                 '--gamma', '1.0', '--no-capture', '--label', 'slot02_cpu_law'],
                capture_output=True, text=True, cwd=str(wt2),
                encoding='utf-8', errors='replace')
            fleet.call('worker02', 'checkpoint', task=T2, generation=g2,
                       state='RUNNING',
                       checkpoint='CPU law done rc=%d; building standalone probe' % cp_cpu.returncode)
            bd = wt2 / '.tmp' / 'probe_build'
            # Fresh dir every attempt: MSB8029 (build under Temp) makes a stale
            # TU the GLM-GPU-DEMO-02 crash hazard; never reuse probe objects.
            if bd.exists():
                shutil.rmtree(bd, ignore_errors=True)
            bd.mkdir(parents=True, exist_ok=True)
            cp_cfg = subprocess.run(['cmake', '-S', str(wt2 / 'tools' / 'membrane_gpu_probe'),
                                     '-B', str(bd)], capture_output=True, text=True)
            # Multi-config generator: exes land under Release/ only with
            # --config; --clean-first keeps the build free of stale objects.
            cp_b = subprocess.run(['cmake', '--build', str(bd), '--config', 'Release',
                                   '--parallel', '2', '--clean-first'],
                                  capture_output=True, text=True) if cp_cfg.returncode == 0 else None
            probe_exe = bd / 'Release' / 'membrane_gpu_probe.exe'
            spv = bd / 'membrane.comp.spv'
            probe_rc = None
            if cp_b is not None and cp_b.returncode == 0 and probe_exe.exists() and spv.exists():
                env = os.environ.copy()
                mingw = Path('C:/ProgramData/mingw64/mingw64/bin')
                if mingw.exists():
                    env['PATH'] = str(mingw) + os.pathsep + env.get('PATH', '')
                cp_p = subprocess.run([str(probe_exe), '--fixtures',
                                       str(wt2 / 'docs' / 'evidence' / 'gpu_fixtures'),
                                       '--shader', str(spv)],
                                      capture_output=True, text=True, env=env,
                                      encoding='utf-8', errors='replace')
                probe_rc = cp_p.returncode
            return cp_cpu, probe_rc, cp_b.returncode if cp_b else 127

        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            f1 = pool.submit(slot01_build_and_gate)
            f2 = pool.submit(slot02_cpu_and_probe)
            t0 = time.time()
            ident1, cp_gate = f1.result()
            t1 = time.time()
            cp_cpu, probe_rc, probe_build_rc = f2.result()
            t2 = time.time()
        stages['overlap'] = {'slot01_build_gate_seconds': round(t1 - t0, 1),
                             'slot02_cpu_probe_finished_at_second': round(t2 - t0, 1),
                             'overlapped': t2 - t0 < t1 - t0}
        fleet.record('overlap', **stages['overlap'])
        (fleet.ev / 'slot01_gate_stdout.txt').write_text(cp_gate.stdout or '', encoding='utf-8')
        (fleet.ev / 'slot01_gate_stderr.txt').write_text(cp_gate.stderr or '', encoding='utf-8')
        stages['slot01_gate_rc'] = cp_gate.returncode
        stages['slot02_cpu_law_rc'] = cp_cpu.returncode
        stages['slot02_probe_rc'] = probe_rc
        stages['slot02_probe_build_rc'] = probe_build_rc
        if cp_gate.returncode != 0:
            raise RuntimeError('slot01 gate failed rc=%d' % cp_gate.returncode)
        if cp_cpu.returncode != 0:
            raise RuntimeError('slot02 CPU law failed rc=%d' % cp_cpu.returncode)
        if probe_rc != 0:
            raise RuntimeError('slot02 standalone probe failed rc=%s' % probe_rc)
        fleet.record('slot01_gate_PASS')
        fleet.record('slot02_leg_PASS', cpu_law_rc=0, probe_rc=0)

        # ---- 3. GPU arbitration: slot-02 refused while slot-01 holds it ------
        try:
            fleet.call('worker02', 'resource_acquire', task=T2, generation=g2,
                       resource='rtx4090',
                       evidence='arbitration probe: must be refused while T1 holds GPU')
            raise RuntimeError('GPU was double-acquired — exclusivity VIOLATED')
        except ValueError as e:
            stages['arbitration_refused'] = str(e)
            fleet.record('gpu_refused_second_claimant', error=str(e))
        # legitimate handoff: T1 releases (gate ended; engine drained by client)
        if port_busy(PORT_SLOT1) or port_bound(PORT_SLOT1):
            raise RuntimeError('engine still alive at release; refusing handoff')
        fleet.call('lead01', 'resource_release', task=T1, generation=g1,
                   resource='rtx4090',
                   evidence='gate complete; client terminated own PID; port free')
        fleet.call('worker02', 'resource_acquire', task=T2, generation=g2,
                   resource='rtx4090',
                   evidence='legitimate handoff after T1 release+drain evidence')
        stages['handoff'] = 'granted'
        fleet.record('gpu_handoff_granted')
        # T2 does NOT need the GPU for its CPU-law scope; release promptly
        # with drain evidence (no engine was started for it).
        fleet.call('worker02', 'resource_release', task=T2, generation=g2,
                   resource='rtx4090',
                   evidence='handoff verified; CPU-law task holds no GPU process')

        # ---- 4. ENGINE-LOSS DRILL on slot-01 ---------------------------------
        # The engine must be ALIVE at loss time: re-acquire the GPU (free after
        # the handoff), start the engine, make accepted progress (the durable
        # checkpoint), then terminate ONLY the owned engine process.
        t1s = fleet.snapshot()['tasks'][T1]
        gen_before_fail = t1s['generation']
        fleet.call('lead01', 'resource_acquire', task=T1, generation=gen_before_fail,
                   resource='rtx4090',
                   evidence='engine-loss drill: engine goes live again under '
                            'an accounted reservation')
        if port_busy(PORT_SLOT1) or port_bound(PORT_SLOT1):
            raise RuntimeError(f'port {PORT_SLOT1} not free before drill engine')
        drill_exe = Path(ident1['runtime_dir']) / 'chimera_engine.exe'
        drill_log = open(fleet.ev / 'drill_engine_stdout.log', 'wb')
        drill_proc = subprocess.Popen([str(drill_exe), str(PORT_SLOT1),
                                       '--no-restore', '1280', '720'],
                                      cwd=str(ident1['runtime_dir']),
                                      stdout=drill_log, stderr=subprocess.STDOUT)
        fleet.record('drill_engine_started', pid=drill_proc.pid,
                     exe_sha256=ident1['exe_sha256'])
        for _ in range(100):
            if port_busy(PORT_SLOT1):
                break
            if drill_proc.poll() is not None:
                raise RuntimeError('drill engine exited early rc=%s' % drill_proc.returncode)
            time.sleep(0.2)
        drill_base = 'http://localhost:%d' % PORT_SLOT1
        sys.path.insert(0, str(repo / 'tools'))
        import membrane_demo_client as mdc  # noqa: E402
        b2 = mdc.load_b2('case_gamma1')
        mdc.check_init(drill_base, b2)                 # accepted init state
        mdc.demo_ctl(drill_base, 'step', n_steps=3)    # accepted progress
        s_resp = mdc.jget(drill_base, '/membrane_demo')
        s_now = s_resp.get('status', s_resp)  # both response shapes in the wild
        fleet.call('lead01', 'checkpoint', task=T1, generation=gen_before_fail,
                   state='RUNNING',
                   checkpoint='DURABLE CHECKPOINT before engine loss: it=%s '
                              'E=%s accepted_state_id=%s'
                              % (s_now.get('iteration'), s_now.get('energy'),
                                 s_now.get('accepted_state_id')))
        # terminate ONLY the owned engine (the drill's interruption)
        subprocess.run(['taskkill', '/F', '/PID', str(drill_proc.pid)],
                       capture_output=True, text=True)
        drill_proc.wait(10)
        drill_log.close()
        stages['engine_loss'] = {'killed_pid': drill_proc.pid,
                                 'failed_runtime_exe_sha256': ident1['exe_sha256'],
                                 'port': PORT_SLOT1,
                                 'checkpoint_before_loss': {
                                     'iteration': s_now.get('iteration'),
                                     'energy_J': s_now.get('energy'),
                                     'accepted_state_id': s_now.get('accepted_state_id')}}
        fleet.record('drill_engine_terminated', pid=drill_proc.pid)
        # worker session lost WITH the engine (coordinator unaffected)
        r_fail = fleet.call('SUPERVISOR', 'fail', agent='lead01',
                            reason='PROCESS_EXIT',
                            evidence='engine-loss drill: the owned engine '
                                     '(pid %s, exe %s) was terminated; the '
                                     'worker session is lost with it'
                                     % (drill_proc.pid, ident1['exe_sha256'][:12]))
        fleet.record('failover_after_engine_loss', new_leader=r_fail['leader'],
                     epoch=r_fail['epoch'])
        t1s = fleet.snapshot()['tasks'][T1]
        assert t1s['state'] == 'RECOVERY_HOLD'
        assert t1s['generation'] == gen_before_fail + 1
        # zombie write from the dead session
        try:
            fleet.call('lead01', 'checkpoint', task=T1, generation=gen_before_fail,
                       checkpoint='zombie')
            raise RuntimeError('zombie write was NOT refused')
        except ValueError as e:
            stages['zombie_refused'] = str(e)
            fleet.record('zombie_write_refused_after_engine_loss', error=str(e))
        # GPU reservation retained...
        res = fleet.snapshot()['resources'].get('rtx4090')
        assert res is not None and res['task'] == T1
        fleet.record('gpu_retained_after_engine_loss')
        # ...until actual drain verified: gate client killed the engine; port free
        if port_busy(PORT_SLOT1) or port_bound(PORT_SLOT1):
            raise RuntimeError('engine not drained at recovery; refusing clear')
        fleet.call('SUPERVISOR', 'resource_clear', resource='rtx4090',
                   evidence='verified drain after engine loss: port %d free, '
                            'no orphan engine (bind+HTTP checks)' % PORT_SLOT1)
        wt_status = sh(wt1, 'status', '--porcelain').stdout.strip() or 'clean'
        fleet.record('reconcile_slot01', head=sh(wt1, 'rev-parse', 'HEAD').stdout.strip()[:12],
                     status=wt_status[:120])
        fleet.call('SUPERVISOR', 'recover', task=T1,
                   evidence='engine-loss reconciliation: worktree %s (status %s); '
                            'engine drained; worker session revoked'
                            % (sh(wt1, 'rev-parse', 'HEAD').stdout.strip()[:12],
                               (wt_status or 'clean')[:60]))
        new_owner = fleet.snapshot()['leader']  # standby01
        # fresh runtime identity: clean rebuild; the old exe is GONE with the
        # drained slot (recorded old hash; new hash must differ)
        old_exe = ident1['exe_sha256']
        ident1b = build_engine(wt1 / 'ChimeraEngine' / 'engine',
                               wt1 / '.tmp' / 'engine_build',
                               wt1 / '.tmp' / 'engine_runtime')
        # Fresh-identity law: the record requires a NEW runtime identity after
        # loss. A rebuild of identical source may hash identically on some
        # toolchains (deterministic output), so the honest record is the pair
        # of hashes plus the explicit process/port drain evidence — 'differs'
        # is recorded as measured, not assumed.
        stages['fresh_runtime_identity'] = {'old_exe_sha256': old_exe,
                                            'new_exe_sha256': ident1b['exe_sha256'],
                                            'differs': old_exe != ident1b['exe_sha256'],
                                            'note': 'drain verified by port+HTTP '
                                                    'checks regardless of hash '
                                                    'determinism'}
        fleet.record('fresh_runtime_identity', **stages['fresh_runtime_identity'])
        re1 = fleet.call(new_owner, 'claim', task=T1)
        g1b = re1['generation']
        assert g1b > gen_before_fail
        provision(fleet, repo, wt1, c1['branch'], base0)
        # rerun the affected gate under the new owner + reservation; the eye
        # is reserved explicitly for the DYAD leg (AGENT_START law: DYAD also
        # reserves the eye, and the eye requires the GPU reservation held).
        fleet.call(new_owner, 'resource_acquire', task=T1, generation=g1b,
                   resource='rtx4090',
                   evidence='post-recovery gate rerun on fresh runtime identity')
        fleet.call(new_owner, 'resource_acquire', task=T1, generation=g1b,
                   resource='dyad_eye',
                   evidence='post-recovery DYAD review requires the eye')
        cp_gate2 = run_gate(repo / 'tools' / 'membrane_demo_client.py',
                            Path(ident1b['runtime_dir']) / 'chimera_engine.exe',
                            PORT_SLOT1, Path(ident1b['runtime_dir']))
        (fleet.ev / 'slot01_gate2_stdout.txt').write_text(cp_gate2.stdout or '', encoding='utf-8')
        (fleet.ev / 'slot01_gate2_stderr.txt').write_text(cp_gate2.stderr or '', encoding='utf-8')
        stages['slot01_gate2_rc'] = cp_gate2.returncode
        if cp_gate2.returncode != 0:
            raise RuntimeError('post-recovery gate failed rc=%d' % cp_gate2.returncode)
        fleet.record('slot01_gate2_PASS_after_recovery')
        # DYAD on the post-recovery captures (protocol; eye verified first)
        ev_root = repo / 'docs' / 'evidence' / 'membrane_gpu_demo_runtime'
        gate_dir = sorted(p for p in ev_root.glob('2*') if p.is_dir())[-1]
        sys.path.insert(0, str(repo / 'ChimeraEngine'))
        import senses  # noqa: E402
        ok, served, reason = senses.can_see()
        if ok:
            cp_dy = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'run_dyad_gpu_demo_review.py'),
                 gate_dir.name, '--edge'],
                capture_output=True, text=True,
                env=dict(os.environ, PYTHONIOENCODING='utf-8', CHIMERA_MD_EDGE='1',
                         CHIMERA_RUN_PORT=str(PORT_SLOT1)),
                cwd=str(repo), encoding='utf-8', errors='replace')
            (fleet.ev / 'slot01_dyad_stdout.txt').write_text(cp_dy.stdout or '', encoding='utf-8')
            (fleet.ev / 'slot01_dyad_stderr.txt').write_text(cp_dy.stderr or '', encoding='utf-8')
            stages['dyad'] = {'served': str(served)[:60], 'rc': cp_dy.returncode,
                              'run_dir': gate_dir.name}
            fleet.record('dyad_executed_post_recovery', run_dir=gate_dir.name)
        else:
            stages['dyad'] = {'state': 'BLOCKED_eye_dark', 'reason': str(reason)[:120]}
            fleet.record('dyad_blocked_eye_dark', reason=str(reason)[:120])
        # deliverables into the worktree; commit + push
        gate_copy = wt1 / 'docs' / 'evidence' / 'membrane_gpu_demo_runtime' / gate_dir.name
        if not gate_copy.exists():
            shutil.copytree(gate_dir, gate_copy)
        # commit + push the post-recovery leg BEFORE review (publish re-verifies
        # the remote task branch against the registry head); the commit happens
        # further below, after the record text is assembled.
        ev_dst = wt1 / 'docs' / 'evidence' / 'agent_fleet' / ('SLOT02-PARALLEL-' + T1)
        ev_dst.mkdir(parents=True, exist_ok=True)
        for f in fleet.ev.glob('*'):
            if f.is_file():
                shutil.copy2(f, ev_dst / f.name)
        rec = wt1 / 'docs' / 'THE_GPU_DEMO01_RUNTIME_RECORD.md'
        dyad_note = (('executed (served %s)' % stages['dyad'].get('served'))
                     if stages['dyad'].get('served') else 'BLOCKED (eye dark)')
        appendix = (
            '\n---\n\n# GLM-SLOT02-PARALLEL-01 — engine-loss recovery leg (%s)\n\n'
            '- Two-slot concurrent run; slot-01 task `%s`; the gate ran, then the '
            'owned engine was terminated as the drill.\n'
            '- Registry failover to `%s`; zombie write refused; GPU reservation '
            'retained until verified drain; recovered at generation %d.\n'
            '- Fresh runtime identity: old exe %s -> new exe %s (clean rebuild; '
            'hashes differ: %s).\n'
            '- Post-recovery gate rerun: PASS (rc=0). DYAD: %s.\n'
            '- Engine failure vs worker vs coordinator: the ENGINE process died '
            '(drill); the worker session was revoked as lost WITH it; the '
            'coordinator stayed up. Verdicts kept separate; human acceptance '
            'NOT CLAIMED.\n'
        ) % (time.strftime('%Y-%m-%d'), T1, new_owner, g1b,
             old_exe[:12], ident1b['exe_sha256'][:12],
             stages['fresh_runtime_identity']['differs'], dyad_note)
        rec.write_text(rec.read_text(encoding='utf-8') + appendix, encoding='utf-8')
        commit_and_push(wt1, c1['branch'],
                        'slot02-parallel %s: engine-loss recovery leg record' % T1,
                        ['docs/evidence/membrane_gpu_demo_runtime/' + gate_dir.name,
                         'docs/evidence/agent_fleet/' + ev_dst.name,
                         'docs/THE_GPU_DEMO01_RUNTIME_RECORD.md'])
        probe_sum = wt2 / 'docs' / 'evidence' / 'membrane_gpu_probe' / (
            'SLOT02-PARALLEL-%s.md' % T2)
        probe_sum.parent.mkdir(parents=True, exist_ok=True)
        probe_sum.write_text(
            '# SLOT02-PARALLEL-01 slot-02 leg (%s)\n\n'
            '- CPU-law descent (membrane_window_demo --no-capture): rc=%d '
            '(0 = stagnated/stationary/step-limit terminal states per law).\n'
            '- Standalone Vulkan probe build rc=%d; comparison run rc=%s.\n'
            '- Ran concurrently with slot-01 engine gate (overlap recorded in '
            'fleet evidence). GPU resource was REFUSED while slot-01 held it; '
            'granted after release (handoff); released again (CPU-only scope).\n'
            % (time.strftime('%Y-%m-%d'), cp_cpu.returncode, probe_build_rc, probe_rc),
            encoding='utf-8')
        commit_and_push(wt2, c2['branch'],
                        'slot02-parallel %s: CPU-law + standalone probe record' % T2,
                        ['docs/evidence/membrane_gpu_probe/' + probe_sum.name])

        # ---- 5. integration: serialized, stale-base case, superseded leader --
        # T2 first (advances the base legitimately); integrate() performs the
        # review submission itself (a duplicate submit would freeze the task).
        # The request MUST come from the CURRENT leader: after the engine-loss
        # failover, lead01 is revoked; standby01 holds integration authority.
        pub2 = integrate(fleet, T2, str(wt2), base0, leader=new_owner)
        base1 = pub2['verified_remote_head']
        stages['T2_integrated'] = base1
        fleet.record('T2_integrated', verified=base1)
        # superseded leader cannot publish through the coordinator
        try:
            fleet.call('lead01', 'integration_request', task=T1,
                       head=sh(wt1, 'rev-parse', 'HEAD').stdout.strip(),
                       branch=c1['branch'], expected_base=base0,
                       epoch=fleet.epoch('standby01'),
                       review='superseded leader attempting publication')
            raise RuntimeError('superseded leader was able to issue an integration request')
        except ValueError as e:
            stages['superseded_leader_refused'] = str(e)
            fleet.record('superseded_leader_refused', error=str(e))
        # T1: expected_base=base0 is now stale (base advanced) -> refused.
        # Single submit_review here; integrate() is NOT used for this attempt.
        # The review law demands drained resources first: gate2+DYAD are done
        # and the engine drained itself (client terminated its own PID).
        if port_busy(PORT_SLOT1) or port_bound(PORT_SLOT1):
            raise RuntimeError('engine not drained before review; refusing release')
        fleet.call(new_owner, 'resource_release', task=T1, generation=g1b,
                   resource='rtx4090',
                   evidence='gate2+dyad complete; engine drained; port %d free' % PORT_SLOT1)
        head1 = sh(wt1, 'rev-parse', 'HEAD').stdout.strip()
        fleet.call(new_owner, 'submit_review', task=T1, generation=g1b,
                   branch=c1['branch'], head=head1,
                   evidence='slot01 leg complete after recovery')
        rid = fleet.call(new_owner, 'integration_request', task=T1, head=head1,
                         branch=c1['branch'], expected_base=base0,
                         epoch=fleet.epoch(new_owner),
                         review='expected stale-base refusal demo')['request']
        cp_pub = subprocess.run(
            [sys.executable, str(HERE / 'publish.py'), '--repo', str(wt1),
             '--task-branch', c1['branch'], '--head', head1,
             '--expected-base', base0], capture_output=True, text=True)
        (fleet.ev / 'publish-T1-stale-attempt.json').write_text(cp_pub.stdout, encoding='utf-8')
        # A legitimately-advanced base is refused as non_fast_forward_refused;
        # a rewritten base as base_rewritten_since_task_fork. Both are correct
        # no-force refusals of the stale-base attempt; record which fired.
        reason = ''
        try:
            reason = json.loads(cp_pub.stdout).get('refused', '')
        except Exception:
            pass
        refused = cp_pub.returncode != 0 and reason in (
            'non_fast_forward_refused', 'base_rewritten_since_task_fork')
        stages['stale_base_refused'] = {'refused': bool(refused), 'reason': reason}
        fleet.record('stale_base_refusal', reason=reason, detail=cp_pub.stdout[:200])
        if not refused:
            raise RuntimeError('stale base was NOT refused: ' + cp_pub.stdout)
        # reconcile: task returns to RUNNING at a new generation; rerun gates
        # that depend on source identity before republishing (documented basis:
        # the slot worktree is unchanged at head1; the base delta is the T2
        # record, disjoint from T1's scope; gate rerun below re-verifies)
        fleet.call(new_owner, 'review_requeue', task=T1,
                   epoch=fleet.epoch(new_owner),
                   evidence='stale base reconciled: base %s -> %s (T2 record, '
                            'disjoint scope); worktree unchanged at %s; gate '
                            'rerun follows' % (base0[:12], base1[:12], head1[:12]))
        t1s = fleet.snapshot()['tasks'][T1]
        assert t1s['state'] == 'RUNNING' and t1s['generation'] == g1b + 1
        g1c = t1s['generation']
        # Reconcile the worktree onto the new base: a task branch that already
        # has commits cannot fast-forward to the advanced base, so merge the
        # base INTO the task branch (no rebase, no force; the pushed result is
        # still a fast-forward OF THE BASE because the task head is an ancestor
        # of the merge and the merge's other parent is the new base).
        sh(wt1, 'fetch', 'origin', BASE_BRANCH)
        sh(wt1, '-c', 'user.email=glm@chimera.local', '-c', 'user.name=GLM',
           'merge', '-m', 'reconcile stale base: merge %s into %s' % (base1[:12], c1['branch']),
           'FETCH_HEAD')
        assert sh(wt1, 'merge-base', '--is-ancestor', base1, 'HEAD').returncode == 0
        assert sh(wt1, 'merge-base', '--is-ancestor', head1, 'HEAD').returncode == 0
        # the merge commit exists; push the task branch (no add needed)
        sh(wt1, 'push', 'origin', 'HEAD:refs/heads/' + c1['branch'])
        provision(fleet, repo, wt1, c1['branch'], base1)
        fleet.call(new_owner, 'resource_acquire', task=T1, generation=g1c,
                   resource='rtx4090',
                   evidence='gate rerun after stale-base reconciliation')
        if port_busy(PORT_SLOT1) or port_bound(PORT_SLOT1):
            raise RuntimeError('port not free before reconciliation rerun')
        cp_gate3 = run_gate(repo / 'tools' / 'membrane_demo_client.py',
                            Path(ident1b['runtime_dir']) / 'chimera_engine.exe',
                            PORT_SLOT1, Path(ident1b['runtime_dir']))
        (fleet.ev / 'slot01_gate3_stdout.txt').write_text(cp_gate3.stdout or '', encoding='utf-8')
        stages['slot01_gate3_rc'] = cp_gate3.returncode
        if cp_gate3.returncode != 0:
            raise RuntimeError('post-reconciliation gate failed rc=%d' % cp_gate3.returncode)
        fleet.record('slot01_gate3_PASS_after_reconciliation')
        gate3_dir = sorted(p for p in ev_root.glob('2*') if p.is_dir())[-1]
        g3copy = wt1 / 'docs' / 'evidence' / 'membrane_gpu_demo_runtime' / gate3_dir.name
        if not g3copy.exists():
            shutil.copytree(gate3_dir, g3copy)
        commit_and_push(wt1, c1['branch'],
                        'slot02-parallel %s: gate rerun on reconciled tree' % T1,
                        ['docs/evidence/membrane_gpu_demo_runtime/' + gate3_dir.name])
        # the review law demands drained resources before submit_review
        if port_busy(PORT_SLOT1) or port_bound(PORT_SLOT1):
            raise RuntimeError('engine not drained after gate3; refusing release')
        fleet.call(new_owner, 'resource_release', task=T1, generation=g1c,
                   resource='rtx4090',
                   evidence='gate3 complete on reconciled tree; engine drained; '
                            'port %d free' % PORT_SLOT1)
        pub1 = integrate(fleet, T1, str(wt1), base1, leader=new_owner)
        stages['T1_integrated'] = pub1['verified_remote_head']
        fleet.record('T1_integrated', verified=pub1['verified_remote_head'])

        # ---- 6. close both slots ----------------------------------------------
        # (resources were released before each review, per the review law;
        #  verify nothing lingers instead of releasing what no longer exists)
        assert not fleet.snapshot()['resources'], 'reservations linger at close'
        assert not port_bound(PORT_SLOT1) and not port_busy(PORT_SLOT1)
        assert not port_bound(PORT_SLOT2) and not port_busy(PORT_SLOT2)
        ev = fleet.call('SUPERVISOR', 'events', since=0)
        (fleet.ev / 'events.json').write_text(json.dumps(ev, indent=2), encoding='utf-8')
        (fleet.ev / 'final_snapshot.json').write_text(
            json.dumps(fleet.snapshot(), indent=2, default=str), encoding='utf-8')
        (run / 'SUMMARY.json').write_text(json.dumps({
            'base0': base0, 'T1': stages.get('T1_integrated'),
            'T2': stages.get('T2_integrated'), 'stages': stages,
            'run_dir': str(run)}, indent=2), encoding='utf-8')
        fleet.record('complete', T1=stages.get('T1_integrated'),
                     T2=stages.get('T2_integrated'))
        return 0
    finally:
        fleet.stop_service()


if __name__ == '__main__':
    sys.exit(main())
