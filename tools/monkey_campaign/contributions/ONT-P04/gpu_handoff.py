"""GPU-A handoff authority/state machine (records profile, CPU-only).

Correction delta for ONT-P04 (lead ruling 2026-09-26, arrival-876e63bf): the
done_when clause "admitted training may interrupt gaming and local inference
through a VERIFIED supervisor handoff" requires the handoff mechanism to exist
and be verified. COORDINATION.md's GPU-handoff section specifies the sequence

    REQUESTED -> DRAINING -> READY -> TRAINING -> RESTORING -> AVAILABLE

with RECOVERY_HOLD ("it never fabricates READY"), priority rules (a protected
training run retains the GPU; training outranks gaming/local inference; fair
arrival-order serialization), supervisor independence, and the GPU-A queue item:
"extend the native controller's request, drain, grant, recovery and release
semantics under its existing authentication."

This module is exactly that extension, implemented as an additive subclass of
the pinned controller (`tools/agent_fleet/control.py` at attempt head
c525b82c7c3ce0128565424764293a3c85811ab3). It adds NO rival authority: one
SQLite registry, every transition inside the controller's BEGIN IMMEDIATE
transaction, actor resolution through `Control._actor`, task/generation
identity through `Control._task`, and the actual GPU grant/release/clear
through the controller's own queue promotion, evidenced release and
supervisor-only clear laws. The machine adds the `handoff` plane
(schema-1-compatible via setdefault) plus an audit journal, and it records --
never executes -- releases: "drained"/"graceful" evidence strings are records
in fixtures, so nothing here launches, kills or unloads a real process.

Every refusal is by name (`control.Refusal`). The exact state/transition/
refusal matrix is frozen in this attempt's PREREGISTRATION.md.
"""
import secrets

from control import Control, Refusal, require, text, integer

PHASES = ('REQUESTED', 'DRAINING', 'READY', 'TRAINING', 'RESTORING',
          'AVAILABLE')
LIVE_PHASES = ('REQUESTED', 'DRAINING', 'READY', 'TRAINING', 'RESTORING',
               'RECOVERY_HOLD')
JOURNAL_LIMIT = 512


def _filled(value):
    return isinstance(value, str) and bool(value.strip())


class HandoffControl(Control):
    """Pinned controller + the six-state training-preemption handoff."""

    def _handoff_plane(self, s):
        return s.setdefault('handoff', {
            'requests': {}, 'queue': [], 'journal': [],
            'gate': None, 'waiters': [], 'instances': {}, 'games': {}})

    def _journal(self, s, plane, op, actor, req, from_phase, to_phase, **detail):
        plane['journal'].append({
            'revision': s['revision'] + 1, 'op': op, 'actor': actor,
            'task': req['task'] if req else None,
            'generation': req['generation'] if req else None,
            'from': from_phase, 'to': to_phase, **detail})
        del plane['journal'][:-JOURNAL_LIMIT]

    def _active_request(self, s, plane, task):
        for rid in plane['queue']:
            req = plane['requests'][rid]
            if req['task'] == task and req['phase'] in LIVE_PHASES:
                return req
        raise Refusal('unknown_handoff_request')

    def _set_phase(self, s, plane, actor, op, req, to_phase, **detail):
        previous = req['phase']
        req['phase'] = to_phase
        self._journal(s, plane, op, actor, req, previous, to_phase, **detail)
        if to_phase == 'AVAILABLE' and req['id'] in plane['queue']:
            plane['queue'].remove(req['id'])

    def _corruption_gate(self, req):
        require(not req.get('corrupted'), 'unknown_state_stays_recovery_hold')

    def _next_action(self, phase):
        return {
            'REQUESTED': 'admit the earliest request; drain cannot start early',
            'DRAINING': 'close inference admission, checkpoint workers, unload '
                        'named models, release games gracefully; then ready',
            'READY': 'confirm the training task holds the GPU grant, then '
                     'launch exactly once',
            'TRAINING': 'protect the run; release only on OBSERVED cessation '
                        'with preservation completed before release',
            'RESTORING': 'release the training hold by owner evidence, reload '
                         'saved restoration configs, resume preserved workers '
                         'once, then AVAILABLE',
            'AVAILABLE': 'idle; a new training cycle is a new request',
            'RECOVERY_HOLD': 'supervisor-only recover from journal + registry '
                             'reality; never fabricate READY',
        }[phase]

    # ------------------------------------------------------------------ ops
    def _dispatch(self, s, actor, op, p):
        if not op.startswith('handoff_'):
            return super()._dispatch(s, actor, op, p)
        plane = self._handoff_plane(s)
        handler = getattr(self, '_h_' + op[len('handoff_'):], None)
        if handler is None:
            raise Refusal('unknown_operation')
        return handler(s, plane, actor, p)

    # 1. Request and validate (fair arrival-order queue; idempotent re-request)
    def _h_request(self, s, plane, actor, p):
        t = self._task(s, actor, p.get('task'), p.get('generation'),
                       instance=p.get('_resolved_instance'))
        text(p.get('evidence'), 'handoff_evidence')
        require(_filled(p.get('derivation_gate_receipt')),
                'invalid_handoff_brief')
        vram = p.get('vram_required_mb')
        require(type(vram) is int and 0 < vram <= 2**40, 'invalid_handoff_brief')
        duration = p.get('expected_duration_minutes')
        require(type(duration) is int and 0 < duration <= 10**6,
                'invalid_handoff_brief')
        admitted = any(q['task'] == t['id'] and q['owner'] == actor
                       and q['generation'] == t['generation'] and not q['served']
                       and any(w['name'] == 'rtx4090' for w in q['wants'])
                       for q in s['resource_queues'])
        require(admitted, 'training_request_not_admitted')
        for req in plane['requests'].values():
            if (req['task'] == t['id'] and req['generation'] == t['generation']
                    and req['phase'] in LIVE_PHASES):
                # Idempotent re-request: same identity, same record, no drain
                # restart, no second queue entry, no journal entry.
                return {'request': req['id'], 'phase': req['phase'],
                        'idempotent_replay': True}
        holder = s['resources'].get('rtx4090')
        rid = secrets.token_hex(12)
        plane['requests'][rid] = {
            'id': rid, 'task': t['id'], 'owner': actor,
            'generation': t['generation'], 'phase': 'REQUESTED',
            'derivation_gate_receipt': p['derivation_gate_receipt'],
            'vram_required_mb': vram,
            'expected_duration_minutes': duration,
            'evidence': p['evidence'],
            'existing_training_owner': ({'task': holder['task'],
                                         'owner': holder['owner'],
                                         'generation': holder['generation']}
                                        if holder else None),
            'drain': {}, 'run_id': None, 'corrupted': False}
        plane['queue'].append(rid)
        self._journal(s, plane, 'handoff_request', actor,
                      plane['requests'][rid], None, 'REQUESTED')
        return {'request': rid, 'phase': 'REQUESTED',
                'arrival_position': plane['queue'].index(rid)}

    def _h_admit(self, s, plane, actor, p):
        req = plane['requests'].get(p.get('request'))
        require(req is not None, 'unknown_handoff_request')
        self._task(s, actor, req['task'], p.get('generation'),
                   instance=p.get('_resolved_instance'))
        self._corruption_gate(req)
        require(req['phase'] == 'REQUESTED', 'handoff_not_requested')
        require(bool(plane['queue']) and plane['queue'][0] == req['id'],
                'handoff_queue_jump_refused')
        require(not any(r['phase'] == 'TRAINING'
                        for r in plane['requests'].values()),
                'protected_run_active')
        self._set_phase(s, plane, actor, 'handoff_admit', req, 'DRAINING')
        return {'request': req['id'], 'phase': 'DRAINING'}

    # 2. Inference admission gate: closed through drain/training; on timeout it
    #    stays closed (a closed gate never falls through to direct inference).
    def _h_gate_close(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        require(req['phase'] == 'DRAINING', 'handoff_not_draining')
        if plane['gate'] and plane['gate'].get('closed'):
            return {'gate': 'CLOSED', 'note': 'already_closed'}
        deadline = p.get('deadline_revision')
        if deadline is not None:
            deadline = integer(deadline, 0, 2**62, 'deadline_revision')
        plane['gate'] = {'closed': True, 'closed_revision': s['revision'] + 1,
                         'deadline_revision': deadline, 'timed_out': False}
        self._journal(s, plane, 'handoff_gate_close', actor, req,
                      'DRAINING', 'DRAINING', gate='CLOSED')
        return {'gate': 'CLOSED',
                'closed_revision': plane['gate']['closed_revision'],
                'deadline_revision': deadline}

    def _h_gate_check(self, s, plane, actor, p):
        gate = plane['gate']
        if not gate or not gate.get('closed'):
            return {'gate': 'OPEN', 'status': 'OPEN'}
        if (gate.get('deadline_revision') is not None
                and s['revision'] + 1 > gate['deadline_revision']):
            gate['timed_out'] = True
            req = plane['requests'][plane['queue'][0]] if plane['queue'] else None
            self._journal(s, plane, 'handoff_gate_check', actor, req,
                          req['phase'] if req else None,
                          req['phase'] if req else None, gate='GATE_TIMEOUT')
            return {'gate': 'CLOSED', 'status': 'GATE_TIMEOUT',
                    'note': 'gate_timeout_gate_stays_closed'}
        return {'gate': 'CLOSED', 'status': 'CLOSED'}

    def _h_gate_open(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        require(req['phase'] == 'RESTORING', 'inference_gate_open_not_allowed')
        require(plane['gate'] and plane['gate'].get('closed'),
                'gate_already_open')
        plane['gate'] = None
        self._journal(s, plane, 'handoff_gate_open', actor, req,
                      'RESTORING', 'RESTORING', gate='OPEN')
        return {'gate': 'OPEN'}

    def _h_infer_wait(self, s, plane, actor, p):
        gate = plane['gate']
        if gate and gate.get('closed'):
            plane['waiters'].append({
                'actor': actor, 'task': p.get('task'),
                'kind': p.get('kind', 'local_inference'),
                'revision': s['revision'] + 1, 'status': 'RESOURCE_WAIT'})
            return {'status': 'RESOURCE_WAIT', 'gate': 'CLOSED',
                    'waiters': len(plane['waiters']),
                    'note': 'waits; no model-load timeout consumption, no '
                            'fallthrough to direct inference'}
        return {'status': 'OPEN', 'gate': 'OPEN'}

    def _h_reload_attempt(self, s, plane, actor, p):
        gate = plane['gate']
        if gate and gate.get('closed'):
            raise Refusal('inference_admission_closed')
        return {'reloaded': 'ALLOWED_WHEN_GATE_OPEN'}

    # 3. Drain evidence: worker checkpoints, named model unloads, graceful game
    #    release. All are records; no process is touched.
    def _h_checkpoint_preserved(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        require(req['phase'] == 'DRAINING', 'handoff_not_draining')
        workers = p.get('workers')
        if not (_filled(p.get('evidence')) and isinstance(workers, list)
                and workers and all(isinstance(w, str) and w for w in workers)):
            raise Refusal('preservation_evidence_required')
        req['drain']['checkpoint_preserved'] = p['evidence']
        req['drain']['preserved_workers'] = list(workers)
        self._journal(s, plane, 'handoff_checkpoint_preserved', actor, req,
                      'DRAINING', 'DRAINING', workers=len(workers))
        return {'preserved': True, 'workers': len(workers)}

    def _h_register_model(self, s, plane, actor, p):
        require(actor == 'SUPERVISOR', 'supervisor_only')
        iid = text(p.get('instance'), 'instance')
        require(iid not in plane['instances'], 'instance_already_registered')
        cfg = p.get('restoration_config')
        require(isinstance(cfg, dict) and cfg.get('artifact')
                and cfg.get('context') is not None,
                'restoration_config_required')
        plane['instances'][iid] = dict(cfg)
        return {'registered': iid}

    def _h_model_unload(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        require(req['phase'] == 'DRAINING', 'handoff_not_draining')
        iid = p.get('instance')
        require(isinstance(iid, str) and iid.strip() and iid != '--all',
                'model_unload_all_refused')
        require(iid in plane['instances'], 'unknown_instance')
        cfg = p.get('restoration_config')
        require(isinstance(cfg, dict) and cfg.get('artifact')
                and cfg.get('context') is not None,
                'restoration_config_required')
        unloaded = req['drain'].setdefault('unloaded', {})
        require(iid not in unloaded, 'instance_already_unloaded')
        unloaded[iid] = dict(cfg)
        self._journal(s, plane, 'handoff_model_unload', actor, req,
                      'DRAINING', 'DRAINING', instance=iid)
        return {'unloaded': iid, 'restoration_config': dict(cfg)}

    def _h_register_game(self, s, plane, actor, p):
        require(actor == 'SUPERVISOR', 'supervisor_only')
        name = text(p.get('name'), 'game_name')
        require(name not in plane['games'], 'game_already_registered')
        plane['games'][name] = {
            'executable': text(p.get('executable'), 'executable'),
            'pid': integer(p.get('pid', 0), 1, 2**31, 'pid'),
            'start_time': text(p.get('start_time'), 'start_time')}
        return {'registered': name}

    def _h_game_release(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        require(req['phase'] == 'DRAINING', 'handoff_not_draining')
        name = text(p.get('name'), 'game_name')
        game = plane['games'].get(name)
        require(game is not None, 'unregistered_game_identity')
        require(p.get('pid') == game['pid']
                and p.get('start_time') == game['start_time'],
                'game_identity_mismatch')
        if not _filled(p.get('evidence')):
            raise Refusal('graceful_release_required')
        free = p.get('observed_free_vram_mb')
        require(type(free) is int and 0 <= free <= 2**40,
                'insufficient_vram_evidence')
        released = req['drain'].setdefault('game_released', {})
        released[name] = {'evidence': p['evidence'],
                          'observed_free_vram_mb': free,
                          'method': 'graceful_save_quit'}
        self._journal(s, plane, 'handoff_game_release', actor, req,
                      'DRAINING', 'DRAINING', game=name)
        return {'released': name, 'method': 'graceful_save_quit',
                'observed_free_vram_mb': free}

    def _h_force_kill(self, s, plane, actor, p):
        # Not a legal operation in any phase, for any actor, ever. A failed
        # graceful release enters RECOVERY_HOLD instead (COORDINATION.md step 4:
        # forced termination needs a separate explicit operator instruction,
        # which this records-profile machine does not implement).
        raise Refusal('force_kill_refused')

    # 4. READY: the whole drain verified; no foreign holder may remain.
    def _h_ready(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        self._task(s, actor, req['task'], p.get('generation'),
                   instance=p.get('_resolved_instance'))
        require(req['phase'] == 'DRAINING', 'handoff_not_draining')
        gate = plane['gate']
        require(gate and gate.get('closed'), 'inference_gate_open')
        require(req['drain'].get('checkpoint_preserved'),
                'preservation_evidence_required')
        unloaded = req['drain'].get('unloaded', {})
        require(set(plane['instances']) <= set(unloaded),
                'model_instances_still_loaded')
        released = req['drain'].get('game_released', {})
        require(set(plane['games']) <= set(released), 'game_not_released')
        observations = [r['observed_free_vram_mb'] for r in released.values()]
        if p.get('observed_free_vram_mb') is not None:
            free = p['observed_free_vram_mb']
            require(type(free) is int and 0 <= free <= 2**40,
                    'insufficient_vram_evidence')
            observations.append(free)
        require(observations
                and max(observations) >= req['vram_required_mb'],
                'insufficient_vram_evidence')
        holder = s['resources'].get('rtx4090')
        require(holder is None or holder['task'] == req['task'],
                'protected_holder_present')
        self._set_phase(s, plane, actor, 'handoff_ready', req, 'READY',
                        observed_free_vram_mb=max(observations))
        return {'request': req['id'], 'phase': 'READY',
                'observed_free_vram_mb': max(observations)}

    # 5. Grant confirmed through the controller, launch exactly once. The
    #    durable run id is checked BEFORE the phase guard: any replay attempt,
    #    from any phase (including across a restart), is already_launched.
    def _h_launch(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        self._task(s, actor, req['task'], p.get('generation'),
                   instance=p.get('_resolved_instance'))
        require(req['run_id'] is None, 'already_launched')
        require(req['phase'] == 'READY', 'handoff_not_ready')
        holder = s['resources'].get('rtx4090')
        require(holder is not None and holder['task'] == req['task']
                and holder['generation'] == req['generation'],
                'gpu_not_held_by_training_task')
        text(p.get('evidence'), 'launch_evidence')
        req['run_id'] = secrets.token_hex(12)
        self._set_phase(s, plane, actor, 'handoff_launch', req, 'TRAINING',
                        run_id=req['run_id'])
        return {'request': req['id'], 'phase': 'TRAINING',
                'run_id': req['run_id'], 'launched': 'exactly_once'}

    # 6. Observed cessation + preservation BEFORE release.
    def _h_cessation(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        self._task(s, actor, req['task'], p.get('generation'),
                   instance=p.get('_resolved_instance'))
        require(req['phase'] == 'TRAINING', 'handoff_not_training')
        require(p.get('observed') is True,
                'release_requires_observed_cessation')
        if not _filled(p.get('preserved_receipts_evidence')):
            raise Refusal('preservation_required_before_release')
        text(p.get('evidence'), 'cessation_evidence')
        req['drain']['cessation'] = {
            'observed': True, 'evidence': p['evidence'],
            'preserved_receipts_evidence': p['preserved_receipts_evidence']}
        self._set_phase(s, plane, actor, 'handoff_cessation', req, 'RESTORING')
        return {'request': req['id'], 'phase': 'RESTORING',
                'protected_until': 'confirmed release by owner evidence'}

    # 7. Restore: only the captured configs; each preserved worker once.
    def _h_restore(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        self._corruption_gate(req)
        self._task(s, actor, req['task'], p.get('generation'),
                   instance=p.get('_resolved_instance'))
        require(req['phase'] == 'RESTORING', 'handoff_not_restoring')
        holder = s['resources'].get('rtx4090')
        require(holder is None or holder['task'] != req['task'],
                'training_hold_not_released')
        unloaded = req['drain'].get('unloaded', {})
        reloads = p.get('reloads')
        require(isinstance(reloads, list) and reloads, 'restore_incomplete')
        seen = set()
        for item in reloads:
            iid = item.get('instance')
            require(iid in unloaded, 'unknown_instance')
            require(iid not in seen, 'instance_already_resumed')
            seen.add(iid)
            require(item.get('restoration_config') == unloaded[iid],
                    'restoration_config_mismatch')
            require(_filled(item.get('health_evidence')),
                    'health_evidence_required')
        require(set(unloaded) <= seen, 'restore_incomplete')
        preserved = req['drain'].get('preserved_workers', [])
        resumes = p.get('resumes')
        require(isinstance(resumes, list), 'restore_incomplete')
        resumed = set()
        for w in resumes:
            require(w in preserved, 'worker_not_preserved')
            require(w not in resumed, 'worker_already_resumed')
            resumed.add(w)
        require(set(preserved) <= resumed, 'restore_incomplete')
        plane['gate'] = None
        self._set_phase(s, plane, actor, 'handoff_restore', req, 'AVAILABLE',
                        gate='OPENED_ON_RESTORE')
        return {'request': req['id'], 'phase': 'AVAILABLE', 'gate': 'OPEN',
                'resumed_workers': sorted(resumed), 'games_relaunched': False}

    # RECOVERY_HOLD: any uncertain/failing transition; never fabricates READY.
    def _h_hold(self, s, plane, actor, p):
        req = self._active_request(s, plane, p.get('task'))
        require(actor == 'SUPERVISOR' or actor == req['owner'],
                'handoff_hold_not_authorized')
        text(p.get('reason'), 'hold_reason')
        if not _filled(p.get('evidence')):
            raise Refusal('hold_evidence_required')
        previous = req['phase']
        self._set_phase(s, plane, actor, 'handoff_hold', req, 'RECOVERY_HOLD',
                        reason=p['reason'])
        return {'request': req['id'], 'phase': 'RECOVERY_HOLD',
                'from_phase': previous}

    def _h_recover(self, s, plane, actor, p):
        require(actor == 'SUPERVISOR', 'supervisor_only')
        req = plane['requests'].get(p.get('request'))
        require(req is not None, 'unknown_handoff_request')
        recorded = req.get('phase')
        holder = s['resources'].get('rtx4090')
        grant_live = (holder is not None and holder['task'] == req['task']
                      and holder['generation'] == req['generation'])
        foreign = holder is not None and holder['task'] != req['task']
        if recorded not in PHASES and recorded != 'RECOVERY_HOLD':
            # Unknown/corrupt persisted phase: RECOVERY_HOLD, and every further
            # transition stays refused until a supervisor reconstructs.
            req['corrupted'] = True
            req['phase'] = 'RECOVERY_HOLD'
            self._journal(s, plane, 'handoff_recover', actor, req,
                          str(recorded), 'RECOVERY_HOLD',
                          note='unknown_state_stays_recovery_hold')
            return {'phase': 'RECOVERY_HOLD',
                    'note': 'unknown_state_stays_recovery_hold',
                    'reconstructed_from_journal': True}
        if recorded == 'RECOVERY_HOLD' or req.get('corrupted'):
            if recorded == 'READY' and foreign:
                raise Refusal('resources_still_held')
            demand = p.get('resume_to')
            if demand == 'READY':
                raise Refusal('cannot_fabricate_ready')
            if demand == 'TRAINING' and not grant_live:
                raise Refusal('cannot_fabricate_ready')
            # A TRAINING record (or any record carrying a durable run id) whose
            # grant is observed live in the registry reconstructs back to
            # TRAINING: protected retention survives the restart, the recorded
            # run id is preserved, and a replayed launch stays already_launched.
            was_training = recorded == 'TRAINING' or bool(req.get('run_id'))
            if was_training and grant_live:
                req['corrupted'] = False
                req['phase'] = 'TRAINING'
                self._journal(s, plane, 'handoff_recover', actor, req,
                              recorded, 'TRAINING',
                              note='protected run grant observed live')
                return {'phase': 'TRAINING',
                        'note': 'protected retention survives restart',
                        'run_id': req['run_id']}
            if (p.get('cessation_observed') is True and not grant_live
                    and was_training):
                if demand == 'RESTORING' and not _filled(
                        p.get('preserved_receipts_evidence')):
                    raise Refusal('preservation_required_before_release')
                if not _filled(p.get('preserved_receipts_evidence')):
                    raise Refusal('preservation_required_before_release')
                req['corrupted'] = False
                req['phase'] = 'RESTORING'
                req['drain']['cessation'] = {
                    'observed': True, 'evidence': p.get('evidence') or '',
                    'preserved_receipts_evidence':
                        p['preserved_receipts_evidence']}
                self._journal(s, plane, 'handoff_recover', actor, req,
                              recorded, 'RESTORING',
                              note='observed cessation evidence supplied')
                return {'phase': 'RESTORING',
                        'note': 'interrupted transition completed with '
                                'observed cessation evidence'}
            if demand == 'RESTORING':
                raise Refusal('recovery_evidence_insufficient')
            return {'phase': 'RECOVERY_HOLD',
                    'note': 'recovery_evidence_insufficient',
                    'reconstructed_from_journal': True}
        # Non-hold phase: reconstruction confirms the phase against registry
        # reality and reports it; no blind resume, no replayed launch.
        if recorded == 'READY' and foreign:
            # A foreign holder appeared across the restart: READY may not be
            # trusted and READY must never be fabricated out of it.
            raise Refusal('resources_still_held')
        return {'phase': recorded, 'grant_live': grant_live,
                'foreign_holder': foreign, 'run_id': req['run_id'],
                'reconstructed_from_journal': True}

    # Visibility through the existing controller (also carried in snapshot).
    def _h_state(self, s, plane, actor, p):
        queue = []
        for rid in plane['queue']:
            req = plane['requests'][rid]
            queue.append({'id': rid, 'task': req['task'], 'owner': req['owner'],
                          'generation': req['generation'], 'phase': req['phase'],
                          'run_id': req['run_id'],
                          'next_action': self._next_action(req['phase'])})
        gate = plane['gate'] or {'closed': False}
        return {'queue': queue, 'gate': gate, 'waiters': len(plane['waiters']),
                'registered_instances': sorted(plane['instances']),
                'registered_games': sorted(plane['games']),
                'journal_tail': plane['journal'][-10:]}
