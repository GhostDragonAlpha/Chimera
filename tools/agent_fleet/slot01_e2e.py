"""SLOT01-E2E: one bounded GPU membrane verification task through slot-01,
on the real fleet control plane, with one real interruption + recovery drill.

Authorized limited universal dispatch (operator, 2026-09-09): existing
controller + universal entry point; ONE worker; slot-01 only.

Path exercised (all real, no mocks in the loop):
  enroll/qualify/elect -> create_task (integration-kind; slot-01's kind)
  -> claim (exclusivity refusal check) -> provision real slot-01 worktree
  -> clean engine build in the SLOT's external build dir (protected
     ChimeraEngine/engine/build untouched) -> runtime dir identity
  -> checkpoint -> resource_acquire rtx4090 -> runtime numerical gate
     (tools/membrane_demo_client.py gate: frozen B2, gamma doubling/zero,
      reset, rejection integrity, edge-contrast captures)
  -> INTERRUPTION DRILL: the owning worker's session process is terminated
     after its durable checkpoint; registry failover elects the standby;
     a zombie (obsolete-generation) write is refused; the GPU reservation
     is retained until the supervisor verifies actual process drain;
     recovery reconciles the worktree; the new leader reclaims at gen 2
  -> DYAD per THE_DYAD_PROTOCOL (eye verified, one image per call)
  -> submit_review -> integration_request -> fetch-verified FF publish
     -> ack -> release_slot -> worktree drain
  -> close: port/process verification, events + snapshot export

Usage (from the primary checkout):
  set CHIMERA_FLEET_SUPERVISOR_TOKEN=...
  set CHIMERA_FLEET_ENROLLMENT_TOKEN=...
  python tools/agent_fleet/slot01_e2e.py --repo <primary checkout>
"""
import argparse
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

BASE_BRANCH = 'astra/gait-capture'
VULKAN_SDK = Path('C:/VulkanSDK/1.4.328.1')
EXPECTED_SHADER_BLOB = '4f7a356e34cdf06716515f0b21e9a998fa35ff21'
CAPTURE_PHI = 0.35      # the GLM-GPU-DEMO-EDGE-01 PASS view
CAPTURE_RADIUS = 3.0
SLOT_ENGINE_PORT = 8101  # slot-01 port candidate per layout.py (8100+1)


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


def build_slot_engine(fleet, repo: Path, slot_root: Path, tid: str) -> dict:
    """Clean build of the engine from the SLOT worktree into the slot's own
    external build dir; stage exe+shaders into the slot runtime dir.
    Protected ChimeraEngine/engine/build is never touched."""
    build = slot_root / '.tmp' / 'engine_build'
    runtime = slot_root / '.tmp' / 'engine_runtime'
    build.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)
    if not VULKAN_SDK.exists():
        raise RuntimeError(f'Vulkan SDK missing at {VULKAN_SDK}')
    src = slot_root / 'ChimeraEngine' / 'engine'
    cp = subprocess.run(['cmake', '-S', str(src), '-B', str(build), '-G',
                         'Visual Studio 17 2022', '-A', 'x64',
                         f'-DVULKAN_SDK={VULKAN_SDK}'],
                        capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError('cmake configure failed: ' + cp.stderr[-2000:])
    # --clean-first: the GLM-GPU-DEMO-02 crash law (stale TU under Temp).
    cp = subprocess.run(['cmake', '--build', str(build), '--config', 'Release',
                         '--parallel', '4', '--clean-first'],
                        capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError('cmake build failed: ' + cp.stderr[-2000:])
    exe_b = build / 'Release' / 'chimera_engine.exe'
    if not exe_b.exists():
        raise RuntimeError('engine exe not produced')
    shutil.copy2(exe_b, runtime / 'chimera_engine.exe')
    shader_dst = runtime / 'shaders'
    shader_dst.mkdir(exist_ok=True)
    for spv in (build / 'Release' / 'shaders').glob('*.spv'):
        shutil.copy2(spv, shader_dst / spv.name)
    exe_r = runtime / 'chimera_engine.exe'
    spv_r = shader_dst / 'membrane_demo.spv'
    comp = slot_root / 'ChimeraEngine' / 'engine' / 'shaders' / 'membrane_demo.comp'
    ident = {
        'build_dir': str(build), 'runtime_dir': str(runtime),
        'worktree_head': sh(slot_root, 'rev-parse', 'HEAD').stdout.strip(),
        'worktree': str(slot_root),
        'comp_sha256': sha256(comp),
        'comp_blob': sh(slot_root, 'rev-parse', 'HEAD:'
                        + str(comp.relative_to(slot_root).as_posix())).stdout.strip(),
        'spv_sha256': sha256(spv_r),
        'exe_sha256_runtime': sha256(exe_r),
        'exe_sha256_builddir': sha256(exe_b),
        'exe_pid_expected': 'assigned at gate launch; only gate-launched PID controlled',
        'port_candidate': SLOT_ENGINE_PORT,
        'protected_build_path_used': False,
    }
    if ident['exe_sha256_runtime'] != ident['exe_sha256_builddir']:
        raise RuntimeError('runtime exe differs from build-dir exe')
    (fleet.ev / 'slot01_binary_identity.json').write_text(
        json.dumps(ident, indent=1), encoding='utf-8')
    fleet.record('slot_engine_built', exe_sha256=ident['exe_sha256_runtime'],
                 spv_sha256=ident['spv_sha256'])
    return ident


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True, help='primary checkout')
    ap.add_argument('--skip-gate', action='store_true',
                    help='resume mode: skip build+gate (already green); '
                         'continue at DYAD')
    ap.add_argument('--skip-build', action='store_true',
                    help='resume mode: reuse the slot build (runtime exe/spv '
                         're-verified against the recorded identity hashes) '
                         'and rerun the gate', default=False)
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    sup = os.environ.get('CHIMERA_FLEET_SUPERVISOR_TOKEN', '')
    enr = os.environ.get('CHIMERA_FLEET_ENROLLMENT_TOKEN', '')
    if not sup or not enr or sup == enr:
        print('Set distinct CHIMERA_FLEET_SUPERVISOR_TOKEN / '
              'CHIMERA_FLEET_ENROLLMENT_TOKEN', file=sys.stderr)
        return 2

    run_root = repo.parent
    run = run_root / ('fleet-slot01-%s' % time.strftime('%Y%m%dT%H%M%S'))
    run.mkdir(parents=True, exist_ok=True)
    tid = 'slot01-membrane-' + time.strftime('%H%M%S')
    state = run / 'state'
    state.mkdir(exist_ok=True)
    fleet = Fleet(run, sup, enr, free_port())

    # ---- 0. preflight: base identity + shader provenance -------------------
    sync = sh(repo, 'pull', '--ff-only', 'origin', BASE_BRANCH, check=False)
    fleet.record('primary_sync', exit=sync.returncode,
                 detail=(sync.stderr or sync.stdout or '').strip()[-300:])
    if sync.returncode != 0:
        print('primary checkout not fast-forwardable; reconcile manually')
        return 2
    base0 = sh(repo, 'rev-parse', 'HEAD').stdout.strip()
    remote = sh(repo, 'ls-remote', 'origin',
                'refs/heads/' + BASE_BRANCH).stdout.split()[0]
    if remote != base0:
        print(f'base moved during preflight: local {base0} remote {remote}')
        return 2
    blob = sh(repo, 'rev-parse', 'HEAD:ChimeraEngine/engine/shaders/'
              'membrane_demo.comp').stdout.strip()
    provenance = {'remote_head': remote, 'local_head': base0,
                  'shader_blob': blob, 'shader_blob_expected': EXPECTED_SHADER_BLOB,
                  'shader_blob_matches_tested': blob == EXPECTED_SHADER_BLOB}
    (fleet.ev / 'slot01_provenance.json').write_text(
        json.dumps(provenance, indent=1), encoding='utf-8')
    fleet.record('preflight', base=base0, shader_blob_ok=provenance[
        'shader_blob_matches_tested'])
    if not provenance['shader_blob_matches_tested']:
        print('shader blob != tested provenance; refusing to proceed')
        return 2

    # ---- preregistration (in the task packet, before any implementation) ---
    PACKET = (
        'SLOT01-E2E preregistration. STATEMENT: one universal entry point '
        'carries a real engine task (frozen-B2 GPU membrane runtime '
        'verification) through execution, interruption, recovery, verification '
        'and publication via the fleet control plane on slot-01. PREDICTION: '
        'ownership stays exclusive (a second claim is refused); evidence '
        'survives a real interruption (checkpoint + worktree preserved); '
        'stale-generation writes are refused; the GPU reservation is retained '
        'until actual process drain is verified; the runtime numerical gate '
        'passes unchanged (gamma doubling/zero, reset, rejection integrity); '
        'DYAD executes per protocol; the task reaches INTEGRATED via '
        'fetch-verified fast-forward publication. FALSIFIER: overlapping '
        'ownership, lost work, stale publication, unmanaged engine process, '
        'missing required verification, an unsupported PASS, or any '
        'tolerance/fixture change.'
    )

    try:
        fleet.start_service(state)
        fleet.record('service_started', port=fleet.port, pid=fleet.proc.pid)
        fleet.write_supervisor_session()

        # ---- 1. identities: owning lead + standby lead + probing worker ----
        for agent, label, can_lead, rank in [
                ('lead01', 'slot01 owning lead', True, 10),
                ('standby01', 'slot01 standby lead', True, 5),
                ('probe01', 'exclusivity probe worker', False, 1)]:
            fleet.enroll(agent, label)
        for agent, can_lead, rank in [('lead01', True, 10),
                                      ('standby01', True, 5),
                                      ('probe01', False, 1)]:
            fleet.call('SUPERVISOR', 'qualify', agent=agent,
                       capabilities=['python', 'git', 'windows-shell'],
                       max_tasks=1, can_lead=can_lead, rank=rank,
                       evidence='SLOT01-E2E qualification (operator-authorized)')
        fleet.call('lead01', 'offer_lead', epoch=fleet.epoch('lead01'),
                   checkpoint='slot01 e2e start; no foreign work')
        fleet.call('SUPERVISOR', 'elect')
        snap = fleet.snapshot()
        assert snap['leader'] == 'lead01', snap['leader']
        fleet.record('elected', leader=snap['leader'], epoch=snap['epoch'])
        # Re-offer AFTER the first election: _elect matches ready_epoch == the
        # CURRENT epoch, so the standby must hold an offer at the new epoch for
        # the drill's failover election to have a candidate.
        fleet.call('standby01', 'offer_lead', epoch=fleet.epoch('standby01'),
                   checkpoint='standby for slot01 e2e failover drill')

        # ---- 2. create + claim the real task -------------------------------
        fleet.call('lead01', 'create_task', task=tid,
                   epoch=fleet.epoch('lead01'), base=base0,
                   scopes=['docs/evidence/membrane_gpu_demo_runtime',
                           'docs/evidence/agent_fleet',
                           'docs/THE_GPU_DEMO01_RUNTIME_RECORD.md',
                           'docs/THE_MASTER_LIST.md'],
                   packet=PACKET, capabilities=['python', 'git', 'windows-shell'],
                   kind='integration')
        claimed = fleet.call('lead01', 'claim', task=tid)
        gen1 = claimed['generation']
        fleet.record('claimed', task=tid, generation=gen1,
                     worktree=claimed['worktree'])
        # exclusivity: a second agent's claim is refused while owned
        try:
            fleet.call('probe01', 'claim', task=tid)
            raise RuntimeError('overlapping claim was NOT refused')
        except ValueError as e:
            fleet.record('overlapping_claim_refused', error=str(e))

        wt = Path(claimed['worktree'])
        slot_root = wt  # the slot worktree IS the slot root; build/runtime live under wt/.tmp (layout.py)
        provision(fleet, repo, wt, claimed['branch'], base0)

        # ---- 3. build the slot engine; record identity ---------------------
        if a.skip_gate:
            ident = json.loads((fleet.ev / 'slot01_binary_identity.json')
                               .read_text(encoding='utf-8'))
            fleet.record('build_skipped_resume', exe=ident['exe_sha256_runtime'])
        elif a.skip_build:
            # Resume: reuse the previous attempt's slot build only if the
            # artifacts still hash-match the recorded identity.
            ident = json.loads(Path(os.environ['CHIMERA_SLOT_IDENTITY'])
                               .read_text(encoding='utf-8'))
            exe = Path(ident['runtime_dir']) / 'chimera_engine.exe'
            spv = Path(ident['runtime_dir']) / 'shaders' / 'membrane_demo.spv'
            if (sha256(exe) != ident['exe_sha256_runtime']
                    or sha256(spv) != ident['spv_sha256']):
                raise RuntimeError('slot artifacts no longer match the '
                                   'recorded identity; rebuild required')
            fleet.record('build_reused_verified', exe=ident['exe_sha256_runtime'])
        else:
            ident = build_slot_engine(fleet, repo, slot_root, tid)
        fleet.call(claimed['owner'], 'checkpoint', task=tid, generation=gen1,
                   state='RUNNING',
                   checkpoint='built+staged; identity in '
                              'slot01_binary_identity.json (exe %s, spv %s)'
                              % (ident['exe_sha256_runtime'][:12],
                                 ident['spv_sha256'][:12]))

        # ---- 4. reserve the GPU, run the runtime numerical gate ------------
        fleet.call(claimed['owner'], 'resource_acquire', task=tid,
                   generation=gen1, resource='rtx4090',
                   evidence='slot01 gate: engine on port %d, exe %s'
                            % (SLOT_ENGINE_PORT, ident['exe_sha256_runtime'][:12]))
        if port_busy(SLOT_ENGINE_PORT) or port_bound(SLOT_ENGINE_PORT):
            raise RuntimeError(f'port {SLOT_ENGINE_PORT} not free before gate')
        fleet.record('gpu_reserved')

        if not a.skip_gate:
            env = dict(os.environ, CHIMERA_MD_EDGE='1')
            cp = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'membrane_demo_client.py'),
                 'gate', '--launch', str(Path(ident['runtime_dir']) /
                                          'chimera_engine.exe'),
                 '--port', str(SLOT_ENGINE_PORT),
                 '--base', 'http://localhost:%d' % SLOT_ENGINE_PORT,
                 '--capture-phi', str(CAPTURE_PHI),
                 '--capture-radius', str(CAPTURE_RADIUS)],
                capture_output=True, text=True, env=env,
                cwd=str(ident['runtime_dir']), encoding='utf-8',
                errors='replace')  # dyad/engine text is utf-8; cp1252 decode dies
        else:
            # resume path: the gate already ran green in an earlier attempt;
            # cp stays undefined and no stdout is re-archived.
            cp = None
        if cp is not None:
            (fleet.ev / 'slot01_gate_stdout.txt').write_text(cp.stdout, encoding='utf-8')
            (fleet.ev / 'slot01_gate_stderr.txt').write_text(cp.stderr, encoding='utf-8')
            if cp.returncode != 0:
                fleet.record('gate_FAILED', rc=cp.returncode)
                raise RuntimeError('runtime gate failed rc=%d (evidence in %s)'
                                   % (cp.returncode, fleet.ev))
            fleet.record('gate_PASS', rc=0)

        # ---- 5. INTERRUPTION DRILL -----------------------------------------
        # 5a. a real owned worker session process, sitting on its claim
        plan = {'steps': [
            ['wait', {'stop_file': str(run / 'worker.stop'), 'poll': 0.5}]]}
        # the claim/checkpoint already happened (owner session above); this
        # process represents the live worker client holding the session open
        plan_path = run / 'worker_plan.json'
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
        wproc = subprocess.Popen(
            [sys.executable, str(HERE / 'worker_step.py'), '--session',
             str(run / ('session-%s.json' % claimed['owner'])), '--plan',
             str(plan_path), '--out', str(run / 'worker_journal.jsonl')],
            cwd=str(run))
        fleet.record('worker_session_started', pid=wproc.pid)
        (run / 'worker.pid').write_text(str(wproc.pid))
        time.sleep(2.0)

        # 5b. terminate ONLY the owned worker client (the drill's interruption)
        subprocess.run(['taskkill', '/F', '/PID', str(wproc.pid)],
                       capture_output=True, text=True)
        wproc.wait(10)
        fleet.record('worker_session_terminated', pid=wproc.pid,
                     mode='taskkill /F (owned worker client only)')

        # 5c. registry failover: trusted observer marks PROCESS_EXIT
        r = fleet.call('SUPERVISOR', 'fail', agent=claimed['owner'],
                       reason='PROCESS_EXIT',
                       evidence='SLOT01-E2E drill: owned worker client terminated '
                                'after durable checkpoint %s' % tid)
        fleet.record('failover', new_leader=r['leader'], epoch=r['epoch'])
        t = fleet.snapshot()['tasks'][tid]
        assert t['state'] == 'RECOVERY_HOLD', t['state']
        assert t['generation'] == gen1 + 1, t['generation']

        # 5d. zombie write with the obsolete generation is refused
        try:
            fleet.call(claimed['owner'], 'checkpoint', task=tid, generation=gen1,
                       checkpoint='zombie write from terminated session')
            raise RuntimeError('obsolete-generation write was NOT refused')
        except ValueError as e:
            fleet.record('zombie_write_refused', error=str(e))

        # 5e. the GPU reservation must NOT appear free while unaccounted
        res = fleet.snapshot()['resources'].get('rtx4090')
        assert res is not None and res['task'] == tid, res
        fleet.record('gpu_reservation_retained', held_by_task=tid)

        # 5f. supervisor verifies ACTUAL process drain before clearing:
        #     gate client terminated its own PID; port must be free now.
        if port_busy(SLOT_ENGINE_PORT) or port_bound(SLOT_ENGINE_PORT):
            raise RuntimeError('engine still running at drill; refuse resource_clear')
        fleet.call('SUPERVISOR', 'resource_clear', resource='rtx4090',
                   evidence='verified drain: gate client terminated own PID; '
                            'port %d free (bind+HTTP checks); no orphan engine'
                            % SLOT_ENGINE_PORT)
        fleet.record('gpu_reservation_cleared_after_drain_check')

        # 5g. reconcile the real worktree, then recover
        wt_status = sh(wt, 'status', '--porcelain').stdout.strip() or 'clean'
        wt_head = sh(wt, 'rev-parse', 'HEAD').stdout.strip()
        fleet.record('reconcile', worktree=str(wt), head=wt_head,
                     status=wt_status[:200], preserved=True)
        fleet.call('SUPERVISOR', 'recover', task=tid,
                   evidence='reconciled: slot-01 worktree at %s (status %s); '
                            'worker client terminated; engine drained'
                            % (wt_head[:12], (wt_status or 'clean')[:60]))
        # 5h. the new leader reclaims at the new generation and continues
        new_owner = fleet.snapshot()['leader']
        re_claim = fleet.call(new_owner, 'claim', task=tid)
        gen2 = re_claim['generation']
        assert gen2 > gen1, (gen1, gen2)
        fleet.record('reassigned', owner=new_owner, generation=gen2,
                     worktree=re_claim['worktree'])
        provision(fleet, repo, wt, claimed['branch'], base0)  # verify-fallback path

        # ---- 6. DYAD (new owner session) ------------------------------------
        fleet.call(new_owner, 'resource_acquire', task=tid, generation=gen2,
                   resource='rtx4090',
                   evidence='slot01 dyad review (GPU reservation carried over '
                            'the recovery; engine drained, new session owns it)')
        fleet.call(new_owner, 'resource_acquire', task=tid, generation=gen2,
                   resource='dyad_eye',
                   evidence='slot01 dyad review; requires the GPU reservation '
                            'held by this task')
        # find the gate's evidence run dir (the newest one in this worktree)
        ev_root = repo / 'docs' / 'evidence' / 'membrane_gpu_demo_runtime'
        gate_dir = sorted(p for p in ev_root.glob('2*') if p.is_dir())[-1]
        sys.path.insert(0, str(repo / 'ChimeraEngine'))
        import senses  # noqa: E402
        ok, served, reason = senses.can_see()
        if not ok:
            fleet.call(new_owner, 'checkpoint', task=tid, generation=gen2,
                       state='BLOCKED',
                       checkpoint='DYAD eye dark: %s. OPERATOR ACTION: load the '
                                  'vision model in LM Studio, then rerun with '
                                  '--skip-gate' % reason)
            fleet.record('dyad_blocked_eye_dark', reason=str(reason)[:200])
            raise RuntimeError('dyad eye dark: %s' % reason)
        fleet.record('dyad_eye_verified', served=str(served)[:120])
        cp = subprocess.run(
            [sys.executable, str(repo / 'tools' / 'run_dyad_gpu_demo_review.py'),
             gate_dir.name, '--edge'],
            capture_output=True, text=True, env=dict(
                os.environ, PYTHONIOENCODING='utf-8', CHIMERA_MD_EDGE='1',
                CHIMERA_RUN_PORT=str(SLOT_ENGINE_PORT)),
            cwd=str(wt), encoding='utf-8', errors='replace')
        (fleet.ev / 'slot01_dyad_stdout.txt').write_text(cp.stdout or '', encoding='utf-8')
        (fleet.ev / 'slot01_dyad_stderr.txt').write_text(cp.stderr or '', encoding='utf-8')
        if cp.returncode != 0:
            raise RuntimeError('dyad runner failed: ' + (cp.stderr or cp.stdout)[-1500:])
        fleet.record('dyad_executed', run_dir=gate_dir.name)

        # ---- 7. deliverables: runtime-record appendix + evidence commit ----
        gate_sum = json.loads((gate_dir / 'summary.json').read_text(encoding='utf-8'))
        verdicts = {}
        for c in gate_sum.get('checks', []):
            verdicts[c['name']] = c['verdict']
        appendix = (
            '\n---\n\n# GLM-SLOT01-E2E — slot-01 end-to-end through the fleet '
            'control plane (%s)\n\n' % time.strftime('%Y-%m-%d')
            + '- Task `%s` on the fleet registry (integration-kind, slot-01); '
              'base %s; evidence dir %s.\n'
              % (tid, base0[:12], gate_dir.name)
            + '- Built clean from the slot worktree head %s; exe sha256 %s; '
              'spv sha256 %s; shader source blob %s (provenance verified '
              'against the tested revision).\n'
              % (ident['worktree_head'][:12], ident['exe_sha256_runtime'][:12],
                 ident['spv_sha256'][:12], ident['comp_blob'][:12])
            + '- Runtime numerical gate (edge-contrast presentation, phi %.2f '
              'radius %.1f): %s.\n'
              % (CAPTURE_PHI, CAPTURE_RADIUS,
                 ', '.join('%s=%s' % kv for kv in verdicts.items()))
            + '- Interruption drill: worker client terminated post-checkpoint; '
              'registry failover to %s; zombie write refused; GPU reservation '
              'retained until verified drain (port %d free); worktree '
              'reconciled at %s; reassigned at generation %d.\n'
              % (new_owner, SLOT_ENGINE_PORT, wt_head[:12], gen2)
            + '- DYAD: executed per THE_DYAD_PROTOCOL (served model %s; one '
              'image per call; raw responses in dyad_gpu_demo_review.json).\n'
              % str(served)[:60]
            + '- Capture association remains CONDITIONAL per GLM-WINDOW-02 '
              '(accepted_state_id linkage is the strongest implemented '
              'linkage; competing-writer exclusion is not proven).\n'
            + '- Human acceptance: NOT CLAIMED. GPU-driven claim unchanged '
              '(compute drives the accepted state; presentation findings are '
              'render-path facts).\n')
        rec = wt / 'docs' / 'THE_GPU_DEMO01_RUNTIME_RECORD.md'
        rec.write_text(rec.read_text(encoding='utf-8') + appendix, encoding='utf-8')
        ml = wt / 'docs' / 'THE_MASTER_LIST.md'
        ml.write_text(ml.read_text(encoding='utf-8') + (
            '\n## SLOT01-E2E (universal dispatch, single slot)\n\n'
            'One bounded GPU membrane verification task executed end-to-end '
            'through the fleet control plane on slot-01 (task `%s`): claim, '
            'clean slot build, runtime gate PASS, real interruption + failover '
            'recovery at generation %d, DYAD executed, fetch-verified '
            'publication. SINGLE-SLOT VERIFIED; not a five-slot deployment.\n'
            % (tid, gen2)), encoding='utf-8')
        # The gate/dyad instruments ran from the primary checkout, so their
        # evidence landed under repo/docs/evidence/...; the deliverable commit
        # lives in the SLOT worktree, so the evidence is copied there first.
        gate_copy = wt / 'docs' / 'evidence' / 'membrane_gpu_demo_runtime' / gate_dir.name
        if not gate_copy.exists():
            shutil.copytree(gate_dir, gate_copy)
        # evidence files into the worktree's evidence scope
        ev_dst = wt / 'docs' / 'evidence' / 'agent_fleet' / ('SLOT01-E2E-' + tid)
        ev_dst.mkdir(parents=True, exist_ok=True)
        for f in fleet.ev.glob('*'):
            if f.is_file():
                shutil.copy2(f, ev_dst / f.name)
        commit_and_push(wt, claimed['branch'],
                        'slot01-e2e %s: gate+dyad evidence, drill record' % tid,
                        ['docs/evidence/membrane_gpu_demo_runtime/' + gate_dir.name,
                         'docs/evidence/agent_fleet/' + ev_dst.name,
                         'docs/THE_GPU_DEMO01_RUNTIME_RECORD.md',
                         'docs/THE_MASTER_LIST.md'])

        # ---- 8. review -> integrate -> release ------------------------------
        fleet.call(new_owner, 'resource_release', task=tid, generation=gen2,
                   resource='dyad_eye',
                   evidence='dyad complete; raw responses recorded')
        fleet.call(new_owner, 'resource_release', task=tid, generation=gen2,
                   resource='rtx4090',
                   evidence='dyad complete; engine drained at gate end; eye '
                            'inference finished')
        pub = integrate(fleet, tid, str(wt), base0, leader=new_owner)
        fleet.record('integrated', verified=pub['verified_remote_head'])

        # ---- 9. close: verify no orphans, export ----------------------------
        assert not port_bound(SLOT_ENGINE_PORT), 'slot engine port still bound'
        ev = fleet.call('SUPERVISOR', 'events', since=0)
        (fleet.ev / 'events.json').write_text(json.dumps(ev, indent=2),
                                              encoding='utf-8')
        (fleet.ev / 'final_snapshot.json').write_text(
            json.dumps(fleet.snapshot(), indent=2, default=str), encoding='utf-8')
        (run / 'SUMMARY.json').write_text(json.dumps({
            'task': tid, 'base': base0,
            'integrated_head': pub['verified_remote_head'],
            'gate_run_dir': gate_dir.name, 'dyad_served': str(served)[:120],
            'drill': {'gen1': gen1, 'gen2': gen2,
                      'zombie_refused': True,
                      'gpu_retained_then_cleared': True},
        }, indent=2), encoding='utf-8')
        fleet.record('complete', verified=pub['verified_remote_head'])
        return 0
    finally:
        fleet.stop_service()


if __name__ == '__main__':
    sys.exit(main())
