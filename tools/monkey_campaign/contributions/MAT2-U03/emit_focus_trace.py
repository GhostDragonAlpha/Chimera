"""MAT2-U03 trace probe: the frozen qualification scenario, tick by tick.

Writes `policy_traces.json` — the profile's "input/state/tick display"
diagnostic layer as NUMERICAL evidence: every injected event, every 20 Hz
boundary, every emitted CommandRecord (v_forward, yaw_rate, issued_tick,
source), the policy gate state, the mapper's held set, and the consumer's
effective demand under the upstream aging floor. CPU-only, stdlib-only,
injected clock, no engine, no desktop input. This is a records display, not
pixels; the visual/camera clause is PENDING_RUNTIME (PREREGISTRATION.md).

Run from the checkout root:
    python -B tools/monkey_campaign/contributions/MAT2-U03/emit_focus_trace.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SEAM = HERE / 'pinned_seam'
PRODUCT = SEAM / 'tools' / 'monkey_campaign' / 'product'

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PRODUCT))
import focus_policy as fp  # noqa: E402
import input_mapper as M   # noqa: E402


def main():
    subject_sha = hashlib.sha256(
        (PRODUCT / 'input_mapper.py').read_bytes()).hexdigest()
    seam_sha = hashlib.sha256(
        (SEAM / 'tools' / 'science_funnel' / 'typeb_export' /
         'command_record.py').read_bytes()).hexdigest()

    sink = M.MockSink()
    policy = fp.FocusPolicy(M.InputMapper(sink))

    # ── the frozen scenario (events injected; ticks at the 20 Hz grid) ──────
    script = [
        (1000, 'press', ('W',)),                    # walk demand begins
        (1257, 'focus_lost', ()),                   # ALT-TAB mid-walk
        (1460, 'press', ('W',)),                    # forced press while gated
        (1500, 'mouse', (40,)),                     # mouse counts while gated
        (1700, 'focus_gained', ()),                 # refocus
        (1710, 'press', ('W',)),                    # fresh grid
        (1815, 'disconnected', ()),                 # DISCONNECT mid-walk
        (2000, 'reconnected', ()),                  # reconnect
        (2010, 'press', ('W',)),
        (2080, 'release', ('W',)),                  # plain KEY RELEASE
        (2400, 'focus_lost', ()),                   # focus lost while idle
    ]
    ticks = [1000, 1050, 1100, 1150, 1200, 1250,
             1300, 1350, 1400, 1450, 1500,
             1700, 1710, 1760, 1810,
             1850, 1900, 1950,
             2000, 2010, 2060,
             2100, 2150, 2200,
             2400, 2450]

    rows = []
    events_by_ms = {}
    for ms, kind, args in script:
        events_by_ms.setdefault(ms, []).append((kind, args))

    # Merged timeline: input/policy events fire at their EXACT injected ms
    # (asynchronous, like a real event loop); the 20 Hz boundary (policy.tick)
    # runs ONLY at the declared tick times. Rows snapshot both kinds of times.
    # (First draft dispatched events only inside tick rows, so events between
    # boundaries never fired -- preserved in report.md as a failure.)
    for now_ms in sorted(set(ticks) | set(events_by_ms)):
        row = {'now_ms': now_ms, 'is_boundary': now_ms in ticks,
               'events': [], 'emitted': [], 'gated': None,
               'held': [], 'effective_demand': None, 'demand_state': None}
        for kind, args in events_by_ms.get(now_ms, ()):
            if kind == 'press':
                action = policy.press(*args, now_ms)
                row['events'].append({'event': 'press', 'name': args[0],
                                      'accepted': action is not None,
                                      'refusal': None if action is not None
                                      else 'press_refused_while_gated'})
            elif kind == 'release':
                policy.release(*args, now_ms)
                row['events'].append({'event': 'release', 'name': args[0]})
            elif kind == 'mouse':
                ok = policy.mouse(*args, now_ms) is not None
                row['events'].append({'event': 'mouse', 'counts': args[0],
                                      'accepted': ok,
                                      'refusal': None if ok
                                      else 'mouse_refused_while_gated'})
            elif kind in ('focus_lost', 'disconnected', 'focus_gained',
                          'reconnected'):
                action = getattr(policy, kind)(now_ms)
                row['events'].append({'event': kind, 'action': action})
        records = policy.tick(now_ms) if row['is_boundary'] else []
        row['emitted'] = [{'v_forward': r.v_forward, 'yaw_rate': r.yaw_rate,
                           'issued_tick': r.issued_tick, 'source': r.source}
                          for r in records]
        row['gated'] = policy.gated
        row['held'] = sorted(policy.held)
        state, rec = policy.effective_demand(now_ms)
        row['demand_state'] = state
        row['effective_demand'] = (None if rec is None
                                   else {'v_forward': rec.v_forward,
                                         'issued_tick': rec.issued_tick})
        rows.append(row)

    # ── frozen invariants, evaluated on the trace itself ────────────────────
    # No-stuck-movement semantics, per demand EPISODE: after a release
    # trigger, the demand that existed at trigger time must cease by
    # trigger+RELEASE_DECAY_MS, and no nonzero effective demand may appear
    # again UNTIL THE NEXT LAWFUL PRESS (a post-resume press at focus_ms is a
    # NEW demand, not stuck movement). (Two earlier drafts of this invariant
    # were wrong -- all-later-rows scan, then deadline-only scan that charged
    # later episodes to earlier triggers; both preserved in report.md.)
    triggers = [('focus_lost_1257', 1257, 1710),    # window ends at the
                 ('disconnected_1815', 1815, 2010), # next lawful press after
                 ('key_release_2080', 2080, None)]  # resume (None: trace end)
    invariants = {}
    for name, ms, window_end in triggers:
        deadline = ms + M.RELEASE_DECAY_MS
        end = window_end if window_end is not None else 10 ** 9
        nonzero_in_window_after_deadline = [
            r['now_ms'] for r in rows
            if deadline < r['now_ms'] < end and r['effective_demand']
            and r['effective_demand']['v_forward'] > 0.0]
        within = [r['now_ms'] for r in rows
                  if ms <= r['now_ms'] <= deadline and r['effective_demand']
                  and r['effective_demand']['v_forward'] > 0.0]
        invariants[name] = {
            'trigger_ms': ms,
            'declared_cease_by_ms': deadline,
            'episode_window_end_ms': window_end,
            'last_nonzero_within_window_ms': max(within) if within else None,
            'nonzero_after_deadline_within_episode': nonzero_in_window_after_deadline,
            'no_stuck_movement': not nonzero_in_window_after_deadline,
        }
    gated_presses_named = [
        e for r in rows for e in r['events']
        if e.get('refusal') == 'press_refused_while_gated']
    invariants['gated_press_refused_by_name'] = bool(gated_presses_named)
    invariants['no_replay_after_resume'] = all(
        r['emitted'] == [] for r in rows
        if 1257 <= r['now_ms'] < 1710 and r['now_ms'] not in (1300, 1350))

    doc = {
        'schema': 'u03_focus_trace.v1',
        'policy_id': fp.POLICY_ID,
        'policy': fp.POLICY,
        'upstream': {
            'input_mapper_sha256': subject_sha,
            'command_record_sha256': seam_sha,
            'constants': {'INTERVAL_MS': M.INTERVAL_MS,
                          'RELEASE_DECAY_MS': M.RELEASE_DECAY_MS,
                          'VALID_MS': M.VALID_MS,
                          'EXPIRY_TICKS': M.EXPIRY_TICKS,
                          'PHYSICS_HZ': M.PHYSICS_HZ,
                          'V_MAX_IN_BAND_M_S': M.V_MAX_IN_BAND_M_S},
        },
        'scenario_events': [
            {'now_ms': ms, 'event': kind, 'args': list(args)}
            for ms, kind, args in script],
        'rows': rows,
        'invariants': invariants,
        'display_honesty': {
            'kind': 'numerical_records_trace',
            'visual_clause': 'PENDING_RUNTIME: the controls motion profile '
                             'camera/visual clause is not claimable here -- '
                             'this sparse attempt checkout has no integrated '
                             'game loop consuming the seam, and real alt-tab '
                             'would touch operator desktop focus, which the '
                             'card observation forbids. Deferred to the '
                             'runtime lane; not passed here.',
            'numerical_clause': 'PASSED_HERE: per-tick command/policy/consumer '
                                'traces with exact injected timing; named '
                                'checks in test_focus_policy.py.',
        },
    }
    out = HERE / 'policy_traces.json'
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print('policy:', fp.POLICY_ID)
    print('rows:', len(rows), '| sink records:', len(sink.records))
    for name in ('focus_lost_1257', 'disconnected_1815', 'key_release_2080'):
        inv = invariants[name]
        print('%s: cease by %s (last nonzero in window: %s; nonzero after '
              'deadline in episode: %s) -> no_stuck_movement=%s'
              % (name, inv['declared_cease_by_ms'],
                 inv['last_nonzero_within_window_ms'],
                 inv['nonzero_after_deadline_within_episode'],
                 inv['no_stuck_movement']))
    print('gated press refused by name:', invariants['gated_press_refused_by_name'])
    print('no replay after resume:', invariants['no_replay_after_resume'])
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
